# Timeframe matrix — the class census, crypto spot (roadmap P1, R13–R20)

Six pre-registered hypotheses × 7 crypto majors × **three timeframes** = **126 cells**.
Frozen parameters, `lag1_next_open` fills, taker fee + slippage on both legs (**26 bps
round turn**), deflated Sharpe against the full trial count, permutation control on
shuffled close-to-close returns.

Artifacts (read every number below from these, not from this prose):

| run | artifact |
|---|---|
| 1h, 3,000 bars | `results/backtest_binance_1h_20261122T090813Z.json` |
| 4h, 4,000 bars | `results/backtest_binance_4h_20261122T093118Z.json` |
| 1d, 1,200 bars | `results/backtest_binance_1d_20261122T093116Z.json` |

---

## 1. Windows and power

| timeframe | bars | window | approx. span | bars/year |
|---|---:|---|---|---:|
| 1h | 3,000 | 2026-07-20 → 2026-11-22 | 125 days | 8,760 |
| 4h | 4,000 | 2025-01-24 → 2026-11-22 | 22 months | 2,190 |
| 1d | 1,200 | 2023-08-11 → 2026-11-22 | 3.3 years | 365 |

The 1h window is short by construction (exchange history limits + rate limits). It is the
weakest of the three and its results are quoted with that in mind.

## 2. Pooled result per family, at 26 bps round turn

Mean net return per trade, in bps, pooled across symbols.

| family | 1h | 4h | **1d** | reading |
|---|---:|---:|---:|---|
| H-R1 trend_pullback | −40.26 | −20.31 | −205.56 | dead at every horizon |
| H-R2 donchian_breakout | −27.41 | −30.80 | **+4.77** | dies on cost until daily, then merely breaks even |
| H-R3 bollinger_meanrev | −28.16 | −46.24 | −92.75 | worse as the horizon lengthens — no reversion edge |
| H-R4 vol_compression | −32.11 | −50.13 | **+20.40** | **sign flips with horizon** — see §4 |
| H-R5 weekend_effect | +5.93 | −46.02 | n/a | the 1h number did not survive a proper test (see §3) |
| H-R6 rsi2_pullback | −16.45 | −27.43 | −165.68 | dead at every horizon |

## 3. Nothing clears the significance bar — at any horizon

| timeframe | best deflated Sharpe among cells with n ≥ 10 | best permutation p-value |
|---|---:|---:|
| 1h | 0.071 | 0.20 |
| 4h | 0.256 | 0.28 |
| 1d | 0.183 | 0.40 |

The bar is DSR ≥ 0.95. **The best cell in 126 attempts reaches 0.256.** That is what a
search of this width produces from noise, and it is why the trial count is recorded.

The weekend effect's apparently strong 4h cell (ETH, PF 1.46, +15.6% total, DSR 0.256) is
the single best number in the matrix — and it is already dead. `proof/weekend_test.py`
re-tested the pure calendar trade over 3.0 years with **clustering by calendar weekend** and
42 control windows: −3.21 bps, 95% CI [−67.3, +64.5], rank **#15 of 42**. The 4h cell is a
different instrument (calendar entry *plus* a 3×ATR bracket), so its PF is not a rescue of
the family — it is a bracket effect on a window that the clustered test says has no drift.

## 4. The one real finding: horizon flips H-R4

`H-R4_vol_compression` (volatility squeeze → 12-bar range breakout) is the **worst family at
1h (−32 bps)** and the **best at 1d (+20 bps, PF 1.075, n=119)**. That direction is
mechanically plausible and worth stating precisely:

- At 1h, a 20 bps round trip has to be earned inside 36 bars (~1.5 days) of a market that
  has just compressed — the breakout is small relative to friction.
- At 1d, the same rule gets 36 **days** for the expansion, so the move it is trying to
  capture is an order of magnitude larger than the cost.

**But it is not an edge yet, for two reasons that must be stated together:**

1. **n = 119, PF = 1.075, mean +20.40 bps, bootstrap 95% CI [−87.90, +132.99],
   P(mean > 0) = 0.646.** A 7.5% gross-to-net margin over 119 trades is inside the noise
   band; the CI straddles zero by a wide margin. (Computed at n_trials = 126, which is the
   deflation input after the timeframe census; the pooled DSR is 0.0118.)
2. **The permutation control says p = 0.40.** On *shuffled* close-to-close returns the same
   rule still produces a similar mean. That is the honest diagnosis: what looks like
   "volatility clustering pays" is reproducible when the clustering is destroyed, which
   means the +20 bps is a property of **the bracket and the entry timing distribution**, not
   of market structure.

That second point is the most valuable line in this document. A horizon scan that reported
only §2 would have promoted H-R4 to a forward pod on the strength of a sign flip. The
shuffle control is what stops that.

## 4b. The same rule, three windows, three wildly different answers

The weekend family is the clearest demonstration of why a short window cannot estimate a
small edge. Same rule, same 26 bps cost, three different samples:

| window | observations | mean per trade | source |
|---|---:|---:|---|
| 42 days (2026-10-11 → 11-22) | 42 | **−162.5 bps** | early run, before the pagination fix — window valid, sample 1/3 the size |
| 125 days (2026-07-20 → 11-22) | 126 | **+5.93 bps** | `results/backtest_latest_1h.json` |
| 3.01 years, clustered by weekend | 156 events | **−3.21 bps** | `results/weekend_test.json` |

A spread from **−162 bps to +6 bps** on the same rule is not noise around a stable mean; it
is a mean that a short sample cannot locate. The 125-day figure is the one that *cleared
friction* and would have justified a forward pod. It is also the one that a 3-year clustered
test reversed.

