# Value vs PEAD — outside evidence, harvested 2026-11-22

Source: duck.ai, model `GPT-6 Luna`, no account, no key, one 450-char prompt, 4,015 chars harvested via
clipboard. Raw: `prototype/transcripts/duckai_pead_raw.txt`.

Question asked (deliberately without our own numbers, to avoid an echo): strongest published evidence for
the value premium and for post-earnings-announcement drift, effect sizes, sample periods, decay
conditions, and — for a 12–20 bp round-trip trader needing to beat a 4.3% T-bill — which to test first
with an explicit kill rule.

## Value premium (HML)

| Item | Reported |
|---|---|
| Effect size | **3–5%/yr ≈ 25–42 bp/month gross**, described as "highly sample-dependent, not a stable monthly payoff" |
| Sample | Standard HML series **1927–2024**; a recent study builds size-adjusted book-to-market portfolios **1977–2023** |
| Decay | HML "lost about half its cumulative value after 2007"; book-to-market **misclassifies firms with substantial intangible assets**, with composite value and operating-cash-flow-to-market offered as alternatives |
| Net of our costs | At 12–20 bp round trip, 25–42 bp/month gross leaves **roughly 5–30 bp/month** before other implementation effects — and that is an arithmetic remainder, not a forecast |

## Post-earnings-announcement drift (PEAD)

| Item | Reported |
|---|---|
| Effect size | Bernard & Thomas: top-minus-bottom standardized-surprise spread positive in **41 of 48 quarters, 1974–1985**; later summary cites **~6% abnormal over 60 days**, with estimates varying widely by sample |
| **Decay — the important one** | **Martineau: PEAD was non-existent for LARGE stocks since 2006**, disappearing only more recently for microcaps |
| Cost sensitivity | One 12-month extreme-portfolio result falls **11.92% → 3.36%** at the highest transaction-cost estimate; a revenue-surprise drift of **6.59% becomes unprofitable after costs** |

## The verdict it gave

Test **value first**; PEAD second, and "the headline 60-day effect is not a reliable net return estimate for
your universe."

The methodological point is worth keeping independently of the ranking: **a market-neutral long–short return
is not comparable to a T-bill yield** unless capital, leverage, collateral and financing are specified. For a
fully funded strategy compare net annualised total return to 4.3%; for a factor strategy compare the return
on **capital actually committed, including cash collateral**.

## Kill rule (pre-registerable as written)

After fixing portfolio, rebalance, universe and cost model **before** looking at the holdout:

> kill if out-of-sample annualised net return **on committed capital** ≤ 4.3%, **or** if the one-sided 95%
> **upper confidence bound** ≤ 4.3% — the optimistic bound then also fails.

Count all turnover costs once; do not double-subtract. Same rule applies to PEAD if it is tested later.

## Cross-model comparison — three sources, one 2× disagreement

Same prompt, no shared numbers, three independent surfaces:

| Source | Value premium | PEAD | Decay claim |
|---|---|---|---|
| **duck.ai / GPT-6 Luna** | 3–5%/yr = **25–42 bp/month** gross; series 1927–2024 | positive in 41/48 quarters 1974–85; ~6% over 60 days | HML lost ~half cumulative value **after 2007**; **Martineau: large-cap PEAD non-existent since 2006** |
| **Router / `ULTRA_FREE_OPENROUTER`** | **0.5–0.7%/month = 50–70 bp/month** gross (top vs bottom quintile); FF 1963–2019+, Asness 1975–2011 international | Ball & Brown 1968; Bernard & Thomas | HML **≈ −0.3%/month 2007–2020**; decay after publication; "net of 15–20 bp/month turnover costs the alpha shrinks to **30–40 bp/month**" |
| **Router / `ULTRA_FREE_CLOUD_LARGE`** | (answer truncated before the value section) | **2.0–3.5%/yr ≈ 20–30 bp/month** SUE1 decile spread; 4–6% over 60 days for extreme SUE; sample **1971–2005 US** | "post-2005 SUE spread compressed" |

**The disagreement is roughly 2×** — 25–42 vs 50–70 bp/month gross for the same factor. Both cannot be right about the same portfolio, and the difference is plausibly the construction: annualised HML return across a very long sample (duck.ai) versus a quintile-spread average per month on a shorter sample (router). That distinction decides whether value clears our 12–20 bp round trip with room to spare or barely at all.

