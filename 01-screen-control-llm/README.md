# 01 — Screen control via LLM / AI

Goal: an agent that can **perceive and drive anything on screen** — VS Code, a browser with logged-in
sessions, a terminal, JetBrains, Office, Explorer, a RustDesk/RDP session, a game — and that **acts like a
competent human at the turn boundary**: it does not stop after one reply, and when it stalls it gets new
information instead of a blind "continue".

## The five layers (keep them separate)

| Layer | Job | Best free choice | What breaks if you skip it |
|---|---|---|---|
| **Actuator** | move mouse, send keys, click a control | `cua` / `cua-driver` (MIT, 32.7k★) — already installed on the reference machine and healthy | coordinates drift, focus theft, DPI breakage |
| **Perceiver** | know what's on screen | UIA / AT-SPI first, then RapidOCR, then a grounding model | you OCR a screenshot and lose hit targets |
| **Grounder** | "where is X?" in pixels | UI-TARS / ShowUI-2B / OmniParser — **not** a chat VLM | 10 s per frame and empty answers (measured) |
| **Orchestrator** | decide the next action, own the loop | Copilot CLI `--autopilot`, Copilot SDK `session.idle`, Claude Code `Stop` hooks, or your own loop | the agent stops at every turn boundary |
| **Supervisor** | judge progress vs. stall, inject facts, enforce budget | nothing off the shelf — ~200 lines bespoke | blind `continue` forever |

Reliability ladder, do not skip rungs:
**app API / CLI → DOM/CDP → UIA/AT-SPI selector → vision grounding → image template → raw coordinates.**

## What was actually measured here

| Finding | Value |
|---|---|
| Windows UIA capture of VS Code as configured | **3 elements** (Minimize/Maximize/Close) — the chat panel is invisible until accessibility is switched on |
| RapidOCR over the same 1456×818 frame | 106 boxes, **18.99 s**; prose and button labels correct, embedded Python and every number mangled |
| `qwen3-vl:4b` reading a single button label | `Keep`, **~1.0 s**, 1241-token prompt |
| `qwen3-vl:2b/4b/8b` returning a click coordinate | **all empty** — thinking trace consumed the budget, `think:false` ignored |
| Copilot CLI 1.0.49 autopilot smoke test | `402 … monthly quota exceeded`, 0 changes |

Details, commands and caveats: [`MEASUREMENTS.md`](MEASUREMENTS.md).

## Files

| File | Contents |
|---|---|
| [`PC_AGENT_CONTROL_RESEARCH.md`](PC_AGENT_CONTROL_RESEARCH.md) | The main report: five layers, four topologies, ~20-tool catalog with licenses, universal surface matrix for every app class, the surface resolver, the 12-verb action grammar, the supervisor design (§5), guardrails, phased plan |
| [`TOOL_INTERFACE.md`](TOOL_INTERFACE.md) | The contract the kernel and supervisor share: 14 tools in 5 families, a common effect/verification envelope, approval classes 0–3, and the task-ledger schema |
| [`MEASUREMENTS.md`](MEASUREMENTS.md) | Every number measured on the reference machine, with reproduction commands |
| [`IMPLEMENTATION.md`](IMPLEMENTATION.md) | Peer implementation: a guarded observe → decide → act → verify loop (accessibility tree + viewport, one JSON action per turn, allowlist/irreversibility gate/budget, CDP click resolved at call time) |
| [`FACTCHECK.md`](FACTCHECK.md) | Four popular LLM answers audited against the actual repositories — what's real, what's unverified, what's wrong |
| [`probes/probe_ocr_vlm.py`](probes/probe_ocr_vlm.py) | The probe used for the OCR/VLM numbers (RapidOCR + Ollama vision) |
| [`kernel/capture.py`](kernel/capture.py) | Window-scoped capture + per-monitor-v2 DPI math: `Rect`, logical↔physical, client↔screen, `capture_region`, `crop_png`. Tests: [`tests/test_capture.py`](tests/test_capture.py) (8 passing) |

## Recommended stack (free, nothing to buy)

1. **Actuator:** `cua-driver` (already present) — background input, no cursor theft, UIA + AT-SPI + X11.
   Add `CursorTouch/Windows-MCP` (MIT, 12k★) if you want desktop control exposed as MCP tools inside
   Claude Desktop / Cursor. `munim-computer-use` (Apache-2.0) and `vercel-labs/agent-desktop`
   (Apache-2.0, 26k★) are real, credible alternatives — both accessibility-first with background input.
2. **Perceiver:** turn accessibility *on* wherever it is off (VS Code `editor.accessibilitySupport`,
   Electron `--force-renderer-accessibility`, JetBrains `jabswitch -enable`), then UIA/AT-SPI selectors;
   RapidOCR on **cropped regions** for text; never OCR for code or numbers.
3. **Grounder (only for the residue):** ShowUI-2B or UI-TARS-2B on a 12 GB card; OmniParser v2 if you
   want a labelled element list instead of a bare coordinate.
4. **Browsers:** Chrome DevTools MCP (`--autoConnect`) or Playwright MCP. Not pixels.
5. **Consoles:** `tmux send-keys` / `capture-pane`, or own the process and read stdout.
6. **Keep-going:** harness-native first (`copilot -p … --autopilot --max-autopilot-continues N`,
   Copilot SDK `session.idle` + `task_complete`, Claude Code `Stop` hook), then a supervisor that
   classifies the stop, injects a brief, and enforces budgets.
