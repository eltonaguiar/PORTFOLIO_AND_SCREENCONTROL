# Validation methodology — three-model panel, audited against our own numbers

**Source:** chatplayground (multi-model), captured 2026-11-23 02:00 local by the operator.
**Models:** ChatGPT-6 Luna, Claude (latest), GLM 5.3 Flash (a fourth answer — Qwen/Gemini — was not captured).
**Prompt:** a generic request for a rigorous proof methodology covering discovery discipline, backtest construction,
the statistics a professional checks, a forward-test protocol, and falsification conditions.
**Echo risk:** LOW. The prompt contained none of our measured numbers, so nothing here can be an echo of our own
figures. Every number below is either the model's proposed *threshold* or our *measured* value, and the two are
kept in separate columns.

---

## 1. The convergent gate table

All three models independently proposed almost the same gate set. Where they set different numbers, both are shown.

| Gate | Proposed threshold | Agreement |
|---|---|---|
| Deflated Sharpe (DSR) | ≥ 0.95 serious, ≥ 0.99 high-stakes | **unanimous** |
| PBO via CSCV | ≤ 0.10 (Luna) vs < 0.25 (Claude/GLM) | split — Luna strictest |
| Walk-forward efficiency | 0.5–1.0 pass; < 0.3 fail; > 1.2 suspicious (leakage) | **unanimous**, including the >1.2 tell |
| IR vs matched benchmark | ≥ 0.5 pass, < 0.25 fail; 95% lower bound > 0 | **unanimous** |
| Alpha t-stat | ≥ 3.0 discovered; ≥ 2.0 pre-registered single hypothesis | **unanimous** (Harvey–Liu–Zhu) |
| 2× cost test | net Sharpe > 0 at 2× costs; break-even cost multiple ≥ 2.5× | **unanimous** |
| Capacity | ≥ 2× (Luna) vs ≥ 3× (Claude/GLM) planned AUM | split |
| Tail ratio | ≥ 1.0 pass, < 0.8 fail (P95/P5, not a stand-alone gate) | Luna + Claude |
| MinTRL | realised length ≥ minimum track-record length at 95% | Claude only |
| Placebo battery | random-signal / shifted-date / subperiod / universe / parameter-neighbourhood | Claude only (most complete) |

**The genuinely new items none of our documents had:** the **placebo battery** (random-signal Sharpe distribution as a
floor for what the discovery pipeline produces by chance), the **break-even cost multiple** (≥ 2.5×, stronger than our
"2× cost survival"), the **parameter-neighbourhood test** (±20% around chosen parameters), and **MinTRL** as a gate
distinct from DSR.

## 2. Power: all three agree, and they agree with us

Claude's table (one-sided α = 0.05, 80% power) is the clearest statement of the constraint:

| True annual Sharpe | Years needed | At α = 0.0005 (~100 trials, Bonferroni) |
|---|---|---|
| 0.5 | **24.7 years** | 68 years |
| 0.75 | 11.0 years | 30 years |
| 1.0 | **6.2 years** | 17 years |
| 1.5 | 2.8 years | 7.6 years |
| 2.0 | 1.5 years | 4.3 years |

