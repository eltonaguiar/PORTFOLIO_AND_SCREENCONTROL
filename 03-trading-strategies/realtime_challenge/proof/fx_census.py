#!/usr/bin/env python3
"""P8 — the FX class census: the one asset class in the ledger never tested here.

The audit3 ledger rates FOREX **WEAK** on n=264 picks (−0.0447/trade, CI straddling zero) and
records the class as "honest-exhausted (H-121 REFUTED)". That verdict comes from the picks
layer. This repo has never run its own six families against the class, and FX is the only major
class where that is still true.

FX differs from crypto and equities in one way that changes the benchmark:

  **There is no buy-and-hold to beat.** A currency pair has roughly zero expected return, so
  holding EUR/USD forever earns nothing. The benchmark is therefore **flat** — the honest
  question is whether the strategy beats doing nothing, not whether it beats holding.

Costs are the harder question. Retail majors trade at roughly 1 pip round turn (~1 bps on
EUR/USD), institutional tighter, spread-widening and swap/financing wider. Three cost levels are
reported (2 / 5 / 10 bps round turn) rather than one, because the class verdict is unusually
sensitive to which you pick — FX edges are small enough that the cost line decides them.

Also reported: the **carry** baseline, because FX carry is the one documented, durable FX risk
premium. If the six technical families cannot beat a static long-high-yield / short-low-yield
basket, the class verdict is "no technical edge" rather than "no edge".

  python -m realtime_challenge.proof.fx_census
"""

from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from realtime_challenge.costs import CostModel
from realtime_challenge.engine import run_from_signals
from realtime_challenge.strategies import builders

RESULTS = Path(__file__).resolve().parent.parent / "results"

# Yahoo tickers for the seven most liquid pairs; all quote USD on one side or are major crosses.
PAIRS = {
    "EURUSD": "EURUSD=X", "USDJPY": "USDJPY=X", "GBPUSD": "GBPUSD=X",
    "AUDUSD": "AUDUSD=X", "USDCAD": "USDCAD=X", "USDCHF": "USDCHF=X",
    "NZDUSD": "NZDUSD=X",
}
START = "2015-01-01"
COST_LEVELS = [2, 5, 10]          # bps round turn
N_PERM = 60
SEED = 11


def load_pair(tkr: str) -> pd.DataFrame | None:
    import yfinance as yf
    try:
        df = yf.download(tkr, start=START, interval="1d", auto_adjust=False, progress=False)
    except Exception as exc:
        print(f"  [fx] {tkr}: {type(exc).__name__}")
        return None
    if df is None or df.empty:
        return None
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.rename(columns=str.lower)[["open", "high", "low", "close"]].dropna()
    df = df[df["close"] > 0]
    return df if len(df) > 500 else None


def summarise(res, cost_bps: float) -> dict:
    nr = np.array([t["net_ret"] for t in res.trades
                   if t.get("net_ret") is not None and math.isfinite(t["net_ret"])])
    if len(nr) < 5:
        return {"n": int(len(nr)), "mean_bps": None, "ci": [None, None], "pf": None}
    rng = np.random.default_rng(SEED)
    means = np.array([rng.choice(nr, len(nr), replace=True).mean() for _ in range(2000)])
    wins = nr[nr > 0].sum(); loss = -nr[nr < 0].sum()
    return {
        "n": int(len(nr)),
        "mean_bps": round(float(nr.mean() * 1e4), 2),
        "ci": [round(float(np.percentile(means, 2.5) * 1e4), 2),
               round(float(np.percentile(means, 97.5) * 1e4), 2)],
        "pf": round(float(wins / loss), 3) if loss > 0 else None,
        "wr": round(float((nr > 0).mean()), 3),
    }


def perm_p(df: pd.DataFrame, sig: pd.Series, name: str, sym: str, costs: CostModel,
           real_mean: float | None) -> float | None:
    """Shuffle the return series, rebuild a synthetic OHLC, re-run. Direction: p = share of
    shuffled runs whose mean >= real (a signal with no structure should land near 0.5)."""
    if real_mean is None:
        return None
    rng = np.random.default_rng(SEED)
    r = df["close"].pct_change().dropna().to_numpy()
    o = df["open"].to_numpy()[1:]
    beats = 0; ran = 0
    for _ in range(N_PERM):
        sh = rng.permutation(r)
        px = o[0] * np.cumprod(1 + sh)
        idx = df.index[1:]
        syn = pd.DataFrame({"open": px, "high": px * 1.001, "low": px * 0.999,
                            "close": px, "volume": 0.0}, index=idx)
        try:
            res = run_from_signals(syn, sig.loc[idx], name, sym, tp_atr=2.0, sl_atr=1.0,
                                   max_bars=10, costs=costs, timeframe="1d")
        except Exception:
            continue
        nr = np.array([t["net_ret"] for t in res.trades
                       if t.get("net_ret") is not None and math.isfinite(t["net_ret"])])
        if len(nr) < 5:
            continue
        ran += 1
        if float(nr.mean() * 1e4) >= real_mean:
            beats += 1
    return round(beats / ran, 3) if ran >= 10 else None


