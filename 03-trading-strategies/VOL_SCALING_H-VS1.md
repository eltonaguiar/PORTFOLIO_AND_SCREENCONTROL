# H-VS1 — "volatility scaling is free alpha": measured

**The claim.** The audit2/audit3 doctrine states, as one of its load-bearing lines:

> "Volatility scaling is free alpha. Simply scaling positions by inverse realized vol improves
> Sharpe by **0.3+ for any momentum strategy**."

It appears in three places in this repository as a **quotation** and had never been run. One of
the four model answers flagged exactly that:

> "Apply your own evidence machinery to the doctrine's claims too — 'vol scaling is free alpha'
> is itself a testable hypothesis, and it mostly works by reducing exposure, not adding return."
> — GLM 5.3 Flash

**Artifacts:** `results/vol_scaling_test.json` ·
`realtime_challenge/proof/vol_scaling_test.py` · reproduce with
`python -m realtime_challenge.proof.vol_scaling_test`

---

## The test

SPY, 2004–2026 (22.9 years), daily. Four base strategies this repo already uses. Each is run
twice: unscaled, and scaled by `target_vol / realized_vol(20d)` with the scale lagged one day
and clipped to a leverage cap. **Every change in the scale factor is charged turnover at
5 bps per side** — most published vol-scaling results omit that, and it is not free.

Two caps are reported, because the claim's leverage is unstated:

- **cap 1.0** — no leverage. Scaling can only de-risk. This is what a retail account can do.
- **cap 2.0** — up to 2× leverage. This is where "+0.3 for any momentum strategy" is usually measured.

## Result: 0 of 4 strategies reach +0.30, and the two that work get worse

| strategy | base Sharpe | cap 1.0 | **Δ** | cap 2.0 | **Δ** | ann vol |
|---|---:|---:|---:|---:|---:|---|
| SPY buy-and-hold | 0.620 | **0.748** | **+0.128** | 0.695 | +0.075 | 18.6% → 10.2% |
| SPY 12m TSMOM | 0.604 | 0.688 | +0.084 | 0.617 | +0.013 | 13.4% → 9.3% |
| SPY + 200d SMA | **0.719** | 0.690 | **−0.029** | 0.618 | **−0.101** | 11.4% → 9.2% |
| SPY 6m equity-curve momentum | **0.710** | 0.676 | **−0.034** | 0.621 | **−0.089** | 11.5% → 9.1% |

**No-leverage: 0 of 4 reach +0.30. With 2× leverage: 0 of 4.** Momentum specifically: 0 of 2.

## Why it fails, and what it does do

Three mechanisms, in order of importance:

**1. The Sharpe gain is the denominator.** Vol targeting does exactly what it says to
realised vol (18.6% → 10.2% on buy-and-hold). Where Sharpe rises, it rises because volatility
fell — under a no-leverage cap, CAGR usually falls with it. That is risk management, and it is
real and useful, but it is not alpha and it is not a return source.

**2. It helps raw beta and hurts timing strategies.** The best gain (+0.128) is on
**buy-and-hold** — the one strategy with no timing signal at all. The two strategies that
actually add timing value (200-day SMA, equity-curve momentum) both get **worse** (−0.03 to
−0.10). Vol targeting *is itself* a trend-following overlay, so stacking it on a trend
strategy double-counts the same signal and pays turnover twice for it. The claim's "for any
momentum strategy" is precisely backwards: momentum is where it does most harm.

**3. The turnover is real.** Rescaling every day is a trade every day. At 5 bps per side it
costs roughly 1 point of Sharpe on its own; the published versions of this result generally do
not charge it.

## What survives from the doctrine

The useful half of the claim, restated honestly:

> **Vol targeting reliably reduces realised volatility and drawdown. On a no-leverage account
> it is a legitimate way to fit a given risk budget. It is not a source of return, and applied
> on top of a trend or momentum signal it typically reduces Sharpe.**

That is worth keeping — it is exactly the drawdown-control role the capital-allocation
document asks for. It is not worth keeping as "free alpha", because it isn't free and it isn't
alpha.

## Where this lands relative to the other results

This is the first claim in the project that **failed while being true in spirit**. Every prior
negative (126 cells, weekend effect, ETF rotation, random-entry) was a strategy that simply had
no edge. This one has a real, measurable effect — volatility does fall as promised — and the
effect is systematically mislabelled. That distinction matters for the allocation document: vol
targeting belongs in the **risk** section, not the **return** section.

## Reproduce

```bash
cd 03-trading-strategies
python -m realtime_challenge.proof.vol_scaling_test
```

Note the sensitivity worth checking next: the result is on SPY only, at a 10% target and a
20-day window. A 60-day window with a 15% target would raise leverage and could change the
magnitude — but not the sign on the two timing strategies, because the double-count of signal
is structural rather than a parameter choice.
