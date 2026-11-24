"""sync_logs.py — share actual conversation logs through the database bridge.

The bridge is MySQL: both the Windows box and eltonsGX10 reach mysql.50webs.com with the credentials in
~/dbpasses.txt, which is why this works from either side without a mount, an SMB share or an SSHFS install.

DESIGN CONSTRAINTS, all measured before writing this:
  Kilo     newest 10 conversations = 1.8 MB     (whole store 5.9 GB, so never sync it all)
  Zoo      newest 10 = 42 MB                    (whole store 401 MB)
  Copilot  newest 5 = 89 MB, because ONE session is 64.6 MB
So: a per-file cap (default 16 MB raw) skips the outliers instead of silently blowing up the row, and every
row is gzipped. JSON conversation logs compress hard.

Every row is scrubbed of credential-shaped strings BEFORE it is stored. Logs contain tool output, and tool
output contains keys. One shared store that leaks a key to four agents is worse than no store.

Usage:
    python sync_logs.py --agent kilo    --limit 10
    python sync_logs.py --agent copilot --limit 5
    python sync_logs.py --agent zoo     --limit 10      # run ON the linux host
    python sync_logs.py --agent hermes  --limit 5
    python sync_logs.py --report                        # sizes, from either side
"""
import argparse
import glob
import gzip
import hashlib
import json
import os
import re
import sqlite3
import sys

import pymysql

DB = "ejaguiar1_stocks"
MAX_RAW_MB = 16

SECRETS = [
    (re.compile(r"\b(sk[-_][A-Za-z0-9\-_]{16,})"), "[REDACTED_KEY]"),
    (re.compile(r"\b(ghp_[A-Za-z0-9]{20,})"), "[REDACTED_GH]"),
    (re.compile(r"\b(github_pat_[A-Za-z0-9_]{20,})"), "[REDACTED_GH]"),
    (re.compile(r"\b(AKIA[0-9A-Z]{16})"), "[REDACTED_AWS]"),
    (re.compile(r"\b(AIza[A-Za-z0-9\-_]{30,})"), "[REDACTED_GCP]"),
    (re.compile(r"\b(gsk_[A-Za-z0-9]{20,})"), "[REDACTED_KEY]"),
    (re.compile(r"\b(xai-[A-Za-z0-9]{20,})"), "[REDACTED_KEY]"),
    (re.compile(r"(Bearer\s+)[A-Za-z0-9\-\._~\+/]{20,}"), r"\1[REDACTED]"),
    (re.compile(r"(password\s*[=:]\s*)\S+", re.I), r"\1[REDACTED]"),
]

DDL = """
CREATE TABLE IF NOT EXISTS agent_log (
  id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  seat         VARCHAR(32)  NOT NULL,
  session_key  VARCHAR(128) NOT NULL,
  captured_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  source_path  VARCHAR(512) NULL,
  bytes_raw    INT UNSIGNED NOT NULL,
  bytes_gz     INT UNSIGNED NOT NULL,
  sha256       CHAR(64)     NOT NULL,
  content_gz   MEDIUMBLOB   NOT NULL,
  UNIQUE KEY uq_log (seat, sha256),
  KEY k_seat_cap (seat, captured_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE OR REPLACE VIEW v_log_census AS
SELECT seat, COUNT(*) AS sessions, SUM(bytes_raw) AS raw_bytes, SUM(bytes_gz) AS gz_bytes,
       ROUND(SUM(bytes_gz)/1024/1024, 2) AS gz_mb, MIN(captured_at) AS oldest, MAX(captured_at) AS newest
FROM agent_log GROUP BY seat;
"""


def conn():
    pw = os.environ.get("COORD_PW") or sys.exit("COORD_PW not set")
    return pymysql.connect(host="mysql.50webs.com", user=DB, password=pw, database=DB,
                           connect_timeout=30, autocommit=True, charset="utf8mb4",
                           max_allowed_packet=64 * 1024 * 1024)


def scrub(text):
    for pat, repl in SECRETS:
        text = pat.sub(repl, text)
    return text


def read_bytes(path):
    """One conversation, as bytes. Handles both a task directory and a single jsonl file."""
    if os.path.isfile(path):
        return open(path, "rb").read()
    parts = []
    for d, _, files in os.walk(path):
        for f in sorted(files):
            if f.endswith((".json", ".jsonl")) and f in (
                    "api_conversation_history.json", "ui_messages.json", "task_metadata.json") or f.endswith(".jsonl"):
                try:
                    parts.append(open(os.path.join(d, f), "rb").read())
                except OSError:
                    pass
    return b"\n".join(parts)


