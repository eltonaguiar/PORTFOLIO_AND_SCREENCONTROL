"""
validation_toolkit.py
=====================
Backtest-integrity statistics a professional actually checks, implemented
with no dependencies beyond numpy/scipy.

Contents
--------
 1. Performance primitives      : sharpe, sortino, ann_return, drawdown, tail_ratio
 2. Sharpe uncertainty          : se_sharpe, block_bootstrap_sr_ci
 3. Probabilistic Sharpe Ratio  : psr, min_trl
 4. Deflated Sharpe Ratio       : expected_max_sr, dsr, effective_n_trials
 5. PBO / CSCV                  : pbo_cscv
 6. Walk-forward efficiency     : wfe
 7. Cost & capacity             : breakeven_cost_bps, capacity_curve
 8. Power / sample size         : required_years, power_at
 9. Multiple-testing helpers    : haircut_pvalue, bh_fdr, romanowolf_threshold
10. Self-test / demo            : python3 validation_toolkit.py

Conventions
-----------
* Input returns are SIMPLE periodic returns (e.g. monthly), as a 1-D array
  or a (T x N) matrix where each column is one strategy configuration.
* "SR" arguments are per-period unless the function name says *_ann.
* Skew/kurtosis use scipy.stats conventions (kurtosis is NON-excess, i.e.
  normal == 3.0). All formulas follow Bailey & Lopez de Prado (2012, 2014)
  and Bailey, Borwein, Lopez de Prado & Zhu (2017).
"""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass

import numpy as np
from scipy import stats

EULER_GAMMA = 0.5772156649015329


# ----------------------------------------------------------------------------
# 1. Performance primitives
# ----------------------------------------------------------------------------
def sharpe(r: np.ndarray, ppy: int = 12, rf: float = 0.0) -> float:
    """Annualised Sharpe ratio. ppy = periods per year."""
    r = np.asarray(r, float)
    r = r[np.isfinite(r)]
    if r.size < 3:
        return np.nan
    sd = r.std(ddof=1)
    if sd == 0:
        return np.nan
    return (r.mean() - rf / ppy) / sd * np.sqrt(ppy)


def sortino(r: np.ndarray, ppy: int = 12, target: float = 0.0) -> float:
    r = np.asarray(r, float)
    downside = r[r < target]
    dd = np.sqrt(np.mean((downside - target) ** 2)) if downside.size else np.nan
    return (r.mean() - target) / dd * np.sqrt(ppy) if dd else np.nan


def ann_return(r: np.ndarray, ppy: int = 12, geometric: bool = True) -> float:
    r = np.asarray(r, float)
    if geometric:
        return float(np.prod(1.0 + r) ** (ppy / r.size) - 1.0)
    return float(r.mean() * ppy)


def max_drawdown(r: np.ndarray) -> float:
    eq = np.cumprod(1.0 + np.asarray(r, float))
    peak = np.maximum.accumulate(eq)
    return float((eq / peak - 1.0).min())


def tail_ratio(r: np.ndarray, q: float = 0.95) -> float:
    """|q-th pct return| / |(1-q)-th pct return|. >1 means fatter right tail."""
    r = np.asarray(r, float)
    hi, lo = np.quantile(r, q), np.quantile(r, 1 - q)
    return float(abs(hi) / abs(lo)) if lo != 0 else np.nan


# ----------------------------------------------------------------------------
# 2. Sharpe uncertainty
# ----------------------------------------------------------------------------
def se_sharpe(sr_ann: float, n_years: float) -> float:
    """Lo (2002) standard error of an annualised SR estimated from n_years."""
    return math.sqrt((1.0 + 0.5 * sr_ann**2) / max(n_years, 1e-9))


