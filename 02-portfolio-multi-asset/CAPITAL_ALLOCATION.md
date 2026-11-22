# Capital allocation — how to invest when your own ledger says 0 of 67 cells are proven

This document answers a different question from the rest of `02-`: not *how to value a portfolio* and not *how to
test a strategy*, but **how to allocate real money across horizons** given what the evidence engine already
reports. Numbers below were fetched live from the audit surface on 2026-11-22 and are cited with their
generator timestamp; everything else is marked as convention or judgement.

## 1. The evidence, fetched not paraphrased

Source: `https://findtorontoevents.ca/audit3/audit3_ledger.json` — `generated_at 2026-11-22T07:10:35Z`,
`source_generated_at 04:00:19Z`. The page's own disclaimer: *"audit3 is an evidence ledger, not a signal
service… PROVEN_T2 does not guarantee future returns."*

| Summary field | Value |
|---|---|
| closed picks scored | **8,827** of 14,914 (59.19%) |
| strategy cells tested (n ≥ 20) | **67** of 374 |
| proven (`PROVEN_T2`) | **0** |
| candidate | **0** |
| weak (no claim either way) | 57 |
| proven harmful (kill) | 10 |
| insufficient n | 307 |

And the measurement that decides the allocation question — **selection alpha**, i.e. pick net return minus the
direction-adjusted return of simply holding the same instrument over the same window:

| Class | n | pick net | hold net | **selection alpha** | 95% CI |
|---|---:|---:|---:|---:|---|
| CRYPTO | 1,674 | −0.70% | −0.14% | **−0.55%** | [−0.91, −0.21] ← excludes 0 |
| COMMODITY | 40 | −3.57% | 0.00% | **−3.57%** | [−5.51, −2.05] ← excludes 0 |
| ETF | 539 | −0.07% | +0.03% | −0.10% | [−0.31, +0.10] |
| FOREX | 132 | −0.14% | −0.07% | −0.07% | [−0.15, +0.01] |
| EQUITY | 731 | −0.05% | −0.01% | −0.05% | [−0.42, +0.33] |
| BOND | 35 | −0.21% | −0.16% | −0.05% | [−0.40, +0.31] |
| FUTURES | 4 | +1.34% | 0.00% | +1.34% | no CI (n=4) |

**Read it this way:** in no class do the picks beat holding, and in two classes they demonstrably lose to it.
That is not "the strategies need tuning" — it is the allocation instruction. Meanwhile the same surface is
reporting *holding* returns that are close to zero or slightly negative over these windows, which is the other
half of the message: short-horizon trading was a cost, not an income.

Costs used (measured, per class, `payload.slippage_validation`): CRYPTO 0.0996%, EQUITY/ETF/BOND 0.05%,
COMMODITY 0.15%, FOREX 0.02%, FUTURES 0.10%, MUTUAL_FUND 0.08%.

Forward gate: **9 pods, 1 pre-registered (POD-EQUITY-BREAKOUT), 8 observe, 0 with enough forward rows to
promote.** So today the correct capital allocation to the strategy book is **zero**, not "small".

## 2. The structure that follows

Three tiers, separated by *when the money is needed*, not by conviction.

| Tier | Horizon | Vehicle | Why this, given the ledger |
|---|---|---|---|
| **1 — Floor** | 0–3 years, plus a 3–6 month emergency reserve | HISA / money-market or T-bill ETF, **GIC ladder** (1/2/3/5y) | the only positive, knowable return available. A GIC is a deliberate trade: liquidity and volatility sold for a known rate. Verify **CDIC** coverage — $100,000 per depositor per member institution per insured category — and split balances across institutions above that |
| **2 — Risk premia** | 5+ years | broad-market index ETFs, lowest available MER; duration-matched bonds for known nominal liabilities | the audit's own doctrine says the surviving public edge is *risk premia*, and the cheapest way to own a premium is to hold it. A 1–2% MER mutual fund is a permanent negative selection alpha |
| **3 — Research** | indefinite | pods only, and only after the forward gate | capped so that a total loss does not change the plan |

Sizing for tier 3 is a policy choice, not an optimization: the four models argued 5%, 5–15% and "≤5–10%"
respectively, all arbitrary. **Use whatever you can lose entirely without changing any other decision** — and
note that at present the correct number is 0%, because no pod has passed the gate.

