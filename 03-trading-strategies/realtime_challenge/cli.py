#!/usr/bin/env python3
"""CLI for the realtime challenge.

  python -m realtime_challenge.cli backtest  --bars 3000 --timeframe 1h
  python -m realtime_challenge.cli backtest  --permutations 200
  python -m realtime_challenge.cli scan
  python -m realtime_challenge.cli live --minutes 30 --poll 20
  python -m realtime_challenge.cli status
"""

from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from . import data as D
from . import engine as E
from . import stats as ST
from . import strategies as S
from .costs import DEFAULT_COSTS, COST_GRID

RESULTS_DIR = Path(__file__).resolve().parent / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_BASES = ["BTC", "ETH", "SOL", "XRP", "DOGE", "ADA", "LINK"]


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def cmd_backtest(args) -> int:
    bases = args.bases or DEFAULT_BASES
    venue = args.venue
    tf = args.timeframe
    bars = args.bars
    ppy = {"1h": 24 * 365, "4h": 6 * 365, "1d": 365, "15m": 96 * 365, "5m": 288 * 365}[tf]

    print(f"fetching {len(bases)} symbols @ {tf} x {bars} bars from {venue} ...")
    panel = D.fetch_panel(venue, bases, tf, bars)
    print(f"  got {len(panel)} symbols; common window {next(iter(panel.values())).index[0]} -> {next(iter(panel.values())).index[-1]}")
    if not panel:
        return 2

    rows = []
    per_symbol_bh = {}
    for base, df in panel.items():
        per_symbol_bh[base] = E.buy_and_hold(df, DEFAULT_COSTS)

    total_trials = S.TRIAL_COUNT * len(panel)
    print(f"  registered hypotheses: {S.TRIAL_COUNT} x {len(panel)} symbols = {total_trials} cells")

    for name, cfg in S.REGISTRY.items():
        for base, df in panel.items():
            sig = cfg["fn"](df)
            res = E.run_from_signals(
                df, sig, name, base,
                tp_atr=cfg["tp_atr"], sl_atr=cfg["sl_atr"], max_bars=cfg["max_bars"],
                costs=DEFAULT_COSTS, timeframe=tf, allow_short=cfg["allow_short"],
            )
            s = ST.summarise(res.trades, res.equity_curve, ppy)
            exposure = getattr(res, "exposure_frac", 0.0)
            # A flat strategy in a falling market "beats" buy-and-hold by doing
            # nothing. Scale the benchmark by time-in-market so that credit is
            # not handed out for sitting out a drawdown.
            bh_scaled = per_symbol_bh[base]["total_return"] * exposure
            row = {
                "strategy": name, "family": cfg["family"], "symbol": base, "timeframe": tf,
                "n": s["n"], "win_rate": s["win_rate"], "profit_factor": s["profit_factor"],
                "expectancy_r": s["expectancy_r"], "total_return": s["total_return"],
                "max_drawdown": s["max_drawdown"], "sharpe_annual": s["sharpe_annual"],
                "mean_net": s["mean_net"], "mean_net_ci_lo": s["mean_net_ci_lo"],
                "mean_net_ci_hi": s["mean_net_ci_hi"], "exit_mix": s["exit_mix"],
                "exposure_frac": round(exposure, 4),
                "bh_return": per_symbol_bh[base]["total_return"],
                "bh_scaled_return": round(bh_scaled, 6),
                "excess_vs_bh": round((s["total_return"] or 0.0) - per_symbol_bh[base]["total_return"], 6),
                "excess_scaled": round((s["total_return"] or 0.0) - bh_scaled, 6),
            }
            if s["n"] >= 10:
                ds = ST.deflated_sharpe([t["net_ret"] for t in res.trades], n_trials=total_trials)
                row["dsr"] = ds.get("dsr")
                row["sr"] = ds.get("sr")
                row["sr0"] = ds.get("sr0")
            else:
                row["dsr"] = None; row["sr"] = None; row["sr0"] = None
            rows.append(row)
            if args.verbose:
                print(f"  {name:26s} {base:5s} n={row['n']:3d} pf={row['profit_factor']} "
                      f"exRet={row['excess_vs_bh']} dsr={row['dsr']}")

    # ---- cost sensitivity on the pooled trades of each strategy
    print("\ncost grid (pooled across symbols, mean net return per trade):")
    cost_rows = []
    for name, cfg in S.REGISTRY.items():
        for cm in COST_GRID:
            pooled = []
            for base, df in panel.items():
                sig = cfg["fn"](df)
                r = E.run_from_signals(df, sig, name, base, tp_atr=cfg["tp_atr"],
                                       sl_atr=cfg["sl_atr"], max_bars=cfg["max_bars"],
                                       costs=cm, timeframe=tf, allow_short=cfg["allow_short"])
                pooled += [t["net_ret"] for t in r.trades]
            if not pooled:
                continue
            cost_rows.append({
                "strategy": name, "round_turn_bps": round(cm.round_turn * 1e4, 1),
                "n": len(pooled), "mean_net_bps": round(float(sum(pooled) / len(pooled)) * 1e4, 2),
                "pf": None if ST.profit_factor(pooled) is None else round(ST.profit_factor(pooled), 3),
            })
            print(f"  {name:26s} {cm.round_turn*1e4:5.1f}bps n={len(pooled):4d} "
                  f"mean={cost_rows[-1]['mean_net_bps']:+8.2f}bps pf={cost_rows[-1]['pf']}")

    # ---- permutation control (one symbol per strategy: the most active)
    perm_rows = []
    if args.permutations > 0:
        print(f"\npermutation control ({args.permutations} shuffles each):")
        for name, cfg in S.REGISTRY.items():
            best = max(rows, key=lambda r: (r["strategy"] == name, r["n"]))
            cand = [r for r in rows if r["strategy"] == name and r["n"] >= 10]
            if not cand:
                perm_rows.append({"strategy": name, "note": "no cell with n>=10", "p_value": None})
                print(f"  {name:26s} skipped (no n>=10 cell)")
                continue
            target = max(cand, key=lambda r: r["n"])
            df = panel[target["symbol"]]
            pr = ST.permutation_control(
                df, cfg["fn"], n_perm=args.permutations,
                engine_kwargs=dict(tp_atr=cfg["tp_atr"], sl_atr=cfg["sl_atr"],
                                   max_bars=cfg["max_bars"], allow_short=cfg["allow_short"]),
            )
            pr["strategy"] = name
            pr["symbol"] = target["symbol"]
            perm_rows.append(pr)
            print(f"  {name:26s} {target['symbol']:5s} real={pr.get('real')} "
                  f"p95(shuffled)={pr.get('p95')} p={pr.get('p_value')}")

    out = {
        "model": "deepseek-flash",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "venue": venue, "timeframe": tf, "bars_requested": bars,
        "universe": bases, "execution_convention": "lag1_next_open",
        "costs": DEFAULT_COSTS.as_dict(),
        "trial_count": S.TRIAL_COUNT, "cells": total_trials,
        "buy_and_hold": per_symbol_bh,
        "cells_detail": rows,
        "cost_grid": cost_rows,
        "permutation": perm_rows,
    }
    path = RESULTS_DIR / f"backtest_{venue}_{tf}_{_stamp()}.json"
    body = json.dumps(out, indent=1, default=str)
    path.write_text(body, encoding="utf-8")
    # One "latest" per timeframe. A single backtest_latest.json silently overwrote the
    # 1h result whenever a 4h or 1d run finished, which makes a committed artifact
    # ambiguous about what it measured.
    (RESULTS_DIR / f"backtest_latest_{tf}.json").write_text(body, encoding="utf-8")
    print(f"\nwrote {path}")
    return 0


