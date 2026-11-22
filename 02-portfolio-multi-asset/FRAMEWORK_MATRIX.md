# Framework matrix — backtesting, research, and portfolio tracking

Metadata verified via the GitHub API on **2026-11-22**: licence (SPDX as GitHub reports it), stars, last push,
archived flag. Stars are a popularity proxy, not a quality signal. Use the "fails when" column before the
"use when" column.

## Event-driven backtest engines (realistic fills, costs, portfolio state)

| Project | Licence | ★ | Last push | Use when | Fails when |
|---|---|---|---|---|---|
| **nautechsystems/nautilus_trader** | LGPL-3.0 | 31,734 | 2026-11-22 | identical code from backtest → paper → live; multi-venue; order-book realism; custom instruments | you want quick daily-bar sweeps; you cannot absorb v1→v2 migration (see `NAUTILUS_ARCHITECTURE.md`) |
| **QuantConnect/Lean** | Apache-2.0 | 22,651 | 2026-11-20 | first prototype across equities/options/futures/FX/crypto/CFDs; C# core + Python API; local CLI or cloud | you need mutual-fund NAV as a first-class class (it isn't); you want a small dependency footprint |
| **freqtrade/freqtrade** | GPL-3.0 | 57,155 | 2026-11-19 | crypto spot/futures bots with hyperopt, dry-run, live; 24/7 markets | anything that is not crypto; you need a general multi-asset portfolio |
| **robcarver17/pysystemtrade** | GPL-3.0 | 3,638 | 2026-11-02 | systematic futures with roll rules, volatility targeting, production discipline | you want a general library rather than an opinionated system |
| **mementum/backtrader** | GPL-3.0 | 23,776 | **2024-08-19** | you are maintaining an existing Backtrader codebase | **new work** — no release in ~2 years; its commission/slippage/fill models are still fine, but nobody is fixing bugs |
| **nkaz001/hftbacktest** | MIT | 5,126 | 2025-12-23 | market making / HFT where queue position, feed latency, and order latency matter | daily-bar or low-frequency work; anything that is not tick/L2 data |
| **backtesting.py** | **AGPL-3.0** | 9,275 | 2026-08-05 | single-instrument iteration with charts and a built-in optimizer | you ship a closed product (AGPL); multi-asset portfolios |
| **stefan-jansen/zipline-reloaded** | Apache-2.0 | 2,020 | 2026-11-02 | US-equity cross-sectional factor research via the Pipeline DSL (+ Alphalens/Pyfolio) | non-US, non-equity, intraday, or futures/FX work |
| **pmorissette/bt** | MIT | 3,045 | 2026-11-20 | asset allocation / rebalancing trees, weight-based strategies | you need exact order types or venue simulation |

## Vectorised research (fast sweeps, not a simulator)

| Project | Licence | ★ | Last push | Use when | Fails when |
|---|---|---|---|---|---|
| **polakowo/vectorbt** | **NOASSERTION** on GitHub | 9,911 | 2026-11-11 | thousands of parameter combinations in seconds; screening ideas before an event-driven port | you treat its fills as realistic — add fees/slippage/funding/borrow yourself; also **read `LICENSE` before commercial use**, the actively developed product is the paid `vectorbtpro` |

## Data and access layer

| Project | Licence | ★ | Last push | Role |
|---|---|---|---|---|
| **ccxt/ccxt** | MIT | 44,953 | 2026-11-22 | unified crypto exchange REST/WS for market data and (optionally) trading |
| **ranaroussi/yfinance** | Apache-2.0 | 25,981 | 2026-11-21 | equities/ETFs/FX/commodities/index daily data from Yahoo — convenient, officially unofficial, rate-limited |
| **OpenBB-finance/OpenBB** | NOASSERTION | 75,636 | 2026-11-18 | research terminal/API aggregating many providers; check per-provider licences |
| **FRED / central-bank APIs** | public | — | — | rates, yields, macro series — the honest source for bond context |

## Tracking / bookkeeping (the "what do I own" problem)

| Project | Licence | ★ | Last push | Use when | Fails when |
|---|---|---|---|---|---|
| **beancount/beancount** | GPL-2.0 | 6,194 | 2026-08-23 | plain-text double-entry ledger, queryable, versionable, script-friendly | you want a UI without writing queries |
| **simonmichael/hledger** | GPL-3.0 | 4,832 | 2026-11-21 | same idea, faster CLI, excellent multi-currency support | you need a GUI-first workflow |
| **ghostfolio/ghostfolio** | AGPL-3.0 | 9,757 | 2026-11-21 | self-hosted web dashboard over your holdings, multi-currency, allocation views | you need auditable double-entry; AGPL obligations if you modify and host it |
| **buchen/portfolio** (Portfolio Performance) | EPL-1.0 | 4,183 | 2026-11-20 | desktop app, good for taxes/performance per position, imports broker statements | automation/headless use; it is a GUI app with a separate data file |

## Multi-asset run vs portfolio run (decide this before choosing an engine)

Two different questions that produce two different answers:

- **Multi-asset run** — the same rule tested independently per symbol, to see whether the edge generalises across
  instruments. Each symbol gets its own account and PnL; combining the results is a reporting step, not a
  simulation step. vectorbt and most single-instrument engines do this naturally.
- **Portfolio run** — one cash account where holdings **compete for the same money, bar by bar**. Position
  sizing, cash constraints, margin, and correlation all change the outcome. Needs an engine with a real
  portfolio object: LEAN, NautilusTrader, bt/QSTrader (allocation-style), pysystemtrade.

A strategy can pass the first and fail the second — most do. If capital is shared, only the portfolio run is
evidence.

## Licence traps worth knowing

- **AGPL** (`backtesting.py`, `ghostfolio`, `UI.Vision` from the screen-control side): network use counts as distribution. Fine for personal use, a legal problem for a SaaS.
- **GPL** (`freqtrade`, `pysystemtrade`, `beancount`, `hledger`, `AutoHotkey`): derivative works inherit the licence. Linking from Python is normally fine; shipping a closed binary is not.
- **LGPL** (`nautilus_trader`): dynamic linking is fine; modifications to the library itself must be published.
- **NOASSERTION** (`vectorbt`, `OpenBB`): GitHub could not classify the licence. Treat it as *unknown* until you read `LICENSE`, not as permissive.

## Suggested decision path

```
Do I need the same code to trade live later?
├── yes → NautilusTrader (custom/multi-venue/microstructure) or LEAN (broad asset classes, faster start)
└── no
    ├── one instrument, fast iteration        → backtesting.py (mind AGPL) or bt
    ├── thousands of parameter combos         → vectorbt (then port the winner to an event-driven engine)
    ├── US equity factors                     → zipline-reloaded + Alphalens
    ├── crypto 24/7 bot                       → freqtrade
    └── HFT / market making                   → hftbacktest
```

Whatever you pick: **the engine is not the data**, and no engine's defaults are realistic enough to skip the
assumption list in [`DATA_EVIDENCE_RULES.md`](DATA_EVIDENCE_RULES.md).
