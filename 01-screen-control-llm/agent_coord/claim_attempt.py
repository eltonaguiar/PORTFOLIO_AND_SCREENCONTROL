"""Pure cross-machine claim race: only attempts the guarded UPDATE, never resets the task.

Run on any number of hosts at once. The total number of reported winners across ALL hosts must be exactly 1.
"""
import os, sys, threading, pymysql

pw = os.environ.get("COORD_PW") or sys.exit("COORD_PW not set")
host_tag = sys.argv[1] if len(sys.argv) > 1 else "unknown"
n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
wins, lock = [], threading.Lock()

def conn():
    return pymysql.connect(host="mysql.50webs.com", user="ejaguiar1_stocks", password=pw,
                           database="ejaguiar1_stocks", connect_timeout=20, autocommit=True, charset="utf8mb4")

def go(i):
    try:
        c = conn(); cur = c.cursor()
        cur.execute("""UPDATE agent_task
                       SET status='claimed', claimed_by=%s, claimed_at=NOW(),
                           lease_until=NOW() + INTERVAL 30 MINUTE
                       WHERE slug=%s AND (status='open' OR (status='claimed' AND lease_until < NOW()))""",
                    (f"{host_tag}-{i}", "claim-race"))
        if cur.rowcount == 1:
            with lock: wins.append(f"{host_tag}-{i}")
        c.close()
    except Exception as e:
        with lock: wins.append(f"ERR {host_tag}-{i}: {str(e)[:40]}")

ts = [threading.Thread(target=go, args=(i,)) for i in range(n)]
[t.start() for t in ts]; [t.join() for t in ts]
print(f"{host_tag}: winners={len(wins)} {wins}")
