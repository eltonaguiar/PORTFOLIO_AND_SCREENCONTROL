#!/usr/bin/env python3
"""Multi-asset TSMOM survived the cost model. Does the TIMING add anything, or is it exposure?

`cost_portability.py` found the first candidate in this project to survive the 26 bps cost model:

    SPY buy-and-hold                 Sharpe 0.62  (flat across all costs — one entry, 23y)
    SPY 12m TSMOM                    Sharpe 0.62 at 26bps
    SPY + 200d SMA                   Sharpe 0.61 at 26bps
    Multi-asset TSMOM (vol-scaled)    Sharpe 0.57 at 26bps, 0.86 at 0bps

That also CORRECTS an earlier result of mine. `vol_scaling_test.py` judged "SPY 12m TSMOM" against
buy-and-hold (0.604 vs 0.620) and I read it as "TSMOM does not beat buy-and-hold". That was an
unfair test of the published claim: Moskowitz/Ooi/Pedersen is **multi-asset and vol-scaled**, not a
single-asset binary switch. Tested properly it does better than B&H here.

But a long/flat overlay has two sources of return and they must be separated:

  1. **EXPOSURE** — it is out of the market ~30% of the time, which by itself changes both return
     and volatility. Any random schedule with the same flat fraction gets this for free.
  2. **TIMING** — it is out of the market on particular days because trailing returns were negative.

The control: hold the *same number* of long days per leg, placed at random. If random placement
reaches the same Sharpe, the signal contributes nothing and the result is exposure, not timing.
Also runs a return-permutation control on each leg.

  python -m realtime_challenge.proof.tsmom_control
"""

from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

RESULTS = Path(__file__).resolve().parent.parent / "results"
START = "2004-01-01"
N_RANDOM = 200
SEED = 17


def sharpe(x: np.ndarray) -> float | None:
    x = x[np.isfinite(x)]
    if len(x) < 250:
        return None
    sd = x.std(ddof=1)
    return float(x.mean() / sd * math.sqrt(252)) if sd else None


