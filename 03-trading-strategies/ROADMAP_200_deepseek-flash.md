# 200 Rounds — from "no edge proven" to a defensible asset-class verdict

**Owner:** `deepseek-flash`
**Created:** 2026-11-22, 03:56 EST
**Repo:** `eltonaguiar/findtorontoevents_antigravity.ca`
**Harness:** `realtime_challenge/`
**Starting position (inherited, not assumed):** 34 pre-registered cells across 10 asset
classes; exactly one (EQUITY `xsmom_top3_6m`, H-201) clears the backtest gates and it has
**zero closed forward trades**. Buy-and-hold SPY returned 10.27% CAGR with a −55.2%
drawdown over 20 years. Nothing is sanctioned for real capital. See
`reports/2026-11-22-capital-allocation-verdict.md`.

That starting position defines the goal. The goal is **not** "find a strategy that
backtests well" — the repo already has one and it is worth nothing yet. The goal is:

> Produce **forward evidence** (≥100 closed trades, net of 26 bps round-turn friction,
> with a bootstrap CI on mean trade return that excludes zero and an excess return
> versus buy-and-hold on the same window) for at least one asset class, or a rigorously
> documented negative result explaining why none exists.

A clean "no class qualifies, here is the proof" is an accepted terminal outcome. What is
not accepted is a headline win rate on n=2, a same-close fill, or a parameter set chosen
after looking at the equity curve.

---

## The four gates a round must clear to count

Every round is judged on artifacts, not prose.

| gate | rule | where it is enforced |
|---|---|---|
| **G1 Execution honesty** | Signals on closed bars only; fills at next-bar open; bid/ask + taker fee both legs | `engine.run_from_signals`, `live.try_open` |
| **G2 Cost survival** | Cell must be positive at 26 bps round-turn, and the breakeven cost must be reported | `cli backtest` cost grid |
| **G3 Luck control** | Bootstrap CI on mean net return, permutation (shuffle) control, deflated Sharpe vs the recorded trial count | `stats.bootstrap_ci`, `stats.permutation_control`, `stats.deflated_sharpe` |
| **G4 Forward proof** | ≥100 closed forward trades net PF ≥ 1.1 **and** positive excess vs buy-and-hold on the same window | `ledger.summary`, `worker/forward_supervisor.py` |

A round that produces a number but no gate verdict is a note. A round that fails a gate
is a **result** and gets written down — it is not repeated with a tweaked parameter.

---

## Phase map

| Phase | Rounds | Question | Terminal artifact |
|---|---|---|---|
| **P0 Harness integrity** | 1–12 | Can this engine be trusted to say "no"? | `proof/HARNESS_CERTIFICATION.md` |
| **P1 Class census** | 13–40 | Which classes are even measurable right now? | `results/class_census.json` |
| **P2 Baselines & anomalies** | 41–66 | Do the documented calendar/funding anomalies survive 26 bps? | 6 pre-registered plans |
| **P3 Factor zoo, counted** | 67–100 | Of N tried, does any survive multiple-testing deflation? | `results/zoo_ledger.json` |
| **P4 Forward pods** | 101–140 | Which survivors keep working on unseen bars? | 100+ closed trades/cell |
| **P5 Portfolio layer** | 141–162 | Does combining candidates beat one of them? | `portfolio/` paper books |
| **P6 Regime & denylist** | 163–178 | Where does it break, and is the break now blocked? | wired denylist |
| **P7 Execution realism** | 179–190 | What do maker fills, latency and sizing actually cost? | calibrated slippage model |
| **P8 Beta vs alpha** | 191–197 | Is any of this better than just holding the index? | final comparison table |
| **P9 Verdict** | 198–200 | What may be allocated, at what size, with what kill switch? | `VERDICT_200.md` |

---

## P0 — Harness integrity (R1–R12)

The point of P0 is to build a machine that is *allowed* to return a negative. Most of
this repo's history is a machine that could not.

