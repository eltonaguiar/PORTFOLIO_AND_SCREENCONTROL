"""Statistics that are allowed to kill a result.

Everything here exists to answer one question: given that we looked at N ideas, is
this one's apparent edge bigger than what luck produces? If a function returns a
number, its units and its convention are documented, because in this domain the
number is where the self-deception lives.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Sequence

import numpy as np

EULER = 0.5772156649015329


def profit_factor(net_rets: Sequence[float]) -> Optional[float]:
    """Gross wins / gross losses, in return units (not dollars). inf if no losses."""
    r = np.asarray(net_rets, dtype=float)
    if r.size == 0:
        return None
    wins = r[r > 0].sum()
    losses = -r[r < 0].sum()
    if losses == 0:
        return float("inf") if wins > 0 else 0.0
    return float(wins / losses)


def win_rate(net_rets: Sequence[float]) -> Optional[float]:
    r = np.asarray(net_rets, dtype=float)
    if r.size == 0:
        return None
    return float((r > 0).mean())


def expectancy_r(rs: Sequence[float]) -> Optional[float]:
    """Mean R-multiple. 1R = the distance that was risked at the stop."""
    r = np.asarray(rs, dtype=float)
    if r.size == 0:
        return None
    return float(r.mean())


def sharpe(returns: Sequence[float], periods_per_year: float) -> Optional[float]:
    """Annualised Sharpe from per-period returns; rf assumed 0 (stated, not hidden)."""
    r = np.asarray(returns, dtype=float)
    if r.size < 3 or r.std(ddof=1) == 0:
        return None
    return float(r.mean() / r.std(ddof=1) * math.sqrt(periods_per_year))


def max_drawdown(equity: Sequence[float]) -> float:
    e = np.asarray(equity, dtype=float)
    if e.size < 2:
        return 0.0
    peak = np.maximum.accumulate(e)
    return float((e / peak - 1.0).min())


def per_trade_sharpe(net_rets: Sequence[float]) -> Optional[float]:
    """Sharpe per trade (not annualised) — the input to the deflated Sharpe."""
    r = np.asarray(net_rets, dtype=float)
    if r.size < 3 or r.std(ddof=1) == 0:
        return None
    return float(r.mean() / r.std(ddof=1))


def bootstrap_ci(
    values: Sequence[float], n_boot: int = 5000, alpha: float = 0.05, seed: int = 20261122
) -> Dict[str, float]:
    """Percentile bootstrap CI for the mean. Deterministic given the seed."""
    v = np.asarray(values, dtype=float)
    if v.size < 3:
        return {"mean": float(v.mean()) if v.size else float("nan"), "lo": float("nan"), "hi": float("nan"), "n": int(v.size)}
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, v.size, size=(n_boot, v.size))
    means = v[idx].mean(axis=1)
    return {
        "mean": float(v.mean()),
        "lo": float(np.quantile(means, alpha / 2)),
        "hi": float(np.quantile(means, 1 - alpha / 2)),
        "n": int(v.size),
        "p_gt_zero": float((means > 0).mean()),
    }


def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _norm_ppf(p: float) -> float:
    """Acklam's approximation — adequate for p in (1e-6, 1-1e-6)."""
    if p <= 0.0:
        return float("-inf")
    if p >= 1.0:
        return float("inf")
    a = [-3.969683028665376e01, 2.209460984245205e02, -2.759285104469687e02,
         1.383577518672690e02, -3.066479806614716e01, 2.506628277459239e00]
    b = [-5.447609879822406e01, 1.615858368580409e02, -1.556989798598866e02,
         6.680131188771972e01, -1.328068155288572e01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e00,
         -2.549732539343734e00, 4.374664141464968e00, 2.938163982698783e00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e00,
         3.754408661907416e00]
    plow, phigh = 0.02425, 1 - 0.02425
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    if p > phigh:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
                ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    q = p - 0.5
    r = q * q
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
           (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)


def deflated_sharpe(
    net_rets: Sequence[float], n_trials: int, sr_variance_across_trials: Optional[float] = None
) -> Dict[str, Optional[float]]:
    """Bailey & Lopez de Prado deflated Sharpe.

    sr            : observed per-trade Sharpe
    sr0           : expected maximum Sharpe from `n_trials` independent trials
    dsr           : probability the true Sharpe exceeds sr0 (>0.95 is the usual bar)
    """
    r = np.asarray(net_rets, dtype=float)
    n = r.size
    if n < 10:
        return {"sr": None, "sr0": None, "dsr": None, "n": int(n), "note": "n<10 too small"}
    sr = per_trade_sharpe(r)
    if sr is None:
        return {"sr": None, "sr0": None, "dsr": None, "n": int(n), "note": "zero variance"}

    var_sr = sr_variance_across_trials if sr_variance_across_trials else (1.0 / max(n, 2))
    sigma_sr = math.sqrt(max(var_sr, 1e-12))
    N = max(int(n_trials), 2)
    sr0 = sigma_sr * ((1 - EULER) * _norm_ppf(1 - 1.0 / N) + EULER * _norm_ppf(1 - 1.0 / (N * math.e)))

    skew = float(((r - r.mean()) ** 3).mean() / (r.std(ddof=0) ** 3 + 1e-12))
    kurt = float(((r - r.mean()) ** 4).mean() / (r.std(ddof=0) ** 4 + 1e-12))
    denom = math.sqrt(max(1 - skew * sr + (kurt - 1) / 4.0 * sr ** 2, 1e-9))
    z = (sr - sr0) * math.sqrt(n - 1) / denom
    return {
        "sr": round(sr, 4),
        "sr0": round(sr0, 4),
        "dsr": round(_norm_cdf(z), 4),
        "n": int(n),
        "n_trials": N,
        "skew": round(skew, 3),
        "kurtosis": round(kurt, 3),
    }


