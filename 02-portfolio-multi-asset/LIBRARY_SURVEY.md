# Library & repo survey — what to use to prove a trading experiment

Every entry below was checked live against the GitHub API on **2026-11-22** (stars,
last push, license, archived flag). Nothing here is quoted from memory.

## What the harness in this repo actually uses

| library | version installed | role | why this one |
|---|---|---|---|
| **ccxt** | 4.5.38 | exchange market data + live quotes | 100+ venues behind one API, **public endpoints need no keys**, so the whole experiment runs without an account or a credential |
| **pandas / numpy / scipy** | 2.3.3 / 2.2.6 / 1.17.0 | bars, indicators, bootstrap | already the repo's substrate |
| **vectorbt** | 0.28.5 | cross-engine reconciliation | independent implementation to catch engine-specific bugs |
| custom engine (`engine.py`) | — | the actual verdict engine | written deliberately small and pessimistic; see `HARNESS_CERTIFICATION.md` |

**Why not a framework for the verdict engine.** Every framework below makes an
*implicit* execution decision (same-bar close fills, mid-price fills, no fee unless
configured). The one thing this project must not do is inherit an optimistic default
silently. A ~200-line engine where `lag1_next_open`, `SL-first intrabar` and `taker +
slippage both legs` are visible in the code is worth more than a framework whose
defaults you have to audit. That is also why `vectorbt` is used as a *check*, not as the
source of truth.

## Verified candidates (stars / last push / license, 2026-11-22)

| repo | stars | last push | license | what it is good for here |
|---|---:|---|---|---|
| `OpenBB-finance/OpenBB` | 75,636 | 2026-11-18 | NOASSERTION | open data platform; useful for cross-asset data plumbing |
| `freqtrade/freqtrade` | 57,152 | 2026-11-19 | GPL-3.0 | crypto bot with **dry-run paper mode** and a built-in backtester; best existing "paper trading" reference |
| `ccxt/ccxt` | 44,953 | 2026-11-20 | MIT | **in use** |
| `nautechsystems/nautilus_trader` | 31,734 | 2026-11-22 | LGPL-3.0 | Rust-core event engine where **backtest and live share one code path** — the strongest answer to "your backtest lies" |
| `ranaroussi/yfinance` | 25,981 | 2026-11-21 | Apache-2.0 | equities/ETF/FX daily history (used for the SPY/B&H benchmark) |
| `mementum/backtrader` | 23,776 | **2024-08-19** | GPL-3.0 | historically popular; last push is 2+ years old — do not start new work here |
| `QuantConnect/Lean` | 22,651 | 2026-11-20 | Apache-2.0 | institutional-grade engine + free cloud backtests; heavy |
| `hummingbot/hummingbot` | 21,343 | 2026-11-20 | Apache-2.0 | market making / HFT execution |
| `AI4Finance-Foundation/FinRL` | 17,162 | 2026-11-18 | MIT | RL research; out of scope for a proof-first pipeline |
| `polakowo/vectorbt` | 9,911 | 2026-11-11 | NOASSERTION | **in use** as an independent check |
| `kernc/backtesting.py` | 9,275 | 2026-08-05 | AGPL-3.0 | simplest honest backtester; AGPL is a real constraint for closed use |
| `jesse-ai/jesse` | 8,828 | 2026-11-17 | MIT | crypto-specific, clean strategy DSL |
| `ranaroussi/quantstats` | 7,903 | 2026-11-02 | Apache-2.0 | tearsheets / Sharpe / drawdown reporting |
| `Drakkar-Software/OctoBot` | 6,971 | 2026-11-21 | GPL-3.0 | grid/DCA bots, tradingview strategies |
| `robertmartin8/PyPortfolioOpt` | 6,177 | 2026-07-07 | MIT | efficient frontier / risk parity for the portfolio layer |
| `nkaz001/hftbacktest` | 5,126 | 2025-12-23 | MIT | L2/L3 order-book backtesting with queue position — only relevant if we move to maker strategies |
| `edtechre/pybroker` | 3,725 | 2026-11-21 | NOASSERTION | ML-flavoured backtesting with walk-forward built in |
| `blankly-finance/blankly` | 2,484 | **2024-12-30** | LGPL-3.0 | stale (2 years) — avoid |
| `Lumiwealth/lumibot` | 2,245 | 2026-11-21 | GPL-3.0 | backtest + paper + live through one API, good Alpaca integration |
| `alpacahq/alpaca-py` | 1,602 | 2026-11-20 | Apache-2.0 | **the** free paper-trading broker API (equities + crypto, 24/7 crypto) |

## Paper-trading venues, ranked by what they cost to adopt

1. **Alpaca paper** (`alpaca-py`, free account, real paper portfolio, equities + crypto).
   The only option here that gives a *broker-side* paper account rather than a
   simulation. Needs account credentials — deliberately not used in this run.
2. **freqtrade dry-run** — real exchange data, no money, proven. Needs a config file.
3. **ccxt + own simulator** (what this repo does) — zero credentials, full control of
   the fill model, and every price is a real public tick. Downside: *we* write the fill
   model, so it must be certified (which is what `proof/test_harness.py` does).
4. **Binance/Bybit testnet** — needs keys even for the sandbox, and funding/settlement
   behaviour differs from production.

## Adopt / avoid, decided

| decision | choice | reason |
|---|---|---|
| data | ccxt public OHLCV, cached to CSV per run | keys-free, reproducible, 5-venue consensus available |
| verdict engine | own, ~200 lines, pessimistic defaults | frameworks hide execution assumptions |
| independent check | vectorbt on the same signals | catches engine-specific artefacts |
| live paper | own simulator on real ticks now; Alpaca paper later | no credentials required to start |
| portfolio maths | PyPortfolioOpt (later phase) | standard, maintained, MIT |
| avoid | backtrader, blankly | no push in 2 years |
