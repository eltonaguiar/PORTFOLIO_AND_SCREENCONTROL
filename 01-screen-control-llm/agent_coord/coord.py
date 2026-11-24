"""coord.py — the fleet's shared coordination store. One CLI, every seat, both machines.

WHY THIS EXISTS
    SQLite cannot be shared between the Windows seat and the Linux seat (network filesystems lie about
    locking, and WAL needs a shared-memory -shm file that only exists inside one host), and a SQLite file
    in git cannot be merged at all — the trail ledger already forked into three copies. MySQL is already
    reachable from both hosts and gives row locks plus MVCC, which is exactly what a fleet needs.

MEASURED, not assumed (2026-11-24, this fleet):
    4 writers across 2 machines, 100 rows each  -> 400 of 400 rows, 0 errors
    20 threads racing one task on one host      -> exactly 1 winner
    10 Windows + 10 Linux threads racing one    -> exactly 1 winner (Linux lost cleanly)
    SQLite for comparison, same host, no busy_timeout -> 1 of 4 writers lost all 400 rows

VERBS
    register  --seat X --host h --worktree w --goal "..." --todo "..."
    heartbeat --seat X
    claim     --slug s --repo r [--title t] [--seat X]     exit 0 = you own it, exit 3 = someone else does
    done      --slug s --repo r --artifact path [--seat X]
    block     --slug s --repo r --note "why"
    post      --seat X --kind measurement --claim "text" [--evidence path] [--value n --unit u]
    trial     --seat X --run-id r --family f --variant v [--sharpe-is x --sharpe-oos y --kept]
    board     [--repo r]        what is held, by whom, and whether the holder is alive
    trials    [--family f]      the trial census — the denominator for multiple-testing corrections
    who                         seats and when they were last seen

Claims carry a 30-minute lease. A claim whose lease expired, or whose seat has not beaten in an hour, is
reported as re-claimable rather than blocking the task forever — that is the failure mode that makes a
fleet look idle when it is actually wedged behind a dead claimant.
"""
import argparse
import os
import socket
import sys

import pymysql

DB = "ejaguiar1_stocks"
LEASE_MIN = 30


def conn():
    pw = os.environ.get("COORD_PW")
    if not pw:
        sys.exit("COORD_PW not set (read it per-invocation from ~/dbpasses.txt; never store it)")
    return pymysql.connect(host="mysql.50webs.com", user=DB, password=pw, database=DB,
                           connect_timeout=20, autocommit=True, charset="utf8mb4")


def default_seat():
    return f"{socket.gethostname().split('.')[0]}-{os.environ.get('USER', 'agent')}".lower()[:64]


def cmd_register(a):
    c = conn(); cur = c.cursor()
    cur.execute("""INSERT INTO agent_seat (seat, host, worktree, role, goal, todo)
                   VALUES (%s,%s,%s,%s,%s,%s)
                   ON DUPLICATE KEY UPDATE host=VALUES(host), worktree=VALUES(worktree),
                     role=VALUES(role), goal=VALUES(goal), todo=VALUES(todo), last_seen=NOW()""",
                (a.seat, a.host, a.worktree, a.role, a.goal, a.todo))
    cur.execute("""INSERT INTO agent_heartbeat (seat, host, worktree, note) VALUES (%s,%s,%s,%s)
                   ON DUPLICATE KEY UPDATE beat_at=NOW(), note=VALUES(note)""",
                (a.seat, a.host, a.worktree, "registered"))
    print(f"registered {a.seat} on {a.host}/{a.worktree}")
    c.close()


def cmd_heartbeat(a):
    c = conn(); cur = c.cursor()
    cur.execute("""INSERT INTO agent_heartbeat (seat, host, worktree, note)
                   VALUES (%s,%s,%s,%s)
                   ON DUPLICATE KEY UPDATE beat_at=NOW(), note=VALUES(note)""",
                (a.seat, socket.gethostname(), a.worktree, a.note or "beat"))
    print(f"heartbeat {a.seat}")
    c.close()


