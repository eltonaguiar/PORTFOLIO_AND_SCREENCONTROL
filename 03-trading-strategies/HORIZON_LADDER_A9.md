# A9 — the cost-horizon ladder, re-derived with units stated

**Task:** `04-investment-strategy/TODO_2026-11-23.md` A9 (owner `H`): *"Re-derive the cost-horizon
ladder with the corrected model and re-publish the figure that currently reads +24.21 bp at 1D."*

**Artifacts:** `realtime_challenge/proof/horizon_ladder.py` · `results/horizon_ladder_latest.json`
· reproduce with `python -m realtime_challenge.proof.horizon_ladder`

---

## What I found before re-deriving anything

The figure **"+24.21 bp at 1D vs −0.57 bp at 15m"** is quoted in four documents as the reason to
work at daily-or-longer horizons:

- `02-portfolio-multi-asset/INVESTMENT_HUB_REVIEW.md:53` — "(Copilot seat, 2026-11-22)"
- `03-trading-strategies/VALUE_VS_PEAD_EVIDENCE.md:62,76`
- `04-investment-strategy/INVESTMENT_DECISION_FRAMEWORK.md:12` — a **gate definition** (G2 Horizon)
- `03-trading-strategies/ASSET_CLASS_IDEA_HARVEST.md:8`

`NEXT_STEPS.md` G-COST-3 defines a kill rule for it:

> "is the 1D cost premium real? recompute on one instrument | **kill the +24.21 bp figure if 1D
> cost > 24.21 bp or < 19 bp** (no edge survives the spread)"

Three defects, in increasing order of seriousness:

1. **No unit.** Nowhere does it say whether 24.21 is **per trade** or **per day**. Those differ by
   365× on a daily strategy.
2. **No gross/net statement.** Whether costs are already subtracted changes the required gross edge
   by the whole round turn.
3. **No implementation.** Neither repo contains a `horizon_ladder`, `cost_horizon` or
   `horizon_sweep` module — checked both `PORTFOLIO_AND_SCREENCONTROL` and
   `findtorontoevents_antigravity.ca`. **Four documents cite a number nobody can recompute.**

## The ladder, rebuilt with every unit stated

Cost is a per-round-trip quantity; the horizon decides how often you pay it:

```
annual cost drag = (365 / holding_days) × round_trip_bps
```

| horizon | round trips/yr | annual drag @ 2bp (equity) | @ 21.07bp (crypto spot) | @ 26bp (our default) |
|---|---:|---:|---:|---:|
| 15m | 35,040 | 70,080% | 738,300% | 911,040% |
| 1h | 8,760 | 17,520% | 184,575% | 227,760% |
| 4h | 2,190 | 4,380% | 46,143% | 56,940% |
| **1D** | **365** | **730%** | **7,691%** | **9,490%** |
| 1W | 52 | 104% | 1,096% | 1,352% |
| 1M | 12 | 24% | 253% | 312% |

Read the *shape*, not the absolute sizes: **the cost drag is inversely proportional to the holding
period**, so the ratio between a 15m hold and a 1D hold is exactly 96× regardless of venue, and
between 1D and 1M exactly 30×. That relationship is the defensible claim and it needs no unstated
figure to state it.

## What the published figure would require to be true

| cost regime | if 24.21 is per-**trade** net → gross edge needed | if per-**year** net → gross needed |
|---|---:|---:|
| equity ETF (2.00bp) | 26.21 bp/trade | 2.07 bp/trade |
| crypto perp cheapest (11.08bp) | 35.29 bp/trade | 11.15 bp/trade |
| crypto spot mid (21.07bp) | 45.28 bp/trade | 21.14 bp/trade |
| crypto spot worst (56.04bp) | 80.25 bp/trade | 56.11 bp/trade |
| our default model (26.00bp) | 50.21 bp/trade | 26.07 bp/trade |

If 24.21 is **per trade net**, it demands a **26–80 bp gross edge on every trade** — on an equity
ETF that is ~9,500 bp/yr gross. If it is **per year net**, the same number is a modest and entirely
plausible 2 bp/trade. **The two readings differ by a factor of 365 and the documents do not say
which one was computed.**

## Does G-COST-3 kill it?

Only partly, and the way it fails is instructive:

| regime | 1D round trip | inside [19, 24.21]? |
|---|---:|---|
| equity ETF (corrected) | 2.00 bp | no → rule fires |
| crypto perp, cheapest venue | 11.08 bp | no → rule fires |
| **crypto spot, mid venue** | **21.07 bp** | **YES → rule does NOT fire** |
| crypto spot, worst venue | 56.04 bp | no → rule fires |
| our default model | 26.00 bp | no → rule fires |

**G-COST-3 fires for 4 of 5 regimes but not for the fifth**, because a 21.07 bp round trip happens to
land inside the 19–24.21 window. The rule is therefore testing the *cost regime*, not the *claim*.
A kill rule whose outcome flips with which venue you happen to measure cannot settle a published
number.

## Verdict

**KILL the `+24.21 bp at 1D` figure as a quoted claim — on reproducibility and unit grounds, not on
the cost test.**

- It is unit-ambiguous by 365× and gross/net ambiguous, and
- it has no implementation in either repo, so it cannot be re-derived by anyone.

**What replaces it,** in every place the old figure appears: the ladder arithmetic above —
`annual cost drag = 365 / holding_days × round_trip_bps`. It is exact, unit-explicit, needs no
venue assumption to state, and it supports the same conclusion the old figure was used for
(work at longer horizons) with a quantity that cannot be misread.

The G2 Horizon gate in `INVESTMENT_DECISION_FRAMEWORK.md` should cite **the 96× ratio between a
15m and a 1D hold**, not a bare bp figure with an unstated basis.

## Follow-ups this exposes

- **G-COST-3 needs rewriting** before it is used again: it must name the instrument, the venue and
  the horizon basis, or it will keep firing on whichever cost happens to be measured.
- The four documents carrying the old figure need a one-line correction. I have not edited them
  here — that is a coordinated edit across two sessions and should not be done unilaterally
  mid-flight.
