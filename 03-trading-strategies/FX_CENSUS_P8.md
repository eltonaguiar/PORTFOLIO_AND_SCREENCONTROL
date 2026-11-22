# P8 — FX class census: the last major class this repo had never tested

**Why.** The audit3 ledger rates FOREX **WEAK** on n=264 picks (−0.0447/trade, CI straddling zero)
and records the class as "honest-exhausted (H-121 REFUTED)". That verdict comes from the *picks*
layer. This repo's own six families had never been run against the class. FX was the last major
class where that was still true.

**Artifacts:** `results/fx_census_latest.json` · `realtime_challenge/proof/fx_census.py` ·
reproduce with `python -m realtime_challenge.proof.fx_census`

---

## Protocol, and the one thing that changes for FX

7 majors (EUR/USD, USD/JPY, GBP/USD, AUD/USD, USD/CAD, USD/CHF, NZD/USD), **3,094–3,095 daily bars
each, 2015-01-02 → 2026-11-22 (11.9 years)**. Six frozen families, no parameter sweeps.
Permutation control at 60 shuffles per cell.

**There is no buy-and-hold to beat.** A currency pair has roughly zero expected return, so holding
EUR/USD forever earns nothing. The benchmark is therefore **flat**, and the honest question is
whether the strategy beats doing nothing — not whether it beats holding.

**Costs decide FX verdicts, so three are reported** (2 / 5 / 10 bps round turn). A major trades at
roughly 1 pip round turn, so 5 bps is already conservative; the verdict is taken at 5.

## Result: 0 of 35 cells clear both gates

| measure at 5 bps round turn | count |
|---|---:|
| cells with n ≥ 5 | 35 |
| positive on point estimate | 8 |
| **net CI excludes zero** | **0** |
| **permutation p ≤ 0.05** | **1** |
| **both** | **0** |

Best cells by point estimate:

| strategy | pair | n | mean @5bps | 95% CI | perm p |
|---|---|---:|---:|---|---:|
| H-R1 trend pullback | USD/JPY | 16 | **+32.77** | [−26.5, +94.2] | 0.017 |
| H-R1 trend pullback | AUD/USD | 12 | +32.13 | [−45.3, +111.9] | 0.117 |
| H-R4 vol compression | USD/CAD | 31 | +13.51 | [−13.3, +43.6] | 0.200 |

The single cell with a passing permutation p — H-R1 on USD/JPY, p = 0.017 — has a confidence
interval spanning [−26.5, +94.2] on **16 trades**. It fails the CI gate, and on its own terms it is
unremarkable: **1 of 35 tests at α = 0.05 has an expected false-positive count of 1.75.** Finding
one is finding fewer than chance. That is the whole finding, and it is why the CI and the
permutation control have to be read together rather than separately.

Every interval in the table straddles zero. No family clears the gate on any pair.

## The carry baseline, and what it does *not* measure

`carry_baseline` builds a static long-AUD/NZD vs short-JPY/CHF basket from the USD legs
(`ret(A/B) = ret(A/USD) − ret(B/USD)`), on identical bars, at zero cost:

| legs | window | CAGR | ann vol | Sharpe | max DD |
|---:|---|---:|---:|---:|---:|
| 4 | 2015-01-02 → 2026-11-20 | **−3.7%** | 14.8% | **−0.18** | **−44.9%** |

**This is spot return only, and it must not be quoted as the carry trade's return.** A carry
trade earns the **interest-rate differential** as well as the spot move, and for AUD-or-NZD versus
JPY that differential was strongly positive for most of this window — it is the dominant term, and
this dataset does not contain it. So the −3.7% means *the high-yielder depreciated against the
low-yielder on spot over this decade*, which is true and is a real headwind for a spot-only
implementation. It does **not** mean carry was unprofitable, and reading it that way would be the
same category error as quoting a tracker's profit factor as evidence of edge.

The honest statement: **the benchmark that would let a technical family claim an FX edge cannot be
computed from spot data alone**, and adding rate differentials is the next step for this class
rather than an optional one.

## Verdict

**NO FX EDGE ESTABLISHED.** 0 of 35 cells have both a net confidence interval above zero and a
permutation p ≤ 0.05 at 5 bps round turn. 8 of 35 are positive on point estimate alone, which is
consistent with noise: on 35 tests, 17.5 positive is the coin-flip expectation, and 8 is *below*
it.

This is a statement about **these six families on daily bars over this decade**, not a proof the
class is untradeable. FX signals fire rarely on daily bars (most cells carry n < 40 over 11.9
years), so the sample per cell is thin in a way crypto's 24/7 4h bars never are. The class stays
WEAK, now with this repo's own measurement behind the ledger's verdict rather than only in front
of it.

## What is queued, not done

1. **Rate differentials**, so carry can be measured rather than spot-proxied. Without this the FX
   class cannot be properly judged at all.
2. **The live leg** — the FX paper probe waits for the Sunday 17:00 EST open. A historical census
   does not need an open market; a forward round does, and there is no point opening one at 05:00
   EST on a Sunday.

## Note on trial count

35 FX cells bring the project-wide count from 240 to **275 tested cells**. FX is the *third* class
to return a clean null on this repo's own machinery (crypto 126 cells, ETF rotation, FX 35), and
each addition makes every subsequent deflated Sharpe harsher. That is the intended behaviour.
