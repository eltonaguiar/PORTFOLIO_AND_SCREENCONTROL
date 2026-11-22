#!/usr/bin/env python3
"""H-E1: does ETF rotation + trend following survive costs? (tests a peer's hypothesis)

A peer note (Copilot/GPT-5, 2026-11-22) states its central hypothesis:

    "the best chance of success is ETF Rotation + Trend Following + Multi-Asset Portfolio
     rather than Day Trading / Scalping / Options, because those tend to break down under
     realistic fills and transaction costs."

That is a testable, directional claim about which class to spend 200 rounds on. It is the
first hypothesis in this project that points at LOW frequency, so it is worth testing
properly rather than deferring to "equities are closed on Sunday" — daily history needs no
open market.

The rule (dual momentum, frozen before running):

    universe   : 10 liquid US ETFs spanning 6 asset classes
    signal     : 12-1 month momentum = close[t] / close[t-12m] - 1, skipping the last month
                 to avoid the short-term reversal that contaminates raw 12m momentum
    absolute   : hold only if close > 10-month SMA (the "trend following" leg)
    ranking    : cross-sectional; hold the top K = 2, equal weight
    rebalance  : monthly. Signal at the month-end CLOSE, fill at the NEXT trading day's OPEN.
                 Weights are effective from the fill day's close, and the fill day's return is
                 measured open -> close, so a rebalance cannot be filled at a price that was
                 not available.
    costs      : 5 bps per side at baseline (zero-commission broker + ~1-2 bp spread on
                 liquid ETFs, rounded up to 5), with a sweep to 26 bps for a poor fill
    benchmark  : SPY buy-and-hold, same window, same cost model

Controls, because a 22-year rotation Sharpe is exactly the kind of number that looks good
for the wrong reason:
    1. buy-and-hold SPY on the same window
    2. a PERMUTATION control that shuffles each ETF's daily returns independently, which
       destroys cross-sectional momentum while preserving each series' own volatility
    3. sub-period stability across three regimes
    4. parameter neighbours (K = 1, 2, 3 and a 6m vs 12m lookback) to check for a plateau
       rather than a single lucky peak

  python -m realtime_challenge.proof.etf_rotation
"""

from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent.parent / "results" / "etf_rotation.json"

UNIVERSE = ["SPY", "QQQ", "IWM", "EFA", "EEM", "TLT", "IEF", "GLD", "DBC", "VNQ"]
CLASS_OF = {
    "SPY": "us_large", "QQQ": "us_tech", "IWM": "us_small",
    "EFA": "intl_developed", "EEM": "emerging",
    "TLT": "long_treasury", "IEF": "mid_treasury",
    "GLD": "gold", "DBC": "commodities", "VNQ": "reit",
}
START = "2004-01-01"
COST_PER_SIDE = 0.0005      # baseline 5 bps
SPY_BNH_COST = 0.0005


def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    import yfinance as yf

    raw = yf.download(UNIVERSE, start=START, auto_adjust=True, progress=False, group_by="column")
    close = raw["Close"][UNIVERSE].dropna(how="all")
    open_ = raw["Open"][UNIVERSE].reindex(close.index)
    return close, open_


def month_end_positions(idx: pd.DatetimeIndex) -> list[int]:
    """Index positions of the last trading day of each month."""
    s = pd.Series(idx, index=idx)
    last = s.groupby([idx.year, idx.month]).tail(1)
    return [idx.get_loc(d) for d in last]