def cmd_scan(args) -> int:
    from .live import scan_signals

    sigs = scan_signals(args.venue, args.bases or DEFAULT_BASES, args.timeframe)
    out = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "signals": sigs}
    print(json.dumps(out, indent=1, default=str))
    (RESULTS_DIR / "latest_scan.json").write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    return 0


def cmd_live(args) -> int:
    from .live import LiveRound

    run_id = args.run_id or f"live_{datetime.now().strftime('%Y%m%d_%H%M')}"
    round_ = LiveRound(
        run_id=run_id, venue=args.venue, universe=args.bases or None,
        starting_cash=args.cash, risk_per_trade=args.risk, max_minutes=args.max_minutes,
        tp_atr=args.tp_atr, sl_atr=args.sl_atr, max_open=args.max_open,
        burst_pct=args.burst,
    )
    # Market-clock preflight: record which classes were open when this round started.
    # Nothing here enforces it yet (the universe is all crypto), but the record is what
    # turns "we only traded crypto because it was Sunday" from a human observation into
    # an artifact.
    from . import market_clock as M

    _open = M.open_classes()
    print(f"market preflight: open now = {_open}")
    if "crypto" not in _open:
        print("  WARNING: crypto is oddly closed — check the exchange before trusting fills")
    round_.ledger.append({"event": "PREFLIGHT", "open_classes": _open,
                          "utc": datetime.now(timezone.utc).isoformat(timespec="seconds")})

    print(f"live round {run_id} | venue={args.venue} | {args.minutes} min | "
          f"risk={args.risk:.1%}/trade | tp={args.tp_atr}ATR sl={args.sl_atr}ATR")
    summary = round_.run(duration_minutes=args.minutes, poll_s=args.poll, book=args.book, min_votes=args.min_votes)
    print(json.dumps(summary, indent=1))
    (RESULTS_DIR / f"{run_id}_summary.json").write_text(json.dumps(summary, indent=1, default=str), encoding="utf-8")
    return 0


