"""Band-rebalancing logic for the portfolio templates (F2).

Rule, inherited from 04-investment-strategy/portfolios.json (F1):
    "Rebalance on bands (+/-5% absolute), not on a calendar, and never on a
    signal from this programme until something passes G1-G5."

Cost assumption (F2): 5 bp per side of every trade, charged on the notional
of each sleeve traded. A sleeve whose weight is outside its target band is
traded back exactly to target. Buys and sells must net to zero (portfolio
stays at 100%), so every rebalance has equal one-sided notional on each side.

The module is deliberately deterministic and price-free: it implements the
rule and the cost arithmetic. A historical drift/backtest (F4) supplies the
realised rebalance frequency; F2 reports cost PER EVENT, never an annualised
number fabricated from an assumed frequency.

Usage:
    python rebalance.py          # worked demo + self-checks, human readable
    python rebalance.py --json   # machine-readable manifest
"""

from __future__ import annotations

import argparse
import json

import sys

BAND_PP = 5.0            # +/-5 percentage points, absolute
COST_BP_PER_SIDE = 5.0   # 5 bp on each side (buy or sell) of traded notional


def load_portfolios(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def out_of_band(current_pct: float, target_pct: float, band_pp: float = BAND_PP) -> bool:
    """True if a sleeve's weight sits outside its +/-band_pp target band."""
    return abs(current_pct - target_pct) > band_pp


def rebalance_trades(currents: dict[str, float], targets: dict[str, float],
                     band_pp: float = BAND_PP) -> list[dict]:
    """Return the list of sleeves to trade to restore every sleeve to target.

    Each entry: {sleeve, target, current, drift_pp, side, trade_pp}
    side is 'buy' (under target) or 'sell' (over target). Sleeves inside the
    band are not traded. Returns an empty list when nothing is out of band.
    """
    trades = []
    for sleeve, target in targets.items():
        current = currents.get(sleeve, target)
        drift = current - target
        if out_of_band(current, target, band_pp):
            trades.append({
                "sleeve": sleeve,
                "target_pct": target,
                "current_pct": current,
                "drift_pp": round(drift, 4),
                "side": "buy" if drift < 0 else "sell",
                "trade_pp": round(abs(drift), 4),   # magnitude to trade back to target; side encodes direction
            })
    return trades


def rebalance_cost_bp(trades: list[dict], cost_bp_per_side: float = COST_BP_PER_SIDE) -> dict:
    """Cost of one rebalance event, in bp of total portfolio value.

    cost_bp = (sum of one-sided traded notional / 100) * cost_bp_per_side
    Since buys == sells, sum|trade_pp| = 2 * buy_notional_pp.
    """
    buy_pp = sum(t["trade_pp"] for t in trades if t["side"] == "buy")
    sell_pp = sum(t["trade_pp"] for t in trades if t["side"] == "sell")
    one_sided_pp = buy_pp  # == sell_pp when balanced
    cost_fraction = (one_sided_pp / 100.0) * (cost_bp_per_side / 10000.0) * 2.0  # both sides
    cost_bp = cost_fraction * 10000.0
    return {
        "buy_notional_pp": round(buy_pp, 4),
        "sell_notional_pp": round(sell_pp, 4),
        "balanced": abs(buy_pp - sell_pp) < 1e-9,
        "cost_bp_per_side": cost_bp_per_side,
        "cost_bp_of_portfolio_per_event": round(cost_bp, 6),
    }


def weights_sum_to_100(weights: dict[str, float]) -> bool:
    return abs(sum(weights.values()) - 100.0) < 1e-9


def trades_net_to_zero(trades: list[dict]) -> bool:
    buys = sum(t["trade_pp"] for t in trades if t["side"] == "buy")
    sells = sum(t["trade_pp"] for t in trades if t["side"] == "sell")
    return abs(buys - sells) < 1e-9


def demo(portfolios_path: str) -> dict:
    data = load_portfolios(portfolios_path)
    results = {"rule": data["rebalance_rule"],
               "band_pp": BAND_PP,
               "cost_bp_per_side": COST_BP_PER_SIDE,
               "examples": [],
               "self_checks": {}}

    # Worked example: Stable portfolio, equity drifts +6 pp (just outside band),
    # cash absorbs the -6 pp, bonds unchanged.
    stable = data["portfolios"][0]
    targets = {s["sleeve"]: s["weight_pct"] for s in stable["sleeves"]}
    currents = {"Cash & T-bills / HISA": 49.0,   # 55 -> 49 (-6)
                "Short-duration govt bonds": 25.0,
                "Broad equity": 26.0}            # 20 -> 26 (+6), out of band
    trades = rebalance_trades(currents, targets)
    cost = rebalance_cost_bp(trades)
    results["examples"].append({
        "portfolio": stable["name"],
        "scenario": "equity +6 pp drift, cash -6 pp, bonds unchanged",
        "currents_pct": currents,
        "targets_pct": targets,
        "trades": trades,
        "cost": cost,
        "weights_sum_100_before": weights_sum_to_100(currents),
        "weights_sum_100_after": weights_sum_to_100(targets),
    })

    # In-band control: same portfolio, equity +4 pp (inside band) -> no trade.
    currents_in = {"Cash & T-bills / HISA": 51.0, "Short-duration govt bonds": 25.0, "Broad equity": 24.0}
    trades_in = rebalance_trades(currents_in, targets)
    cost_in = rebalance_cost_bp(trades_in)
    results["examples"].append({
        "portfolio": stable["name"],
        "scenario": "equity +4 pp drift (inside +/-5pp band) -> no rebalance",
        "currents_pct": currents_in,
        "targets_pct": targets,
        "trades": trades_in,
        "cost": cost_in,
        "no_trade_because_in_band": True,
    })

    # Self-checks across all three portfolios: every sleeve carries a weight,
    # weights sum to 100.
    all_ok = True
    for p in data["portfolios"]:
        w = {s["sleeve"]: s["weight_pct"] for s in p["sleeves"]}
        ok = weights_sum_to_100(w)
        all_ok = all_ok and ok
        results["self_checks"][p["name"]] = {
            "sleeves": len(w),
            "weights_sum_pct": round(sum(w.values()), 4),
            "sums_to_100": ok,
        }
    results["self_checks"]["all_portfolios_sum_to_100"] = all_ok
    results["self_checks"]["worked_trades_net_to_zero"] = trades_net_to_zero(trades)
    results["self_checks"]["worked_cost_0_6_bp"] = abs(cost["cost_bp_of_portfolio_per_event"] - 0.6) < 1e-6
    return results


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true", help="emit machine-readable manifest")
    ap.add_argument("--portfolios", default="04-investment-strategy/portfolios.json")
    args = ap.parse_args()

    results = demo(args.portfolios)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(f"Rule: {results['rule']}")
        print(f"Band: +/-{results['band_pp']} pp absolute | Cost: {results['cost_bp_per_side']} bp/side\n")
        for ex in results["examples"]:
            print(f"Example: {ex['portfolio']}")
            print(f"  Scenario: {ex['scenario']}")
            for t in ex["trades"]:
                print(f"  TRADE {t['side'].upper():4s} {t['sleeve']}: {t['current_pct']}% -> {t['target_pct']}%  ({t['trade_pp']} pp)")
            if not ex["trades"]:
                print("  TRADE: none (sleeve inside band)")
            c = ex["cost"]
            print(f"  Cost: {c['cost_bp_of_portfolio_per_event']} bp of portfolio per event "
                  f"(buy {c['buy_notional_pp']}pp, sell {c['sell_notional_pp']}pp, balanced={c['balanced']})")
            print()
        print("Self-checks:")
        for k, v in results["self_checks"].items():
            print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
