#!/usr/bin/env python3
"""P9 — recompute the carry series from the accumulated JSONL.

Reads results/carry_roundtrip.jsonl (one line per symbol per tick, appended by
carry_roundtrip.py) and publishes:

  results/carry_series_summary.json — n, running median, min/max for the
      round-trip cost and the net carry, overall and per symbol, plus the
      first/last tick of the series.

The headline number the fleet can quote: running median of roundtrip_cost_bps
with n — this is the measurement comparable to Mercury3's 42.64 bp median
round trip (n = 5, ~94% fees). carry_net_bps is this repo's own live carry
estimate per one funding interval; it is not forced to match any snapshot.

  cd 03-trading-strategies
  python -m realtime_challenge.proof.carry_series
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_IN = ROOT / "results" / "carry_roundtrip.jsonl"
DEFAULT_OUT = ROOT / "results" / "carry_series_summary.json"

MERCURY3_SNAPSHOT_BPS = 42.64
MERCURY3_SNAPSHOT_N = 5


def load(path: Path) -> list[dict]:
    rows: list[dict] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def stats(values: list[float]) -> dict:
    if not values:
        return {"n": 0}
    vs = sorted(values)
    return {
        "n": len(vs),
        "median": round(median(vs), 4),
        "min": round(min(vs), 4),
        "max": round(max(vs), 4),
    }


def recompute(rows: list[dict]) -> dict:
    ok = [r for r in rows if r.get("ok") is True]
    costs = [r["roundtrip_cost_bps"] for r in ok if isinstance(r.get("roundtrip_cost_bps"), (int, float))]
    nets = [r["carry_net_bps"] for r in ok if isinstance(r.get("carry_net_bps"), (int, float))]
    fundings = [r["funding_bps"] for r in ok if isinstance(r.get("funding_bps"), (int, float))]

    by_symbol: dict[str, dict] = {}
    for r in ok:
        sym = r["symbol"]
        by_symbol.setdefault(sym, {"costs": [], "nets": [], "fundings": []})
        if isinstance(r.get("roundtrip_cost_bps"), (int, float)):
            by_symbol[sym]["costs"].append(r["roundtrip_cost_bps"])
        if isinstance(r.get("carry_net_bps"), (int, float)):
            by_symbol[sym]["nets"].append(r["carry_net_bps"])
        if isinstance(r.get("funding_bps"), (int, float)):
            by_symbol[sym]["fundings"].append(r["funding_bps"])

    per_symbol = {}
    for sym, buckets in sorted(by_symbol.items()):
        per_symbol[sym] = {
            "roundtrip_cost_bps": stats(buckets["costs"]),
            "carry_net_bps": stats(buckets["nets"]),
            "funding_bps": stats(buckets["fundings"]),
        }

    timestamps = [r["ts"] for r in ok if r.get("ts")]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": str(DEFAULT_IN.relative_to(ROOT)),
        "reference": {
            "note": "Mercury3 snapshot: 42.64 bp median round trip, n = 5, ~94% pure fees. "
                    "This repo's series is a separate live measurement; not forced to match.",
            "mercury3_median_roundtrip_bps": MERCURY3_SNAPSHOT_BPS,
            "mercury3_n": MERCURY3_SNAPSHOT_N,
        },
        "ticks_total": len(rows),
        "ticks_ok": len(ok),
        "symbols": sorted({r["symbol"] for r in ok}),
        "roundtrip_cost_bps": stats(costs),
        "carry_net_bps": stats(nets),
        "funding_bps": stats(fundings),
        "carry_positive_frac": round(sum(1 for v in nets if v > 0) / len(nets), 4) if nets else None,
        "per_symbol": per_symbol,
        "first_ts": min(timestamps) if timestamps else None,
        "last_ts": max(timestamps) if timestamps else None,
    }


def main() -> int:
    rows = load(DEFAULT_IN)
    summary = recompute(rows)
    DEFAULT_OUT.parent.mkdir(parents=True, exist_ok=True)
    with DEFAULT_OUT.open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
        fh.write("\n")

    rc = summary["roundtrip_cost_bps"]
    net = summary["carry_net_bps"]
    print(
        f"carry series: n={rc['n']} ticks "
        f"median roundtrip cost {rc['median']:+.2f} bp "
        f"(range {rc['min']:+.2f}..{rc['max']:+.2f}) | "
        f"median net carry {net['median']:+.2f} bp (n={net['n']}) | "
        f"{summary['first_ts']} -> {summary['last_ts']}"
    )
    print(f"wrote {DEFAULT_OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