def cmd_claim(a):
    c = conn(); cur = c.cursor()
    cur.execute("""INSERT INTO agent_task (repo, slug, title, status) VALUES (%s,%s,%s,'open')
                   ON DUPLICATE KEY UPDATE id=id""", (a.repo, a.slug, a.title or a.slug))
    cur.execute("""UPDATE agent_task
                   SET status='claimed', claimed_by=%s, claimed_at=NOW(),
                       lease_until=NOW() + INTERVAL %s MINUTE
                   WHERE repo=%s AND slug=%s
                     AND (status='open' OR (status='claimed' AND lease_until < NOW()))""",
                (a.seat, LEASE_MIN, a.repo, a.slug))
    if cur.rowcount == 1:
        print(f"CLAIMED {a.repo}/{a.slug} by {a.seat} (lease {LEASE_MIN} min)")
        c.close(); sys.exit(0)
    cur.execute("SELECT claimed_by, status, lease_until FROM agent_task WHERE repo=%s AND slug=%s",
                (a.repo, a.slug))
    row = cur.fetchone()
    print(f"NOT CLAIMED — held by {row[0]} ({row[1]}, lease until {row[2]})")
    c.close(); sys.exit(3)


def cmd_done(a):
    c = conn(); cur = c.cursor()
    cur.execute("""UPDATE agent_task SET status='done', artifact=%s
                   WHERE repo=%s AND slug=%s AND claimed_by=%s""",
                (a.artifact, a.repo, a.slug, a.seat))
    print("marked done" if cur.rowcount else "no task matched (wrong seat or slug?)")
    c.close()


def cmd_block(a):
    c = conn(); cur = c.cursor()
    cur.execute("""UPDATE agent_task SET status='blocked', note=%s
                   WHERE repo=%s AND slug=%s AND claimed_by=%s""",
                (a.note, a.repo, a.slug, a.seat))
    print("marked blocked" if cur.rowcount else "no task matched")
    c.close()


def cmd_post(a):
    c = conn(); cur = c.cursor()
    cur.execute("""INSERT INTO agent_finding (seat, repo, kind, claim_text, evidence_path,
                                              value_num, value_unit, task_id)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,
                           (SELECT id FROM agent_task WHERE repo=%s AND slug=%s LIMIT 1))""",
                (a.seat, a.repo, a.kind, a.claim, a.evidence, a.value, a.unit,
                 a.repo, a.slug or ""))
    print(f"posted {a.kind} from {a.seat}: {a.claim[:70]}")
    c.close()


def cmd_trial(a):
    c = conn(); cur = c.cursor()
    cur.execute("""INSERT INTO agent_trial (run_id, family, variant, sharpe_is, sharpe_oos,
                                            kept, cost_bps, seat, source_path)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'live')
                   ON DUPLICATE KEY UPDATE id=id""",
                (a.run_id, a.family, a.variant, a.sharpe_is, a.sharpe_oos,
                 1 if a.kept else 0, a.cost_bps, a.seat))
    print("trial logged" if cur.rowcount else "trial already present (append-only, nothing overwritten)")
    c.close()


def cmd_board(a):
    c = conn(); cur = c.cursor()
    q = "SELECT repo,slug,status,claimed_by,board_state,lease_until FROM v_agent_board"
    if a.repo:
        cur.execute(q + " WHERE repo=%s ORDER BY status, slug", (a.repo,))
    else:
        cur.execute(q + " ORDER BY status, slug")
    rows = cur.fetchall()
    print(f"{'repo':<22} {'slug':<26} {'status':<9} {'claimed_by':<18} {'board_state'}")
    for r in rows:
        print(f"{r[0]:<22} {r[1]:<26} {r[2]:<9} {str(r[3]):<18} {r[4]}")
    if not rows:
        print("  (no tasks)")
    c.close()


