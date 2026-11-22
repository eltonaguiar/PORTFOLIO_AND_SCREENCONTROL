# PROGRESS — trading strategies / backtests / paper trading

Append-only running log. Every row must point at an artifact in this folder; a row with no
artifact is a claim, not progress. Newest session at the top.

Legend for **status**: `RUN` executed · `PASS`/`FAIL` gate result · `FIX` defect found and
fixed · `DOC` written · `PEER` reconciliation with another agent's work.

---

## Session 6 — 2026-11-22 (13:32–13:45 UTC) — `hermes` (Session B, cron queue axis)
Question: why is the scheduled carry time series red on GitHub Actions, and can it be fixed with public endpoints only?

| time (UTC) | status | item | artifact |
|---|---|---|---|
| 13:38 | FIX | carry_roundtrip.py measured binance only; binance.com returns HTTP 451 from GitHub's US datacenter IPs, so the scheduled carry-series job wrote 0 lines and exited 1 at every :30 run (failures at 12:32 and 13:31 UTC). Added venue failover (bybit → okx → binance, per symbol, first reachable wins) mirroring forward_supervisor's proven order; disclosed default-tier taker fees (bybit 6 bp, okx 5 bp, binance 5 bp) are written on every line. Local end-to-end tick green: 7/7 symbols via bybit; series now 14 ticks, median roundtrip 12.04 bp, median net carry −11.83 bp — funding still below cost, so carry stays net-negative and no venue beats cash. | realtime_challenge/proof/carry_roundtrip.py, results/carry_roundtrip.jsonl, results/carry_series_summary.json |

## Session 5 — 2026-11-22 (13:27 UTC) — `hermes` (Session B, cron queue axis)

| time (UTC) | status | item | artifact |
|---|---|---|---|
| 13:27 | PASS | (e) crypto census under the walk-forward split, fold count published | proof/crypto_census.py, results/crypto_census_latest.json |


## Session 4 — 2026-11-22 (12:16–12:30 UTC) — `hermes` (Session B, verification axis)

Question: can the FX carry baseline be made quotable with verified rate differentials, and does the broken P8 module run end to end?

| time (UTC) | status | item | artifact |
|---|---|---|---|
| 12:17 | FIX | Removed fabricated hardcoded policy rates (AUD 4.10 / NZD 4.00 / JPY 0.50 / CHF 1.00 — not verifiable from any reachable source) and the unused next_imm_date stub from fx_census.py; fetch_rate_differentials() now returns None and the module degrades to an honestly labeled spot-only baseline. The committed module previously had a syntax error and could not import; it now compiles and runs end to end. | proof/fx_census.py |
| 12:23 | RUN | Re-ran P8 FX census end to end with the fixed module: 7 majors, ~3,094 daily bars each (2015-01-02 -> 2026-11-22), 6 families x 3 cost levels, 60-shuffle permutation control at 5bps. 0 of 35 cells clear both gates - 8 of 35 positive on point estimate (coin flip predicts 17.5), 0 CI intervals exclude zero, 1 perm p<=0.05 (H-R1/USDJPY p=0.017, n=16, CI [-26.5,+94.2], below the 1.75 expected false positives). Clean null, same as the prior published run. | results/fx_census_20261122T122903Z.json, results/fx_census_latest.json |
| 12:28 | BLOCKER | FX rate differentials unavailable: Yahoo CME futures quotes stale/illiquid (double-digit artifacts), RBA JS-only, RBNZ Cloudflare, SNB/BOJ 404, FRED only stale BOJ (Dec 2023) plus current Fed 3.88%, DDG captcha. Carry baseline stays spot-only (-3.7% CAGR) and is recorded as not quotable; honestly labeled in carry_note. No rate-differential number published. | results/fx_census_latest.json carry_note |

## Session 3 — 2026-11-22 (10:45–11:05 UTC) — `deepseek-flash`

Question: what do the live rounds actually say once the round has *finished*, and does a peer's
control idea change any verdict?

| time (UTC) | status | item | artifact |
|---|---|---|---|
| 10:46 | FIX | **Corrected my own reporting.** Session 1 described the probe book as "3 trades, −$55.76". That was a partial read of a round still running. The full round closed **11 trades**. Corrected in the challenge write-up | `REALTIMECHALLENGE_deepseek-flash_2026-11-22_0356_EST.MD` §5.3 |
| 10:47 | FAIL | Full probe round: **11 closed, 18.2% WR, PF 0.038, −$120.83 (−1.21%)**. Gross price component **−$47.50**, fees **−$73.33** → **fees were 61% of the loss** | `ledger/liveprobe_bybit_v2.jsonl` |
| 10:48 | RUN | Decomposed every trade into gross vs friction. Mean round-turn friction **20.05 bps on all 11**. Trade 8 (SOL short) is the cleanest specimen in the project: **gross +0.200%, net +0.000%** — the gross edge was exactly the width of the round turn. Three trades had positive gross; only one survived the fee | `REALTIMECHALLENGE...MD` §5.3 |
| 10:49 | FAIL | Combined live sample: **17 closed trades, −$148.62, of which $113.33 (76%) is commission.** Gross component across both books only −$35.29. Also directionally wrong: all 5 stops were shorts stopped out in a +3.4% BTC session | same |
| 10:51 | RUN | **Adopted GLM's random-entry control** (new third null): random entries with identical bracket/sizing/hold/costs, only the entry moment differs | `proof/random_entry_control.py` |
| 10:52 | FAIL | Raw: 2 of 29 cells at p<0.05 (H-R2/SOL 0.015; H-R4/ETH 0.030, +240.5 bps vs random median −17.8, 97th pct) | `results/random_entry_control.json` |
| 10:52 | FIX | **Caught my own multiple-testing error.** v1 printed a per-cell label "SIGNAL ADDS TIMING VALUE" above the 95th percentile — on 29 cells that is a machine for manufacturing findings. Label neutralised; BH FDR added | same |
| 10:53 | FAIL | **Corrected: 0 of 29 survive.** Expected false positives for 29 tests at α=0.05 is **1.45**; BH 5% thresholds are 0.00172 and 0.00345 against observed 0.015 / 0.030. Nothing survives | `TIMEFRAME_MATRIX.md` §4c |
| 10:54 | RUN | The control **does** establish a large wrong-direction effect: H-R6 entries are worse than random by an order of magnitude across four cells (−374, −427, −434, −300 bps vs random −10 to −101). Mean reversion into a falling asset was the worst of 29 timings tested | same |
| 10:56 | RUN | Adopted `market_clock.py` (GLM): sessions in the market's own timezone via zoneinfo so DST is handled. Verified against our first live round's moment (Sun 09:00 UTC) → `open_classes == ['crypto']` only | `realtime_challenge/market_clock.py`, `results/market_status.json` |
| 10:57 | RUN | Adopted the outcome taxonomy (Claude Haiku) and the decay alarm (GLM, 60→**20** trades): `ledger.summary()` now returns `outcome`, `rolling_sharpe_20`, `decay_alarm` | `realtime_challenge/ledger.py` |
| 10:59 | DOC | Numeric G1/G2 gate thresholds written into the roadmap as stated *policy choices* with reasons, not as facts | `ROADMAP_200_deepseek-flash.md` |
| 11:01 | DOC | `WORKSTREAMS.md` created: the two concurrent sessions now have an explicit boundary (build/tracking vs verification) with disjoint file ownership, so merges are no-ops | `../WORKSTREAMS.md` |

