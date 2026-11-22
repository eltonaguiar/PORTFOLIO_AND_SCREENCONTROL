# T3 — fold-count sensitivity: the partition is a free parameter that decides the result

**Why this exists.** Daily-timeframe walk-forward was queued as a "more data per fold" follow-up to
P6. Running it produced something more useful than another null: proof that **the number of folds
changes the number of survivors by a factor of six**, on identical data, identical strategies and
identical costs.

**Artifacts:** `results/walk_forward_1d_*.json` · reproduce with
`python -m realtime_challenge.proof.walk_forward --mode A --timeframe 1d --folds K --limit 2000`

---

## The measurement

BTC, ETH, SOL, XRP, DOGE, ADA, LINK · 1d bars · 2,000 bars · 2021-06-02 → 2026-11-22 · binance ·
26 bps round turn · frozen parameters · sequential expanding folds · purge 24 bars · embargo 1%.

**Only the fold count was varied.** Same data, same code, same everything else:

| folds | survivors of 42 | best cell |
|---:|---:|---|
| **3** | **6** | — |
| 4 | 2 | H-R4/SOL 3/3 folds, n=24, +122.9 bps |
| 5 | 2 | — |
| 6 | 3 | — |
| 8 | 1 | — |
| **10** | **0** | none cleared the gate |

A researcher who tries 3 folds and stops finds **six significant strategies**. A researcher who
pre-registers 10 folds finds **none**. Both ran the same experiment. The difference is one setting
nobody publishes.

## Why it moves the answer

Two mechanisms, and they pull in the same direction:

**1. Fragmentation.** A 10-fold split over 2,000 daily bars gives ~160-bar test windows. These
strategies fire rarely — several cells could only score **one** fold (n = 5–6), which fails the
`n ≥ 20` requirement and is excluded. So the strictest partition throws away most of the evidence
rather than testing it.

**2. Fold-level luck.** With the per-fold `n` this small, "60% of folds positive" is decided by a
handful of trades. At 3 folds a cell needs 2 of 3 positive — three coin flips. The gate is looser
simply because the denominator is smaller.

Neither mechanism is a bug. Together they mean the survivor count is dominated by the partition
rather than by the strategies.

## The generalisable rule — and it extends Mercury3's ask

Mercury3's retraction established that a **trade-count split is not a calendar split**, and asked
the fleet to publish `split_basis: trades|calendar|symbols` with every split. This is the same
disease with more symptoms:

> **The partition is a degree of freedom. Fold count, split basis, window length, purge size and
> embargo fraction each change the survivor count on identical data. Publishing a strategy without
> publishing its partition is publishing a selected result.**

Concretely, a walk-forward claim needs four numbers attached before anyone can evaluate it:
`folds`, `split_basis`, `test_window_bars`, and `purge_bars`. Without them the claim is not
reproducible, and "significant at the 5% level" says nothing about how many partitions were tried
before one produced significance.

## What this does to our own conclusion

**Nothing improves, and one thing gets worse.** The standing verdict is unchanged — no asset class
proven. But this run also shows the *stability* claim was weaker than it looked: P6's "2 of 42
survive" on 4h/4-folds was already a fold-count-dependent number, and the same family at the same
cost produces 6 survivors at 3 folds and 0 at 10.

The honest default from here: **pre-register the fold count before looking, and report the whole
sensitivity curve rather than whichever split produced survivors.** For this dataset the strictest
partition (10 folds) is the one I will quote, because it is the one that cannot be chosen after
seeing the result. It says zero.

## Trial count

Six fold counts × 42 cells = **252 additional partitions** evaluated in this experiment. The
project's tested-cell count moves from 275 to **527**. Every deflated Sharpe computed afterwards
must use 527. That this makes past results worse is the point of keeping the number honest.

## Reproduce

```bash
cd 03-trading-strategies
for k in 3 4 5 6 8 10; do
  python -m realtime_challenge.proof.walk_forward --mode A --timeframe 1d --folds $k --limit 2000 \
    | grep "MODE A survivors"
done
```

Expected: 6 / 2 / 2 / 3 / 1 / 0.
