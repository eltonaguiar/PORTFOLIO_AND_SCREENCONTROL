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