def block_bootstrap_sr_ci(r: np.ndarray, ppy: int = 12, n_boot: int = 2000,
                          block: int | None = None, alpha: float = 0.05,
                          seed: int = 7) -> tuple[float, float, float]:
    """Stationary (Politis-Romano) block bootstrap CI for annualised SR.
    Block length defaults to ~ T^(1/3). Returns (point, lo, hi)."""
    r = np.asarray(r, float)
    T = r.size
    if block is None:
        block = max(1, int(round(T ** (1 / 3))))
    rng = np.random.default_rng(seed)
    out = np.empty(n_boot)
    p = 1.0 / block
    for b in range(n_boot):
        idx = np.empty(T, dtype=int)
        i = rng.integers(0, T)
        for t in range(T):
            idx[t] = i
            if rng.random() < p:
                i = rng.integers(0, T)
            else:
                i = (i + 1) % T
        out[b] = sharpe(r[idx], ppy)
    lo, hi = np.nanquantile(out, [alpha / 2, 1 - alpha / 2])
    return sharpe(r, ppy), float(lo), float(hi)


# ----------------------------------------------------------------------------
# 3. Probabilistic Sharpe Ratio and Minimum Track Record Length
# ----------------------------------------------------------------------------
def psr(sr_hat: float, T: int, skew: float = 0.0, kurt: float = 3.0,
        sr_star: float = 0.0) -> float:
    """P(true SR > sr_star). All SRs per-period.
    skew = skewness, kurt = NON-excess kurtosis (3 for normal)."""
    denom = 1.0 - skew * sr_hat + 0.25 * (kurt - 1.0) * sr_hat**2
    if denom <= 0:
        return np.nan
    z = (sr_hat - sr_star) * math.sqrt(max(T - 1, 1)) / math.sqrt(denom)
    return float(stats.norm.cdf(z))


def min_trl(sr_hat: float, sr_star: float = 0.0, skew: float = 0.0,
            kurt: float = 3.0, conf: float = 0.95) -> float:
    """Minimum number of PERIODS needed for PSR(sr_star) >= conf."""
    if sr_hat <= sr_star:
        return np.inf
    z = stats.norm.ppf(conf)
    num = 1.0 - skew * sr_hat + 0.25 * (kurt - 1.0) * sr_hat**2
    return 1.0 + num * (z / (sr_hat - sr_star)) ** 2


# ----------------------------------------------------------------------------
# 4. Deflated Sharpe Ratio
# ----------------------------------------------------------------------------
def expected_max_sr(var_sr_trials: float, n_trials: int,
                    gamma: float = EULER_GAMMA) -> float:
    """E[max SR] under the null across n_trials independent trials whose SR
    estimates have variance var_sr_trials (per-period units)."""
    if n_trials < 2:
        return 0.0
    a = stats.norm.ppf(1.0 - 1.0 / n_trials)
    b = stats.norm.ppf(1.0 - 1.0 / (n_trials * math.e))
    return math.sqrt(var_sr_trials) * ((1 - gamma) * a + gamma * b)


def dsr(sr_hat: float, T: int, var_sr_trials: float, n_trials: int,
        skew: float = 0.0, kurt: float = 3.0) -> float:
    """Deflated Sharpe Ratio = PSR evaluated against the expected maximum SR
    achievable by pure selection bias across n_trials. Per-period units.
    Pass the EFFECTIVE number of trials from effective_n_trials()."""
    sr0 = expected_max_sr(var_sr_trials, n_trials)
    return psr(sr_hat, T, skew, kurt, sr_star=sr0), sr0


def effective_n_trials(returns_matrix: np.ndarray) -> float:
    """Effective number of INDEPENDENT trials from the participation ratio of
    the correlation-matrix eigenvalues, N_eff = (sum L)^2 / sum L^2."""
    R = np.asarray(returns_matrix, float)
    if R.ndim == 1:
        return 1.0
    C = np.corrcoef(R, rowvar=False)
    C = np.nan_to_num(C, nan=0.0)
    ev = np.linalg.eigvalsh(C)
    ev = ev[ev > 0]
    return float(ev.sum() ** 2 / (ev ** 2).sum())