| # | Round | Deliverable | Gate |
|---|---|---|---|
| R1 | Ship `realtime_challenge/` skeleton: costs, data, engine, stats | working imports | — |
| R2 | Lag test: inject a 1-bar look-ahead and prove the harness detects it | `proof/test_lookahead.py` | G1 |
| R3 | TP/SL tie test: construct a bar touching both and assert SL fills first | `proof/test_intrabar.py` | G1 |
| R4 | Cost accounting test: a zero-edge random strategy must lose ≈ round-turn × n | `proof/test_costs.py` | G2 |
| R5 | Shuffle control calibration: on permuted prices, p-value must be ≈ uniform | `proof/test_permutation.py` | G3 |
| R6 | Deflated-Sharpe sanity: 100 pure-noise strategies must yield ≈0 cells above DSR 0.95 | `proof/test_dsr_null.py` | G3 |
| R7 | Cross-engine reconciliation: same signals through `vectorbt` and this engine; explain every difference | `proof/CROSS_ENGINE.md` | — |
| R8 | Data provenance: 5-venue OHLCV consensus; flag any bar where venues disagree > 50 bps | `proof/data_consensus.json` | — |
| R9 | Survivorship audit: list every symbol dropped for missing history and why | `proof/universe_audit.md` | — |
| R10 | Trial-count ledger: one append-only file counting every hypothesis ever run | `experiments/trial_count.json` | G3 |
| R11 | **Live harness proof**: open and close real positions on live prices | `REALTIMECHALLENGE_*.MD` §Live | G1 |
| R12 | Certification doc: state exactly what the harness can and cannot prove | `proof/HARNESS_CERTIFICATION.md` | all |

**Kill condition:** if R6 finds >5 of 100 noise cells "significant", the statistics layer
is broken and P1 cannot start. Fix the layer first.

---

## P1 — Class census (R13–R40)

Measurability before profitability. A class that cannot be measured correctly cannot be
cleared or killed, and quoting a PF for it is worse than saying nothing.

| # | Round | Class / instrument | Note |
|---|---|---|---|
| R13–R16 | Crypto spot 1h — BTC, ETH, SOL, XRP | 24/7, deepest data, no session gap | live now |
| R17–R20 | Crypto spot 4h and 1d | slower horizon, fewer trades, lower friction drag | live now |
| R21–R23 | Crypto perps funding/basis | needs exchange funding endpoints, no keys | live now |
| R24–R27 | FX majors (EURUSD, GBPUSD, USDJPY, USDCAD) | **opens Sun 17:00 EST** — 13h after this doc | needs session-aware bars |
| R28–R31 | US equity index ETFs (SPY, QQQ, IWM) | opens Mon 09:30 EST | gap risk is the whole story |
| R32–R34 | Single-name equities (large cap, liquid) | borrow/short constraints | G1 must model overnight gaps |
| R35–R36 | Commodities via ETFs (GLD, USO, DBC) | roll contamination — the repo's known unmeasurable | repair or formally retire |
| R37–R38 | Rates/bonds (TLT, IEF, SHY) | carry + duration, low vol, friction-sensitive | |
| R39 | Prediction markets | structurally zero-sum for a taker — test maker-only or drop | |
| R40 | Census verdict: what is measurable, what is retired, what needs a new feed | `results/class_census.json` | |

**Standing rule for P1:** every class entry records `bars_available`, `gap_structure`,
`median_spread_bps`, and `measurable: true/false` with a reason. Do not compute a PF for a
class marked unmeasurable.

---

## P2 — Baselines and anomalies (R41–R66)

Six pre-registered hypotheses, one per round-pair. Each gets a fixed parameter set
*before* the run; the run is not repeated after seeing results.

| # | Hypothesis | Why it might exist | Kill if |
|---|---|---|---|
| R41–R44 | H-R5 weekend effect (Fri 20:00 → Sun 20:00 UTC) | crypto has no market close; calendar flows differ | net ≤ 0 at 26 bps over ≥2 years |
| R45–R48 | H-R2 Donchian 20-bar TSMOM (both directions) | the single most replicated premium in the literature | fails permutation p<0.05 |
| R49–R52 | H-R1 trend pullback (EMA50/200 + EMA20 dip) | buying dips in an uptrend is the desk's core equity idea | excess vs B&H ≤ 0 |
| R53–R56 | H-R3 Bollinger lower-band reversion in uptrend | mean reversion pays where trend is intact | PF < 1.1 at 26 bps |
| R57–R60 | H-R4 ATR compression breakout | volatility clustering is real and measurable | no cell beats shuffle p95 |
| R61–R64 | H-R6 RSI(2) < 10 pullback | already a live equity family; port to 24/7 | forward n≥100 shows PF < 1.1 |
| R65 | Cross-hypothesis correlation matrix of trade returns | six "independent" ideas may be one bet | any pair |ρ| > 0.7 → merge |
| R66 | Anomaly verdict: which of six survives G2+G3 | — | — |

