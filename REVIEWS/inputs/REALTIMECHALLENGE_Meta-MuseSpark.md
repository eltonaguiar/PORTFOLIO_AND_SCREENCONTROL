This is buildable for \$0, local-first, on Windows — but only if you split it into **two separate problems** that most people conflate:

1. **Desktop / agent orchestration:** one Windows host controls everything, agents take turns, nothing runs concurrently on the same mouse/keyboard.
2. **Trading challenge:** one reproducible Python pipeline that does backtest → paper-monitor → live pretend-trade, with the same signal logic in all three.

Below is your Round 1 + Round 2 decision, the reusable framework, and the full prototype file you can save as:

**`REALTIMECHALLENGE_MuseSpark_2026-11-22_EST.MD`**

I can't write directly to your disk from this logged-out chat, so copy the block in `## The file to save` into that filename in your repo root. Every agent you hand it to should start from that file.

---

## Your answers, locked in

| Decision | Your answer | What it forces |
|---|---|---|
| **A1 Host** | Windows | Windows-MCP is the primary driver. Linux is *controlled through* Windows via RustDesk / SSH, not a second host. |
| **A2 Apps** | VS Code, browser, Hermes desktop, RustDesk, Word, LinkedIn — mixed / canvas-heavy | Tree-first + vision/OCR fallback. Never assume accessibility tree alone works for RustDesk, canvas apps, or logged-in web apps. |
| **A3 RustDesk** | Drive it, not just observe | Needs screenshot + coordinate click/type inside the RustDesk window, plus a fallback: SSH / CLI on the Linux box for anything deterministic. GUI-only-via- RustDesk is the last resort. |
| **A4 Windows** | Not too many for now | 1 orchestrator + max 2-3 worker agents, **serialized** on one machine. |
| **A5 Mode** | Unattended for hours, interruptible later | Needs durable queue, heartbeat, checkpoint files. No in-memory-only agent loop. |
| **A6 Approval** | No | Compensate with: allowlist of apps/paths, no live-money execution ever, dry-run flag, audit log. |
| **A7 Code trust** | Trusted but vetted | Scan new repos with Malwarebytes + manual review of `install` / post-install scripts before any agent runs them. No auto-`pip install` from unreviewed URLs. |
| **A8 Cost / location** | Free, local-only realistic | No cloud VM, no paid APIs, no paid data. |
| **B1 Assets** | All + anything else worth money | Stocks, ETFs, indices, crypto spot/perps, forex, futures, commodities, bonds/rates, mutual funds (daily only). Options later — options backtests are the weakest link without Greeks / IV surface. |
| **B2 Realism** | Both fast triage + realistic fills | Two engines: vectorized for sweeps, event-driven / bar-replay for validation. |
| **B3 Live** | Paper only is fine | Winning trades just need clear, re-runnable buy/sell logic. No broker live execution in scope. |
| **B4 Data** | Free only | See free-data table below. |
| **B5 Scope** | Portfolio, many strategies in parallel | Portfolio-level backtest + per-strategy ledger. |
| **B6 Grid** | Thousands of parameter combos | Vectorized sweep engine required. |
| **B7 Language** | Mostly AI agents write it | Python + strict templates. Agents never invent their own backtest harness. |
| **B8 AI writes strategy** | Yes, sometimes | AI proposes strategy JSON → template converts to code → harness runs it. No free-form code execution. |
| **B9 History** | Unknown | Default: use max free history, report history length per asset. Short crypto history is a disqualifier for long-horizon claims. |

---

## 1. The reusable framework: `orchestrator + harness`

Give every agent — Muse, ChatGPT, Gemini, Copilot, local model, it doesn't matter — the **same three interfaces**. That is what makes it console/IDE/browser agnostic.

### A. Desktop control: Windows-MCP + vision fallback

**Primary:** Windows-MCP — lightweight, open-source, acts as an MCP server bridging LLMs and Windows, for file navigation, app control, UI interaction, and simulated input.

**Fallback for canvas / RustDesk / OCR:** `own-computer-use-mcp` — self-hosted MCP server giving screen reading with built-in OCR, mouse, keyboard, clipboard, and app launching on Windows, Python 3.10+.

