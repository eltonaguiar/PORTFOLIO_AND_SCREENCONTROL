#!/usr/bin/env python3
"""P7 — bracket reachability. The rule that explains 0 take-profits in 27 live trades.

What went wrong in the live books, stated precisely: brackets were opened with `tp_atr` 0.8-1.2
and `sl_atr` 0.5-0.6 on a 1h ATR of ~0.7%, inside 8-12 minute holds. The target sat ~0.57% away
and the stop ~0.43%, on a market that moved 0.2-0.5% in that time. Twenty-seven trades produced
**12 stops, 14 time stops, 0 targets.**

There are two independent defects in a bracket, and conflating them hides the fix:

  1. UNREACHABLE — the barrier is farther than the market is likely to travel before the time
     stop fires. Both barriers sit outside the expected excursion, so the exit is decided by the
     clock. The take-profit is decoration; it cannot be hit.

  2. UNBALANCED — the barriers are reachable but asymmetric in a way that loses money. On a
     driftless walk the probability of touching TP before SL is exactly `sl_dist / (tp + sl)`,
     so a 2.0/1.0 bracket wins only 33.3% of the time before costs. That can still be profitable
     with enough payoff, but a wide TP with a tight SL is a low-win-rate bet that is usually
     misread as a "high quality" setup.

A bracket can fail either one. This module measures both, and refuses the bracket rather than
letting the live loop open it.

Math
----
Per-bar volatility `s` (from ATR or close-to-close), price `P`, hold horizon `H` bars.

  expected excursion      E = s * P * sqrt(H)          (1 standard deviation of the max move)

  P(touch upper barrier at distance a within H)  ~=  2 * Phi(-a / (s*P*sqrt(H)))
      the reflection-principle approximation for a driftless Brownian motion; good to a few
      percent for a/sqrt(H) > 0.3, which is the regime this gate cares about.

  P(TP touches before SL)  =  b / (a + b)              exact for a driftless walk

  P(exit by TP)  ~=  P(TP first) * P(some barrier touched within H)

The last line is the number that matters: it is the fraction of trades that can possibly end in
the take-profit. Everything else is stops and timeouts.

Gates
-----
  G-REACH   P(some barrier touched within H) >= MIN_TOUCH      default 0.50
  G-BALANCE P(exit by TP) >= MIN_TP_EXIT                       default 0.20
  G-EDGE    expected net per trade > 0 after costs, given P(TP exit)

A bracket failing G-REACH will time out regardless of the signal being right. A bracket failing
G-BALANCE can only win by being right far more often than the geometry allows.

  python -m realtime_challenge.bracket --check --price 59700 --atr 426 --hold-bars 3
  python -m realtime_challenge.bracket --audit-ledger ledger/liveprobe_bybit_v2.jsonl
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

MIN_TOUCH = 0.50
MIN_TP_EXIT = 0.20


def _phi(x: float) -> float:
    """Standard normal CDF."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


@dataclass
class Verdict:
    price: float
    atr: float
    hold_bars: int
    tp_dist: float
    sl_dist: float
    expected_excursion: float
    p_touch_any: float
    p_tp_first: float
    p_tp_exit: float
    p_sl_exit: float
    p_timeout: float
    fail_reach: bool
    fail_balance: bool
    fail_ev: bool
    exp_net_r: float
    reasons: list[str]

    def ok(self) -> bool:
        return not (self.fail_reach or self.fail_balance or self.fail_ev)

    def as_dict(self) -> dict:
        d = asdict(self)
        d["ok"] = self.ok()
        return d


