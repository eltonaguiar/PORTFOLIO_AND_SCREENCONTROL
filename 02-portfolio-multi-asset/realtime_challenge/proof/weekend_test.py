#!/usr/bin/env python3
"""Is the crypto "weekend effect" real, or is pooling fooling us?

The 1h matrix found H-R5 (Fri 20:00 UTC -> Sun 20:00 UTC) as the only family with a
positive pooled mean at 26 bps: +5.9 bps/trade, PF 1.06, n=126. That number is the
single most promising thing in the matrix and it is also the most likely artefact,
because:

  (a) 7 symbols x 18 weekends is NOT 126 independent observations. All 7 coins share
      the same weekend, so the effective sample is ~18 calendar events, not 126.
  (b) crypto drifts over any 48-hour window in a bull phase. A "weekend effect" only
      exists if weekend windows drift MORE than weekday windows of the same length.

So this script does three things the 1h matrix cannot:

  1. EXTENDS history to ~3 years of 4h bars (4h bars have a bar boundary at 20:00 UTC,
     so the entry and exit times are exact).
  2. CLUSTER-BOOTSTRAPS by calendar weekend, not by trade, so the 7 correlated coins
     cannot manufacture significance.
  3. RUNS THE CONTROL: every other 48h window (Mon->Wed, Tue->Thu, ...) with the same
     cost model. The weekend is only an anomaly if it beats those.

Output: results/weekend_test.json, plus a printed verdict.

  python -m realtime_challenge.proof.weekend_test
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from realtime_challenge import data as D  # noqa: E402

BASES = ["BTC", "ETH", "SOL", "XRP", "DOGE", "ADA", "LINK"]
BARS_4H = 6600          # ~3 years
ROUND_TURN = 0.0026     # 26 bps, the default friction
N_BOOT = 10000
SEED = 20261122

OUT = Path(__file__).resolve().parent.parent / "results" / "weekend_test.json"


def window_returns(df: pd.DataFrame, start_dow: int, start_hour: int, hold_bars: int = 12) -> pd.Series:
    """Return of buying at the close of each matching bar and holding `hold_bars` bars.

    Labels each observation by its entry date so observations from the same week can
    be clustered.
    """
    idx = df.index
    mask = (idx.dayofweek == start_dow) & (idx.hour == start_hour)
    close = df["close"].to_numpy(float)
    # 4h bars => 12 bars is 48 hours
    out = {}
    for i in np.flatnonzero(mask):
        if i + hold_bars >= len(df):
            continue
        entry = close[i]
        exit_ = close[i + hold_bars]
        gross = exit_ / entry - 1.0
        out[idx[i].date()] = gross - ROUND_TURN
    return pd.Series(out).sort_index()


def cluster_bootstrap_ci(series: pd.Series, n_boot: int = N_BOOT, seed: int = SEED) -> dict:
    """Bootstrap the MEAN over the independent units (the dates), not the trades.

    Each element of `series` is already one calendar event with all 7 coins averaged
    into it, so resampling dates is the correct cluster resample.
    """
    v = series.to_numpy(float)
    if v.size < 5:
        return {"mean": float(v.mean()) if v.size else None, "lo": None, "hi": None, "n": int(v.size)}
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, v.size, size=(n_boot, v.size))
    means = v[idx].mean(axis=1)
    return {
        "mean_bps": round(float(v.mean()) * 1e4, 2),
        "lo_bps": round(float(np.quantile(means, 0.025)) * 1e4, 2),
        "hi_bps": round(float(np.quantile(means, 0.975)) * 1e4, 2),
        "p_gt_zero": round(float((means > 0).mean()), 4),
        "n_events": int(v.size),
        "ann_bps_if_every_week": round(float(v.mean()) * 1e4 * 52, 1),
    }


def main() -> int:
    print(f"fetching {len(BASES)} symbols, 4h x {BARS_4H} bars from binance ...")
    panel = D.fetch_panel("binance", BASES, "4h", BARS_4H)
    any_df = next(iter(panel.values()))
    years = (any_df.index[-1] - any_df.index[0]).days / 365.25
    print(f"  {len(panel)} symbols | window {any_df.index[0].date()} -> {any_df.index[-1].date()} ({years:.2f} y)")

    # ---- per-symbol weekend returns, then average across symbols per weekend
    per_symbol: Dict[str, pd.Series] = {}
    for base, df in panel.items():
        per_symbol[base] = window_returns(df, start_dow=4, start_hour=20, hold_bars=12)  # Fri 20:00 -> Sun 20:00

    # Align on date, then column-mean = one observation per weekend
    aligned = pd.concat(per_symbol, axis=1)
    per_weekend = aligned.mean(axis=1).dropna()
    weekend_ci = cluster_bootstrap_ci(per_weekend)

    per_symbol_stats = {}
    for base, s in per_symbol.items():
        per_symbol_stats[base] = {
            "n": int(len(s)),
            "mean_bps": round(float(s.mean()) * 1e4, 2),
            "win_rate": round(float((s > 0).mean()), 3),
            "t_stat": round(float(s.mean() / (s.std(ddof=1) / math.sqrt(len(s)))) if len(s) > 2 else 0, 2),
        }

    # ---- THE CONTROL: every other 48h window, same costs, same clustering
    controls: Dict[str, dict] = {}
    for dow in range(7):
        for hour in (0, 4, 8, 12, 16, 20):
            windows = {}
            for base, df in panel.items():
                windows[base] = window_returns(df, start_dow=dow, start_hour=hour, hold_bars=12)
            al = pd.concat(windows, axis=1).mean(axis=1).dropna()
            if len(al) < 10:
                continue
            key = f"{['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][dow]} {hour:02d}:00"
            controls[key] = {
                "mean_bps": round(float(al.mean()) * 1e4, 2),
                "n_events": int(len(al)),
                "win_rate": round(float((al > 0).mean()), 3),
            }

    ranked = sorted(controls.items(), key=lambda kv: -kv[1]["mean_bps"])
    weekend_rank = next((i + 1 for i, (k, _) in enumerate(ranked) if k == "Fri 20:00"), None)
    control_means = np.array([v["mean_bps"] for v in controls.values()])
    z_vs_controls = (
        (weekend_ci["mean_bps"] - control_means.mean()) / control_means.std(ddof=1)
        if control_means.std(ddof=1) > 0 else None
    )

    verdict_bits = []
    if weekend_ci["lo_bps"] is not None and weekend_ci["lo_bps"] > 0:
        verdict_bits.append("weekend return is positive with a CI excluding zero")
    else:
        verdict_bits.append("weekend return CI includes zero -> NOT significant")
    if weekend_rank == 1:
        verdict_bits.append("it is also the single best 48h window of the 42 tested")
    else:
        verdict_bits.append(f"it ranks #{weekend_rank} of {len(ranked)} 48h windows tested")
    if weekend_rank and weekend_rank <= 3 and weekend_ci["lo_bps"] is not None and weekend_ci["lo_bps"] > 0:
        verdict = "CANDIDATE — worth a forward pod, not capital"
    else:
        verdict = "NOT ESTABLISHED — do not trade, do not quote as an edge"

    out = {
        "test": "crypto weekend effect, clustered by calendar weekend",
        "venue": "binance",
        "timeframe": "4h",
        "window": {"start": str(any_df.index[0]), "end": str(any_df.index[-1]), "years": round(years, 2)},
        "round_turn_cost": ROUND_TURN,
        "rule": "buy Fri 20:00 UTC close, sell Sun 20:00 UTC close (12 x 4h bars)",
        "weekend_pooled": weekend_ci,
        "per_symbol": per_symbol_stats,
        "control_windows_top10": [{"window": k, **v} for k, v in ranked[:10]],
        "control_windows_bottom3": [{"window": k, **v} for k, v in ranked[-3:]],
        "n_control_windows": len(controls),
        "weekend_rank_among_windows": weekend_rank,
        "z_vs_control_mean": None if z_vs_controls is None else round(float(z_vs_controls), 2),
        "verdict": verdict,
        "verdict_reasons": verdict_bits,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")

    print("\n--- weekend window (Fri 20:00 -> Sun 20:00), clustered by weekend ---")
    print(f"  mean {weekend_ci['mean_bps']:+.2f} bps/event  "
          f"95% CI [{weekend_ci['lo_bps']:+.2f}, {weekend_ci['hi_bps']:+.2f}]  "
          f"n_events={weekend_ci['n_events']}  P(>0)={weekend_ci['p_gt_zero']}")
    print(f"  annualised if traded every week: {weekend_ci['ann_bps_if_every_week']:+.0f} bps "
          f"({weekend_ci['ann_bps_if_every_week']/100:+.2f}%)")
    print("\n  per symbol:")
    for b, s in per_symbol_stats.items():
        print(f"    {b:5s} n={s['n']:3d} mean={s['mean_bps']:+8.2f}bps wr={s['win_rate']:.3f} t={s['t_stat']:+.2f}")
    print(f"\n--- control: {len(controls)} 48h windows, same costs ---")
    for k, v in ranked[:6]:
        print(f"    {k:9s} mean={v['mean_bps']:+8.2f}bps n={v['n_events']} wr={v['win_rate']:.3f}")
    print(f"    ... worst: {ranked[-1][0]} {ranked[-1][1]['mean_bps']:+.2f}bps")
    print(f"  weekend rank: #{weekend_rank} of {len(ranked)}   z vs control mean: {out['z_vs_control_mean']}")
    print(f"\nVERDICT: {verdict}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
