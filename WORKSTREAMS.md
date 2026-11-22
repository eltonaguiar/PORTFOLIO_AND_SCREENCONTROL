# WORKSTREAMS — who owns what, so two sessions don't duplicate or collide

Two agent sessions work this repository concurrently and each has a scheduled job. This file
is the boundary. **It is append-only and owner-neutral — add your section, never rewrite
another session's.**

Last confirmed: 2026-11-22 10:50 EST.

---

## The split

| | Session A (clone `C:/Users/zerou/repos/PORTFOLIO_AND_SCREENCONTROL`) | Session B (clone `C:/Users/zerou/pasc`) |
|---|---|---|
| **Axis** | **Build + tracking** — kernel implementation, static gates, backlog, index | **Empirical verification** — run the proofs, falsify claims, decide verdicts |
| Cron jobs | `pasc-index-sync` (180m, script-only) · `pasc-progress` (180m, agent) | `PASC repo continuous update` (360m, agent) |
| Files it writes | `NEXT_STEPS.md`, `PROGRESS_LOG.md`, `TRACKING.md`, `scripts/`, `STATIC_GATE_AUDIT.md`, `kernel/` under `01-screen-control-llm/` | `REVIEWS/*`, `03-trading-strategies/{TIMEFRAME_MATRIX,ETF_ROTATION_H-E1,HARNESS_CERTIFICATION,PEERCROSSCHECK_deepseek-flash,PROGRESS}.md`, `03-trading-strategies/realtime_challenge/**`, `results/`, `ledger/` |
| Does **not** touch | `REVIEWS/`, the harness, any verdict document | `NEXT_STEPS.md`, `PROGRESS_LOG.md`, `TRACKING.md`, `scripts/`, `kernel/` |

Both push to `origin/main` on disjoint paths, so a merge is a no-op rather than a conflict.

---

## Why the split is this way

**Session A is building the thing. Session B is trying to break it.**

Session A implements `kernel/capture.py`, `resolve.py`, `act.py`, `overseer.py` and keeps the
backlog machine-readable. That work is additive and sequential — one file at a time, with a
definition of done.

Session B's output is subtractive: it takes a claim (a peer's, a dashboard's, or its own) and
tries to falsify it against an artifact. Its products are negative results, gate verdicts and
corrected numbers. That work is not sequential and cannot live in a backlog, because the whole
point is that you do not know in advance which claim will fail.

Two sessions doing verification and two doing construction would duplicate each other. One of
each does not.

---

## Standing rules for both

1. **Never rewrite the other session's files.** Append a dated, agent-named section.
2. **Never tick a box in `NEXT_STEPS.md` you did not verify.** Same rule as the backlog's own
   header.
3. **A number needs its artifact.** If a claim in either session's docs is not backed by a file
   in `results/`, `ledger/`, or a commit, it is an opinion.
4. **If you find a defect in the other session's area, hand it over on COMS rather than
   patching it.** Two agents editing one file produces two divergent fixes.
5. **The standing verdict is shared and unchanged:** no asset class is proven profitable.
   126 cells, 0 above deflated Sharpe 0.95, 0 beating the permutation control, 0 of 29
   surviving BH-corrected random-entry testing. Neither session may soften that without a new
   artifact.

---

## Session B — current backlog (Session A's lives in `NEXT_STEPS.md`)

| # | item | status |
|---|---|---|
| 1 | Random-entry control with Benjamini–Hochberg correction | **done** — 0 of 29 survive (v1 had a per-cell label that manufactured findings; caught and fixed) |
| 2 | `market_clock.py` — refuse to trade a closed class | **done** |
| 3 | Outcome taxonomy (PROFIT/LOSS/NO_SIGNAL/DATA_UNAVAILABLE/MARKET_CLOSED/STALE_DATA/INCONCLUSIVE) | **done** |
| 4 | Decay alarm (rolling 20-trade Sharpe < 0) | **done** |
| 5 | Numeric G1/G2 gate thresholds | **done** — in `ROADMAP_200` |
| 6 | Walk-forward harness (the gate that has never been run here) | **next** |
| 6a | Live-round accounting: always read `n_open == 0` before quoting a P&L (session 1 understated the probe loss 2x by reading a running process) | **done** — rule in PROGRESS session 3 |
| 7 | Re-run the crypto census with a real walk-forward split | pending |
| 8 | FX class census — opens 17:00 EST Sunday, measurable from tonight | pending |
| 9 | Equity single-name and ETF factor set beyond H-E1 | pending |
| 10 | Reconcile the trend-overlay discrepancy for R191–R192 on one shared script | pending |