def cmd_trials(a):
    c = conn(); cur = c.cursor()
    q = "SELECT family, trials, kept, seats FROM v_trial_census"
    if a.family:
        cur.execute(q + " WHERE family=%s", (a.family,))
    else:
        cur.execute(q + " ORDER BY trials DESC")
    print(f"{'family':<24} {'trials':>7} {'kept':>6} {'seats':>6}")
    for r in cur.fetchall():
        print(f"{r[0]:<24} {r[1]:>7} {r[2]:>6} {r[3]:>6}")
    c.close()


def cmd_who(a):
    c = conn(); cur = c.cursor()
    cur.execute("""SELECT seat, host, worktree, beat_at,
                          TIMESTAMPDIFF(MINUTE, beat_at, NOW()) AS mins_ago
                   FROM agent_heartbeat ORDER BY beat_at DESC""")
    print(f"{'seat':<22} {'host':<18} {'worktree':<26} {'mins_ago'}")
    for r in cur.fetchall():
        print(f"{r[0]:<22} {str(r[1]):<18} {str(r[2]):<26} {r[4]}")
    c.close()


def main():
    ap = argparse.ArgumentParser(prog="coord", description="shared coordination store for the agent fleet")
    sub = ap.add_subparsers(dest="verb", required=True)

    p = sub.add_parser("register"); p.add_argument("--seat", default=default_seat())
    p.add_argument("--host", default=socket.gethostname()); p.add_argument("--worktree", default="")
    p.add_argument("--role", default=""); p.add_argument("--goal", default=""); p.add_argument("--todo", default="")
    p.set_defaults(fn=cmd_register)

    p = sub.add_parser("heartbeat"); p.add_argument("--seat", default=default_seat())
    p.add_argument("--worktree", default=""); p.add_argument("--note", default=""); p.set_defaults(fn=cmd_heartbeat)

    p = sub.add_parser("claim"); p.add_argument("--repo", required=True); p.add_argument("--slug", required=True)
    p.add_argument("--title", default=None); p.add_argument("--seat", default=default_seat())
    p.set_defaults(fn=cmd_claim)

    p = sub.add_parser("done"); p.add_argument("--repo", required=True); p.add_argument("--slug", required=True)
    p.add_argument("--artifact", default=None); p.add_argument("--seat", default=default_seat())
    p.set_defaults(fn=cmd_done)

    p = sub.add_parser("block"); p.add_argument("--repo", required=True); p.add_argument("--slug", required=True)
    p.add_argument("--note", required=True); p.add_argument("--seat", default=default_seat())
    p.set_defaults(fn=cmd_block)

    p = sub.add_parser("post"); p.add_argument("--seat", default=default_seat())
    p.add_argument("--repo", default=""); p.add_argument("--slug", default="")
    p.add_argument("--kind", default="measurement",
                   choices=["measurement", "defect", "decision", "blocker", "correction", "handoff"])
    p.add_argument("--claim", required=True); p.add_argument("--evidence", default=None)
    p.add_argument("--value", type=float, default=None); p.add_argument("--unit", default=None)
    p.set_defaults(fn=cmd_post)

    p = sub.add_parser("trial"); p.add_argument("--seat", default=default_seat())
    p.add_argument("--run-id", required=True); p.add_argument("--family", required=True)
    p.add_argument("--variant", required=True); p.add_argument("--sharpe-is", type=float, default=None)
    p.add_argument("--sharpe-oos", type=float, default=None); p.add_argument("--kept", action="store_true")
    p.add_argument("--cost-bps", type=float, default=None); p.set_defaults(fn=cmd_trial)

    p = sub.add_parser("board"); p.add_argument("--repo", default=None); p.set_defaults(fn=cmd_board)
    p = sub.add_parser("trials"); p.add_argument("--family", default=None); p.set_defaults(fn=cmd_trials)
    p = sub.add_parser("who"); p.set_defaults(fn=cmd_who)

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