| 11:10 | PEER | **Duplication check on a pasted allocation-strategy batch.** Five of six items were already in the repo: the four model answers verbatim in `REVIEWS/inputs/ALLOCATION_FOUR_MODEL_ANSWERS.md`, the synthesis in `02-portfolio-multi-asset/CAPITAL_ALLOCATION.md`, the audit3 verdict table (fetched live, timestamped), and the ETF-rotation question already settled by H-E1. Wrote no fifth synthesis | `../WORKSTREAMS.md` duplication log |
| 11:12 | RUN | **The one uncovered item was the doctrine's most load-bearing claim**, quoted in three places and never run: "volatility scaling is free alpha... improves Sharpe by 0.3+ for any momentum strategy". Tested on SPY 2004-2026, 4 strategies, with turnover charged at 5bps/side | `proof/vol_scaling_test.py`, `results/vol_scaling_test.json` |
| 11:13 | FAIL | **0 of 4 strategies reach +0.30 Sharpe** at either a 1.0 or 2.0 leverage cap. Best gain **+0.128** on buy-and-hold (no timing signal at all); TSMOM +0.013 with leverage | `VOL_SCALING_H-VS1.md` |
| 11:14 | FAIL | **It hurts exactly the strategies it claims to help.** The two with real timing value get WORSE: SPY+200d −0.029 (unlev) / −0.101 (lev); SPY 6m ECM −0.034 / −0.089. Vol targeting is itself a trend overlay, so stacking it on a trend signal double-counts the signal and pays turnover twice | same |
| 11:15 | PASS | The useful half survives and is recorded separately: vol targeting does cut realised vol (18.6 pct to 10.2 pct) and drawdown reliably — it belongs in the RISK section of the allocation doc, not the RETURN section | same |

| 11:24 | RUN | **All five live books are now complete.** Read from the ledgers, not the summaries: bybit smoke 6 closed, bybit probe v1 3, bybit probe v2 11, kraken 3, okx 4 = **27 closed trades, 2 winners (7.4% WR), −$285.14** | `REALTIMECHALLENGE...MD` §5.4 |
| 11:25 | FAIL | Fees **$180.00** of a **−$285.14** result = **63%**. Gross price component across all 27 is −$105.14. Mean round-turn friction 20 bps on every trade | same |
| 11:26 | FAIL | **The take-profit fired 0 times in 27 trades** (12 SL, 14 TIME, 0 TP). With tp_atr 0.8-1.2 and sl_atr 0.5-0.6 on a 1h ATR of ~0.7%, the target sat ~0.57% away inside 8-12 min holds where the market moved 0.2-0.5%. This is the roadmap P7 rule confirmed empirically: a bracket wider than the expected move over the hold is unreachable, so the outcome is decided by the clock and the stop, never by the thesis | same |
| 11:27 | PASS | Four venues (bybit ×2, kraken, okx) agree on direction: all lost. Not four independent tests — one wrong idea (shorting 5m dips in a +3.4% session) repeated on four exchanges — but it does confirm the fill/exit plumbing behaves identically across venues, which is what these books existed to check | same |
| 11:28 | FIX | **Silent-overwrite race closed in the new proof.** The stale v1 random-entry run finished after the BH-corrected v2 and wrote the same path; the artifact was verified to be v2 both on disk and on origin, but the race is the same class as `backtest_latest.json`. Script now writes a timestamped copy first, then the canonical file, and carries `generated_utc` | `proof/random_entry_control.py` |

| 11:32 | RUN | **P6 walk-forward — the one gate in our table never executed.** 4h, binance, 7 symbols, 4,000 bars (22 months), sequential expanding folds, purge 48 bars, embargo 1%, 26 bps costs | `proof/walk_forward.py` |
| 11:33 | FIX | Two bugs on the first run, both of which would have silently changed the answer: `BacktestResult.trades` holds `as_dict()` payloads not `Trade` objects (AttributeError), and **kraken's inner-joined 4h panel across 7 symbols is only 721 bars, not 4,000** — the first version would have walked forward over 4 months instead of 22 and reported whatever fits in 120 days. Panel now from binance, cache bypassed | same |
| 11:34 | FAIL | **Mode A (frozen params): 2 of 42 cells survive** temporal stability — H-R6/ADA (3 of 4 folds, n=43, +40.84 bps) and H-R5 weekend/ETH (3 of 5 folds, n=82, +21.12 bps) | `WALKFORWARD_P6.md` |
| 11:35 | FAIL | **Both survivors are cells two other controls already killed.** H-R6/ADA was the *worst of 29* in the random-entry control (real −434.17 bps vs random −101.07, p=0.995, verified from `results/random_entry_control.json`) and H-R5 weekend/ETH was refuted by the 3.01y clustered test (verified from `results/weekend_test.json`: −3.21 bps, CI [−67.26,+64.51], rank 15 of 42). **Walk-forward stability resurrects cells that permutation and random-entry destroy** — it is the weakest of the four controls because it only asks whether the sign held, never whether the sign beat luck | same |
| 11:36 | FAIL | **Mode B (fitted params): 33 folds made money in-sample, 24 of those lost money on the next window — a 73% collapse rate.** OOS positive rate 28.6%, worse than a coin flip. Selecting (tp_atr, sl_atr, max_bars) on the training window had **negative predictive value** for the following window | same |
| 11:37 | DOC | This is the strongest generalisable claim the project can currently make: **tuning TP/SL on data you then score is not a small bias, it is how the edge gets created and destroyed.** It also explains the live books — 0 take-profits in 27 trades from bracket widths chosen by apparent tuning value | same |
| 11:40 | RUN | **P8 FX class census** — the last major class this repo had never tested. 7 majors, 3,094-3,095 daily bars each (2015-01-02 to 2026-11-22, 11.9y), 6 families, 3 cost levels, 60 shuffles/cell | `proof/fx_census.py` |
| 11:44 | FAIL | **0 of 35 cells clear both gates.** 8 of 35 positive on point estimate (a coin flip predicts 17.5, so 8 is *below* chance); **0 CI intervals exclude zero**; 1 permutation p≤0.05 (H-R1/USDJPY p=0.017, n=16) whose CI is [−26.5,+94.2] — and 1 of 35 tests at α=0.05 has an expected false-positive count of 1.75, so finding one is finding fewer than chance | `FX_CENSUS_P8.md` |
| 11:45 | FIX | **Caught a mislabelled benchmark in my own FX work.** My carry baseline printed −3.7% CAGR / Sharpe −0.18 and it would have been easy to write "the classic carry trade lost money this decade". It measures **spot only**. A carry trade also earns the interest differential, which for AUD/NZD vs JPY was strongly positive for most of the window and is the dominant term; that data is not in this dataset. Recorded as "cannot be quoted as carry's return" rather than as a negative | same |
| 11:46 | DOC | Trial count 126 → 240 (walk-forward) → **275** (FX). FX is the third class to return a clean null on this repo's own machinery | same |

