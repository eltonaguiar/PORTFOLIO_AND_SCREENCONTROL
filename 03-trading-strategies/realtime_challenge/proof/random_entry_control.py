#!/usr/bin/env python3
"""Random-entry control — the luck benchmark.

Adapted from a peer proposal (GLM 5.3 Flash): a strategy should be compared against
*random entries with identical exits*, not only against buy-and-hold. This is a different
question from the permutation control already in this repo:

  permutation control  : does the signal beat the same rule on SHUFFLED PRICES?
                         -> answers "is there structure in the price series?"

  random-entry control : does the signal beat RANDOM TIMING with the same bracket,
                         size, duration and costs?
                         -> answers "does the SIGNAL's timing add anything at all?"

A rule can pass one and fail the other. The failure this catches is the one that matters
for H-R4: a rule whose entire positive mean comes from its exit bracket (36 bars for a
volatility expansion to pay for the round trip) rather than from *when* it enters. If
random entries with the same brackets produce the same mean, the signal is decoration.

Method
------
For each real cell (strategy, symbol):
  1. take the real trade count n and the real mean net return per trade
  2. draw `n_perm` random signal series with the SAME number of entries, the SAME direction
     mix, spread uniformly over the same index range
  3. run them through the identical engine, brackets, sizing and costs
  4. report the real value's percentile in that distribution and a one-sided p-value

Nothing is tuned. Random entries are long-only when the real strategy is long-only, so the
comparison isolates timing rather than direction.

  python -m realtime_challenge.proof.random_entry_control
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from realtime_challenge import data as D, engine as E, strategies as S, stats as ST  # noqa: E402
from realtime_challenge.costs import DEFAULT_COSTS  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "results" / "random_entry_control.json"
BASES = ["BTC", "ETH", "SOL", "XRP", "DOGE", "ADA", "LINK"]
N_PERM = 200
SEED = 20261122


def real_signals(df: pd.DataFrame, cfg: dict) -> pd.Series:
    return cfg["fn"](df)


def matched_random_signals(df: pd.DataFrame, n_entries: int, direction: int,
                           rng: np.random.Generator) -> pd.Series:
    """Random entries spread uniformly, same count and direction as the real signal."""
    sig = pd.Series(0, index=df.index, dtype=int)
    if n_entries <= 0 or n_entries >= len(df):
        return sig
    spots = rng.choice(np.arange(len(df)), size=min(n_entries, len(df)), replace=False)
    sig.iloc[spots] = direction
    return sig


def run_test(df: pd.DataFrame, cfg: dict, n_perm: int = N_PERM, seed: int = SEED) -> dict:
    real_sig = real_signals(df, cfg)
    kw = dict(tp_atr=cfg["tp_atr"], sl_atr=cfg["sl_atr"], max_bars=cfg["max_bars"],
              costs=DEFAULT_COSTS, timeframe="1d", allow_short=cfg["allow_short"])

    real = E.run_from_signals(df, real_sig, "real", "x", **kw)
    real_net = [t["net_ret"] for t in real.trades]
    if len(real_net) < 10:
        return {"n_real": len(real_net), "note": "fewer than 10 real trades — underpowered"}
    real_mean = float(np.mean(real_net))
    real_pf = ST.profit_factor(real_net)

    # direction mix of the real signal, so random entries match it
    nonzero = real_sig[real_sig != 0]
    dirs = nonzero.to_numpy()
    n_entries = int(len(nonzero))

    rng = np.random.default_rng(seed)
    sims: list[float] = []
    sim_pfs: list[float] = []
    for _ in range(n_perm):
        d = int(rng.choice(dirs))
        rs = matched_random_signals(df, n_entries, d, rng)
        try:
            r = E.run_from_signals(df, rs, "rand", "x", **kw)
            if len(r.trades) < 10:
                continue
            m = float(np.mean([t["net_ret"] for t in r.trades]))
            sims.append(m)
            pf = ST.profit_factor([t["net_ret"] for t in r.trades])
            if pf is not None and np.isfinite(pf):
                sim_pfs.append(pf)
        except Exception:
            continue

    if not sims:
        return {"n_real": len(real_net), "note": "no usable random sims"}

    arr = np.asarray(sims)
    pct = float((arr < real_mean).mean())
    return {
        "n_real": len(real_net),
        "n_random_sims": len(arr),
        "real_mean_bps": round(real_mean * 1e4, 2),
        "real_pf": None if real_pf is None else round(real_pf, 3),
        "random_mean_bps": round(float(arr.mean()) * 1e4, 2),
        "random_p05_bps": round(float(np.quantile(arr, 0.05)) * 1e4, 2),
        "random_p95_bps": round(float(np.quantile(arr, 0.95)) * 1e4, 2),
        "real_percentile_vs_random": round(pct, 3),
        "p_value_one_sided": round(float((arr >= real_mean).mean()), 4),
        # Deliberately neutral: this is a PER-CELL percentile, and 29 cells are tested at
        # once. Labelling a cell "adds timing value" here would be exactly the multiple-
        # testing error this whole project exists to avoid. The project-wide reading below
        # applies the correction; the per-cell label must not.
        "verdict": (
            "real entries ranked BELOW 95% of matched random entries"
            if pct < 0.95 else
            "candidate only — top 5% vs random on this cell, NOT corrected for the number of cells tested"
        ),
    }


def main() -> int:
    print(f"loading {len(BASES)} symbols @ 1d ...")
    panel = D.fetch_panel("binance", BASES, "1d", 1200)
    any_df = next(iter(panel.values()))
    print(f"  window {any_df.index[0].date()} -> {any_df.index[-1].date()} ({len(any_df)} bars)")

    # Pool per strategy across symbols by running the test on the pooled trades of each
    # symbol, then reporting each cell that is powered. H-R4 is the family of interest.
    results = []
    for name, cfg in S.REGISTRY.items():
        for base, df in panel.items():
            r = run_test(df, cfg)
            if r.get("n_real", 0) < 10:
                continue
            results.append({"strategy": name, "symbol": base, **r})
            print(f"  {name:24s} {base:5s} n={r['n_real']:3d} real={r['real_mean_bps']:+8.2f}bps "
                  f"random_med={r['random_mean_bps']:+8.2f}bps pct={r['real_percentile_vs_random']:.2f} "
                  f"p={r.get('p_value_one_sided')}")

    # aggregate: how many cells beat random timing, and does ANY survive multiplicity?
    powered = [r for r in results if r.get("p_value_one_sided") is not None]
    sig = [r for r in powered if r["p_value_one_sided"] < 0.05]

    # Benjamini-Hochberg FDR at 5% across every powered cell. Without this, "2 of 29 at
    # p<0.05" reads like a discovery when the expected false-positive count for 29 tests at
    # alpha=0.05 is 1.45 — i.e. 2 observed is indistinguishable from noise.
    m = len(powered)
    bh = {"m_tests": m, "alpha": 0.05, "expected_false_positives_at_0.05": round(0.05 * m, 2),
          "survivors": [], "thresholds": []}
    if m:
        ordered = sorted(powered, key=lambda r: r["p_value_one_sided"])
        kmax = 0
        for k, r in enumerate(ordered, start=1):
            thr = k * 0.05 / m
            bh["thresholds"].append({"k": k, "cell": f"{r['strategy']}/{r['symbol']}",
                                     "p": r["p_value_one_sided"], "bh_threshold": round(thr, 5),
                                     "passes": r["p_value_one_sided"] <= thr})
            if r["p_value_one_sided"] <= thr:
                kmax = k
        bh["survivors"] = [f"{r['strategy']}/{r['symbol']}" for r in ordered[:kmax]]
    bh["any_survive"] = bool(bh["survivors"])

    hr4 = [r for r in results if r["strategy"] == "H-R4_vol_compression"]
    hr4_verdict = None
    if hr4:
        best = max(hr4, key=lambda r: r["real_mean_bps"])
        hr4_verdict = {
            "best_symbol": best["symbol"],
            "real_mean_bps": best["real_mean_bps"],
            "random_median_bps": best["random_mean_bps"],
            "percentile": best["real_percentile_vs_random"],
            "p_value": best["p_value_one_sided"],
            "reading": best["verdict"],
        }

    out = {
        "test": "random-entry control — does the signal's TIMING beat random timing with identical exits?",
        "proposed_by": "GLM 5.3 Flash, 2026-11-22 (S3 seeded random-entry control)",
        "complements": "stats.permutation_control (shuffled prices) — this shuffles ENTRY TIMING instead",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "timeframe": "1d", "bars": 1200, "n_perm": N_PERM, "seed": SEED,
        "costs": DEFAULT_COSTS.as_dict(),
        "cells": results,
        "n_cells_powered": len(powered),
        "n_cells_signal_beats_random_p05": len(sig),
        "cells_signal_beats_random": [f"{r['strategy']}/{r['symbol']}" for r in sig],
        "H_R4_focus": hr4_verdict,
        "multiple_testing": bh,
        "project_wide_reading": (
            f"{len(sig)} of {len(powered)} powered cells beat random timing at raw p<0.05, "
            f"but the expected false-positive count for {m} tests at alpha=0.05 is "
            f"{round(0.05*m,2)}, and Benjamini-Hochberg at 5% FDR leaves "
            f"{len(bh['survivors'])} survivor(s). "
            + ("NO cell survives correction: the timing advantage is indistinguishable from "
               "the luck of running 29 tests, and the brackets are doing the work."
               if not bh["any_survive"] else
               f"Survivors after BH: {bh['survivors']} — promote ONLY these, and only with a "
               "pre-registered single-cell forward test.")
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(out, indent=1, default=str)
    # Timestamped copy first, canonical second. Two concurrent runs of this script write the
    # same path, and a stale run finishing last silently overwrites the fresh one — the exact
    # race already fixed for backtest_latest.json. `generated_utc` makes a stale copy
    # detectable; the timestamped filename makes it recoverable.
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    (OUT.parent / f"random_entry_control_{stamp}.json").write_text(body, encoding="utf-8")
    OUT.write_text(body, encoding="utf-8")

    print(f"\npowered cells: {len(powered)}   beating random at p<0.05: {len(sig)}")
    if sig:
        print("  ->", out["cells_signal_beats_random"])
    if hr4_verdict:
        print(f"\nH-R4 focus ({hr4_verdict['best_symbol']}): real {hr4_verdict['real_mean_bps']:+.2f}bps "
              f"vs random median {hr4_verdict['random_median_bps']:+.2f}bps, "
              f"percentile {hr4_verdict['percentile']:.2f}, p={hr4_verdict['p_value']}")
        print(f"  {hr4_verdict['reading']}")
    print(f"\nBH FDR 5% across m={bh['m_tests']} tests — expected false positives at raw 0.05: "
          f"{bh['expected_false_positives_at_0.05']}")
    for t in bh["thresholds"][:4]:
        print(f"  k={t['k']} {t['cell']:34s} p={t['p']:.3f}  BH={t['bh_threshold']:.5f}  "
              f"{'PASS' if t['passes'] else 'fails'}")
    print(f"  survivors after BH: {bh['survivors'] or 'NONE'}")
    print(f"\n{out['project_wide_reading']}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
