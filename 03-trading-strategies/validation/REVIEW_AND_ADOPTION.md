# Strategy validation protocol v1.0 — verification and adoption

**Source:** `.../Downloads/workspace-01a20621-.../strategy_validation/` (operator-supplied, 22 Nov 2026).
**Files adopted verbatim into this directory:**

| File | Size | What it is |
|---|---|---|
| `strategy_validation_protocol.md` | 49,890 B | the full protocol, v1.0 — 7 sections + 3 appendices |
| `validation_toolkit.py` | 17,731 B | 23 functions in 10 sections, numpy/scipy |
| `trial_ledger_template.csv` | 1,427 B | append-only ledger schema **plus 5 worked example rows** |

**Note on provenance:** the file first handed over as `~/Downloads/strategy_validation_protocol.md` is a 20,281 B
*excerpt* (it stops at §2.8). The workspace copy is the complete document. Any earlier reading of the short one
understates the protocol by more than half.

## 1. Verification — it runs

Executed the toolkit self-test on this machine: **numpy 2.2.6, scipy 1.17.0**, exit 0. Reference output, recorded so
later readers can detect a change in behaviour:

| Block | Result |
|---|---|
| [A] 20y monthly, SR 0.51 | 90% stationary-bootstrap CI **[0.08, 0.92]**, PSR(0)=0.9891, **MinTRL = 124 months (10.3 y)** |
| [B] DSR, N_eff=200, sd(SR_trials)=0.35/yr | E[max SR \| null] = **0.97** annualised → **DSR = 0.0182** |
| [C] PBO/CSCV, S=16, 40 configs × 240 mo, 12,870 splits | pure noise **0.51** · weak 4%/yr **0.46** · strong 8%/yr **0.20** |
| [D] N_eff | 100 configs from 3 latent drivers → **1.4** (independent grid would be 100) |
| [E] Power | SR 0.5 → **24.7 y**; SR 1.0 → **6.2 y** (t=3 needs **9.0 y**) |
| [F] Break-even | 8.51% gross at 300% turnover → **284 bp** round-trip tolerance |
| [G] BH-FDR q=10% | 5 of 8 p-values survive |

## 2. What this adds that our gate list genuinely lacked

1. **MinTRL** as a first-class gate, not a footnote to DSR — 124 months needed for a 0.51 Sharpe is a number a
   human can act on ("I will not know for a decade").
2. **N_eff by eigenvalue participation ratio** `(Σλ)²/Σλ²`. This is the formal answer to a question we kept
   answering by hand: how many of our 65-config sweeps were actually independent tests. Demo answer: **100 configs
   off 3 latent drivers ≈ 1.4 effective trials.**
3. **PBO noise baseline (0.51).** Without it, "PBO = 0.11" and "PBO = 0.84" are numbers without a reference. With
   it, our crypto VWAP pod at **0.84–0.97 is worse than a pure-noise family**, which is a sharper statement than
   "overfitted".
4. **Five mechanical leakage tests** (§2.7): timestamp audit, time-shuffle placebo, universe placebo, progressive
   rebuild (max abs diff must be 0), and a **holdout seal test that asserts loading the sealed window raises**.
5. **Hypothesis tiering A–D with prior decay rates** (§1.1) and the rule *"if you can't write the mechanism
   sentence, it's Tier D"* — i.e. prior = 1/N_trials.
6. **The research firewall**: cross-market holdouts (develop US → validate Canada/UK) preferred to time-splits,
   because it dodges the "the world changed after my in-sample" objection.
7. **Capacity curve and power budget** as code, not prose.

## 3. Cross-check against our own measured state

| Protocol claim / demo number | Our measured value | Consistent? |
|---|---|---|
| DSR collapses under honest N (0.0182 at N_eff=200) | Copilot: **0.9543 → 0.3191** at N 15→90; Kilo rows 0.0068/0.000 at N=658 | yes — same direction, ours is worse |
| PBO noise ≈ 0.51; a real 8%/yr edge ≈ 0.20 | Kilo 0.11 (better than the strong-family baseline, on a *much* smaller n); crypto VWAP **0.84–0.97** (worse than noise) | mixed — and the 0.11 deserves suspicion precisely because it beats the 8%/yr-edge baseline |
| 100 correlated configs ≈ 1.4 trials | our "65-config sweep" was never 65 independent tests | yes — retroactively explains the deflation collapse |
| SR 1.0 needs 6.2 y (t=3 → 9.0 y) | Copilot independently derived 4+ years from 10%/yr vol; 3-model panel got 6.2 y | yes — three sources |
| Commission $0.0035/sh at $30 = **11.7 bp/side** | Copilot measured IBKR **11 bp/side at a $1k ticket, 0.4 bp at $25k** | yes, exactly — this is our binding constraint |
| Mega-cap round trip **8 bp** | our measured ETF **6.7122 bp**, direct equity **12.0749 bp** | plausible; ours is measured on our own bars, theirs is a 2025–26 assumption table |
| 30–60% haircut to published premia | our HML: **+0.11%/yr gross** — i.e. ~100% decay | ours is worse than their prior |

## 4. Where it does not bind for us (and what to use instead)

The protocol is written for **US equities with a short leg and PIT fundamentals**. Our universe is ETFs, crypto,
FX and futures with **no short leg**, so:

- **Borrow / HTB / locate-failure sections do not apply.** The analogous blocker for us is **futures roll
  adjustment**, which Zoo Code already recorded as `BLOCKED_MISSING_DATA` rather than approximated.
- **CRSP/Shumway delisting defaults (−30%/−55%) are equity-specific.** Our equivalent is ETF closure handling and
  ticker change on the same security; applying equity defaults to a bond ETF would be a category error.
- **Participation caps (1–5% of ADV) are irrelevant at our size** — we are at 0.008% of ADV. The binding retail
  cost for us is the **fixed per-ticket commission**, which the protocol states correctly in §2.5 and which our own
  IBKR measurement confirms.
- **PIT fundamentals** is the section that matters most and where we fail hardest: our universe is
  survivor-conditioned and EDGAR `filed` was never polled, so §2.1's verdict rule applies — *"you are not measuring
  a strategy; you are measuring data."*

## 5. Adoption actions

| Action | Lands in |
|---|---|
| Adopt the **ledger schema** verbatim, including `n_eff_est` and `n_trials_cumulative` per row | `03-trading-strategies/tools/trial_ledger.csv` |
| **MinTRL** printed beside DSR on every scorecard | scorecards |
| **PBO reported against the 0.51 noise baseline** (never bare) | scorecards |
| **N_eff** computed for every multi-config sweep before deflation | every pre-registration |
| §2.7's **five leakage tests** become mandatory before a backtest is reported | `STRATEGY_SPEC.md` |
| **§3.11 master gate sheet** adopted as the scorecard template | `03-trading-strategies/` |
| Break-even cost multiple **≥ 2.5×**, capacity ≥ 3× planned AUM | already added via the panel audit; now with code |

## 6. Duplicate removed

A stdlib-only re-implementation of PSR/DSR/PBO was written here before the real toolkit surfaced
(`tools/validation_toolkit.py`). **Deleted.** One owner per concern: the supplied toolkit is richer (MinTRL,
capacity curve, power budget, BH-FDR, stationary bootstrap CI) and now verified on this machine, whereas the
re-implementation covered roughly half the functions and had never been cross-checked against a reference
implementation. Keeping both would guarantee the two drift apart — the same failure the playbook already names.

**Status:** protocol text, toolkit and ledger adopted verbatim; demo output recorded as `observed` (run on this
machine, 2026-11-23); no claim in §3 was recomputed here beyond quoting both sides.