def run_rotation(close: pd.DataFrame, open_: pd.DataFrame, k: int, lookback_m: int,
                 abs_filter_m: int, cost_per_side: float = COST_PER_SIDE) -> dict:
    idx = close.index
    n = len(idx)
    me = month_end_positions(idx)

    # weights effective from the fill day's close, one row per trading day
    W = pd.DataFrame(0.0, index=idx, columns=close.columns)
    fills: list[dict] = []

    for m in me:
        fill = m + 1                      # next trading day, executed at its open
        if fill >= n:
            continue
        if m < lookback_m * 21 + 1:       # not enough history
            continue

        px_now = close.iloc[m]
        px_old = close.iloc[m - lookback_m * 21]
        mom = (px_now / px_old - 1.0).dropna()

        sma = close.iloc[max(0, m - abs_filter_m * 21 + 1):m + 1].mean()
        above = px_now > sma                     # absolute momentum / trend filter
        elig = mom[above.reindex(mom.index).fillna(False)]
        elig = elig[elig.notna() & (elig > 0)]   # must be above trend AND positive momentum

        picks = list(elig.sort_values(ascending=False).head(k).index)
        if picks:
            W.iloc[fill:] = 0.0
            W.loc[idx[fill]:, picks] = 1.0 / len(picks)
            fills.append({"signal_date": str(idx[m].date()), "fill_date": str(idx[fill].date()),
                          "picks": picks, "mom": {p: round(float(mom[p]), 4) for p in picks}})
        else:
            W.iloc[fill:] = 0.0                # all cash: nothing above trend
            fills.append({"signal_date": str(idx[m].date()), "fill_date": str(idx[fill].date()),
                          "picks": [], "mom": {}})

    # daily returns: fill day uses open -> close, all other days close -> close
    ret = close.pct_change()
    fill_days = {idx.get_loc(pd.Timestamp(f["fill_date"])) for f in fills}
    for i in fill_days:
        ret.iloc[i] = (close.iloc[i] / open_.iloc[i] - 1.0)

    gross = (W.shift(0) * ret.shift(0)).sum(axis=1)
    # weights set at close of day i earn day i+1's return
    gross = (W.shift(1) * ret).sum(axis=1).fillna(0.0)

    turnover = W.diff().abs().sum(axis=1).fillna(W.abs().sum(axis=1)).fillna(0.0)
    costs = turnover * cost_per_side
    net = gross - costs

    eq = (1.0 + net).cumprod()
    sd = net.std(ddof=1)
    sharpe = None if sd == 0 else float(net.mean() / sd * math.sqrt(252))
    mdd = float((eq / eq.cummax() - 1.0).min())
    yrs = (idx[-1] - idx[0]).days / 365.25
    cagr = float(eq.iloc[-1] ** (1 / yrs) - 1) if eq.iloc[-1] > 0 else None

    return {
        "k": k, "lookback_m": lookback_m, "abs_filter_m": abs_filter_m,
        "cost_per_side": cost_per_side,
        "years": round(yrs, 2),
        "cagr": None if cagr is None else round(cagr, 4),
        "sharpe": None if sharpe is None else round(sharpe, 3),
        "max_drawdown": round(mdd, 4),
        "total_return": round(float(eq.iloc[-1] - 1), 4),
        "avg_turnover_per_year": round(float(turnover.sum() / yrs), 2),
        "pct_days_in_market": round(float((W.sum(axis=1) > 0).mean()), 3),
        "n_rebalances": len(fills),
        "equity": eq,            # not serialised
        "net": net,
        "fills": fills,
    }


def buy_and_hold(close: pd.Series, cost: float = SPY_BNH_COST) -> dict:
    r = close.pct_change().fillna(0.0)
    r.iloc[0] = close.iloc[0] / close.iloc[0] - 1.0
    r = r - 0.0
    r.iloc[0] -= cost
    eq = (1 + r).cumprod()
    yrs = (close.index[-1] - close.index[0]).days / 365.25
    sd = r.std(ddof=1)
    return {
        "cagr": round(float(eq.iloc[-1] ** (1 / yrs) - 1), 4),
        "sharpe": round(float(r.mean() / sd * math.sqrt(252)), 3) if sd else None,
        "max_drawdown": round(float((eq / eq.cummax() - 1).min()), 4),
        "total_return": round(float(eq.iloc[-1] - 1), 4),
        "equity": eq,
    }