# ----------------------------------------------------------------------------
# 5. PBO / CSCV  (Bailey, Borwein, Lopez de Prado & Zhu 2017)
# ----------------------------------------------------------------------------
def pbo_cscv(R: np.ndarray, S: int = 16, max_combos: int = 20000,
             seed: int = 11) -> dict:
    """Probability of Backtest Overfitting via Combinatorially Symmetric
    Cross-Validation.

    R : (T x N) matrix, T observations, N strategy configurations in the
        SAME research family (grid, universe variants, frequencies...).
    S : even number of contiguous time blocks (16 -> C(16,8)=12,870 splits).

    Returns dict with pbo, median logit, per-config OOS-degradation, and the
    share of splits in which the IS winner is bottom-half OOS.
    """
    R = np.asarray(R, float)
    T, N = R.shape
    if S % 2 or S < 4:
        raise ValueError("S must be an even integer >= 4")
    L = T // S
    T_used = L * S
    R = R[T - T_used:]                      # drop the oldest partial block
    blocks = R.reshape(S, L, N)
    b_sum = blocks.sum(axis=1)               # (S, N)
    b_ssq = (blocks ** 2).sum(axis=1)
    b_n = np.full((S, N), float(L))

    combos = list(itertools.combinations(range(S), S // 2))
    rng = np.random.default_rng(seed)
    if len(combos) > max_combos:
        pick = rng.choice(len(combos), max_combos, replace=False)
        combos = [combos[i] for i in pick]
    sel = np.array(combos)                   # (C, S/2)
    C = sel.shape[0]

    def sr_from_sums(s, ssq, n):
        mean = s / n
        var = (ssq - n * mean**2) / (n - 1.0)
        var = np.where(var > 0, var, np.nan)
        return mean / np.sqrt(var)

    tot_sum, tot_ssq = b_sum.sum(0), b_ssq.sum(0)
    tot_n = b_n.sum(0)

    is_sum = b_sum[sel].sum(axis=1)          # (C, N)
    is_ssq = b_ssq[sel].sum(axis=1)
    is_n = b_n[sel].sum(axis=1)
    sr_is = sr_from_sums(is_sum, is_ssq, is_n)

    sr_oos = sr_from_sums(tot_sum - is_sum, tot_ssq - is_ssq, tot_n - is_n)

    best = np.nanargmax(sr_is, axis=1)
    oos_of_best = sr_oos[np.arange(C), best]
    # relative rank of the IS winner in the OOS distribution, 1..N
    rank = np.array([(sr_oos[c] <= oos_of_best[c]).sum() for c in range(C)], float)
    lam = rank / (N + 1.0)
    eps = 1e-12
    logit = np.log(np.clip(lam, eps, 1 - eps) / (1 - np.clip(lam, eps, 1 - eps)))

    # degradation of each config: OOS SR - IS SR
    return {
        "pbo": float((lam <= 0.5).mean()),
        "median_logit": float(np.median(logit)),
        "n_splits": C,
        "n_configs": N,
        "S": S,
        "sr_is_median": np.nanmedian(sr_is, axis=0),
        "sr_oos_median": np.nanmedian(sr_oos, axis=0),
        "logits": logit,
    }


# ----------------------------------------------------------------------------
# 6. Walk-forward efficiency
# ----------------------------------------------------------------------------
def wfe(is_sr: float, oos_sr: float) -> float:
    """Walk-forward efficiency on annualised SR (or return). >1 suspicious."""
    return np.nan if is_sr == 0 else oos_sr / is_sr


# ----------------------------------------------------------------------------
# 7. Costs and capacity
# ----------------------------------------------------------------------------
def breakeven_cost_bps(gross_r: np.ndarray, turnover: np.ndarray,
                       ppy: int = 12) -> float:
    """Round-trip cost (bps) at which annual net return = 0.
    gross_r = per-period GROSS returns; turnover = per-period traded fraction
    (sum of |dw|, i.e. 1.0 = 100% of the book traded once)."""
    g = np.asarray(gross_r, float)
    to = np.asarray(turnover, float)
    ann_gross_bps = ann_return(g, ppy, geometric=False) * 1e4
    ann_turnover = to.mean() * ppy          # turnover per YEAR
    return float(ann_gross_bps / ann_turnover) if ann_turnover > 0 else np.inf


def capacity_curve(gross_sr: float, ann_turnover: float, aum_grid: list[float],
                   cost_fn) -> list[dict]:
    """Net SR as a function of AUM. cost_fn(aum) -> round-trip cost in bps."""
    out = []
    for aum in aum_grid:
        drag = ann_turnover * cost_fn(aum) / 1e4
        out.append({"aum": aum, "cost_bps": cost_fn(aum),
                    "ann_cost_drag": drag,
                    "net_ann_return_after_drag_only": -drag})
    return out


# ----------------------------------------------------------------------------
# 8. Power and sample size
# ----------------------------------------------------------------------------
def required_years(sr_ann: float, alpha: float = 0.05, power: float = 0.80,
                   one_sided: bool = True) -> float:
    """Years of live/paper data needed to reject SR=0 at `alpha` with `power`.
    Uses the large-sample approximation T = ((z_{1-a} + z_{power}) / SR)^2."""
    z_a = stats.norm.ppf(1 - alpha) if one_sided else stats.norm.ppf(1 - alpha / 2)
    z_b = stats.norm.ppf(power)
    return ((z_a + z_b) / sr_ann) ** 2


def power_at(sr_ann: float, n_years: float, alpha: float = 0.05,
             one_sided: bool = True) -> float:
    z_a = stats.norm.ppf(1 - alpha) if one_sided else stats.norm.ppf(1 - alpha / 2)
    return float(stats.norm.cdf(sr_ann * math.sqrt(n_years) - z_a))


def years_for_t(sr_ann: float, t_target: float = 3.0) -> float:
    """Years needed for a raw t-stat of t_target: t ~= SR * sqrt(T)."""
    return (t_target / sr_ann) ** 2


# ----------------------------------------------------------------------------
# 9. Multiple-testing helpers
# ----------------------------------------------------------------------------
def haircut_pvalue(p: float, n_trials: int) -> float:
    """Bonferroni-style familywise p-value (conservative)."""
    return min(1.0, p * n_trials)


def bh_fdr(pvals: list[float], q: float = 0.10) -> list[bool]:
    """Benjamini-Hochberg FDR control. Returns rejection mask."""
    p = np.asarray(pvals, float)
    n = p.size
    order = np.argsort(p)
    thresh = q * (np.arange(1, n + 1) / n)
    passed = p[order] <= thresh
    mask = np.zeros(n, bool)
    if passed.any():
        k = np.max(np.where(passed)[0])
        mask[order[: k + 1]] = True
    return mask.tolist()


def romanowolf_threshold(tstats: np.ndarray, max_stat_null: np.ndarray,
                         alpha: float = 0.05) -> float:
    """Data-driven |t| threshold from a bootstrap Reality-Check null
    distribution (max statistic across strategies)."""
    q = np.quantile(np.abs(max_stat_null), 1 - alpha)
    return float(q)


# ----------------------------------------------------------------------------
# 10. Demo
# ----------------------------------------------------------------------------
def _sim_family(alpha_ann: float, n_cfg: int = 40, T: int = 240,
                sigma: float = 0.05, rho: float = 0.5,
                seed: int = 0) -> np.ndarray:
    """Synthetic research family: config j earns alpha_ann * w_j (w ~ U(0.5,1.5))
    on a shared market-ish factor plus idio noise. alpha_ann = 0 makes the
    family pure noise, so CSCV should return PBO ~ 0.5."""
    rng = np.random.default_rng(seed)
    common = rng.standard_normal(T)
    w = rng.uniform(0.5, 1.5, n_cfg)
    out = np.empty((T, n_cfg))
    for j in range(n_cfg):
        idio = rng.standard_normal(T)
        out[:, j] = alpha_ann / 12.0 * w[j] + sigma * (
            rho * common + math.sqrt(1 - rho**2) * idio)
    return out


if __name__ == "__main__":
    np.set_printoptions(precision=3, suppress=True)
    print("=" * 74)
    print("SELF-TEST / DEMO")
    print("=" * 74)

    rng = np.random.default_rng(42)
    T, mo = 240, 12

    # --- A real-ish strategy: 0.6 annual SR over 20 years of months
    r_good = rng.normal(0.0075, 0.042, T)
    print(f"\n[A] single strategy, 20y monthly, true-ish SR")
    print(f"    ann.return {ann_return(r_good):.2%}  vol {r_good.std(ddof=1)*math.sqrt(12):.2%}"
          f"  SR {sharpe(r_good):.2f}  maxDD {max_drawdown(r_good):.1%}"
          f"  tail_ratio {tail_ratio(r_good):.2f}")
    p, lo, hi = block_bootstrap_sr_ci(r_good)
    print(f"    SR 90% stationary-bootstrap CI: [{lo:.2f}, {hi:.2f}]")
    sr_m = sharpe(r_good) / math.sqrt(12)
    sk, ku = stats.skew(r_good), stats.kurtosis(r_good, fisher=False)
    print(f"    PSR(0)      = {psr(sr_m, T, sk, ku):.4f}")
    print(f"    MinTRL(0)   = {min_trl(sr_m, 0.0, sk, ku):.0f} months "
          f"({min_trl(sr_m, 0.0, sk, ku)/12:.1f} years)")

    # --- Deflated SR: 200 effective trials, SR dispersion 0.35 ann
    var_trials_ann = 0.35**2
    var_trials = var_trials_ann / 12
    d, sr0 = dsr(sr_m, T, var_trials, n_trials=200, skew=sk, kurt=ku)
    print(f"\n[B] DSR with N_eff=200, sd(SR_trials)=0.35/yr")
    print(f"    E[max SR | null] = {sr0*math.sqrt(12):.2f} annualised")
    print(f"    DSR              = {d:.4f}   (need >= 0.95)")

    # --- PBO on a pure-noise family vs a family with a genuine edge
    print(f"\n[C] PBO / CSCV, S=16, 40 configs x 240 months")
    for label, a in [("pure-noise family (edge 0%/yr)", 0.0),
                     ("weak family (edge 4%/yr, wi~U(.5,1.5))", 0.04),
                     ("strong family (edge 8%/yr)", 0.08)]:
        fam = _sim_family(a, n_cfg=40, T=T, seed=1)
        res = pbo_cscv(fam, S=16)
        print(f"    {label:42s} PBO={res['pbo']:.2f}  "
              f"median logit={res['median_logit']:+.2f}  splits={res['n_splits']}")

    # --- effective trials from a correlated grid
    rngd = np.random.default_rng(2)
    F = rngd.standard_normal((T, 3))
    B = rngd.uniform(0.2, 1.0, (3, 100))
    grid = F @ B + 0.3 * rngd.standard_normal((T, 100))   # 100 configs, 3 drivers
    print(f"\n[D] Effective trials: 100 configs built from 3 latent drivers "
          f"-> N_eff = {effective_n_trials(grid):.1f} "
          f"(independent grid would be 100)")

    # --- Power table
    print(f"\n[E] Years needed to reject SR=0 (one-sided 5%, 80% power)")
    for s in [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0]:
        print(f"    SR {s:4.2f} -> {required_years(s):6.1f} years "
              f"(t=3 needs {years_for_t(s,3):5.1f}y)")

    # --- Costs / capacity
    gross = rng.normal(0.006, 0.04, T)
    to = np.full(T, 0.25)          # 25% of the book traded per month
    be = breakeven_cost_bps(gross, to)
    print(f"\n[F] gross ann {ann_return(gross,12,False):.2%}, "
          f"{to.mean()*12*100:.0f}% annual turnover -> breakeven round-trip cost "
          f"{be:.0f} bps")
    ann_to = to.mean() * 12
    for c in [5, 10, 20, 40, 80]:
        print(f"    at {c:3d} bps round-trip: net ann "
              f"{ann_return(gross,12,False) - ann_to*c/1e4:+.2%}  "
              f"(cost drag {ann_to*c/1e2:.1f}%/yr)")

    # --- FDR example
    pv = [0.0001, 0.004, 0.02, 0.04, 0.06, 0.20, 0.55, 0.90]
    print(f"\n[G] BH-FDR at q=10% on 8 p-values -> rejected: {bh_fdr(pv)}")
