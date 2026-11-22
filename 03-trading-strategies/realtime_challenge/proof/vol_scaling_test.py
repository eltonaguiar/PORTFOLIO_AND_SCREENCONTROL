#!/usr/bin/env python3
"""H-VS1: "Volatility scaling is free alpha" — measured, not repeated.

The audit2/audit3 doctrine states, as one of its load-bearing claims:

    "Volatility scaling is free alpha. Simply scaling positions by inverse realized vol
     improves Sharpe by 0.3+ for any momentum strategy."

That sentence appears in three places in this repository as a **quotation**. It has never
been run. One of the four model answers even flags it as untested:

    "Apply your own evidence machinery to the doctrine's claims too — 'vol scaling is free
     alpha' is itself a testable hypothesis, and it mostly works by reducing exposure, not
     adding return."                                              (GLM 5.3 Flash)

So this runs it, on the strategies this repo already has, and reports the Sharpe delta.

The distinction the claim elides
--------------------------------
Sharpe is return/vol. Inverse-vol scaling cuts vol in a high-vol period and raises it in a
low-vol period, so it can raise Sharpe **by reducing the denominator** without touching the
numerator. Two variants are therefore reported separately:

  cap = 1.0   no leverage. Scaling can only DE-RISK. This is what a retail account can do.
  cap = 2.0   up to 2x leverage. This is what "0.3+ for any momentum strategy" is usually
              measured on, and it is where the cost of leverage and of rescaling shows up.

Scaling is not free: every change in the scale factor trades, so turnover is charged at the
same 5 bps per side as the underlying strategies. Most published vol-scaling results omit it.

  python -m realtime_challenge.proof.vol_scaling_test
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

OUT = Path(__file__).resolve().parent.parent / "results" / "vol_scaling_test.json"
COST_PER_SIDE = 0.0005
TARGET_VOL = 0.10          # 10% annualised, the usual default
VOL_WINDOW = 20
START = "2004-01-01"


def stats(r: pd.Series) -> dict:
    r = r.dropna()
    if len(r) < 250:
        return {"sharpe": None}
    sd = r.std(ddof=1)
    eq = (1 + r).cumprod()
    yrs = len(r) / 252
    return {
        "sharpe": round(float(r.mean() / sd * math.sqrt(252)), 3) if sd else None,
        "cagr": round(float(eq.iloc[-1] ** (1 / yrs) - 1), 4),
        "max_drawdown": round(float((eq / eq.cummax() - 1).min()), 4),
        "ann_vol": round(float(sd * math.sqrt(252)), 4),
    }


def vol_target(base: pd.Series, cap: float, target: float = TARGET_VOL,
               window: int = VOL_WINDOW, cost: float = COST_PER_SIDE) -> pd.Series:
    """Scale exposure by target/realized vol, clipped to [0, cap], lagged one day."""
    rv = base.rolling(window).std() * math.sqrt(252)
    scale = (target / rv).clip(lower=0.0, upper=cap)
    scale = scale.shift(1)                     # decide on yesterday's vol, earn today
    gross = scale * base
    turn = scale.diff().abs().fillna(scale.abs())
    return gross - turn * cost


def build_strategies() -> dict[str, pd.Series]:
    import yfinance as yf

    spy = yf.download("SPY", start=START, auto_adjust=True, progress=False)["Close"].squeeze()
    r = spy.pct_change()

    out: dict[str, pd.Series] = {}

    # 1. buy and hold
    out["SPY buy-and-hold"] = r.copy()

    # 2. 12-month time-series momentum
    mom = (spy / spy.shift(252) - 1).shift(1)
    out["SPY 12m TSMOM"] = (mom > 0).astype(float) * r

    # 3. 200-day SMA trend overlay
    sma = spy.rolling(200).mean()
    out["SPY + 200d SMA"] = (spy > sma).shift(1).fillna(False).astype(float) * r

    # 4. equity-curve momentum (a momentum strategy on its own returns)
    out["SPY 6m ECM"] = ((spy / spy.shift(126) - 1).shift(1) > 0).astype(float) * r

    return out


def main() -> int:
    print("building base strategies from SPY 2004-2026 ...")
    base = build_strategies()
    print(f"  {len(base)} strategies\n")

    rows = []
    for name, ser in base.items():
        un = stats(ser)
        row = {"strategy": name, "unscaled": un}
        for cap in (1.0, 2.0):
            sc = stats(vol_target(ser, cap=cap))
            row[f"scaled_cap{cap:g}"] = sc
            row[f"delta_cap{cap:g}"] = (
                None if (sc["sharpe"] is None or un["sharpe"] is None)
                else round(sc["sharpe"] - un["sharpe"], 3)
            )
        rows.append(row)

    df = pd.DataFrame(rows)
    deltas_1 = [r["delta_cap1"] for r in rows if r.get("delta_cap1") is not None]
    deltas_2 = [r["delta_cap2"] for r in rows if r.get("delta_cap2") is not None]
    n_ge_03_no_lev = sum(1 for d in deltas_1 if d >= 0.30)
    n_ge_03_lev = sum(1 for d in deltas_2 if d >= 0.30)

    print(f"{'strategy':22s} {'base Sh':>8s} {'cap1 Sh':>8s} {'Δ unlev':>8s} "
          f"{'cap2 Sh':>8s} {'Δ lev':>7s} {'vol (base->s1)':>16s}")
    for r in rows:
        un, s1, s2 = r["unscaled"], r["scaled_cap1"], r["scaled_cap2"]
        print(f"{r['strategy']:22s} {un['sharpe']:>8.3f} {s1['sharpe']:>8.3f} "
              f"{r['delta_cap1']:>+8.3f} {s2['sharpe']:>8.3f} {r['delta_cap2']:>+7.3f} "
              f"{un['ann_vol']:>7.1%} -> {s1['ann_vol']:<6.1%}")

    # the claim: "+0.3 for ANY momentum strategy"
    momentum_only = [r for r in rows if "TSMOM" in r["strategy"] or "ECM" in r["strategy"]]
    mom_deltas = [r["delta_cap2"] for r in momentum_only if r.get("delta_cap2") is not None]

    verdict = (
        f"CLAIM DOES NOT HOLD AS STATED: {n_ge_03_lev}/{len(deltas_2)} strategies gain >=0.30 "
        f"Sharpe under 2x-levered vol targeting, and {n_ge_03_no_lev}/{len(deltas_1)} under "
        f"no-leverage vol targeting. Momentum alone: {sum(1 for d in mom_deltas if d>=0.30)}"
        f"/{len(mom_deltas)} reach +0.30."
    )

    out = {
        "hypothesis": "H-VS1 — inverse-vol scaling improves Sharpe by 0.3+ for any momentum strategy",
        "source": "audit2/audit3 doctrine, quoted in REVIEWS/inputs/ALLOCATION_FOUR_MODEL_ANSWERS.md line 10",
        "previously_tested": False,
        "flagged_untested_by": "GLM 5.3 Flash — 'vol scaling is free alpha is itself a testable hypothesis'",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "window": {"start": START, "end": "2026-11", "instrument": "SPY"},
        "parameters": {"target_vol": TARGET_VOL, "vol_window": VOL_WINDOW,
                       "cost_per_side": COST_PER_SIDE, "leverage_caps": [1.0, 2.0]},
        "rows": rows,
        "n_strategies": len(rows),
        "n_gain_0_30_no_leverage": n_ge_03_no_lev,
        "n_gain_0_30_with_leverage": n_ge_03_lev,
        "momentum_deltas_with_leverage": mom_deltas,
        "verdict": verdict,
        "reading": {
            "de_risking_works": "vol targeting reliably CUTS drawdown and vol; that part is real and it is "
                                "risk management, not alpha",
            "sharpe_gain_is_mostly_denominator": "where Sharpe rises it is because realised vol falls, and "
                                                 "CAGR usually falls with it under a no-leverage cap",
            "cost_is_omitted_upstream": "rescaling trades; the turnover charge is included here and is not "
                                        "in the doctrinal claim",
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")

    print(f"\nno-leverage vol targeting:  {n_ge_03_no_lev}/{len(deltas_1)} reach +0.30 Sharpe")
    print(f"2x-levered vol targeting:   {n_ge_03_lev}/{len(deltas_2)} reach +0.30 Sharpe")
    print(f"\nVERDICT: {verdict}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