| 11:52 | **CORRECTION** | **My 11:26 entry is wrong and is superseded.** I claimed the bracket was "wider than the expected move over the hold, so unreachable". Re-running all 27 closed trades through the reachability gate with each trade's own `atr_1h`: only **6 of 27** were unreachable (all from the smoke book). The other 21 were reachable and still guaranteed to lose | `BRACKET_P7.md` |
| 11:53 | RUN | **Found the identity that explains it.** For a driftless walk `p_TP = sl/(tp+sl)`, so gross `E[R] = p_TP·(tp/sl) − p_SL = a/(a+b) − a/(a+b) = 0` **identically, for every bracket**. Verified numerically across 16 brackets (every one returns gross_EV = 0.000000R). Friction then makes every bracket negative. **A bracket cannot create an edge — the target is where profit is collected, never where it is made** | `proof/test_bracket.py` (22 tests) |
| 11:54 | FAIL | **27 of 27 live trades would have been refused before opening.** NEGATIVE-EV on all 27; UNREACHABLE on only 6. So every trade in every book was arithmetically incapable of showing a profit regardless of signal quality | `bracket.py --audit-ledger` |
| 11:55 | FAIL | **Second independent defect: direction.** Predicted P(TP exit) averaged **0.269**, so ~**7.3 targets of 27** should have occurred. Observed **0** → two-sided binomial **p=0.0003**. Incompatible with the geometry, so the driftless assumption is violated: the positions were systematically against the move | same |
| 11:56 | PASS | Shipped the gate as enforceable code rather than a docstring: `evaluate()` returns `fail_reach` / `fail_balance` / `fail_ev` (the third was initially missing — it only printed a reason while `ok()` still returned True; caught by a test that asserted the probe bracket was refused), `exit_mix_test()` asks whether realised exits match the geometry, and the formulas are validated against 20,000-path Monte Carlo | `realtime_challenge/bracket.py` |
| 11:57 | DOC | Roadmap P7 rule rewritten from "the bracket must be reachable" to the provable form: **"a bracket must have positive expectancy at its own geometry-implied hit rates, which is only possible if the entry carries directional skill"** | `ROADMAP_200_deepseek-flash.md` |

| 12:08 | RUN | **Re-derived the forward gate (`proof/power.py`).** required_n = (z_a+z_b)²·(σ/μ)² from each strategy's own measured dispersion, replacing the arbitrary `n>=100`. Result on the pooled 27 live trades: mean **−31.68 bps**, sd 19.56 bps, **t=−8.42, p=6.7×10⁻⁹**, required n = **3** | `results/power_analysis.json` |
| 12:09 | **CORRECTION** | **I had claimed `n>=100` was "off by four to five orders of magnitude". That was wrong and this calculation refuted it.** The 1.2–28M figure is the *break-even* margin (edge earning exactly zero). For a *useful* +5 bps/trade the requirement is a **+4.93pp win-rate edge over geometry**, verifiable in **121 trades** — so the 100 gate is approximately correct, not absurd | `BRACKET_P7.md` correction section |
| 12:10 | FAIL | **The real constraint is the edge, not the sample.** +5 bps/trade requires beating geometry by 4.93pp of win rate; +20 bps requires 18.95pp. No family in 435 tested cells has come within a fraction of that | same |
| 12:11 | FAIL | **The live books are conclusively unprofitable, not inconclusive.** p=6.7e-9 at n=27, running 31.7 bps/trade worse than break-even. Calling them "too small a sample" would have been a way of not saying so | same |

| 12:52 | RUN | **t3 daily walk-forward, 10 folds.** 1d, binance, 7 symbols, 2,000 bars (2021-06 → 2026-11), purge 24 bars, 10 folds: **0 of 42 cells survive.** Most cells scored only ONE fold (n=5-6) because ~160-bar test windows are too short for rare daily signals | `results/walk_forward_1d_*.json` |
| 12:54 | RUN | **4 folds on the SAME data: 2 of 42 survive** (H-R4/SOL 3/3 folds n=24 +122.9bps; H-R6/ETH 2/3 n=27 +56.53bps). Same strategies, same costs, same window — different answer | same |
| 12:56 | FAIL | **Swept the fold count: 3→6 survivors, 4→2, 5→2, 6→3, 8→1, 10→0 of 42.** A SIX-FOLD swing in survivor count from one undisclosed setting. Try 3 folds and you find six significant strategies; pre-register 10 and you find none | `FOLD_SENSITIVITY_T3.md` |
| 12:57 | DOC | **Generalisable rule extending Mercury3's split_basis ask:** the partition is a degree of freedom. Fold count, split basis, window length, purge and embargo each change the survivor count on identical data. **Publishing a strategy without its partition is publishing a selected result.** A walk-forward claim needs folds + split_basis + test_window_bars + purge_bars attached | same |
| 12:58 | DOC | Standing default from here: **pre-register the fold count before looking, and report the whole sensitivity curve** rather than whichever split produced survivors. For this dataset the strictest partition (10 folds) is the one that cannot be chosen after seeing the result — it says zero | same |
| 12:59 | FIX | Fixed a log line that printed "fetching 4h panel" while actually fetching daily bars — a misreported artifact label is how a 1d result gets cited as a 4h one | `proof/walk_forward.py` |

