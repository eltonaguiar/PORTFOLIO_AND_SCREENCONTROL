#!/usr/bin/env python3
"""Mechanics certification for the screen-control loop.

Run: python tests/test_loop.py    (exit 0 = all pass)

These tests use MockTransport on purpose. A loop that can only be tested with a live
model and a live browser is not testable; every failure is ambiguous between "the model
was wrong", "the page was slow" and "the loop is broken". Each test below isolates one
mechanism and fails loudly if that mechanism stops working.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from screen_control import (  # noqa: E402
    Action, Guard, GuardConfig, LoopConfig, ScreenLoop, ScriptedPlanner, MockTransport,
)

RESULTS = []


def rec(name, ok, detail):
    RESULTS.append((name, ok, detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")


def pages():
    return {
        "home": {
            "title": "Portal",
            "text": "Welcome to the portal",
            "elements": [
                {"handle": "1", "role": "button", "name": "Continue", "goes_to": "form"},
                {"handle": "2", "role": "link", "name": "Delete account"},
            ],
        },
        "form": {
            "title": "Details",
            "text": "Enter your name",
            "elements": [{"handle": "3", "role": "textbox", "name": "Full name"}],
        },
    }


def loop(script, cfg=None, guard=None, transport=None):
    t = transport or MockTransport(pages())
    g = guard or Guard(GuardConfig(allowed_hosts={"mock"}, allow_any_host=True, max_steps=10))
    return ScreenLoop(t, ScriptedPlanner(script), g, cfg or LoopConfig(screenshot_every=0))


# ---------------------------------------------------------------- 1 happy path
def t1_happy():
    l = loop([
        {"verb": "click", "thought": "open the form", "target": "1", "expect": "enter your name"},
        {"verb": "read", "thought": "confirm the page", "target": "body", "meta": {"selector": "body"}},
        {"verb": "done", "thought": "form reached", "text": "reached form"},
    ])
    out = l.run("reach the form")
    ok = out["status"] == "done"
    rec("T1 happy path reaches done", ok,
        f"status={out['status']} steps={out['steps']} final={l.t.current}",
        )


# ---------------------------------------------------------------- 2 host allowlist
def t2_host():
    g = Guard(GuardConfig(allowed_hosts={"example.com"}, allow_any_host=False))
    l = loop([{"verb": "navigate", "thought": "go elsewhere", "url": "https://evil.test/x"},
              {"verb": "done", "thought": "stop"}], guard=g)
    out = l.run("x")
    blocked = any(step["blocked"] for step in out["transcript"])
    rec("T2 off-allowlist navigation is refused", blocked,
        f"blocked={blocked} reason={(g.refusals[0]['reason'] if g.refusals else None)}")


# ---------------------------------------------------------------- 3 destructive gate
def t3_destructive():
    g = Guard(GuardConfig(allow_any_host=True, max_steps=5))
    l = loop([{"verb": "click", "thought": "delete it", "target": "2"},
              {"verb": "done", "thought": "stop"}], guard=g)
    out = l.run("delete something")
    blocked = any(step["blocked"] for step in out["transcript"])
    reason = g.refusals[0]["reason"] if g.refusals else ""
    rec("T3 destructive element needs confirm=True", blocked and "irreversible" in reason, reason)


# ---------------------------------------------------------------- 4 Enter gate
def t4_enter():
    g = Guard(GuardConfig(allow_any_host=True, max_steps=5))
    t = MockTransport({"home": {"title": "T", "text": "",
                                "elements": [{"handle": "9", "role": "button", "name": "Send money"}]}})
    l = loop([{"verb": "key", "thought": "submit", "key": "Enter", "target": "9"},
              {"verb": "done", "thought": "stop"}], guard=g, transport=t)
    out = l.run("send")
    rec("T4 Enter on a destructive target is refused",
        any(s["blocked"] for s in out["transcript"]),
        g.refusals[0]["reason"] if g.refusals else "no refusal recorded")


# ---------------------------------------------------------------- 5 repeat budget
def t5_repeat():
    g = Guard(GuardConfig(allow_any_host=True, max_steps=12, max_consecutive_failures=99))
    benign = {"title": "Home", "text": "welcome",
              "elements": [{"handle": "5", "role": "button", "name": "Refresh"}]}
    same = {"verb": "click", "thought": "try again", "target": "5"}
    l = loop([same] * 12, guard=g, transport=MockTransport({"home": benign}))
    out = l.run("loop forever")
    reps = [r for r in g.refusals if "repeated" in r["reason"]]
    rec("T5 repeated action is capped", bool(reps), f"repeat refusals={len(reps)} status={out['status']}")


# ---------------------------------------------------------------- 6 invalid action
def t6_invalid():
    l = loop([{"verb": "teleport", "thought": "nonsense"},
              {"verb": "done", "thought": "gave up"}])
    out = l.run("x")
    first = out["transcript"][0]
    rec("T6 unknown verb rejected without crashing", first["ok"] is False and "invalid action" in first["detail"],
        first["detail"][:80])


# ---------------------------------------------------------------- 7 verify mismatch
def t7_verify():
    l = loop([{"verb": "click", "thought": "click continue", "target": "1",
               "expect": "completely unrelated phrase about submarines"},
              {"verb": "done", "thought": "stop"}])
    out = l.run("x")
    s0 = out["transcript"][0]
    rec("T7 unmet expectation marks the step failed", s0["ok"] is False, s0["detail"][:90])


# ---------------------------------------------------------------- 8 failure abort
def t8_abort():
    g = Guard(GuardConfig(allow_any_host=True, max_steps=20, max_consecutive_failures=2))
    bad = [{"verb": "click", "thought": "bad handle", "target": "999"} for _ in range(20)]
    # vary so the repeat limiter is not what fires
    bad = [{"verb": "click", "thought": "bad handle", "target": str(900 + i)} for i in range(20)]
    l = loop(bad, guard=g)
    out = l.run("x")
    rec("T8 consecutive failures abort the loop", out["status"] == "aborted",
        f"status={out['status']} reason={out.get('reason')}")


# ---------------------------------------------------------------- 9 transcript
def t9_transcript():
    import tempfile
    d = tempfile.mkdtemp()
    l = loop([{"verb": "click", "thought": "go", "target": "1"},
              {"verb": "done", "thought": "done"}], cfg=LoopConfig(screenshot_every=0, transcript_dir=d))
    out = l.run("x")
    files = list(Path(d).glob("transcript_*.json"))
    ok = bool(files)
    if ok:
        import json
        rows = json.loads(files[0].read_text())
        ok = len(rows) == 2 and rows[0]["verb"] == "click" and "thought" in rows[0]
    rec("T9 transcript is written and auditable", ok, f"{len(files)} file(s), rows ok={ok}")


if __name__ == "__main__":
    print("SCREEN-CONTROL MECHANICS CERTIFICATION")
    for fn in (t1_happy, t2_host, t3_destructive, t4_enter, t5_repeat, t6_invalid, t7_verify, t8_abort, t9_transcript):
        fn()
    n = sum(1 for _, ok, _ in RESULTS if ok)
    print(f"\n{n}/{len(RESULTS)} passed")
    sys.exit(0 if n == len(RESULTS) else 1)