def permutation_control(close: pd.DataFrame, open_: pd.DataFrame, n_perm: int = 100,
                        seed: int = 20261122) -> dict:
    """Shuffle each ETF's daily returns independently, rebuild prices, re-run.

    This destroys the CROSS-SECTIONAL structure (which ETF is doing better than which) while
    keeping every series' own volatility and drift. If the real Sharpe is inside that
    distribution, the rotation result is not evidence of momentum.
    """
    real = run_rotation(close, open_, k=2, lookback_m=12, abs_filter_m=10)
    real_sharpe = real["sharpe"]
    rets = close.pct_change().dropna()
    rng = np.random.default_rng(seed)
    sims = []
    for _ in range(n_perm):
        fake = {}
        for c in close.columns:
            r = rets[c].dropna().to_numpy()
            path = close[c].dropna().iloc[0] * np.cumprod(1 + rng.permutation(r))
            col = pd.Series(np.nan, index=close.index)
            col.iloc[-len(path):] = path
            fake[c] = col.ffill().bfill()
        fc = pd.DataFrame(fake)
        fo = fc.shift(1).bfill()
        try:
            res = run_rotation(fc, fo, k=2, lookback_m=12, abs_filter_m=10)
            if res["sharpe"] is not None:
                sims.append(res["sharpe"])
        except Exception:
            continue
    if not sims:
        return {"real": real_sharpe, "p_value": None, "n_perm": 0}
    arr = np.asarray(sims)
    return {
        "real": real_sharpe,
        "shuffled_median": round(float(np.median(arr)), 3),
        "p95": round(float(np.quantile(arr, 0.95)), 3),
        "p_value": None if real_sharpe is None else round(float((arr >= real_sharpe).mean()), 4),
        "n_perm": len(arr),
    }