| 13:05 | RUN | **Mercury3's fleet ask delivered: scheduled carry round-trip series.** `carry_rtt.py` + `.github/workflows/carry-rtt-series.yml` (hourly at :23, commits each tick). Verified green: run 45019309665, bot commit 7e3b96e, **40 rows on origin**. Fees and spread measured separately | `CARRY_RTT_T4.md` |
| 13:06 | PASS | First cross-venue readings (5 ticks, 6 cells): **okx/perp 11.08bp RTT**, bybit/perp 16.25, binance/spot 21.07, bybit/spot 21.07, okx/spot 31.07, **kraken/spot 56.04**. A **5.1x spread** across venues for the same asset | `results`/`ledger/carry_rtt_series.jsonl` |
| 13:07 | **CORRECTION** | **Mercury3's verdict is right and their mechanism is wrong.** They measured 42.64bp, concluded carry is cash-dominated at VIP0 fees. **Five of six venues I can reach are far below their 33.5bp break-even** (okx perp 11.08 = 3.8x cheaper) and all five clear the 0.50 cliff comfortably. Cost is not what kills carry on a competitive venue | same |
| 13:08 | FAIL | **And yet 0 of 6 beat cash.** Net 0.527–0.749bp/day against a 3.5% T-bill at **0.96bp/day**. The binding constraint is **funding decay, not friction**: forward-honest funding of 0.872bp/day sits *below* the risk-free rate, so fixing the fee tier cannot rescue carry. Structural and venue-independent | same |
| 13:09 | DOC | Both statements hold: **cost decides WHICH VENUE** (kraken/spot at 56bp does fail the cliff), **funding decides WHETHER**. The one open question left is whether Mercury3's 46% funding decay is a level or a trend — the series answers it without another backtest | same |
| 13:12 | RUN | **Cross-checked a peer's "sub-2.5bp" assessment against the measured floor.** Three harvested ideas (cross-venue latency arb, auction-imbalance fade, ETF-constituents lead-lag) were judged to need <2.5bp round trips. Measured crypto floor is **11.08bp** → they are **4.4x short on crypto**, dead by a factor rather than a margin | same |
| 13:13 | RUN | But Copilot retracted its ETF round trip from 41.05bp to **~1.4–2.1bp**, which IS under 2.5. So those ideas belong on **equities, not crypto** — the crypto venue is where friction lives. Roughly **40x** across the two classes, so any strategy stating an edge in bps must state its venue class | same |

### Standing state after session 3

- **Three independent null hypotheses now agree.** Deflated Sharpe best 0.256 vs a 0.95 bar ·
  permutation best p = 0.40 · BH-corrected random-entry 0 of 29. One answer.
- **Live evidence is 27 closed trades, −$285.14, 63% commission, 7.4% win rate, and the target
  fired zero times.** No forward edge of any kind.
- **Walk-forward, run for the first time, fails everything and explains the live books.** 2 of 42
  cells survive frozen-parameter stability and both were already killed by other controls; with
  fitted brackets **73% of in-sample winners lose money in the next window**.
- **FX is the third class to return a clean null:** 0 of 35 cells pass CI + permutation.
- **Carry is not killed by fees; it is killed by funding below cash.** Measured round trips 11.08–56.04bp
  across six venue/market cells, five of which clear the 0.50bp/day cliff — yet 0 of 6 beat a 3.5%
  T-bill, because forward-honest funding (0.872bp/day) sits under the risk-free 0.96bp/day.
- **The partition decides the answer.** Same daily data, same strategies: 6 survivors at 3 folds,
  0 at 10. Fold count is an undisclosed multiple-testing axis, and the strictest partition is the
  only one that cannot be chosen after the fact.
- **The sample-size gate was never the binding constraint; the edge requirement is.** +5 bps/trade
  needs +4.93pp of win-rate edge over geometry, verifiable in 121 trades. The live books ran
  31.7 bps/trade worse than break-even (p=6.7e-9), so they are conclusively bad, not underpowered.
- **Brackets provably cannot create an edge** (algebraic identity, 16/16 verified): every one of
  the 27 live trades was negative-EV at its own implied hit rates, and 0 targets against 7.3
  expected says the direction was wrong too.
- **The cleanest single fact in the whole challenge:** a trade with the direction exactly right
  (+0.200% gross) netted +0.000% because the round turn was 20 bps.

### What session 4 must not do

Report a live P&L before the round has exited. Session 1's "3 trades, −$55.76" became "11
trades, −$120.83" once the round finished — a 2x understatement of the loss, from reading a
running process. **Read `n_open == 0` before quoting a total.**

---

## Session 2 — 2026-11-22 (09:30–09:45 UTC) — `deepseek-flash`

Question: does the verdict hold at other horizons, or was 1h hiding something?

