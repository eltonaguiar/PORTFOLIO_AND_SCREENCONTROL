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
