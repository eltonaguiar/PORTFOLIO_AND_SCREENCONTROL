# VERDICT_200 — consolidated status of every tested class

Generated: 2026-11-22 (Session B, cron queue axis, workdir C:/Users/zerou/pasc)
Repo: github.com/eltonaguiar/PORTFOLIO_AND_SCREENCONTROL, branch main

This is the single source of truth for what has been measured, what survived, and what is retired. Every number below comes from a committed artifact on main; none is a live P&L, none is quoted before n_open == 0, and no gate was lowered to let a candidate through.

## Bottom line

| Category | Classes |
|---|---|
| PROVEN | none |
| CANDIDATE | none |
| DEAD | crypto spot 1d walk-forward, crypto census (edge), equity factors VLUE/QUAL/USMV/MTUM, R191/R192 trend overlay, FX majors census |
| UNMEASURABLE | FX rate differentials / carry baseline |

No tested class delivers a harvestable edge after costs, permutation control, and the exposure control. The honest state is: nothing to allocate to yet.

## Verdict table

| Class | Verdict | Gate that decided it | Deciding number | Artifact |
|---|---|---|---|---|
| Crypto spot 1d walk-forward (binance, 7 sym, 2000 bars) | DEAD | walk-forward gate: >=60% folds positive AND pooled>0 AND n>=20 | 0 of 42 cells survive (Mode A frozen params); Mode B 20/42 collapses (~47%), train-picked bracket has negative predictive value | realtime_challenge/results/walk_forward_1d_latest.json |
| Crypto census (walk-forward split, descriptive) | DEAD (no edge claimed) | descriptive census, no edge scored | 7 symbols x 10 folds = 70 cells scored, ~142-157 bar test windows, window returns -62% to +360%, no edge claimed | realtime_challenge/results/crypto_census_latest.json |
| Equity factors VLUE/QUAL/USMV/MTUM vs SPY | DEAD | four checks: timed Sharpe vs SPY, permutation p<=0.05, exposure control, SPY reproducibility | no factor clears all four; timed Sharpe VLUE 0.372 / QUAL 0.498 / USMV 0.532 / MTUM 0.519 / 4-factor 0.566, all below SPY 0.619; permutation p 0.61/0.35/0.68/0.28; SPY 10.28% CAGR / 0.619 Sharpe matches H-E1 independent script | realtime_challenge/results/equity_factors_latest.json |
| R191/R192 trend overlay | DEAD (as reproducible edge) | one script, one window, one convention: month-end close signal -> next-day open fill, 5 bps/side | SPY B&H reconciles (10.28% vs peer 10.27% CAGR; -55.19% vs -55.2% DD exact) but overlay does not reproduce: 5.83% vs peer 8.37% on 2006-2026; start date explains only ~16% of gap | realtime_challenge/results/r191_r192_reconciliation.json |
| FX majors census (P8, 7 majors, ~3094 bars) | DEAD | both gates: CI excludes zero AND permutation p<=0.05 | 0 of 35 cells clear both gates; 8 of 35 positive on point estimate (coin flip predicts 17.5); 0 CI exclude zero; 1 perm p<=0.05 (below expected 1.75 false positives); carry baseline spot-only -3.7% CAGR / -0.18 Sharpe | realtime_challenge/results/fx_census_latest.json |
| FX rate differentials / carry baseline | UNMEASURABLE | reachable rate-differential feed required; none available | Yahoo CME futures stale/illiquid, RBA JS-only, RBNZ Cloudflare, SNB/BOJ 404, FRED only stale BOJ (Dec 2023); carry baseline stays spot-only and is recorded as not quotable | realtime_challenge/proof/fx_census.py (fetch_rate_differentials() returns None) |

## Per-class notes

### Crypto spot 1d walk-forward — DEAD
Ten sequential expanding folds over 2021-06-02 -> 2026-11-22, purge 24 bars, embargo 1%, 26 bps round-turn, 7 symbols (BTC, ETH, SOL, XRP, DOGE, ADA, LINK), 42 parameter cells. Mode A (frozen params): no cell reaches the >=60%-folds-positive / pooled>0 / n>=20 gate; most cells score a single fold with n=5-6 because ~150-bar daily test windows are too short for rare daily signals. Mode B (fitted params): 43 folds train-positive, 24 test-positive, 20 collapses (~47%) — picking (tp_atr, sl_atr, max_bars) on the train window has negative predictive value for the next daily window, the same overfitting signature as the 4h horizon. Reproduces Session 3's fold-sweep on current data: 10 folds -> 0 of 42.