**Anti-sin rule:** `strategies.py` asserts `tp_atr/sl_atr ≤ 2.5` because the desk's own
registry records R:R > 2.5 as anti-predictive (30.6% WR). Entries are also zeroed during
UTC hours {2, 8, 13, 20}. Both constraints come from
`alpha_engine/negative_knowledge_registry.py` and are enforced in code, not in prose.

---

## P3 — Factor zoo, counted (R67–R100)

Here is where most projects die of multiple testing. The rule: **every hypothesis run
increments the trial counter, and the deflation bar rises with it.** By R100 the counter
will be ~150; at that point a per-trade Sharpe of 0.05 is noise.

| # | Round | Content |
|---|---|---|
| R67–R72 | Volatility-scaled momentum (target-vol position sizing) across 3 timeframes |
| R73–R78 | Short-horizon reversal (1–3 bar) with explicit spread cost |
| R79–R84 | Cross-sectional crypto momentum (rank top-3 of 7, weekly rebalance) |
| R85–R88 | Volatility risk premium proxy (sell realized vol via straddle-like sizing — flag as untradeable without options data) |
| R89–R92 | Order-flow imbalance from public trades endpoint (taker buy/sell ratio) |
| R93–R96 | Funding-rate carry (long negative-funding, short positive) |
| R97–R99 | Sequential DSR re-test of every cell after each increment to the trial counter |
| R100 | Zoo ledger: N tried, N passing DSR 0.95, and the expected-false-positive count |

**Deliverable:** `results/zoo_ledger.json` with, per cell, `n`, `pf`, `mean_bps`,
`dsr`, `perm_p`, `breakeven_cost_bps`, `trial_index_at_run`.

---

## P4 — Forward pods (R101–R140)

Backtest survivors graduate to a forward pod: real prices, real clock, no re-optimization.
The pod is the only thing that can ever produce G4 evidence.

| # | Round | Content |
|---|---|---|
| R101–R104 | Forward pod infra: GitHub Actions cron, state in git, TP/SL supervisor, daily digest |
| R105–R112 | Pod A: crypto 1h consensus book (≥2 hypotheses agree), 1% risk/trade, max 4 open |
| R113–R120 | Pod B: single-hypothesis books, one per survivor, equal notional, so attribution is clean |
| R121–R128 | Pod C: the same books on a second venue (Kraken vs Bybit) to measure venue/slippage effect |
| R129–R136 | Accumulate to n ≥ 100 per cell; weekly interim read-outs, **no peeking-driven changes** |
| R137–R140 | G4 verdict per cell: `PROMOTE` / `MONITOR` / `KILL` with the CI that decided it |

**Peeking rule:** interim read-outs are logged but do not change parameters. A parameter
change is a **new cell** with a new ID and its own forward clock starting at zero.

---

## P5 — Portfolio layer (R141–R162)

| # | Round | Content |
|---|---|---|
| R141–R146 | Vol-target overlay (10% annualized) on the promoted set; measure the vol drag honestly |
| R147–R152 | Risk parity vs equal weight vs inverse-vol across promoted cells |
| R153–R156 | Correlation-aware sizing; hard cap on any cluster with |ρ| > 0.7 |
| R157–R160 | Paper portfolios: `portfolio_10k`, `portfolio_100k` with rebalance rules and a kill switch at −15% |
| R161–R162 | Attribution: how much of the portfolio return is beta to BTC, and how much is selection alpha |

**Already implemented (2026-11-22):** `proof/portfolio_combination.py` builds a daily
mark-to-market equity curve per strategy (a flat day is 0.0%, not a missing observation),
forms the equal-capital combination, and reports each book's Sharpe, max drawdown,
correlation matrix and diversification ratio. First result: combined Sharpe **−0.123** vs
best single **+0.243** with a diversification ratio of **1.841** — the mix is genuinely less
volatile, and that did not help, because only 2 of 6 components had positive expectancy.
Portfolio construction is downstream of per-strategy edge, not a substitute for it.

**The test that matters:** selection alpha = pick return − direction-adjusted buy-and-hold
over the same holding windows. If its CI upper bound is below zero, the portfolio loses to
holding and must be reported as such regardless of any single cell's PF.

---

## P6 — Regime and denylist (R163–R178)