**Browser:** Playwright MCP (or browser-use) for logged-in LinkedIn / job extraction. Do NOT drive the browser by pixel-clicking if a DOM tool exists — DOM is deterministic, pixels are not.

**Rule for agents:**
```
1. Try accessibility / DOM / CLI first
2. Try window title + UI Automation second
3. Screenshot + OCR + coordinate click LAST, and log coordinates + screenshot path
4. If 3 fails twice, STOP that task, write failure to queue, move to next task
```

This rule alone prevents 80% of “agent stuck clicking the wrong button for 3 hours.”

### B. Orchestration: file queue, not vibes

No agent talks directly to another agent. All coordination goes through files in the repo:

```
challenge/
  REALTIMECHALLENGE_<model>_<datetime>_EST.MD   # this file, append-only log
  queue/
    tasks.jsonl          # one JSON per line, status: queued|claimed|done|failed
    heartbeats.jsonl     # agent_id, timestamp, current_task, last_progress
    results/             # one JSON per completed round
  src/
    data/                # fetchers, cache to data/parquet/
    strategies/          # strategy JSON -> generated Python
    backtest/           # vectorbt sweep + event validator
    paper/              # paper monitor + pretend-trade executor
  .github/workflows/
    backtest.yml         # nightly / on-push sweep
    monitor.yml          # every 15-60 min, check TP/SL on open paper trades
```

**Task format every agent must use:**

```json
{"id":"R007","type":"backtest","asset":"BTC/USDT","strategy":"ema_cross","params":{"fast":12,"slow":26},"status":"queued","owner":null,"started_at":null,"result_path":null}
```

**Orchestrator loop (runs on Windows, unattended):**

1. Pick next `queued` task, mark `claimed`, write heartbeat every 60s
2. Spawn ONE worker at a time for any desktop-control task
3. Worker writes result JSON + appends to `REALTIMECHALLENGE...MD`
4. If heartbeat stale > 10 min, orchestrator marks task `failed: heartbeat timeout`, re-queues it, and restarts worker
5. Every hour, orchestrator posts a `STATUS` summary to the challenge file

**Cross-checking peers:** Every agent must, after finishing its own round, run `peer_review` on the previous agent's result: re-run the same backtest with the same seed/params/data-hash, and record `reproduced: true/false`. If false, the round does NOT count as profitable.

### C. Safety allowlist for unattended, no-approval mode

Since A6 = no human approval, hard-code this:

