#!/usr/bin/env python3
"""Harness certification: proofs that the engine is allowed to return "no".

Four tests, each of which can FAIL. If any of them fails, no result produced by this
harness is publishable, because the failure means the machine cannot distinguish an
edge from an accounting error.

  T1 LOOK-AHEAD DETECTION
     Build two versions of the same rule: an honest one, and one that peeks at the
     next bar. The harness must show the peeking version as dramatically better, which
     proves the honest version is not accidentally peeking too. Then assert the honest
     version's signal at bar i is unchanged when bar i+1.. are deleted (structural
     causality check).

  T2 COST ACCOUNTING
     A symmetric zero-information strategy must lose approximately the round-turn cost
     per trade. If it loses less, friction is not being charged; if it loses more,
     something is double-counting.

  T3 INTRABAR TIE RESOLUTION
     A single bar that touches both the take-profit and the stop must resolve to the
     STOP. Verified by construction on a one-trade fixture.

  T4 NULL CALIBRATION (deflated Sharpe)
     Generate many pure-noise strategies. The fraction that appear "significant" at
     DSR > 0.95 must be near zero. If noise passes, the statistics layer is broken.

Run: python -m realtime_challenge.proof.test_harness
Exit code 0 = all pass.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from realtime_challenge import engine as E  # noqa: E402
from realtime_challenge import stats as ST  # noqa: E402
from realtime_challenge.costs import CostModel  # noqa: E402

RESULTS: list[dict] = []


def _synth(n: int = 4000, seed: int = 7, drift: float = 0.0, vol: float = 0.01) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    r = rng.normal(drift, vol, n)
    close = 100 * np.cumprod(1 + r)
    open_ = np.r_[close[0], close[:-1]]
    hi = np.maximum(open_, close) * (1 + np.abs(rng.normal(0, 0.002, n)))
    lo = np.minimum(open_, close) * (1 - np.abs(rng.normal(0, 0.002, n)))
    idx = pd.date_range("2024-01-01", periods=n, freq="h", tz="UTC")
    return pd.DataFrame({"open": open_, "high": hi, "low": lo, "close": close,
                         "volume": rng.uniform(100, 1000, n)}, index=idx)


def _record(name: str, passed: bool, detail: str, value=None):
    RESULTS.append({"test": name, "passed": bool(passed), "detail": detail, "value": value})
    print(f"  [{'PASS' if passed else 'FAIL'}] {name}: {detail}")


# ---------------------------------------------------------------- T1
def t1_lookahead():
    df = _synth(3000, seed=11)

    def honest(d):
        # 20-bar momentum on the CLOSED bar only
        return (d["close"] > d["close"].rolling(20).mean()).astype(int)

    def peeking(d):
        # deliberately illegal: compares the NEXT bar's close
        nxt = d["close"].shift(-1)
        return (nxt > d["close"].rolling(20).mean()).astype(int)

    kw = dict(tp_atr=2.0, sl_atr=1.0, max_bars=12)
    h = E.run_from_signals(df, honest(df), "honest", "X", **kw)
    p = E.run_from_signals(df, peeking(df), "peeking", "X", **kw)
    h_mean = np.mean([t["net_ret"] for t in h.trades])
    p_mean = np.mean([t["net_ret"] for t in p.trades])
    detected = p_mean > h_mean
    _record("T1a look-ahead is detectable", detected,
            f"peeking mean {p_mean*1e4:+.1f}bps vs honest {h_mean*1e4:+.1f}bps",
            {"peeking_bps": round(p_mean * 1e4, 2), "honest_bps": round(h_mean * 1e4, 2)})

    # causality: truncating the future must not change past signals
    trunc = df.iloc[:2000]
    same = bool((honest(trunc).astype(int).to_numpy() == honest(df).astype(int).to_numpy()[:2000]).all())
    _record("T1b signals are causal", same, "signal at bar i unchanged when bars >i are deleted")


# ---------------------------------------------------------------- T2
def t2_costs():
    df = _synth(6000, seed=23, drift=0.0, vol=0.008)
    # coin-flip entries, symmetric 1:1 bracket -> zero expected gross edge
    rng = np.random.default_rng(5)
    sig = pd.Series(rng.choice([-1, 1], size=len(df)), index=df.index)
    kw = dict(tp_atr=1.0, sl_atr=1.0, max_bars=6)

    rows = []
    for cm in [CostModel(0, 0), CostModel(0.001, 0.0003)]:
        r = E.run_from_signals(df, sig, "noise", "X", costs=cm, **kw)
        net = np.array([t["net_ret"] for t in r.trades])
        rows.append((cm.round_turn, net.mean(), net.size))

    zero_mean = rows[0][1]
    cost_mean = rows[1][1]
    drag = (zero_mean - cost_mean) * 1e4
    expected = 26.0
    # tolerance: the bracket truncates the return distribution, so the drag is
    # approximately, not exactly, the round turn.
    passed = abs(drag - expected) <= 6.0
    _record("T2 cost drag matches the round turn", passed,
            f"drag {drag:.1f}bps vs expected ~{expected:.0f}bps (n={rows[1][2]})",
            {"drag_bps": round(drag, 2), "expected_bps": expected})


# ---------------------------------------------------------------- T3
def t3_intrabar_tie():
    idx = pd.date_range("2025-01-01", periods=4, freq="h", tz="UTC")
    df = pd.DataFrame({
        "open":  [100.0, 100.0, 100.0, 100.0],
        "high":  [100.2, 112.0, 100.1, 100.1],   # bar 1 touches BOTH tp and sl
        "low":   [ 99.8,  88.0,  99.9,  99.9],
        "close": [100.0, 100.0, 100.0, 100.0],
        "volume": [1, 1, 1, 1],
    }, index=idx)
    sig = pd.Series([1, 0, 0, 0], index=idx)
    # ATR(1) ~ 12 on bar 0 would make tp/sl wide; force tight brackets instead
    r = E.run_from_signals(df, sig, "tie", "X", tp_atr=0.1, sl_atr=0.1,
                           max_bars=3, atr_window=1, costs=CostModel(0, 0))
    reason = r.trades[0]["exit_reason"] if r.trades else None
    _record("T3 both-touched bar resolves to STOP", reason == "SL",
            f"exit_reason={reason} (must be SL, not TP)", {"exit_reason": reason})


# ---------------------------------------------------------------- T4
def t4_null_calibration():
    n_cells = 60
    sig_count = 0
    dsrs = []
    for i in range(n_cells):
        df = _synth(2500, seed=1000 + i)
        rng = np.random.default_rng(2000 + i)
        sig = pd.Series(rng.choice([-1, 1], size=len(df)), index=df.index)
        r = E.run_from_signals(df, sig, f"noise{i}", "X", tp_atr=1.5, sl_atr=1.0, max_bars=8)
        net = [t["net_ret"] for t in r.trades]
        if len(net) < 10:
            continue
        ds = ST.deflated_sharpe(net, n_trials=n_cells)
        if ds.get("dsr") is None:
            continue
        dsrs.append(ds["dsr"])
        if ds["dsr"] >= 0.95:
            sig_count += 1
    frac = sig_count / max(len(dsrs), 1)
    passed = frac <= 0.05
    _record("T4 pure noise almost never clears DSR 0.95", passed,
            f"{sig_count}/{len(dsrs)} noise cells at DSR>=0.95 ({frac:.1%}), max DSR {max(dsrs) if dsrs else 'n/a'}",
            {"false_positive_rate": round(frac, 4), "n_cells": len(dsrs)})


def main() -> int:
    print("HARNESS CERTIFICATION")
    print(f"  engine: {E.__file__}")
    t1_lookahead()
    t2_costs()
    t3_intrabar_tie()
    t4_null_calibration()

    n_pass = sum(r["passed"] for r in RESULTS)
    print(f"\n{n_pass}/{len(RESULTS)} passed")
    out = Path(__file__).resolve().parent.parent / "results" / "harness_certification.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"tests": RESULTS, "passed": n_pass, "total": len(RESULTS)}, indent=1), encoding="utf-8")
    print(f"wrote {out}")
    return 0 if n_pass == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
