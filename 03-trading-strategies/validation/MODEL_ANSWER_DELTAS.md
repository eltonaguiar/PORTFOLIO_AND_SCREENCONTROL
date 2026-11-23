# Model answers vs protocol v1.0 — deltas, looseness and errors

**Purpose.** Five model answers to the same "prove a strategy works" question now exist in this programme
(chatplayground: Luna, Claude, GLM; 1min.ai: two answers, call them **1A** and **1B**). The adopted standard is
`strategy_validation_protocol.md` v1.0 (§3.11's 17-gate sheet). This file records, per answer, which thresholds are
**looser** than v1.0 (do not adopt), which are **stricter** (safe), and which contain **factual or arithmetic errors**.

Rule applied: a model answer may add a *test*, but it may never move a gate downwards. A looser threshold adopted
"because a model said so" is exactly the multiple-testing debt this programme is trying to escape.

---

## 1. Threshold comparison

| Gate | v1.0 | Luna | Claude | GLM | **1A** | **1B** | Verdict on the models |
|---|---|---|---|---|---|---|---|
| DSR | ≥ 0.95 | ≥ 0.95 | ≥ 0.95 | ≥ 0.95 | ≥ 0.95 | **> 0.80** | **1B looser — reject** |
| PBO | ≤ 0.10 | ≤ 0.10 | < 0.25 | < 0.25 | < 0.25 (ideally .15) | < 0.10 | Luna/1B equal; Claude/GLM/1A **looser** |
| WFE | ≥ 0.60 | ≥ 0.50 | 0.5–1.0 | ≥ 0.50 | > 0.50 | > 0.60 | v1.0 stricter than all but 1B |
| Alpha t | 3.0 / 3.5 / 4.0 by N_eff | ≥ 3.0 | ≥ 3.0 / ≥ 2.0 | ≥ 3.5 / 3.0 / 2.0 | > 2.0 (ideally 3.0) | not specified | **1A looser at the low end** |
| IR | ≥ 0.50 | ≥ 0.50 | ≥ 0.50 | not specified | > 0.50 / .75 | **> 0.30 minimum** | **1B looser — reject** |
| 2× cost | net ≥ 50% of 1× net | positive | ≥0.5× base | not specified | **net SR > 0.75** | **SR > 0.30** | 1A strict but absolute (scale-dependent); **1B looser** |
| Break-even multiple | ≥ 4× | not specified | ≥ 2.5× | not specified | not specified | not specified | v1.0 alone |
| Capacity | ≥ 5× intended AUM | ≥ 2× | ≥ 3× | not specified | ≥ 5× | > target AUM | 1A equal; others looser |
| Tail ratio | ≥1.0 **+ skew >−0.5 + best-month ≤25%** | ≥ 1.0 | ≥ 1.0 | not specified | ≥ 1.0 | **"≥2 good, <1.5 risky"** | 1B uses a different scale entirely |

**Net:** Luna is the closest to v1.0 and adds nothing conflicting. Claude and GLM relax PBO to 0.25. **1A is broadly
sound but softens alpha t and omits break-even.** **1B relaxes DSR, IR, 2× cost and capacity, and should not be
used for gating in any form.**

## 2. Errors worth naming

| Answer | Error | Why it matters |
|---|---|---|
| **1B** | "Require minimum sample length (e.g., **3 years** or 36 months out-of-sample)" alongside "80% power for SR=0.5" | Internally inconsistent. SR 0.5 needs **24.7 years** at 80% power; even SR 1.0 needs **6.2 years**. A 3-year OOS test cannot distinguish an SR of 1.0 from zero |
| **1B** | *"from Bailey, Ledoit (2012)"* for the Deflated Sharpe Ratio | **Misattributed** — DSR is Bailey & **López de Prado** (2014); Ledoit is a different author (shrinkage estimators). Same class of defect as the earlier Gray & Vogel and Ang/Liu/Schwarz errors |
| **1A** | "2× cost stress: net Sharpe remains **> 0.75**" | Absolute rather than relative. A strategy with 1× net Sharpe 0.8 that keeps 0.77 at 2× costs passes while barely decaying; a strategy at 1.6 that drops to 0.9 fails. v1.0's relative form (≥50% of 1× net, and > 0) is the correct construction |
| **1B** | Tail ratio "< 1.5 may indicate undesirable tail risk" | P95/\|P5\| of a symmetric distribution is ≈1.0, so 1.5 is *already* right-skewed — the scale is shifted and would fail almost every symmetric strategy |

*Arithmetic check on 1A's power formula `T ≈ 6.18/SR²`:* (1.645 + 0.842)² = **6.185**, giving SR 1.0 → 6.2 y and
SR 3.0 → 0.69 y (8.2 months). **The arithmetic is correct** — it is 1B's *conclusion* that ignores it.

## 3. Genuinely additive items (adopt these)

1. **Parameter-cliff falsifier (1A):** perturbing any key parameter by **±15%** that drops Sharpe by **> 35%** is a
   kill. v1.0 has a stability gate (SR CV ≤ 0.30 over ±20%) but does not state the cliff as a *falsifier*; both are
   useful, and 1A's version is easier to say out loud.
2. **Factor-subsumption falsifier (1A):** if regressing live/OOS returns on FF+Momentum gives **alpha t < 1.5**, the
   strategy is "an expensive, concentrated factor ETF". v1.0 tests alpha t ≥ 3.0 against FF6+industry as a *gate*;
   1A's version is a cheaper first pass and worth running before the full gate.
3. **Concentration falsifier (1A):** cumulative return goes negative when the **top 5% of days** are removed. v1.0
   has best-month ≤ 25%; the top-5%-of-days test catches a different failure (a handful of lucky days) and costs
   nothing to compute.
4. **Participation cap expressed as 1% of ADDV (1A)** — v1.0 uses 1–5% of ADV. For a retail account both are
   non-binding, but ADDV is the better denominator once we ever size up.

## 4. What no model answer got right

Every one of the five treats the ERP claim as settled background ("4–6%/yr, single strongest documented premium") and
none asks the question that decides the whole exercise: **is the premium obtainable at our cost and horizon?** v1.0
asks it in Gate 10/11 (2× cost and break-even multiple); the models treat cost as a robustness test applied *after* a
candidate looks good, rather than as the first filter. That ordering difference is why four of five model answers
would have let us keep testing families that our own measurements already killed.

## 5. Standing instruction

Gate with **v1.0 §3.11 only**. Use model answers for (a) falsifier ideas, (b) prose that explains a gate to a human,
and (c) a lower bound on what other people accept — never as a threshold source. Where a model is looser than v1.0,
the model is wrong by construction.

**Status:** thresholds quoted from the answers as supplied; v1.0 values read from §3.11 of
`validation/strategy_validation_protocol.md`; the 1B arithmetic and citation errors verified by inspection
(6.185 → 6.2 y for SR 1.0).
