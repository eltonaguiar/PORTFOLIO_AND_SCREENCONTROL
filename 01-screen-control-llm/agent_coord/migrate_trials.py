"""Migrate the three forked trial_ledger.db files into agent_trial, keeping provenance.

The fork happened because trial_log.py takes the database path as argv[1] and dsr.py defaults it to a
bare relative name, so each cron run wrote its own ledger from whatever directory it started in. Three
copies survive with 2, 13 and 6 rows. They are merged here into one append-only table, and each row keeps
source_path so nobody has to guess which fork a trial came from.

Idempotent: the unique key (run_id, family, variant, seat) means a re-run inserts nothing new.
"""
import glob
import os
import sqlite3
import sys

import pymysql

DB = "ejaguiar1_stocks"
REPO = r"C:/Users/zerou/repos/antigravity_review"
PATTERNS = [
    "CONTEST/trial_ledger.db",
    "CONTEST/tools/trial_ledger.db",
    "CONTEST/tools/reports/trial_ledger.db",
]


def read_fork(path):
    if not os.path.exists(path):
        return []
    try:
        c = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=10)
        cur = c.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        if not any(r[0] == "trials" for r in cur.fetchall()):
            return []
        cur.execute("PRAGMA table_info(trials)")
        cols = [r[1] for r in cur.fetchall()]
        cur.execute("SELECT * FROM trials")
        rows = cur.fetchall()
        c.close()
        return [dict(zip(cols, r)) for r in rows]
    except Exception as e:
        print(f"  {path}: read error {str(e)[:70]}")
        return []


def pick(row, *names, default=None):
    for n in names:
        if n in row and row[n] is not None:
            return row[n]
    return default


def main():
    pw = os.environ.get("COORD_PW") or sys.exit("COORD_PW not set")
    con = pymysql.connect(host="mysql.50webs.com", user=DB, password=pw, database=DB,
                          connect_timeout=20, autocommit=True, charset="utf8mb4")
    cur = con.cursor()
    total = inserted = 0
    for rel in PATTERNS:
        path = os.path.join(REPO, rel)
        rows = read_fork(path)
        print(f"{rel}: {len(rows)} rows")
        for r in rows:
            total += 1
            run_id = str(pick(r, "run_id", "run", default="unknown"))
            family = str(pick(r, "family", "strategy", default="unknown"))
            variant = str(pick(r, "variant", "name", default="unknown"))
            seat = "migrated"
            try:
                cur.execute("""INSERT INTO agent_trial
                               (run_id, family, variant, sharpe_is, sharpe_oos, kept, cost_bps, seat, source_path)
                               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                               ON DUPLICATE KEY UPDATE id=id""",
                            (run_id[:64], family[:96], variant[:96],
                             pick(r, "sharpe_is", "sharpe"), pick(r, "sharpe_oos", "sharpe_oos"),
                             int(pick(r, "kept", default=0) or 0), pick(r, "cost_bps"),
                             seat, rel))
                inserted += cur.rowcount
            except Exception as e:
                print(f"   insert failed: {str(e)[:80]}")
    print(f"\nread {total} rows across {len(PATTERNS)} forks, inserted {inserted} new")
    cur.execute("SELECT family, trials, kept, seats FROM v_trial_census ORDER BY trials DESC")
    print("\ntrial census (the denominator multiple-testing actually needs):")
    for r in cur.fetchall():
        print(f"   {r[0]}: {r[1]} trials, {r[2]} kept, {r[3]} seat(s)")
    cur.execute("SELECT COUNT(*) FROM agent_trial")
    print(f"\nagent_trial total rows: {cur.fetchone()[0]}")
    con.close()


if __name__ == "__main__":
    main()