**Where all three agree, and it is the more useful finding:**

1. **PEAD decayed post-2005/2006 and nothing after that is large-cap reliable.** Three independent models, three different citation sets, same conclusion.
2. **Value is the better first test**, and it is a *monthly* strategy — the horizon our own cost ladder says survives (+24.21 bp at 1D vs −0.57 bp at 15m).
3. **Turnover costs are the binding constraint**, not signal strength: the router's own arithmetic takes 50–70 bp/month down to 30–40.

**What this changes in practice:** the magnitude must be **measured on our data, not imported from literature**, because the literature disagrees with itself by a factor of two. The pre-registered kill rule is unchanged and is exactly what resolves it — OOS net return on committed capital ≤ 4.3%, or the one-sided 95% upper bound ≤ 4.3%.

**Citations to verify at source** (none of these has been checked against the paper yet): Fama & French 1992 *J Finance*; Fama & French 2019 *JFE*; Asness, Moskowitz & Pedersen 2013 *J Finance*; Ball & Brown 1968 *JAR*; Bernard & Thomas 1989 *JAR*; Ball & Bartov 1996 *JAE*; Livnat & Mendenhall 2006 *TAR*; Martineau (SSRN).

## What this means for our programme

- **PEAD is the weakest of the two for us.** If the repo's PEAD infrastructure is large-cap and post-2006,
  the expected result is zero, and "PEAD exists in the code" is not evidence that it pays. Copilot is
  currently researching exactly this — the honest deliverable is a *dated, universe-specific* number, and a
  null is the likely outcome rather than a failure.
- **Value is the better first test**, and it is testable with monthly rebalancing, which is the one horizon
  our own cost ladder says can survive (+24.21 bp at 1D vs −0.57 bp at 15m).
- The killer arithmetic is unchanged: 25–42 bp/month gross against a 12–20 bp round trip leaves a thin
  margin, and any long-short construction adds financing and short-borrow that we have not measured.

## Cross-check against our own state

All seven classes are REFUTED here, `mega_rotation` is QUARANTINE, 0 proven, 0 forward observations, zero
capital. This harvest does not change that — it names the two families that were never measured rather than
the two that were measured and failed. Evidence class: **external claim, not verified against primary
papers**; the Martineau result in particular should be confirmed at source before it is used to kill a
research line.

---

# 2026-11-23 UPDATE — Arena A/B round, and it reverses the "value first" call above

A later Arena comparison (Assistant A vs Assistant B, same value-premium/PEAD question with a **12–20 bp round-trip
cost** and a **4.3% T-bill hurdle**) produced a materially better answer. Both of its recent citations were verified
against primary sources, and its arithmetic checks. **It changes which family we test first.**

> **Vote-row note:** the A/B "A is better / Both are good / Both are bad / B is better" control at the bottom of that
> page writes to the operator's account and hides identities until voted. It was not clicked, per standing rule.

## 1. Citation verification — both recent sources are real, with matching magnitudes

| Cited | Verified | Magnitude match |
|---|---|---|
| **Meursault, Liang, Routledge & Scanlon (2023), "PEAD.txt: Post-Earnings-Announcement Drift Using Text", JFQA 58(6) 2299–2326** | ✅ real, exact volume/pages | ✅ the paper's own abstract states PEAD.txt vs classic PEAD of **2.87%–1.54%**, exactly as quoted |
| **"Is the Value Premium Dead? Forecasting Value–Growth Cycles with the Implied Value Premium" (JFQA)** | ✅ real | ✅ HML **+5.20%/yr Jul 1926–Dec 2007 vs −0.86%/yr Jan 2008–Mar 2025**; value beat growth **55% → 43%** of months, verbatim match |

That is the first answer in this programme whose 2023/2026 citations survived checking **and** whose numbers matched
the abstracts to the decimal. Contrast with the AskAnyModel table, where 3 of 7 were invented.

## 2. Arithmetic re-derived

