# Multi-AI harvest: how to prove a stock strategy works

Run 2026-11-22 · Prompt: candidate discovery without self-deception, backtest construction rules,
professional statistics with thresholds, forward/paper-test protocol with power, and falsification
criteria. Four sites driven in the user's own logged-in Chrome (`zerounderscore@gmail.com`).

## 1. Coverage — who actually answered

| Site | Models that answered | Harvest | File |
|---|---|---|---|
| **web.chatplayground.ai** | ChatGPT-6 Luna, Claude (Latest Model), GLM 5.3 Flash — **3/3** | **complete** (33.7 KB) | `harvest/chatplayground_methodology.md` |
| **app.1min.ai** | GPT-4.1 mini (6 models selected, 1 responded in full) | **complete** (10.6 KB) | `harvest/1min_methodology.md` |
| **askanymodel.xyz** | Second pass with 6 selected: Gemma 4 26B A4B, Nemotron 3.5 Super VL, Nemotron 3.5 Lightning, **GPT-5 Nano, Gemini, Claude Haiku 4.5** — 6/6 answered (Gemini first + most detailed, Claude Haiku shortest) | **partial** — page text is not selectable and the a11y tree is virtualised; only fragments captured | `prototype/transcripts/askanymodel_tree_raw.txt` |
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

Both arena answers push past "pick a threshold and pass it":

- **Three outcomes, not two.** *Pass* / *Fail* / **Inconclusive** — and inconclusive is **not** permission
  to lower the hurdle, change the metric, or keep testing until something passes. That is the failure
  mode of nearly every retail research loop.
- **A fixed reporting pack** to be allowed to say "works": pre-registration + trial log with N and V;
  PIT/survivorship/cost plus audit tests; net equity, drawdown, monthly table, turnover, exposures;
  DSR + PBO/CSCV histograms; walk-forward table; IR and factor regression; 2×-cost; tail; and a kill list.
- **A stronger null**: Hansen SPA / White Reality Check with **p > 0.10 across the family**, and DSR
  recomputed with the *true* N including every forward tweak, targeting **< 0.90**. Our forward gate only
  asks for a CI lower bound above zero at 2× costs — arena's null is stricter and worth adopting.
- **The scaling rule**: pass everything, then survive **12+ months live at small size with IR intact** —
  and only then scale. No single Sharpe, PBO, or backtest plot substitutes for that.

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
