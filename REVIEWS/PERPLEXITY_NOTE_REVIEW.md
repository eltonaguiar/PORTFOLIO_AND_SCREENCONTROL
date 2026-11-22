# Review — Perplexity note (the two-layer plan)

Input: pasted 2026-11-22, ~2.2k words. Audited the same day against the GitHub API, the installed Hermes build,
and the measurements in [`../01-screen-control-llm/MEASUREMENTS.md`](../01-screen-control-llm/MEASUREMENTS.md).

**Verdict: the most technically sober of the five answers, and the only one that gets NautilusTrader's
architecture right ("Rust-native", "same core components for backtest and live"). Its weakness is naming — two
of its products could not be found — and it offers no numbers, no failure modes, and no injection mechanism for
"keep going" beyond a task ledger.**

## Claim audit

| Claim | Verdict | Reality |
|---|---|---|
| "NautilusTrader is open source, **Rust-native**, asset-class-agnostic, and its backtests use the same core components as live trading" | ✅ **correct, and rare** | Confirmed from source (`02-portfolio-multi-asset/NAUTILUS_ARCHITECTURE.md`): v2.0.0 is a Rust core (`nautilus-system` kernel) with one kernel shared by Backtest/Sandbox/Live. Caveat it omits: **PyPI stable is still 1.231.0 (Cython v1)**; v2 is RC-only |
| "Windows-MCP: MIT-licensed bridge for app/window/keyboard/mouse/native UI-state inspection" | ✅ | `CursorTouch/Windows-MCP`, MIT, **11,997★**, pushed 2026-11-22 |
| "ScreenHand … local native OS APIs, low-latency actions" | ❌ as described | Only `SayDoneAI/Screenhand` (0★, MIT) and `manushi4/Screenhand` (15★, AGPL). Nothing supports the low-latency/native-API characterisation |
| "`screen-use` … cross-platform desktop framework with visual perception" | ❌ | No repository matches; search returns screenshot helpers and unrelated projects |
| "Playwright / Browser Use for browser-native work; reserve pixel clicking for apps without an API" | ✅ | Playwright MCP Apache-2.0 39,989★; browser-use MIT 121,713★ |
| "For RustDesk, run a computer-use agent on the remote machine too" | ✅ | Exactly the conclusion the measurements force: a pixel-only channel loses the tree, exit codes and transcript. Add: prefer SSH when it exists (see §4.2 of the research doc) |
| "A plain LLM response stops because it has no persistent execution loop… durable task queue, scheduler, acceptance criteria, checkpoints, supervisor that reassigns stalled work" | ✅ correct framing | Matches the supervisor design, but stops short of the operational detail: *what* to do when the stop is a loop vs a quota wall vs an approval reflex |
| "Eigent — open-source multi-agent platform for browser/terminal/document/MCP execution" | ✅ | `eigent-ai/eigent`, **Apache-2.0, 15,867★**, pushed 2026-11-20 |
| "open-cowork — local desktops, cloud VMs, browsers, human-in-the-loop approval" | ✅ | `OpenCoworkAI/open-cowork`, **MIT, 2,283★**, pushed 2026-10-20 (plus `open-claude-cowork` forks at 4.3k/3.4k★) |
| "LumiBot — broker-connected bots, backtest/paper/live across brokers" | ✅ | `Lumiwealth/lumibot`, **GPL-3.0, 2,245★**, pushed 2026-11-21 |
| "Nuphus" (in its own suggested follow-up: "Nuphus vs Open Computer Use vs Agent S3") | 🟡 real but tiny | `mrpulor-gh/nuphus-mcp`, MIT, 336★ — a small MCP project, not a peer of Agent-S |
| "vectorbt supports fees, slippage, leverage, futures multipliers, and **shared portfolio cash**" | ✅ largely | Accurate feature description; still a vectorised simulation, not an event-driven fill model — and its GitHub licence reports NOASSERTION |
| "vectorbt supports multipliers but does not automatically handle contract rolls" | ✅ good catch | One of the few answers to name a concrete futures gap |
| "Bonds / mutual funds … generic OHLCV backtesters are usually inadequate" | ✅ | Correct, and stronger than most answers allow |
| "Task ledger: goal, subtasks, current owner/window, last observation, next action, evidence, completion criteria" | ✅ useful | Adopted into the tool-interface spec — this is the right schema for the supervisor's state file |
| "A sensible first deliverable is a local MCP toolkit: screenshot, read_window, click, type, list_windows, browser_navigate, browser_extract, run_python, save_artifact, query_market_data, run_backtest, request_approval" | ✅ **best single idea in the batch** | Written up as [`../01-screen-control-llm/TOOL_INTERFACE.md`](../01-screen-control-llm/TOOL_INTERFACE.md) with contracts and approval rules |
| "Use APIs, official SDKs, or a sandboxed browser profile for anything involving trading, credentials, or irreversible actions" | ✅ | Consistent with every other answer and with this repo's scope boundary |
| "Open one orchestrator with a task queue + state DB (SQLite/Postgres), APScheduler or Celery" | ✅ reasonable | For one machine a file-backed ledger and a single process is enough; reach for a queue when concurrency > 1 |

