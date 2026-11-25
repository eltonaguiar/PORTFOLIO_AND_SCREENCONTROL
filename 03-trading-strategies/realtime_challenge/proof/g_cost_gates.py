#!/usr/bin/env python3
"""G-COST-1..4 — pre-registered cost-model validation gates (NEXT_STEPS.md Q4).

Purpose: a cost assumption cannot silently change. Every gate measures from
PUBLIC exchange endpoints only (ccxt, no API keys, no orders sent) and reports
PASS / KILL / UNMEASURABLE with instrument, venue and horizon basis named.

Run:  cd 03-trading-strategies && python -m realtime_challenge.proof.g_cost_gates
Writes: results/g_cost_gates_latest.json
Exit code: 0 if no gate KILLs, 1 if any gate KILLs (CI job fails fast).

G-COST-1 | median realised fill cost over >= 30 live fills, 15m horizon
         | kill the cost assumption if median >= 8.0 bp
G-COST-2 | slippage distribution on liquid pairs at 15m
         | kill if P50 > 8 bp or P90 > 20 bp
G-COST-3 | RECAST after A9: the "1D cost premium" is ILL-POSED, not merely noisy.
         | Per-round-trip cost is horizon-independent; only frequency multiplies
         | it. The old [19,24.21] bp band on the measured 1D cost is retired: a
         | ~10bp/side venue forces a PASS by construction (20 bp round-turn fee),
         | so it tested the fee schedule, not the claim. The gate now measures the
         | one well-defined quantity (round-trip cost on a named instrument/venue)
         | and reports the frequency ladder + dead-figure provenance. Verdict is
         | ILL-POSED (no falsifiable content) or UNMEASURABLE (book unreadable).
G-COST-4 | RECAST after A10 (2026-11-25): the blind |gap| kill rule was ILL-POSED
         | (a de-risked overlay always diverges from buy-and-hold when the asset
         | trends, in either sign). Now reports a NON-overlapping 24-session signed
         | decomposition with correct daily-vol annualisation (sqrt(365)); verdict
         | ILL-POSED (measurable) / UNMEASURABLE (book unreadable), no |gap| KILL.
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import ccxt

RESULTS = Path(__file__).resolve().parent.parent / "results"

# --- Named subjects (G-COST-3 fix: instrument, venue and horizon basis stated) ---
VENUE_ID = "binance"                 # ccxt venue id
VENUE_NAME = "Binance spot"
INSTRUMENT = "BTC/USDT"              # single named instrument (G-COST-3)
LIQUID_PAIRS = ["BTC/USDT", "ETH/USDT"]  # liquid pairs (G-COST-2)
NOTIONAL_USD = 5000.0                # book-walk notional per side (G-COST-2)
FILL_SNAPSHOTS = 36                  # >= 30 live fills (G-COST-1)
SESSIONS = 24                        # >= 20 sessions (G-COST-4)
FEE_URL = "https://www.binance.com/en/fee/schedule"

# --- Frequency ladder (A9 replacement claim: annual drag = freq x round_trip) ---
PERIODS_PER_YEAR = {"15m": 35040, "1h": 8760, "4h": 2190, "1D": 365, "1W": 52, "1M": 12}

# Files where the dead 24.21 figure may legitimately appear as a rule/definition
# rather than a live empirical claim (excluded from the provenance-risk list).
DEFINITIONAL_DOCS = {
    "NEXT_STEPS.md",                               # defines the kill rule itself
    "04-investment-strategy/TODO_2026-11-23.md",   # task list
    "03-trading-strategies/HORIZON_LADDER_A9.md",  # the retraction artifact
}


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def fetch_taker_fee_bps(exchange) -> tuple[float, str, str]:
    """Round-turn taker fee in bp with source; falls back to the published schedule."""
    fetch_date = now_utc()[:10]
    try:
        exchange.load_markets()
        fees = exchange.fetch_trading_fees()  # public endpoint, no keys
        entry = fees.get(INSTRUMENT) or fees.get("BTC/USDT") or {}
        taker = float(entry.get("taker", 0.001))
        if taker > 0:
            return taker * 1e4, f"ccxt fetch_trading_fees ({VENUE_NAME})", fetch_date
    except Exception as exc:  # noqa: BLE001 — public data is best effort
        pass
    return 10.0, f"published schedule assumed ({FEE_URL})", fetch_date


def mid_price(book: dict) -> float:
    return (float(book["bids"][0][0]) + float(book["asks"][0][0])) / 2.0


def book_walk_slippage_bps(book: dict, side: str, notional_usd: float, mid: float) -> float:
    """One-way slippage in bp of walking the book for notional_usd vs mid."""
    levels = book["asks"] if side == "buy" else book["bids"]
    remaining = notional_usd
    filled_qty = 0.0
    notional_spent = 0.0
    for price_str, amount_str in levels:
        price = float(price_str)
        amount = float(amount_str)
        level_notional = price * amount
        take_notional = min(level_notional, remaining)
        take_qty = take_notional / price
        notional_spent += take_notional
        filled_qty += take_qty
        remaining -= take_notional
        if remaining <= 1e-9:
            break
    if filled_qty <= 0:
        return float("nan")
    avg_price = notional_spent / filled_qty
    if side == "buy":
        return (avg_price - mid) / mid * 1e4
    return (mid - avg_price) / mid * 1e4


def gate_g_cost_1(exchange, taker_fee_bps: float) -> dict:
    """G-COST-1: median realised fill cost over >= 30 live fills, 15m horizon.
    Kill the cost assumption if median >= 8.0 bp.

    Proxy for a realised fill: live top-of-book spread (full round-turn spread)
    plus round-turn taker fee, sampled across live snapshots. No live account and
    no orders are sent, so this is a live-book measurement, not executed fills.
    """
    round_turn_fee_bps = 2.0 * taker_fee_bps
    samples: list[float] = []
    snapshots = 0
    errors = 0
    while snapshots < FILL_SNAPSHOTS and errors < 10:
        try:
            book = exchange.fetch_order_book(INSTRUMENT)
            mid = mid_price(book)
            spread_bps = (float(book["asks"][0][0]) - float(book["bids"][0][0])) / mid * 1e4
            samples.append(spread_bps + round_turn_fee_bps)
            snapshots += 1
        except Exception as exc:  # noqa: BLE001
            errors += 1
        if snapshots < FILL_SNAPSHOTS:
            time.sleep(0.6)
    n = len(samples)
    if n < 30:
        return {
            "gate": "G-COST-1",
            "instrument": INSTRUMENT,
            "venue": VENUE_NAME,
            "horizon_basis": "15m assumed fill cadence; cost per round trip",
            "n": n,
            "threshold": {"kill_if_median_bps_ge": 8.0},
            "measured": {"median_bps": None, "samples": samples},
            "verdict": "UNMEASURABLE",
            "evidence": f"only {n} of {FILL_SNAPSHOTS} live snapshots obtained ({errors} failures); need >= 30",
            "fee": {"per_side_bps": taker_fee_bps, "source": FEE_URL, "fetch_date": now_utc()[:10]},
        }
    median_bps = statistics.median(samples)
    verdict = "KILL" if median_bps >= 8.0 else "PASS"
    return {
        "gate": "G-COST-1",
        "instrument": INSTRUMENT,
        "venue": VENUE_NAME,
        "horizon_basis": "15m assumed fill cadence; cost per round trip",
        "n": n,
        "threshold": {"kill_if_median_bps_ge": 8.0},
        "measured": {
            "median_bps": round(median_bps, 3),
            "p90_bps": round(statistics.quantiles(samples, n=10)[8], 3),
            "min_bps": round(min(samples), 3),
            "max_bps": round(max(samples), 3),
        },
        "verdict": verdict,
        "evidence": (
            f"median realised fill cost {median_bps:.3f} bp over {n} live snapshots "
            f"at {VENUE_NAME} {INSTRUMENT}; "
            f"{'KILLS' if verdict == 'KILL' else 'holds against'} the 8.0 bp cost assumption"
        ),
        "fee": {"per_side_bps": taker_fee_bps, "source": FEE_URL, "fetch_date": now_utc()[:10]},
    }


def gate_g_cost_2(exchange, taker_fee_bps: float) -> dict:
    """G-COST-2: slippage distribution on liquid pairs at 15m.
    Kill if P50 > 8 bp or P90 > 20 bp.
    """
    samples: list[float] = []
    snapshots_per_pair = 16
    for pair in LIQUID_PAIRS:
        for _ in range(snapshots_per_pair):
            try:
                book = exchange.fetch_order_book(pair)
                mid = mid_price(book)
                buy_slip = book_walk_slippage_bps(book, "buy", NOTIONAL_USD, mid)
                sell_slip = book_walk_slippage_bps(book, "sell", NOTIONAL_USD, mid)
                samples.append(buy_slip + sell_slip)  # round-trip slippage
            except Exception:  # noqa: BLE001
                pass
            time.sleep(0.4)
    n = len(samples)
    if n < 30:
        return {
            "gate": "G-COST-2",
            "instrument": "/".join(LIQUID_PAIRS),
            "venue": VENUE_NAME,
            "horizon_basis": "15m; round-trip slippage of a $5,000 notional market order vs mid",
            "n": n,
            "threshold": {"kill_if_p50_bps_gt": 8.0, "kill_if_p90_bps_gt": 20.0},
            "measured": {"p50_bps": None, "p90_bps": None},
            "verdict": "UNMEASURABLE",
            "evidence": f"only {n} book walks obtained; need >= 30",
            "pairs": LIQUID_PAIRS,
        }
    ordered = sorted(samples)
    p50 = statistics.median(ordered)
    p90 = statistics.quantiles(ordered, n=10)[8]
    verdict = "KILL" if (p50 > 8.0 or p90 > 20.0) else "PASS"
    return {
        "gate": "G-COST-2",
        "instrument": "/".join(LIQUID_PAIRS),
        "venue": VENUE_NAME,
        "horizon_basis": "15m; round-trip slippage of a $5,000 notional market order vs mid",
        "n": n,
        "threshold": {"kill_if_p50_bps_gt": 8.0, "kill_if_p90_bps_gt": 20.0},
        "measured": {"p50_bps": round(p50, 3), "p90_bps": round(p90, 3)},
        "verdict": verdict,
        "evidence": (
            f"round-trip slippage P50={p50:.3f} bp P90={p90:.3f} bp over {n} walks "
            f"on {LIQUID_PAIRS} at {VENUE_NAME}; "
            f"{'KILLS' if verdict == 'KILL' else 'within'} the 8 bp / 20 bp thresholds"
        ),
        "pairs": LIQUID_PAIRS,
    }


def _frequency_ladder(round_trip_bps: float) -> tuple[dict, float, float]:
    """Annual cost drag at each horizon = periods_per_year * round_trip_bps.

    This is the A9 replacement claim. The *ratios* are structural (number of round
    trips per year), not market predictions: 15m/1D = 96.0, 1D/1M = ~30.4.
    """
    rows = {
        name: {
            "round_trips_per_year": per_year,
            "annual_drag_bps": round(per_year * round_trip_bps, 3),
        }
        for name, per_year in PERIODS_PER_YEAR.items()
    }
    ratio_15m_1d = PERIODS_PER_YEAR["15m"] / PERIODS_PER_YEAR["1D"]
    ratio_1d_1m = PERIODS_PER_YEAR["1D"] / PERIODS_PER_YEAR["1M"]
    return rows, ratio_15m_1d, ratio_1d_1m


def _provenance_sweep(repo_root: Path) -> tuple[list[str], bool]:
    """Tracked *.md files still quoting the dead 24.21 figure.

    Run from the REPO ROOT with repo-relative pathspecs so subdirectory docs
    (02-portfolio-multi-asset/, 04-investment-strategy/) are not silently missed —
    the previous cwd-relative '-- *.md' sweep found only 03-trading-strategies/*.md
    and even leaked the excluded A9 artifact because exclusion matched the wrong
    path prefix.
    """
    import subprocess

    try:
        output = subprocess.run(
            ["git", "grep", "-l", "24\\.21", "--", "*.md"],
            cwd=str(repo_root), capture_output=True, text=True, check=False,
        ).stdout
    except Exception:  # noqa: BLE001
        return ["grep unavailable"], False
    found = [f.strip() for f in output.splitlines() if f.strip()]
    return [f for f in found if f not in DEFINITIONAL_DOCS], True


def gate_g_cost_3(exchange, taker_fee_bps: float) -> dict:
    """G-COST-3 (RECAST): the "1D cost premium" is ILL-POSED, not merely noisy.

    A9 showed the old kill rule tested the cost REGIME, not the claim: it PASSed
    iff the measured round trip landed in [19, 24.21] bp, which is satisfied by any
    venue charging ~9.5-12.1 bp/side (round-turn fee alone is ~20 bp). The verdict
    was therefore a function of the published fee schedule, not of any property of
    a 1D horizon.

    The deeper defect: per-round-trip cost is horizon-INDEPENDENT. There is no
    "cost per trade" that differs between a 15m and a 1D hold; what differs is how
    often the same round trip is paid. annual_drag = (365/holding_days)*c_rt. So
    "the 1D cost premium" does not name a measurable quantity and cannot be tested
    by a threshold on c_rt. A9's replacement (96x 15m->1D, ~30x 1D->1M) is the
    frequency ratio, i.e. arithmetic, not a market prediction.

    This gate RETIRES the absolute-band kill predicate (it could never fail or pass
    on the claim) and instead measures the one well-defined quantity on the named
    instrument/venue, reports the frequency ladder, and records which tracked docs
    still quote the dead figure. Verdict: ILL-POSED when measurable (no
    falsifiable content remains), UNMEASURABLE if the book cannot be read. It does
    NOT emit PASS/KILL on the absolute band — doing so was the original defect.
    """
    kill_lo, kill_hi = 19.0, 24.21  # retained only as the historical band, for the record
    try:
        book = exchange.fetch_order_book(INSTRUMENT)
        mid = mid_price(book)
        spread_bps = (float(book["asks"][0][0]) - float(book["bids"][0][0])) / mid * 1e4
        round_trip_cost_bps = spread_bps + 2.0 * taker_fee_bps
        measurable = True
    except Exception:  # noqa: BLE001
        round_trip_cost_bps = None
        measurable = False

    repo_root = Path(__file__).resolve().parents[3]
    risk_docs, sweep_ok = _provenance_sweep(repo_root)

    if not measurable:
        return {
            "gate": "G-COST-3",
            "instrument": INSTRUMENT,
            "venue": VENUE_NAME,
            "horizon_basis": "1 day, one round trip (per-round-trip cost is horizon-independent)",
            "n": 0,
            "verdict": "UNMEASURABLE",
            "claim_tested": "1D cost premium is real and equals the +24.21 bp figure",
            "retired_predicate": "absolute band [19, 24.21] bp on the measured 1D cost",
            "evidence": "order book unreadable; no round-trip cost measured",
            "kill_range_bps": [kill_lo, kill_hi],
            "provenance": {"sweep_ok": sweep_ok, "docs_still_quoting": risk_docs},
        }

    ladder, ratio_15m_1d, ratio_1d_1m = _frequency_ladder(round_trip_cost_bps)

    # Why the old predicate was vacuous: with a 10bp/side fee the round-turn fee
    # alone (20 bp) sits inside [19, 24.21]; the acceptance window is really a
    # window on FEE PER SIDE, i.e. on the venue's published schedule.
    fee_lo = (kill_lo - spread_bps) / 2.0
    fee_hi = (kill_hi - spread_bps) / 2.0

    return {
        "gate": "G-COST-3",
        "instrument": INSTRUMENT,
        "venue": VENUE_NAME,
        "horizon_basis": "1 day, one round trip (per-round-trip cost is horizon-independent)",
        "n": 1,
        "measured": {
            "round_trip_cost_bps": round(round_trip_cost_bps, 3),
            "spread_bps": round(spread_bps, 4),
            "round_turn_fee_bps": round(2.0 * taker_fee_bps, 3),
        },
        "verdict": "ILL-POSED",
        "claim_tested": "1D cost premium is real and equals the +24.21 bp figure",
        "retired_predicate": "absolute band [19, 24.21] bp on the measured 1D cost",
        "retirement_reason": (
            "per-round-trip cost is horizon-independent; annual drag = (365/holding_days)*c_rt. "
            "A threshold on c_rt tests the venue fee schedule, not the claim: a ~10bp/side venue "
            "forces the old [19,24.21] PASS by construction."
        ),
        "frequency_ladder": ladder,
        "frequency_ratios": {
            "15m_over_1D": round(ratio_15m_1d, 4),
            "1D_over_1M": round(ratio_1d_1m, 4),
        },
        "old_predicate_accepts_fee_per_side_bps": [round(fee_lo, 3), round(fee_hi, 3)],
        "kill_range_bps": [kill_lo, kill_hi],
        "a9_kill_grounds": "unit unstated (per trade vs per day, 365x), gross/net unstated, no implementation in either repo",
        "provenance": {
            "sweep_ok": sweep_ok,
            "sweep_root": "repo root",
            "docs_still_quoting": risk_docs,
            "note": "coordinated multi-doc correction deferred per HORIZON_LADDER_A9.md; provenance is a documentation risk, not a cost signal",
        },
        "evidence": (
            f"measured round-trip cost {round_trip_cost_bps:.3f} bp at {VENUE_NAME} {INSTRUMENT} "
            f"(spread {spread_bps:.4f} + round-turn fee {2.0 * taker_fee_bps:.3f} bp). "
            f"'1D cost premium is real' is ILL-POSED: cost per trade does not vary with horizon; "
            f"the 15m->1D annual-cost ratio is the fixed frequency ratio {ratio_15m_1d:.1f}x and "
            f"1D->1M {ratio_1d_1m:.2f}x. The old [19,24.21] band accepts any fee/side in "
            f"[{fee_lo:.2f},{fee_hi:.2f}] bp — a fee-schedule artifact, not evidence. "
            f"Dead figure still quoted in {len(risk_docs)} tracked doc(s) outside its own definition."
        ),
        "fee": {"per_side_bps": taker_fee_bps, "source": FEE_URL, "fetch_date": now_utc()[:10]},
    }


def gate_g_cost_4(exchange) -> dict:
    """G-COST-4 (RECAST): the blind |gap| kill rule was ILL-POSED — retire it.

    The committed predicate had three independent defects:
      (B1) it built 24 hourly-SPACED samples of overlapping 24h returns — a ~2-day
           snapshot, not 24 daily sessions;
      (B2) it annualised a DAILY variance by 24*sqrt(365) instead of sqrt(365), a
           24x oversizing that shrank the vol-target scale ~24x and inflated the gap;
      (B3) it KILLed whenever |vol_target - buy_and_hold| > 5 bp/day regardless of
           sign. This is fatal: a directionally de-risked overlay MUST diverge from
           buy-and-hold whenever the asset trends (it gives up upside in rallies and
           loses less in crashes), so |gap| measures the asset move, not overlay
           quality. Proof: the same committed gate reported buy-and-hold +246.3 bp/day
           at 01:21Z (rally) and -255.2 bp/day at 10:11Z (crash), BOTH KILL — the sign
           of the underlying flipped while the verdict did not.

    This recast uses NON-overlapping daily returns over a real 24-session window,
    annualises daily vol by sqrt(365) (correct), reports the SIGNED overlay effect
    (report-only diagnostic, framework 2c), and carries no PASS/KILL on the retired
    |gap| band. Verdict: ILL-POSED (measurable) / UNMEASURABLE (book unreadable).
    """
    try:
        ohlcv = exchange.fetch_ohlcv(INSTRUMENT, "1h", limit=760)
    except Exception as exc:  # noqa: BLE001
        return {
            "gate": "G-COST-4",
            "instrument": INSTRUMENT,
            "venue": VENUE_NAME,
            "horizon_basis": "24 non-overlapping daily sessions, 1h bars resampled 24h, BTC/USDT",
            "n": 0,
            "threshold": {"retired_kill_if_abs_gap_bps_per_day_gt": 5.0, "min_sessions": 20},
            "measured": None,
            "verdict": "UNMEASURABLE",
            "evidence": f"OHLCV fetch failed: {exc}",
        }

    closes = [float(row[4]) for row in ohlcv]
    # NON-overlapping daily returns: advance one day (24 hourly bars) per step.
    daily = [closes[i] / closes[i - 24] - 1.0 for i in range(24, len(closes), 24)]
    daily = daily[-SESSIONS:]
    n = len(daily)
    if n < 20:
        return {
            "gate": "G-COST-4",
            "instrument": INSTRUMENT,
            "venue": VENUE_NAME,
            "horizon_basis": "24 non-overlapping daily sessions, 1h bars resampled 24h, BTC/USDT",
            "n": n,
            "threshold": {"retired_kill_if_abs_gap_bps_per_day_gt": 5.0, "min_sessions": 20},
            "measured": None,
            "verdict": "UNMEASURABLE",
            "evidence": f"only {n} non-overlapping daily sessions available; need >= 20",
        }

    def mean_bp_day(series: list[float]) -> float:
        return statistics.mean(series) * 1e4

    vol_target = 0.10
    window = 5
    round_turn_cost = 0.0026  # project default model: 26 bp round turn

    # Exposure for each day is decided from PAST realised vol only (no look-ahead):
    # daily vol annualised by sqrt(365) (the committed version multiplied by an
    # extra 24, shrinking scale ~24x — the B2 defect).
    scales: list[float] = []
    for i in range(len(daily)):
        if i < window:
            scales.append(0.0)
        else:
            seg = daily[i - window:i]
            r = (statistics.pvariance(seg) ** 0.5) * (365 ** 0.5)  # daily -> annual
            scales.append(min(1.0, vol_target / r) if r > 0 else 0.0)

    net: list[float] = []
    prev = 0.0
    for s, r in zip(scales, daily):
        net.append(s * r - abs(s - prev) * round_turn_cost)  # cost on scale change
        prev = s

    bah_bp_day = mean_bp_day(daily)
    vt_bp_day = mean_bp_day(net)
    signed_effect = vt_bp_day - bah_bp_day  # + overlay helped, - overlay lagged

    return {
        "gate": "G-COST-4",
        "instrument": INSTRUMENT,
        "venue": VENUE_NAME,
        "horizon_basis": "24 non-overlapping daily sessions, 1h bars resampled 24h, BTC/USDT; vol target 10% annualised (sqrt(365)), cap 1.0",
        "n": n,
        "threshold": {"retired_kill_if_abs_gap_bps_per_day_gt": 5.0, "min_sessions": 20},
        "measured": {
            "buy_and_hold_bps_per_day": round(bah_bp_day, 3),
            "vol_target_bps_per_day": round(vt_bp_day, 3),
            "signed_effect_bps_per_day": round(signed_effect, 3),
            "mean_scale": round(statistics.mean(scales), 4),
        },
        "verdict": "ILL-POSED",
        "retired_predicate": "kill if |vol_target - buy_and_hold| > 5 bp/day",
        "retirement_reason": (
            "|gap| is direction-blind: a de-risked overlay always diverges from buy-and-hold "
            "when the asset trends (gives up upside in rallies, loses less in crashes), so the "
            "predicate measures the asset move, not overlay quality. The committed code also "
            "used hourly-sampled overlapping returns (~2 days, not 24 sessions) and annualised "
            "daily vol by 24*sqrt(365) instead of sqrt(365), shrinking scale ~24x and inflating the gap."
        ),
        "diagnostic_note": "signed_effect is report-only (framework 2c: report, do not wire). Positive = vol-target beat buy-and-hold net; negative = it lagged. Window-dependent by construction.",
        "evidence": (
            f"over {n} non-overlapping daily sessions: buy-and-hold {bah_bp_day:.3f} bp/day vs "
            f"vol-targeted {vt_bp_day:.3f} bp/day (mean exposure {statistics.mean(scales):.3f}); "
            f"signed effect {signed_effect:+.3f} bp/day. The |gap| KILL rule is retired as ILL-POSED "
            f"(it measures the asset move, not the overlay)."
        ),
    }


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    exchange = ccxt.binance({"enableRateLimit": True})
    taker_fee_bps, fee_source, fee_date = fetch_taker_fee_bps(exchange)

    gates = [
        gate_g_cost_1(exchange, taker_fee_bps),
        gate_g_cost_2(exchange, taker_fee_bps),
        gate_g_cost_3(exchange, taker_fee_bps),
        gate_g_cost_4(exchange),
    ]

    report = {
        "generated_utc": now_utc(),
        "venue": VENUE_NAME,
        "venue_id": VENUE_ID,
        "fee_source": fee_source,
        "fee_fetch_date": fee_date,
        "gates": gates,
        "kills": [g["gate"] for g in gates if g["verdict"] == "KILL"],
        "passes": [g["gate"] for g in gates if g["verdict"] == "PASS"],
        "unmeasurable": [g["gate"] for g in gates if g["verdict"] == "UNMEASURABLE"],
        "retired": [g["gate"] for g in gates if g["verdict"] == "ILL-POSED"],
    }
    report["overall"] = (
        "KILL" if report["kills"]
        else ("UNMEASURABLE" if report["unmeasurable"] else ("RETIRED" if report["retired"] else "PASS"))
    )

    body = json.dumps(report, indent=1) + "\n"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    (RESULTS / f"g_cost_gates_{stamp}.json").write_text(body, encoding="utf-8")
    (RESULTS / "g_cost_gates_latest.json").write_text(body, encoding="utf-8")

    print(f"G-COST gates — {report['overall']}")
    for g in gates:
        m = g.get("measured", {})
        print(f"  {g['gate']}: {g['verdict']} | n={g.get('n')} | {g['evidence'][:160]}")
    if report["kills"]:
        print("KILL gates:", ", ".join(report["kills"]))
    print(f"wrote results/g_cost_gates_latest.json")
    return 1 if report["kills"] else 0


if __name__ == "__main__":
    sys.exit(main())
