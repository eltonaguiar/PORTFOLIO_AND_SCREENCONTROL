# H-E1 — ETF rotation vs trend overlay vs buy-and-hold (first equity/ETF class test)

**Why this exists.** A peer note (Copilot/GPT-5, 2026-11-22) states its central hypothesis:

> "the best chance of success is **ETF Rotation + Trend Following + Multi-Asset Portfolio**
> rather than **Day Trading / Scalping / Options**, because those tend to break down under
> realistic fills and transaction costs."

That is a testable directional claim, and it is the first hypothesis in this project aimed at
**low** frequency. Equities were closed (Sunday), but daily history needs no open market, so
it was tested today rather than deferred.

**Artifacts:** `results/etf_rotation.json` ·
`realtime_challenge/proof/etf_rotation.py` · reproduce with
`python -m realtime_challenge.proof.etf_rotation`

---

## The rule (frozen before running)

| element | setting |
|---|---|
| universe | 10 liquid US ETFs across 6 classes: SPY, QQQ, IWM (US) · EFA, EEM (intl) · TLT, IEF (rates) · GLD (gold) · DBC (commodities) · VNQ (REIT) |
| signal | **12-1 month momentum** = `close[t] / close[t-12m] − 1`, skipping the last month to avoid short-term reversal |
| absolute filter | hold only if `close > 10-month SMA` — the "trend following" leg |
| ranking | cross-sectional, top **K = 2**, equal weight |
| rebalance | monthly. Signal at the **month-end close**, fill at the **next trading day's OPEN**; weights live from that close, and the fill day's return is measured open→close |
| costs | **5 bps per side** baseline (zero-commission broker + ~1–2 bp spread, rounded up), swept to 52 bps |
| window | 2004-01-02 → 2026-11-20 (**22.9 years**, 5,759 daily bars) |
| benchmark | SPY buy-and-hold, same window, same cost model |

## Result — it fails, and it is dominated

| book | CAGR | **Sharpe** | max DD | total |
|---|---:|---:|---:|---:|
| SPY buy & hold | **10.28%** | **0.620** | −55.19% | +838.5% |
| **H-E1 rotation (K=2, 12-1m)** | **5.37%** | **0.410** | −32.78% | +230.6% |
| SPY + 200-day SMA overlay | 7.51% | **0.693** | −21.54% | — |
| SPY + 100-day SMA overlay | 7.34% | **0.702** | −19.34% | — |

Rotation gives up **4.9 points of CAGR** and **0.21 of Sharpe** to buy-and-hold. It does cut
the drawdown from −55% to −33%, so it is not useless — but a **one-line 200-day SMA overlay
beats it on all three axes**: higher CAGR (7.51% vs 5.37%), higher Sharpe (0.693 vs 0.410),
and smaller drawdown (−21.5% vs −32.8%). H-E1 is **strictly dominated** by the benchmark plus
one line of code.

## The shuffle control is what kills it

Shuffle each ETF's daily returns **independently** — which destroys the cross-sectional
structure (who is doing better than whom) while preserving each series' own volatility and
drift — rebuild the prices, and re-run the identical rule:

| | Sharpe |
|---|---:|
| real rotation | **0.408** |
| shuffled cross-section, median | — |
| shuffled cross-section, **p95** | **0.741** |
| **p-value** | **0.66** |

The shuffled cross-section produces a **higher** Sharpe than the real one. That is a
legitimate negative about the signal, not a bug: there is no cross-sectional momentum edge in
this universe over this window that survives rotation against destroyed structure. Two thirds
of random cross-sections do better.

## Where the edge used to be

| period | rotation Sharpe | SPY Sharpe | rotation CAGR | SPY CAGR |
|---|---:|---:|---:|---:|
| 2004–2012 | **0.465** | 0.331 | 6.71% | 4.88% |
| 2013–2019 | 0.096 | **1.102** | 0.43% | 14.18% |
| 2020–2026 | 0.409 | **0.715** | 5.18% | 13.11% |

