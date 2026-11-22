"""Task runner — executes a declarative task file against whatever surface it lands on.

The task is data (`tasks/*.json`); the surface is decided at runtime by `kernel.resolve`; the
actual clicking/typing/reading is a `Transport`. That separation is the whole point: the same task
file must run against a browser page, an Electron IDE, a native dialog or a RustDesk viewer without
being rewritten — only the transport and the rung change.

Usage:
    python prototype/run_task.py prototype/tasks/chatplayground.json --prompt "hello" --dry-run
    python prototype/run_task.py ... --transport cua        # requires cua-driver on PATH

Every run writes `transcripts/run_<utc>.jsonl` (one line per step, with the rung used and the
verdict) plus a manifest, so a failed run is still a recorded result.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Protocol

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from kernel.resolve import Decision, Probe, Rung, SurfaceClass, WindowProfile, classify  # noqa: E402


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


# --------------------------------------------------------------------------------------------
# Transport port
# --------------------------------------------------------------------------------------------


class Transport(Protocol):
    """The only thing a task needs from the outside world. One method per action verb."""

    name: str

    def probe(self, profile: WindowProfile, rung: Rung) -> Probe: ...

    def click_text(self, profile: WindowProfile, texts: list[str]) -> dict: ...

    def focus_text_field(self, profile: WindowProfile, placeholders: list[str]) -> dict: ...

    def type_text(self, profile: WindowProfile, text: str) -> dict: ...

    def read_text(self, profile: WindowProfile) -> str: ...

    def read_clipboard(self) -> str: ...

    def wait(self, seconds: float) -> None: ...


class DryTransport:
    """Records what would happen and returns plausible-but-marked-empty results.

    A dry run is how you check a task file without touching the user's session; every verdict it
    returns is labelled `dry-run`, so nothing here can be mistaken for evidence.
    """

    name = "dry"

    def __init__(self) -> None:
        self.log: list[tuple[str, Any]] = []

    def probe(self, profile: WindowProfile, rung: Rung) -> Probe:
        return Probe(rung=rung, detail="dry-run probe")

    def click_text(self, profile, texts):
        self.log.append(("click_text", texts))
        return {"ok": True, "effect": "dry-run", "verified": False}

    def focus_text_field(self, profile, placeholders):
        self.log.append(("focus", placeholders))
        return {"ok": True, "effect": "dry-run", "verified": False}

    def type_text(self, profile, text):
        self.log.append(("type", text[:60]))
        return {"ok": True, "effect": "dry-run", "verified": False}

    def read_text(self, profile):
        return ""

    def read_clipboard(self):
        return ""

    def wait(self, seconds):
        self.log.append(("wait", seconds))


class CuaTransport:
    """Transport backed by cua-driver's CLI. Fails loudly rather than pretending to work.

    cua-driver exposes the primitives this needs (window-scoped capture, background input, UIA
    reads) through its MCP tools; driving it from a script requires either its CLI or a tiny MCP
    client. Until that client lives here, this class refuses instead of silently no-opping — a
    transport that pretends is worse than one that is missing.
    """

    name = "cua"

    def __init__(self) -> None:
        import shutil

        if not shutil.which("cua-driver"):
            raise RuntimeError(
                "cua-driver not on PATH: install it (hermes computer-use install) or run with "
                "--transport dry, or drive the run through the computer_use tool instead"
            )

    def probe(self, profile, rung):  # pragma: no cover - needs a live desktop
        raise NotImplementedError("MCP client not wired yet; see NEXT_STEPS A2/A4")

    def click_text(self, profile, texts):  # pragma: no cover
        raise NotImplementedError("MCP client not wired yet")

    def focus_text_field(self, profile, placeholders):  # pragma: no cover
        raise NotImplementedError("MCP client not wired yet")

    def type_text(self, profile, text):  # pragma: no cover
        raise NotImplementedError("MCP client not wired yet")

    def read_text(self, profile):  # pragma: no cover
        raise NotImplementedError("MCP client not wired yet")

    def read_clipboard(self):  # pragma: no cover
        raise NotImplementedError("MCP client not wired yet")

    def wait(self, seconds):  # pragma: no cover
        time.sleep(seconds)


# --------------------------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------------------------


@dataclass
class StepResult:
    step_id: str
    kind: str
    verdict: str            # PASS | FAIL | SKIP | UNFINISHED
    rung: str = ""
    latency_ms: int = 0
    detail: str = ""
    evidence: str = ""

    def as_dict(self) -> dict:
        return {
            "step": self.step_id,
            "kind": self.kind,
            "verdict": self.verdict,
            "rung": self.rung,
            "latency_ms": self.latency_ms,
            "detail": self.detail,
            "evidence": self.evidence,
        }


@dataclass
class Run:
    task: dict
    prompt: str
    transport: Transport
    profile: WindowProfile
    decision: Optional[Decision] = None
    results: list[StepResult] = field(default_factory=list)
    started: str = field(default_factory=utc_stamp)

    def record(self, r: StepResult) -> StepResult:
        self.results.append(r)
        return r

    @property
    def sha(self) -> str:
        blob = json.dumps([r.as_dict() for r in self.results], sort_keys=True).encode()
        return hashlib.sha256(blob).hexdigest()[:16]


def _step(task: dict, step_id: str) -> Optional[dict]:
    for s in task.get("steps", []):
        if s.get("id") == step_id:
            return s
    return None


def pretriage(run: Run) -> bool:
    """Perceive once, decide the rung, and refuse to start if the surface is wrong.

    This is the step that stops the classic failure: a task file written for a browser being
    pointed at an IDE, then "clicking Login" somewhere in the file explorer.
    """
    t0 = time.time()
    surf = run.task.get("surface", {})
    expected = classify(*surf.get("app_match", [""]))
    run.profile = WindowProfile(
        app=run.profile.app, title=run.profile.title, hwnd=run.profile.hwnd,
        width=run.profile.width, height=run.profile.height,
    )
    if surf.get("class") and run.profile.surface.value != surf["class"]:
        run.record(StepResult("pretriage", "assert", "FAIL", detail=(
            f"surface mismatch: task expects {surf['class']}, window looks like "
            f"{run.profile.surface.value}")))
        return False

    run.decision = _decide(run.profile, run.transport)
    run.record(StepResult(
        "pretriage", "resolve", "PASS", rung=run.decision.rung.value,
        latency_ms=int((time.time() - t0) * 1000),
        detail=run.decision.reason,
        evidence=f"tried={[r.value for r in run.decision.tried]} hint={run.decision.hint}",
    ))
    return True


def _decide(profile: WindowProfile, transport: Transport) -> Decision:
    from kernel.resolve import ResolverCache

    cache = ResolverCache()
    return cache.resolve(profile, transport.probe)


def run_task(task: dict, prompt: str, transport: Transport, profile: WindowProfile,
             out_dir: Path) -> Run:
    run = Run(task=task, prompt=prompt, transport=transport, profile=profile)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not pretriage(run):
        write_artifacts(run, out_dir)
        return run

    for step in task.get("steps", []):
        sid, kind = step.get("id", "?"), step.get("kind", "?")
        t0 = time.time()
        try:
            if kind == "click_any_text":
                res = transport.click_text(run.profile, step.get("match", []))
                verdict = "PASS" if res.get("verified") else ("SKIP" if step.get("optional") else "UNFINISHED")
                detail = res.get("effect", "")
            elif kind == "focus_text_field":
                res = transport.focus_text_field(run.profile, step.get("match_placeholder", []))
                verdict = "PASS" if res.get("verified") else "UNFINISHED"
                detail = res.get("effect", "")
            elif kind == "type":
                text = step.get("text", "").replace("{{prompt}}", prompt)
                res = transport.type_text(run.profile, text)
                verdict = "PASS" if res.get("verified") else "UNFINISHED"
                detail = res.get("effect", "")
            elif kind == "wait_all_panels":
                verdict, detail = wait_for_panels(run, step)
            elif kind == "write_transcript":
                verdict, detail = "PASS", "written at end of run"
            elif kind == "assert":
                surface_text = transport.read_text(run.profile)
                verdict = "PASS" if step.get("evidence", "") and step["evidence"] in surface_text else "UNFINISHED"
                detail = f"{len(surface_text)} chars read"
            else:
                verdict, detail = "SKIP", f"unknown step kind {kind}"
        except Exception as exc:
            verdict, detail = "FAIL", f"{type(exc).__name__}: {exc}"

        run.record(StepResult(sid, kind, verdict, rung=run.decision.rung.value if run.decision else "",
                              latency_ms=int((time.time() - t0) * 1000), detail=detail))
        if verdict == "FAIL":
            break

    write_artifacts(run, out_dir)
    return run


def wait_for_panels(run: Run, step: dict) -> tuple[str, str]:
    """Poll until every panel shows its done signature and the text stops changing.

    Two conditions, because either alone lies: a panel can show a TTFT strip while still streaming,
    and a panel can be textually stable while a Stop button is still present (a stalled request).
    """
    sig = step.get("done_signature", {})
    positive = sig.get("positive", ["TTFT"])
    negative = sig.get("negative", ["Stop"])
    interval = float(step.get("poll_interval_s", 3))
    timeout = float(step.get("timeout_s", 240))

    last, stable, t0 = None, 0, time.time()
    while time.time() - t0 < timeout:
        text = run.transport.read_text(run.profile)
        has_pos = any(p in text for p in positive)
        has_neg = any(n in text for n in negative)
        stable = stable + 1 if text and text == last else 0
        last = text
        if has_pos and not has_neg and stable >= 2:
            return "PASS", f"done after {int(time.time() - t0)}s, signature present, no stop control"
        run.transport.wait(interval)
    return "UNFINISHED", f"no done signature within {timeout}s"


def write_artifacts(run: Run, out_dir: Path) -> Path:
    stamp = utc_stamp()
    jsonl = out_dir / f"run_{stamp}.jsonl"
    with jsonl.open("w", encoding="utf-8") as fh:
        for r in run.results:
            fh.write(json.dumps(r.as_dict()) + "\n")
    manifest = out_dir / f"run_{stamp}.manifest.json"
    manifest.write_text(json.dumps({
        "task": run.task.get("name"),
        "prompt_sha256": hashlib.sha256(run.prompt.encode()).hexdigest(),
        "surface": run.profile.surface.value,
        "window": run.profile.app,
        "rung": run.decision.rung.value if run.decision else None,
        "rung_reason": run.decision.reason if run.decision else None,
        "transport": run.transport.name,
        "started_utc": run.started,
        "steps": [r.as_dict() for r in run.results],
        "results_sha256": run.sha,
        "verdict": "PASS" if all(r.verdict in ("PASS", "SKIP") for r in run.results) else "INCOMPLETE",
    }, indent=2), encoding="utf-8")
    return manifest


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Run a declarative screen-control task.")
    ap.add_argument("task_file")
    ap.add_argument("--prompt", default="")
    ap.add_argument("--app", default="chrome.exe")
    ap.add_argument("--title", default="")
    ap.add_argument("--transport", default="dry", choices=["dry", "cua"])
    ap.add_argument("--dry-run", action="store_true", help="alias for --transport dry")
    ap.add_argument("--out", default=str(HERE / "transcripts"))
    args = ap.parse_args(argv)

    task = json.loads(Path(args.task_file).read_text(encoding="utf-8"))
    transport = DryTransport() if (args.dry_run or args.transport == "dry") else CuaTransport()
    profile = WindowProfile(app=args.app, title=args.title, hwnd=None, width=1456, height=782)
    run = run_task(task, args.prompt, transport, profile, Path(args.out))
    print(json.dumps({
        "task": task.get("name"),
        "rung": run.decision.rung.value if run.decision else None,
        "verdicts": [r.as_dict() for r in run.results],
        "sha": run.sha,
        "artifacts": str(Path(args.out)),
    }, indent=2))
    return 0 if all(r.verdict in ("PASS", "SKIP") for r in run.results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
