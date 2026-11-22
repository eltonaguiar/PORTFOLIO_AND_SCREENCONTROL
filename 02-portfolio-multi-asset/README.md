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

## Where the strategy and backtest work lives

This folder is about **tracking and valuing** a portfolio, and the tooling/data traps that
break it. The **strategy, backtest and paper-trading work** — the harness that produced the
measured numbers, plus the 200-round plan and the live forward pods — lives in its own
folder so the two jobs stay separable:

→ [`../03-trading-strategies/`](../03-trading-strategies/)

The split is deliberate. A tracker answers "what do I own and what is it worth"; a strategy
harness answers "would this rule have made money, and is that answer real". Mixing them is
how a dashboard's PF gets quoted as evidence of an edge.
