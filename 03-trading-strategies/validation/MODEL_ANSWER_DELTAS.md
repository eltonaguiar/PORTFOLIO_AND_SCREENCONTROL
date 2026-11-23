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
used for gating in any form.** **1C is unusable — see §2b: it treats DSR as a ratio rather than a probability and
sets a pass mark of 1.5, which cannot occur.**

## 2. Errors worth naming

| Answer | Error | Why it matters |
|---|---|---|
| **1B** | "Require minimum sample length (e.g., **3 years** or 36 months out-of-sample)" alongside "80% power for SR=0.5" | Internally inconsistent. SR 0.5 needs **24.7 years** at 80% power; even SR 1.0 needs **6.2 years**. A 3-year OOS test cannot distinguish an SR of 1.0 from zero |
| **1B** | *"from Bailey, Ledoit (2012)"* for the Deflated Sharpe Ratio | **Misattributed** — DSR is Bailey & **López de Prado** (2014); Ledoit is a different author (shrinkage estimators). Same class of defect as the earlier Gray & Vogel and Ang/Liu/Schwarz errors |
| **1A** | "2× cost stress: net Sharpe remains **> 0.75**" | Absolute rather than relative. A strategy with 1× net Sharpe 0.8 that keeps 0.77 at 2× costs passes while barely decaying; a strategy at 1.6 that drops to 0.9 fails. v1.0's relative form (≥50% of 1× net, and > 0) is the correct construction |
| **1B** | Tail ratio "< 1.5 may indicate undesirable tail risk" | P95/\|P5\| of a symmetric distribution is ≈1.0, so 1.5 is *already* right-skewed — the scale is shifted and would fail almost every symmetric strategy |

*Arithmetic check on 1A's power formula `T ≈ 6.18/SR²`:* (1.645 + 0.842)² = **6.185**, giving SR 1.0 → 6.2 y and
SR 3.0 → 0.69 y (8.2 months). **The arithmetic is correct** — it is 1B's *conclusion* that ignores it.

## 2b. 1C — unusable for gating, and instructive for why

The third 1min.ai answer is the clearest example in this programme of *fluent, confident, structurally impossible*.
It is not "a bit loose"; four of its gates cannot be computed as stated.

| 1C claim | Why it fails |
|---|---|
| **"Deflated Sharpe (DSR): > 1.5 (minimum)"**, and later **"falsified if DSR < 1.5"** | **Impossible.** DSR is a probability in [0,1] — it is PSR evaluated at SR0. A DSR of 1.5 has no meaning, and every real strategy would be rejected by this gate. A process that cannot pass is not conservative; it is broken |
| **"PBO < 0.5 (50% chance of overfitting)"** as a pass | 0.5 is the point where selection is **no better than a coin flip** — v1.0 rejects anything > 0.25 and passes ≤ 0.10. 1C makes the coin flip the pass mark |
| **"CSCV (Bergomi, 2016)"** | **Misattributed.** CSCV/PBO is Bailey, Borwein, López de Prado & Zhu (2014/2017). Bergomi is a stochastic-volatility author |
| **"Independent R² (IR)" = Strategy Alpha / Residual Volatility** | Conflates R² with Information Ratio, and the formula is neither. IR is mean active return / tracking error |
| **"Tail ratio > 1.5 (fat tails)"** | P95/\|P5\| > 1.5 means **right-skew**, not fat tails. Fat tails show up as kurtosis and expected shortfall |
| **"Trial accounting: run a pilot backtest on a small subset to estimate effect size"** | This is *peeking*, and it contradicts its own pre-registration rule. A pilot on data you later reuse is a trial, not a free sample |
| **"Minimum 50 trades (for statistical power)"** alongside **"12 months minimum"** and **"10 years OOS"** | Three mutually inconsistent sample-size rules in one answer. 50 trades cannot power any Sharpe claim |
| **"Capacity > $100M (for retail)"** | Not a retail number, and the definition ("max AUM where slippage > 50bps/yr") is garbled — capacity is where net alpha falls to the hurdle, not where slippage crosses an arbitrary level |
| **"50 bps round-trip for US equities"** | ~7× our measured ETF cost (6.71 bp) and ~4× direct equity (12.07 bp). Conservative direction, but as a *hard-coded* cost it kills everything and prevents the cost comparison that decides the answer |
| **"Exclude only those dead *before* the backtest"** (survivorship row) | Inverted. The rule is to **include** names that died *during* the window with their delisting returns |

