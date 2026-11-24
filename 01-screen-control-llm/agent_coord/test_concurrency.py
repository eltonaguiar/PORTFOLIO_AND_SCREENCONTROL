"""Cross-machine concurrency proof for the agent_coord store.

Run this from BOTH machines at the same time. It writes rows to the same MySQL table and then reports
how many actually landed. The point is to replace "SQLite locking is risky" with a measured result on
this fleet's real topology: a Windows seat and a Linux seat writing simultaneously.

Usage:
    python test_concurrency.py --seat kilo-test --rows 200
    python test_concurrency.py --claim-test --rows 20     # atomic-claim test instead
"""
import argparse
import os
import sys
import threading
import time

import pymysql

DB = "ejaguiar1_stocks"


def connect():
    pw = os.environ.get("COORD_PW")
    if not pw:
        sys.exit("COORD_PW not set")
    return pymysql.connect(host="mysql.50webs.com", user=DB, password=pw, database=DB,
                           connect_timeout=20, autocommit=False, charset="utf8mb4")


def write_rows(seat, rows):
    """Each row is its own committed transaction, which is what an agent actually does."""
    ok = err = 0
    errors = []
    t0 = time.time()
    for i in range(rows):
        try:
            c = connect()
            cur = c.cursor()
            cur.execute("""INSERT INTO agent_finding
                           (seat, repo, kind, claim_text, evidence_path, value_num, value_unit)
                           VALUES (%s, %s, 'measurement', %s, %s, %s, 'concurrency-test')""",
                        (seat, "concurrency-test", f"row {i} from {seat} on {os.uname().sysname if hasattr(os,'uname') else os.name}",
                         "test_concurrency.py", i))
            c.commit()
            ok += 1
            c.close()
        except Exception as e:
            err += 1
            errors.append(str(e)[:80])
    dt = time.time() - t0
    print(f"{seat}: ok={ok} err={err} in {dt:.2f}s ({ok/max(dt,0.001):.0f} writes/s)")
    if errors:
        print("  first errors:", errors[:3])


def claim_test(rows):
    """N seats race for the same task. Exactly one must win. This is the test that matters for a fleet:
    two agents picking up the same unit of work is worse than a slow database."""
    c = connect()
    cur = c.cursor()
    cur.execute("""INSERT INTO agent_task (repo, slug, title, status)
                   VALUES ('concurrency-test', 'claim-race', 'atomic claim race', 'open')
                   ON DUPLICATE KEY UPDATE status='open', claimed_by=NULL, claimed_at=NULL, lease_until=NULL""")
    c.commit()
    cur.execute("SELECT id FROM agent_task WHERE repo='concurrency-test' AND slug='claim-race'")
    task_id = cur.fetchone()[0]
    c.close()

    wins = []
    lock = threading.Lock()

    def attempt(n):
        try:
            c = connect()
            cur = c.cursor()
            # the claim is a single UPDATE guarded by the current state, so the database decides the winner
            cur.execute("""UPDATE agent_task
                           SET status='claimed', claimed_by=%s, claimed_at=NOW(),
                               lease_until=NOW() + INTERVAL 30 MINUTE
                           WHERE id=%s AND (status='open'
                                            OR (status='claimed' AND lease_until < NOW()))""",
                        (f"racer-{n}", task_id))
            c.commit()
            if cur.rowcount == 1:
                with lock:
                    wins.append(f"racer-{n}")
            c.close()
        except Exception as e:
            with lock:
                wins.append(f"ERROR racer-{n}: {str(e)[:50]}")

    threads = [threading.Thread(target=attempt, args=(i,)) for i in range(rows)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    c = connect()
    cur = c.cursor()
    cur.execute("SELECT claimed_by, status FROM agent_task WHERE id=%s", (task_id,))
    row = cur.fetchone()
    c.close()
    print(f"claim race: {rows} concurrent attempters -> winners={len(wins)} {wins}")
    print(f"task row now: claimed_by={row[0]} status={row[1]}")
    print("EXPECTED: exactly 1 winner" if len(wins) == 1 else "FAILED: more than one winner")


def count_rows():
    c = connect()
    cur = c.cursor()
    cur.execute("SELECT COUNT(*) FROM agent_finding WHERE repo='concurrency-test'")
    n = cur.fetchone()[0]
    cur.execute("SELECT seat, COUNT(*) FROM agent_finding WHERE repo='concurrency-test' GROUP BY seat")
    per = cur.fetchall()
    c.close()
    print(f"TOTAL rows in agent_finding for the test repo: {n}")
    for seat, k in per:
        print(f"   {seat}: {k}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seat", default="unknown")
    ap.add_argument("--rows", type=int, default=100)
    ap.add_argument("--claim-test", action="store_true")
    ap.add_argument("--count", action="store_true")
    a = ap.parse_args()
    if a.count:
        count_rows()
    elif a.claim_test:
        claim_test(a.rows)
    else:
        write_rows(a.seat, a.rows)
