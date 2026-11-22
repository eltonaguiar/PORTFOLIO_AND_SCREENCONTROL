"""The closed loop: observe -> decide -> guard -> act -> verify -> record.

Control flow, and why it is in this order:

    observe()      build a compact observation (accessible elements + url + title)
    guard.exhausted()  bail before spending another model call if the budget is gone
    planner.act()  one decision
    action.validate()   reject structurally invalid decisions before touching the UI
    guard.check()  policy refusal -> recorded, loop continues (does not crash)
    execute()      perform the single action, resolving coordinates at act time
    verify()       re-observe and check the declared post-condition
    record()       append a transcript row; screenshot kept every N steps

Two behaviours that matter in practice:

  * A refused or failed step is NOT fatal. The loop continues and the model sees the
    failure in its history, which is usually enough to make it try a different route.
    It only aborts on a spent budget.
  * `verify` is advisory-but-recorded. If the declared `expect` does not appear, the
    step is marked failed even if the click "succeeded", because a click that changes
    nothing is the most common silent agent bug.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional

from .guard import Guard, GuardConfig
from .schema import Action, StepResult


@dataclass
class LoopConfig:
    max_steps: int = 25
    screenshot_every: int = 1
    settle_ms: int = 350
    transcript_dir: Optional[str] = None


class ScreenLoop:
    def __init__(self, transport, planner, guard: Guard, cfg: LoopConfig = LoopConfig()):
        self.t = transport
        self.planner = planner
        self.guard = guard
        self.cfg = cfg
        self.history: List[StepResult] = []
        self.transcript: List[dict] = []

    # ------------------------------------------------------------------ helpers
    def _record(self, res: StepResult) -> None:
        self.history.append(res)
        self.transcript.append(
            {
                "step": res.step,
                "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "verb": res.action.verb,
                "target": res.action.target,
                "thought": res.action.thought,
                "expect": res.action.expect,
                "ok": res.ok,
                "blocked": res.blocked,
                "detail": res.detail,
                "screenshot": res.screenshot,
            }
        )

    def _save(self) -> Optional[str]:
        if not self.cfg.transcript_dir:
            return None
        d = Path(self.cfg.transcript_dir)
        d.mkdir(parents=True, exist_ok=True)
        p = d / f"transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        p.write_text(json.dumps(self.transcript, indent=1), encoding="utf-8")
        return str(p)

    # ------------------------------------------------------------------ main
    def run(self, goal: str) -> dict:
        for step in range(1, self.cfg.max_steps + 1):
            exhausted = self.guard.exhausted()
            if exhausted:
                self._save()
                return {"status": "aborted", "reason": exhausted, "steps": step - 1,
                        "transcript": self.transcript}

            obs = self.t.observe()
            obs["goal"] = goal

            try:
                action = self.planner.act(obs, self.transcript)
            except Exception as exc:
                res = StepResult(step=step, action=Action(verb="fail", thought="planner error"),
                                 ok=False, detail=f"planner error: {type(exc).__name__}: {exc}")
                self._record(res)
                self.guard.record(False)
                continue

            if action.verb == "done":
                self._record(StepResult(step=step, action=action, ok=True, detail="task complete"))
                self._save()
                return {"status": "done", "summary": action.text, "steps": step,
                        "transcript": self.transcript}
            if action.verb == "fail":
                self._record(StepResult(step=step, action=action, ok=False, detail=action.text or "failed"))
                self._save()
                return {"status": "failed", "reason": action.text, "steps": step,
                        "transcript": self.transcript}

            try:
                action.validate()
            except Exception as exc:
                self._record(StepResult(step=step, action=action, ok=False,
                                        detail=f"invalid action: {exc}"))
                self.guard.record(False)
                continue

            refuse = self.guard.check(action, element_name=self.t.element_name(action.target))
            if refuse:
                self.guard.refuse(action, refuse)
                self._record(StepResult(step=step, action=action, ok=False,
                                        detail=refuse, blocked=True))
                self.guard.record(False)
                continue

            ok, detail = self.t.execute(action)
            time.sleep(self.cfg.settle_ms / 1000.0)

            verified, vdetail = True, "no expectation declared"
            if action.expect:
                verified, vdetail = self.t.verify(action.expect)
            ok = bool(ok) and bool(verified)
            detail = f"{detail} | verify: {vdetail}"

            shot = None
            if self.cfg.screenshot_every and step % self.cfg.screenshot_every == 0:
                shot = self.t.screenshot()

            self._record(StepResult(step=step, action=action, ok=ok, detail=detail,
                                    screenshot=shot))
            self.guard.record(ok)

        self._save()
        return {"status": "max_steps", "steps": self.cfg.max_steps, "transcript": self.transcript}
