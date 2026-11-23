#!/usr/bin/env python3
"""G5 (owner H) — alert on [SILENT] streaks. G4 — who actually PRODUCED something.

The problem this exists for, stated as it actually happened: on 2026-11-22 the IDE agents stopped at
08:17 and nobody noticed for eight hours. The lesson in the TODO is right —

    "an agent that reports nothing for 6 ticks is probably stuck, not calm."

An agent that reports nothing looks exactly like an agent that is working on something long. The
only way to tell them apart without watching the screen is to measure the *record*: did a tick fire,
did it report, and did anything measurable appear as a result.

Four distinct failure modes, because they need different fixes:

  NEVER_RAN        enabled and scheduled, but `last_run_at` is null. The scheduler or the job
                   definition is broken, not the agent. (Found in the wild: rustdesk-antigravity-watch
                   was enabled hourly and had never fired.)
  OVERDUE          last run older than 2x its own interval. Something stopped firing.
  SILENT_STREAK    N consecutive runs that reported nothing ([SILENT], empty, or unchanged output).
                   The agent is running and producing no information.
  FAILING_STREAK   N consecutive non-ok run statuses.

And G4's question — who produced something measurable — is answered separately by looking for
artifacts (commits) inside each job's window, so "produced" means "changed the repo", not "said
something".

  python observability/agent_liveness.py                # report + exit 1 if any alert
  python observability/agent_liveness.py --json         # machine-readable only
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERMES = Path.home() / "AppData" / "Local" / "hermes"
CRON = HERMES / "cron"
JOBS = CRON / "jobs.json"
EXEC_DB = CRON / "executions.db"
OUTPUT = CRON / "output"

# Watchdog thresholds. These are policy choices, stated so they can be argued with.
WINDOW_HOURS = 24.0          # set by --window-hours; 168 for the weekly G4 digest
SILENT_STREAK_ALERT = 6      # the TODO's number
FAILING_STREAK_ALERT = 3
OVERDUE_FACTOR = 2.0

INTERVAL_RE = re.compile(r"^every\s+(\d+)\s*(m|min|h|hour)s?$", re.I)

# The engine records a successful run as "completed", not "ok". Counting "completed" as a failure
# reported a 12-run failing streak on a job whose own failure_streak was 0 — an alerting tool that
# cries wolf is worse than no tool, so the success set is explicit.
OK_STATUSES = {"ok", "success", "completed", "done", "running", "skipped"}


def parse_interval_minutes(schedule) -> float | None:
    """The job's own cadence in minutes, or None when it is not a fixed interval.

    jobs.json stores schedule as a dict: {"kind":"interval","minutes":60,"display":"every 60m"}
    or {"kind":"cron","expr":"40 */4 * * *",...}. A cron expression is deliberately NOT converted
    here: turning '40 */4 * * *' into a single interval would misreport the overdue test, and a
    wrong interval produces false NEVER_RAN/OVERDUE alerts, which is worse than no alert.
    """
    if isinstance(schedule, dict):
        if schedule.get("kind") == "interval" and schedule.get("minutes"):
            try:
                return float(schedule["minutes"])
            except (TypeError, ValueError):
                return None
        disp = schedule.get("display") or ""
    else:
        disp = schedule or ""
    m = INTERVAL_RE.match(str(disp).strip())
    if m:
        n = float(m.group(1))
        return n * 60.0 if m.group(2).lower().startswith("h") else n
    return None


def load_jobs() -> list[dict]:
    if not JOBS.exists():
        return []
    raw = json.loads(JOBS.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        # jobs.json has been seen as {"jobs": [...]} and as {job_id: {...}}
        items = raw.get("jobs")
        if isinstance(items, list):
            return items
        return [dict(v, job_id=v.get("job_id", k)) for k, v in raw.items()
                if isinstance(v, dict)]
    return raw


def is_watcher(job: dict) -> bool:
    name = (job.get("name") or "").lower()
    return any(tok in name for tok in ("watch", "-cycle", "burst", "progress", "monitor"))


def executions_for(job_id: str) -> list[dict]:
    if not EXEC_DB.exists():
        return []
    try:
        con = sqlite3.connect(f"file:{EXEC_DB}?mode=ro", uri=True, timeout=5)
        con.row_factory = sqlite3.Row
        rows = con.execute(
            "select job_id,status,started_at,finished_at,error,delivery_outcome "
            "from executions where job_id=? order by coalesce(finished_at, started_at) desc limit 40",
            (job_id,)).fetchall()
        con.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def run_outputs(job_id: str) -> list[tuple[str, str]]:
    """Newest-first (filename, body) for a job's recorded runs."""
    d = OUTPUT / job_id
    if not d.is_dir():
        return []
    out = []
    for f in sorted(d.glob("*.md"), reverse=True):
        try:
            out.append((f.name, f.read_text(encoding="utf-8", errors="replace")))
        except Exception:
            continue
    return out