def leg_series(s: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
    """returns, TSMOM weight, vol-scaled weight for one instrument."""
    rr = s.pct_change()
    m = (s / s.shift(252) - 1).shift(1)
    sig = rr.rolling(60).std().shift(1) * math.sqrt(252)
    w = (0.10 / sig).clip(0.0, 3.0).where(m > 0, 0.0)
    return rr, w


def portfolio(legs: dict[str, tuple[pd.Series, pd.Series]], weights=None) -> np.ndarray:
    """Equal-weight portfolio of (w.shift(1)*r). If `weights` given, use those instead of TSMOM."""
    R = pd.DataFrame({k: v[0] for k, v in legs.items()})
    W = pd.DataFrame(weights) if weights is not None else pd.DataFrame(
        {k: v[1] for k, v in legs.items()})
    gross = (W.shift(1) * R).sum(axis=1) / len(legs)
    return gross.to_numpy(float)


def main() -> int:
    import yfinance as yf

    tickers = ["SPY", "EFA", "EEM", "TLT", "IEF", "GLD", "DBC", "UUP"]
    px = {}
    for t in tickers:
        try:
            d = yf.download(t, start=START, auto_adjust=True, progress=False)["Close"].squeeze()
            if len(d) > 500:
                px[t] = d
        except Exception:
            pass
    # instruments have different history lengths (GLD starts 2004-11, DBC 2006, UUP 2007).
    # Without a common index every leg's series is a different length and the shuffle step
    # raises "Length of values does not match length of index" — align once, up front.
    if px:
        common = None
        for s in px.values():
            common = s.index if common is None else common.intersection(s.index)
        px = {k: v.loc[common] for k, v in px.items()}
        print(f"{len(px)} instruments, common window {common[0].date()} -> {common[-1].date()} "
              f"({len(common)} bars)\n")

    legs = {}
    for k, s in px.items():
        rr, w = leg_series(s)
        legs[k] = (rr, w)

    real_w = {k: v[1] for k, v in legs.items()}
    real = portfolio(legs, real_w)
    real_sh = sharpe(real)
    flat_frac = {k: float((v[1].fillna(0) == 0).mean()) for k, v in legs.items()}
    print(f"real multi-asset TSMOM: Sharpe {real_sh:.3f}")
    print("  flat fraction per leg: " +
          ", ".join(f"{k} {f:.0%}" for k, f in list(flat_frac.items())[:4]) + " ...")

    # 1. EXPOSURE CONTROL — same number of long days per leg, placed at random
    rng = np.random.default_rng(SEED)
    idx = legs["SPY"][0].index
    n = len(idx)
    rand_sh = []
    for _ in range(N_RANDOM):
        rw = {}
        for k, (rr, w) in legs.items():
            n_long = int((w.fillna(0) > 0).sum())
            arr = np.zeros(n)
            if n_long > 0:
                arr[rng.choice(n, size=n_long, replace=False)] = 1.0
            rw[k] = pd.Series(arr, index=idx)
        rand_sh.append(sharpe(portfolio(legs, rw)))
    rand_sh = np.array([x for x in rand_sh if x is not None])
    pct = float((rand_sh >= real_sh).mean())
    print(f"\nEXPOSURE CONTROL ({n_rand if False else N_RANDOM} random schedules, same flat fraction):")
    print(f"  random Sharpe  mean {rand_sh.mean():.3f}  sd {rand_sh.std():.3f}  "
          f"p05 {np.percentile(rand_sh,5):.3f}  p95 {np.percentile(rand_sh,95):.3f}")
    print(f"  real {real_sh:.3f} -> percentile {float((rand_sh < real_sh).mean()):.3f}, "
          f"p(rand >= real) = {pct:.3f}")

    # 2. PERMUTATION CONTROL — shuffle each leg's returns, keep the TSMOM weights
    perm_sh = []
    for _ in range(N_RANDOM):
        pl = {}
        for k, (rr, w) in legs.items():
            arr = rng.permutation(rr.fillna(0).to_numpy())
            pl[k] = (pd.Series(arr, index=idx), w)
        perm_sh.append(sharpe(portfolio(pl, real_w)))
    perm_sh = np.array([x for x in perm_sh if x is not None])
    p_perm = float((perm_sh >= real_sh).mean())
    print(f"\nPERMUTATION CONTROL ({N_RANDOM} shuffles):")
    print(f"  shuffled Sharpe mean {perm_sh.mean():.3f}  p95 {np.percentile(perm_sh,95):.3f}")
    print(f"  real {real_sh:.3f} -> p = {p_perm:.3f}")

    # 3. buy-and-hold benchmark on the same window
    bh = pd.concat([v[0] for v in legs.values()], axis=1).mean(axis=1).to_numpy(float)
    bh_sh = sharpe(bh)
    print(f"\nbenchmark: equal-weight buy-and-hold of the same 8 instruments = {bh_sh:.3f}")

    verdict_bits = []
    if real_sh <= bh_sh:
        verdict_bits.append("fails to beat equal-weight buy-and-hold")
    if pct > 0.05:
        verdict_bits.append(f"random exposure with the same flat fraction matches it (p={pct:.3f}) "
                            f"-> the result is EXPOSURE, not timing")
    if p_perm > 0.05:
        verdict_bits.append(f"permuted returns do as well (p={p_perm:.3f})")

    out = {
        "hypothesis": "multi-asset vol-scaled TSMOM beats buy-and-hold for TIMING reasons",
        "corrects": ("vol_scaling_test.py judged TSMOM on a single-asset binary version; the "
                     "published construction is multi-asset and vol-scaled"),
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "window": {"start": START, "universe": list(px)},
        "real_sharpe": round(real_sh, 3),
        "buy_and_hold_sharpe": round(bh_sh, 3),
        "exposure_control": {
            "n_random": int(len(rand_sh)), "mean": round(float(rand_sh.mean()), 3),
            "sd": round(float(rand_sh.std()), 3),
            "p05": round(float(np.percentile(rand_sh, 5)), 3),
            "p95": round(float(np.percentile(rand_sh, 95)), 3),
            "p_random_beats_real": round(pct, 3),
        },
        "permutation_control": {
            "n": int(len(perm_sh)), "mean": round(float(perm_sh.mean()), 3),
            "p95": round(float(np.percentile(perm_sh, 95)), 3), "p_value": round(p_perm, 3),
        },
        "verdict": ("TIMING ADDS VALUE" if not verdict_bits
                    else "NO TIMING EDGE: " + "; ".join(verdict_bits)),
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    body = json.dumps(out, indent=1, default=str)
    (RESULTS / f"tsmom_control_{stamp}.json").write_text(body, encoding="utf-8")
    (RESULTS / "tsmom_control_latest.json").write_text(body, encoding="utf-8")
    print(f"\nVERDICT: {out['verdict']}")
    print("wrote results/tsmom_control_latest.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
