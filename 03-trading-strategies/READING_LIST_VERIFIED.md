# Verified reading list — six families, six real citations, six dated crash windows

**Source:** Grok 4.20 via AskAnyModel multi-chat, 2026-11-23. Verbatim capture at
`REVIEWS/inputs/askanymodel_multichat_strategy_table_2026-11-23.txt`.
**Status: this is the only one of the three strategy tables that survives a citation check.** The 1min.ai table had
2 of 7 misattributed; the AskAnyModel/Gemma-pane table had 3 of 7 unusable with two rows swapped
(`PROVEN_STRATEGIES_TABLE_AUDIT.md` §1 and §6). Grok's is 6 for 6.

## 1. The table, with citations verified

| Strategy | Canonical source | Verified | Replicated assets | Sample | Named failure mode |
|---|---|---|---|---|---|
| **Carry** | Koijen, Moskowitz, Pedersen & Vrugt (2018), *Carry* (JFE) | ✅ real, right scope | FX, commodities, govt bonds, equities, credit | 1970s–2014, OOS ~2022 | sharp unwind in global risk-off — **2008 carry collapse** |
| **Time-series momentum / trend** | Moskowitz, Ooi & Pedersen (2012), *Time Series Momentum*; Hurst, Ooi & Pedersen (2017), *A Century of Evidence on Trend-Following* | ✅ both real | futures: equity, FI, FX, commodities | **1880s–2016**, strong OOS post-2012 | long drawdowns and whipsaw in choppy regimes — **2014–2019, parts of 2022** |
| **Cross-sectional momentum** | Jegadeesh & Titman (1993); Asness, Moskowitz & Pedersen (2013) | ✅ both real | global equities, country indices, sectors | 1927–2011 incl. global OOS | **momentum crash in rapid bear→bull reversals — 2009, ~−81% on WML** |
| **Risk premia (value, term, credit)** | Fama–French (1992/93); Asness et al. (2013) *Value and Momentum Everywhere* | ✅ real | global equities, bonds, FX, commodities | 1926–present, int'l from 1970s | multi-year regime underperformance — **value drawdown 2012–2020; term premium ≈0 post-2000** |
| **Volatility risk premium** | Carr & Wu (2009), *Variance Risk Premiums*; Bollerslev, Tauchen & Zhou (2009) | ✅ real | index options / VIX futures | 1986–present | catastrophic left tail — **1987, 2008, Feb 2018 (Volmageddon), Mar 2020** |
| **Mean reversion** | De Bondt & Thaler (1985); Balvers, Wu & Gilliland (2000) | ✅ both real | single stocks (short horizon), national indices | 1926–1990s, weaker OOS | inconsistent across horizons; momentum dominates the intermediate term; costs destroy short-horizon versions |

Unlike the other two tables, every "failure mode" here is **dated and specific**, not "regime shifts" or
"structural breaks". That is the difference between a table written from the literature and one written about it.

## 2. The part we should actually use: named test windows

Gate 17 of protocol v1.0 asks for "regime coverage" without saying which regimes. Grok's failure column supplies
them. Our regime-coverage test now requires a pass through **all** of:

| Window | What it tests | Why it is mandatory |
|---|---|---|
| **Oct 1987** | crash tail (VRP) | single-day vol explosion |
| **2008 H2** | carry unwind + VRP left tail + momentum reversal | three families fail together — the correlation spike is the real risk |
| **2009 Mar–Dec** | momentum crash (WML ≈ −81%) | bear→bull reversal is the classic momentum kill |
| **2012–2020** | value drawdown | an eight-year underperformance is a behavioural test, not a statistical one |
| **Feb 2018** | Volmageddon | short-vol strategies lose in days, not months |
| **Mar 2020** | COVID gap | liquidity plus tail simultaneously |
| **2014–2019, 2022** | trend whipsaw | the regime where trend-following grinds sideways |
| **post-2000 term premium** | bond risk premium ≈0 | a premium that stopped being paid |

If a candidate's equity curve cannot be sliced across those seven windows and survive, it has not been tested — it
has been fitted to whatever period happened to contain the backtest.

## 3. Its "what proven cannot mean" — the best-argued version of the six answers

> *"'Proven' means the strategies show statistically significant positive risk-adjusted returns in peer-reviewed
> academic papers, survive out-of-sample tests by independent researchers, different geographies, longer histories,
> and alternative specifications — **typically before or with modest institutional transaction costs**."*

And the five things it does not mean: you can extract them net of retail costs; the edge survives publication and
crowding; you can tolerate 30–60% drawdowns lasting years; implementation is easy (most need futures, listed options,
leverage, margin, 20–60 instruments, tax-aware rebalancing); or positive expectancy is guaranteed — *"these are risk
premia with crash risk, not arbitrage."*

It also states the uncomfortable statistic plainly: **"the vast majority of self-directed retail traders lose money
attempting systematic strategies."** That is consistent with everything this programme has measured.

## 4. Where this leaves the ranked list

Unchanged, and for a sharper reason than before. The reading list is now *verified* — but every family on it was
already measured on our own bars and failed:

| Family | Our measured result |
|---|---|
| Carry | FX Sharpe **−0.126**, break-even 468 bp ≈ 62× cost; crypto funding **−11 bp/tick** |
| TSMOM / trend | only live line; SPY-200d null 53.4 vs excess **−6.8 pp**; ETF version 9.3 years from a verdict |
| Cross-sectional momentum | N=90 → **DSR 0.9543 → 0.3191**, 0 of 6 classes survive |
| Risk premia (value) | **+0.11%/yr gross, +0.02% net** vs 4.32% hurdle |
| VRP | **unmeasured** — no options history in the estate |
| Mean reversion | FX break-even 4.30 bp **< 7.53 bp measured**; crypto PF 0.815 after costs |

Six verified families, five measured and dead, one unmeasured for lack of data. The reading list explains *why the
hypotheses were worth testing*; it does not resurrect a single one of them. That distinction — literature sets the
prior, our bars set the verdict — is the whole discipline in one line.
