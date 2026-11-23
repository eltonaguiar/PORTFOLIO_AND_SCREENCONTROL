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

---

## 6. Second table (AskAnyModel, same question) — the citations are the failure

**Provenance first, because it discredits the rest.** In the AskAnyModel run, four panes were selected and **three
were unavailable** (`Nemotron 3.5 Super VL`, `Gemma 4 31B IT`, `Nemotron 3.5 Lightning` — all "This model is
temporarily unavailable"). The single pane that answered is labelled **"Gemma 4 26B A4B IT"** and underneath it
reads **"answered by GPT-OSS 20B Reasoning LLM · Pollinations community"**.

> The model name on the pane is not the model that produced the text. Any comparison built on this screenshot is
> comparing labels, not models. This is the same defect class as the replay-report and the dead COMS pointer:
> the reference resolves, the identity is wrong.

### Citation audit — three of seven are unusable, and two rows are swapped

| Row | Cited | Verdict |
|---|---|---|
| Risk premium | Fama & French (1993), *Common Risk Factors…* | **real paper, wrong role.** It is a cross-sectional factor model; the stated sample `1963–1998` is also wrong (the paper's is 1963–1991). It is not an OOS risk-premia survey |
| **Time-series momentum** | **Jegadeesh & Titman (1993), *Profitability of Momentum Strategies*** | **MISATTRIBUTED** — J&T 1993 is *cross-sectional* momentum. TSMOM is Moskowitz, Ooi & Pedersen (2012) |
| **Cross-sectional momentum** | **"Moskowitz, Rand & White (2012), *Time-Series Momentum in Hedge Funds*"** | **FABRICATED.** No such author set exists and no such paper exists; the real TSMOM paper is Moskowitz, **Ooi & Pedersen**. The title also contradicts the row it is attached to |
| Trend following | **"Gray, Kritzman & Khandani (2011), *Modern Portfolio Theory for Atlas*"** | **FABRICATED TITLE.** Web search returns nothing for it. Real trend literature: Hurst/Ooi/Pedersen, Clare/Seaton/Smith/Thomas (2012), Fung & Hsieh (2001) |
| Mean reversion | "Al-Arouri, Kim & Luan (2017), *Mean-reversion vs Butterfly*" | **zero search results** — unverifiable at best |
| Carry | "Geanakoplos, Johannsen & Welch (2012), *The High-Frequency Carry Trade*" | suspicious title; canonical is Burnside et al. (2011) and Lustig/Pervushin/Verdelhan (2011) |
| Volatility risk premium | "Bollerslev & Todorov (2017), *Volatility Risk Premium*" | authors are real (Bollerslev & Todorov 2011, *Tails, Fears and Risk Premia*); the 2017 title appears invented |

**The structural giveaway:** rows 2 and 3 are **swapped**. J&T (cross-sectional) is labelled time-series, and a
paper titled *Time-Series Momentum in Hedge Funds* is labelled cross-sectional. Two adjacent rows contradict each
other — no one who has read either paper produces that. A reader skimming the table sees seven plausible
author-year pairs and would not notice that two of them are alphabet soup.

### What this table gets right, and why that makes it more dangerous

Its *shape* is correct: seven families, canonical-source column, replication column, sample period, failure mode,
retail implication. It even includes the right rhetorical move — *"OOS evidence means the strategy has performed on
fresh data, not that it will continue forever."* It reads exactly like the good answers.

But its failure modes are generic (*"structural breaks in macro regime"*, *"regime shifts"*, *"coupling dissolve
during crises"*) where the better answers are specific: **"2008 carry-trade collapse"**, **"2014–2019 whipsaw in
choppy regimes"**, **"profit only pre-publication"**. Generic failure modes are the tell — they are what you write
when you do not know the literature.

### Operational rule adopted from this

> **When a table pairs a plausible author with an implausible title, verify the title, not the author.**
> Fabrication hides in the title and the sample window, never in the surname.

And a second: **never treat a pane's model label as provenance.** This run's only answer came from a community
Pollinations endpoint wearing a Gemma badge, which means tonight's "Gemma 4 26B" and "GPT-OSS 20B" are the same
answer, and the comparison the UI implies is fiction.

### Ranking of the three tables we now hold

| Table | Citation integrity | Failure-mode specificity | Usable? |
|---|---|---|---|
| **Grok 4.20** (AskAnyModel) | **high** — Koijen/Moskowitz/Pedersen/Vrugt 2018 for carry, Moskowitz/Ooi/Pedersen 2012 + Hurst/Ooi/Pedersen for trend; correct; names OOS extensions | specific (2008 carry unwind; 2014–2019 whipsaw) | **yes, as a reading list** |
| 1min.ai (first table) | medium — 2 of 7 misattributed | moderate — "decay in some premia post-publication", no magnitude | partially |
| **This table** | **low — 3 of 7 unusable, 2 rows swapped** | generic | **no** |