def ingest(agent, items, con):
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=%s AND table_name='agent_log'",
                (DB,))
    if not cur.fetchone()[0]:
        for stmt in DDL.split(";"):
            if stmt.strip():
                cur.execute(stmt)
        print("agent_log table and v_log_census view created")
    stored = skipped = 0
    for path in items:
        try:
            raw = read_bytes(path)
        except Exception as e:
            print(f"  skip {os.path.basename(path)[:40]}: {str(e)[:50]}")
            continue
        if not raw:
            continue
        if len(raw) > MAX_RAW_MB * 1024 * 1024:
            print(f"  SKIP {os.path.basename(path)[:42]} — {len(raw)/1e6:.1f} MB exceeds the "
                  f"{MAX_RAW_MB} MB cap (a single Copilot session can be 65 MB)")
            skipped += 1
            continue
        text = raw.decode("utf-8", errors="replace")
        clean = scrub(text).encode("utf-8")
        gz = gzip.compress(clean, 6)
        sha = hashlib.sha256(clean).hexdigest()
        cur.execute("""INSERT INTO agent_log (seat, session_key, source_path, bytes_raw, bytes_gz, sha256, content_gz)
                       VALUES (%s,%s,%s,%s,%s,%s,%s)
                       ON DUPLICATE KEY UPDATE id=id""",
                    (agent, os.path.basename(path.rstrip("/\\"))[:128], os.path.basename(path)[:512],
                     len(clean), len(gz), sha, gz))
        if cur.rowcount:
            stored += 1
    print(f"{agent}: stored {stored} conversations, skipped {skipped} over cap")


def hermes_items(limit):
    """Hermes has no task folder. Its transcript is sqlite: state.db -> sessions + messages."""
    import tempfile
    db = r"C:/Users/zerou/AppData/Local/hermes/state.db"
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=15)
    cur = con.cursor()
    cur.execute("""SELECT id, COALESCE(title,''), COALESCE(last_activity_at,0) FROM sessions
                   ORDER BY last_activity_at DESC LIMIT ?""", (limit,))
    out = []
    tmp = tempfile.mkdtemp(prefix="hermes_logs_")
    for sid, title, when in cur.fetchall():
        cur.execute("""SELECT role, COALESCE(content,'') FROM messages
                       WHERE session_id=? AND role IN ('user','assistant') ORDER BY id""", (sid,))
        msgs = [{"role": r, "content": c} for r, c in cur.fetchall()]
        if not msgs:
            continue
        fp = os.path.join(tmp, f"{sid[:48]}.json")
        json.dump({"session": sid, "title": title, "messages": msgs}, open(fp, "w", encoding="utf-8"))
        out.append(fp)
    con.close()
    return out


def new_items(agent, limit):
    if agent == "kilo":
        root = r"C:/Users/zerou/AppData/Roaming/Code/User/globalStorage/kilocode.kilo-code/tasks"
    elif agent == "copilot":
        root = r"C:/Users/zerou/AppData/Roaming/Code/User/workspaceStorage/2f9cb8396e4cba859c32af53ae8f852c/chatSessions"
    elif agent == "zoo":
        root = os.path.expanduser("~/.vscode-server/data/User/globalStorage/zoocodeorganization.zoo-code/tasks")
    elif agent == "hermes":
        return hermes_items(limit)
    else:
        return []
    items = sorted(glob.glob(root + "/*"), key=os.path.getmtime, reverse=True)[:limit]
    return items


def report(con):
    cur = con.cursor()
    cur.execute("""SELECT ROUND(SUM(data_length+index_length)/1024/1024,2) FROM information_schema.tables
                   WHERE table_schema=%s""", (DB,))
    print(f"database total: {cur.fetchone()[0]} MB")
    try:
        cur.execute("SELECT seat, sessions, raw_bytes, gz_bytes, gz_mb, newest FROM v_log_census ORDER BY gz_bytes DESC")
        rows = cur.fetchall()
        if not rows:
            print("agent_log: empty")
        for r in rows:
            print(f"  {r[0]:<10} {r[1]:>4} sessions  raw {float(r[2])/1e6:>7.1f} MB  gz {float(r[3])/1e6:>6.1f} MB  newest {r[5]}")
    except Exception as e:
        print("  agent_log not created yet:", str(e)[:60])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", choices=["kilo", "copilot", "zoo", "hermes"])
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    con = conn()
    if a.report:
        report(con)
    else:
        ingest(a.agent, new_items(a.agent, a.limit), con)
        report(con)
    con.close()
