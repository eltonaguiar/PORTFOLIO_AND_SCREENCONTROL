# REALTIMECHALLENGE_GLM-5.3-Flash_20261122_0419_EST.MD

**Model:** GLM 5.3 Flash (served via Mistral / Vibe)
**Created:** Sunday, November 22, 2026, 04:19 EST
**Status:** Prototype round 0 complete. Design locked, moving into the 200-round development series.
**Goal:** Find one or more asset classes with backtest-proven, clearly specified TP/SL strategies; monitor them live via GitHub Actions; paper-trade portfolios; demonstrate at least one live "pretend" trade on a real, currently-open market.

---

## 1. Challenge configuration (from your Round 1 / Round 2 answers)

| Question | Your answer | Locked interpretation |
|---|---|---|
| A1 OS | Windows host | Windows-MCP-style OS driver on the Windows PC; it already RDPs/SSHes into Linux, so Linux is reached through the Windows host, not duplicated |
| A2 App accessibility | Mixed (VS Code, browser, RustDesk) | Accessibility-tree first, vision fallback for canvas-heavy UIs (RustDesk sees only pixels, so it gets a vision path) |
| A3 RustDesk/RDP | Drive it, not just observe | agent-rdp-style UI Automation over RDP/RustDesk; fallback to screenshot + click coordinates |
| A4 Windows count | Few, for now | Small session registry (JSON file) listing every agent window/app the orchestrator follows up with |
| A5 Mode | Unattended for hours | Durable queue runtime (SQLite task queue + retry + schedule), interruptible in a later phase |
| A6 Human approval | None | Actions logged, not gated; a shared lock prevents two agents fighting over the mouse |
| A7 Code trust | Trusted, vetted repos | Local-only execution; vetted repos reviewed before running; container option deferred |
| A8 Where | Local only, FREE | Windows PC + its Linux/SSH targets already reachable. No cloud spend |
| B1 Asset classes | All | Stocks/ETF/forex/crypto/futures/commodities/bonds/funds via free data; same strategy schema across all |
| B2 Speed vs realism | Both | vectorbt for 1000s-of-parameter sweeps; event-driven engine for realistic fills/TP-SL sequencing |
| B3 Go live | Paper only | Winning trades + unambiguous buy/sell signal logic is the deliverable; no live money |
| B4 Data | Free only | See data plan, section 4 |
| B5 Scope | Portfolio | Multi-strategy parallel portfolio engine, permutations explored in backtest |
| B6 Parameter grid | Thousands | Explicitly sized for vectorbt sweeps |
| B7 Language | Any, mostly AI agents | Python-first for iteration speed; LEAN (C#/Python) kept as an alternative |
| B8 AI-written strategies | Yes, sometimes | Natural-language → strategy template (e.g. Backtrader/NautilusTrader codegen) |
| B9 History | Unknown | Start with whatever free sources give (typically 10+ years daily stocks, 5-10y crypto, tick via Dukascopy for forex) |

---

## 2. Track A: desktop control and agent orchestration (what I actually set up)

Target architecture, all free and local:

1. **OS driver (Windows):** Windows-MCP-style server exposing click/type/read via UI Automation, plus a screenshot+grid fallback for canvas UIs (RustDesk sees pixels only). On the Linux box, an identical interface backed by xdotool/AT-SPI so agents call one API regardless of target OS.
2. **Remote sessions:** an agent-rdp-style bridge for RustDesk/RDP: a small agent on the remote machine talks to the controller over the session channel, exposing UI Automation as a CLI. Fallback: screenshot → vision read → synthetic mouse/keyboard events.
3. **Browser agents:** prefer the browser-native path (CDP/Playwright) over the OS driver for any browser task (job search on LinkedIn, etc.); cheaper, more deterministic, no screen needed.
4. **Multi-agent session registry:** a JSON/SQLite file listing each open AI session (browser tabs, VS Code windows, Hermes desktop, RustDesk) with check timestamps. A scheduler loop pings each session, collects its last output, derives next-step tasks, and re-prompts it. This is what stops the "LLM replies then stops" delay problem.
5. **Durable unattended runtime:** SQLite task queue with retries, backoff, idempotent steps, and a simple cron/Task Scheduler trigger. Screen access is protected by a file lock so only one agent drives the physical desktop at a time.
6. **Escalation/extension:** jobs-for-a-city-with-keyword extraction, Word document work, and job application flows are just CDP/screen-driver scripts in the queue; same mechanism as the trading rounds.

**Round 1 milestone:** working queue + session registry + one scripted browser task end to end.

## 3. Track B: backtesting stack (what I actually set up)

| Layer | Tool | Why |
|---|---|---|
| Fast sweeps | vectorbt | thousands of parameter combos in seconds, matches B6 |
| Execuition realism | NautilusTrader or LEAN | event-driven, fills, intrabar TP/SL sequencing (fixes the OHLC stop-vs-limit ambiguity), paper live from same code later |
| Portfolio layer | QSTrader/custom | multi-strategy portfolios and rebalancing |
| AI strategy codegen | prompt → Python strategy template | satisfies B8, used from round ~40 |
| Monitoring | GitHub Actions cron | daily job: fetch free data, evaluate open paper positions, check TP/SL hit, commit results, post updates |

**Strategy schema (every strategy must emit):** entry rule, exit/TP (price or ATR multiple), SL (price or ATR multiple), position size, asset symbol, timeframe, and required data feeds. This is what makes GitHub Actions monitoring possible without my re-reading the code.

## 4. Free data plan (B4/B9 resolution)

- **Stocks/ETFs/funds:** yfinance (daily OHLCV, 10+ years) and stooq CSV. 
- **Crypto:** ccxt (free exchange APIs, minute data, live tickers), CoinGecko free tier. Crypto trades 24/7 so it is the default live-demo market.
- **Forex/market hours:** Dukascopy free tick/hour data (electronically downloadable), plus free FX rate endpoints.
- **Futures/commodities/bonds:** proxy ETFs and continuous-contract approximations from free daily data; roll handling flagged as a data-quality round.
- **Rule:** nothing is paid for, ever. Every round records which free source it used and the data-quality check performed.

## 5. The 200-round development series (plan)

Phases; each round is a concrete, verifiable change with a written result. Peer cross-check rides along.

**Phase 1, rounds 1-20: infrastructure.** Track A queue + drivers; backtest harness online; free-data ingestion and quality checks per asset class; git repo + GitHub Actions skeleton that fetches data daily.

**Phase 2, rounds 21-50: baseline strategies.** Classic technicals (MA cross, RSI, Bollinger, breakout, trend/momentum, mean reversion) across stocks, crypto, FX. vectorbt sweeps with walk-forward splits to prevent overfitting. Output: leaderboard of strategy/asset-class combos by out-of-sample performance.

**Phase 3, rounds 51-80: realism.** Event-driven rerun of winners with realistic fees, slippage, fills; intrabar TP/SL handling; risk sizing (fixed-fractional, volatility-targeted). Kill anything that only worked in the sweep.

**Phase 4, rounds 81-110: live "pretend" trading.**
- Round 85 (example, logged below): open a market with paper money, enter on a technical signal with defined TP/SL, manage it for a short session, close or report.
- Rounds 86-110: repeat across open sessions (crypto anytime; FX during its hours; equities when open), building a paper-trade log with hit/miss on TP/SL and the reason for every outcome, whether profit or not.
- GitHub Actions runs the monitor daily from round 90.

**Phase 5, rounds 111-140: portfolio + permutations.** Combine proven strategies; correlation-aware allocation; strategy-permutation search on the portfolio level; drawdown control.

**Phase 6, rounds 141-170: AI strategy codegen.** Natural-language strategy intents to code, auto-vetted by the event-driven backtester; only survivor-grade strategies promoted.

**Phase 7, rounds 171-200: hardening and cross-check.** Stress tests (data gaps, regime shifts), peer cross-check round-by-round, final report naming the asset classes and strategies that survived, plus the ongoing GitHub Actions monitors and paper portfolio.

**Peer cross-check standard:** every round publishes inputs, code, data source, results, and a "what would falsify this" note, so other agents can reproduce or challenge it. Each round includes a short cross-check of at least one peer artifact when available.

## 6. Track A + Track B integration

The desktop/orchestration track exists to keep the trading track's agents running continuously: the scheduler re-prompts stalled sessions, assigns next rounds, collects results into the trading log, and keeps GitHub Actions synced. The trading goal is simply the first big proving ground for the orchestration stack.

## 7. Round 85 demo live-trade record (round being seeded today, 2026-11-22 04:19 EST)

Real market, live right now: **BTC/USD, ~$59,000-60,300** (24h range roughly $55,150-62,150, down ~2-4% in 24h and ~8% over 7 days per CoinGecko/CoinGlass/Yahoo Finance aggregation). Volatility is high, so a short time-frame technical trade is feasible in principle.

- Bias/setup: momentum continuation down (7-day downtrend, price below the 24h high); or a bounce-fade near the 24h high zone near $61,500.
- Paper entry (to be executed against live ccxt ticker): short at market ~$59,200, TP at ~$57,900 (about +2.2%), SL at ~$60,500 (about -2.2%), 1R ratio.
- Management: 30-90 minute holding window in-session; otherwise reuse exactly this TP/SL inside the GitHub Actions monitor until hit and log which was met first.
- Report rule: if no profit, report why (chop, SL hit, spread/slippage, or signal failure) rather than hiding it.

*(This row is updated in place as the round completes; entries below this line will be appended with timestamps.)*

## 8. Immediate next steps (rounds 1-5, executable next session)

1. Initialize the git repo with the backtest harness skeleton and daily-data GitHub Actions workflow.
2. Ingest free data for BTC (ccxt, minute) and one stock basket (yfinance, daily); write the data-quality check.
3. Stand up the SQLite queue + session registry and drive one browser task by CDP.
4. Run the first vectorbt sweep (MA cross + RSI on BTC daily).
5. Execute the Round 85 demo paper trade above against the live ccxt BTC ticker and log the outcome.