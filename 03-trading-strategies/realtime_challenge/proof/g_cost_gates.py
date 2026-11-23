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
G-COST-3 | is the 1D cost premium real? recompute on one instrument (fixed:
         | names instrument, venue and horizon basis; was firing on regime,
         | not on the claim — see A9 / HORIZON_LADDER_A9.md)
         | kill the +24.21 bp figure if 1D cost > 24.21 bp or < 19 bp
G-COST-4 | vol-target gap decomposition (2.3 vs 10.7 bp/day) on one instrument
         | kill the vol-target overlay if the gap persists > 5 bp/day after 20 sessions
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


def gate_g_cost_3(exchange, taker_fee_bps: float) -> dict:
    """G-COST-3 (fixed): is the 1D cost premium real? recompute on one instrument.

    FIX vs A9 finding: the instrument (BTC/USDT spot), venue (Binance) and horizon
    basis (1 day, one round trip) are named, so the rule tests the claim at one
    defined regime instead of flipping with whichever venue is measured.
    Kill the +24.21 bp figure if 1D cost > 24.21 bp or < 19 bp.
    Independently (A9): the figure is already killed on unit/reproducibility
    grounds (no unit, no implementation, four documents quote it) — see
    HORIZON_LADDER_A9.md and realtime_challenge/proof/horizon_ladder.py.
    """
    kill_lo, kill_hi = 19.0, 24.21
    try:
        book = exchange.fetch_order_book(INSTRUMENT)
        mid = mid_price(book)
        spread_bps = (float(book["asks"][0][0]) - float(book["bids"][0][0])) / mid * 1e4
        one_day_cost_bps = spread_bps + 2.0 * taker_fee_bps
        measurable = True
    except Exception as exc:  # noqa: BLE001
        one_day_cost_bps = None
        measurable = False

    # Doc sweep: does any tracked file still assert the figure as a live claim?
    import subprocess

    quoted_files: list[str] = []
    try:
        output = subprocess.run(
            ["git", "grep", "-l", "24\\.21", "--", "*.md"],
            capture_output=True, text=True, check=False,
        ).stdout
        excluded = {
            "04-investment-strategy/TODO_2026-11-23.md",
            "03-trading-strategies/HORIZON_LADDER_A9.md",
            "03-trading-strategies/realtime_challenge/proof/horizon_ladder.py",
        }
        quoted_files = [
            f for f in output.splitlines()
            if f and not any(f.endswith(ex) or ex in f for ex in excluded)
        ]
    except Exception:  # noqa: BLE001
        quoted_files = ["grep unavailable"]

    cost_test_fires = measurable and (one_day_cost_bps > kill_hi or one_day_cost_bps < kill_lo)
    verdict = "KILL" if cost_test_fires else "PASS"
    note = (
        f"measured 1D round-trip cost {one_day_cost_bps:.3f} bp at {VENUE_NAME} {INSTRUMENT} "
        f"(1 day basis); kill range [{kill_lo}, {kill_hi}] bp — "
        f"{'cost test fires' if cost_test_fires else 'cost test does not fire'}. "
        "The +24.21 bp figure is independently dead on A9 grounds "
        "(unit unstated, gross/net unstated, no implementation); this gate now guards "
        "its resurrection at the named venue/basis."
    )
    if quoted_files:
        note += f" Figure still quoted in tracked files: {', '.join(quoted_files)} (coordinated edit pending, not made here)."
    return {
        "gate": "G-COST-3",
        "instrument": INSTRUMENT,
        "venue": VENUE_NAME,
        "horizon_basis": "1 day, one round trip (named instrument, venue, basis)",
        "n": 1 if measurable else 0,
        "threshold": {"kill_if_cost_bps_gt": kill_hi, "kill_if_cost_bps_lt": kill_lo},
        "measured": {"one_day_cost_bps": round(one_day_cost_bps, 3) if measurable else None},
        "verdict": verdict,
        "evidence": note,
        "kill_range_bps": [kill_lo, kill_hi],
        "a9_kill_grounds": "unit unstated (per trade vs per day, 365x), gross/net unstated, no implementation in either repo",
        "fee": {"per_side_bps": taker_fee_bps, "source": FEE_URL, "fetch_date": now_utc()[:10]},
    }


