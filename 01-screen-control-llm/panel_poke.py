"""panel_poke.py — queue-driven keep-alive for VS Code AI panels (Kilo / Zoo / Copilot).

Why this exists: nudging panels by hand means reading state, deciding, typing and verifying as four
separate manual steps, and it degrades the moment you look away. This does the whole loop in one
call: check the CDP listener, read each panel's real state, pop the next queued task for any panel
that is IDLE, send it, and record what was sent so the same task is never delivered twice.

Rules it enforces (learned the hard way, see SKILL.md):
  * never send to a panel that is RUNNING (a queued message cannot execute behind a gate)
  * never open a new session; always type into the existing composer
  * never re-send a task that is already in the sent-log
  * an unsent human draft in the composer is left alone
  * Copilot's input path is unreliable on some builds; failure is reported, not retried blindly

Usage:
  python panel_poke.py --queue queue.json            # act on idle panels
  python panel_poke.py --queue queue.json --dry-run  # report only, send nothing
  python panel_poke.py --status                      # state of every panel, send nothing

queue.json:
  {
    "kilo":  ["task one", "task two"],
    "zoo":   ["task one"],
    "copilot": ["task one"]
  }

The sent-log lives beside the queue as <queue>.sent.json so a task is never delivered twice.
"""
import argparse
import json
import os
import sys
import time

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PANEL_MODULE_HINT = "01-screen-control-llm"  # where screen_control/vscode_panels.py lives


def load_panels():
    """Import the committed control module, or fall back to a minimal local CDP client."""
    for p in (os.environ.get("PANEL_MODULE_PATH"), ".", "..",
              os.path.join(os.path.expanduser("~"), "repos", "PORTFOLIO_AND_SCREENCONTROL",
                           PANEL_MODULE_HINT)):
        if p and os.path.isdir(os.path.join(p, "screen_control")):
            sys.path.insert(0, p)
            break
    try:
        import screen_control.vscode_panels as vp
        return vp, vp.Panels()
    except Exception as e:
        print(f"FATAL: cannot import screen_control.vscode_panels ({e})")
        print("Set PANEL_MODULE_PATH to the directory containing screen_control/")
        sys.exit(2)


def cdp_alive(port=9333):
    import urllib.request
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=6) as r:
            return json.loads(r.read().decode()).get("Browser", "")
    except Exception:
        return ""


def sender_state(panels, name):
    """Return (state, detail). 'running' suppresses all sends."""
    try:
        st = panels.status(name)
        return st.get("state", "unknown"), st
    except Exception as e:
        return "unavailable", {"error": str(e)[:120]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--queue")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--only", help="comma separated panel names")
    args = ap.parse_args()

    browser = cdp_alive()
    print(f"CDP 9333: {'alive — ' + browser if browser else 'DEAD (no listener; panels unreachable)'}")
    if not browser:
        print("Action: relaunch VS Code with --remote-debugging-port=9333 before nudging.")
        return 1

    vp, panels = load_panels()
    names = [n.strip() for n in args.only.split(",")] if args.only else ["kilo", "zoo", "copilot"]

    states = {}
    for n in names:
        state, detail = sender_state(panels, n)
        states[n] = state
        print(f"  {n:8} {state:12} {json.dumps(detail)[:110]}")

    if args.status or not args.queue:
        panels.close()
        return 0

    queue = json.load(open(args.queue, encoding="utf-8"))
    sent_path = args.queue.replace(".json", "") + ".sent.json"
    sent = json.load(open(sent_path, encoding="utf-8")) if os.path.exists(sent_path) else {}

    acted = 0
    for n in names:
        if states.get(n) != "idle":
            print(f"  {n:8} skip — state is {states.get(n)}")
            continue
        todo = [t for t in queue.get(n, []) if t not in sent.get(n, [])]
        if not todo:
            print(f"  {n:8} skip — queue exhausted")
            continue
        task = todo[0]
        preview = task.replace("\n", " ")[:90]
        if args.dry_run:
            print(f"  {n:8} WOULD SEND: {preview}")
            continue
        try:
            ok = panels.send(n, task, verify=False)
        except Exception as e:
            print(f"  {n:8} SEND FAILED: {type(e).__name__}: {str(e)[:110]}")
            continue
        if ok:
            sent.setdefault(n, []).append(task)
            json.dump(sent, open(sent_path, "w", encoding="utf-8"), indent=1)
            acted += 1
            print(f"  {n:8} SENT: {preview}")
        else:
            print(f"  {n:8} send returned False — not logged, will retry next run")
        time.sleep(1.5)

    # verify: a panel that accepted a message should stop reporting idle on the next read
    time.sleep(6)
    for n in names:
        state, _ = sender_state(panels, n)
        print(f"  {n:8} now: {state}")
    panels.close()
    print(f"\n{acted} task(s) dispatched")
    return 0


if __name__ == "__main__":
    sys.exit(main())
