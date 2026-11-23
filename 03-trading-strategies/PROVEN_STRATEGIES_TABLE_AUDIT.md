# 1min.ai "proven strategies" table — claim and citation audit

**Source:** 1min.ai multi-model answer, captured 2026-11-23 02:00 local by the operator.
**Shape of the answer:** a seven-row table of strategy families, each with a canonical source, asset classes, sample
period, and caveats, plus a short section on what "proven" can and cannot mean.
**Verdict: useful as a reading list, unusable as evidence.** Zero rows carry a sample size, a trial count, a deflated
statistic, or a measured cost. The column header says "Proven" while the caveat section admits it means
*"historically delivered statistically significant positive returns"* — different claims, and only the second is true.

---

## 1. Citation audit

Checked against the actual papers. Two are wrong in a way that would waste a researcher's afternoon.

| Row | Cited source | Status |
|---|---|---|
| Risk premia | Asness, Moskowitz, Pedersen (2013), *Value and Momentum Everywhere* | **correct** — JF/Account (2013). Caution: the paper's own value+momentum result is a long–short factor; it tells you nothing about a retail-accessible implementation |
| Time-series momentum | Moskowitz, Ooi, Pedersen (2012), *Time Series Momentum* | **correct** — JFE 104(2). This is the family our ETF trend line belongs to |
| Cross-sectional momentum | Jegadeesh & Titman (1993); Asness et al. (2013) | **correct** |
| Trend following | *"Fama and French (1988) (early), later refined by Gray & Vogel (2016)"* | **MISATTRIBUTED (both).** Fama–French (1988) is *Dividend Yields and Expected Stock Returns*; Gray & Vogel (2016) is *Analyzing Valuation Measures: A Performance Horse Race over the Past 40 Years* — a **valuation** paper, not trend. The real trend-following literature is Hurst/Ooi/Pedersen and the AQR *A Century of Evidence on Trend-Following* strand |
| Mean reversion | Poterba & Summers (1988); Campbell & Hentschel (1992) | **half wrong.** Poterba–Summers (1988) is correct on mean reversion. Campbell & Hentschel (1992) is *No News is Good News: An Asymmetric Model of Changing Volatility* — an asymmetric-volatility paper, not a mean-reversion result |
| Carry | Burnside, Eichenbaum, Kleshchelski, Rebelo (2011) | **correct** — *Do Peso Problems Explain the Returns to the Carry Trade?* Also the source that documents carry's crash risk, which the row understates |
| Volatility risk premium | Ang, Liu, Schwarz (2014) | **MISATTRIBUTED.** Their paper is *Using Stocks or Portfolios in Tests of Factor Models* (JFQA). Canonical VRP sources are Carr & Wu (2009) and Bollerslev, Tauchen & Zhou (2009) |

Two of seven rows cite a real paper for the wrong phenomenon. That is the same failure mode as a dead COMS
pointer — a citation that resolves but does not support the claim.

## 2. Our own measurements against the same seven families

This is the part the table cannot supply, and it reverses most of its retail guidance.

| Family | 1min.ai framing | Our measured result |
|---|---|---|
| Risk premia (value) | "proven… stable average returns" | **HML +0.11%/yr gross, +0.02% net** on 186 names, 44 monthly rebalances — the premium is *absent* in our sample, not merely cost-eaten |
| Time-series momentum | "proven out-of-sample on many asset classes" | Only live line we have; the ETF 12-month absolute momentum test is **forward-only and years from a verdict**. SPY-200d specifically: null 53.4, excess **−6.8 pp** → NOT_INVESTABLE |
| Cross-sectional momentum | "works well over long periods; high trading costs" | 6 classes × 15 configs = **N=90**; DSR collapses **0.9543 → 0.3191**; **0 of 6 classes survive** |
| Trend following | "strong long-term edge" | ETF wrapper cost 6.7122 bp RT is the one thing that passes — a **cost** fact, not an alpha fact |
| Mean reversion | "evidence strongest in short-term horizons" | FOREX mean-rev break-even **4.3038 bp < measured 7.533 bp cost**; crypto intraday mean-rev PF 0.815 after costs — dead |
| Carry | "good sharpe ratios historically" | FX carry Sharpe **−0.126**, break-even 468 bp ≈ 62× measured cost; crypto funding carry **−11 bp/tick** on 63 ticks; funding-basis only 2.89% of 2,838 episodes reach break-even |
| Volatility risk premium | "usually positive long term" | **never measured** — no options chain history in the estate. Options are 1 line in the 12-class plan with `UNMEASURED` against every gate |

Six of seven families are measured on our data and six fail. The seventh (VRP) is untested because we have no data,
which is a different statement from "works".

## 3. The structural error

The answer treats *documented out-of-sample performance in an academic sample* as transferable to a retail account.
Its own caveats say otherwise — *"Many academic proofs assume institutional-level trading costs, leverage, low
slippage, and scalability which retail traders may not access"* — but the table's column header still says "Proven",
and nine words later the same document defines proven as merely "statistically significant… after adjusting for
risk". Risk-adjusted is not cost-adjusted.

What the table never supplies, and what our gates require: **n**, trial count, deflated Sharpe, PBO, walk-forward
efficiency, information ratio against a matched benchmark, break-even cost multiple, capacity, tail ratio, and the
date each sample ends. Post-publication decay is mentioned once in a caveat ("Decay in some premia post-publication")
with no magnitude — and our HML measurement (+0.11%/yr gross) suggests the decay is total, not partial.

## 4. What is worth keeping

1. **The reading list**, minus the two misattributions. Moskowitz/Ooi/Pedersen (2012) and Burnside et al. (2011) are
   the two that matter for the families we actually test.
2. **"Proven cannot mean profitability after all fees, slippage and taxes for small retail accounts."** Written by the
   model, true, and exactly what our own numbers show.
3. **Crash risk in carry** — it names it and our FX carry measurement quantifies it (Sharpe −0.126).

## 5. Process note

Neither of these two harvests (this and `VALIDATION_METHODOLOGY_PANEL.md`) changed a decision. That is the correct
outcome for literature: it supplies *gate definitions* and *citations*, not evidence. Evidence has to be measured on
our own bars, at our own ticket size, with the trial count declared — which is why the ranked list stays empty and
why the panel's own power table puts any verdict 6+ years away.

**Status:** citation checks performed by web search on 2026-11-23 (Gray & Vogel 2016 → valuation paper;
Ang/Liu/Schwarz → factor-model testing paper). Measured numbers in §2 are `observed` in the repos named in
`VALIDATION_METHODOLOGY_PANEL.md` §3.
