"""read_peer.py — print a coworker's most recent conversation, read out of the database bridge.

An agent does not need the peer's folder mounted to read it, and never has to load a 65 MB file: this
selects one row, decompresses it, and prints a bounded tail.
"""
import argparse, gzip, os, sys, pymysql

def conn():
    pw = os.environ.get("COORD_PW") or sys.exit("COORD_PW not set")
    return pymysql.connect(host="mysql.50webs.com", user="ejaguiar1_stocks", password=pw,
                           database="ejaguiar1_stocks", connect_timeout=30, autocommit=True, charset="utf8mb4")

ap = argparse.ArgumentParser()
ap.add_argument("--agent", required=True, choices=["kilo","zoo","copilot","hermes"])
ap.add_argument("--index", type=int, default=0, help="0 = newest")
ap.add_argument("--chars", type=int, default=6000)
ap.add_argument("--list", action="store_true")
a = ap.parse_args()
c = conn(); cur = c.cursor()
if a.list:
    cur.execute("""SELECT session_key, bytes_raw, bytes_gz, captured_at FROM agent_log
                   WHERE seat=%s ORDER BY captured_at DESC""", (a.agent,))
    for k, raw, gz, when in cur.fetchall():
        print(f"  {when}  {str(k)[:46]:<48} raw {int(raw)/1e6:>6.2f} MB  gz {int(gz)/1e6:>5.2f} MB")
else:
    cur.execute("""SELECT session_key, content_gz, captured_at FROM agent_log
                   WHERE seat=%s ORDER BY captured_at DESC LIMIT 1 OFFSET %s""", (a.agent, a.index))
    row = cur.fetchone()
    if not row:
        sys.exit(f"no log stored for {a.agent}")
    text = gzip.decompress(row[1]).decode("utf-8", errors="replace")
    print(f"=== {a.agent} / {row[0]} / stored {row[2]} / {len(text)} chars ===")
    print(text[-a.chars:])
c.close()