Two lessons, both now enforced:

1. **Pooled n overstates evidence when the observations share a cause.** 7 coins × 18
   weekends is ~18 events, not 126. The clustered bootstrap in `proof/weekend_test.py`
   resamples *weekends*, which is the reason its CI is honest.
2. **A cell that only clears costs on a short window has not cleared costs.** The breakeven
   cost table (§2) is a statement about a point estimate; it is only meaningful next to the
   window that produced it.

The two failing artifacts from the buggy data path (`..._090644Z.json`, 1,000 bars instead of
3,000) were **removed from `results/`** rather than kept with a caveat, because a committed
JSON with the wrong window is indistinguishable from a correct one to anyone who does not
read `bars`. Its numbers survive only in this table, labelled.

## 4c. Third control: random entry (does the SIGNAL's timing add anything?)

Adopted from a peer proposal (GLM 5.3 Flash: a seeded random-entry control). This answers a
different question from the permutation control:

| control | shuffles | asks |
|---|---|---|
| permutation | **prices** (`stats.permutation_control`) | is there structure in the price series? |
| random-entry | **entry timing** (`proof/random_entry_control.py`) | does *when* the signal fires beat a random entry with the same exit machinery? |

A rule can pass one and fail the other, and the failure it catches is specific: a rule whose
positive mean comes from its **bracket** (36 bars for a volatility expansion to pay a 26 bps
round trip) rather than from its **timing**. Random entries get the identical TP/SL multiples,
sizing, `max_bars` and costs; only the entry moments are drawn uniformly.

**What it found, before correction:** 2 of 29 powered cells beat random timing at raw
p < 0.05 — `H-R2_donchian_breakout/SOL` (p = 0.015) and `H-R4_vol_compression/ETH` (p = 0.030,
real **+240.5 bps/trade** vs random median **−17.8 bps**, 97th percentile).

**What it found, after correction:** nothing.

| k | cell | raw p | BH threshold (5% FDR) | survives? |
|---:|---|---:|---:|---|
| 1 | H-R2_donchian_breakout/SOL | 0.015 | 0.00172 | ✗ |
| 2 | H-R4_vol_compression/ETH | 0.030 | 0.00345 | ✗ |
| 3 | H-R3_bollinger_meanrev/XRP | 0.050 | 0.00517 | ✗ |

The expected false-positive count for 29 tests at α = 0.05 is **1.45**. Observing 2 is
indistinguishable from noise, and Benjamini–Hochberg leaves **0 survivors**.

That correction matters enough to be stated explicitly, because the first version of this
test printed a per-cell label — *"SIGNAL ADDS TIMING VALUE"* — for any cell above the 95th
percentile. On its own that label was a multiple-testing machine: 29 cells, one of which will
land above the 95th percentile by construction. The per-cell verdict is now deliberately
neutral and only the BH-corrected reading can claim anything.

### What it does establish

One thing is not noise, because it is a large effect in the wrong direction:

| cell | real mean | random median | percentile |
|---|---:|---:|---:|
| H-R6_rsi2_pullback/SOL | **−374.4 bps** | −27.7 bps | 0.00 |
| H-R6_rsi2_pullback/LINK | **−426.6 bps** | −16.4 bps | 0.00 |
| H-R6_rsi2_pullback/ADA | **−434.2 bps** | −101.1 bps | 0.005 |
| H-R3_bollinger_meanrev/SOL | **−299.6 bps** | −9.9 bps | 0.01 |

The mean-reversion entries are **worse than random** by an order of magnitude, across four
independent cells. Buying a dip in an asset that keeps falling is not a neutral mistake — it
is the worst of the 29 timings tested. That reinforces the archive decision on H-R3 and H-R6
from §2 with a second, independent mechanism.

### The three controls now agree

| control | best result across 126 cells |
|---|---|
| deflated Sharpe (vs trial count) | **0.256** against a 0.95 bar |
| permutation (shuffled prices) | **p = 0.40** |
| random-entry (shuffled timing, BH-corrected) | **0 of 29 survive** |

Three mechanisms, three different null hypotheses, one answer. That is the strongest form the
negative result can take, and it is why the verdict is "no asset class proven" rather than
"promising but unconfirmed".

## 5. What this changes in the plan

| change | why |
|---|---|
| H-R1, H-R3, H-R6 **archived across all horizons** | negative at every timeframe and every cost level; not re-run with new parameters |
| H-R2 **survives only at 1d**, and only at breakeven | +4.77 bps, PF 1.013, n=445, CI [−72.2, +81.2], P(>0)=0.549 — not tradeable after any cost variance |
| H-R4 **gets one forward pod at 1d**, not at 1h | the only cell family with a positive pooled mean at retail cost and a mechanism; must prove itself live, and its permutation p = 0.40 is disclosed next to any PF |
| trial count is now **126**, not 42 | every deflated Sharpe quoted from here uses 126 |
| the 1h window is flagged as low-power | 125 days cannot distinguish a 20 bps edge from zero; the 4h/1d windows are the ones to quote |

## 6. Reproduce

```bash
cd 03-trading-strategies
python -m realtime_challenge.cli backtest --venue binance --timeframe 1h --bars 3000 --permutations 100 --verbose
python -m realtime_challenge.cli backtest --venue binance --timeframe 4h --bars 4000 --permutations 60 --verbose
python -m realtime_challenge.cli backtest --venue binance --timeframe 1d --bars 1200 --permutations 60 --verbose
python -m realtime_challenge.proof.weekend_test
```

Each run writes `results/backtest_latest_<timeframe>.json` plus a timestamped copy, so a
committed artifact is never ambiguous about which timeframe it measured.
