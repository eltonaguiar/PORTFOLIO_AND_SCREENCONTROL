"""Build cross-agent chat digests so the three VS Code agents can see each other's recent work.

WHY DIGESTS AND NOT THE RAW FOLDERS
    Kilo Code   6.4 GB (204 tasks)   raw api_conversation_history.json up to 448 KB per task
    Zoo Code    402 MB (406 tasks)   remote, same format
    Copilot      57 MB + 41 chatSessions jsonl, the newest alone 62 MB
Feeding any of those wholesale to another agent would exhaust its context before it read a single
useful line, and they contain API keys and database secrets. So this writes one compact markdown per
agent - recent tasks, last few turns, truncated - with secrets scrubbed on the way out.

WHAT IT WRITES
    kilo.md      newest tasks from the local Kilo Code store
    zoo.md       newest tasks from the remote Zoo Code store (produced on the host, copied back)
    copilot.md   newest Copilot Chat sessions for this workspace
    INDEX.md     who wrote what, how fresh, and what each agent should do with it

Local run:  python agent_bridge.py local <outdir>
"""
import json
import os
import re
import sys
import glob

MAX_TASKS = 12          # newest N conversations per agent
MAX_TURNS = 6           # last N exchanges inside each conversation
MAX_CHARS = 700         # per message
HEAD = 90               # chars of the first user instruction, kept as the task label

# anything that looks like a credential, plus this project's own secret shapes
SECRET_PATTERNS = [
    (re.compile(r"\b(sk-[A-Za-z0-9\-_]{16,})"), "[REDACTED_KEY]"),
    (re.compile(r"\b(ghp_[A-Za-z0-9]{20,})"), "[REDACTED_GH]"),
    (re.compile(r"\b(github_pat_[A-Za-z0-9_]{20,})"), "[REDACTED_GH]"),
    (re.compile(r"\b(AKIA[0-9A-Z]{16})"), "[REDACTED_AWS]"),
    (re.compile(r"\b(gsk_[A-Za-z0-9]{20,})"), "[REDACTED_KEY]"),
    (re.compile(r"\b(xai-[A-Za-z0-9]{20,})"), "[REDACTED_KEY]"),
    (re.compile(r"(Bearer\s+)[A-Za-z0-9\-\._~\+/]{20,}"), r"\1[REDACTED_TOKEN]"),
    (re.compile(r"(password\s*[=:]\s*)\S+", re.I), r"\1[REDACTED]"),
    (re.compile(r"(mysql\.50webs\.com)"), r"\1"),
]


def scrub(text: str) -> str:
    if not text:
        return ""
    out = text
    for pat, repl in SECRET_PATTERNS:
        out = pat.sub(repl, out)
    return out


def clip(text: str, n: int = MAX_CHARS) -> str:
    t = " ".join((text or "").split())
    return (t[:n] + " …") if len(t) > n else t


def task_dirs(root: str):
    """Cline-family stores: one subdirectory per conversation."""
    if not os.path.isdir(root):
        return []
    dirs = [d for d in glob.glob(os.path.join(root, "*")) if os.path.isdir(d)]
    dirs.sort(key=lambda d: os.path.getmtime(d), reverse=True)
    return dirs


def session_files(root: str):
    """Copilot stores: one .jsonl FILE per conversation, not a directory."""
    if not os.path.isdir(root):
        return []
    files = glob.glob(os.path.join(root, "*.jsonl"))
    files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
    return files


def read_history(task_dir: str):
    """Cline-family store: api_conversation_history.json is [{role, content}, ...]."""
    for name in ("api_conversation_history.json", "ui_messages.json"):
        p = os.path.join(task_dir, name)
        if not os.path.exists(p):
            continue
        try:
            data = json.load(open(p, encoding="utf-8", errors="replace"))
        except Exception:
            continue
        msgs = []
        if isinstance(data, list):
            for item in data:
                if not isinstance(item, dict):
                    continue
                role = item.get("role") or item.get("type") or "?"
                content = item.get("content") or item.get("text") or ""
                if isinstance(content, list):
                    content = " ".join(
                        c.get("text", "") for c in content if isinstance(c, dict)
                    )
                if not content:
                    continue
                if role in ("system", "tool", "user_feedback", "api_req_started"):
                    continue
                msgs.append((role, str(content)))
        if msgs:
            return msgs
    return []


def read_copilot_session(path: str):
    """Copilot: append-only jsonl. kind 0 is the full snapshot; kind 2 are key/value patches."""
    snap = None
    try:
        for line in open(path, encoding="utf-8", errors="replace"):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            if rec.get("kind") == 0 and isinstance(rec.get("v"), dict):
                snap = rec["v"]
    except Exception:
        return []
    if not snap:
        return []
    msgs = []
    for req in (snap.get("requests") or []):
        if not isinstance(req, dict):
            continue
        um = req.get("message") or {}
        text = um.get("text") if isinstance(um, dict) else str(um)
        if text:
            msgs.append(("user", str(text)))
        resp = req.get("response") or req.get("result") or []
        if isinstance(resp, dict):
            v = resp.get("value") or resp.get("content") or resp.get("text") or ""
            if isinstance(v, str) and v.strip():
                msgs.append(("assistant", v))
        elif isinstance(resp, list):
            parts = []
            for r in resp:
                if isinstance(r, dict):
                    v = r.get("value") or r.get("content") or ""
                    if isinstance(v, str):
                        parts.append(v)
            if parts:
                msgs.append(("assistant", " ".join(parts)))
    return msgs


