# Multi-AI harvest: how to prove a stock strategy works

Run 2026-11-22 · Prompt: candidate discovery without self-deception, backtest construction rules,
professional statistics with thresholds, forward/paper-test protocol with power, and falsification
criteria. Four sites driven in the user's own logged-in Chrome (`zerounderscore@gmail.com`).

## 1. Coverage — who actually answered

| Site | Models that answered | Harvest | File |
|---|---|---|---|
| **web.chatplayground.ai** | ChatGPT-6 Luna, Claude (Latest Model), GLM 5.3 Flash — **3/3** | **complete** (33.7 KB) | `harvest/chatplayground_methodology.md` |
| **app.1min.ai** | GPT-4.1 mini (6 models selected, 1 responded in full) | **complete** (10.6 KB) | `harvest/1min_methodology.md` |
| **askanymodel.xyz** | Six panes selected; **4 distinct answers** — Gemma 4 26B A4B, Gemini, Claude Haiku 4.5, and one body shared verbatim by *Nemotron 3.5 Super VL / Nemotron 3.5 Lightning / GPT-5 Nano* | **complete** (26.8 KB) — needs a click in the **blank gutter between columns** before `Ctrl+A`; every pane ended with "This answer reached its length limit" | `harvest/askanymodel_methodology.md` |
| **arena.ai** | Blind pair `Assistant A` / `Assistant B` (identities hidden until a vote) — **2/2 answered** | **complete** (38.6 KB) — Chat mode; the Chat→Agent switch ignores synthetic clicks, so the run went through Chat | `harvest/arena_methodology.md` |

Failure worth recording: on the first askanymodel pass, `Gemma 4 31B` returned *"This model is
temporarily unavailable"* and `Nemotron 3.5 Lightning` never answered. Rotating in three different
models (GPT-5 Nano, Gemini, Claude Haiku 4.5) produced **6/6 answers** on the second pass — so model
failure is a routing problem, not a task failure.

## 2. What the models agree on (convergent, and it matches our own gates)

**Discovery**
- Pre-register the claim before touching confirmation data: economic rationale, instruments and dates,
  exact signal/execution rules, primary outcome, benchmark, decision gates, permitted changes. Timestamp
  protocol + code + data snapshot.
- **Count every trial**, including informal tuning. "If a result inspires a new rule, that rule is a new
  hypothesis — not a confirmation of the old one."
- Keep discovery / validation / confirmation chronologically separate; a holdout spent once is spent.

**Backtest construction** (each item was named independently by every model)
- Point-in-time data; no restatements of fundamentals.
- Point-in-time universe **including delisted names** (survivorship).
- Signal timestamp ≤ decision time; fill at the next available price, never the signal bar's close.
- Corporate actions handled (adjusted for signals, raw for fills).
- Costs: commission + spread + measured slippage, then **re-run at 2× cost** with nothing else changed.
- Capacity: participation limits, market impact, borrow availability — re-estimate as capital scales.
- Intrabar ambiguity: OHLC cannot order a TP and an SL touch inside one bar; resolve conservatively.

**Statistics with thresholds** (as given in the harvest, not invented here)

| Statistic | Pass | Fail |
|---|---|---|
| Deflated Sharpe (DSR) | **≥ 0.95** | < 0.80 (0.80–0.95 marginal) |
| Min track-record length | realised history ≥ MinTRL at 95% | shorter |
| PBO via CSCV | **≤ 0.5**, ideally ≤ 0.2 | ranking unstable across splits |
| Walk-forward efficiency (net OOS Sharpe / net IS Sharpe) | ≳ 0.5 | — ; **> 1.2 suggests leakage** |
| Information ratio vs matched benchmark | **≥ 0.5** | < 0.25 |
| Alpha t-statistic (Newey-West) | **≥ 3.0** for discovered factors, ≥ 2.0 for a single pre-registered hypothesis | < 2.0 |
| 2× cost test | net edge still > 0 | edge < friction |
| Tail / capacity | drawdown, expected shortfall, skew, stress, participation limits acceptable | ruin risk or unfillable at size |

The `t ≥ 3` hurdle comes from Harvey, Liu & Zhu (2016) on multiple testing in the factor literature —
the models cited it unprompted, which is a good sign the answers are grounded rather than generic.

**Forward test**
- Same rules as the backtest, adversarial fills (next bar + measured slippage), no parameter changes.
- Sample size from **power, not round numbers**: with α = 0.05 and 80% power, an annualised Sharpe of
  1.0 needs roughly **1,560 independent daily observations ≈ 6 years**; serial dependence reduces the
  effective sample, so use Newey-West or block bootstrap.
- Stopping rules declared in advance; multiple-testing correction across the whole family tested.
- Falsification criteria written **before** the first forward row.

## 3. What arena's blind pair added that the others missed

**Assistant B is the single most operational answer in the set** — it is a stage-gate, not advice:

