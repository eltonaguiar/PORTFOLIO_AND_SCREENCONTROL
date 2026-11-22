# Portable AI Agent Playbook: Desktop Control, Persistent Work, and Market Research

**Purpose:** a reusable starting point to hand to coding/chat agents in an IDE or terminal on Windows, Linux, or macOS. It separates *how the agent sees/acts*, *how work survives and gets checked*, and *how financial strategies are researched/backtested*.

> **Important:** This is a research/backtesting and paper-trading blueprint, not a recommendation to trade. Never let an LLM place live orders or handle broker credentials without explicit, scoped human approval.

## Short recommendation

Build a small **local agent runner + adapters**, rather than relying on one giant prompt or one universal desktop-control server:

1. **Browser:** use Microsoft's Playwright MCP for websites and browser tabs. It reads structured accessibility snapshots and interacts with page elements, which is generally more reliable than pixel coordinates. [Playwright MCP](https://github.com/microsoft/playwright-mcp)
2. **Desktop / IDE / remote desktop:** run a computer-use adapter on the machine whose desktop must be controlled. Prefer each OS's native accessibility/UI automation API; use screenshots + mouse/keyboard only when semantic controls are unavailable. A RustDesk session is still just a desktop surface: for dependable input, the adapter normally needs to run in the interactive session on the remote target (or on the controlling host if only its RustDesk window can be operated). A community RustDesk bridge illustrates that deployment shape, but validate its maintenance, platform support, and permissions before use. [Example bridge listing](https://glama.ai/mcp/servers/jeremiejt38/rustdesk-mcp-bridge)
3. **Agent persistence:** use **Temporal** when jobs must survive crashes, wait for markets/replies, retry safely, and be inspected or resumed. Use **LangGraph** when you primarily need a Python/LLM workflow with checkpoints and human approval. A chat history or repeated prompt is not a durable task runner. [Temporal durable execution](https://docs.temporal.io/evaluate/understanding-temporal) · [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview)
4. **Backtesting:** start by evaluating **QuantConnect LEAN** for conventional multi-asset event-driven simulation, and **NautilusTrader** when identical strategy code across historical backtest and live/paper systems, custom instruments, or multi-venue use matters. Neither removes the need to source and validate data. For mutual funds and niche bonds, expect to supply/normalize data and possibly write an adapter/custom instrument layer. [LEAN assets](https://www.quantconnect.com/docs/v2/writing-algorithms/securities/asset-classes) · [LEAN source](https://github.com/QuantConnect/Lean) · [NautilusTrader instruments](https://nautilustrader.io/docs/latest/concepts/instruments/)
5. **MCP is the tool interface, not the supervisor:** expose browser, desktop, market-data and backtest capabilities as separate least-privilege tools. MCP standardizes tool discovery/calls across compatible hosts; it does not by itself keep an agent working or make actions safe.

## Practical architecture

```text
Human goal + acceptance tests
          |
Durable workflow runner (Temporal; or LangGraph for a lighter Python agent workflow)
          |-- task state / checkpoints / deadline / retries / heartbeat / audit log
          |-- agent adapters: MCP client, CLI, API, IDE-specific agent integration
          |-- evidence gate: tests, source links, data timestamps, reproducible run IDs
          |
Local capability adapters on each machine
          |-- browser: Playwright MCP
          |-- desktop: native accessibility first; screenshot/input fallback
          |-- remote desktop: control the RustDesk window or install an adapter in the remote interactive session
          |-- market data: provider/API + normalized local data store
          |-- research/backtest: LEAN or NautilusTrader + report exporter
```

### Cross-platform reality

A portable **contract** is feasible; one identical low-level UI driver for every desktop is not. Install/authorize an adapter separately on each Windows/Linux/macOS machine, and verify the actual display server (X11 vs Wayland), permissions, session type, and remote-desktop behavior. For headless Linux, use a virtual display only when the target application can run in that environment. For browser tasks, prefer DOM/accessibility-based Playwright instead of screen coordinates. On a remote desktop, install the agent bridge in the remote interactive session if the remote apps need direct control. Never expose a raw desktop-control endpoint to an untrusted network.

### “Keep working” means a monitored workflow, not an endless agent loop

For every task, define:
- a durable `task_id`, goal, deadline, and stop conditions;
- explicit stages and outputs (research, data check, run, validation, report);
- heartbeat/progress events and a maximum no-progress interval;
- bounded retries, backoff, and a human escalation path;
- persisted logs, exact tool inputs/outputs, source/data timestamps, and run artifacts;
- a verifier that checks acceptance criteria before marking the task complete.

Do not retry side-effecting UI actions blindly: first inspect current state. Require confirmation for destructive actions, broker login changes, order placement, payments, account changes, or sending external messages. Provide a conspicuous stop/pause control.

## Reusable market/backtest options

| Option | Good fit | Watch-outs |
|---|---|---|
| **QuantConnect LEAN** | Python/C#; event-driven research and backtesting across equities, equity/index/futures options, futures, forex, crypto, crypto futures, and CFDs; open-source engine and CLI. [Docs](https://www.quantconnect.com/docs/v2/writing-algorithms/securities/asset-classes) · [GitHub](https://github.com/QuantConnect/Lean) | The engine is not the data. Local runs require local data and vendor terms may restrict redistribution. Confirm the precise instrument, venue, resolution, and model support. Mutual-fund NAV data may need to be imported as custom data; LEAN's standard asset-class list does not list mutual funds as a dedicated class. [LEAN CLI/data notes](https://www.quantconnect.com/docs/v2/lean-cli/key-concepts/data) |
| **NautilusTrader** | Python/Rust, event-driven; backtest/paper/live parity; instruments include equity/ETF, FX/crypto pairs, commodities, futures, options, CFDs, and custom/synthetic instruments. Its documented Interactive Brokers adapter also lists bonds and bond funds. [Instruments](https://nautilustrader.io/docs/latest/concepts/instruments/) · [IB adapter](https://nautilustrader.io/docs/nightly/integrations/ib/) · [GitHub](https://github.com/nautechsystems/nautilus_trader) | More engineering-oriented; instrument definitions, adapters, and licensed historical data still matter. Check current docs/release support for the exact product before committing. |
| **vectorbt** | Fast vectorized strategy research and parameter sweeps in Python; useful as a research companion for large grids. [Project](https://github.com/polakowo/vectorbt) | Not a universal event-driven market simulator; add realistic fills, fees, corporate actions, funding, borrow, and instrument-specific rules or validate elsewhere. |

**Suggested default:** if you need a single first engine for normal stocks/ETFs, futures, FX, crypto and options, prototype LEAN. If you need broad custom instrument definitions or same-code backtest-to-live and have engineering capacity, prototype NautilusTrader. Do a short representative-data proof of concept before selecting. “Supports an asset class” does not mean that every product has good data or realistic simulation. Mutual funds usually need daily NAV/total-return data and specific distribution/fee treatment; futures need roll rules; FX/crypto need venue, spread, funding/swap and timestamp policies; bonds need coupon/accrual, clean-vs-dirty price, and calendar handling.

## Data and evidence rules (mandatory for market research)

For every input series, record:
- provider/source and retrieval timestamp (UTC), symbols/contracts, venue, timezone, frequency, and price type (trade, quote, midpoint, NAV);
- whether data are live, delayed, or historical; the measured delay/last-update time; missing bars and stale-feed checks;
- adjustment policy (splits/dividends/distributions), contract rolls, survivorship/look-ahead controls, and license/redistribution restrictions;
- fees, bid/ask spread, slippage, financing/funding/swap, borrow, margin, and market-calendar assumptions.

A backtest report must include strategy/version hash, data snapshot or immutable data reference, date range, assumptions, benchmark, trades, equity curve, return, volatility, drawdown, exposure, and out-of-sample/walk-forward results. The agent must label facts as **observed**, **derived**, or **assumed**, link the evidence, and say “not verified” when it cannot prove a claim. A live quote is not proof of future market behavior.

## Host-neutral handoff prompt (copy this into an agent)

```text
You are one worker in a supervised, persistent research workflow. Do not claim to be running after this invocation unless the workflow runner reports a live heartbeat.

Goal: {GOAL}
Task ID: {TASK_ID}
Deadline: {DEADLINE_UTC}
Allowed scope: {READ_ONLY / RESEARCH / PAPER_TRADING}
Acceptance tests: {TESTS}

1. Inspect available tools and report what you can actually access (browser, desktop, remote desktop, files, market data, backtester). Do not assume a tool exists.
2. Break the goal into short, observable stages. Persist a checkpoint and emit progress after each stage. If blocked or stalled, report the blocker and request a human decision; do not silently loop.
3. Prefer documented APIs and accessibility-based browser automation. Use desktop clicks only when needed, inspect the screen before acting, and verify the resulting state after each important action.
4. For market claims, identify exact instrument, venue, source, timestamp and whether data are real-time, delayed or historical. Never fabricate data or cite a simulated/test feed as real. Respect provider licenses.
5. For a backtest, state assumptions and costs, guard against look-ahead/survivorship bias, use a reproducible data snapshot, and run out-of-sample or walk-forward checks. Report failures as well as successes.
6. Do not place live orders, reveal credentials, change accounts, or perform irreversible actions. Stop before any such action and request explicit human approval.
7. Finish with: status (done/blocked/failed), evidence and links, artifacts/run IDs, tests passed/failed, remaining work, and the exact next action. Do not declare success until the acceptance tests pass.
```

## Suggested first implementation milestone

1. Pick one Windows machine and one Linux machine; install and test a local desktop adapter in the real interactive session. Add Playwright MCP for browser-only tasks.
2. Create a small agent-runner interface: `start_task`, `get_status`, `append_progress`, `pause`, `resume`, `cancel`, `request_approval`, `attach_artifact`.
3. Put Temporal around one sample workflow: read a goal → call an IDE/CLI agent → wait on a durable timer or human input → verify files/tests → produce a report. Start with LangGraph instead if the initial job is short and Python-only; keep the durable task API separate so the runner can change later.
4. Run a backtest proof-of-concept on one liquid symbol from each intended category, with a known historical interval and documented source. Specifically test an ETF, a futures contract, an FX pair, crypto, a bond, and a mutual fund NAV series; do not infer coverage from one successful instrument.
5. Keep live execution disconnected. Only consider paper-trading after data validation, unit tests, replay tests, stale-data alarms, risk limits and human approval are demonstrated.