def body_of(md: str) -> str:
    """The agent's own answer, not the echoed prompt."""
    for marker in ("## Response", "## Final Response", "## Output"):
        i = md.find(marker)
        if i >= 0:
            return md[i + len(marker):].strip()
    # no marker: fall back to the tail after the last '---'
    parts = md.rsplit("\n---\n", 1)
    return (parts[1] if len(parts) > 1 else md).strip()


def is_silent(md: str) -> bool:
    b = body_of(md)
    if not b:
        return True
    low = b.lower()
    if "[silent]" in low or low in ("silent", "nothing to report"):
        return True
    # a response that only restates status with no change is indistinguishable from silence
    if len(b) < 40:
        return True
    return False


def commits_in_window(since: datetime, workdir: str | None) -> int:
    """G4: did anything measurable appear? Commits, not words."""
    if not workdir or not Path(workdir).exists():
        return 0
    try:
        r = subprocess.run(
            ["git", "-C", workdir, "log", "--since", since.isoformat(),
             "--oneline", "--no-merges"],
            capture_output=True, text=True, timeout=20)
        return len([l for l in r.stdout.splitlines() if l.strip()])
    except Exception:
        return 0


def analyse(job: dict, now: datetime) -> dict:
    jid = job.get("id") or job.get("job_id") or "?"
    name = job.get("name") or jid
    sched = job.get("schedule") or ""
    interval = parse_interval_minutes(sched)
    execs = executions_for(jid)
    outs = run_outputs(jid)

    last_run_raw = job.get("last_run_at")
    last_run = None
    if last_run_raw:
        try:
            last_run = datetime.fromisoformat(str(last_run_raw))
            if last_run.tzinfo is None:
                last_run = last_run.replace(tzinfo=now.astimezone().tzinfo)
        except Exception:
            last_run = None

    silent = 0
    for _, md in outs[:20]:
        if is_silent(md):
            silent += 1
        else:
            break

    failing = int(job.get("failure_streak") or 0)
    if not failing:
        for e in execs[:20]:
            if (e.get("status") or "").lower() not in OK_STATUSES:
                failing += 1
            else:
                break

    enabled = bool(job.get("enabled", True))
    overdue_min = None
    if interval and last_run:
        overdue_min = round((now - last_run).total_seconds() / 60.0, 1)

    state = (job.get("state") or "").lower()
    retired = (not enabled) or state in ("completed", "paused", "cancelled")

    alerts = []
    # NEVER_RAN and OVERDUE only mean something for a job that is supposed to be firing
    if not retired and last_run is None and interval:
        alerts.append("NEVER_RAN")
    if not retired and interval and overdue_min is not None and overdue_min > interval * OVERDUE_FACTOR:
        alerts.append("OVERDUE")
    if silent >= SILENT_STREAK_ALERT:
        alerts.append("SILENT_STREAK")
    if failing >= FAILING_STREAK_ALERT:
        alerts.append("FAILING_STREAK")

    produced = commits_in_window(now - timedelta(hours=WINDOW_HOURS), job.get("workdir"))

    return {
        "job_id": jid, "name": name,
        "schedule": (sched.get("display") if isinstance(sched, dict) else str(sched)),
        "interval_minutes": interval, "enabled": enabled,
        "last_run_at": last_run_raw, "minutes_since_last_run": overdue_min,
        "ticks_recorded": len(outs), "consecutive_silent": silent,
        "consecutive_failing": failing,
        "commits_24h": produced,
        "produced_something": produced > 0,
        "alerts": alerts,
        "status": ("ALERT" if alerts else
                   "RETIRED" if retired else
                   "ACTIVE" if produced else "SILENT_BUT_FIRING"),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--window-hours", type=float, default=24.0,
                    help="artifact window; 168 for the weekly G4 digest")
    ap.add_argument("--alert-only", action="store_true",
                    help="print ONLY when there is an alert (watchdog pattern: no output = "
                         "healthy, so a cron job that sends nothing means nothing is wrong)")
    a = ap.parse_args()

    global WINDOW_HOURS
    now = datetime.now(timezone.utc)
    WINDOW_HOURS = a.window_hours
    jobs = [j for j in load_jobs() if is_watcher(j)]
    if not jobs:
        print("no watcher jobs found", file=sys.stderr)
        return 2

    rows = [analyse(j, now) for j in jobs]
    order = {"ALERT": 0, "SILENT_BUT_FIRING": 1, "ACTIVE": 2}
    rows.sort(key=lambda r: (order.get(r["status"], 9), r["name"]))

    alerts = [r for r in rows if r["alerts"]]
    report = {
        "generated_utc": now.isoformat(timespec="seconds"),
        "n_watchers": len(rows),
        "n_alerts": len(alerts),
        "thresholds": {"silent_streak": SILENT_STREAK_ALERT,
                       "failing_streak": FAILING_STREAK_ALERT,
                       "overdue_factor": OVERDUE_FACTOR},
        "watchers": rows,
    }

    if a.json:
        print(json.dumps(report, indent=1, default=str))
        return 1 if alerts else 0

    if a.alert_only:
        # watchdog: stay silent unless something is actually wrong
        if not alerts:
            return 0
        lines = [f"AGENT LIVENESS ALERT {now:%Y-%m-%d %H:%M}Z: {len(alerts)} of {len(rows)} "
                 f"watchers need attention"]
        for r in alerts:
            lines.append(f"  {r['name']} [{r['schedule']}] -> {', '.join(r['alerts'])}"
                         + (f" (last run {r['minutes_since_last_run']:.0f}m ago)"
                            if r['minutes_since_last_run'] is not None else " (never ran)"))
        quiet = [r for r in rows if r["status"] == "SILENT_BUT_FIRING"]
        if quiet:
            lines.append("  firing but producing nothing: " + ", ".join(
                f"{r['name']} ({r['consecutive_silent']} silent ticks)" for r in quiet))
        print("\n".join(lines))
        return 1

    print("=" * 92)
    print(f"AGENT LIVENESS — {len(rows)} watchers, {len(alerts)} alert(s) — {now:%Y-%m-%d %H:%M}Z")
    print("=" * 92)
    print(f"{'watcher':34s} {'sched':>10s} {'last run':>11s} {'silent':>7s} "
          f"{'failing':>8s} {'commits':>8s}  status")
    for r in rows:
        last = "never" if r["last_run_at"] is None else (
            f"{r['minutes_since_last_run']:.0f}m ago" if r["minutes_since_last_run"] is not None
            else "?")
        print(f"{r['name'][:34]:34s} {str(r['schedule'])[:10]:>10s} {last:>11s} "
              f"{r['consecutive_silent']:>7d} {r['consecutive_failing']:>8d} "
              f"{r['commits_24h']:>8d}  {r['status']}")

    if alerts:
        print("\nALERTS")
        for r in alerts:
            print(f"  {r['name']}  ->  {', '.join(r['alerts'])}")
            if "NEVER_RAN" in r["alerts"]:
                print(f"     enabled={r['enabled']} schedule={r['schedule']} "
                      f"but last_run_at is null: the job has never fired")
            if "OVERDUE" in r["alerts"]:
                print(f"     {r['minutes_since_last_run']:.0f}m since last run vs "
                      f"{r['interval_minutes']:.0f}m interval")
            if "SILENT_STREAK" in r["alerts"]:
                print(f"     {r['consecutive_silent']} consecutive runs reported nothing "
                      f"(threshold {SILENT_STREAK_ALERT})")
            if "FAILING_STREAK" in r["alerts"]:
                print(f"     {r['consecutive_failing']} consecutive non-ok runs")

    quiet = [r for r in rows if r["status"] == "SILENT_BUT_FIRING"]
    if quiet:
        print(f"\nFIRING BUT PRODUCING NOTHING ({len(quiet)}): "
              f"{', '.join(r['name'] for r in quiet)}")
        print("  These look identical to a busy agent. That is the whole reason this script exists.")

    print(f"\nexit {'1 (alerts)' if alerts else '0 (clean)'}")
    return 1 if alerts else 0


if __name__ == "__main__":
    sys.exit(main())
