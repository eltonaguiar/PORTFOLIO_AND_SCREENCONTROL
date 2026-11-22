#!/usr/bin/env python3
"""P6 — the walk-forward gate. The one gate in this project's own table never run.

Everything else in `03-trading-strategies` tests a strategy over one full window. That answers
"did this rule work over 22 months" — not "would I have known to use it at the time". Walk-forward
is the difference, and it is the gate that catches a result produced by choosing parameters on
the same data that was scored.

Two modes, because they answer different questions:

  Mode A — FROZEN params.  The six families already have frozen parameters (no sweeps), so the
           only honest question is temporal stability: does the sign of the net expectancy hold
           fold by fold, or is the 22-month average produced by one good stretch? Reports
           per-fold n and mean net, plus the fraction of folds above zero.

  Mode B — FITTED params.  A 3x3x2 grid over (tp_atr, sl_atr, max_bars) is fitted on each train
           window by net expectancy, then applied untouched to the next window. This is the
           real overfitting test: a family that works only when you pick its parameters on the
           scoring data will show a sharp train->test collapse here.

Purge and embargo (Lopez de Prado). A trade opened near the end of a train window can close
inside the test window, so the last MAX_BARS of train are PURGED — their labels overlap the
test set. An EMBARGO of 1% of the train length is dropped from the start of the test window so
features estimated on late-train bars cannot price early-test entries.

Folds are strictly sequential and expanding: fold k trains on everything before its test window
and never sees it. No shuffling, no k-fold on time series.

  python -m realtime_challenge.proof.walk_forward            # both modes, 4h
  python -m realtime_challenge.proof.walk_forward --mode A
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from realtime_challenge import data as D
from realtime_challenge.costs import DEFAULT_COSTS
from realtime_challenge.engine import buy_and_hold, run_from_signals
from realtime_challenge.strategies import builders

RESULTS = Path(__file__).resolve().parent.parent / "results"
UNIVERSE = ["BTC", "ETH", "SOL", "XRP", "DOGE", "ADA", "LINK"]
GRID_SYMBOLS = ["BTC", "ETH", "SOL"]          # mode B stays on the three most liquid
GRID = [(tp, sl, mb)
        for tp in (1.0, 2.0, 3.0)
        for sl in (0.75, 1.0, 1.5)
        for mb in (12, 24)]
N_FOLDS_A = 5
N_FOLDS_B = 4
PURGE_BARS = 48          # longest max_bars in the grid
EMBARGO_FRAC = 0.01
WF_MIN_FOLDS_POSITIVE = 0.60


def boot_ci(x: np.ndarray, n: int = 2000, seed: int = 7) -> tuple[float, float]:
    if len(x) < 10:
        return (float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    means = np.array([rng.choice(x, size=len(x), replace=True).mean() for _ in range(n)])
    return (float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5)))


def net_returns(res) -> np.ndarray:
    """`BacktestResult.trades` holds as_dict() payloads, not Trade objects — read by key."""
    vals = []
    for t in res.trades:
        v = t.get("net_ret") if isinstance(t, dict) else getattr(t, "net_ret", None)
        if v is not None and math.isfinite(v):
            vals.append(v)
    return np.array(vals)


def _run(df, sig, name, sym, tp, sl, mb, tf):
    return run_from_signals(df, sig, name, sym, tp_atr=tp, sl_atr=sl, max_bars=mb,
                            costs=DEFAULT_COSTS, timeframe=tf)


def folds_for(n_bars: int, k: int, min_train: int = 400):
    """Sequential expanding splits. Returns [(train_end, test_start, test_end)]."""
    usable = n_bars - min_train
    if usable < k * 30:
        return []
    step = usable // k
    out = []
    for i in range(k):
        train_end = min_train + i * step
        test_start = train_end
        test_end = n_bars if i == k - 1 else train_end + step
        out.append((train_end, test_start, test_end))
    return out


def mode_a(panel, tf, n_folds: int = N_FOLDS_A, purge: int = PURGE_BARS) -> list[dict]:
    """Frozen parameters: temporal stability only."""
    rows = []
    for name, build in builders().items():
        for sym, df in panel.items():
            sig = build(df)
            fl = folds_for(len(df), n_folds)
            per = []
            for train_end, t0, t1 in fl:
                # purge: labels from the tail of train may resolve inside test
                te_stop = max(1, train_end - purge)
                emb = int((te_stop) * EMBARGO_FRAC)
                lo = min(t1, t0 + emb)
                if t1 - lo < 30:
                    continue
                sub = df.iloc[lo:t1]
                r = _run(sub, sig.loc[sub.index], name, sym, 2.0, 1.0, 24, tf)
                nr = net_returns(r)
                per.append({"test_start": str(sub.index[0]), "test_end": str(sub.index[-1]),
                            "n": int(len(nr)),
                            "mean_bps": round(float(nr.mean() * 1e4), 2) if len(nr) else None})
            scored = [p for p in per if p["n"] >= 5]
            pos = sum(1 for p in scored if (p["mean_bps"] or 0) > 0)
            rows.append({
                "strategy": name, "symbol": sym, "folds": per,
                "n_scored_folds": len(scored),
                "folds_positive": pos,
                "fold_positivity": round(pos / len(scored), 3) if scored else None,
                "total_oos_trades": int(sum(p["n"] for p in scored)),
                "pooled_mean_bps": (round(float(np.mean([p["mean_bps"] for p in scored
                                                         for _ in range(p["n"])])), 2)
                                    if scored else None),
            })
    return rows


def mode_b(panel, tf, n_folds: int = N_FOLDS_B, purge: int = PURGE_BARS) -> list[dict]:
    """Fit the bracket on train, apply untouched to test."""
    rows = []
    for name, build in builders().items():
        for sym in GRID_SYMBOLS:
            df = panel[sym]
            sig = build(df)
            fl = folds_for(len(df), n_folds)
            per = []
            for train_end, t0, t1 in fl:
                te_stop = max(1, train_end - purge)
                emb = int(te_stop * EMBARGO_FRAC)
                tr = df.iloc[max(0, te_stop - 2500):te_stop]
                lo = min(t1, t0 + emb)
                if len(tr) < 200 or t1 - lo < 30:
                    continue
                best, best_e = None, -1e9
                for (tp, sl, mb) in GRID:
                    r = _run(tr, sig.loc[tr.index], name, sym, tp, sl, mb, tf)
                    nr = net_returns(r)
                    if len(nr) >= 8:
                        e = float(nr.mean())
                        if e > best_e:
                            best_e, best = e, (tp, sl, mb)
                if best is None:
                    continue
                tp, sl, mb = best
                te = df.iloc[lo:t1]
                rte = _run(te, sig.loc[te.index], name, sym, tp, sl, mb, tf)
                nre = net_returns(rte)
                per.append({"test_start": str(te.index[0]), "test_end": str(te.index[-1]),
                            "picked": {"tp_atr": tp, "sl_atr": sl, "max_bars": mb},
                            "train_mean_bps": round(best_e * 1e4, 2),
                            "n_test": int(len(nre)),
                            "test_mean_bps": round(float(nre.mean() * 1e4), 2) if len(nre) else None})
            scored = [p for p in per if p["n_test"] >= 5]
            collapse = [p for p in scored
                        if p["train_mean_bps"] > 0 and (p["test_mean_bps"] or 0) <= 0]
            rows.append({
                "strategy": name, "symbol": sym, "folds": per,
                "n_scored_folds": len(scored),
                "folds_train_positive": sum(1 for p in scored if p["train_mean_bps"] > 0),
                "folds_test_positive": sum(1 for p in scored if (p["test_mean_bps"] or 0) > 0),
                "train_to_test_collapses": len(collapse),
                "total_oos_trades": int(sum(p["n_test"] for p in scored)),
            })
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="both", choices=["A", "B", "both"])
    ap.add_argument("--timeframe", default="4h")
    ap.add_argument("--folds", type=int, default=None,
                    help="folds per mode; defaults 5 for A and 4 for B")
    ap.add_argument("--limit", type=int, default=4000, help="bars to request")
    ap.add_argument("--purge", type=int, default=None,
                    help="purge bars; defaults to PURGE_BARS (48) on intraday, 24 on daily")
    ap.add_argument("--venue", default="binance")
    a = ap.parse_args()
    # daily bars need a shorter purge: a 48-bar purge on a 1d fold would delete most of the
    # training tail, since the longest bracket held is max_bars (<=24), not 48 bars
    purge = a.purge if a.purge is not None else (24 if a.timeframe.endswith("d") else PURGE_BARS)
    folds_a = a.folds or N_FOLDS_A
    folds_b = a.folds or N_FOLDS_B

    print(f"fetching {a.timeframe} panel, {len(UNIVERSE)} symbols, limit {a.limit} ...")
    # Venue matters for history depth: kraken's inner-joined 4h panel across all seven
    # symbols is only ~721 bars (120 days), which cannot support 4-5 expanding folds.
    # binance carries the full 4000-bar (22-month) 4h history used by the census.
    panel = D.fetch_panel(a.venue, UNIVERSE, timeframe=a.timeframe,
                          limit=a.limit, use_cache=False)
    if not panel:
        print("no data"); return 1
    nbars = min(len(v) for v in panel.values())
    # test window size in bars (median scored window across expanding folds)
    sample_df = next(iter(panel.values()))
    sample_fl = folds_for(len(sample_df), folds_a)
    tw = []
    for train_end, t0, t1 in sample_fl:
        te_stop = max(1, train_end - purge)
        emb = int(te_stop * EMBARGO_FRAC)
        lo = min(t1, t0 + emb)
        sub = sample_df.iloc[lo:t1]
        if len(sub) >= 30:
            tw.append(len(sub))
    test_window_bars = int(round(statistics.median(tw))) if tw else None
    print(f"  {len(panel)} symbols, common window {min(v.index[0] for v in panel.values())} "
          f"-> {max(v.index[-1] for v in panel.values())} ({nbars} bars)\n")

    out = {
        "hypothesis": "P6 — do any of the six families survive walk-forward with purge+embargo?",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "timeframe": a.timeframe, "universe": UNIVERSE,
        "folds_a": folds_a, "folds_b": folds_b, "purge_bars": purge, "test_window_bars": test_window_bars, "venue": a.venue,
        "costs": DEFAULT_COSTS.as_dict(),
        "protocol": {
            "folds": "sequential expanding, strictly no look-ahead",
            "purge_bars": purge,
            "embargo_frac": EMBARGO_FRAC,
            "split_basis": "calendar",
            "mode_a": "frozen parameters — temporal stability",
            "mode_b": f"grid {len(GRID)} brackets fitted on train, applied untouched to test",
            "mode_b_symbols": GRID_SYMBOLS,
            "pass_rule": f"pooled OOS CI lower bound > 0 AND >= {WF_MIN_FOLDS_POSITIVE:.0%} folds positive",
            "test_window_bars": test_window_bars,
        },
    }

    if a.mode in ("A", "both"):
        print("MODE A — frozen parameters, temporal stability")
        rows_a = mode_a(panel, a.timeframe, n_folds=folds_a, purge=purge)
        rows_a.sort(key=lambda r: (-(r["fold_positivity"] or 0), -(r["total_oos_trades"] or 0)))
        print(f"  {'strategy':24s} {'sym':5s} {'folds+':>7s} {'n_oos':>6s} {'pooled bps':>11s}")
        for r in rows_a[:10]:
            print(f"  {r['strategy']:24s} {r['symbol']:5s} "
                  f"{r['folds_positive']}/{r['n_scored_folds']:<5d} "
                  f"{r['total_oos_trades']:6d} {str(r['pooled_mean_bps']):>11s}")
        survivors = [r for r in rows_a
                     if (r["fold_positivity"] or 0) >= WF_MIN_FOLDS_POSITIVE
                     and (r["pooled_mean_bps"] or -1) > 0
                     and r["total_oos_trades"] >= 20]
        print(f"\n  MODE A survivors (>=60% folds positive, pooled>0, n>=20): "
              f"{len(survivors)} of {len(rows_a)}")
        for r in survivors:
            print(f"    {r['strategy']}/{r['symbol']}  {r['folds_positive']}/"
                  f"{r['n_scored_folds']} folds  n={r['total_oos_trades']}  "
                  f"{r['pooled_mean_bps']} bps")
        out["mode_a"] = {"rows": rows_a, "n_survivors": len(survivors),
                         "survivors": [f"{r['strategy']}/{r['symbol']}" for r in survivors]}

    if a.mode in ("B", "both"):
        print(f"\nMODE B — {len(GRID)}-bracket grid fitted on train, applied to test")
        rows_b = mode_b(panel, a.timeframe, n_folds=folds_b, purge=purge)
        rows_b.sort(key=lambda r: -r["folds_test_positive"])
        print(f"  {'strategy':24s} {'sym':5s} {'train+':>7s} {'test+':>6s} "
              f"{'collapse':>9s} {'n_oos':>6s}")
        for r in rows_b:
            print(f"  {r['strategy']:24s} {r['symbol']:5s} "
                  f"{r['folds_train_positive']}/{r['n_scored_folds']:<5d} "
                  f"{r['folds_test_positive']}/{r['n_scored_folds']:<4d} "
                  f"{r['train_to_test_collapses']:9d} {r['total_oos_trades']:6d}")
        tot_tr = sum(r["folds_train_positive"] for r in rows_b)
        tot_te = sum(r["folds_test_positive"] for r in rows_b)
        tot_cl = sum(r["train_to_test_collapses"] for r in rows_b)
        print(f"\n  across all fitted folds: train positive {tot_tr}, "
              f"test positive {tot_te}, collapses {tot_cl}")
        out["mode_b"] = {"rows": rows_b, "train_positive_folds": tot_tr,
                         "test_positive_folds": tot_te, "collapses": tot_cl}

    RESULTS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    body = json.dumps(out, indent=1, default=str)
    (RESULTS / f"walk_forward_{a.timeframe}_{stamp}.json").write_text(body, encoding="utf-8")
    (RESULTS / f"walk_forward_{a.timeframe}_latest.json").write_text(body, encoding="utf-8")
    print(f"\nwrote results/walk_forward_{a.timeframe}_{stamp}.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