### Crypto census — DEAD for edge claims (descriptive only)
70 cells (7 symbols x 10 folds) under the identical walk-forward partition as walk_forward.py, all scored, live marks captured at generation time. Descriptive only: no strategy is scored and no edge is claimed. Window returns span -62% (SOL) to +360% (XRP) across folds — wide dispersion, no persistent signal. Measurable class; no edge.

### Equity factors — DEAD
VLUE (value), QUAL (quality), USMV (low_vol), MTUM (momentum reference), each timed 12-1m momentum + 10m SMA, monthly rebalance, fill at next day's open, 5 bps/side, vs SPY buy-and-hold and exposure-scaled SPY, 200 random long/flat schedules, 100-shuffle permutation, common window 2004-01-02 -> 2026-11-20 (5,759 bars). No factor clears all four checks. SPY reproducibility check passes (10.28% CAGR / 0.619 Sharpe matches H-E1's independently written script to two decimals). Same conclusion as H-E1: factor rotation is dominated by SPY plus a slow trend overlay.

### R191/R192 trend overlay — DEAD as reproducible edge
SPY buy-and-hold and max drawdown reconcile with the peer (10.28% vs 10.27% CAGR; -55.19% vs -55.2% DD exact), and SPY matches H-E1's independent script. The trend overlay does NOT reproduce under one convention: peer reports 8.37% over 2006-2026; this repo measures 5.83% on the same window. Start date (2004 vs 2006) explains only ~16% of the gap (5.34% vs 5.83%); the remainder is convention/cost difference (likely daily close-to-close signaling vs month-end signal -> next-day open fill). R191/R192 closed on numbers: SPY row reconciled, overlay row flagged convention-dependent, not re-runnable to the peer's figure.

### FX majors census — DEAD (clean null)
7 majors (EURUSD, USDJPY, GBPUSD, AUDUSD, USDCAD, USDCHF, NZDUSD), ~3,094 daily bars each (2015-01-02 -> 2026-11-22), 6 strategy families x 3 cost levels (2/5/10 bps RT) = 35 cells, 60-shuffle permutation at 5 bps. Benchmark is FLAT (FX has ~zero expected return), not buy-and-hold. 0 of 35 cells clear both gates. Spot-only carry baseline: -3.7% CAGR, -0.18 Sharpe, -44.87% max drawdown over 2015-01-02 -> 2026-11-20.

### FX rate differentials / carry baseline — UNMEASURABLE
No reachable rate-differential source. Checked and failed: Yahoo CME futures quotes stale/illiquid (double-digit artifacts), RBA JS-only, RBNZ Cloudflare, SNB/BOJ 404, FRED only stale BOJ (Dec 2023) plus current Fed 3.88%, DDG captcha. fetch_rate_differentials() now returns None and fx_census.py degrades to an honestly labeled spot-only baseline. Carry baseline stays spot-only and is recorded as NOT quotable. No rate-differential number published. Unblocked only when a reachable feed appears.

## Infrastructure status (not a class verdict)

- Bracket gate: wired in .github/workflows/realtime-challenge.yml, schedule `45 * * * *`, runs `bracket.evaluate()` + `exit_mix_test()` unattended on the P7 audit probe bracket (BTC 59,700, 1h ATR 426, tp 0.9xATR / sl 0.55xATR, 3-bar hold). The gate must refuse it: at geometry every bracket is zero-EV before costs, and the driftless identity means no bracket choice can create an edge.
- Carry series: hourly at :30 UTC via the carry-series job; 28 ticks recorded, round-trip cost median 11.43 bps, carry-net median -11.35 bps, carry-positive fraction 0.0%. One snapshot is a floor not a mean — the series keeps accruing.
- Forward pod: hourly at :07 UTC via the forward-pod job; no API keys, public exchange endpoints only, no orders sent.

## Reproducibility (R200 pack)

Rebuild each quoted number from main:

- `python -m realtime_challenge.proof.walk_forward --timeframe 1d --folds 10 --limit 2000 --venue binance` -> walk_forward_1d_latest.json (0 of 42)
- `python -m realtime_challenge.proof.crypto_census` -> crypto_census_latest.json (70 cells, descriptive)
- `python -m realtime_challenge.proof.equity_factors` -> equity_factors_latest.json (no factor clears all four)
- `python -m realtime_challenge.proof.r191_r192_overlay` -> r191_r192_reconciliation.json (SPY reconciles, overlay does not)
- `python -m realtime_challenge.proof.fx_census` -> fx_census_latest.json (0 of 35 cells)
- `python -m realtime_challenge.proof.carry_roundtrip` + `python -m realtime_challenge.proof.carry_series` -> carry_series_summary.json (carry series tick)

Nothing here is PROVEN or CANDIDATE. Nothing is funded. Review this doc when a new class passes its gate, or when the FX rate-differential feed becomes reachable.