**What 1C is still good for:** its ERP framing (Dimson, Marsh & Staunton 2023, ~5–6% real, survives survivorship
and cross-market replication) is the best-argued of the five, and it is the only answer that names a *data source
family* for each bias control. Keep those two paragraphs; discard every threshold.

**The generalisable lesson:** a model that mislabels a probability as a ratio will also mislabel a crash as a
robustness pass. When an answer contains one impossible quantity, the rest of its numbers deserve re-derivation, not
spot-checking — and no gate from that answer should be adopted, even the ones that happen to be right.

## 2c. 1D — the strongest of the six, and the only one whose worked example reproduces

> **Correction found on re-read (this answer was submitted twice).** 1D states *"about 45 independent trials on 5
> years of data are expected to produce a Sharpe of 1.0 from pure noise"* **and**, in the same paragraph,
> *"a conservative bound on the minimum backtest length is 2·ln(N)/SR² years."* The two disagree. Recomputed with
> `E[max SR] ≈ √(2 ln N / Y)`:
>
> | N | E[max SR] over 5 y | MinBTL at SR 1.0 |
> |---|---|---|
> | 12 | 0.997 | 4.97 y |
> | 20 | 1.095 | 5.99 y |
> | **45** | **1.234** | **7.61 y** |
> | 100 | 1.357 | 9.21 y |
>
> So 45 trials over 5 years produce an expected **max Sharpe of ~1.23**, not 1.0; a 1.0 from noise on 5 years needs
> only **~12 trials**; and 45 trials need **7.6 years** to be beaten at Sharpe 1.0 — which is exactly what its own
> `2·ln(N)` formula says. **Its rule is right; its example misapplies it by 1.5×.** Directionally the paragraph is
> correct (more trials, less data → higher noise Sharpe), and the operational message — *fewer trials, stronger
> prior* — is unaffected. But a document that states a formula and then violates it three words later is precisely
> the failure mode we file these audits for: quote the rule, not the illustration.

The fourth 1min.ai answer is materially better than the others: it states formulas rather than names them, and its
arithmetic holds. Verified here:

> *"with 100 trials whose Sharpes have a standard deviation of 0.5, SR\* ≈ 1.27"*
> `SR* = √0.25 · [(1−0.5772)·Φ⁻¹(0.99) + 0.5772·Φ⁻¹(1−1/271.8)]`
> `= 0.5 · [0.4228·2.3263 + 0.5772·2.6808] = 0.5 · 2.5306 = **1.2653**` → **1.27 ✓** to three decimals.

Its conclusion from that example is correct and is the single most useful sentence any of the six wrote:
*"A backtest Sharpe of 1.2 is then worse than expected from luck."*

### Where 1D is still looser than v1.0 (do not adopt these three)

| Gate | 1D | v1.0 | Note |
|---|---|---|---|
| Walk-forward | > 50% | **≥ 0.60** | 1D's grey zone 30–50% is also wider |
| Break-even cost | ≥ 3× | **≥ 4×** | 1D moves the right direction from 1B/1C but stops short |
| Factor alpha t | > 2 (3 if mined) | **3.0 / 3.5 / 4.0 by N_eff** | 1D is right that "if mined" needs more; v1.0 scales it automatically |

### Six items from 1D worth adopting outright

