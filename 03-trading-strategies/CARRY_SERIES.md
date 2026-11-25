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

**Attribution audit (2026-11-25, Hermes — empirical verification).** The
`roundtrip_cost_bps` headline is **~90% an ASSUMED fee, not a measured cost**:
`roundtrip_cost_bps = 2 x taker_fee_bps + spread_bps`, and `taker_fee_bps` is a
hardcoded published *default-tier* constant in `carry_roundtrip.py` (5.0 bp on
okx/binance, 6.0 bp on bybit) — never a measured fill. On the current 532-row
series the median round trip is **11.13 bp = 10.0 bp assumed fee + 1.13 bp
measured top-of-book spread** (fee = 89.83%). This is the same fee-schedule
artefact corrected for G-COST-1, and it is why `CARRY_RTT_T4.md` reports fees
and spread separately. Two further corrections from the same audit:

- **Venue mix, not binance-only.** The series is 97.4% okx (binance 7, bybit 7,
  okx 518 rows); the summary pools venues *per symbol*, so per-symbol medians
  blend 5 bp (okx/binance) and 6 bp (bybit) taker tiers. The "binance only"
  claim below was true at the first n=7 tick and is false for the series.
- **The null is fee-driven, not funding-driven.** Net carry is negative on 0 of
  532 ticks, but with the taker fee set to zero (`funding_bps - spread_bps`) it
  is *positive* on 18.4% of ticks (BTC/okx: 94.6%, median +0.35 bp vs ~0.02 bp
  spread). So "funding ≈ 0 so carry is negative" mis-attributes it: the funding
  is small-positive on BTC/ETH and it is the ~10 bp taker fee that swamps it.
  Capturing that spread needs maker fills — A7 (KILO) records maker
  measurability as UNMEASURED. **KILL unchanged:** at any realistic taker fee
  the net is negative on every tick; no gate lowered. Artifact:
  `results/carry_series_attribution_audit_2026-11-25.json`.

**Comparison with Mercury3 (reference, not our result).** Mercury3: 42.64 bp
median round trip, n = 5, ~94% pure fees. This repo: 11.13 bp median round-trip
cost, n = 7, ~90% fees (2 × 5 bp taker + spread). Directionally consistent —
round-trip cost is fee-dominated in both — but the two snapshots are not the
same measurement and are not quoted interchangeably.

**Rules observed.** No live P&L is quoted (n_open == 0, nothing sent to the
market). Costs are charged on position changes (open + close), not return
changes. Instruments are **not held to a single venue**: the summary pools
whatever venue answered per symbol (failover bybit → okx → binance), so the
current series is okx-dominant and per-symbol medians are a cross-venue blend —
a provenance caveat, flagged in the attribution audit above. The gate
is not lowered: this tick's negative net carry is reported as-is; a clean
negative is a deliverable, a fabricated positive is not.

**Run it.** `cd 03-trading-strategies && python -m
realtime_challenge.proof.carry_roundtrip` (one tick) then
`python -m realtime_challenge.proof.carry_series` (recompute the summary).