def permutation_control(
    df,
    signal_builder,
    *,
    n_perm: int = 200,
    seed: int = 20261122,
    engine_kwargs: Optional[dict] = None,
    metric: str = "mean_net",
) -> Dict[str, float]:
    """Shuffle bar-to-bar CLOSE RETURNS, rebuild a price path, re-run the strategy.

    If the strategy does as well on shuffled prices as on real ones, the "edge" is
    a property of the signal+holding rule, not of market structure. Returns the
    realised metric and the shuffled distribution it must beat.
    """
    import pandas as pd
    from .engine import run_from_signals

    engine_kwargs = engine_kwargs or {}
    real = run_from_signals(df, signal_builder(df), strategy="perm_real", symbol="x", **engine_kwargs)
    real_metric = _metric(real.trades, metric)

    rets = df["close"].pct_change().dropna().to_numpy(float)
    rng = np.random.default_rng(seed)
    shuffled: List[float] = []
    for _ in range(n_perm):
        perm = rng.permutation(rets)
        path = np.cumprod(np.insert(1.0 + perm, 0, 1.0))
        fake = pd.DataFrame(
            {
                "open": np.r_[df["open"].iloc[0], path[:-1]] * 1.0,
                "high": path * 1.0015,
                "low": path * 0.9985,
                "close": path,
                "volume": float(df["volume"].mean()),
            },
            index=df.index[: len(path)],
        )
        try:
            r = run_from_signals(fake, signal_builder(fake), strategy="perm", symbol="x", **engine_kwargs)
            m = _metric(r.trades, metric)
            if m is not None:
                shuffled.append(m)
        except Exception:
            continue

    if not shuffled:
        return {"real": real_metric, "p95": None, "p_value": None, "n_perm": 0}
    arr = np.asarray(shuffled, dtype=float)
    p = float((arr >= real_metric).mean()) if real_metric is not None else None
    return {
        "real": None if real_metric is None else round(real_metric, 6),
        "shuffled_median": round(float(np.median(arr)), 6),
        "p95": round(float(np.quantile(arr, 0.95)), 6),
        "p_value": None if p is None else round(p, 4),
        "n_perm": len(shuffled),
    }


def _metric(trades: List[dict], metric: str):
    if not trades:
        return None
    r = np.asarray([t["net_ret"] for t in trades], dtype=float)
    if metric == "mean_net":
        return float(r.mean())
    if metric == "total_net":
        return float(np.prod(1 + r) - 1)
    if metric == "pf":
        return profit_factor(r)
    raise ValueError(metric)


def summarise(trades: List[dict], equity: Sequence[float], periods_per_year: float) -> Dict:
    if not trades:
        return {
            "n": 0, "win_rate": None, "profit_factor": None, "expectancy_r": None,
            "total_return": 0.0, "max_drawdown": 0.0, "sharpe_annual": None,
            "mean_net": None, "mean_net_ci_lo": None, "mean_net_ci_hi": None,
            "exit_mix": {}, "best": None, "worst": None,
        }
    net = [t["net_ret"] for t in trades]
    rs = [t["r_multiple"] for t in trades if t.get("r_multiple") is not None]
    exit_mix: Dict[str, int] = {}
    for t in trades:
        exit_mix[t["exit_reason"]] = exit_mix.get(t["exit_reason"], 0) + 1
    eq = list(equity) if equity else [1.0]
    ci = bootstrap_ci(net)
    return {
        "n": len(trades),
        "win_rate": round(win_rate(net), 4),
        "profit_factor": None if profit_factor(net) is None else round(profit_factor(net), 4),
        "expectancy_r": None if expectancy_r(rs) is None else round(expectancy_r(rs), 4),
        "total_return": round(float(eq[-1] - 1.0), 6),
        "max_drawdown": round(max_drawdown(eq), 6),
        "sharpe_annual": None if sharpe(net, periods_per_year) is None else round(sharpe(net, periods_per_year), 3),
        "mean_net": round(ci["mean"], 6),
        "mean_net_ci_lo": round(ci["lo"], 6) if ci["lo"] == ci["lo"] else None,
        "mean_net_ci_hi": round(ci["hi"], 6) if ci["hi"] == ci["hi"] else None,
        "exit_mix": exit_mix,
        "best": round(max(net), 6),
        "worst": round(min(net), 6),
    }
