"""The supervisor — take charge and stop stopping (§5).

Implements the loop contract from `TOOL_INTERFACE.md` §task-ledger:

    while state == "in_progress":
        ledger = read(task_id)                      # disk, not context
        if STOP file exists or budget exhausted: state = "cancelled"; break
        obs = perceive(next_action.target)
        result = act(next_action)                    # with verify
        append_evidence(result)
        state, next_action = decide(ledger, obs, result)   # progress | loop | blocked | done
        write_atomic(ledger)                         # before any external side effect

`decide` never blindly re-sends "continue". It classifies the stop and either
supplies a new fact (a steer brief) or stops.

The class keeps zero persistent state of its own: the `Ledger` (on disk) is the
memory, and every decision is reproducible from it. That makes this module easy
to test without a GUI, a model, or a running agent — the acceptance test for A6
is a simulated session: stop -> continue -> loop -> steer with a new fact -> done.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

__all__ = [
    "Ledger", "LedgerError", "StopFile", "Overseer", "OverseerDecision",
    "classify_stop", "step_signature", "utc_now",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def step_signature(tool: str, args: dict, output: str) -> str:
    """Canonical hash of one step: tool + normalized args + normalized output.

    Normalisation strips timestamps, PIDs and temp paths so identical failures
    hash identically — otherwise two iterations of the same stuck loop look
    different and the supervisor misses it (§5.2). Meaningful digits (line
    numbers, exit codes) are deliberately kept so *different* failures hash
    differently.
    """
    norm = re.sub(r"[\(\[]?\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(?::\d{2})?(?:Z|[+-]\d{2}:?\d{2})?[\)\]]?", "", output)
    norm = re.sub(r"[\(\[]?\b(?:pid|PID)=?\d+\b[\)\]]?", "", norm)
    norm = re.sub(r"\b\d{5,}\b", "<NUM>", norm)          # long epoch-ish numbers
    norm = re.sub(r"/(?:tmp|temp|var|Users)/[^\s'\"<>{}()]+", "<PATH>", norm)
    norm = re.sub(r"\b[A-Fa-f0-9]{8,}\b", "<HEX>", norm)  # hashes / addresses
    norm = re.sub(r"\[\s*\]|\(\s*\)", "", norm)            # empty brackets left by stripping
    norm = re.sub(r"\s+", " ", norm).strip()               # whitespace-insensitive
    payload = f"{tool}|{json.dumps(args, sort_keys=True)}|{norm}"
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]


class LedgerError(Exception):
    """Raised when the ledger cannot be read or written."""


@dataclass
class Ledger:
    """One JSON file per task, written atomically, re-read every cycle.

    This is the supervisor's durable state. It survives context compaction,
    model switches, and crashes — the plan stays on disk, not in the window.
    """

    task_id: str
    goal: str
    created_utc: str = field(default_factory=utc_now)
    deadline_utc: Optional[str] = None
    approval_class: int = 1
    definition_of_done: dict = field(default_factory=dict)
    state: str = "in_progress"          # in_progress | done | blocked | cancelled
    cycle: int = 0
    last_observation: dict = field(default_factory=dict)
    next_action: Optional[dict] = None
    attempts: list = field(default_factory=list)
    evidence: list = field(default_factory=list)
    blocked_reason: Optional[str] = None
    budget: dict = field(default_factory=lambda: {"cycles_left": 40, "minutes_left": 45})
    passed_checks: list = field(default_factory=list)

    @classmethod
    def load(cls, path: str | Path) -> "Ledger":
        p = Path(path)
        if not p.exists():
            raise LedgerError(f"ledger not found: {p}")
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise LedgerError(f"cannot read ledger {p}: {exc}") from exc
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def save(self, path: str | Path) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(p.suffix + ".tmp")
        tmp.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        os.replace(tmp, p)

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "goal": self.goal,
            "created_utc": self.created_utc,
            "deadline_utc": self.deadline_utc,
            "approval_class": self.approval_class,
            "definition_of_done": self.definition_of_done,
            "state": self.state,
            "cycle": self.cycle,
            "last_observation": self.last_observation,
            "next_action": self.next_action,
            "attempts": self.attempts,
            "evidence": self.evidence,
            "blocked_reason": self.blocked_reason,
            "budget": self.budget,
            "passed_checks": self.passed_checks,
        }


@dataclass(frozen=True)
class StopFile:
    """The kill switch (§5.5): a file the loop checks each cycle."""

    path: str | Path

    @property
    def exists(self) -> bool:
        return Path(self.path).exists()


@dataclass
class OverseerDecision:
    state: str                            # in_progress | done | blocked | cancelled
    next_action: Optional[dict]
    steer: Optional[str]                  # injected brief when state == "in_progress"
    reason: str                           # human-readable why
    audit: dict                           # one ndjson row per decision


class Overseer:
    """Classify the stop before acting. Never re-sends "continue".

    Classification table (§5.1):
      - done: DoD met + verification passed
      - cancelled: STOP file / budget exhausted / environmental stop (402, 401, disk full)
      - blocked: genuine user question (credentials, product decision)
      - loop: same signature twice, or no-progress across N steps
      - in_progress: steer with a brief and continue
    """

    def __init__(
        self,
        ledger: Ledger,
        stop_file: StopFile,
        *,
        max_repeat_signatures: int = 2,
        max_no_progress_steps: int = 3,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.ledger = ledger
        self.stop_file = stop_file
        self.max_repeat_signatures = max_repeat_signatures
        self.max_no_progress_steps = max_no_progress_steps
        self._clock = clock

    # ------------------------------------------------------------------ decide
    def decide(self, observation: dict, result: dict) -> OverseerDecision:
        ledger = self.ledger
        ledger.cycle += 1
        ledger.last_observation = {
            "at_utc": utc_now(),
            "summary": observation.get("summary", ""),
            "evidence": observation.get("evidence", []),
        }
        if result:
            ledger.evidence.append(
                {"kind": "result", "at_utc": utc_now(), **result}
            )
            ledger.attempts.append(
                {
                    "sig": step_signature(
                        result.get("tool", ""), result.get("args", {}), result.get("output", "")
                    ),
                    "tool": result.get("tool", ""),
                    "result": result.get("status", ""),
                    "count": 1,
                }
            )

        # 1. kill switch / budget ------------------------------------------------
        if self.stop_file.exists:
            ledger.state = "cancelled"
            ledger.blocked_reason = "STOP file present"
            return OverseerDecision(
                "cancelled", None, None, "STOP file present", self._audit(ledger),
            )
        if self._budget_exhausted(ledger):
            ledger.state = "cancelled"
            ledger.blocked_reason = "budget exhausted"
            return OverseerDecision(
                "cancelled", None, None, "budget exhausted", self._audit(ledger),
            )

        # 2. done -----------------------------------------------------------------
        if self._dod_met(ledger, result):
            ledger.state = "done"
            return OverseerDecision(
                "done", None, None, "definition of done met and verified", self._audit(ledger),
            )

        # 3. loop detection --------------------------------------------------------
        if self._is_loop(ledger):
            ledger.state = "blocked"
            ledger.blocked_reason = "loop detected — same signature repeated"
            return OverseerDecision(
                "blocked", None, None,
                "same action signature repeated; injecting diagnosis instead of continuing",
                self._audit(ledger),
            )

        # 4. steer — inject a brief and continue -----------------------------------
        brief = self._build_brief(ledger, observation, result)
        ledger.state = "in_progress"
        ledger.next_action = {
            "tool": "respond",
            "args": {"brief": brief},
            "issued_utc": utc_now(),
        }
        return OverseerDecision(
            "in_progress",
            ledger.next_action,
            steer=brief,
            reason=f"cycle {ledger.cycle}: continuing with steer",
            audit=self._audit(ledger),
        )

    # ------------------------------------------------------------------ checks
    def _budget_exhausted(self, ledger: Ledger) -> bool:
        b = ledger.budget or {}
        if b.get("cycles_left") is not None and b["cycles_left"] <= 0:
            return True
        if b.get("minutes_left") is not None and b["minutes_left"] <= 0:
            return True
        return False

    def _dod_met(self, ledger: Ledger, result: dict) -> bool:
        checks = (ledger.definition_of_done or {}).get("checks", [])
        if not checks:
            return False
        all_cmds = [c.get("cmd") for c in checks if c.get("cmd")]
        pending = [cmd for cmd in all_cmds if cmd not in ledger.passed_checks]
        if result:
            status = result.get("status", "")
            explicit = result.get("cmd")
            tool = result.get("tool", "")
            for cmd in list(pending):
                matched = explicit and explicit == cmd
                if not matched and tool and cmd.split(None, 1)[0] == tool:
                    matched = True
                if matched and status == "passed":
                    if cmd not in ledger.passed_checks:
                        ledger.passed_checks.append(cmd)
                    pending.remove(cmd)
        return not pending

    def _is_loop(self, ledger: Ledger) -> bool:
        """True when the same signature appeared max_repeat_signatures times,
        or when there was no diff-producing change for max_no_progress_steps."""
        sigs = [a["sig"] for a in ledger.attempts if a.get("sig")]
        if len(sigs) >= self.max_repeat_signatures:
            recent = sigs[-self.max_repeat_signatures:]
            if len(set(recent)) == 1:
                return True
        if ledger.cycle >= self.max_no_progress_steps:
            diffs = [
                e for e in ledger.evidence
                if e.get("kind") == "diff" and e.get("changed")
            ]
        else:
            diffs = []
        if len(diffs) < 1 and ledger.cycle >= self.max_no_progress_steps:
            return True
        return False

    def _build_brief(self, ledger: Ledger, observation: dict, result: dict) -> str:
        lines = [
            f"STATE: cycle {ledger.cycle}, state={ledger.state}",
            f"GOAL (unchanged): {ledger.goal}",
        ]
        if result:
            lines.append(
                f"EVIDENCE: {result.get('tool','')} -> {result.get('status','')}: "
                f"{result.get('output','')[:200]}"
            )
        if ledger.attempts:
            tried = sorted({a["tool"] for a in ledger.attempts[-5:]})
            lines.append(f"ALREADY TRIED (do not repeat): {', '.join(tried)}")
        lines.append(
            "NEXT SINGLE ACTION: re-read the last observation and take one step "
            "toward the definition of done."
        )
        if ledger.definition_of_done:
            lines.append(
                f"VALIDATION: {ledger.definition_of_done} must all pass before state=done."
            )
        return "\n".join(lines)

    def _audit(self, ledger: Ledger) -> dict:
        return {
            "at_utc": utc_now(),
            "task_id": ledger.task_id,
            "cycle": ledger.cycle,
            "state": ledger.state,
            "blocked_reason": ledger.blocked_reason,
        }


def classify_stop(observation: dict) -> str:
    """One-off classification helper used by the agent's own planner.

    Returns one of: done | blocked | loop | continue.
    """
    if observation.get("done"):
        return "done"
    if observation.get("blocked"):
        return "blocked"
    if observation.get("loop"):
        return "loop"
    return "continue"


# ------------------------------------------------------------------ runnable smoke
if __name__ == "__main__":
    import tempfile

    d = Path(tempfile.mkdtemp())
    ledger_path = d / "task.json"
    stop_path = d / "STOP"

    ledger = Ledger(
        task_id="smoke",
        goal="make the failing test green",
        definition_of_done={
            "checks": [{"cmd": "pytest -q tests/test_smoke.py", "expect_exit": 0}]
        },
    )
    ledger.save(ledger_path)

    over = Overseer(ledger, StopFile(stop_path))

    # cycle 1: progress, steer
    obs = {"summary": "test failing", "evidence": ["tests/test_smoke.py:12 AssertionError"]}
    res = {"tool": "pytest", "args": {"target": "tests/test_smoke.py"},
           "status": "failed", "output": "AssertionError at line 12"}
    dec = over.decide(obs, res)
    assert dec.state == "in_progress" and dec.steer, dec
    ledger.save(ledger_path)

    # cycle 2: same signature twice -> blocked (loop), not continue
    ledger = Ledger.load(ledger_path)
    over = Overseer(ledger, StopFile(stop_path))
    dec = over.decide(obs, res)
    assert dec.state == "blocked", dec.state
    assert "loop" in dec.reason.lower() or "repeated" in dec.reason.lower(), dec.reason

    # cycle 3: a new fact breaks the loop -> continue again
    ledger = Ledger.load(ledger_path)
    ledger.state = "in_progress"
    ledger.attempts = []  # fresh hypothesis cleared the signature history
    ledger.save(ledger_path)
    over = Overseer(ledger, StopFile(stop_path))
    res2 = {"tool": "edit", "args": {"file": "tests/test_smoke.py"},
            "status": "passed", "output": "fixed line 12"}
    dec = over.decide(obs, res2)
    assert dec.state == "in_progress", dec.state

    # cycle 4: DoD met -> done
    ledger = Ledger.load(ledger_path)
    ledger.state = "in_progress"
    ledger.attempts = []
    ledger.save(ledger_path)
    over = Overseer(ledger, StopFile(stop_path))
    res3 = {"tool": "pytest", "args": {"target": "tests/test_smoke.py"},
            "status": "passed", "output": "1 passed"}
    dec = over.decide(obs, res3)
    assert dec.state == "done", dec.state

    print("OVERSEER SMOKE: stop->continue->loop->steer->done  OK")