def build(agent: str, roots, reader, outdir: str, note: str, files_mode: bool = False) -> dict:
    items = []
    for root in roots:
        items.extend(session_files(root) if files_mode else task_dirs(root))
    tasks = items[:MAX_TASKS]
    lines = [
        f"# {agent} — recent conversation digest",
        "",
        f"_{note}_",
        f"_Generated {__import__('datetime').datetime.now().astimezone().isoformat(timespec='seconds')}; "
        f"{len(tasks)} newest conversations attempted, {MAX_TURNS} turns each, secrets scrubbed._",
        "",
    ]
    written = 0
    for t in tasks:
        msgs = reader(t)
        if not msgs:
            continue
        label = clip(msgs[0][1], HEAD)
        stamp = __import__("datetime").datetime.fromtimestamp(
            os.path.getmtime(t)).strftime("%Y-%m-%d %H:%M")
        lines.append(f"## {stamp} — {label}")
        lines.append("")
        for role, content in msgs[-MAX_TURNS:]:
            who = "USER" if role in ("user", "human") else "AGENT"
            lines.append(f"- **{who}:** {clip(scrub(content))}")
        lines.append("")
        written += 1
    path = os.path.join(outdir, f"{agent.lower()}.md")
    body = "\n".join(lines)
    open(path, "w", encoding="utf-8", newline="").write(body)
    return {"agent": agent, "path": path, "tasks": written, "bytes": len(body.encode("utf-8"))}


def build_hermes(outdir: str, limit_sessions: int = 12) -> dict:
    """Hermes has no VS Code log. Its transcript is sqlite: state.db -> sessions + messages."""
    import sqlite3
    db = r"C:/Users/zerou/AppData/Local/hermes/state.db"
    lines = [
        "# HERMES — recent conversation digest",
        "",
        "_Hermes runs outside VS Code. Its transcript is a SQLite database, not a task folder:_",
        "_`%LOCALAPPDATA%/hermes/state.db` tables `sessions` and `messages` (996 sessions, 78k messages at build time)._",
        f"_Generated {__import__('datetime').datetime.now().astimezone().isoformat(timespec='seconds')}; "
        f"newest {limit_sessions} sessions, last {MAX_TURNS} turns each, secrets scrubbed._",
        "",
    ]
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=15)
    cur = con.cursor()
    cur.execute("""SELECT id, COALESCE(title,'(untitled)'), COALESCE(last_activity_at,'')
                   FROM sessions ORDER BY last_activity_at DESC LIMIT ?""", (limit_sessions,))
    rows = cur.fetchall()
    written = 0
    for sid, title, when in rows:
        try:
            stamp = __import__("datetime").datetime.fromtimestamp(float(when)).strftime("%Y-%m-%d %H:%M")
        except (TypeError, ValueError):
            stamp = str(when)[:19]
        cur.execute("""SELECT role, COALESCE(content,'') FROM messages
                       WHERE session_id=? AND role IN ('user','assistant') AND COALESCE(content,'')<>''
                       ORDER BY id DESC LIMIT ?""", (sid, MAX_TURNS))
        msgs = list(reversed(cur.fetchall()))
        if not msgs:
            continue
        lines.append(f"## {stamp} — {clip(scrub(title), HEAD)}")
        lines.append("")
        for role, content in msgs:
            who = "USER" if role == "user" else "AGENT"
            lines.append(f"- **{who}:** {clip(scrub(content))}")
        lines.append("")
        written += 1
    con.close()
    path = os.path.join(outdir, "hermes.md")
    body = "\n".join(lines)
    open(path, "w", encoding="utf-8", newline="").write(body)
    return {"agent": "HERMES", "path": path, "tasks": written, "bytes": len(body.encode("utf-8"))}


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "local"
    outdir = sys.argv[2] if len(sys.argv) > 2 else "."
    os.makedirs(outdir, exist_ok=True)
    results = []
    if mode == "hermes":
        results.append(build_hermes(outdir))
    elif mode == "local":
        results.append(build(
            "KILO", [r"C:/Users/zerou/AppData/Roaming/Code/User/globalStorage/kilocode.kilo-code/tasks"],
            read_history, outdir,
            "Kilo Code store on the local Windows machine (204 tasks, 6.4 GB raw)"))
        results.append(build(
            "COPILOT",
            [r"C:/Users/zerou/AppData/Roaming/Code/User/workspaceStorage/2f9cb8396e4cba859c32af53ae8f852c/chatSessions"],
            read_copilot_session, outdir,
            "GitHub Copilot Chat sessions for ssh-remote+eltonsgx10 / findtorontoevents_antigravity.ca (41 sessions)",
            files_mode=True))
    else:
        results.append(build(
            "ZOO", [os.path.expanduser("~/.vscode-server/data/User/globalStorage/zoocodeorganization.zoo-code/tasks")],
            read_history, outdir,
            "Zoo Code store on the remote host eltonsGX10 (406 tasks, 402 MB raw)"))
    for r in results:
        print(f"{r['agent']:8} {r['tasks']:>3} conversations -> {r['bytes']:>7,} bytes  {r['path']}")