1. **Paper-vs-replay correlation ≥ 0.95** as the implementation-fidelity gate — replay the backtest over the exact
   paper window and correlate daily returns. This is a *computable* pass criterion where v1.0 has a prose contract,
   and < 0.90 is a halt-and-find-the-bug trigger rather than a judgement call.
2. **Count independent bets, not trades.** *"50 positions opened the same day are closer to one bet."* Cluster by
   day or week before any power calculation. This is the operational version of N_eff and no other answer has it.
3. **Vault Sharpe ≥ 50% of discovery Sharpe retained** as a first-class gate, separate from out-of-market replication.
4. **MinBTL ≈ 2·ln(N)/SR²** as a cheap pre-test lower bound (≈ 7.6 y at N=45, SR=1) — a five-second sanity check
   before a single backtest is run.
5. **O'Brien-Fleming boundaries spelled out for 4 scheduled looks: z > 4.05, 2.86, 2.34, 2.02.** Concrete enough to
   code; v1.0 specifies the method but not the numbers.
6. **"A net Sharpe above 3 on daily bars almost always indicates a bug."** A tripwire, not a gate — and correct.

### Also correct and worth quoting

`McLean & Pontiff 2016`: **−26% out-of-sample, −58% post-publication** · `Harvey, Liu & Zhu 2016` t > 3.0 for
published anomalies · the Harvey & Liu **50% haircut** for live sizing · *"if you then modify the strategy, the vault
is burned and you need new data."*

**Verdict: 1D is the closest of the six to v1.0 and the only one whose quantitative example survives re-derivation.
Use it for operational prose and the six items above; gate with v1.0.**

## 2d. Scoreboard across all six answers

| Answer | Closest to v1.0 | Governing error | Safe to gate with? |
|---|---|---|---|
| **1D** (1min) | **yes** | three gates looser (WFE, break-even, alpha t) | no — adopt prose + 6 items |
| **Luna** | yes | none found; under-specifies operations | no — use v1.0 |
| **Claude** | close | PBO relaxed to 0.25 | no |
| **GLM** | close | PBO relaxed to 0.25, alpha t tiered low | no |
| **1A** (1min) | moderate | alpha t 2.0, absolute 2× cost gate, no break-even | no |
| **1B** (1min) | poor | DSR 0.80, IR 0.30, 3-year OOS vs its own power claim | **no** |
| **1C** (1min) | none | DSR gated at 1.5 — impossible | **no** |

**Six answers, six different threshold sets, and not one of them matches another.** That variance is itself the
finding: model consensus on a numeric gate is worth nothing, which is why a written protocol with a fixed gate sheet
and a ledger is the only thing that can be audited after the fact.

## 2e. 1E — the best of the seven, and it corrects our own adopted number

The fifth 1min.ai answer is the only one that behaves like a working document rather than a summary: 18 gates, 8
leakage tests, 18 falsifiers, a documented execution ladder, and **arithmetic that survives re-computation**.

### Its DSR worked example reproduces

Inputs: `T=5040`, annualised SR 1.2 → `ŜR = 1.2/√252 = 0.0756`; skew −0.5; kurtosis 8; cross-trial SD 0.3
annualised → `√V = 0.3/√252 = 0.01890`; `N = 200`.

| Quantity | 1E claims | Recomputed here |
|---|---|---|
| `Z⁻¹(0.995)`, `Z⁻¹(1−1/(200e))` | 2.576, 2.905 | **2.5758, 2.9045** |
| `SR₀` | 0.0523 | **0.05226** |
| Denominator | 1.0236 | **1.02362** |
| DSR | **0.947** | **0.9472** |

Its interpretation is right and is the reason to trust the rest: *"a 1.2 Sharpe over 20 years, after 200 trials, is
borderline (0.947 < 0.95) … The trial count is worth more than the Sharpe."*
**One sub-case is slightly off:** for `N=20` it uses a z-sum of 2.20, but `0.4228·1.6449 + 0.5772·2.0881 = 1.901`
→ `SR₀ = 0.0359`, `DSR = 0.997` (it says 0.995). Both pass, so the conclusion is unaffected; the constant is simply
mis-multiplied.