## Notable omissions (relative to the other answers)

- No mention of **accessibility switches** (Electron a11y, Java Access Bridge) — the cheapest reliability win
  measured here.
- No mention of **grounding models** for canvas/remote surfaces, so its "vision fallback" has no implementation.
- No continuation mechanics per harness (flags, hooks, `session.idle`) — the ledger alone does not restart a
  vendor agent's tool loop.
- No numbers: no latency, no token cost, no failure rates. Its recommendations are structurally right and
  empirically empty.

## What was folded into the repository

1. [`TOOL_INTERFACE.md`](../01-screen-control-llm/TOOL_INTERFACE.md) — the twelve-tool MCP contract plus the
   task-ledger schema, with approval gates and verification rules. This is the interface the kernel
   (`capture`/`resolve`/`act`) and `overseer.py` were both missing.
2. `REVIEWS/README.md` index entry for this audit.

## Scoreboard across the five answers

| Answer | Structure | Factual accuracy | Numbers | Actionable |
|---|---|---|---|---|
| Grok | good | mixed (real + invented) | none | medium |
| Mercury | good sketch | mixed | none | low (placeholder API) |
| SUB Q (both notes) | best formatted | weakest citations (repeated hallucination) | stale | high on ops advice |
| Arena playbook | good | high | none | high on policy |
| **Perplexity** | good | **highest on frameworks** | none | **highest on interface** |

---

# Addendum — `deepseek-flash`, 2026-11-22 10:10 EST

The audit above is thorough on the **screen-control** half and I am not repeating it: I
re-checked its factual table against the GitHub API on 2026-11-22 and every finding holds
(`Windows-MCP` 11,999★ MIT; `SayDoneAI/Screenhand` 0★ and `manushi4/Screenhand` 15★, neither
matching the "low-latency native API" description; `screen-use` still returns no matching
repository; `eigent-ai/eigent` 15,867★ Apache-2.0; `OpenCoworkAI/open-cowork` 2,283★ MIT;
`mrpulor-gh/nuphus-mcp` 336★).

This addendum covers the **backtesting half**, which the audit above only touches, and it
adds the one thing a documentation review cannot: what happens when you build this note's
recommended gate list and run it.

## A1. Licensing — four engines, one undisclosed constraint each

The note recommends engines by capability and never mentions licence. That is a material
omission because two of the four most-affecting picks are copyleft:

| engine | note's framing | licence (GitHub API, 2026-11-22) | what it means |
|---|---|---|---|
| `nautechsystems/nautilus_trader` | "open source, Rust-native" — correct | **LGPL-3.0**, 31,735★ | LGPL is fine for most use, but it is not permissive: static linking / modification carries obligations the note does not state |
| `polakowo/vectorbt` | "vectorbt / vectorbt.pro" presented together | **NOASSERTION** (not an OSI tag), 9,911★ | and **`vectorbt.pro` has no public repository** — the GitHub API returns only third-party wrappers, so the paid tier cannot be audited the way vectorbt can. Treating them as one option is misleading |
| `kernc/backtesting.py` | "lightweight, easy to learn" | **AGPL-3.0**, 9,276★ | AGPL is the strictest of the set. Recommending it with no warning is the most consequential omission here — anyone shipping a service around it inherits network-copyleft obligations |
| `Lumiwealth/lumibot` | "broker-connected bots" | **GPL-3.0**, 2,245★ | as above |
| `pmorissette/bt` | "portfolio construction" | MIT, 3,045★ | clean |

A reader following this note's stack without checking licences could end up with an AGPL
component in a commercial product. That is a bigger risk than any architectural nit.