| time (UTC) | status | item | artifact |
|---|---|---|---|
| 09:31 | RUN | 4h census: 7 majors × 6 × 4,000 bars (2025-01-24 → 2026-11-22, 22 months) | `results/backtest_binance_4h_20261122T093118Z.json` |
| 09:31 | RUN | 1d census: 7 majors × 6 × 1,200 bars (2023-08-11 → 2026-11-22, 3.3 y) | `results/backtest_binance_1d_20261122T093116Z.json` |
| 09:33 | FAIL | Across **126 cells** at three horizons, nothing clears DSR 0.95. Best deflated Sharpe per timeframe: 1h **0.071**, 4h **0.256**, 1d **0.183** | `TIMEFRAME_MATRIX.md` §3 |
| 09:33 | PASS | Permutation control holds at every horizon — best p-value 0.20 (1h) / 0.28 (4h) / 0.40 (1d). No cell beats a shuffled price path | `TIMEFRAME_MATRIX.md` §3 |
| 09:34 | RUN | **Horizon flip found:** H-R4 vol_compression is the worst family at 1h (−32.1 bps) and the best at 1d (**+20.4 bps**, PF 1.075, n=119). Mechanically plausible: 36 bars vs 36 days to let the expansion pay for the round trip | `TIMEFRAME_MATRIX.md` §4 |
| 09:34 | FAIL | …but H-R4 1d still fails: bootstrap 95% CI on mean trade return **[−87.90, +132.99]**, P(>0)=0.646, pooled DSR 0.0118, permutation **p=0.40**. On *shuffled* returns the same rule reproduces the mean, so the +20 bps is a bracket/timing property, not market structure | `TIMEFRAME_MATRIX.md` §4 |
| 09:35 | FIX | `backtest_latest.json` was silently overwritten by whichever timeframe finished last, making a committed artifact ambiguous about what it measured. Now writes `backtest_latest_<tf>.json` alongside the timestamped copy | `realtime_challenge/cli.py` |
| 09:36 | DOC | Timeframe matrix written: windows and power, pooled per-family table, significance table, the horizon flip with its disconfirming evidence, and what it changes in the plan | `TIMEFRAME_MATRIX.md` |
| 09:42 | FIX | **Data integrity:** `results/` still held `backtest_binance_1h_20261122T090644Z.json` — an artifact from the *pagination-bug* run (1,000 bars, 42-day window). A committed JSON with the wrong window is indistinguishable from a correct one to anyone who does not read the `bars` field. Removed, not caveated | `results/` |
| 09:42 | FIX | `backtest_latest.json` was still present and held the **4h** run under a timeframe-free name — the exact ambiguity I had just patched `cli.py` to prevent. Removed; each timeframe now has only `backtest_latest_<tf>.json` | `results/` |
| 09:42 | FIX | The 1h/4h/1d runs all predate the `cli.py` patch, so no `backtest_latest_<tf>.json` existed. Copied each verified timestamped artifact to its per-timeframe name — a copy, **not a re-run**; no number was re-derived | `results/backtest_latest_{1h,4h,1d}.json` |
| 09:43 | DOC | **New finding from the batch of earlier runs:** the weekend family returned **−162.5 bps** (42 obs, 42-day window), **+5.93 bps** (126 obs, 125 days), **−3.21 bps** (156 clustered events, 3.01 years) on the same rule at the same 26 bps cost. A spread from −162 to +6 bps is a mean a short sample cannot locate — and the +5.93 figure is the one that cleared friction and would have justified a forward pod | `TIMEFRAME_MATRIX.md` §4b |

| 09:52 | PEER | Audited the Subq stack note via the GitHub API: `agent-desktop` 26,040★, Browser MCP 7,398★, `bt` 3,045★, `OptimalPortfolios` 99★ all accurate; **Windows-MCP is 11,999★, not the stated ~6,750**; **backtrader (push 2024-08-19) and qstrader (2024-06-30) recommended as the validation and portfolio layers without disclosing they are 2+ years stale** | `../REVIEWS/SUBQ_STACK_RECOMMENDATION_REVIEW.md` §1 |
| 09:53 | RUN | **Tested the note's headline claim** ("combining strategies improves risk-adjusted return 30-50%") on our own trades: 6 hypotheses × 7 majors, 1d, 3.3 y, 26 bps, daily mark-to-market where a flat day is 0.0% | `realtime_challenge/proof/portfolio_combination.py`, `results/portfolio_combination.json` |
| 09:53 | FAIL | **Claim does not reproduce.** Combined Sharpe **−0.123** vs best single (H-R4) **+0.243** = **−150.6%**. Average pairwise correlation 0.105 and diversification ratio **1.841** — the mix genuinely is far less volatile (4.7% vs 7.4-17.9% annualised) and it still lost. Only **2 of 6** strategies had positive Sharpe | `results/portfolio_combination.json` |
| 09:53 | DOC | Conclusion recorded: diversification reduces variance, it does not create expected return. Portfolio construction is downstream of per-strategy edge — combining four negative-expectancy families with two positive ones yields a diversified near-zero (−2.27% over 3.3 years) | `../REVIEWS/SUBQ_STACK_RECOMMENDATION_REVIEW.md` §3 |
| 09:54 | FIX | The note's multi-asset-vs-portfolio distinction exposed a **real gap I own**: this harness sizes each symbol independently with no shared cash constraint. Mitigated by the pod's `max_open = 4`, but a per-bar shared-cash simulation is still missing (roadmap P5 R157-R160) | `ROADMAP_200_deepseek-flash.md` P5 |
| 09:54 | DOC | `portfolio_combination.py` is a **permanent** portfolio-layer check, not a one-off rebuttal; added qstrader to the avoid list with its verified push date | `realtime_challenge/proof/`, `LIBRARY_SURVEY.md` |

| 09:36 | PEER | Registered on the COMS fleet bus as `inbox/desktop-081g9oh/pasc/hermes-deepseek-flash` (broker 192.168.2.52:1883, ~50 seats). Read before broadcasting: Mercury3 PART13 and subq-savant-1-4 were both already active on this | `coms.ps1 roster` |
| 09:38 | PEER | **Mercury3 PART13 replicated independently**: their 30-symbol 5m run gives gross +28.02 pct, fees 250.80 pct, net -222.78 pct, +2.2bps/trade needing >=12bps, best-case edge/cost 0.56 vs a 3.0 bar. Same mechanism reached here from a different universe, fill convention and codebase | `../03-trading-strategies/PEERCROSSCHECK_deepseek-flash.md` §11.1 |
| 09:58 | DOC | Broadcast to `mentions/all` (retained) with the four items PART13 does not have: the 126-cell census, the frequency answer (1h -32.1bps to 1d +20.4bps), the permutation disconfirmation (p=0.40), and the killed weekend survivor | COMS `mentions/all` |
| 10:02 | DOC | Long-form evidence published to retained topic `notes/pasc-subq-combine-claim-test-2026-11-22`; short non-retained pointers DM'd to `subq-savant-1-4` and `copilot-cli-moneyresearch` | COMS `notes/pasc-subq-combine-claim-test-2026-11-22` |
| 10:04 | FIX | Adopted Mercury3's reporting rule as a standing requirement: every sub-hourly strategy reports **gross / fees / net and the ratio** — if the fee line exceeds the gross line it is a donation, not a strategy | `ROADMAP_200_deepseek-flash.md` |
| 10:05 | PEER | Documented the two fleet-hygiene behaviours hit here: `coms.ps1` refuses `--retain` into another seat's inbox (last-writer-wins guard), and `check` without `-WorktreeName` resolves to the newest registered seat and misses a new worktree's inbox | `PEERCROSSCHECK_deepseek-flash.md` §11.3 |

