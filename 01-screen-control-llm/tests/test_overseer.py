"""Overseer supervisor tests — no window, no model, no network.

Covers §5 of PC_AGENT_CONTROL_RESEARCH.md:
- stop -> continue -> loop -> steer with a new fact -> done (simulated session)
- signature hashing is stable under timestamps/PIDs/temp paths
- STOP file and budget both cancel
- done requires every DoD check to pass
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from kernel.overseer import (  # noqa: E402
    Ledger,
    Overseer,
    StopFile,
    classify_stop,
    step_signature,
    utc_now,
)

TMP = Path("/tmp/hermes_overseer_tests")


def fresh(tmp: Path, task_id: str = "t") -> tuple[Path, Path, Ledger, Overseer]:
    tmp.mkdir(parents=True, exist_ok=True)
    ledger_path = tmp / f"{task_id}.json"
    stop_path = tmp / "STOP"
    ledger = Ledger(
        task_id=task_id,
        goal="make the failing test green",
        definition_of_done={
            "checks": [{"cmd": "pytest -q tests/test_smoke.py", "expect_exit": 0}]
        },
    )
    ledger.save(ledger_path)
    return ledger_path, stop_path, ledger, Overseer(ledger, StopFile(stop_path))


def obs(summary: str = "test failing") -> dict:
    return {"summary": summary, "evidence": ["tests/test_smoke.py:12 AssertionError"]}


def res(tool: str = "pytest", status: str = "failed", output: str = "AssertionError", args: dict | None = None) -> dict:
    return {"tool": tool, "args": args or {"target": "tests/test_smoke.py"},
            "status": status, "output": output}


def test_stop_continue_loop_steer_done_simulated_session() -> None:
    """The A6 acceptance test: a full simulated session without a GUI."""
    tmp = TMP / "session"
    ledger_path, stop_path, ledger, over = fresh(tmp)

    # cycle 1: progress -> steer
    dec = over.decide(obs(), res())
    assert dec.state == "in_progress" and dec.steer, dec
    assert "GOAL" in dec.steer and "NEXT SINGLE ACTION" in dec.steer
    ledger.save(ledger_path)

    # cycle 2: same signature twice -> blocked (loop), never "continue"
    ledger = Ledger.load(ledger_path)
    over = Overseer(ledger, StopFile(stop_path))
    dec = over.decide(obs(), res())
    assert dec.state == "blocked", dec.state
    assert "loop" in dec.reason.lower() or "repeated" in dec.reason.lower(), dec.reason

    # cycle 3: new fact clears the signature history -> continue again
    ledger = Ledger.load(ledger_path)
    ledger.state = "in_progress"
    ledger.attempts = []
    ledger.save(ledger_path)
    over = Overseer(ledger, StopFile(stop_path))
    dec = over.decide(obs(), res(tool="edit", status="passed", output="fixed line 12"))
    assert dec.state == "in_progress", dec.state

    # cycle 4: DoD met + verification passed -> done
    ledger = Ledger.load(ledger_path)
    ledger.state = "in_progress"
    ledger.attempts = []
    ledger.save(ledger_path)
    over = Overseer(ledger, StopFile(stop_path))
    dec = over.decide(obs(), res(status="passed", output="1 passed"))
    assert dec.state == "done", dec.state


def test_stop_file_cancels() -> None:
    tmp = TMP / "stop"
    ledger_path, stop_path, ledger, over = fresh(tmp)
    stop_path.write_text("stop", encoding="utf-8")
    dec = over.decide(obs(), res())
    assert dec.state == "cancelled", dec.state
    assert dec.steer is None, "a cancelled run must not steer"


def test_budget_exhausted_cancels() -> None:
    tmp = TMP / "budget"
    ledger_path, stop_path, ledger, over = fresh(tmp)
    ledger.budget = {"cycles_left": 0, "minutes_left": 45}
    ledger.save(ledger_path)
    over = Overseer(ledger, StopFile(stop_path))
    dec = over.decide(obs(), res())
    assert dec.state == "cancelled", dec.state


def test_done_requires_every_dod_check() -> None:
    tmp = TMP / "dod"
    ledger_path, stop_path, ledger, over = fresh(tmp)
    ledger.definition_of_done = {
        "checks": [
            {"cmd": "pytest -q tests/a.py", "expect_exit": 0},
            {"cmd": "mypy tests/b.py", "expect_exit": 0},
        ]
    }
    ledger.save(ledger_path)
    # one check passes -> not done yet
    dec = over.decide(obs(), res(tool="pytest", args={"target": "tests/a.py"},
                                status="passed", output="ok"))
    assert dec.state == "in_progress", dec.state
    # second check passes -> done
    dec = over.decide(obs(), res(tool="mypy", args={"target": "tests/b.py"},
                                status="passed", output="ok"))
    assert dec.state == "done", dec.state


def test_step_signature_stable_under_noise() -> None:
    base = step_signature("pytest", {"target": "t.py"},
                          "FAILED tests/test_smoke.py::test_x - AssertionError at line 12")
    noisy = step_signature("pytest", {"target": "t.py"},
                           "FAILED tests/test_smoke.py::test_x - AssertionError at line 12 [2026-11-22T15:56Z pid=4711]")
    assert base == noisy, (base, noisy)


def test_step_signature_changes_on_real_output_change() -> None:
    a = step_signature("pytest", {"target": "t.py"}, "AssertionError at line 12")
    b = step_signature("pytest", {"target": "t.py"}, "AssertionError at line 42")
    assert a != b


def test_classify_stop() -> None:
    assert classify_stop({"done": True}) == "done"
    assert classify_stop({"blocked": True}) == "blocked"
    assert classify_stop({"loop": True}) == "loop"
    assert classify_stop({}) == "continue"
    assert classify_stop({"summary": "still working"}) == "continue"


def test_ledger_round_trip() -> None:
    tmp = TMP / "roundtrip"
    ledger_path, _, ledger, _ = fresh(tmp)
    loaded = Ledger.load(ledger_path)
    assert loaded.task_id == ledger.task_id
    assert loaded.goal == ledger.goal
    assert loaded.state == "in_progress"


if __name__ == "__main__":
    import traceback

    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    n = 0
    for t in tests:
        try:
            t()
            print(f"  [PASS] {t.__name__}")
            n += 1
        except Exception:
            print(f"  [FAIL] {t.__name__}")
            traceback.print_exc()
    print(f"\n{n}/{len(tests)} passed")
    sys.exit(0 if n == len(tests) else 1)