## A2. The gate list is the note's best idea and it is missing the decisive gate

The note's §4 closes with: *"Add evaluation gates: out-of-sample testing, transaction costs,
slippage, position limits, drawdown limits, data-quality checks, and reproducible run
artifacts."*

This repository implemented **all of those** and ran them across **126 cells** (7 crypto
majors × 6 pre-registered hypotheses × 1h/4h/1d). Result: **0 cells qualified.**

| the note's gate | implemented here | outcome across 126 cells |
|---|---|---|
| transaction costs | 26 bps round turn, both legs | 5 of 6 families negative *before* any cost at 1h |
| slippage | 3 bps per side, baked into fill prices | included above |
| position limits | 1% equity risk at the stop, 1× notional cap | applied |
| drawdown limits | computed per book | best single book −8.8%, worst −31.6% |
| out-of-sample | 4h/1d windows, 3.3 y for daily | 0 cells above deflated Sharpe 0.95 |
| data quality | 5-venue quote consensus; bars cached per run | no bar dropped |
| reproducible artifacts | timestamped JSON + append-only ledger per run | every number traceable |

**The gate that killed every candidate is not on that list.** Two were needed:

1. **Trial accounting / deflated Sharpe.** With 126 cells the expected best in-sample Sharpe
   from pure noise is not zero. The best cell here reached DSR **0.256** against a 0.95 bar —
   a number that looks like a finding until it is deflated by the number of cells tried.
   "Out-of-sample testing" does not fix this: OOS still lets you pick the best of N OOS
   results.
2. **A permutation control.** Shuffle the bar-to-bar returns, rebuild a price path, re-run the
   same rule. Here every strategy's realised mean sat inside the shuffled distribution
   (best p = 0.20 / 0.28 / 0.40 across timeframes). One case is the clearest illustration in
   the whole run: H-R4 vol-compression goes from **−32.1 bps at 1h to +20.4 bps at 1d**, a
   genuinely plausible horizon effect — and its permutation **p = 0.40** shows the same rule
   reproduces that mean on *shuffled* prices. It is a bracket-and-entry-timing property, not
   market structure. Without the control, that cell gets promoted.

So the note's gate list is necessary and **not sufficient**. Add trial accounting and a shuffle
control, or a rigorous-looking gate table still certifies noise. Artifacts:
[`../03-trading-strategies/TIMEFRAME_MATRIX.md`](../03-trading-strategies/TIMEFRAME_MATRIX.md),
[`../03-trading-strategies/HARNESS_CERTIFICATION.md`](../03-trading-strategies/HARNESS_CERTIFICATION.md)
(certification test **T4** is exactly this: 0 of 60 pure-noise cells reach DSR 0.95).

## A3. Engine choice is not the binding constraint

The note's core recommendation is the two-tier stack: *vectorbt for research, NautilusTrader
for production*. Both picks are defensible and match
[`../03-trading-strategies/LIBRARY_SURVEY.md`](../03-trading-strategies/LIBRARY_SURVEY.md).

But the measured evidence says the binding constraint is **not** engine throughput or
execution fidelity. Across 126 cells, with an engine that is certified on look-ahead, cost
drag and intrabar ordering, the constraint was: **the per-trade edge is smaller than the
round-turn cost.** Mercury3's independent 30-symbol 5m run reached the same place from
another codebase: gross +28.02%, fees 250.80%, net −222.78% — the fee line is 9× the edge.

Choosing NautilusTrader over vectorbt changes how faithfully you simulate a strategy that
does not have enough edge to survive 26 bps. It does not create edge. The stack advice is
right and it is secondary; the note's silence on "what if nothing clears cost" is the gap
that matters, and it is the gap this repository has now measured.

## A4. What was adopted from the note (unchanged from the audit above)

The twelve-tool MCP contract and the task-ledger schema are genuinely the best artefacts in
this batch of answers and are already written up in
[`../01-screen-control-llm/TOOL_INTERFACE.md`](../01-screen-control-llm/TOOL_INTERFACE.md).
The safety line — *"use APIs, official SDKs, or a sandboxed browser profile for anything
involving trading, credentials, or irreversible actions"* — is the same boundary
`01-screen-control-llm/SAFETY.md` draws, and the implementation enforces it with an
irreversibility gate that refuses any action whose target name contains a destructive verb
unless `confirm` is set.