| # | Round | Content |
|---|---|---|
| R163–R168 | Regime tags: trend/chop × vol-high/vol-low, using only information available at the bar |
| R169–R172 | Per-regime cell performance; identify cells that only work in one regime |
| R173–R175 | Wire every KILL verdict into `negative_knowledge_registry` as a denylist entry |
| R176–R178 | Regression test: the scanner must refuse a denylisted symbol/combo (assert in CI) |

The repo's failure mode here was an audit that could only delete. R173–R175 close that
loop: kills become machine-enforced blocks, not paragraphs.

---

## P7 — Execution realism (R179–R190)

| # | Round | Content |
|---|---|---|
| R179–R182 | Calibrate slippage from live bid/ask observations actually recorded by the pods |
| R183–R185 | Maker-fill model: what fraction of signals could have been filled at the passive price, and what that does to PF |
| R186–R188 | Latency sensitivity: re-run promoted cells with 5s/30s/120s entry delay |
| R189–R190 | Capacity: at what notional does the edge disappear given observed depth |

**Rule adopted from the COMS fleet (Mercury3 PART13, 2026-11-22):** every strategy
evaluated at sub-hourly frequency reports **gross / fees / net and the edge-to-cost ratio**.
If the fee line is larger than the gross line, it is a donation rather than a strategy, and
it is cheap to check. Measured here: 1h cells run edge/cost near 1.2 at best, against the
fleet's 3.0 bar.

**Rule adopted from the peer review (2026-11-22):** a scheduled runner supervises every
~60 minutes, so the bracket must also be *survivable across one supervision gap*. Every
cell must report `supervision_gap_s / median_hold_s` and
`bracket_width_bps / max_expected_move_over_gap`; a bracket narrower than the move the
market can make while nobody is watching is not a stop.

**Rule adopted from the live round (2026-11-22):** the bracket must be *reachable inside
the holding period*, or the risk model is fictional. The live smoke book used a 1.2×ATR
bracket (~120 bps on BTC 1h) with a 6-minute hold — the market moved 6 bps, so TP/SL never
fired and every trade resolved on the clock, guaranteeing "friction + noise". Every cell
must now report `expected_move_over_hold / bracket_width`; below ~0.5 the bracket is
decoration and the cell is not a strategy.

---

## P8 — Beta versus alpha (R191–R197)

| # | Round | Content |
|---|---|---|
| R191 | Reproduce the peer table: SPY B&H, AOA, 60/40, SPY+200d overlay, GIC — one script, one window |
| R192 | Reconcile the three disputed rows (SPY terminal value, max DD, trend overlay) |
| R193 | Add the crypto equivalent: BTC B&H vs BTC+trend overlay |
| R194 | Risk-adjusted comparison across classes on real returns, net of fees |
| R195 | Drawdown-survival table: what a holder actually had to sit through |
| R196 | State which is better for the *user's* stated tolerance, with the cost of each |
| R197 | Beta/alpha verdict |

---

## P9 — Verdict (R198–R200)

| # | Round | Content |
|---|---|---|
| R198 | `VERDICT_200.md`: per class, `PROVEN` / `CANDIDATE` / `DEAD` / `UNMEASURABLE` with the gate that decided it |
| R199 | Capital allocation memo: what may be funded, at what size, with what kill switch and what review date |
| R200 | Reproducibility pack: one command that rebuilds every number quoted in the verdict |

---

## Cross-check protocol (runs alongside every phase)

Peers are working the same repo. Each round therefore also does:

1. `git log --since` for peer commits touching `reports/`, `updates/`, `realtime_challenge/`
2. Read their verdict doc; reconcile against mine on **one shared script**, not two
3. Record disagreements in `PEERCROSSCHECK_deepseek-flash.md` with the numbers side by side
4. Never overwrite a peer's file; add a dated reconciliation section instead
5. Log to the fleet bus (`redis-bus/agent_bus.py`) before starting work on a shared file

---

## What would make me abandon this plan

- If by R100 no cell clears DSR 0.95 at the then-current trial count, the honest answer is
  that this parameter space has no edge and the remaining rounds convert to P8/P9 only.
- If forward pods at n≥100 show selection alpha with a CI entirely below zero, every
  trading book is retired and the deliverable becomes the allocation memo.
- If the harness certification (P0) cannot be completed, nothing downstream is publishable.

## Standing disclaimer

Nothing here is financial advice. Every number is a measurement of a paper experiment.
No real order is ever sent by this code.