## 3. What "the best investment" actually is, per horizon

| Question | Answer | Not because it is exciting — because |
|---|---|---|
| Day trading | **No** | the ledger's own cost gate: measured slippage 5–15 bps per side against an edge that is negative before costs |
| Swing trading (2–30 days) | **Not with money yet** | one pod family (equity breakout) has positive OOS statistics and **zero forward rows**; the VWAP lab result collapses under a 1-bar execution lag (PF → 0.957) |
| Medium term (months–years) | index + rebalance on bands | selection alpha is negative in every class measured |
| Long term (5y+) | low-cost global index, tax-sheltered | the premium is the holding period, not the pick |
| GIC / savings | **yes, for money with a date** | a known rate beats an unknown one when the horizon is shorter than the variance |
| Crypto | **no** until a pod promotes | selection alpha −0.55%/pick with a CI entirely below zero, and DSR 0.000 |
| Commodities / futures | **no** | 50 picks at −3.57%/pick; futures n=4 |
| Forex | **no** | FX class is "honest-exhausted": 132 picks at −0.07%, CI touching zero |

## 4. Funding rule (the only part that is mechanical)

```
capital moves to a pod  ⇔  forward_gate passed
forward_gate           =  n ≥ 100 forward rows after registration
                          ∧ net CI lower bound > 0 at 2× measured slippage
                          ∧ IR ≥ 0.5 vs the matched benchmark leg
                          ∧ split-half stable
```

No exceptions, no "small pilot", no discretion. A promotion moves a **fixed increment** of tier 3, never the
whole book, and every kill switch executes as written — including `CI-LB ≤ 0 at day 30 or 60 ends the pod`.

## 5. Fix the measurement system before adding hypotheses

The ledger's doctrine says the binding constraint is hypothesis quality and trial budget. On that logic the
highest-return work right now is not a new strategy:

1. **POD-EQUITY-BREAKOUT is starving while orphan H-119 has 430 forward rows** — the only pre-registered pod
   accrues nothing while unowned data streams in. Wire the emitter.
2. **The winner-stays bug** gave POD-ETF-DUAL-MOMENTUM zero closes.
3. **Dormant emitters** — `commodity_basis_carry` emits zero rows; `contango_roll_yield` is misclassified.
4. **9,277 auto-expired rows score as neither win nor loss**, so a wide-TP strategy escapes judgement forever.
   Score timeouts as their own class.
5. **5,994 integrity-excluded rows** (ghost rows, WON-vs-PnL contradictions) is a data-quality problem worth
   more than any new cell.
6. **Reproducibility**: the ledger's own provenance warns that its source is a `/tmp` build path, and audit2's
   population endpoint returns 404. Commit the build; fix the endpoint.
7. **Commit the cost basis**: the measured per-class slippage table above is the most valuable number in the
   repo — make sure it is versioned with the ledger, not regenerated silently.

## 6. Which of the four answers to trust

| Source | Best at | Where it errs |
|---|---|---|
| **GLM 5.3 Flash** | the operational diagnosis (starving pod, orphan rows, winner-stays, dormant emitters, `/tmp` build) and the funding rule | nothing material |
| **ChatGPT-6 Luna** | horizon framing, emergency reserve, CDIC, "audit scores 59.2%" caveat | generic on Canada specifics; no live numbers |
| **Claude** | clear separation of core vs capped experiment, benchmark comparison, kill rule | "5% or less" is a number without a derivation |
| **Qwen3.6 Flash** | the validation-pipeline translation (pre-register → purged WF → 2× cost → forward gate) | asserts "indexing beats active selection 90%+ of the time" without a citation (SPIVA-style studies support high underperformance rates, but say so); invents an 80/5/15 split as if it followed from the ledger |

All four agree on the important thing, and the ledger agrees with them: **0 proven cells is not a reason to
stop investing; it is a reason to stop paying for picks.**

## 7. What this document does not do

No position sizing, no tax advice, no security selection. Account choice (TFSA / RRSP / FHSA / RESP), withholding
tax, and FX conversion will change net numbers and belong to a fee-only advisor and your own tax situation.
Nothing here is financial advice.
