#!/usr/bin/env python3
"""P9 — live perp/spot carry round-trip series.

Measures, for each crypto major, the carry available from one funding interval
of a perpetual swap versus spot, and the round-trip cost of opening + closing
the perp leg. One JSON line per symbol per run is appended to
results/carry_roundtrip.jsonl so the series accumulates over scheduled runs.

Public endpoints only: spot ticker, perp funding rate, order-book top. No API
keys, no orders, no positions — this is a measurement, not a trade.

  cd 03-trading-strategies
  python -m realtime_challenge.proof.carry_roundtrip   # one tick, 7 majors, appends
  python -m realtime_challenge.proof.carry_series      # recompute running median + n

Mercury3 measured a 42.64 bp median round trip (n = 5, ~94% fees) on one
snapshot. This series repeats that measurement over time so the mean and the
trend — not just the floor — are observable.

Output line (one per symbol per tick):

  ts, venue, symbol, spot_symbol — when/where/what
  spot, mark, index, basis_bps — perp vs spot deviation at this tick
  funding_interval_hours, funding_rate, funding_bps, funding_annualized_bps — carry per interval
  spread_bps, taker_fee_bps, roundtrip_cost_bps — cost to open + close the perp leg
  carry_net_bps = funding_bps − roundtrip_cost_bps — net per one-interval hold
  next_funding_ts, seconds_to_next_funding — when the next payment lands
  ok, error, source — line validity and provenance
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import ccxt

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "results" / "carry_roundtrip.jsonl"

# 7 majors, same universe as the P8 FX census so the two class measurements are
# comparable. Perp = USDT-M swap quoted against USDT spot.
SYMBOLS = ["BTC", "ETH", "SOL", "XRP", "ADA", "DOGE", "LINK"]

# Published venue defaults (binance USDT-M, non-VIP tier). A scheduled run can
# only read public endpoints, so the fee line is a disclosed constant, not a
# measured fill. Round-trip cost = 2 x taker + one full spread crossing.
VENUES = {
    "binance": {
        "interval_hours": 8.0,        # funding pays at 08:00 / 16:00 / 00:00 UTC
        "taker_fee_bps": 5.0,         # published USDT-M taker, default tier
        "spot": lambda base: f"{base}/USDT",
        "perp": lambda base: f"{base}/USDT:USDT",
    },
}


def measure_one(exchange: ccxt.Exchange, venue: str, cfg: dict, base: str) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    try:
        spot_symbol = cfg["spot"](base)
        perp_symbol = cfg["perp"](base)

        t_spot = exchange.fetch_ticker(spot_symbol)
        fr = exchange.fetch_funding_rate(perp_symbol)
        ob = exchange.fetch_order_book(perp_symbol, limit=5)

        info = fr.get("info") or {}
        spot = float(t_spot.get("last") or t_spot.get("close") or 0)
        mark = float(fr.get("markPrice") or info.get("markPrice") or spot)
        index = float(info.get("indexPrice") or spot)
        basis_bps = (mark / index - 1.0) * 1e4

        rate = float(
            fr.get("lastFundingRate")
            or info.get("lastFundingRate")
            or info.get("fundingRate")
            or 0.0
        )
        interval_hours = float(cfg["interval_hours"])
        funding_bps = rate * 1e4                      # paid by the long, per interval
        funding_annualized_bps = funding_bps * (8760.0 / interval_hours)

        bid = float(ob["bids"][0][0])
        ask = float(ob["asks"][0][0])
        mid = (bid + ask) / 2.0
        spread_bps = (ask - bid) / mid * 1e4 if mid > 0 else None

        taker = float(cfg["taker_fee_bps"])
        roundtrip_cost_bps = 2.0 * taker + (spread_bps or 0.0)
        carry_net_bps = funding_bps - roundtrip_cost_bps   # short perp collects funding when rate > 0

        next_funding = info.get("nextFundingTime")
        secs_to_next = None
        if next_funding is not None:
            secs_to_next = round((int(next_funding) - time.time() * 1000) / 1000.0, 1)

        return {
            "ts": now,
            "venue": venue,
            "symbol": perp_symbol,
            "spot_symbol": spot_symbol,
            "spot": round(spot, 6),
            "mark": round(mark, 6),
            "index": round(index, 6),
            "basis_bps": round(basis_bps, 4),
            "funding_interval_hours": interval_hours,
            "funding_rate": round(rate, 10),
            "funding_bps": round(funding_bps, 4),
            "funding_annualized_bps": round(funding_annualized_bps, 4),
            "next_funding_ts": int(next_funding) if next_funding is not None else None,
            "seconds_to_next_funding": secs_to_next,
            "spread_bps": round(spread_bps, 4) if spread_bps is not None else None,
            "taker_fee_bps": taker,
            "roundtrip_cost_bps": round(roundtrip_cost_bps, 4),
            "carry_net_bps": round(carry_net_bps, 4),
            "carry_received_by_short_bps": round(funding_bps, 4),
            "ok": True,
            "error": None,
            "source": "public endpoints only; no orders sent",
        }
    except Exception as exc:  # one symbol must not kill the tick
        return {
            "ts": now,
            "venue": venue,
            "symbol": f"{base}/USDT:USDT",
            "spot_symbol": f"{base}/USDT",
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
            "source": "public endpoints only; no orders sent",
        }


def main() -> int:
    ap = argparse.ArgumentParser(description="Measure one live carry round-trip tick across the majors")
    ap.add_argument("--venue", default="binance", choices=list(VENUES))
    ap.add_argument(
        "--symbols",
        default=",".join(SYMBOLS),
        help="comma-separated base symbols, e.g. BTC,ETH",
    )
    ap.add_argument(
        "--out",
        default=str(DEFAULT_OUT),
        help="JSONL path to append one line per symbol per tick",
    )
    args = ap.parse_args()

    if args.venue not in VENUES:
        print(f"unknown venue {args.venue}", file=sys.stderr)
        return 2

    cfg = VENUES[args.venue]
    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    exchange = ccxt.binance({"enableRateLimit": True})

    n_ok = 0
    with out_path.open("a", encoding="utf-8") as fh:
        for base in symbols:
            line = measure_one(exchange, args.venue, cfg, base)
            fh.write(json.dumps(line, separators=(",", ":")) + "\n")
            fh.flush()
            if line["ok"]:
                n_ok += 1
                print(
                    f"{line['ts']} {base}: funding {line['funding_bps']:+.2f} bp/interval "
                    f"roundtrip {line['roundtrip_cost_bps']:.2f} bp "
                    f"carry_net {line['carry_net_bps']:+.2f} bp"
                )
            else:
                print(f"{line['ts']} {base}: FAILED {line['error']}", file=sys.stderr)

    print(f"wrote {n_ok}/{len(symbols)} lines to {out_path}")
    return 0 if n_ok > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
