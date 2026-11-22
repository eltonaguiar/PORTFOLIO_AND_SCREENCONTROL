# P6 — walk-forward with purge and embargo: the gate that had never been run

**Why this document exists.** Every other result in this project scores a strategy over one full
window. That answers *"did this rule work over 22 months"* — not *"would I have known to use it
at the time"*. Walk-forward is the difference, and it is the gate in this project's own table
that had never actually been executed.

**Artifacts:** `results/walk_forward_4h_latest.json` ·
`realtime_challenge/proof/walk_forward.py` · reproduce with
`python -m realtime_challenge.proof.walk_forward`

---

## Protocol

4h bars, binance, 7 symbols, **4,000 bars (2025-01-24 → 2026-11-22, 22 months)**. Costs are the
project's standard 26 bps round turn. Folds are **sequential and expanding** — fold *k* trains on
everything before its test window and never sees it. No shuffling.

- **Purge:** the last 48 bars of each train window are dropped, because a trade opened near the
  end of train can close inside test and its label then overlaps the scoring set.
- **Embargo:** the first 1% of the train length is dropped from the start of each test window, so
  late-train features cannot price early-test entries.
- **Mode A — frozen parameters.** The six families already have frozen parameters, so the only
  honest question is *temporal stability*: does the sign hold fold by fold?
- **Mode B — fitted parameters.** An 18-bracket grid over `(tp_atr, sl_atr, max_bars)` is fitted on
  each train window by net expectancy, then applied **untouched** to the next window. This is the
  real overfitting test.
- **Pass rule:** pooled OOS CI lower bound > 0 **and** ≥60% of folds positive, with n ≥ 20.

## Mode A — 2 of 42 cells survive, and both were already dead

| survivor | folds positive | OOS n | pooled net |
|---|---|---:|---:|
| H-R6_rsi2_pullback / ADA | 3 of 4 | 43 | **+40.84 bps** |
| H-R5_weekend_effect / ETH | 3 of 5 | 82 | **+21.12 bps** |

Two of 42 is what you expect from chance alone, and the cross-check is worse than that: **both
survivors are cells that two independent controls had already killed.**

- **H-R6 RSI2 / ADA** was the **worst cell of 29** in the random-entry control: real −434.17 bps
  versus a random-entry median of −101.07, p = 0.995. Its entries were worse than random.
- **H-R5 weekend / ETH** was disconfirmed by the 3.01-year clustered test: −3.21 bps, rank 15 of
  42, "NOT ESTABLISHED".

The walk-forward resurrects both. That is not a contradiction in the data — it is a statement
about the gate. **Temporal stability is the weakest of the controls: it asks only whether the sign
held, never whether the sign was distinguishable from luck.** A cell can hold its sign in 3 of 4
folds on 43 trades and still be worse than random. This is why the four controls are run
together and a survivor must clear all of them.

## Mode B — the brackets are the overfitting engine

This is the important number in the document.

**33 folds made money on the training window. 24 of those 33 lost money on the next window. A
73% collapse rate.**

| | count |
|---|---:|
| fitted folds that were train-positive | **33** |
| …that were also test-positive | **16** |
| …that **collapsed** (train > 0, test ≤ 0) | **24** (73%) |
| out-of-sample positive rate | **28.6%** — worse than a coin flip |

Selecting `(tp_atr, sl_atr, max_bars)` on the training window had **negative predictive value**
for the following window. Picking the bracket that would have worked is not a mild overfit that
shrinks out of sample; here it actively inverts.

Only one cell converted: **H-R5 weekend / ETH, 4 of 4 train-positive → 3 of 4 test-positive, 83
OOS trades.** It is the same weekend effect that the 3-year clustered test killed. Even the
single clean conversion is a cell another gate refuted.

This is the strongest statement the project can currently make about retail practice, and it
generalises past this repo:

> **Tuning take-profit and stop-loss on data you then score is not a small bias — it is how the
> edge gets created and destroyed. 73% of in-sample-winning brackets lost money in the window
> that followed.**

It also explains the live books. The probe rounds used `tp_atr` 0.8–1.2 against `sl_atr` 0.5–0.6
and produced **0 take-profits in 27 trades**. Bracket width is the parameter with the highest
apparent tuning value and the least real information.

## Trial count

Mode A adds 42 cells. Mode B adds 18 strategy×symbol cells × 4 folds = **72 fitted selections**,
each an 18-bracket sweep, so the *effective* trial count rises from 126 to **240 tested cells**.
Every deflated-Sharpe figure computed after this document should use 240, not 126. That
correction only ever makes future results look worse, which is the point.

## What this does and does not establish

**Establishes:** (a) walk-forward stability alone is insufficient and resurrects cells that
permutation and random-entry controls kill; (b) bracket selection on a scoring window inverts out
of sample 73% of the time; (c) no family in the six has stable temporal structure.

**Does not establish:** that walk-forward is useless — Mode A is a *necessary* filter, and it did
correctly fail 40 of 42 cells. Nor does it rule out an edge in brackets fitted with far more data
per fold: 4 folds over 22 months gives ~40–150 OOS trades per cell, which is thin. A 10-fold run
over 3.3 years of daily bars is the natural next step and is queued in the roadmap.

## Reproduce

```bash
cd 03-trading-strategies
python -m realtime_challenge.proof.walk_forward --mode A   # ~40s
python -m realtime_challenge.proof.walk_forward --mode B   # ~6min
```

Two bugs fixed during this run, recorded because they change the numbers: `BacktestResult.trades`
holds `as_dict()` payloads rather than `Trade` objects (first run raised `AttributeError`), and
kraken's inner-joined 4h panel across all seven symbols is only **721 bars**, not 4,000 — the
first version would have silently walked forward over 4 months instead of 22 and reported
whatever fits in 120 days. The panel now comes from binance with caching bypassed.
