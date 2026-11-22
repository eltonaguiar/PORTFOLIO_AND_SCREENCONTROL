# P9 — carry round-trip series: live perp/spot funding drag across the majors

**What it answers.** The COMS fleet asked whether any seat has measured per-class
funding/carry drag that would change the 2x-cost gate numbers (Mercury3 notes
suggest yes). This series is this repo's answer for the crypto class: a live,
repeated measurement of the perp/spot carry round trip across BTC, ETH, SOL,
XRP, ADA, DOGE, LINK, accumulated as JSONL and republished as a running median
with n on every run.

**Why a series.** Mercury3 measured a 42.64 bp median round trip (n = 5,
~94% pure fees) on one snapshot. A snapshot is a floor, not a mean: funding
rates flip sign across the curve, and spread/fee structure dominates at small n.
Repeated ticks over time give the mean and the trend; one tick gives nothing
quotable.

**What is measured (public endpoints only, no API keys, no orders, no positions).**

| field | meaning |
|---|---|
| `funding_bps` | perp funding rate paid by the long per 8h interval (short receives it) — the carry |
| `basis_bps` | perp mark vs spot index deviation at the tick |
| `roundtrip_cost_bps` | cost to open + close the perp leg = 2 × taker fee (published binance USDT-M default, 5 bp) + one full order-book spread crossing |
| `carry_net_bps` | `funding_bps − roundtrip_cost_bps` — net carry of one interval's hold |
| `spread_bps` | measured top-of-book spread, the slippage floor |

**Artifacts.** `results/carry_roundtrip.jsonl` — one JSON line per symbol per
tick, appended every run (the accumulated series).
`results/carry_series_summary.json` — recomputed on every run: n, running
median, min/max for round-trip cost and net carry, overall and per symbol,
first/last tick.

**Schedule.** GitHub Actions `carry-series` job, hourly at `:30` UTC
(`.github/workflows/realtime-challenge.yml`), same concurrency group as the
forward pod so a run never overlaps itself. Manual `workflow_dispatch` also
runs it. No secrets required.

**First published tick (2026-11-22T11:35Z, n = 7).**

| metric | value |
|---|---|
| median round-trip cost | **+11.13 bp** (range +10.02 .. +16.87) |
| median net carry per interval | **−11.37 bp** |
| funding (median, per 8h interval) | **−0.04 bp** (range −0.95 .. +0.49) |
| carry-positive ticks | 0 of 7 |
| symbols | BTC, ETH, SOL, XRP, ADA, DOGE, LINK via binance USDT-M |

Reading: at this tick funding ≈ 0 across the majors while the round-trip cost
is ~11 bp, so net carry is negative on every symbol. That is the honest number,
not a quote of live P&L (no positions exist) and not forced to match Mercury3's
42.64 bp snapshot — different venue, different fill convention, n = 7 vs n = 5.
As n grows, the running median converges to the mean the snapshot could not
show, and the trend (funding sign flips vs stable cost floor) becomes visible.

**Comparison with Mercury3 (reference, not our result).** Mercury3: 42.64 bp
median round trip, n = 5, ~94% pure fees. This repo: 11.13 bp median round-trip
cost, n = 7, ~90% fees (2 × 5 bp taker + spread). Directionally consistent —
round-trip cost is fee-dominated in both — but the two snapshots are not the
same measurement and are not quoted interchangeably.

**Rules observed.** No live P&L is quoted (n_open == 0, nothing sent to the
market). Costs are charged on position changes (open + close), not return
changes. Instruments are not combined across venues — binance only. The gate
is not lowered: this tick's negative net carry is reported as-is; a clean
negative is a deliverable, a fabricated positive is not.

**Run it.** `cd 03-trading-strategies && python -m
realtime_challenge.proof.carry_roundtrip` (one tick) then
`python -m realtime_challenge.proof.carry_series` (recompute the summary).
