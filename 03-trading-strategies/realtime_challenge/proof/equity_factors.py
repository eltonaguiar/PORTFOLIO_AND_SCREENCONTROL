#!/usr/bin/env python3
"""H-E1's question applied to style factors instead of asset classes: do value
(VLUE), quality (QUAL), and low-vol (USMV) — plus momentum (MTUM, the H-E1
reference family) — deliver a harvestable premium once you (a) charge costs on
position changes, (b) scale the benchmark by time-in-market, and (c) compare
against random-exposure and permutation controls?

H-E1 tested 12-1m momentum ETF rotation (top-2, above a 10m SMA) and failed:
Sharpe 0.41 vs SPY 0.62, shuffle p=0.66, strictly dominated by SPY+200d SMA.
This asks whether the *factors themselves* do any better, each timed with the
same frozen rule (12-1m momentum, above the 10-month SMA, signal at month-end
close, fill at the next day's open) and each compared against its own
buy-and-hold.

Decision rule, frozen before running: a factor is ESTABLISHED only if its timed
version beats SPY buy-and-hold on Sharpe, beats exposure-scaled SPY, beats the
random-exposure p95, AND clears the permutation control (p < 0.05). Otherwise
it is a clean negative and is archived — no parameter sweep, no after-the-fact
lookback choice.

  python -m realtime_challenge.proof.equity_factors
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

from realtime_challenge.stats import bootstrap_ci  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "results"
START = "2004-01-01"
COST_PER_SIDE = 0.0005          # equity baseline: 5 bps per side, 10 bps round turn
SMA_M = 10                      # trend filter, months
MOM_M = 12                      # momentum lookback, months
DAYS_M = 21
RANDOM_SCHEDULES = 200
PERMUTATION_SHUFFLES = 100
SEED = 20261122
PPY = 252

UNIVERSE = ["SPY", "VLUE", "QUAL", "USMV", "MTUM"]
FACTORS = ["VLUE", "QUAL", "USMV", "MTUM"]
CLASS_OF = {
    "SPY": "market",
    "VLUE": "value",
    "QUAL": "quality",
    "USMV": "low_vol",
    "MTUM": "momentum",  # H-E1 reference family
}


def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    import yfinance as yf

    raw = yf.download(UNIVERSE, start=START, auto_adjust=True, progress=False, group_by="column")
    close = raw["Close"][UNIVERSE].dropna(how="all")
    open_ = raw["Open"][UNIVERSE].reindex(close.index)
    return close, open_


def month_ends(idx: pd.DatetimeIndex) -> list[int]:
    s = pd.Series(idx, index=idx)
    last = s.groupby([idx.year, idx.month]).tail(1)
    return [idx.get_loc(d) for d in last]


def run_timing(close: pd.DataFrame, open_: pd.DataFrame, ticker: str,
               cost_per_side: float) -> dict:
    """12-1m momentum + 10m SMA trend filter, 0/1 weight, monthly rebalance.

    Signal at the month-end close, fill at the next trading day's open;
    weights live from the fill day's close and the fill day's return is
    measured open->close (identical convention to H-E1 / etf_rotation.py).
    Costs are charged on POSITION changes: |dw| * cost_per_side, so a full
    0->1->0 cycle charges exactly one round turn.
    """
    idx = close.index
    n = len(idx)
    px = close[ticker]
    opn = open_[ticker]
    me = month_ends(idx)

    w = pd.Series(0.0, index=idx)
    fills: list[dict] = []
    for m in me:
        f = m + 1
        if f >= n:
            continue
        if m < MOM_M * DAYS_M + 1:
            continue
        mom = float(px.iloc[m] / px.iloc[m - MOM_M * DAYS_M] - 1.0)
        sma = float(px.iloc[max(0, m - SMA_M * DAYS_M + 1): m + 1].mean())
        above = float(px.iloc[m]) > sma
        w_new = 1.0 if (mom > 0.0 and above) else 0.0
        w.iloc[f:] = w_new
        fills.append({
            "signal_date": str(idx[m].date()),
            "fill_date": str(idx[f].date()),
            "mom": round(mom, 4),
            "above_trend": bool(above),
            "weight": float(w_new),
        })

    r = px.pct_change()
    fill_days = {idx.get_loc(pd.Timestamp(fill["fill_date"])) for fill in fills}
    for i in fill_days:
        r.iloc[i] = float(px.iloc[i] / opn.iloc[i] - 1.0)

    gross = (w.shift(1).fillna(0.0) * r.fillna(0.0))
    turnover = w.diff().abs().fillna(w.abs()).fillna(0.0)
    cost = turnover * cost_per_side
    net = gross - cost

    eq = (1.0 + net).fillna(0.0).cumprod()
    sd = net.std(ddof=1)
    sharpe = float(net.mean() / sd * math.sqrt(PPY)) if sd and sd > 0 else None
    mdd = float((eq / eq.cummax() - 1.0).min())
    yrs = (idx[-1] - idx[0]).days / 365.25
    cagr = float(eq.iloc[-1] ** (1 / yrs) - 1) if eq.iloc[-1] > 0 else None
    exposure = float((w > 0).mean())
    total_cost_bps = float(cost.sum() * 1e4)

    return {
        "ticker": ticker,
        "_w": w,
        "_net": net,
        "cagr": round(cagr, 4) if cagr is not None else None,
        "sharpe": round(sharpe, 3) if sharpe is not None else None,
        "max_drawdown": round(mdd, 4),
        "total_return": round(float(eq.iloc[-1] - 1.0), 4),
        "turnover_per_year": round(float(turnover.sum() / yrs), 2),
        "exposure_frac": round(exposure, 4),
        "total_cost_bps": round(total_cost_bps, 1),
        "n_rebalances": len(fills),
        "window": {"start": str(idx[0].date()), "end": str(idx[-1].date()), "years": round(yrs, 2)},
        "recent_fills": fills[-6:],
    }


def buy_and_hold(px: pd.Series, cost_per_side: float) -> dict:
    r = px.pct_change().fillna(0.0)
    r.iloc[0] -= cost_per_side  # single entry over the whole window
    eq = (1.0 + r).cumprod()
    yrs = (px.index[-1] - px.index[0]).days / 365.25
    sd = r.std(ddof=1)
    sharpe = float(r.mean() / sd * math.sqrt(PPY)) if sd and sd > 0 else None
    return {
        "cagr": round(float(eq.iloc[-1] ** (1 / yrs) - 1), 4),
        "sharpe": round(sharpe, 3) if sharpe is not None else None,
        "max_drawdown": round(float((eq / eq.cummax() - 1.0).min()), 4),
        "total_return": round(float(eq.iloc[-1] - 1.0), 4),
        "turnover_per_year": round(1.0 / yrs, 4),
        "exposure_frac": 1.0,
        "total_cost_bps": round(cost_per_side * 1e4, 1),
    }


def exposure_scaled_spy(bh_total_return: float, exposure: float) -> float:
    """Credit SPY only for the fraction of time the timed strategy is invested
    (cli.py convention: a flat strategy in a falling market does not earn
    credit for sitting out a drawdown)."""
    return round(bh_total_return * exposure, 6)


def random_exposure_control(px: pd.Series, w: pd.Series, cost_per_side: float,
                            n_schedules: int = RANDOM_SCHEDULES, seed: int = SEED) -> dict:
    r = px.pct_change().fillna(0.0)
    exposure = float((w > 0).mean())
    rng = np.random.default_rng(seed)
    n = len(r)
    sharpes = []
    for _ in range(n_schedules):
        wr = (rng.random(n) < exposure).astype(float)
        wr = pd.Series(wr, index=r.index)
        gross = wr.shift(1).fillna(0.0) * r
        turnover = wr.diff().abs().fillna(wr.abs()).fillna(0.0)
        net = gross - turnover * cost_per_side
        sd = net.std(ddof=1)
        if sd and sd > 0 and len(net) > 1:
            sharpes.append(float(net.mean() / sd * math.sqrt(PPY)))
    arr = np.asarray(sharpes)
    return {
        "exposure": round(exposure, 4),
        "n_schedules": int(len(sharpes)),
        "sharpe_mean": round(float(arr.mean()), 3) if len(sharpes) else None,
        "sharpe_p95": round(float(np.quantile(arr, 0.95)), 3) if len(sharpes) else None,
        "sharpe_median": round(float(np.median(arr)), 3) if len(sharpes) else None,
    }


def permutation_control(close: pd.DataFrame, open_: pd.DataFrame, ticker: str,
                        cost_per_side: float, n_shuffles: int = PERMUTATION_SHUFFLES,
                        seed: int = SEED) -> dict:
    idx = close.index
    px = close[ticker]
    rets = px.pct_change().dropna().to_numpy(float)
    rng = np.random.default_rng(seed)
    real = run_timing(close, open_, ticker, cost_per_side)
    real_sharpe = real["sharpe"]
    sims = []
    for _ in range(n_shuffles):
        perm = rng.permutation(rets)
        path = np.cumprod(np.insert(1.0 + perm, 0, 1.0))
        fake_px = pd.Series(np.nan, index=idx)
        fake_px.iloc[-len(path):] = path
        fake_px = fake_px.ffill().bfill()
        fake_opn = fake_px.shift(1).bfill()
        fake_close = pd.DataFrame({ticker: fake_px})
        fake_open = pd.DataFrame({ticker: fake_opn})
        try:
            res = run_timing(fake_close, fake_open, ticker, cost_per_side)
            if res["sharpe"] is not None:
                sims.append(res["sharpe"])
        except Exception:
            continue
    arr = np.asarray(sims) if sims else np.asarray([float("nan")])
    p = float((arr >= real_sharpe).mean()) if real_sharpe is not None and sims else None
    return {
        "real": real_sharpe,
        "shuffled_median": round(float(np.median(arr)), 3) if sims else None,
        "p95": round(float(np.quantile(arr, 0.95)), 3) if sims else None,
        "p_value": None if p is None else round(p, 4),
        "n_shuffles": int(len(sims)),
    }


def main() -> int:
    print(f"loading {len(UNIVERSE)} ETFs from {START} ...")
    close, open_ = load()
    print(f"  {close.shape[1]} series, {len(close)} daily bars, "
          f"{close.index[0].date()} -> {close.index[-1].date()}")
    spy_bh = buy_and_hold(close["SPY"], COST_PER_SIDE)
    print(f"  SPY buy-and-hold: CAGR {spy_bh['cagr']:.2%} Sharpe {spy_bh['sharpe']} "
          f"maxDD {spy_bh['max_drawdown']:.2%} cost {spy_bh['total_cost_bps']} bps")
    rows = []
    timed_cache = {}
    for ticker in FACTORS:
        timed = run_timing(close, open_, ticker, COST_PER_SIDE)
        timed_cache[ticker] = timed
        bh = buy_and_hold(close[ticker], COST_PER_SIDE)
        rand = random_exposure_control(close[ticker], timed["_w"], COST_PER_SIDE)
        perm = permutation_control(close, open_, ticker, COST_PER_SIDE)
        beats_spy_sharpe = (timed["sharpe"] is not None and spy_bh["sharpe"] is not None
                            and timed["sharpe"] > spy_bh["sharpe"])
        beats_exposure_scaled = timed["total_return"] > exposure_scaled_spy(
            spy_bh["total_return"], timed["exposure_frac"])
        beats_random_p95 = (timed["sharpe"] is not None and rand["sharpe_p95"] is not None
                            and timed["sharpe"] > rand["sharpe_p95"])
        clears_perm = perm["p_value"] is not None and perm["p_value"] < 0.05
        established = all([beats_spy_sharpe, beats_exposure_scaled, beats_random_p95, clears_perm])
        net_drop = timed["_net"].dropna()
        ci = bootstrap_ci(net_drop.to_numpy(float)) if len(net_drop) > 2 else None
        row = {
            "ticker": ticker, "class": CLASS_OF[ticker],
            "timed": {k: v for k, v in timed.items() if k not in ("_w", "_net")},
            "buy_and_hold": bh,
            "spy_buy_and_hold": spy_bh,
            "exposure_scaled_spy_return": exposure_scaled_spy(
                spy_bh["total_return"], timed["exposure_frac"]),
            "random_exposure": rand,
            "permutation": perm,
            "mean_net_ci": ci,
            "checks": {
                "beats_spy_sharpe": beats_spy_sharpe,
                "beats_exposure_scaled_spy": beats_exposure_scaled,
                "beats_random_exposure_p95": beats_random_p95,
                "clears_permutation_p_lt_05": clears_perm,
            },
            "established": bool(established),
        }
        rows.append(row)
        print(f"  {ticker} ({CLASS_OF[ticker]}): timed Sharpe {timed['sharpe']} vs SPY {spy_bh['sharpe']} | "
              f"exposure {timed['exposure_frac']:.2%} random p95 {rand['sharpe_p95']} | "
              f"perm p={perm['p_value']} | established={established}")


    nets = [timed_cache[r["ticker"]]["_net"] for r in rows]
    port_net = pd.concat(nets, axis=1).mean(axis=1)
    port_w = pd.concat([timed_cache[r["ticker"]]["_w"] for r in rows], axis=1).mean(axis=1)
    port_eq = (1.0 + port_net).cumprod()
    port_sd = port_net.std(ddof=1)
    port_sharpe = float(port_net.mean() / port_sd * math.sqrt(PPY)) if port_sd and port_sd > 0 else None
    port_mdd = float((port_eq / port_eq.cummax() - 1.0).min())
    port_yrs = (close.index[-1] - close.index[0]).days / 365.25
    port_cagr = float(port_eq.iloc[-1] ** (1 / port_yrs) - 1) if port_eq.iloc[-1] > 0 else None
    port_exposure = float((port_w > 0).mean())
    port_established = (port_sharpe is not None and spy_bh["sharpe"] is not None
                        and port_sharpe > spy_bh["sharpe"]
                        and port_net.mean() * PPY > exposure_scaled_spy(
                            spy_bh["total_return"], port_exposure)
                        and port_sharpe is not None
                        and all(r["random_exposure"]["sharpe_p95"] is not None
                                and port_sharpe > r["random_exposure"]["sharpe_p95"] for r in rows)
                        and all(r["permutation"]["p_value"] is not None
                                and r["permutation"]["p_value"] < 0.05 for r in rows))
    portfolio_row = {
        "ticker": "EQUAL_WEIGHT_4_FACTOR", "class": "multi_factor",
        "timed": {
            "cagr": round(port_cagr, 4) if port_cagr is not None else None,
            "sharpe": round(port_sharpe, 3) if port_sharpe is not None else None,
            "max_drawdown": round(port_mdd, 4),
            "total_return": round(float(port_eq.iloc[-1] - 1.0), 4),
            "turnover_per_year": None,
            "exposure_frac": round(port_exposure, 4),
            "total_cost_bps": None,
            "n_rebalances": None,
            "window": {"start": str(close.index[0].date()), "end": str(close.index[-1].date()),
                       "years": round(port_yrs, 2)},
            "recent_fills": [],
        },
        "buy_and_hold": None,
        "spy_buy_and_hold": spy_bh,
        "exposure_scaled_spy_return": exposure_scaled_spy(spy_bh["total_return"], port_exposure),
        "random_exposure": None,
        "permutation": None,
        "mean_net_ci": bootstrap_ci(port_net.dropna().to_numpy(float)) if len(port_net.dropna()) > 2 else None,
        "checks": {
            "beats_spy_sharpe": port_sharpe is not None and spy_bh["sharpe"] is not None
            and port_sharpe > spy_bh["sharpe"],
            "beats_exposure_scaled_spy": port_net.mean() * PPY > exposure_scaled_spy(
                spy_bh["total_return"], port_exposure),
            "beats_random_exposure_p95": all(
                r["random_exposure"]["sharpe_p95"] is not None and port_sharpe is not None
                and port_sharpe > r["random_exposure"]["sharpe_p95"] for r in rows),
            "clears_permutation_p_lt_05": all(
                r["permutation"]["p_value"] is not None
                and r["permutation"]["p_value"] < 0.05 for r in rows),
        },
        "established": bool(port_established),
    }
    any_established = any(r["established"] for r in rows) or portfolio_row["established"]
    verdict = ("ESTABLISHED: at least one factor clears all four checks" if any_established
               else "CLEAN NEGATIVE: no factor beats SPY on Sharpe after the exposure, "
               "random-exposure, and permutation controls")
    out = {
        "question": ("do value/quality/low-vol (and momentum as the H-E1 reference) deliver a harvestable "
                     "equity factor premium once costs are charged on position changes, the benchmark is "
                     "scaled by time-in-market, and random-exposure + permutation controls are applied?"),
        "reference": "H-E1 dual-momentum ETF rotation (archived: Sharpe 0.41 vs SPY 0.62, shuffle p=0.66)",
        "rule": "12-1m momentum, above 10m SMA, signal at month-end close, fill at next day's open, 0/1 weight",
        "cost_per_side_bps": round(COST_PER_SIDE * 1e4, 1),
        "round_trip_bps": round(COST_PER_SIDE * 2e4, 1),
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "universe": UNIVERSE, "class_of": CLASS_OF,
        "window": {"start": str(close.index[0].date()), "end": str(close.index[-1].date())},
        "spy_buy_and_hold": spy_bh,
        "factors": rows,
        "portfolio": portfolio_row,
        "verdict": verdict,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    body = json.dumps(out, indent=1, default=str)
    (OUT / f"equity_factors_{stamp}.json").write_text(body, encoding="utf-8")
    (OUT / "equity_factors_latest.json").write_text(body, encoding="utf-8")
    print(f"\n{'ticker':22s} {'class':12s} {'timed Sharpe':>12s} {'SPY Sharpe':>10s} {'exp':>6s} "
          f"{'rand p95':>9s} {'perm p':>8s} {'est.':>6s}")
    for r in rows + [portfolio_row]:
        t = r["timed"]
        print(f"{r['ticker']:22s} {r['class']:12s} {str(t['sharpe']):>12s} {str(spy_bh['sharpe']):>10s} "
              f"{t['exposure_frac']:>6.2%} {str(r['random_exposure']['sharpe_p95'] if r['random_exposure'] else None):>9s} "
              f"{str(r['permutation']['p_value'] if r['permutation'] else None):>8s} {str(r['established']):>6s}")
    print(f"\nVERDICT: {verdict}")
    print(f"wrote results/equity_factors_latest.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