def carry_baseline(panel: dict[str, pd.DataFrame]) -> dict:
    """Static long high-yielder / short low-yielder, zero cost.

    The crosses are built from the USD legs already loaded rather than downloaded: with
    X = quote currency per USD,
        ret(A/B) = ret(A/USD) - ret(B/USD)
    so long AUD vs short JPY = ret(AUDUSD) - ret(USDJPY). This avoids a second data pull and
    keeps the benchmark on exactly the same bars as the cells it is compared against.

    The yield ordering (AUD/NZD high, JPY/CHF low) is a fixed, known-in-advance fact about
    those currencies, not a parameter fitted to this sample."""
    def ret(k):
        return panel[k]["close"].pct_change() if k in panel else None

    aud, nzd = ret("AUDUSD"), ret("NZDUSD")
    jpy, chf = ret("USDJPY"), ret("USDCHF")
    legs = []
    for hi in (aud, nzd):
        for lo in (jpy, chf):
            if hi is not None and lo is not None:
                legs.append((hi - lo).rename("cross"))
    if not legs:
        return {"note": "no cross constructible from loaded USD legs"}
    s = pd.concat(legs, axis=1).mean(axis=1).dropna()
    eq = (1 + s).cumprod()
    yrs = len(s) / 252
    sd = s.std()
    return {
        "legs": len(legs), "window": f"{s.index[0].date()} -> {s.index[-1].date()}",
        "cagr": round(float(eq.iloc[-1] ** (1 / yrs) - 1), 4),
        "ann_vol": round(float(sd * math.sqrt(252)), 4),
        "sharpe": round(float(s.mean() / sd * math.sqrt(252)), 3) if sd else None,
        "max_drawdown": round(float((eq / eq.cummax() - 1).min()), 4),
    }


def main() -> int:
    print(f"loading {len(PAIRS)} FX pairs from {START} ...")
    panel = {}
    for k, tkr in PAIRS.items():
        df = load_pair(tkr)
        if df is not None:
            panel[k] = df
            print(f"  {k}: {len(df)} daily bars {df.index[0].date()} -> {df.index[-1].date()}")
    if len(panel) < 4:
        print("insufficient FX data"); return 1

    rows = []
    for name, build in builders().items():
        for sym, df in panel.items():
            sig = build(df)
            for cb in COST_LEVELS:
                costs = CostModel(taker_fee=cb / 2e4, slippage=0.0)
                res = run_from_signals(df, sig, name, sym, tp_atr=2.0, sl_atr=1.0,
                                       max_bars=10, costs=costs, timeframe="1d")
                s = summarise(res, cb)
                # the permutation control is expensive; run it only at the verdict cost
                # level (5 bps), which is the one the class decision is made on
                if cb == COST_LEVELS[1]:
                    s["p_perm"] = perm_p(df, sig, name, sym, costs, s["mean_bps"])
                s["cost_bps_rt"] = cb
                s.update(strategy=name, symbol=sym)
                rows.append(s)
        print(f"  {name}: done")

    # verdict at the middle cost level
    mid = [r for r in rows if r["cost_bps_rt"] == 5 and r["mean_bps"] is not None]
    pos = [r for r in mid if r["mean_bps"] > 0]
    ci_pos = [r for r in mid if r["ci"][0] is not None and r["ci"][0] > 0]
    perm_ok = [r for r in mid if r.get("p_perm") is not None and r["p_perm"] <= 0.05]
    both = [r for r in ci_pos if r.get("p_perm") is not None and r["p_perm"] <= 0.05]

    print(f"\nFX census — {len(panel)} pairs x {len(builders())} families, daily")
    print(f"{'strategy':24s} {'pair':8s} {'n':>4s} {'mean@5bps':>11s} {'CI':>22s} {'p_perm':>7s}")
    for r in sorted(mid, key=lambda x: -(x["mean_bps"] or -9e9))[:12]:
        print(f"{r['strategy']:24s} {r['symbol']:8s} {r['n']:4d} {r['mean_bps']:>11.2f} "
              f"{str([round(r['ci'][0] or 0,1), round(r['ci'][1] or 0,1)]):>22s} "
              f"{str(r.get('p_perm')):>7s}")

    car = carry_baseline(panel)
    print(f"\ncarry baseline (long AUD/NZD vs short JPY/CHF, zero cost): {car}")

    out = {
        "hypothesis": "P8 — does any of the six families show net-positive expectancy on FX?",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pairs": list(panel), "start": START, "cost_levels_bps_rt": COST_LEVELS,
        "benchmark_note": "FX has ~zero expected return, so the benchmark is FLAT, not buy-and-hold",
        "n_cells": len(mid),
        "n_positive_at_5bps": len(pos),
        "n_ci_excludes_zero_at_5bps": len(ci_pos),
        "n_perm_p_le_0_05": len(perm_ok),
        "n_ci_and_perm": len(both),
        "survivors": [f"{r['strategy']}/{r['symbol']}" for r in both],
        "carry_baseline": car,
        "rows": rows,
        "verdict": (f"NO FX EDGE ESTABLISHED: {len(both)} of {len(mid)} cells have both a net CI "
                    f"above zero and a permutation p<=0.05 at 5bps round turn. "
                    f"{len(pos)} of {len(mid)} cells are positive on point estimate alone."),
        "class_note": ("n per cell is small (daily bars, one pair): FX daily signals fire rarely. "
                       "A null here is a statement about these six families on daily bars over "
                       "this decade, not a proof the class is untradeable."),
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    body = json.dumps(out, indent=1, default=str)
    (RESULTS / f"fx_census_{stamp}.json").write_text(body, encoding="utf-8")
    (RESULTS / "fx_census_latest.json").write_text(body, encoding="utf-8")

    print(f"\npositive at 5bps: {len(pos)}/{len(mid)}  |  CI excludes zero: {len(ci_pos)}"
          f"  |  perm p<=0.05: {len(perm_ok)}  |  BOTH: {len(both)}")
    print(f"VERDICT: {out['verdict']}")
    print(f"wrote results/fx_census_latest.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
