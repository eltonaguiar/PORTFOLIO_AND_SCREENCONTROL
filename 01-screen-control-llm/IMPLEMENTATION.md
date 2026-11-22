# Screen control via LLM / AI

A guarded **observe → decide → act → verify** loop that lets a language model drive a real
screen, without letting it do anything unrecoverable.

```
            ┌──────────────┐
  screen ──▶│  perceive    │  accessibility tree + viewport + visible text
            └──────┬───────┘
                   ▼
            ┌──────────────┐
            │  decide      │  ONE JSON action per turn (Scripted / LLM / Agent-in-loop)
            └──────┬───────┘
                   ▼
            ┌──────────────┐
            │  guard       │  allowlist · irreversibility gate · budget
            └──────┬───────┘
                   ▼
            ┌──────────────┐
            │  act (CDP)   │  box model resolved at click time, never baked in
            └──────┬───────┘
                   ▼
            ┌──────────────┐
            │  verify      │  declared post-condition, checked against the new screen
            └──────┬───────┘
                   ▼
              transcript (append-only, auditable)
```

## Status — verified, not asserted

| claim | how it was checked | result |
|---|---|---|
| the loop mechanics work | `tests/test_loop.py`, 9 isolated cases on an in-memory screen | **9/9 pass** |
| it drives a real browser | `examples/live_demo.py` against a live page via CDP | **4/4 steps pass**, transcript on disk |
| the guard refuses off-allowlist navigation | test T2 | refused before the request |
| the guard refuses destructive clicks without `confirm` | tests T3, T4 | `"delete account"` and `Enter` on `"Send money"` both blocked |
| repeated actions are capped | test T5 | 10 refusals, loop cannot spin |
| a silent no-op click is caught | test T7 | unmet `expect` marks the step failed |

## The five design decisions that matter

**1. Element space, not pixel space.**
The observation is the Chromium accessibility tree filtered to interactive roles, each
node carrying its `backendDOMNodeId` as a handle and its accessible *name*. A model can
reason about "Send money" — it cannot reason about `(412, 588)`. Click coordinates are
resolved from the live box model at **act** time, so scroll, zoom, DPI change and sticky
headers cannot silently redirect the click.

**2. Every action declares a post-condition.**
`expect: "Order confirmed"` is verified against the page after the action. A click that
"succeeds" but changes nothing is recorded as a **failure**. This is the single most
common silent agent bug, and it is invisible without an explicit expectation.

**3. The guard has three independent limits, because each one alone fails.**
Allowlist kills prompt-injected navigation. The irreversibility gate kills "the agent
filled the form and also submitted it". The budget kills the model that repeats itself
forever. Refusals are *data* — recorded in the transcript, not raised as exceptions, so a
reviewer sees exactly what was attempted and denied.

**4. The planner is an interface with three implementations.**
`ScriptedPlanner` (deterministic) exists so the mechanics can be certified **without a
model** — otherwise a failure is ambiguous between "model error" and "loop bug".
`LLMPlanner` is any OpenAI-compatible endpoint. `AgentPlanner` is agent-in-the-loop:
observation printed, one JSON action read back on stdin — which is how a human or an
external agent drives the same guarded loop.

**5. Irreversibility is decided by target name, not just verb.**
`type` and `key` are the "dangerous" verbs, but a click on a button named *Delete account*
is worse than typing into a search box. So the gate also scans the accessible name against
a destructive-word list, and requires `confirm: true` either way.

## Layout

```
screen_control/
  schema.py      the 9 allowed verbs + Action/StepResult, with validation
  guard.py       allowlist · irreversibility gate · step/time/repeat budget
  policy.py      ScriptedPlanner · LLMPlanner · AgentPlanner
  transports.py  BrowserUseTransport (CDP) · MockTransport (tests)
  loop.py        the closed loop + transcript
tests/test_loop.py        9 mechanics tests, no browser, no model
examples/live_demo.py     real-browser run, benign and repeatable
docs/SAFETY.md            threat model and the rules that follow from it
```

## Run it

```bash
cd 01-screen-control-llm
python tests/test_loop.py          # mechanics: 9/9
python examples/live_demo.py       # needs a browser; see the file header
```

Driving it with a model:

```python
from screen_control import Guard, GuardConfig, LoopConfig, ScreenLoop, LLMPlanner, BrowserUseTransport

loop = ScreenLoop(
    BrowserUseTransport(js=js, cdp=cdp, screenshot=shot, navigate=goto),
    LLMPlanner(base_url="https://api.openai.com/v1", model="gpt-4o-mini"),
    Guard(GuardConfig(allowed_hosts={"app.example.com"}, max_steps=20)),
    LoopConfig(transcript_dir="transcripts"),
)
print(loop.run("Find the invoice for August and read out its total"))
```

## Honest limitations

- **No vision fallback yet.** If a control is a bare `<div onclick>` with no accessible
  name, it will not appear in the observation. A screenshot + coordinate path exists in
  the schema (`x`/`y`) but is not model-driven today.
- **`verify` is lexical, not semantic.** It checks whether the expectation's content words
  appear on the page. That catches no-ops and wrong-page navigation; it will not catch a
  subtly wrong value.
- **The scroll verb needed a JS fallback.** Live testing showed
  `Input.dispatchMouseEvent(type="mouseWheel")` timing out against this CDP daemon after
  5 s; the transport now falls back to `window.scrollBy`. That bug was found by running
  the demo, not by reading the code.
- **No multi-tab / frame handling.** One page, top frame.
- **Not tested against hostile pages.** The allowlist is the mitigation, not a proof.