def gate_g_cost_4(exchange) -> dict:
    """G-COST-4: vol-target gap decomposition on one instrument.
    Kill the vol-target overlay if the gap persists > 5 bp/day after 20 sessions.
    """
    try:
        ohlcv = exchange.fetch_ohlcv(INSTRUMENT, "1h", limit=480)
    except Exception as exc:  # noqa: BLE001
        return {
            "gate": "G-COST-4",
            "instrument": INSTRUMENT,
            "venue": VENUE_NAME,
            "horizon_basis": "1 day sessions, 1h bars, BTC/USDT",
            "n": 0,
            "threshold": {"kill_if_gap_bps_per_day_gt": 5.0, "min_sessions": 20},
            "measured": {"gap_bps_per_day": None},
            "verdict": "UNMEASURABLE",
            "evidence": "OHLCV fetch failed",
        }
    closes = [float(row[4]) for row in ohlcv]
    # session = 24h return; use the last SESSIONS sessions
    rets = []
    for i in range(24, len(closes)):
        rets.append(closes[i] / closes[i - 24] - 1.0)
    rets = rets[-SESSIONS:]
    n = len(rets)
    if n < 20:
        return {
            "gate": "G-COST-4",
            "instrument": INSTRUMENT,
            "venue": VENUE_NAME,
            "horizon_basis": "1 day sessions, 1h bars, BTC/USDT",
            "n": n,
            "threshold": {"kill_if_gap_bps_per_day_gt": 5.0, "min_sessions": 20},
            "measured": {"gap_bps_per_day": None},
            "verdict": "UNMEASURABLE",
            "evidence": f"only {n} sessions available; need >= 20",
        }

    def mean_bp_day(series: list[float]) -> float:
        return statistics.mean(series) * 1e4

    bah_bp_day = mean_bp_day(rets)

    # Vol-targeted: scale exposure by target_vol / rolling realised vol, cap 1.0,
    # charge round-turn cost on scale changes (Binance spot taker ~10 bp/side).
    target_vol = 0.10
    window = 5
    rv = []
    for i in range(window - 1, len(rets)):
        seg = rets[i - window + 1:i + 1]
        mu = statistics.mean(seg)
        var = statistics.pvariance(seg)
        rv.append((var ** 0.5) * (24 * 365 ** 0.5))  # annualised approx
    scales = []
    for i in range(len(rv)):
        scale = min(1.0, target_vol / rv[i]) if rv[i] > 0 else 0.0
        scales.append(scale)
    scales = [0.0] + scales  # align: scale decided on past vol
    gross = [s * r for s, r in zip(scales, rets)]
    round_turn_cost = 0.0026  # project default model: 26 bp round turn
    net = [
        g - abs(scales[i] - scales[i - 1]) * round_turn_cost
        for i, g in enumerate(gross)
    ]
    vt_bp_day = mean_bp_day(net)
    gap = abs(vt_bp_day - bah_bp_day)
    verdict = "KILL" if gap > 5.0 else "PASS"
    return {
        "gate": "G-COST-4",
        "instrument": INSTRUMENT,
        "venue": VENUE_NAME,
        "horizon_basis": "1 day sessions, 1h bars, BTC/USDT; vol target 10% annualised, cap 1.0",
        "n": n,
        "threshold": {"kill_if_gap_bps_per_day_gt": 5.0, "min_sessions": 20},
        "measured": {
            "buy_and_hold_bps_per_day": round(bah_bp_day, 3),
            "vol_target_bps_per_day": round(vt_bp_day, 3),
            "gap_bps_per_day": round(gap, 3),
        },
        "verdict": verdict,
        "evidence": (
            f"over {n} sessions: buy-and-hold {bah_bp_day:.3f} bp/day vs vol-targeted "
            f"{vt_bp_day:.3f} bp/day, gap {gap:.3f} bp/day; "
            f"{'KILLS' if verdict == 'KILL' else 'within'} the 5 bp/day overlay limit"
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
    }
    report["overall"] = "KILL" if report["kills"] else ("UNMEASURABLE" if report["unmeasurable"] else "PASS")

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