### It corrects OUR figure: 9.3 years, not 6.2

1E applies the variance of the Sharpe estimator, `Var(ŜR) ≈ (1 + SR²/2)/Y`, giving
`Y = 6.185·(1 + SR²/2)/SR²`. Recomputed:

| True net Sharpe | Crude `6.18/SR²` (what we had adopted) | Variance-corrected (1E) |
|---|---|---|
| 0.5 | 24.74 y | **27.83 y** |
| 0.75 | 11.00 y | **14.09 y** |
| **1.0** | **6.18 y** | **9.28 y** |
| 1.5 | 2.75 y | **5.84 y** |
| 2.0 | 1.55 y | **4.64 y** |
| 3.0 | 0.69 y | **3.78 y** |

**This supersedes the 6.2-year figure** quoted in `VALIDATION_METHODOLOGY_PANEL.md`, in the protocol's own toolkit
output, and in every agent report that repeated it. The crude formula ignores the `SR²/2` term in the variance of
a Sharpe estimate, which is not negligible at the Sharpes we care about. Corrected consequence: **a Sharpe-1.0
strategy needs ~9.3 years of forward evidence, and a Sharpe-0.5 strategy needs ~28 years** — the ETF trend test's
verdict is further out than we said, not closer.

`MinBTL = 2·ln(N)/SR²` also reproduces exactly (N=10 → 4.6 y, N=100 → 9.2 y, N=1 000 → 13.8 y, N=10 000 → 18.4 y at
SR 1.0; and 18.4 / 36.8 / 55.3 / 73.7 y at SR 0.5).

### Five items from 1E worth adopting outright

1. **The canary test.** Deliberately inject *tomorrow's* return as a feature; Sharpe must explode (> 5). *"If it
   doesn't, your pipeline isn't reading features correctly and your 'good' result is also meaningless."* No other
   answer proposes a positive control — every other leakage test checks for a signal that shouldn't exist, this one
   checks the harness can see a signal that must.
2. **Per-trade power: `t = SR_per_trade·√N_trades`.** With per-trade Sharpe 0.05 you need **3,600 trades** for t = 3;
   at 0.10, 900; at 0.20, 225. This reframes the forward test as a *trade count* problem, which is measurable
   weekly, instead of a calendar-time problem, which is not.
3. **After-tax Sharpe as a secondary gate.** *"A strategy with 200% annual turnover in a taxable account can lose
   30–50% of its net compounding to tax."* v1.0 has no tax line at all; for a Canadian retail account this is not
   optional.
4. **Size on 1.5× the backtest max drawdown**, because realised drawdowns exceed backtest drawdowns by roughly that
   factor.
5. **Stationary bootstrap (Politis–Romano, mean block 10–20 days)** for Sharpe confidence intervals rather than the
   iid bootstrap — the toolkit's default block bootstrap is close, but the stationary version is the right one for
   autocorrelated daily returns.

### Its two strongest falsifiers (new to us)

- **"Deliberately shuffled signals still produce positive P&L → your P&L engine is broken; all results are void."**
  That distinguishes *no edge* from *no accounting*, which is the difference between a null result and a bug.
- **"Short leg contributes > 70% of alpha but those names were hard-to-borrow → the trade was never available."**

### Where it is still looser than v1.0

`PBO ≤ 0.25` hard (v1.0 ≤ 0.10) · `WFE ≥ 0.5` (v1.0 ≥ 0.60) · break-even `≥ 2.0` soft (v1.0 ≥ 4×) · tail ratio
`≥ 0.8` soft (v1.0 ≥ 1.0) · raw net Sharpe `≥ 0.7` as a hard gate (v1.0 gates the statistics, not the raw Sharpe).
Capacity `≥ 10×` is *stricter* than v1.0's 5×.

