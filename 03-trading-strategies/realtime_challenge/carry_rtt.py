#!/usr/bin/env python3
"""Scheduled carry round-trip measurement — Mercury3's fleet ask.

Mercury3 measured the carry round trip once: **42.64 bp median, 94% pure fees, only 2.6 bp
slippage** (n=5 live books). Their own caveat, and the reason they asked the fleet:

    "One snapshot = a FLOOR not a mean."

This appends one line per pair per tick to a committed jsonl and reports the running median with
n, so the number becomes a distribution instead of an anecdote. It measures the two components
separately, because they behave differently:

  FEES     — deterministic per venue/account tier. Does not vary tick to tick; varies enormously
             across tiers (that is Mercury3's whole "conditional on fee tier" finding).
  SPREAD   — varies tick to tick and by size and by time of day. This is the part a time series
             actually helps with, and the part a single snapshot misreports.

Round-trip cost of crossing the book in and out:

    rtt_bps = 2 * (taker_fee_bps + half_spread_bps)

Both a spot and a perp reading are taken per symbol where the venue offers both, because carry
trades one against the other and the pair's cost is the sum, not either leg.

  python -m realtime_challenge.carry_rtt                 # measure once, append, print stats
  python -m realtime_challenge.carry_rtt --stats-only    # read the series, no network
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SERIES = ROOT / "ledger" / "carry_rtt_series.jsonl"

# Venue failover: bybit/okx refuse US datacentre IPs, so a run that dies on one venue must still
# produce a reading from the others rather than an empty tick.
VENUES = ["binance", "bybit", "okx", "kraken"]
BASKET = ["BTC", "ETH", "SOL", "XRP", "DOGE"]


def _perps_for(ex) -> dict[str, str]:
    """base -> perpetual symbol, for venues that expose swap markets."""
    out = {}
    try:
        for sym, m in ex.markets.items():
            if not m.get("swap"):
                continue
            base = m.get("base")
            if base and base not in out and m.get("linear", True):
                out[base] = sym
    except Exception:
        pass
    return out


def measure_venue(venue: str) -> list[dict]:
    import ccxt

    try:
        ex = getattr(ccxt, venue)({"enableRateLimit": True, "timeout": 12000})
        ex.load_markets()
    except Exception as exc:
        print(f"  [{venue}] unavailable: {type(exc).__name__}: {str(exc)[:70]}")
        return []

    perps = _perps_for(ex)
    rows = []
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    for base in BASKET:
        for kind, market in (("spot", f"{base}/USDT"), ("perp", perps.get(base))):
            if not market or market not in ex.markets:
                continue
            try:
                t = ex.fetch_ticker(market)
                bid, ask = t.get("bid"), t.get("ask")
                if not bid or not ask or ask <= bid:
                    continue
                mid = (bid + ask) / 2.0
                spread_bps = (ask - bid) / mid * 1e4
                m = ex.markets[market]
                taker = m.get("taker")
                if taker is None:
                    # fall back to the market's fee structure; do not invent a number
                    continue
                fee_bps = float(taker) * 1e4
                rtt = 2.0 * (fee_bps + spread_bps / 2.0)
                rows.append({
                    "ts_utc": now, "venue": venue, "kind": kind, "base": base,
                    "symbol": market, "bid": float(bid), "ask": float(ask),
                    "half_spread_bps": round(spread_bps / 2.0, 3),
                    "fee_bps_per_side": round(fee_bps, 3),
                    "rtt_bps": round(rtt, 3),
                    "fee_share": round(fee_bps / (fee_bps + spread_bps / 2.0), 3)
                    if (fee_bps + spread_bps / 2.0) > 0 else None,
                })
            except Exception:
                continue
    print(f"  [{venue}] {len(rows)} readings")
    return rows


def append(rows: list[dict]) -> int:
    SERIES.parent.mkdir(parents=True, exist_ok=True)
    with SERIES.open("a", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, separators=(",", ":")) + "\n")
    return len(rows)


def load() -> list[dict]:
    if not SERIES.exists():
        return []
    out = []
    for line in SERIES.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def stats(rows: list[dict]) -> dict:
    if not rows:
        return {"n": 0}
    by = {}
    for kind in ("spot", "perp"):
        xs = [r["rtt_bps"] for r in rows if r["kind"] == kind]
        if xs:
            by[kind] = {
                "n": len(xs),
                "median_rtt_bps": round(statistics.median(xs), 2),
                "min": round(min(xs), 2), "max": round(max(xs), 2),
                "median_fee_share": round(
                    statistics.median([r["fee_share"] for r in rows
                                       if r["kind"] == kind and r["fee_share"] is not None]), 3)
                if any(r["fee_share"] is not None for r in rows if r["kind"] == kind) else None,
            }
    # per venue, because fee tiers are per venue and that is the decision variable
    by_venue = {}
    for v in sorted({r["venue"] for r in rows}):
        xs = [r["rtt_bps"] for r in rows if r["venue"] == v]
        by_venue[v] = {"n": len(xs), "median_rtt_bps": round(statistics.median(xs), 2)}

    # spread-only trend: fees are constant, so any movement in rtt is the spread
    ticks = sorted({r["ts_utc"] for r in rows})
    per_tick = []
    for t in ticks:
        xs = [r["half_spread_bps"] for r in rows if r["ts_utc"] == t]
        if xs:
            per_tick.append({"ts_utc": t, "n": len(xs),
                             "median_half_spread_bps": round(statistics.median(xs), 3)})

    return {
        "n": len(rows), "ticks": len(ticks), "by_kind": by, "by_venue": by_venue,
        "half_spread_by_tick": per_tick,
        "first_tick": ticks[0] if ticks else None, "last_tick": ticks[-1] if ticks else None,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stats-only", action="store_true")
    a = ap.parse_args()

    rows = load()
    print(f"existing series: {len(rows)} readings, {len({r['ts_utc'] for r in rows})} ticks")

    if not a.stats_only:
        new = []
        for v in VENUES:
            new += measure_venue(v)
        if new:
            n = append(new)
            print(f"appended {n} readings -> {SERIES.relative_to(ROOT)}")
            rows += new
        else:
            print("NO VENUE RETURNED A READING — nothing appended. This is a data-availability "
                  "result, not a zero-cost result; do not record it as one.")
            return 1

    s = stats(rows)
    print(json.dumps(s, indent=1))

    if s.get("n"):
        p = s["by_kind"].get("perp") or {}
        spot = s["by_kind"].get("spot") or {}
        print(f"\nMERCURY3 COMPARISON: their single perp snapshot was 42.64bps median "
              f"(94% fees). Ours: perp {p.get('median_rtt_bps')}bps over n={p.get('n')}, "
              f"spot {spot.get('median_rtt_bps')}bps over n={spot.get('n')}.")
        if p.get("median_rtt_bps") and p["median_rtt_bps"] < 42.64:
            print("  -> BELOW their number. Likely a different fee tier or venue mix, which is "
                  "exactly the variable their own verdict is conditional on.")
        else:
            print("  -> AT OR ABOVE their number, consistent with a fee-dominated cost.")
        print(f"  fee share of the round trip: spot {spot.get('median_fee_share')}, "
              f"perp {p.get('median_fee_share')}  (Mercury3 measured 94%)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