| Claim | Recompute | Verdict |
|---|---|---|
| 4.3% annual = 35.8 bp/month | 4.3/12 = 0.358% | ✅ |
| 63-day hurdle `(1.043)^(63/252) − 1` = 1.058% | `exp(0.25·ln1.043) − 1 = 1.0584%` | ✅ |
| Bernard–Thomas 4.2% over 60 trading days ≈ 147 bp/month | 4.2 × 21/60 = 1.47% | ✅ |
| PEAD.txt 2.87% over 63 days ≈ 96 bp/month | 2.87 × 21/63 = 0.957% | ✅ |
| Classic SUE in same design 1.54% over 63 days ≈ 51 bp/month | 1.54 × 21/63 = 0.513% | ✅ |

## 3. The evidence that decides it

**Value (HML), modern:** 49 → 10 bp/month all-cap from 1963–91 to 1991–2019; **big-stock 42 → 4 bp/month**; the
largest-cap decile spread was only **25 bp/month** even in the 1992 discovery sample; HML alpha after profitability
and investment controls is **−4 bp/month (t = −0.47)**; and post-2007 HML is **−0.86%/yr = −7 bp/month**. Our own
measurement (+0.11%/yr gross on 186 names) sits inside that consensus rather than contradicting it.

**PEAD, classic:** Bernard–Thomas 147 bp/month in 1974–86 but **size-dependent (large caps 98 bp)**; Chordia et al.
value-weighted spread in the most liquid stocks **4 bp/month** with costs eating 70–100% of the paper profit;
**Martineau (2022): non-microcap PEAD is −32 / 0 / −64 bp/month in 2006–10 / 2011–15 / 2016–19** — negative in the
last window. This confirms, from primary sources, what we had recorded as an unverified external claim.

**PEAD, text-conditioned:** **96 bp/month gross over 63 days, 2010–2019, and it survives in years when classic PEAD
is ≈0.** That is the only modern published PEAD magnitude that clears a 35.8 bp/month cash hurdle before costs.

## 4. What this changes — and the honest caveat

**Text-conditioned PEAD is the first candidate in this programme with a published modern magnitude above our
hurdle.** But three caveats travel with it, and they are load-bearing:

1. **The portfolios are equal-weighted.** EW in a 5-quintile long-short over ~thousands of names is not implementable
   at our ticket size without massive per-name costs; value-weighting will shrink the 96 bp substantially.
2. **It is not transaction-cost-net.** The authors report gross. Our 12–20 bp round trip, doubled for a long-short
   (two legs), plus borrow, is the first subtraction the published number has never faced.
3. **It needs data we do not have: earnings-call transcripts**, plus a rolling eight-quarter text model. This is a
   **procurement task, not a coding task** — the same wall that stopped PEAD at `BLOCKED_MISSING_DATA` and value at
   "no point-in-time fundamentals store."

## 5. Pre-registered kill rule adopted from this round

> Universe: above the NYSE 20th-percentile market-cap cut (non-microcap).
> Holdout: **2020Q1–2025Q4, untouched**.
> Signal: published rolling eight-quarter text model (SUE.txt), top quintile long / bottom short.
> Entry: first close after the call. Hold: **63 trading days**.
> Costs: actual slippage + commissions + fees + borrow deducted.
> Inference: overlapping-cohort returns with **63-lag HAC** standard error.
> **Kill if the one-sided 95% upper bound on net 63-day return ≤ 1.058%** (equivalently ≤ 35.15 bp/month).
> Breakeven gross before borrow is 1.298%–1.458% per 63-day cohort at 12–20 bp per leg.

This is now the *second* pre-registered item in the programme that can actually kill something on our own data — the
first being the ETF 12-month absolute-momentum test. Both are years from a verdict; both have a frozen threshold.

## 6. Revision to the line above

The earlier conclusion — *"Value is the better first test"* — was based on value being untested and PEAD being dead
in large caps. Both remained true, but neither made value the better *first* test: value's modern expectancy
(**−7 bp/month** post-2007) cannot clear a 35.8 bp/month hurdle **before** costs, while text-conditioned PEAD's
96 bp can. **Value drops from "the live line" to "measured and insufficient"; text-conditioned PEAD takes its place
as the only family whose published modern magnitude justifies an implementation test** — conditional on acquiring
transcripts.