Luna's equivalent arrives at **≈1,560 independent daily observations ≈ 6 years** for Sharpe 1.0. This independently
reproduces the number Copilot derived for our own programme ("with ~10%/yr strategy vol the SE of the annualised mean
is ≈10/√n, so 4+ years"). Three models and one of our agents converged on the same arithmetic from different
directions — treat it as settled: **a four-hour window, or a four-month paper test, cannot prove a modest Sharpe.**

**Consequence for us:** the only honest forward test we can start is one whose verdict is years away. Anything we
"prove" inside a session is a construction check, not a validation.

> **CORRECTION (added after the sixth answer was audited).** The `6.2 years` figure above uses the crude
> `Y = 6.185/SR²`. The variance of a Sharpe estimate is `Var(ŜR) ≈ (1 + SR²/2)/Y`, so the correct requirement is
> `Y = 6.185·(1 + SR²/2)/SR²`, verified by direct computation: **SR 1.0 → 9.28 y** (not 6.18), **SR 0.5 → 27.83 y**
> (not 24.74), SR 1.5 → 5.84 y, SR 2.0 → 4.64 y. Every downstream statement that says "6.2 years" — including the
> adopted toolkit's printed output and three agent reports — is the optimistic version. Use the corrected column.

## 3. Our programme measured against the gates

| Gate | Required | Our measured value | Status |
|---|---|---|---|
| DSR | ≥ 0.95 | Kilo: 0.0068 / 0.000 on the ranked rows (N=658); Copilot: 0.9543 → **0.3191** when N was corrected 15 → 90 | **FAIL** |
| PBO | ≤ 0.10 (strict) | Kilo: 0.11; crypto VWAP pod 0.84–0.97 at lag (0.18 same-bar) | **FAIL / marginal at best** |
| Deflation survival | any | **0 of 55** survive at SR\* 1.014, σ_SR 0.439; **0 of 6 classes** at N=90 | **FAIL** |
| WFE | ≥ 0.5 | not computed anywhere in the estate | **UNMEASURED** |
| IR vs matched benchmark | ≥ 0.5, LB > 0 | undefined — no class has a CI on net return | **UNMEASURED (blocked)** |
| Alpha t | ≥ 3 discovered / ≥ 2 pre-registered | not computed at programme level | **UNMEASURED** |
| 2× cost | net > 0 | ETF survives (13.4244 bp RT vs 6.7122 measured); FOREX fails (15.066 vs 4.3038 break-even) | **1 pass, most fail** |
| Break-even cost multiple | ≥ 2.5× | never computed — only "2× survival" was used | **NEW GATE, UNMEASURED** |
| Capacity | ≥ 2–3× planned AUM | participation at 20% of ADV only; impact at size unmeasured; FX carry capacity $29,438 on XRP | **FAIL / UNMEASURED** |
| Tail ratio | ≥ 1.0 | never computed | **UNMEASURED** |
| Placebo battery | strategy in top 1–5% of random-signal distribution | never run | **UNMEASURED** |
| MinTRL | realised ≥ required | Kilo's forward book has ~137 trades over weeks | **FAR BELOW** |

Only one row is a pass, and it is a pass on a *wrapper* (ETF trading cost), not on a strategy. Everything that
would tell us whether a rule has an edge is either measured and failing, or not measured at all.

## 4. Where the panel is wrong or not applicable to us

1. **CRSP/Shumway-style delisting returns (−30% NYSE / −55% NASDAQ) assume a US equities universe.** We trade ETFs,
   crypto spot/perp, FX and futures. Applying equity defaults would be a category error; the equivalent for us is
   delisting-aware *ETF closure* handling and futures roll adjustment, which Zoo Code correctly flagged as
   `BLOCKED_MISSING_DATA` rather than approximated.
2. **"≤ 5% of ADV per day" is unusable at our size in the other direction** — at a $1k–$25k ticket our participation
   is 0.008% of ADV, so capacity is not the binding constraint. The panel's capacity gates matter only if someone
   proposes deploying six figures. Our capacity problem is the opposite: costs are per-ticket fixed, so small tickets
   carry a *higher* bp cost, which is why the IBKR 11 bp/side at $1k vs 0.4 bp at $25k measurement matters more than
   any impact curve.
3. **Borrow-fee modelling is irrelevant to a long-only ETF book** (no short leg), and central to the families we
   already killed (HML long-short died partly of borrow/implementation, FX carry of spread).
4. **Group-sequential / alpha-spending designs presuppose a trial with a fixed endpoint.** Our pods have kill rules
   with day-based triggers (H-201 at day 40), which is a *safety* stop, not an efficacy boundary — the panel is right
   that a safety stop must not be reported as evidence either way, and our pods should say so explicitly.

## 5. Adopted into our process

| Item | Where it lands |
|---|---|
| Break-even cost multiple ≥ 2.5× (replacing bare "2× survival") | `03-trading-strategies/STRATEGY_SPEC.md` gate list |
| Parameter-neighbourhood ±20% test | new required robustness row per candidate |
| Random-signal placebo battery | required before any candidate is called ALIVE |
| MinTRL reported alongside DSR | every scorecard |
| One-look holdout rule (a second look burns the holdout) | written into each pre-registration |
| "Safety stop is not an efficacy boundary" | the H-201 / pod kill-rule wording |

## 6. What this changes about the answer to "what should we invest in"

Nothing. It strengthens it: the panel's thresholds are *stricter* than the ones we applied, and our programme fails
even the softer version. The ranking stays empty, cash at 4.32% stays the benchmark, and the single live forward test
remains ETF 12-month absolute momentum — with the explicit acceptance that its verdict is **years** away, not weeks.

**Status of this document:** model answers quoted as `MODEL CLAIM`; every number in §3 is `observed` in our repos or
agent reports, with the source named. No claim in §3 was recomputed here.

---

## 7. SUPERSEDED IN PART — cross-check against the adopted v1.0 protocol

After this document was written, the operator supplied a full **strategy validation protocol v1.0** (49,890 bytes,
now at `03-trading-strategies/validation/`) with a runnable toolkit and a 17-gate master sheet (§3.11). **v1.0 is the
operational standard; this panel document is corroboration only.** On every gate the models and v1.0 both specify,
v1.0 is equal or stricter:

| Gate | Panel (model consensus) | v1.0 §3.11 | Which binds |
|---|---|---|---|
| PBO | ≤ 0.10 (Luna) / < 0.25 (Claude, GLM) | **≤ 0.10 pass**, 0.10–0.25 marginal, > 0.25 fail | **v1.0 = Luna's strict end** |
| Walk-forward | ≥ 0.5 | **≥ 0.60**, < 0.40 fail | v1.0 stricter |
| Alpha t | ≥ 3.0 discovered / ≥ 2.0 pre-registered | **≥ 3.0 at N_eff ≤ 10, 3.5 at ≤ 100, 4.0 above** — scaled by trial count | v1.0 stricter |
| Break-even cost | ≥ 2.5× | **≥ 4×**, < 2× fail | v1.0 stricter |
| Capacity | ≥ 2× / ≥ 3× planned AUM | **≥ 5×**, < 2× fail | v1.0 stricter |
| Tails | tail ratio ≥ 1.0 | tail ratio ≥ 1.0 **and skew > −0.5 and best-month share ≤ 25%** | v1.0 adds two conditions |
| DSR | ≥ 0.95 | ≥ 0.95 (marginal 0.90–0.95) | equal |
| IR vs matched benchmark | ≥ 0.5 | ≥ 0.50 | equal |

**Gates v1.0 has that the panel never proposed:** data integrity (≥99% PIT-valid universe-months *with* delisting
returns), survivorship sensitivity (SR(full) − SR(naive) < 0.10), parameter stability (SR CV over ±20% ≤ 0.30),
regime count (zero negative-SR sub-periods), out-of-market replication (≥50% of headline on a cross-market or
post-publication sample), and MinTRL ≤ available sample length.

**What this does to our programme.** v1.0's gates are ordered with data integrity first, and it says explicitly:
*"if you cannot certify ≥99% of universe-months as PIT-valid with delisting returns present, stop. You are not
measuring a strategy; you are measuring data."* Our universe is **survivor-conditioned** and EDGAR `filed` was never
polled — so we fail **Gate 1**, which is mandatory. Under v1.0's scoring (*"17/17 = green, any mandatory fail = red
(kill, log, move on)"*) the programme is **red before any statistic is consulted**, and the empty ranked list is not
a shortfall of the strategies but a correct refusal to rank strategies measured on a broken universe.

That is a stronger conclusion than this document reached on its own, and it is the reason the protocol supersedes
it: the panel told us our strategies fail; v1.0 tells us we cannot yet *measure* them.

