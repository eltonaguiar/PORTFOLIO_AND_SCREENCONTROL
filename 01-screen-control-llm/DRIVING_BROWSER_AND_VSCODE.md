# Driving a browser vs driving VS Code — same question, two surfaces, two methods

Measured on 2026-11-22 on this host. Short answer: **they are different methods**, and the browser run in
this session did **not** use CDP — it used UIA + synthetic input + the clipboard. CDP was used earlier in
the day for a *different* pair of sites.

## The one rule that decides the method

> Use the highest rung that answers: **app API/CLI → DOM/CDP → accessibility (UIA/AT-SPI) → text layer →
> element detection → raw pixels.** Each rung down costs about an order of magnitude in reliability.

The surface picks the rung, not preference. Both of today's targets are Chromium-family, which is exactly
the trap: Chrome-the-browser was drivable three different ways; VS Code only one-and-a-half.

## Side by side

| | **Browser** (duck.ai in Chrome 157) | **VS Code** (pid 25836, SSH remote) |
|---|---|---|
| Method used | `computer_use` = cua-driver, **UIA + synthetic input** | `computer_use` = cua-driver, **UIA + synthetic input** |
| CDP? | **No** for this run (CDP was used earlier for arena.ai / 1min.ai) | **No** — Electron, no debug port open, and relaunching for `--remote-debugging-port` would risk the other agents' sessions |
| What the a11y tree gave | composer `#29 Edit 'Ask anything privately'`, submit `#35 Button 'Ask'` — enough to do the whole job by element | the **chrome** only: 127 elements = tabs, panel buttons, terminals. Not one webview composer |
| What it did NOT give | — | the Copilot chat input and transcript (transcript nodes sit at **negative y** = virtualized, and there is no `Edit` node for that composer at all) |
| Text entry | `set_value(#29, prompt)` | click composer by **pixel**, then foreground `type` |
| Submit | `click(#35)` — after a **fresh** capture | foreground `return` |
| Answer capture | select-all + copy → clipboard (**11,018 chars**) | not needed; read state from the transcript prose |
| Failure that cost the most | coordinate clicks: `coordinate=` is **screenshot space**, driver scales ×1.32; I passed native coords, so `(1550,980)` posted at `(2044,1292)` — outside a 1920×1080 window, silently | focus routing: `Ctrl+Alt+I` ("Chat") went to the **middle** panel's agent chat, so the first nudge typed into the box you told me not to touch |

## So what actually happened, in order

**Browser (duck.ai, no login).** Capture → `#29` composer, `#35` Ask button both present. `set_value` filled
it; the first `click(#35)` did nothing because a `vision` capture in between had invalidated the snapshot
indices (`snapshot_id_required`). Re-captured `ax`, clicked `#35` again from that snapshot → answer streamed
(model `GPT-6 Luna`). Harvest was **not** a tree dump: click a blank gutter, `Ctrl+A`, `Ctrl+C`, read the
Windows clipboard → 11,018 chars including the whole methodology answer.

**VS Code.** `capture mode=ax` returned 127 elements — but they are all *outer* UI. The two things I needed
(the Copilot composer, the Zoo Code composer) are webviews, and only the **middle** agent panel exposed an
`Edit` node (`#76 @ [529,926,559,20]`), which is precisely the one I must not touch. So the method had to
split: **elements for state, pixels for the webview composer, foreground keys for the text.**

Pixel targeting works only once you accept the coordinate contract: **`coordinate=` takes screenshot pixels
and the driver multiplies by the scale (1.32 here)**. Copilot's composer lives at screenshot `(1170,744)`;
passing that posted `(1543,981)` and landed. Everything before that was arithmetic against native bounds,
and every one of those clicks missed.

## One hazard worth its own line

VS Code maps `Ctrl+Alt+I` to "Chat", and with three agent panels open it focused the **middle** one. The
typed text therefore appeared in the panel marked *do not touch*. It was cleared with `Ctrl+A`, `Delete`
before `Enter` was ever pressed, so nothing was submitted — but the lesson is:

> **Keyboard shortcuts are ambiguous when several panels register the same command. Verify the caret
> visually in a capture BEFORE pressing Enter, and clear rather than retry.**

## Both agents ended up working, and the feedback loop is why

- **Copilot** (right panel) was idle: "Completed 65 steps in 5m 24s", 29 files changed, item 6 of 8 open.
  Nudge: *"Continue: finish item 6 (strategy_variant on emitted picks), then re-run the harness
  certification…"* → it accepted, ran `rg` over `alpha_engine/audit_sync.py`, found bare `except` at
  **725, 768, 793, 813, 837, 964**, and moved to considering.
- **Zoo Code** (left panel) was stopped and asking for two decisions (push approval; a mixed
  `hypothesis_registry.json`). Answering those two questions restarted it at 38%, step **2/8** of `P1:
  VERIFY DISK STATE before any push`, with a live stop button.
- **Zoo Code corrected me**, which is the point of injecting an instruction rather than a plan: it rejected
  my `audit3_tml.json:8843` claim — the file is a Python module, the real citations are **1639** and **1642**
  inside `alpha_engine/audit3_tml.py`. An agent that answers back is working; one that says "done" is not
  evidence of anything.

## When CDP *was* the right answer (same day, different sites)

arena.ai and 1min.ai exposed one opaque `Group` to UIA and kept their composer in contenteditable hosts, so
element clicks found nothing. For those, a dedicated profile plus
`chrome.exe --remote-debugging-port=9222 --user-data-dir=C:/Users/zerou/chrome-agent-profile` and Playwright
`connect_over_cdp("http://127.0.0.1:9222")` was the only route that worked — `select_option` on a native
`<select>`, `keyboard.insert_text` into ProseMirror, and key events that ignore window focus.

That is the whole distinction:

| Need | Rung |
|---|---|
| Page has a real DOM and you must read or fill it precisely, at scale, repeatedly | **CDP** (dedicated profile, port 9222) |
| Page is a normal consumer site, one question, no login, and a human-sized answer | **UIA + clipboard** (a regular Chrome launch is enough) |
| Native/Electron app shell | **UIA elements** |
| A webview inside that app (chat composers, canvas, editors) | **pixels at screenshot scale**, verified by capture before any submit |
| Nothing accessible at all | OCR on a crop for *state* only — never for code, numbers or paths |

## Reproduce the two wins

```bash
# browser: no CDP, no login, element handles + clipboard
#   capture(mode="ax") -> set_value(element=<composer>, value=<prompt>) -> fresh capture -> click(element=<send>)
#   then: click a blank gutter, ctrl+a, ctrl+c, and read the clipboard
powershell -NoProfile -Command "(Get-Clipboard -Raw) | Out-File -Encoding utf8 out.txt"

# VS Code: element handles for state, pixels for the webview composer (x1.32 from screenshot to native)
#   capture(mode="ax")                     -> read tabs/buttons/terminals
#   click(coordinate=[1170, 744])          -> Copilot composer   (posts 1543,981)
#   click(coordinate=[117,  714])          -> Zoo Code composer  (posts  155,942)
#   type(text=..., delivery_mode="foreground"); capture; VERIFY; then key("return", foreground)
```

## Evidence class

Everything above is **observed** on this host: element indices and bounds came from live captures, the
clipboard harvest size is a `wc -c`, and the two agent states (65 steps / 19.3k context and 2/8 on P1) were
read from screen. The ×1.32 factor is measured from two independent postings. Nothing here is derived from
documentation.
