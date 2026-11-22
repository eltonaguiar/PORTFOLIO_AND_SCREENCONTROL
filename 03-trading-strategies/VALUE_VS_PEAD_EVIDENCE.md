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
