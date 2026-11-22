# 02 — Financial portfolio tracking across multiple asset classes

Two different jobs live under this heading and mixing them up costs months:

| Job | Question it answers | Right tool class |
|---|---|---|
| **Tracking / valuation / reporting** | "What do I own, what is it worth in my base currency today, and how did it perform?" | Double-entry ledger + price store + report generator (Beancount, hledger, Ghostfolio, Portfolio Performance) |
| **Research / backtesting** | "Would this rule have made money, with what drawdown, under realistic costs?" | Event-driven or vectorised backtest engine (NautilusTrader, LEAN, vectorbt, backtesting.py, bt) |

A backtester is not a portfolio tracker, and a tracker cannot tell you whether a rule generalises. The files
here cover both, plus the data-evidence rules that make either one honest.

## Asset-class reality check (the part that breaks first)

| Asset class | Data you actually need | What usually breaks | Engines that handle it |
|---|---|---|---|
| **Stocks / ETFs** | OHLCV + splits + dividends + point-in-time universe | survivorship bias, corporate actions, delisting returns | LEAN, Nautilus, zipline-reloaded, vectorbt, bt |
| **Bonds** | clean price, accrued interest, coupon schedule, day-count, calendar | clean-vs-dirty confusion, illiquidity, no continuous series | Nautilus (IG adapter / custom instruments), LEAN (custom data), or a bespoke curve model |
| **Mutual funds** | daily NAV **plus distributions** (income + capital gains) | NAV ≠ return; NAV is struck once a day, after your cut-off | any engine as custom data; track total return, not price |
| **Commodities / futures** | continuous contracts + roll rules + margins | roll methodology silently dominates returns | LEAN, Nautilus (futures + roll), pysystemtrade |
| **FX** | venue-specific quotes, swap/financing, session calendar | retail data quality, spread assumptions, weekend gaps | Nautilus (FX), LEAN, backtesting.py with care |
| **Crypto** | exchange trades/quotes, funding for perps, fees | 24/7 calendars, exchange downtime, funding cost | Nautilus (10+ crypto venues), freqtrade, ccxt for data |
| **Options** | chains, greeks, expiry/assignment, early exercise | modelling depth, liquidity, pin risk | LEAN, Nautilus (options), hftbacktest for microstructure |

## Files

| File | Contents |
|---|---|
| [`NAUTILUS_ARCHITECTURE.md`](NAUTILUS_ARCHITECTURE.md) | NautilusTrader **v2.0.0** read from source: crate map with real LOC, kernel, message bus, threading model, quote and order flows, component lifecycle FSM, crash-only design, backtest/live parity, migration deltas from v1 |
| [`FRAMEWORK_MATRIX.md`](FRAMEWORK_MATRIX.md) | Backtest and tracking options with **verified** licence/★/last-push, fit notes, and the failure mode of each |
| [`PORTFOLIO_TRACKING.md`](PORTFOLIO_TRACKING.md) | The tracking/valuation stack: ledgers, aggregators, multi-currency valuation, TWR vs MWR, reconciliation, broker imports |
| [`DATA_EVIDENCE_RULES.md`](DATA_EVIDENCE_RULES.md) | Mandatory provenance for every series and every backtest report; `observed` / `derived` / `assumed` labelling; multiple-testing discipline |
| [`PAPER_TRADING_AND_MONITORING.md`](PAPER_TRADING_AND_MONITORING.md) | The audit loop between backtest and money: fill model assumptions, TP/SL sequencing, event log schema, latency/slippage metrics, a scheduler that is actually suitable, kill switches |

## Recommendation in one paragraph

For **tracking a real multi-asset portfolio**, keep a plain-text double-entry ledger (Beancount or hledger) as
the source of truth, feed prices from yfinance (equities/ETFs/FX/commodities) and ccxt or an exchange archive
(crypto), convert to a base currency at daily rates, and generate TWR/MWR reports from the ledger rather than
from a spreadsheet. Add Ghostfolio (self-hosted) only if you want a web UI for the same data. For
**backtesting**, prototype QuantConnect LEAN if you want the shortest path to multi-asset with a live
brokerage story, and NautilusTrader when you need identical strategy code from backtest to live, custom
instruments, or multi-venue microstructure. Use vectorbt for parameter sweeps and port winners into one of the
event-driven engines. Do not infer asset-class coverage from a single successful instrument — run one liquid
symbol per category with a documented data source first.

## Non-negotiables

- No agent places live orders or holds broker credentials. Paper/backtest only, human approval for anything else.
- Every reported number carries its source, timestamp, and whether it was observed, derived, or assumed.
- Every backtest ships with its data snapshot, assumptions, benchmark, and out-of-sample result — or it is an anecdote.

---

## Working harness — `realtime_challenge/` (added 2026-11-22, `deepseek-flash`)

The documents above are research and design. This directory now also contains a **running**
harness that was executed end to end, plus the measured results. Everything below is read
out of an artifact in `results/` or `ledger/`.

| file | job |
|---|---|
| `realtime_challenge/` | costs · data (ccxt) · engine · 6 pre-registered strategies · stats · live round · ledger · GH Actions worker · 2 proof suites |
| `REALTIMECHALLENGE_deepseek-flash_2026-11-22_0356_EST.MD` | **the challenge write-up: setup, results, live round, verdict** |
| `ROADMAP_200_deepseek-flash.md` | 200 rounds across 10 phases with explicit gates |
| `HARNESS_CERTIFICATION.md` | 5 tests that make the engine allowed to say "no" |
| `PEERCROSSCHECK_deepseek-flash.md` | line-level audit of the repo's prior 2-hour challenge + agreement with the capital-allocation verdict |
| `LIBRARY_SURVEY.md` | 20 backtesting/paper-trading repos with star/push/licence verified via the GitHub API on 2026-11-22 |
| `results/`, `ledger/` | every JSON and every append-only event log the numbers came from |

**Headline result of the first run — a clean negative, which is the point:**

- 42 cells (7 crypto majors × 6 hypotheses), 3,000×1h bars, 26 bps round turn → **0** above
  deflated Sharpe 0.95, **0** beating the permutation control.
- Only the crypto weekend effect survived friction (+5.9 bps/trade, breakeven ≈35 bps).
  It then **died** on a proper test: 3.0 years, bootstrapped **by calendar weekend**
  (pooling 7 correlated coins is not 7 observations) with all 42 other 48-hour windows as
  controls → **−3.21 bps**, CI **[−67.3, +64.5]**, rank **#15 of 42**.
- A live paper round opened and closed real positions on real bid/ask. The no-signal book
  lost **−0.278% with 0/6 winners and $40 in fees** — i.e. it lost exactly the friction,
  which is the correct answer for a zero-edge entry and is the live reproduction of the
  certification test that predicts a 26 bps drag.

This directly instantiates the non-negotiables at the bottom of this file: data snapshot,
assumptions, benchmark, out-of-sample result — or it is an anecdote.

Run it: `python -m realtime_challenge.proof.test_harness` (must be 5/5) then
`python -m realtime_challenge.cli backtest --bars 3000 --permutations 100 --verbose`.
Automation: `.github/workflows/realtime-challenge.yml` runs the forward pod hourly.
