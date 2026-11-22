#!/usr/bin/env python3
"""Tests for the P7 bracket gate. The closed forms are validated against Monte Carlo, because a
reachability formula that is wrong in the permissive direction would approve unreachable brackets
and make the live books look like the gate was working.

  python -m realtime_challenge.proof.test_bracket
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from realtime_challenge.bracket import evaluate

PASSED, FAILED = 0, 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global PASSED, FAILED
    if cond:
        PASSED += 1
        print(f"  PASS  {name}")
    else:
        FAILED += 1
        print(f"  FAIL  {name}  {detail}")


def mc(price, atr, tp_atr, sl_atr, hold_bars, n=20000, seed=3):
    """Driftless random walk in PRICE terms: per-bar sd chosen so the horizon sd equals
    atr*sqrt(hold_bars), which is the same quantity the closed form uses. Barriers are the
    TP and SL distances, touched first-and-only (no time stop inside the horizon)."""
    rng = np.random.default_rng(seed)
    horizon_sd = atr * math.sqrt(hold_bars)
    bar_sd = horizon_sd / math.sqrt(hold_bars)
    tp, sl = tp_atr * atr, sl_atr * atr
    steps = rng.normal(0.0, bar_sd, size=(n, hold_bars))
    path = np.cumsum(steps, axis=1)
    hit_tp = (path >= tp).any(axis=1)
    hit_sl = (path <= -sl).any(axis=1)
    # first-touch side on the realised path
    first_tp = np.zeros(n, dtype=bool)
    for i in range(n):
        p = path[i]
        it = np.argmax(p >= tp) if hit_tp[i] else hold_bars + 1
        is_ = np.argmax(p <= -sl) if hit_sl[i] else hold_bars + 1
        first_tp[i] = it < is_
    return {
        "p_any": float((hit_tp | hit_sl).mean()),
        "p_tp_first": float(first_tp[hit_tp | hit_sl].mean()) if (hit_tp | hit_sl).any() else 0.0,
        "p_tp_exit": float(first_tp.mean()),
    }


def main() -> int:
    print("P7 bracket gate — formula vs Monte Carlo")

    # 1. the exact result: driftless walk, P(TP before SL) = sl/(tp+sl)
    v = evaluate(price=100.0, atr=1.0, tp_atr=2.0, sl_atr=1.0, hold_bars=10)
    # Verdict rounds to 4dp, so the tolerance is 1e-4 rather than 1e-6
    check("balance is exact: tp2/sl1 -> P(TP first)=1/3",
          abs(v.p_tp_first - 1 / 3) < 1e-4, f"got {v.p_tp_first}")
    v2 = evaluate(price=100.0, atr=1.0, tp_atr=0.5, sl_atr=2.0, hold_bars=10)
    check("balance is exact: tp0.5/sl2 -> P(TP first)=0.8",
          abs(v2.p_tp_first - 0.8) < 1e-6, f"got {v2.p_tp_first}")

    # 2. closed form vs MC on three regimes (tight, moderate, wide relative to horizon)
    print("\n  regime                        formula   MC      delta")
    for tp_atr, sl_atr, hold in [(1.0, 1.0, 4), (2.0, 1.0, 10), (3.0, 1.5, 60)]:
        f = evaluate(price=100.0, atr=1.0, tp_atr=tp_atr, sl_atr=sl_atr, hold_bars=hold)
        m = mc(100.0, 1.0, tp_atr, sl_atr, hold)
        d = abs(f.p_tp_exit - m["p_tp_exit"])
        print(f"  tp{tp_atr:g} sl{sl_atr:g} H{hold:<3d}                 "
              f"{f.p_tp_exit:.3f}     {m['p_tp_exit']:.3f}   {d:.3f}")
        # the approximation is documented as coarse; require the same ballpark and same side
        check(f"MC agrees within 0.10 (tp{tp_atr:g} sl{sl_atr:g} H{hold})", d < 0.10, f"delta={d:.3f}")
        check(f"MC agrees on p_any within 0.12 (H{hold})",
              abs(f.p_touch_any - m["p_any"]) < 0.12,
              f"f={f.p_touch_any:.3f} mc={m['p_any']:.3f}")

    # 3. THE LIVE PROBE'S BRACKET — and the finding that overturned my earlier claim.
    #    BTC at 59,700, 1h ATR 426 (0.71%), tp 0.9xATR, sl 0.55xATR, 3-bar hold.
    #    I had written that the bracket was "wider than the expected move over the hold,
    #    therefore unreachable". The geometry says otherwise: it IS reachable. It is refused
    #    for a different and worse reason — it is negative-EV at the probabilities its own
    #    geometry implies, so it could not have paid even with a perfectly-timed signal.
    probe = evaluate(price=59700.0, atr=426.0, tp_atr=0.9, sl_atr=0.55, hold_bars=3)
    print(f"\n  live-probe bracket: P(touch)={probe.p_touch_any:.2f} "
          f"P(TP exit)={probe.p_tp_exit:.3f} P(timeout)={probe.p_timeout:.2f} "
          f"E[net]={probe.exp_net_r:+.4f}R")
    check("probe bracket is REACHABLE (barriers are inside the expected excursion)",
          not probe.fail_reach, f"p_any={probe.p_touch_any}")
    check("probe bracket is balanced enough on first-touch odds",
          not probe.fail_balance, f"p_tp_exit={probe.p_tp_exit}")
    check("probe bracket is refused on EV/edge-demand, not geometry", probe.fail_ev,
          f"exp_net={probe.exp_net_r} req_edge={probe.required_edge_pp}pp")
    print(f"    probe 0.9/0.55 needs {probe.required_win_rate:.1%} vs "
          f"{probe.geometry_win_rate:.1%} geometry = {probe.required_edge_pp:+.2f}pp of edge")
    check("probe bracket overall is refused", not probe.ok())

    # 3b. THE FOLLOW-UP: 0 of 27 take-profits against a geometry-implied 34%.
    #     If the geometry is right, seeing zero is essentially impossible — so the bracket
    #     was NOT the binding constraint. Something else (direction) was.
    from realtime_challenge.bracket import exit_mix_test
    em = exit_mix_test(probe.p_tp_exit, n_tp=0, n_total=27)
    print(f"\n  exit-mix vs geometry: expected {em['expected_tp_count']} TPs of 27, "
          f"observed {em['observed_tp_count']}, p={em['p_value_two_sided']:.2e}")
    check("0/27 is statistically INCOMPATIBLE with the bracket geometry",
          em["p_value_two_sided"] < 0.001, str(em))
    check("verdict names the violated assumption, not the bracket",
          "driftless assumption is violated" in em["verdict"], em["verdict"])

    # and the diagnostic is not trigger-happy: an outcome at the predicted rate passes
    em_ok = exit_mix_test(0.34, n_tp=9, n_total=27)
    check("9/27 at a predicted 34% is judged CONSISTENT",
          "CONSISTENT" in em_ok["verdict"], em_ok["verdict"])

    # 4. THE IDENTITY: under a driftless walk every bracket is exactly zero-EV before costs.
    #    With p_tp = sl/(tp+sl) and p_sl = tp/(tp+sl),
    #        EV = p_tp*(tp/sl) - p_sl = tp/(tp+sl) - tp/(tp+sl) = 0
    #    for ALL (tp, sl). So no bracket can create an edge, and after any friction every
    #    bracket is negative. The entire edge must come from the entry being right more often
    #    than the geometry implies. A symmetric 1:1 bracket is therefore REFUSED, correctly.
    print("\n  driftless identity — gross EV before costs must be 0 for every bracket:")
    worst = 0.0
    for tp in (0.5, 1.0, 2.0, 3.0):
        for sl in (0.5, 1.0, 2.0, 3.0):
            v_ = evaluate(price=100.0, atr=1.0, tp_atr=tp, sl_atr=sl, hold_bars=50,
                          round_turn_cost_bps=0.0)
            gross = (v_.p_tp_exit * (tp / sl) - v_.p_sl_exit)
            worst = max(worst, abs(gross))
            print(f"    tp{tp:<4g} sl{sl:<4g} p_tp={v_.p_tp_exit:.4f} "
                  f"p_sl={v_.p_sl_exit:.4f} gross_EV={gross:+.6f}R")
    check("gross EV is 0 for every bracket (identity holds)", worst < 0.02, f"worst={worst:.4f}")

    sym = evaluate(price=100.0, atr=1.0, tp_atr=1.0, sl_atr=1.0, hold_bars=30)
    check("symmetric 1:1 bracket is REFUSED after costs", not sym.ok(),
          f"E={sym.exp_net_r}R")
    check("refused on EV, not on reachability", sym.fail_ev and not sym.fail_reach)
    print(f"    1:1 needs {sym.required_win_rate:.1%} win rate vs {sym.geometry_win_rate:.1%} "
          f"geometry -> {sym.required_edge_pp:+.2f}pp of edge")
    check("1:1 break-even win rate is just above 50% (friction)",
          0.50 < sym.required_win_rate < 0.51, f"{sym.required_win_rate}")

    # 4b. THE GATE IS NOT A BLOCKER: supplying a measured directional edge lets a bracket pass.
    #     This is the only way anything can pass, and it is why the live loop refuses everything
    #     today — no strategy in this repo has a demonstrated edge to supply.
    edged = evaluate(price=100.0, atr=1.0, tp_atr=1.0, sl_atr=1.0, hold_bars=30,
                     assumed_p_tp=0.60)
    print(f"    with a 60% supplied hit rate: E={edged.exp_net_r:+.4f}R ok={edged.ok()}")
    check("a bracket with a real supplied edge PASSES", edged.ok(), str(edged.reasons[:1]))
    check("that bracket is not flagged for reachability either", not edged.fail_reach)

    # 4c. THE STRUCTURE OF THE REQUIREMENT: required edge == cost/(1+tp/sl), so it is bounded
    #     above by the round-trip cost and can never exceed it. There is therefore no such thing
    #     as a bracket that "demands unrealistic skill" — every bracket demands LESS edge than
    #     the friction itself. What varies is only how many trades it takes to VERIFY that edge.
    print("\n  required edge and verification cost by bracket:")
    for tp, sl in [(0.5, 1.0), (1.0, 1.0), (2.0, 1.0), (3.0, 1.0), (6.0, 0.5)]:
        g = evaluate(price=100.0, atr=1.0, tp_atr=tp, sl_atr=sl, hold_bars=200)
        pred = 26.0 / (1.0 + tp / sl) / 1e4 * 100
        print(f"    tp{tp:<4g} sl{sl:<4g} need={g.required_edge_pp:+.3f}pp  "
              f"(cost/(1+ratio)={pred:+.3f}pp)  n_to_verify={g.required_n_to_verify:,}")
        check(f"required edge == cost/(1+ratio) for tp{tp:g}/sl{sl:g}",
              abs(g.required_edge_pp - pred) < 0.01,
              f"{g.required_edge_pp} vs {pred}")

    greedy = evaluate(price=100.0, atr=1.0, tp_atr=6.0, sl_atr=0.5, hold_bars=200)
    check("even an extreme bracket demands less edge than the friction itself",
          greedy.required_edge_pp < 26.0, f"{greedy.required_edge_pp}pp")
    check("required edge is still positive for every bracket", greedy.required_edge_pp > 0)

    # 5. the classic asymmetry trap: wide TP, tight SL. Reachable but a low-win-rate bet.
    trap = evaluate(price=100.0, atr=1.0, tp_atr=3.0, sl_atr=0.5, hold_bars=40)
    check("wide-TP/tight-SL is flagged as unbalanced", trap.fail_balance,
          f"p_tp_exit={trap.p_tp_exit}")
    check("but it is NOT flagged unreachable (barriers are hittable)",
          not trap.fail_reach, f"p_any={trap.p_touch_any}")

    # 5b. units regression: expected_excursion must be in PRICE units, not price*atr.
    #     A 426-point ATR on a 59,700 BTC over 1 bar is ~71 bps, not ~5.5 million bps.
    u = evaluate(price=59700.0, atr=426.0, tp_atr=2.0, sl_atr=1.0, hold_bars=1)
    bps = u.expected_excursion / 59700.0 * 1e4
    print(f"\n  units check: expected excursion = {u.expected_excursion:.1f} price = {bps:.1f} bps")
    check("expected_excursion is in price units (71 bps, not millions)", 60 < bps < 85, f"{bps:.1f}")
    check("expected_excursion equals atr*sqrt(hold) in price units",
          abs(u.expected_excursion - 426.0) < 1e-6, str(u.expected_excursion))

    # 6. monotonicity: a longer hold must never lower the touch probability
    prev = -1.0
    mono = True
    for h in (1, 2, 4, 8, 16, 32):
        cur = evaluate(price=100.0, atr=1.0, tp_atr=1.0, sl_atr=1.0, hold_bars=h).p_touch_any
        if cur < prev - 1e-9:
            mono = False
        prev = cur
    check("p_touch_any is monotone increasing in hold_bars", mono)

    # 7. degenerate input is rejected rather than silently returning a verdict
    try:
        evaluate(price=0.0, atr=1.0, tp_atr=1.0, sl_atr=1.0, hold_bars=3)
        check("zero price raises", False)
    except ValueError:
        check("zero price raises", True)

    print(f"\n{PASSED} passed, {FAILED} failed")
    return 0 if FAILED == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