def cmd_market(args) -> int:
    """Which asset classes are tradeable right now. Run before any live round."""
    from . import market_clock as M

    print(f"UTC now: {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    status = M.market_status()
    for name, st in status.items():
        print(f"  {'OPEN  ' if st.open else 'closed'} {name:10s} [{st.precision:6s}] {st.detail}")
        if st.next_open_utc:
            print(f"          next open: {st.next_open_utc}")
    print(f"\nTradeable now: {M.open_classes()}")
    out = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "status": {k: v.as_dict() for k, v in status.items()},
           "open_classes": M.open_classes()}
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / "market_status.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    return 0


def cmd_status(args) -> int:
    from .ledger import Ledger
    from .live import scan_signals

    paths = sorted((Path(__file__).resolve().parent / "state").glob("*.jsonl"))
    if not paths:
        print("no live runs yet")
        return 0
    for p in paths[-5:]:
        led = Ledger(p.stem)
        print(p.stem, json.dumps(led.summary()))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="realtime_challenge")
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("backtest")
    b.add_argument("--venue", default="binance")
    b.add_argument("--bases", nargs="*")
    b.add_argument("--timeframe", default="1h")
    b.add_argument("--bars", type=int, default=3000)
    b.add_argument("--permutations", type=int, default=0)
    b.add_argument("--verbose", action="store_true")
    b.set_defaults(func=cmd_backtest)

    s = sub.add_parser("scan")
    s.add_argument("--venue", default="binance")
    s.add_argument("--bases", nargs="*")
    s.add_argument("--timeframe", default="1h")
    s.set_defaults(func=cmd_scan)

    lv = sub.add_parser("live")
    lv.add_argument("--venue", default="binance")
    lv.add_argument("--bases", nargs="*")
    lv.add_argument("--minutes", type=float, default=30)
    lv.add_argument("--poll", type=float, default=30)
    lv.add_argument("--cash", type=float, default=10000.0)
    lv.add_argument("--risk", type=float, default=0.01)
    lv.add_argument("--max-minutes", type=int, default=60)
    lv.add_argument("--tp-atr", type=float, default=2.0)
    lv.add_argument("--sl-atr", type=float, default=1.0)
    lv.add_argument("--max-open", type=int, default=4)
    lv.add_argument("--book", default="preregistered", choices=["preregistered", "probe", "smoke"])
    lv.add_argument("--min-votes", type=int, default=2)
    lv.add_argument("--burst", type=float, default=0.004)
    lv.add_argument("--run-id", default=None)
    lv.set_defaults(func=cmd_live)

    mk = sub.add_parser("market")
    mk.set_defaults(func=cmd_market)

    st = sub.add_parser("status")
    st.set_defaults(func=cmd_status)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