### The one argument in any answer that is strategically useful to us

> *"Retail advantage: your capacity constraint is usually irrelevant ($50k–$500k), which means micro-cap and
> low-liquidity edges are genuinely available to you and unavailable to funds. **That is your only structural
> edge** — but it comes with the widest spreads and worst data. Price it honestly."*

That is the first time any of the seven named where a retail account's edge actually comes from, and it is testable
against our own numbers: our measured micro-cap-adjacent costs (MEME 13.59 bp, small-cap 60 bp round trip in v1.0's
table) mean the "only structural edge" is also the one our gate sheet rejects first. Worth holding as a hypothesis,
not a conclusion.

## 2f. 1F — Claude 5.5 Haiku (1min.ai): strong and comprehensive, two arithmetic defects

The most *complete* answer of the seven — 17 numbered falsifiers, a decision table, MinTRL, permutation tests, and an
explicit rejected-trade log. Four things it contributes that none of the others had:

1. **"Parsimony: each parameter typically adds about one to two effective trials."** A usable heuristic for
   estimating N_eff *before* you have the trial matrix — the cheapest possible defence against the debt.
2. **"Record all rejected trades: count orders that could not be filled."** Nobody else asks for the *unfilled*
   orders, and they are the difference between a simulated portfolio and a portfolio.
3. **A neighbourhood rule stated operably:** *"an edge that exists only at lookback = 37 and disappears at 36 or 38
   is an artifact."* Concrete enough to implement as a test.
4. **Hypothesis budget framed as capital:** *"each hypothesis tested on the same data consumes statistical capital."*

### Verified

Its DSR worked example reproduces exactly:

> `N=100`, variance of per-period trial Sharpes `0.0004` (sd `0.02`), `(1−γ)Φ⁻¹(0.99) = 0.4228 × 2.326 = 0.983`,
> `γΦ⁻¹(1−1/(100e)) = 0.5772 × 2.6808 = 1.547`, `SR₀ = 0.02 × 2.530 = **0.0506**` → **computed 0.0506 ✓**

### Defect 1 — its power table is the crude formula

| True SR | 1F "single test" | crude `6.185/SR²` | variance-corrected (adopted) |
|---|---|---|---|
| 0.5 | 24.8 | 24.7 ✓ | **27.8** |
| 1.0 | 6.2 | 6.2 ✓ | **9.3** |
| 2.0 | 1.6 | 1.5 ✓ | **4.6** |

So its own table is internally consistent with the crude formula and inherits the same 50% understatement at
SR 1.0 that `MODEL_ANSWER_DELTAS` §2e corrected. 1E is the only answer that got this right.

### Defect 2 — its Bonferroni column is 24% overstated at low Sharpe

Claimed vs recomputed at `α = 0.0025` one-sided (`z = 2.81`, sum `3.652`):

| True SR | 1F claims | `(3.652/SR)²` | Error |
|---|---|---|---|
| 0.3 | **183** | **148.2** | +23% |
| 0.5 | **66** | **53.3** | +24% |
| 1.0 | 13.4 | 13.3 | ✓ |
| 1.5 | 6.0 | 5.9 | ✓ |
| 2.0 | 3.4 | 3.3 | ✓ |

The high-Sharpe rows are right and the low-Sharpe rows are wrong by a quarter — the direction of error is
conservative (it discourages), but it is still wrong, and a table where two adjacent rows use different arithmetic
is the same defect class as 1D's MinBTL contradiction.

### Scoreboard update

**1F joins 1E and 1D at the top on breadth, but is the weakest of those three on arithmetic** (one exact example,
one crude power table, one miscalculated column). Rank on content: 1F ≈ 1E > 1D > Luna > Claude > GLM > 1A > 1B > 1C.
Rank on arithmetic integrity: **1E > 1D > 1F**.

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