def main() -> int:
    print(f"loading {len(UNIVERSE)} ETFs from {START} ...")
    close, open_ = load()
    span_yrs = (close.index[-1] - close.index[0]).days / 365.25
    print(f"  {close.shape[1]} series, {len(close)} daily bars, "
          f"{close.index[0].date()} -> {close.index[-1].date()} ({span_yrs:.1f} y)")

    # ---- the pre-registered rule
    base = run_rotation(close, open_, k=2, lookback_m=12, abs_filter_m=10)
    spy = buy_and_hold(close["SPY"])
    eq_bench = (1 + close["SPY"].pct_change().fillna(0)).cumprod()

    # ---- cost sensitivity on the SAME rule
    cost_rows = []
    for cps in (0.0, 0.0002, 0.0005, 0.0013, 0.0026):
        r = run_rotation(close, open_, k=2, lookback_m=12, abs_filter_m=10, cost_per_side=cps)
        cost_rows.append({"cost_per_side_bps": round(cps * 1e4, 1),
                          "round_trip_bps": round(cps * 2e4, 1),
                          "cagr": r["cagr"], "sharpe": r["sharpe"],
                          "max_drawdown": r["max_drawdown"], "total_return": r["total_return"]})

    # ---- parameter neighbours: plateau or spike?
    neighbours = []
    for k in (1, 2, 3):
        for lb in (6, 12):
            r = run_rotation(close, open_, k=k, lookback_m=lb, abs_filter_m=10)
            neighbours.append({"k": k, "lookback_m": lb, "cagr": r["cagr"],
                               "sharpe": r["sharpe"], "max_drawdown": r["max_drawdown"],
                               "turnover_per_year": r["avg_turnover_per_year"]})

    # ---- sub-period stability
    periods = []
    for label, (a, b) in {"2004-2012": ("2004-01-01", "2012-12-31"),
                          "2013-2019": ("2013-01-01", "2019-12-31"),
                          "2020-2026": ("2020-01-01", "2026-12-31")}.items():
        sl = (close.index >= a) & (close.index <= b)
        if sl.sum() < 300:
            continue
        c2, o2 = close[sl], open_[sl]
        r = run_rotation(c2, o2, k=2, lookback_m=12, abs_filter_m=10)
        bh = buy_and_hold(c2["SPY"])
        periods.append({"period": label, "rotation_sharpe": r["sharpe"], "rotation_cagr": r["cagr"],
                        "rotation_maxdd": r["max_drawdown"], "spy_sharpe": bh["sharpe"],
                        "spy_cagr": bh["cagr"], "spy_maxdd": bh["max_drawdown"]})

    print("\npermutation control (shuffled cross-section, 100 sims) ...")
    perm = permutation_control(close, open_, n_perm=100)

    # ---- verdict arithmetic
    excess_cagr = None
    if base["cagr"] is not None and spy["cagr"] is not None:
        excess_cagr = round(base["cagr"] - spy["cagr"], 4)
    beats_spy_cagr = excess_cagr is not None and excess_cagr > 0
    beats_spy_sharpe = base["sharpe"] is not None and spy["sharpe"] is not None and base["sharpe"] > spy["sharpe"]
    survives_perm = perm.get("p_value") is not None and perm["p_value"] < 0.05

    if beats_spy_cagr and beats_spy_sharpe and survives_perm:
        verdict = "PROMOTE: beats SPY on both CAGR and Sharpe and exceeds the shuffled cross-section"
    elif beats_spy_sharpe and survives_perm:
        verdict = "CANDIDATE: better risk-adjusted than SPY and beats the shuffle, but not higher CAGR"
    elif beats_spy_sharpe:
        verdict = "NOT ESTABLISHED: better Sharpe than SPY, but the shuffle control says the cross-section carries no edge"
    else:
        verdict = "FAILS: does not beat buy-and-hold SPY on either CAGR or Sharpe"

    out = {
        "hypothesis": "H-E1 dual momentum ETF rotation (12-1m, top-2, above 10m SMA)",
        "tests_peer_claim": "ETF rotation + trend following + multi-asset beats day trading after costs",
        "peer": "Copilot / GPT-5 note, 2026-11-22",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "universe": UNIVERSE, "class_of": CLASS_OF,
        "window": {"start": str(close.index[0].date()), "end": str(close.index[-1].date()),
                   "years": round(span_yrs, 2)},
        "execution_convention": "signal at month-end close, fill at next trading day OPEN, weights live from that close",
        "base": {k: v for k, v in base.items() if k not in ("equity", "net", "fills")},
        "spy_buy_and_hold": {k: v for k, v in spy.items() if k != "equity"},
        "excess_cagr_vs_spy": excess_cagr,
        "cost_sensitivity": cost_rows,
        "parameter_neighbours": neighbours,
        "sub_periods": periods,
        "permutation": perm,
        "verdict": verdict,
        "recent_fills": base["fills"][-6:],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")

    print(f"\n{'':28s} {'CAGR':>8s} {'Sharpe':>8s} {'maxDD':>8s} {'total':>10s}")
    print(f"{'H-E1 rotation (k=2, 12-1m)':28s} {base['cagr']:>8.2%} {base['sharpe']:>8.2f} "
          f"{base['max_drawdown']:>8.2%} {base['total_return']:>10.1%}")
    print(f"{'SPY buy and hold':28s} {spy['cagr']:>8.2%} {spy['sharpe']:>8.2f} "
          f"{spy['max_drawdown']:>8.2%} {spy['total_return']:>10.1%}")
    print(f"\nturnover/yr {base['avg_turnover_per_year']}, in-market {base['pct_days_in_market']:.0%}, "
          f"{base['n_rebalances']} rebalances")
    print("\ncost sensitivity (round-trip bps -> Sharpe):")
    for r in cost_rows:
        print(f"  {r['round_trip_bps']:5.1f} bps  sharpe={r['sharpe']}  cagr={r['cagr']}")
    print("\nparameter neighbours (plateau check):")
    for r in neighbours:
        print(f"  k={r['k']} lookback={r['lookback_m']:2d}m  sharpe={r['sharpe']}  cagr={r['cagr']}")
    print("\nsub-periods:")
    for r in periods:
        print(f"  {r['period']}  rot sharpe={r['rotation_sharpe']} cagr={r['rotation_cagr']}  |  "
              f"spy sharpe={r['spy_sharpe']} cagr={r['spy_cagr']}")
    print(f"\npermutation: real={perm['real']} p95(shuffled)={perm.get('p95')} p={perm.get('p_value')}")
    print(f"\nVERDICT: {verdict}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