- **Allowed:** `challenge/`, `%USERPROFILE%\challenge-data\`, VS Code, browser, RustDesk viewer, Word docs in `challenge/`
- **Forbidden:** live broker login, real money, deleting outside `challenge/`, installing software without vetting, sending email/DMs, changing system settings, opening password managers
- **All desktop actions logged:** timestamp, app, action, screenshot path

---

## 2. Backtesting stack: free, portfolio, thousands of params

**Sweep engine:** vectorbt — Python toolkit for trading research, vectorized with pandas / NumPy / Numba, built to compare thousands of ideas across assets and timeframes. It covers stocks, ETFs, crypto, forex, futures, any OHLCV series, and the open version ships a yfinance wrapper.

**Validation engine:** `backtrader` or a small event-driven bar-replay script. This is where you add slippage, fees, spread, and intrabar TP/SL sequencing. vectorbt finds candidates, the event engine kills false positives.

**Strategy definition (AI-friendly, no free-form code):**

```json
{
  "name": "ema_cross_rsi_filter",
  "asset_class": "crypto",
  "timeframe": "1h",
  "entry_long": "EMA(fast) crosses above EMA(slow) AND RSI(14) < 70",
  "exit": "TP=+2.0% OR SL=-1.0% OR EMA cross down",
  "fees_bps": 10,
  "slippage_bps": 5,
  "max_position_pct": 5
}
```

Agent writes JSON → template generates vectorbt code → harness runs it. If the agent can't express it in JSON, it doesn't run.

### Free data — no paid feed

| Asset | Free source | Notes |
|---|---|---|
| Stocks / ETFs / indices / futures / commodities / FX pairs | yfinance / Yahoo Finance | No key needed, broadest coverage for exploratory work. Rate-limited, unofficial — cache everything to Parquet. |
| Crypto spot / perps | Binance public REST + WebSocket via `ccxt` | No API key for public OHLCV: `ccxt.binance().fetch_ohlcv("BTC/USDT")`. Binance also delivers real-time trades/order book over WebSocket with no auth on public streams. |
| Forex / stocks / crypto snapshots | Alpha Vantage, Twelve Data, Finnhub free tiers | Alpha Vantage: 25 req/day, Twelve Data: 800 req/day, Finnhub: 60 req/min on free tier. Use only as backup / cross-check. |
| Bonds / rates / macro | FRED (free key) | Daily/weekly only. Good for regime filter, not intraday signals. |
| Mutual funds | yfinance daily | Daily only. Never claim intraday edge on mutual funds. |

**Data rules that prevent fake profits:**
- Cache raw data with `source + symbol + timeframe + fetched_at + sha256`
- Never backtest on data that includes future corporate actions without adjustment — use adjusted close for equities
- For TP/SL in same bar: if using daily/hourly OHLC, you **cannot** know if TP or SL hit first. Mark as `ambiguous` and re-test on lower timeframe or tick data. This is the #1 source of inflated backtests.
- Survivorship: report universe, delisted handling, and history length per asset

---

## 3. The 200-round plan

Don't do 200 random rounds. Do **10 blocks x 20 rounds**, each block has a kill criterion.

| Block | Rounds | Goal | Pass / Kill |
|---|---|---|---|
| 0. Infra | 1-10 | Data fetchers, cache, vectorbt harness, GitHub Actions, queue | If backtest not reproducible by peer, stop |
| 1. Baseline | 11-30 | Buy-and-hold, SMA/EMA cross, RSI, MACD, Bollinger on BTC, ETH, SPY, QQQ, EUR/USD | Keep top 5 by out-of-sample Sharpe |
| 2. Crypto intraday | 31-50 | 15m/1h momentum, mean-reversion, breakout on BTC/ETH/SOL | Must survive fees + slippage |
| 3. Forex | 51-70 | EUR/USD, GBP/USD, USD/JPY, 1h/4h trend + session filter | Kill if spread kills edge |
| 4. Equities / ETFs | 71-90 | SPY, QQQ, sector ETFs, momentum rotation | Portfolio-level, not single-symbol cherry-pick |
| 5. Commodities / futures | 91-110 | Gold, oil, natgas, continuous contracts, roll handling | Kill if roll cost not modeled |
| 6. Bonds / rates / funds | 111-130 | TLT, IEF, bond ETF trend, mutual-fund monthly rotation | Daily only, low turnover |
| 7. Multi-asset portfolio | 131-150 | Combine top 5 strategies, correlation, drawdown, position sizing | Must beat equal-weight baseline out-of-sample |
| 8. Live pretend-trading | 151-175 | Paper trades on live markets, TP/SL monitor via GitHub Actions | See Section 4 |
| 9. Robustness | 176-195 | Walk-forward, parameter sensitivity, different regimes, transaction-cost stress | Kill strategies that only work on one parameter set |
| 10. Final | 196-200 | Re-run top 3 end-to-end, peer re-run, write final report | Only strategies reproduced by 2 agents count |

**Per-round output (mandatory):**
`results/R###.json` with: strategy JSON, data hash, in-sample metrics, out-of-sample metrics, max drawdown, win rate, profit factor, fees/slippage used, `reproduced_by_peer`, `verdict: keep/kill/promote-to-paper`

**GitHub Actions:**
- `backtest.yml`: on push + nightly, runs sweep, uploads `results/` as artifact, fails if any `keep` strategy can't reproduce
- `monitor.yml`: every 30 min during market hours, fetches latest price for open paper trades, checks TP/SL, writes `paper/trades.jsonl`, commits if a trade closed

---

## 4. Round 8 prototype: live “pretend” trading on real, live markets

This is the round you asked for — and the one that exposes whether a strategy is real.