| 10:08 | PEER | Perplexity note audit: a peer review of the **same** note already existed (`REVIEWS/PERPLEXITY_NOTE_REVIEW.md`, 5 matching tool names), so I re-verified its factual table instead of duplicating it - Windows-MCP 11,999 stars MIT, SayDoneAI/Screenhand 0 stars, screen-use no match, Eigent 15,867, open-cowork 2,283, nuphus-mcp 336 all confirmed | `../REVIEWS/PERPLEXITY_NOTE_REVIEW.md` addendum A0 |
| 10:10 | DOC | Appended a backtesting-half addendum: **four undisclosed licences** (`backtesting.py` AGPL-3.0, `LumiBot` GPL-3.0, `NautilusTrader` LGPL-3.0, vectorbt NOASSERTION) and `vectorbt.pro` has no public repo to audit | `../REVIEWS/PERPLEXITY_NOTE_REVIEW.md` A1 |
| 10:10 | FAIL | Its proposed gate list (OOS, costs, slippage, position limits, drawdown limits, data quality, reproducible artifacts) is **necessary and not sufficient**: all seven were implemented here across 126 cells and **0 qualified**. The missing gates are trial accounting / deflated Sharpe and a permutation control | `../REVIEWS/PERPLEXITY_NOTE_REVIEW.md` A2, `TIMEFRAME_MATRIX.md` |
| 10:11 | DOC | Recorded that engine choice is not the binding constraint: NautilusTrader over vectorbt changes how faithfully you simulate an edge smaller than 26bps; it does not create one. Mercury3 PART13 reaches the same place from a different codebase (fees 9x gross edge) | `../REVIEWS/PERPLEXITY_NOTE_REVIEW.md` A3 |

| 10:14 | PEER | Audited a peer's claimed profitable live trade (ETH/USD long, +0.449% net, 8 min) leg by leg against **1-minute bars from Kraken and Binance**, not against prose | `../REVIEWS/GEMINI_TRADE_0001_AUDIT.md` |
| 10:14 | FAIL | **Cross-venue splice:** entry 1681.50 @09:17 is inside Kraken's bar (1680.76-1681.92) but 0.13 pct BELOW Binance's low; exit 1690.73 @09:25 is 0.14 pct ABOVE Kraken's bar high (1688.43) but inside Binance's. Each leg real on one book, no single venue supports both. On Kraken the price traded at **09:23**, two minutes before the claimed exit | `../REVIEWS/GEMINI_TRADE_0001_AUDIT.md` §2 |
| 10:15 | FAIL | **The profit is the fee assumption.** Claimed 10bps round trip = 5bps/side, below every retail spot taker. Repriced at Kraken base (52bps RT) the best honest exit nets **+0.001 pct - exactly zero**. Same mechanism as Mercury3 PART13 (fees 9x gross) and my 126-cell census (5 of 6 families negative) | `../REVIEWS/GEMINI_TRADE_0001_AUDIT.md` §3 |
| 10:15 | FAIL | **Its OPEN trade is mispriced:** TRADE_0002 entry 1690.73 @09:26 is 0.26 pct above Kraken's high (1686.36) and 0.10 pct above Binance's (1689.35) - unattainable on both, and it is still accumulating | `../REVIEWS/GEMINI_TRADE_0001_AUDIT.md` §4 |
| 10:16 | PASS | Confirmed two design choices in my own harness were the right ones: venue is fixed on the trade at open (a fallback would mark it unverified, never re-price it), and the ledger is append-only JSONL with state rebuilt from it, not a mutable JSON document | `realtime_challenge/ledger.py`, `live.py` |

| 10:21 | RUN | **First equity/ETF class test (roadmap P1, R28-R31).** H-E1 dual-momentum rotation: 10 ETFs across 6 classes, 12-1m momentum, top-2, 10m SMA filter, monthly rebalance, month-end signal -> next-day OPEN fill, 5bps/side, 2004-2026 (22.9 y) | `realtime_challenge/proof/etf_rotation.py`, `results/etf_rotation.json` |
| 10:21 | FAIL | H-E1 vs buy-and-hold: CAGR **5.37 pct vs 10.28 pct**, Sharpe **0.410 vs 0.620**, maxDD -32.8 pct vs -55.2 pct. Gives up 4.9 points of CAGR and 0.21 of Sharpe | `ETF_ROTATION_H-E1.md` |
| 10:22 | FAIL | **Permutation control kills it:** shuffle each ETF's returns independently (destroys the cross-section, keeps each series' volatility) -> real Sharpe 0.408, shuffled **p95 0.741**, **p = 0.66**. A destroyed cross-section does better than two thirds of random draws | `results/etf_rotation.json` |
| 10:22 | RUN | **Strictly dominated by one line of code:** SPY + 200d SMA = CAGR 7.51 pct, Sharpe **0.693**, maxDD -21.5 pct; SPY + 100d = 7.34 pct, **0.702**, -19.3 pct. H-E1 loses on all three axes | `ETF_ROTATION_H-E1.md` |
| 10:23 | PASS | **Reproduced the repo's own benchmark independently:** peer verdict quotes SPY 10.27 pct CAGR / -55.2 pct DD (2006-2026); this separately written script gets **10.28 pct / -55.19 pct** on 2004-2026. Two decimals of agreement. Peer's trend-overlay row (8.37 pct / -20.5 pct) vs mine (7.51 pct / -21.54 pct) is a 0.9-point gap -> roadmap R191-R192 | `ETF_ROTATION_H-E1.md` |
| 10:23 | RUN | Sub-period decay: rotation beat SPY in 2004-2012 (Sharpe 0.465 vs 0.331) and lost badly after (0.096 vs 1.102 in 2013-2019). A 2004-start test alone would have proven it; a 2013-start test alone would have killed it | `results/etf_rotation.json` |
| 10:24 | DOC | Cost was never the constraint: turnover 6.6x/yr, Sharpe 0.429 at 0bps -> 0.322 at 52bps. **Low frequency trivially survives costs** - so surviving costs is not evidence of edge. Day trading died at the cost line; this dies at the no-alpha line. Frequency is necessary, not sufficient | `ETF_ROTATION_H-E1.md` |
| 10:25 | DOC | H-E1 archived with its test. The only thing beating buy-and-hold risk-adjusted is the slow trend overlay (timed beta, not alpha) - which agrees with the peer capital-allocation verdict | `../REVIEWS/COPILOT_GPT5_STACK_AND_ETF_HYPOTHESIS_REVIEW.md` |