| Gate | Test | Pass to continue |
|---|---|---|
| 0 | economic rationale + pre-registration | written **before** seeing OOS |
| 1 | backtest integrity | every build-checklist row passes |
| 2 | multiple-testing-adjusted significance | **DSR ≥ 0.95, PBO ≤ 0.20** |
| 3 | robustness | WFE ≥ 0.50, IR ≥ 0.50, 2×-cost Sharpe > 0.5 *and* > 50% of base, tail ratio > 1.0, capacity > 20× intended size |
| 4 | forward/paper + live incubation | pre-specified N, alpha-spending, no peeking |
| 5 | live monitoring | no falsification trigger fires |

One fail stops the process; a revision is a new candidate needing new confirmatory data.

Its **worked DSR example** is the clearest statement of how data mining dies: 5 years daily (T = 1260),
SR 1.2 net, skew −0.2, kurt 4.5 — with N = 200 trials and V = 0.04 → SR₀ = 0.55 → **DSR ≈ 1.00, PASS**.
Same strategy, but you tried **N = 1000 with V = 0.25 → SR₀ ≈ 1.62 > SR 0.8 → DSR ≈ 0.02, REJECT.**
The only thing that changed was how many things you tried.

Its **forward-duration table** (80% power, one-sided α = 0.05) is the number most retail plans ignore:

| Active IR above hurdle | daily obs | years |
|---|---|---|
| 0.25 | 24,900 | **99** |
| 0.50 | 6,230 | 24.7 |
| 0.75 | 2,770 | 11.0 |
| 1.00 | 1,560 | 6.2 |
| 2.00 | 390 | 1.5 |

with ~620 independent trades if per-trade μ/σ = 0.10 — i.e. **a daily Sharpe below ~1 cannot be demonstrated
by a six-month paper test**, however good the early P&L looks.

Also from B, and worth adopting: PBO computed over C(16,8)/2 = **6,435** train/test splits; kill triggers with
concrete numbers (realised slippage > 2× modelled for 3 months; borrow hard on > 15% of shorts; live drawdown
> 1.5× worst IS drawdown; **any PIT/survivorship bug that removes > 20% of backtest Sharpe invalidates all
prior tests**); and a **stricter null**: Hansen SPA / White Reality Check **p > 0.10** across the family, DSR
recomputed with the true N including forward tweaks, targeting **< 0.90**.

From Assistant A, the framing that survives its messier formatting: *Pass / Fail / **Inconclusive***, where
inconclusive is **not** permission to lower the hurdle, change the metric, or keep testing until something
passes. A writes its numbers as LaTeX, and the clipboard dump splits formulas across lines — so A's equations
should be read from the rendered page, not the copy. B's tables survive the copy intact.

**Disagreement to resolve inside the repo:** B rejects below DSR 0.90 and accepts ≥ 0.95; the chatplayground
answers set the pass mark at 0.95 with 0.80–0.95 marginal. Our own forward gate does not use DSR at all yet —
it uses a CI lower bound above zero at 2× costs. B's version is the stricter and better-specified one.

## 4. Where they differ

- **How much discretion is allowed after pre-registration.** ChatGPT-6 Luna permits tightening gates
  before results are seen; Claude and GLM treat any change as a new trial. The stricter reading is the
  safer one.
- **Whether a paper test can confirm anything at all.** Claude's line is the sharpest: a paper test can
  only *fail* a strategy quickly; confirmation needs out-of-sample data the researcher never touched.
  Luna is more permissive about forward evidence counting as confirmation.
- **Capacity emphasis.** 1min.ai's answer (GPT-4.1 mini) puts capacity and participation limits into the
  discovery phase; the chatplayground answers put them at the end. Early is better — it kills ideas
  cheaply.

## 5. How this maps onto our repo

The harvested methodology is the same rule set this repo already enforces, which is a useful
cross-check rather than a new opinion:

- `03-trading-strategies/FABRICATION_CHECKLIST.md` — S1–S6 static gates (causality, exit ordering,
  annualisation, trial counting, cron UTC, workflow permissions), all passing on our harness.
- `02-portfolio-multi-asset/DATA_EVIDENCE_RULES.md` — provenance labels, intrabar ambiguity rule.
- `03-trading-strategies/STRATEGY_SPEC.md` — G1–G8 declaration gates, JSON-only authoring.
- `02-portfolio-multi-asset/CAPITAL_ALLOCATION.md` — the forward gate: n ≥ 100 rows after registration,
  CI lower bound > 0 at 2× measured slippage, IR ≥ 0.5, split-half stable.

Live audit state: **0 of 67 tested cells proven, selection alpha negative in every asset class.** The
methodology above is precisely why that number is credible rather than disappointing.

## 6. Reproduce

```
# clipboard route (full text, works on chatplayground + 1min)
click page → Ctrl+A → Ctrl+C → save clipboard
python prototype/parse_clipboard.py RAW.txt --models … --out harvest/x.md

# tree route (works when the answer fits the viewport)
python prototype/extract.py elements_<id>.json --prompt "…" --out harvest/y.md
```

Full transcripts and raw dumps: `prototype/transcripts/`.