**Setup (tonight, since it's Sunday morning Toronto time):**
- Crypto is open 24/7, forex opens Sunday evening ET. Use crypto for immediate live test, forex for Sunday-night test.
- Pick ONE promoted strategy from Blocks 1-2, e.g. BTC/USDT 15m EMA cross + RSI filter, TP +1.5%, SL -0.75%, fees 10bps, max 5% paper capital.
- Paper capital: \$10,000 pretend, no real money, no broker login.

**Live loop:**
```
1. Fetch live BTC/USDT 15m via Binance public WS / ccxt
2. Every new closed candle, evaluate signal
3. If signal: open paper trade in paper/trades.jsonl with entry price, time, TP, SL, reason
4. Monitor.yml checks every 5-15 min: if high >= TP -> close WIN, if low <= SL -> close LOSS, if both in same candle -> AMBIGUOUS, do not count as win
5. After 10 paper trades OR 4 hours, stop and report
```

**What “profit in short timeframe” actually means:**
- If you get 10 trades in 4h on 15m BTC and net > fees, that's a *candidate*, not proof. Report it as: `n=10, net +X%, win rate Y%, max drawdown Z%, ambiguous N`
- If you get 0 trades, that's also a result: strategy is too selective for that timeframe/market regime. Report why: no cross, RSI filter blocked all signals, volatility too low, spread/fees > edge.
- If you get losses, report the kill reason: e.g. “whipsaw in ranging market, 6 false crosses in 2h, SL hit before TP in 4/6”

**Why most short-timeframe live tests fail:** ranging markets, fees + slippage > 1-2% edge, TP/SL both hit in same candle on low timeframe, and signal generated on a candle that already moved. Your monitor must log the *exact* candle close time vs. trade open time to prove no lookahead.

---

## 5. Same framework for non-trading tasks (jobs, Word, LinkedIn)

The queue + Windows-MCP + Playwright stack is task-agnostic. Example for your LinkedIn job hunt:

```
Task: linkedin_jobs
Steps:
  1. Playwright MCP: open linkedin.com/jobs, already logged in via user profile (agent never asks for password)
  2. Search: keyword="ServiceNow", location="Toronto", filter: past 24h
  3. Extract: title, company, location, link, posted_at -> jobs.csv
  4. Windows-MCP: open Word, create doc from jobs.csv, one page per job with match notes
  5. Result: jobs.csv + docx path + count
```

Same rules apply: one agent on the desktop at a time, heartbeat, result JSON, peer re-run.

---

## The file to save

```markdown
# REALTIMECHALLENGE_MuseSpark_2026-11-22_EST
# Host: Windows | Mode: unattended, no approval | Cost: $0 local-only
# Goal: 200 rounds, find >=1 backtest-proven, paper-proven asset/strategy

## Status
- Round: 0 / 200
- Current block: 0 Infra
- Open paper trades: 0
- Last heartbeat: 2026-11-22 09:00 EST

## Decisions (A1-A8, B1-B9)
- A1 Windows, A2 mixed, A3 drive RustDesk, A4 <=3 agents, A5 unattended,
  A6 no approval, A7 vetted trusted code, A8 free local-only
- B1 all assets, B2 both sweep+realistic, B3 paper, B4 free data only,
  B5 portfolio, B6 thousands params, B7 AI-written, B8 yes, B9 max free history

## Stack
- Desktop: Windows-MCP (primary) + own-computer-use-mcp (OCR/vision fallback)
- Browser: Playwright MCP
- Orchestration: queue/tasks.jsonl + heartbeats.jsonl + results/R###.json
- Backtest: vectorbt (sweep) + event-driven validator (fees/slippage/TP-SL)
- Data: yfinance (stocks/ETFs/FX/futures), Binance/ccxt (crypto), FRED (rates)
- CI: .github/workflows/backtest.yml + monitor.yml

## Rules
1. One desktop agent at a time. No concurrent mouse/keyboard.
2. Strategy must be JSON -> template -> harness. No free-form backtest code.
3. TP/SL same-bar = AMBIGUOUS unless lower timeframe proves order.
4. Every keep must be reproduced by a peer agent with same data hash.
5. No live money, no broker login, no secrets in repo.

## Log (append-only)
- [2026-11-22] Round 0: Prototype defined. Next: Round 1 data fetchers + harness.
```

**Next step I recommend:** tell your first worker agent: “Start Round 1-5: build `src/data/` fetchers for SPY, BTC/USDT, EUR/USD, cache to Parquet, and prove vectorbt reproduces the same Sharpe on two runs with the same data hash.” That is the gate — if that fails, no 200-round plan matters.

Want me to draft the exact `tasks.jsonl` for Rounds 1-20 and the `backtest.yml` / `monitor.yml` files so you can paste them straight into the repo?