def evaluate(price: float, atr: float, tp_atr: float, sl_atr: float, hold_bars: int,
             *, min_touch: float = MIN_TOUCH, min_tp_exit: float = MIN_TP_EXIT,
             round_turn_cost_bps: float = 26.0) -> Verdict:
    """Judge a bracket before it is opened.

    `atr` is the per-bar true range in price units; `hold_bars` the time stop. The horizon
    volatility is ATR * sqrt(hold_bars), which deliberately uses ATR rather than close-to-close
    sigma: ATR is what the bracket is expressed in, so the barrier distance and the volatility
    estimate are the same units and the same instrument.
    """
    if price <= 0 or atr <= 0 or hold_bars < 1:
        raise ValueError("price, atr and hold_bars must be positive")

    tp_dist = tp_atr * atr
    sl_dist = sl_atr * atr
    horizon_sd = atr * math.sqrt(hold_bars)
    expected_excursion = horizon_sd * price

    # P(touch a barrier at distance d within the horizon), one-sided, reflected BM
    def p_touch(d: float) -> float:
        z = d / horizon_sd
        return min(1.0, 2.0 * (1.0 - _phi(z))) if z > 0 else 1.0

    # a barrier is touched iff either side is reached, so p_any = 1 - P(neither).
    # (The two events are not independent, but for barriers on opposite sides of a
    # continuous path the union bound below is the standard reflection approximation and is
    # validated against Monte Carlo in proof/test_bracket.py.)
    p_any = 1.0 - (1.0 - p_touch(tp_dist)) * (1.0 - p_touch(sl_dist))

    p_tp_first = sl_dist / (tp_dist + sl_dist)
    p_tp_exit = p_tp_first * p_any
    p_sl_exit = (1.0 - p_tp_first) * p_any
    p_timeout = 1.0 - p_any

    # net expectancy of a unit-risk trade at these probabilities, after friction
    cost = round_turn_cost_bps / 1e4
    exp_net = p_tp_exit * (tp_atr / sl_atr) - p_sl_exit - (p_tp_exit + p_sl_exit) * cost

    reasons = []
    fail_reach = p_any < min_touch
    fail_balance = p_tp_exit < min_tp_exit
    if fail_reach:
        reasons.append(
            f"UNREACHABLE: barriers are {tp_dist/price*1e4:.0f}/{sl_dist/price*1e4:.0f} bps away "
            f"but the market is expected to travel ~{expected_excursion/price*1e4:.0f} bps over "
            f"{hold_bars} bars; only {p_any:.0%} chance either is touched, so {p_timeout:.0%} "
            f"exit on the clock")
    if fail_balance:
        reasons.append(
            f"UNBALANCED: even when a barrier is reached, TP is first only {p_tp_first:.0%} of "
            f"the time; P(TP exit) = {p_tp_exit:.1%} < {min_tp_exit:.0%}. A "
            f"{tp_atr:g}xATR target against {sl_atr:g}xATR risks a low-win-rate bet")

    fail_ev = exp_net <= 0
    if fail_ev:
        reasons.append(
            f"NEGATIVE-EV: at these probabilities the expected net is {exp_net:+.3f}R after "
            f"{round_turn_cost_bps:g} bps; the geometry cannot pay for the friction")

    return Verdict(
        price=price, atr=atr, hold_bars=hold_bars,
        tp_dist=round(tp_dist, 8), sl_dist=round(sl_dist, 8),
        expected_excursion=round(expected_excursion, 8),
        p_touch_any=round(p_any, 4), p_tp_first=round(p_tp_first, 4),
        p_tp_exit=round(p_tp_exit, 4), p_sl_exit=round(p_sl_exit, 4),
        p_timeout=round(p_timeout, 4),
        fail_reach=fail_reach, fail_balance=fail_balance, fail_ev=fail_ev,
        exp_net_r=round(exp_net, 4), reasons=reasons,
    )


def exit_mix_test(predicted_p_tp: float, n_tp: int, n_total: int) -> dict:
    """Is the observed take-profit rate consistent with the geometry-implied rate?

    This is the follow-up question the pre-trade gate cannot ask. If the geometry says 34% of
    trades should end at the take-profit and 0 of 27 do, the bracket was not the problem — the
    **driftless-walk assumption was violated**, which means the positions were systematically
    aligned against the move. That is a direction error, and it is a different fix.

    Two-sided by construction: a take-profit rate far ABOVE the prediction is equally
    suspicious (it usually means the bracket, not the signal, produced the win rate).
    """
    from math import comb
    p = max(1e-9, min(1 - 1e-9, predicted_p_tp))
    if n_total <= 0:
        return {"error": "n_total must be positive"}
    # exact two-sided binomial: sum of probabilities no greater than the observed one
    probs = [comb(n_total, k) * p ** k * (1 - p) ** (n_total - k) for k in range(n_total + 1)]
    obs = probs[n_tp]
    p_value = sum(pr for pr in probs if pr <= obs + 1e-15)
    expected = predicted_p_tp * n_total
    verdict = ("CONSISTENT with the bracket geometry" if p_value > 0.05 else
               "INCONSISTENT — the driftless assumption is violated; this is a direction or "
               "volatility-estimate problem, not a bracket problem")
    return {
        "predicted_p_tp": round(predicted_p_tp, 4),
        "expected_tp_count": round(expected, 2),
        "observed_tp_count": n_tp,
        "n_total": n_total,
        "observed_rate": round(n_tp / n_total, 4),
        "p_value_two_sided": round(p_value, 8),
        "verdict": verdict,
    }