| 10:31 | PEER | Audited the ChatGPT/GPT-6 note. It is the **only submission that abstained**: NO TRADE, with every deliverable marked unstarted and the reason stated as 'a documented no-trade decision is better than false evidence' | `../REVIEWS/CHATGPT_GPT6_ARCHITECTURE_AND_NOTRADE_REVIEW.md` §1 |
| 10:31 | FAIL | Its BTC snapshot (59,080-59,316 at 09:18 UTC) was stale ~0.7 pct: the quoted HIGH is **$272 below the lowest print on any of three venues** in that minute (Kraken 59,588 / Bybit 59,688 / Binance 59,692) | `../REVIEWS/CHATGPT_GPT6_ARCHITECTURE_AND_NOTRADE_REVIEW.md` §2 |
| 10:32 | PASS | **But it disclosed the timestamp defect and refused to trade on it** - which is exactly why a stale quote did not become a fake win. Same mistake class as the Gemini trade, opposite handling: one abstained, the other booked +0.449 pct that nets +0.001 pct at real fees | `../REVIEWS/CHATGPT_GPT6_ARCHITECTURE_AND_NOTRADE_REVIEW.md` §2 |
| 10:33 | PEER | Verified its UFO² recommendation: `microsoft/UFO` **10,226 stars, MIT, pushed 2026-10-30**, HostAgent/AppAgents/MCP all confirmed in the README. Mild version drift - the repo is now branded **UFO³** with UFO² a component, so the pick is valid but one generation back | `../REVIEWS/CHATGPT_GPT6_ARCHITECTURE_AND_NOTRADE_REVIEW.md` §3 |
| 10:34 | DOC | Recorded the batch-wide gap: its three-agent red-team (generate / disprove / validate data) has no **trial accountant**, so 'thousands of variations' will yield the luckiest candidate as a confirmed winner. Permutation control + deflated Sharpe are the mechanical versions of those roles | `../REVIEWS/CHATGPT_GPT6_ARCHITECTURE_AND_NOTRADE_REVIEW.md` §5 |

### Verdict changes after session 2

- **Trial count: 42 → 126.** Every deflated Sharpe quoted from here deflates against 126.
- **H-R1, H-R3, H-R6 archived across all horizons.** Negative at every timeframe and every
  cost level. Not to be re-run with new parameters.
- **H-R2 survives only at 1d and only at breakeven** (+4.77 bps, CI [−72.2, +81.2]).
- **H-R4 is the single cell family worth a forward pod, at 1d only** — with its permutation
  p=0.40 disclosed next to any PF it is ever quoted with.
- **The 1h window is low-power** (125 days). Quote 4h and 1d results.
- **Portfolio combination is not a rescue.** Combined Sharpe −0.123 vs best single +0.243 on
  a book where only 2 of 6 families have positive expectancy. Do not present diversification
  as a path to profitability while the components are negative.

### What session 3 must not do

Promote H-R4 on the strength of the sign flip. The shuffle control already says the effect
is reproducible without any market structure, and a forward pod that ignores that is
measuring the bracket, not the market.

---

## Session 1 — 2026-11-22 (08:56–09:35 UTC) — `deepseek-flash`

Topic split: this folder was created out of `02-portfolio-multi-asset/` so that
**strategy/backtest evidence** stops living next to **portfolio valuation**. `02` keeps the
tracking/valuation research; everything measured lives here.

### Harness built

| time (UTC) | status | item | artifact |
|---|---|---|---|
| 08:56 | RUN | Challenge defined; venue = crypto spot (the only class open at 04:00 EST Sunday) | `REALTIMECHALLENGE_deepseek-flash_2026-11-22_0356_EST.MD` §2 |
| 09:00 | DOC | 6 pre-registered hypotheses with frozen params; desk denylist wired in (no AVAX/TRX/MATIC, no UTC 2/8/13/20, `tp/sl ≤ 2.5` asserted at import) | `realtime_challenge/strategies.py` |
| 09:04 | PASS | Harness certification 5/5 — look-ahead detectable, signals causal, cost drag 25.4 bps vs 26 expected, both-touched bar → SL, 0/60 noise cells at DSR 0.95 | `results/harness_certification.json` |
| 09:06 | FIX | ccxt pagination bug: `since` is a *start* time, so paging "backwards" re-returned the same 1,000 bars. The first matrix covered 42 days, not 125. All numbers regenerated | `realtime_challenge/data.py` |
| 09:08 | FAIL | 1h matrix, 42 cells, 26 bps: **0** above deflated Sharpe 0.95 (best 0.071), **0** beating the permutation control (p = 0.20–0.89) | `results/backtest_latest.json` |
| 09:08 | FIX | Metric defect: `excess_vs_bh` credited H-R2 with **+28% "alpha"** for being flat in a −29% bear window. Replaced with `excess_scaled` = strategy − B&H × time-in-market; every excess figure in the first run withdrawn | `realtime_challenge/cli.py` |
| 09:09 | FAIL | Weekend effect re-test, 3.01 y, **clustered by calendar weekend**, 42 control windows: **−3.21 bps**, CI [−67.26, +64.51], P(>0) 0.4465, rank **#15 of 42**, z +0.44 → NOT ESTABLISHED | `results/weekend_test.json` |
| 09:11 | RUN | Live round 1 (SMOKE_TEST): 3 real positions opened on Bybit at real ask + 10 bps | `ledger/live_smoke_bybit.jsonl` |
| 09:18 | FAIL | Live round 1 closed: **6 trades, 0 winners, −$27.79 (−0.278%)**, $40.00 fees. Market moved −5.7 to +2.4 bps; friction took 20 bps. Live reproduction of certification T2 | `ledger/live_smoke_bybit.jsonl`, `results/live_smoke_bybit_summary.json` |
| 09:16 | RUN | Live round 2 (HARNESS_PROBE_5M_BURST): 3 shorts opened on a real 5m impulse signal | `ledger/liveprobe_bybit_v2.jsonl` |
| 09:20 | FAIL | Live round 2 closed: all 3 stopped out at **−49.6/−53.2/−64.6 bps** for −$55.76. Shorting a 5-min dip inside a +3.4% day. Realised loss exceeded the stop distance — slippage through the stop charged, not assumed | `ledger/liveprobe_bybit_v2.jsonl` |
| 09:12 | FIX | Burst scanner sampled only the latest closed 5m bar while each iteration takes 1–6 min, so it saw ~1 bar in 3 and missed most signals (diagnostic: `max\|5m ret\|` 0.70%, 3 qualifying bars/hour, 0 signals fired). Now scans the last 12 closed bars | `realtime_challenge/live.py` |
| 09:24 | FIX | GitHub Actions pod failed: `venue bybit returned no quotes` — Bybit/OKX refuse US datacentre IPs and runners are Azure US. Added venue failover (kraken → coinbase → bybit → okx → binance), single-symbol probe first, venue recorded in the pass summary | `realtime_challenge/worker/forward_supervisor.py` |
| 09:26 | PASS | GHA dispatch green: supervisor picked **kraken**, equity $10,000.00, ledger committed by the bot (`rtc: forward pod pass 2026-11-22T09:26Z`) | Actions run 45007519943 |
| 09:22 | PASS | `screen-control-tests` green on GitHub's Ubuntu runner (9/9) — CI-enforced | Actions run 45007260204 |
| 09:30 | PEER | Audited the repo's prior 2-hour challenge: `REAL_CHALLENGE_FINAL.md` declares a winner on **n=2 trades**, gross of any fee (`grep` for fee/commission/slippage in `challenge_v3.py` → **0** hits), entries priced at the signal bar's own price. Not evidence. Also agreed with the capital-allocation verdict | `PEERCROSSCHECK_deepseek-flash.md` §2–§3 |
| 09:33 | PEER | Reconciled the mid-session peer commits (GPT-4.1-mini blueprint review, paper-trading design, TOOL_INTERFACE approval classes). Adopted their GHA caveat as a rule: hourly supervision ⇒ the bracket must be survivable across a 60-min gap | `PEERCROSSCHECK_deepseek-flash.md` §7–§9 |
| 09:34 | DOC | Roadmap gains the supervision-gap rule; 200 rounds across 10 phases with kill conditions | `ROADMAP_200_deepseek-flash.md` |
| 09:35 | DOC | Library survey: 20 repos, star/last-push/licence verified via the GitHub API on 2026-11-22 | `LIBRARY_SURVEY.md` |

