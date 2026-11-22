#!/usr/bin/env python3
"""One non-interactive forward-pod pass. Designed for a GitHub Actions cron.

Each invocation:
  1. loads the persistent ledger for the run_id
  2. marks every open position at live bid/ask
  3. closes anything that has met TP, SL, or its time stop   <- the TP/SL supervisor
  4. scans the pre-registered book and opens at most `max_new` positions
  5. writes a heartbeat and a state snapshot, then exits 0

It exits 0 even when nothing happened (an empty pass is a valid observation), but it
exits non-zero if the exchange is unreachable, so a red workflow means a real problem
rather than a quiet one.

  python -m realtime_challenge.worker.forward_supervisor --book pod_a --max-new 2
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from .. import data as D
from ..live import DEFAULT_UNIVERSE, LiveRound, _quote, scan_signals

STATE = Path(__file__).resolve().parent.parent / "state"
RESULTS = Path(__file__).resolve().parent.parent / "results"


# Venue preference order. Cloud IP ranges (GitHub Actions runs on Azure US) are
# blocked by several exchanges: Bybit and OKX refuse US datacentre traffic, Binance
# restricts US IPs. Kraken and Coinbase accept it. The supervisor therefore probes in
# this order and uses the first venue that actually answers, then RECORDS which one it
# used so a run is never ambiguous about its price source.
VENUE_ORDER = ["kraken", "coinbase", "bybit", "okx", "binance"]


def pick_venue(preferred: str, universe, attempts: int = 2):
    """Return (venue, marks) for the first venue that answers with live quotes.

    Probes a SINGLE symbol first, so a geo-blocked venue costs ~2 seconds rather than
    len(universe) x retries. Only a venue that passes the probe is asked for the rest.
    """
    order = [preferred] + [v for v in VENUE_ORDER if v != preferred]
    errors = []
    for venue in order:
        probe = None
        for attempt in range(attempts):
            probe = _quote(venue, universe[0])
            if probe:
                break
            time.sleep(1.0)
        if not probe:
            errors.append(f"{venue}: probe failed")
            continue
        marks = {universe[0]: probe}
        for base in universe[1:]:
            q = _quote(venue, base)
            if q:
                marks[base] = q
        if len(marks) >= max(3, len(universe) // 2):
            return venue, marks
        errors.append(f"{venue}: {len(marks)}/{len(universe)} quotes")
    raise SystemExit("no venue returned quotes — treating as an outage. " + " | ".join(errors))


def one_pass(book: str, run_id: str, venue: str, max_open: int, max_new: int,
             min_votes: int, poll_cash: float, allow_failover: bool = True) -> dict:
    r = LiveRound(
        run_id=run_id, venue=venue, universe=DEFAULT_UNIVERSE,
        starting_cash=poll_cash, max_open=max_open,
    )

    # 1. live marks (with venue failover)
    if allow_failover:
        venue, marks = pick_venue(venue, r.universe)
        r.venue = venue
    else:
        marks = {}
        for base in r.universe:
            q = _quote(venue, base)
            if q:
                marks[base] = q
        if not marks:
            raise SystemExit(f"venue {venue} returned no quotes — treating as an outage")

    # 2. + 3. TP / SL / time-stop supervisor
    closed = r.check_exits(marks)

    # 4. open new positions (pre-registered consensus book)
    opened = []
    if book == "pod_a" and len(r.ledger.open_positions) < max_open:
        sigs = scan_signals(venue, r.universe, "1h")
        new_left = max_new
        for base, info in sigs.items():
            if new_left <= 0 or len(r.ledger.open_positions) >= max_open:
                break
            if base in r.ledger.open_positions or "error" in info:
                continue
            votes = [v["signal"] for v in info["strategies"].values() if v.get("signal")]
            if len(votes) < min_votes or len({v > 0 for v in votes}) != 1:
                continue
            d = 1 if sum(votes) > 0 else -1
            ev = r.try_open(base, d, f"consensus={votes}")
            if ev:
                opened.append(base)
                new_left -= 1

    equity = r.ledger.equity({b: q.get("bid") or q.get("last") for b, q in marks.items()})
    summary = r.ledger.summary()
    summary["pass"] = {
        "ts_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "venue": venue,
        "closed_this_pass": [
            {"symbol": c["symbol"], "reason": c["exit_reason"], "pnl": c["pnl"],
             "ret_pct": c.get("ret_pct"), "held_minutes": c.get("held_minutes")}
            for c in closed
        ],
        "opened_this_pass": opened,
        "marks": {b: q.get("bid") for b, q in marks.items()},
        "equity": round(equity, 2),
    }
    r.ledger.append({"event": "PASS", **summary["pass"]})
    r.ledger.save_state(summary)
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / f"{run_id}_summary.json").write_text(json.dumps(summary, indent=1, default=str), encoding="utf-8")
    return summary


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--book", default="pod_a", choices=["pod_a", "none"])
    ap.add_argument("--run-id", default="pod_a_crypto_1h")
    ap.add_argument("--venue", default="bybit")
    ap.add_argument("--max-open", type=int, default=4)
    ap.add_argument("--max-new", type=int, default=2)
    ap.add_argument("--min-votes", type=int, default=2)
    ap.add_argument("--cash", type=float, default=10000.0)
    ap.add_argument("--no-failover", action="store_true")
    args = ap.parse_args(argv)

    s = one_pass(args.book, args.run_id, args.venue, args.max_open, args.max_new,
                 args.min_votes, args.cash, allow_failover=not args.no_failover)
    print(json.dumps(s, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