def audit_ledger(path: str | Path) -> dict:
    """Re-run the gate against closed trades that were already taken, using each trade's own
    bracket and realised hold. Answers: how many of these could ever have hit TP?"""
    events = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    # join each CLOSE to its OPEN so the trade's OWN atr_1h is used rather than a reconstruction
    opens: dict[tuple, dict] = {}
    for e in events:
        if e.get("event") == "OPEN":
            opens[(e.get("run_id"), e.get("symbol"))] = e

    rows = [e for e in events if e.get("event") == "CLOSE"]
    if not rows:
        return {"error": "no CLOSE events", "path": str(path)}

    out = {"path": str(path), "n_closed": len(rows), "trades": []}
    n_refused = 0
    for e in rows:
        o = opens.get((e.get("run_id"), e.get("symbol")), {})
        price = e.get("entry_price", o.get("entry_price"))
        tp = e.get("tp", o.get("tp"))
        sl = e.get("sl", o.get("sl"))
        atr = o.get("atr_1h")
        minutes = e.get("held_minutes")
        if not all(isinstance(v, (int, float)) for v in (price, tp, sl)):
            continue
        if not isinstance(minutes, (int, float)):
            continue
        tp_dist = abs(tp - price)
        sl_dist = abs(sl - price)
        if tp_dist <= 0 or sl_dist <= 0:
            continue
        # No ATR on the OPEN event (older books): fall back to the stop distance and judge on
        # the tp/sl ratio only. Note the multiple becomes relative, so only the balance gate
        # is meaningful in that case.
        real_atr = atr if isinstance(atr, (int, float)) and atr > 0 else sl_dist
        # hold in bars of the TRADE's own bar size. These probes held 8-12 minutes on 1h
        # signals, i.e. a fraction of one bar; floor at 1 bar, which GIVES the strategy the
        # benefit of the doubt (more time = more chance to touch). Failing even then is the
        # stronger finding.
        bars = max(1, int(round(minutes / 60.0)))
        v = evaluate(price, real_atr, tp_atr=tp_dist / real_atr, sl_atr=sl_dist / real_atr,
                     hold_bars=bars)
        if not v.ok():
            n_refused += 1
        out["trades"].append({
            "exit_reason": e.get("exit_reason"),
            "symbol": e.get("symbol"),
            "held_minutes": minutes,
            "bars_held_used": bars,
            "atr_used": round(real_atr, 4),
            "tp_bps": round(tp_dist / price * 1e4, 1),
            "sl_bps": round(sl_dist / price * 1e4, 1),
            "p_tp_exit": v.p_tp_exit,
            "p_timeout": v.p_timeout,
            "would_refuse": (not v.ok()),
            "reasons": v.reasons,
        })
    out["n_would_refuse"] = n_refused
    out["refused_frac"] = round(n_refused / max(1, len(out["trades"])), 3)
    out["exit_mix"] = {}
    for t in out["trades"]:
        out["exit_mix"][t["exit_reason"]] = out["exit_mix"].get(t["exit_reason"], 0) + 1
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--price", type=float)
    ap.add_argument("--atr", type=float)
    ap.add_argument("--hold-bars", type=int, default=3)
    ap.add_argument("--tp-atr", type=float, default=2.0)
    ap.add_argument("--sl-atr", type=float, default=1.0)
    ap.add_argument("--audit-ledger", type=str)
    a = ap.parse_args()

    if a.audit_ledger:
        r = audit_ledger(a.audit_ledger)
        print(json.dumps({k: v for k, v in r.items() if k != "trades"}, indent=1))
        for t in r.get("trades", [])[:15]:
            flag = "REFUSE" if t["would_refuse"] else "ok    "
            print(f"  {flag} {t['exit_reason']:5s} hold={t["held_minutes"]:>5.1f}m "
                  f"tp={t['tp_bps']:>6.1f}bps sl={t['sl_bps']:>6.1f}bps "
                  f"P(tp)={t['p_tp_exit']:.3f} P(timeout)={t['p_timeout']:.3f}")
        return 0

    if not (a.check and a.price and a.atr):
        ap.print_help(); return 1

    v = evaluate(a.price, a.atr, a.tp_atr, a.sl_atr, a.hold_bars)
    print(json.dumps(v.as_dict(), indent=1))
    print("\n" + ("PASS — bracket is reachable and balanced" if v.ok() else "REFUSE"))
    for r in v.reasons:
        print("  " + r)
    return 0 if v.ok() else 2


if __name__ == "__main__":
    sys.exit(main())
