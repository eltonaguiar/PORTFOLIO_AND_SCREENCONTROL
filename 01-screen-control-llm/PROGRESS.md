# PROGRESS — screen control via LLM / AI

Append-only running log for the **implementation** in this folder. The research documents
(`PC_AGENT_CONTROL_RESEARCH.md`, `MEASUREMENTS.md`, `FACTCHECK.md`, `TOOL_INTERFACE.md`)
have their own provenance rules and are not duplicated here.

Every row points at a file or a test output. Newest session at the top.

Legend: `RUN` executed · `PASS`/`FAIL` result · `FIX` defect found and fixed · `DOC` written
· `PEER` reconciliation.

---

## Session 1 — 2026-11-22 (09:00–09:35 UTC) — `deepseek-flash`

Question: can the research in this folder be turned into a loop that actually drives a
screen, and can its guardrails be *proved* rather than asserted?

### Built

| time (UTC) | status | item | artifact |
|---|---|---|---|
| 09:00 | DOC | Loop contract fixed as 9 verbs (`click`, `type`, `key`, `scroll`, `navigate`, `wait`, `read`, `done`, `fail`); unknown verbs are a hard error, not an improvisation | `screen_control/schema.py` |
| 09:02 | DOC | Three independent limits, because each fails alone: host allowlist (prompt-injected navigation), irreversibility gate (destructive accessible name needs `confirm: true`), budget (steps/seconds/consecutive failures/repeat signatures) | `screen_control/guard.py` |
| 09:04 | DOC | Planner as an interface — `ScriptedPlanner` (certify mechanics without a model), `LLMPlanner` (OpenAI-compatible, dependency-free urllib), `AgentPlanner` (observation to stdout, one JSON action back on stdin) | `screen_control/policy.py` |
| 09:05 | DOC | Transport split: `BrowserUseTransport` over CDP (injected `js`/`cdp`/`screenshot`/`navigate`) and `MockTransport` for tests | `screen_control/transports.py` |
| 09:07 | PASS | **9/9** mechanics tests on `MockTransport` — happy path, off-allowlist refusal, destructive click, Enter on a destructive target, repeat cap, invalid verb, unmet expectation, consecutive-failure abort, transcript written | `tests/test_loop.py` |
| 09:08 | FIX | Test T5 initially passed for the wrong reason: the repeated action was a destructive click, so the *irreversibility* gate refused it before the repeat counter could fire. Replaced the fixture with a benign repeated button — the test now exercises the budget it claims to | `tests/test_loop.py` |
| 09:09 | FIX | Test T6 asserted "invalid action" but `ScriptedPlanner` validated eagerly, so the failure surfaced as "planner error". Moved validation into the loop so a bad scripted action and a bad model action take the same code path | `screen_control/policy.py` |
| 09:10 | RUN | First live-browser attempt failed: `example.com` does not resolve on this machine and the demo derived its package path from `__file__`, which points at the harness when exec'd. Both fixed | `examples/live_demo.py` |
| 09:12 | FAIL | Live run 1: 3/4 steps. `scroll` raised `_IPCResponseTimeout: Input.dispatchMouseEvent timed out after 5s` — `mouseWheel` is not answered by this CDP daemon | transcript `20261122_041358` |
| 09:13 | FIX | Scroll now falls back to `window.scrollBy` when the wheel event times out, and reports the scroll position before/after so the fallback is visible in the transcript rather than silent | `screen_control/transports.py` |
| 09:14 | PASS | Live run 2: **4/4** steps against `iana.org` — navigate + verify 2/2 expectation words, read 1,256 chars, scroll 0→400 px, done | `transcripts/transcript_20261122_041417.json` |
| 09:22 | PASS | `screen-control-tests` green in GitHub Actions on Ubuntu 3.11 (9/9) — the mechanics are CI-enforced, so a regression fails a build instead of a demo | Actions run 45007260204 |
| 09:31 | PASS | Re-verified **4/4** live after the folder was moved into `01-screen-control-llm/` | transcript `20261122_042231` |
| 09:33 | PEER | Reconciled against `TOOL_INTERFACE.md` approval classes 0–3: this loop implements a coarser two-state version and infers class from the **target's accessible name**, so a button labelled "Go" that submits a payment would pass. Recorded as a round-2 fix (declare class, take the max of declared and inferred) | `IMPLEMENTATION.md` limitations · `../03-trading-strategies/PEERCROSSCHECK_deepseek-flash.md` §9 |

### Standing state after session 1

- **Mechanics: certified.** 9/9 in CI, 4/4 on a live page.
- **Vision fallback: absent.** A `<div onclick>` with no accessible name is invisible to the
  observation. The `x`/`y` verbs exist in the schema but are not model-driven yet.
- **`verify` is lexical, not semantic.** Catches no-ops and wrong-page navigation; will not
  catch a subtly wrong value.
- **Approval class is inferred, not declared** — the known gap, above.

### What session 2 should do

1. Add a grounding rung: accessibility tree → DOM text → OCR → grounding model, with the
   same post-condition discipline, so canvas apps stop being invisible.
2. Make approval class explicit and take `max(declared, inferred)`.
3. Multi-frame / multi-tab observation.
4. Replace lexical `verify` with a per-action typed assertion (`text_equals`,
   `element_state`, `url_matches`) so "did it work" stops being a word-overlap guess.

---

## Session template (copy for each new session)

```
## Session N — <date> (<start>–<end> UTC) — <agent>
<one line: what question this session answered>

| time (UTC) | status | item | artifact |
|---|---|---|---|
| | | | |

Standing state: <tests / live steps / open gaps>
```
