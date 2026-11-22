#!/usr/bin/env python3
"""Live demo: drive a real Chromium through the guarded loop.

Run inside the Hermes browser sandbox (js/cdp/capture_screenshot are injected):

    exec(open("examples/live_demo.py").read())

Or standalone with a custom transport. The demo is deliberately benign:

  1. navigate to example.com and verify the heading
  2. scroll
  3. read the visible text
  4. declare done

Every step goes through the guard, gets a post-condition, and lands in the transcript.
It proves the CDP path end to end: accessibility tree -> element handle -> live box
model -> mouse event -> re-observe -> verify.
"""

import json
import sys
from pathlib import Path

# Hard-coded root: when this file is exec'd by a browser harness, __file__ points at
# the harness, so deriving the package path from it silently imports the wrong tree.
PKG_ROOT = Path(r"C:\Users\zerou\pasc\01-screen-control-llm")
if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))

from screen_control import (  # noqa: E402
    Guard, GuardConfig, LoopConfig, ScreenLoop, ScriptedPlanner, BrowserUseTransport,
)

TRANSPORT = BrowserUseTransport(
    js=js, cdp=cdp, screenshot=capture_screenshot, navigate=goto_url  # noqa: F821
)

# A scripted policy is used here on purpose: the goal is to certify the MECHANICS.
# Swapping in LLMPlanner changes only which object is passed as `planner`.
SCRIPT = [
    {"verb": "navigate", "thought": "open a real static reference page",
     "url": "https://www.iana.org/help/example-domains", "expect": "Example Domains"},
    {"verb": "read", "thought": "capture the page text for the record", "target": "body",
     "meta": {"selector": "body"}},
    {"verb": "scroll", "thought": "exercise the scroll path", "dy": 400},
    {"verb": "done", "thought": "all steps verified", "text": "navigated, read, scrolled"},
]

guard = Guard(GuardConfig(allowed_hosts={"iana.org", "wikipedia.org"}, max_steps=8, max_seconds=90))
loop = ScreenLoop(
    TRANSPORT,
    ScriptedPlanner(SCRIPT),
    guard,
    LoopConfig(max_steps=8, screenshot_every=99,
               transcript_dir=str(PKG_ROOT / "transcripts")),
)

obs = TRANSPORT.observe()
print("OBSERVED:", json.dumps(
    {"url": obs["url"], "title": obs["title"], "n_elements": len(obs["elements"]),
     "first_elements": obs["elements"][:5]}, indent=1))

result = loop.run("prove the screen-control loop works on a real page")
print("\nRESULT:", result["status"], "|", result.get("summary") or result.get("reason"))
for row in result["transcript"]:
    print(f"  step {row['step']}: {row['verb']:9s} ok={row['ok']}  {row['detail'][:110]}")

read_step = next((r for r in result["transcript"] if r["verb"] == "read"), None)
print("\nREAD_RESULT_OK:", bool(read_step and read_step["ok"]))