7. **Remote desktop:** control over SSH when it exists; RustDesk for watching. Pixels only as a last resort.

## Build order

- **Phase 0 — flip structure switches** (config only): Electron/JetBrains/terminal/browser accessibility, viewer scale for RustDesk.
- **Phase 1 — kernel** (`capture` / `resolve` / `act`, ~400 lines): one codebase, every app; acceptance test = drive VS Code + Windows Terminal + Explorer + Chrome in one run with no per-app code.
- **Phase 2 — channel upgrades:** tmux for consoles, CDP for browsers/Electron, adb for phones, SSH+AT-SPI for Linux hosts.
- **Phase 3 — supervisor:** task ledger, stop classifier, loop signatures, injected briefs, budgets, audit log.
- **Phase 4 — grounder** for canvas/game/RustDesk residue.

## Not in scope

Live-trading actions, credential handling, CAPTCHA solving, and any cloud computer-use API that ships your
screen off-machine. Automating consumer web apps can violate their terms — decide that per site, deliberately.

---

## Working implementation — `screen_control/` (added 2026-11-22, `deepseek-flash`)

The research above describes what *should* be built. This directory now also contains a
**running** implementation of the core loop, and it was exercised against a real browser.

| file | job |
|---|---|
| `screen_control/schema.py` | the 9 allowed verbs, `Action`/`StepResult`, validation |
| `screen_control/guard.py` | host allowlist · irreversibility gate · step/time/repeat budget |
| `screen_control/policy.py` | `ScriptedPlanner` · `LLMPlanner` (OpenAI-compatible) · `AgentPlanner` |
| `screen_control/transports.py` | `BrowserUseTransport` (CDP) · `MockTransport` (tests) |
| `screen_control/loop.py` | observe → decide → guard → act → verify → transcript |
| `tests/test_loop.py` | **9/9** mechanics tests, no browser, no model |
| `examples/live_demo.py` | **4/4** steps against a live page through CDP |
| `IMPLEMENTATION.md` | design notes, what was measured, and the honest limitations |
| `SAFETY.md` | threat model and the rules that follow from it |

It agrees with this folder's reliability ladder and picks the same rung: **DOM/CDP with the
accessibility tree**, not pixels. Two implementation choices are worth flagging because
they are failure modes the research above predicts:

- **Coordinates are resolved at act time** from `DOM.getBoxModel`, never baked in at decide
  time — this is the concrete fix for "coordinates drift".
- **Every action declares a post-condition**, so a click that changes nothing is recorded
  as a *failure*. Without it, a grounder that resolves the wrong element looks like success.

Two bugs were found only by running the demo, not by reading the code: `example.com` does
not resolve on the reference machine, and `Input.dispatchMouseEvent(type="mouseWheel")`
times out against this CDP daemon after 5 s (the transport now falls back to
`window.scrollBy`). Both are recorded in `IMPLEMENTATION.md`.

Run it: `python tests/test_loop.py` (mechanics, CI-enforced) then `python examples/live_demo.py`.

## Ownership — one owner per concern

The folder carries two implementations that share the research but not the runtime: this folder's `kernel/` (perception + supervision) and the peer's `screen_control/` (the running loop). Decision: **the peer's `screen_control/` owns the running loop** — observe → decide → guard → act → verify — and the `kernel/` owns perception (capture/DPI math) and supervision (overseer). The kernel's five-rung ladder (`resolve.py`) and the unwritten `act.py` (A1/A2, blocked pending a desktop session) remain documented policy, not a second runtime.

| Concern | Owner | Notes |
|---|---|---|
| Perception / capture | `kernel/capture.py` | Window-scoped capture, per-monitor-v2 DPI math, `Rect` logical↔physical↔client mapping. No click path lives here. |
| Rung decision / surface ladder | `kernel/resolve.py` | Five-rung ladder (API → A11Y → TEXT → MARKS → PIXELS) with per-window caching and re-probe on resize. Documented policy; not wired into the running loop. |
| Verbs + Action schema + planners | `screen_control/schema.py`, `screen_control/policy.py` | 9 verbs, `Action`/`StepResult` validation, Scripted/LLM/Agent planners. |
| Policy gate | `screen_control/guard.py` | Host allowlist, irreversibility gate (`confirm=True`), step/time/repeat budget. |
| Actuation / click path | `screen_control/transports.py` | The single execution path for click/type/key/scroll/navigate/read; box-model coordinates resolved at act time. |
| Observe→decide→guard→act→verify loop | `screen_control/loop.py` | Transcript + `MockTransport` for certification, CDP transport live. |
| Supervision | `kernel/overseer.py` | Stop classifier, signature hashing, brief injection, budgets, `STOP` file. |
| Mechanics certification | `tests/` | `test_capture.py`, `test_resolve.py`, `test_overseer.py` (kernel) and `test_loop.py` (loop); CI-enforced via `.github/workflows/screen-control-tests.yml`. |
| Approval classes (0–3) | [`TOOL_INTERFACE.md` §6 — Gate](TOOL_INTERFACE.md#6---gate) | 0=free, 1=reversible, 2=side-effecting, 3=irreversible; enforced by the tool layer, not the model's judgement. `kernel/act.py` does not exist (A2, blocked on a desktop session) — linkage deferred to A2. |

No duplicated capture path: the loop observes through its transport, never through `kernel/capture.py`. No duplicated click path: `screen_control/transports.py.execute()` is the only execution path; `kernel/act.py` does not exist and is not called anywhere.