Rotation **won** the 2004–2012 period and then stopped working. This is the shape of momentum
decay, and it is also why a 22-year backtest is the minimum bar: a 2004-start test alone would
have "proven" the strategy, and a 2013-start test alone would have killed it.

## Cost was never the binding constraint here

| round trip | 0 bps | 4 bps | 10 bps | 26 bps | 52 bps |
|---|---:|---:|---:|---:|---:|
| Sharpe | 0.429 | 0.421 | 0.408 | 0.375 | 0.322 |
| CAGR | 5.71% | 5.57% | 5.37% | 4.81% | 3.92% |

Turnover is **6.6× per year**, so friction barely registers. **This is the direct answer to the
peer's hypothesis:** low frequency trivially survives costs — and that is exactly why "it
survives costs" is not evidence of an edge. The day-trading families in this repo died *at*
the cost line; this one sails past the cost line and dies at the **no-alpha line**. Frequency
is necessary, not sufficient.

## Parameter neighbours — a plateau, but a low one

| K | lookback | Sharpe | CAGR |
|---:|---:|---:|---:|
| 1 | 6m | 0.307 | 4.34% |
| 1 | 12m | 0.448 | 7.25% |
| 2 | 6m | 0.409 | 5.56% |
| **2** | **12m** | **0.408** | 5.37% |
| 3 | 6m | 0.493 | 6.41% |
| 3 | 12m | 0.421 | 5.19% |

No lucky spike — every neighbour sits in 0.31–0.49. That is a genuine plateau, which means the
result is a real property of the rule rather than a fitted point. **The plateau is simply below
SPY's 0.620**, so the honest reading is "this rule is robustly mediocre", and the robustness
does not rescue it.

## Bonus: this independently reproduces the repo's own benchmark

The peer capital-allocation verdict (`reports/2026-11-22-capital-allocation-verdict.md`) quotes
**SPY 10.27% CAGR, −55.2% drawdown** over 2006–2026. This run, on a different window
(2004–2026) and a separately written script, gets **10.28% CAGR, −55.19% drawdown**. Two
decimals of agreement on an independent implementation.

Its **trend overlay** row quotes 8.37% CAGR / −20.5% DD (200-day). This run gets
**7.51% / −21.54%**. Same direction, ~0.9 points apart — most likely the start date (2004 vs
2006) and the rebalance convention (daily close vs month-end). That is roadmap **R191–R192**
materials: one shared script, one window, one convention, then the row is settled.

Also worth recording: the 50-day overlay degrades badly (**Sharpe 0.401**, DD −38.0%) while
100/150/200-day all land at 0.69–0.70. A trend filter needs to be slow; a fast one is just
whipsaw.

---

## Verdict

**FAILS — and it is dominated by the benchmark plus one line.**

| question | answer |
|---|---|
| Does rotation beat SPY? | **No** on CAGR (5.37% vs 10.28%) and **no** on Sharpe (0.41 vs 0.62) |
| Does it beat a 200-day SMA overlay? | **No on every axis** (CAGR, Sharpe, drawdown) |
| Is the cross-sectional momentum signal real? | **No** — shuffle p = 0.66, shuffled p95 above the real Sharpe |
| Was cost the constraint? | **No** — 52 bps round trip only costs 0.15 of Sharpe; it fails with zero costs too |
| Is it stable? | Yes, a genuine plateau across K and lookback — just a plateau below the benchmark |

**What this does to the plan:** the peer's direction — go low frequency, go multi-asset — is
supported on the cost side and **falsified on the outcome side**. The only thing in this entire
project that beats buy-and-hold on a risk-adjusted basis is the **SPY + 100/200-day SMA
overlay** (Sharpe 0.69–0.70 vs 0.62, drawdown −19% to −22% vs −55%), and that is *timed beta*,
not alpha. It agrees with the peer verdict's own conclusion: the defensible default is beta
sized to drawdown tolerance, with a slow trend overlay if −55% is unacceptable.

H-E1 is archived. Do not re-run it with a different K or lookback — the plateau already spans
them, and the shuffle control already says the structure is not there.