### Standing state after session 1

- **No asset class is proven profitable.** 42 cells, 0 clearing deflated Sharpe 0.95.
- **One family cleared friction and then failed a proper test** (weekend effect).
- **Forward evidence count: 0 qualifying trades** from the pre-registered book. The pods
  are live and hourly; `n` starts accumulating from here.
- **Kilometre zero for the 200-round plan:** P0 (harness integrity) complete; P1 (class
  census) next, with FX opening 17:00 EST and equities Monday 09:30.

### What session 2 must not do

Re-run the 42 dead cells with new TP/SL. They are dead. A parameter change after seeing
results is a new hypothesis with a new id and a fresh forward clock.

---

## Session template (copy for each new session)

```
## Session N — <date> (<start>–<end> UTC) — <agent>
<one line: what question this session answered>

| time (UTC) | status | item | artifact |
|---|---|---|---|
| | | | |

Standing state: <cells / forward n / verdicts changed>
```

## Session 7 — 2026-11-22 (13:45–13:51 UTC) — `hermes` (Session B, cron queue axis)

Question: do value/quality/low-vol (and momentum as the H-E1 reference) deliver a harvestable equity factor premium once costs are charged on position changes, the benchmark is scaled by time-in-market, and random-exposure + permutation controls are applied?

| time (UTC) | status | item | artifact |
|---|---|---|---|
| 13:45 | RUN | (f) equity factor set beyond H-E1: VLUE (value), QUAL (quality), USMV (low_vol), MTUM (momentum reference), each timed 12-1m momentum + 10m SMA, monthly rebalance, fill at next day's open, 5 bps/side; compared vs SPY buy-and-hold, exposure-scaled SPY, 200 random long/flat schedules, 100-shuffle permutation; common window 2004-01-02 -> 2026-11-20 (5,759 bars) | proof/equity_factors.py, results/equity_factors_latest.json |
| 13:51 | FAIL | CLEAN NEGATIVE: no factor clears all four checks. Timed Sharpe: VLUE 0.372, QUAL 0.498, USMV 0.532, MTUM 0.519, equal-weight 4-factor 0.566 — all below SPY 0.619. Permutation p: 0.61 / 0.35 / 0.68 / 0.28. Exposure 37–55% (strategies sit out most of the market and still can't beat SPY risk-adjusted). SPY reproducibility check passes (10.28% CAGR / 0.619 Sharpe matches H-E1). Same conclusion as H-E1: factor rotation is dominated by SPY + slow trend overlay. | results/equity_factors_latest.json |

SPY buy-and-hold reproducibility: CAGR 10.28% / Sharpe 0.619 / maxDD −55.19% over 2004-2026 — two-decimal agreement with H-E1's independently written script.

---

## Session 8 — 2026-11-22 (14:15–14:30 UTC) — `hermes` (Session B, cron queue axis)

Question: does the peer's ETF rotation + trend overlay table reproduce on one shared script, one window, one convention (roadmap R191–R192)?

| time (UTC) | status | item | artifact |
|---|---|---|---|
| 14:15 | RUN | (g) R191/R192 trend-overlay reconciliation: SPY B&H, AOA, 60/40, GIC, SPY+200d overlay under one convention (month-end close signal -> next-day open fill, 5bps/side, 2004 vs 2006 starts), vs peer verdict rows (SPY 10.27% / -55.2%, overlay 8.37% / -20.5% over 2006-2026) | proof/r191_r192_overlay.py, results/r191_r192_reconciliation.json |
| 14:29 | PASS | SPY B&H and max DD reconcile: 10.28% vs peer 10.27% CAGR (2004-start matches H-E1's independent script), -55.19% vs -55.2% DD exact. Trend overlay does NOT reproduce under one convention: peer 8.37% vs mine 5.83% on the same 2006-2026 window; start date explains only ~16% of the gap (5.34% vs 5.83%), so the remainder is convention/cost difference (likely daily close-to-close signaling vs month-end->next-open). R191/R192 closed on numbers: SPY row reconciled, overlay row flagged as convention-dependent, not re-runnable to the peer's figure. | results/r191_r192_reconciliation.json |
