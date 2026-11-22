#!/usr/bin/env python3
"""Crypto class census under the walk-forward split.

Enumerates the seven-symbol crypto universe (BTC, ETH, SOL, XRP, DOGE, ADA, LINK)
under the published walk-forward partition and publishes the fold count used:

  binance 1d, folds=10, split_basis=calendar, purge=24 bars, embargo=1%,
  window 2021-06-02 -> 2026-11-22 (~5.4 y, 2,000 bars).

This is a census, not a backtest: no strategy is scored and no edge is claimed.
One row per symbol x fold with test-window bounds, bars, first/last close and
window return, plus live marks for the universe at generation time (best effort —
a dead feed is recorded as an error, not a fatality). Publishing the partition
(folds + split_basis + test_window_bars + purge_bars) is the point: a walk-forward
claim on crypto is unevaluable without it.

  python -m realtime_challenge.proof.crypto_census
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from realtime_challenge import data as D
from realtime_challenge.proof.walk_forward import folds_for

RESULTS = Path(__file__).resolve().parent.parent / "results"
UNIVERSE = ["BTC", "ETH", "SOL", "XRP", "DOGE", "ADA", "LINK"]
VENUE = "binance"
TIMEFRAME = "1d"
LIMIT_BARS = 2000
FOLD_COUNT = 10
PURGE_BARS = 24
EMBARGO_FRAC = 0.01
MIN_TEST_BARS = 30


def window_stats(sub: pd.DataFrame) -> dict:
    if len(sub) == 0:
        return {"bars": 0, "first_close": None, "last_close": None, "window_ret": None, "ann_vol": None}
    c = sub["close"].astype(float)
    r = c.pct_change().dropna()
    return {
        "bars": int(len(c)),
        "first_close": round(float(c.iloc[0]), 6),
        "last_close": round(float(c.iloc[-1]), 6),
        "window_ret": round(float(c.iloc[-1] / c.iloc[0] - 1), 6),
        "ann_vol": round(float(r.std() * np.sqrt(365)), 6) if len(r) > 1 else None,
    }


def main() -> int:
    print(f"fetching {TIMEFRAME} panel from {VENUE}: {UNIVERSE}, limit {LIMIT_BARS} ...")
    panel = D.fetch_panel(VENUE, UNIVERSE, timeframe=TIMEFRAME, limit=LIMIT_BARS, use_cache=False)
    if not panel:
        print("no data"); return 1
    sample = next(iter(panel.values()))
    fl = folds_for(len(sample), FOLD_COUNT)
    if not fl:
        print("panel too short for 10 folds"); return 1
    window_utc = f"{sample.index[0].date()} -> {sample.index[-1].date()}"

    # Test-window size is identical for every symbol (inner-joined panel) — compute once.
    test_windows = []
    for train_end, t0, t1 in fl:
        te_stop = max(1, train_end - PURGE_BARS)
        emb = int(te_stop * EMBARGO_FRAC)
        lo = min(t1, t0 + emb)
        if t1 - lo >= MIN_TEST_BARS:
            test_windows.append(t1 - lo)
    test_window_bars = int(round(float(np.median(test_windows)))) if test_windows else None

    rows = []
    for sym in UNIVERSE:
        df = panel[sym]
        for train_end, t0, t1 in fl:
            te_stop = max(1, train_end - PURGE_BARS)
            emb = int(te_stop * EMBARGO_FRAC)
            lo = min(t1, t0 + emb)
            sub = df.iloc[lo:t1]
            ws = window_stats(sub)
            rows.append({
                "symbol": sym,
                "train_end": str(df.index[train_end - 1]) if train_end - 1 < len(df) else None,
                "test_start": str(sub.index[0]) if len(sub) else str(df.index[t0]) if t0 < len(df) else None,
                "test_end": str(sub.index[-1]) if len(sub) else None,
                "bars": ws["bars"],
                "first_close": ws["first_close"],
                "last_close": ws["last_close"],
                "window_ret": ws["window_ret"],
                "ann_vol": ws["ann_vol"],
                "scored": ws["bars"] >= MIN_TEST_BARS,
            })

    # Live marks — best effort, never fatal for a census.
    live_marks = {}
    for sym in UNIVERSE:
        try:
            q = D.live_quote(VENUE, sym)
            live_marks[sym] = {
                "bid": q.get("bid"), "ask": q.get("ask"), "last": q.get("last"),
                "ts_utc": q.get("ts_utc"), "exchange_ts": q.get("exchange_ts"),
            }
        except Exception as exc:  # a single broken feed must not abort the census
            live_marks[sym] = {"error": f"{type(exc).__name__}: {str(exc)[:80]}"}

    scored = [r for r in rows if r["scored"]]
    out = {
        "hypothesis": "Crypto universe census under the walk-forward split — descriptive only, no edge claimed.",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "timeframe": TIMEFRAME, "venue": VENUE, "universe": UNIVERSE,
        "limit_bars": LIMIT_BARS, "window_utc": window_utc,
        "fold_count": FOLD_COUNT,
        "split_basis": "calendar",
        "purge_bars": PURGE_BARS,
        "embargo_frac": EMBARGO_FRAC,
        "test_window_bars": test_window_bars,
        "protocol": "sequential expanding folds, strictly no look-ahead, purge+embargo (Lopez de Prado); identical partition to walk_forward.py mode A",
        "n_symbols": len(UNIVERSE), "n_folds": FOLD_COUNT, "n_cells": len(rows),
        "n_scored_cells": len(scored),
        "rows": rows,
        "live_marks": live_marks,
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    body = json.dumps(out, indent=1, default=str)
    path = RESULTS / f"crypto_census_{stamp}.json"
    path.write_text(body, encoding="utf-8")
    (RESULTS / "crypto_census_latest.json").write_text(body, encoding="utf-8")
    print(f"n_symbols={len(UNIVERSE)} fold_count={FOLD_COUNT} test_window_bars={test_window_bars} "
          f"n_cells={len(rows)} n_scored={len(scored)}")
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
