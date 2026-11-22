#!/usr/bin/env python3
"""Does combining these strategies improve risk-adjusted return, as the peer note claims?

A note supplied on 2026-11-22 states: "Combining strategies into one portfolio improved
risk-adjusted returns by 30-50% versus single-strategy approaches in the cited research."

That is a testable claim, and it is testable *here*, on trades this harness actually
measured — no external citation needed. This script:

  1. runs all six pre-registered hypotheses on 1d bars over 3.3 years
  2. builds a proper **daily mark-to-market equity curve per strategy** (a flat book earns
     0.0% that day, not "no observation" — that distinction is what makes a portfolio
     Sharpe comparable at all)
  3. forms the combined book as equal capital across the six (1/6 each)
  4. reports Sharpe, max drawdown and total return for every single strategy, the combined
     book, and buy-and-hold on the same window
  5. reports the **diversification ratio** and the correlation matrix, so the mechanism is
     visible rather than asserted

The claim is scored, not accepted: if the combined Sharpe is not materially above the best
single strategy, the note's 30-50% figure does not reproduce on this book.

  python -m realtime_challenge.proof.portfolio_combination
"""

from __future__ import annotations

import json
import math
import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from realtime_challenge import data as D, engine as E, strategies as S  # noqa: E402
from realtime_challenge.costs import CostModel, DEFAULT_COSTS  # noqa: E402

BASES = ["BTC", "ETH", "SOL", "XRP", "DOGE", "ADA", "LINK"]
TF = "1d"
BARS = 1200
OUT = Path(__file__).resolve().parent.parent / "results" / "portfolio_combination.json"


def strategy_daily_returns(df: pd.DataFrame, trades, costs: CostModel) -> pd.Series:
    """Daily mark-to-market return series for one strategy on one symbol.

    A day with no position is 0.0, not NaN. That matters: a portfolio Sharpe computed only
    over days the strategy was in the market silently deletes the cost of being flat, and
    flatters every strategy with low exposure.
    """
    close = df["close"]
    daily = pd.Series(0.0, index=df.index)
    idx = df.index

    for t in trades:
        try:
            i0 = idx.get_loc(pd.Timestamp(t["entry_ts"]))
            i1 = idx.get_loc(pd.Timestamp(t["exit_ts"]))
        except KeyError:
            continue
        if i1 <= i0:
            continue
        long_ = t["direction"] == "LONG"
        entry, exitp = t["entry_price"], t["exit_price"]

        # entry bar: mark from the fill price to that bar's close
        f = close.iloc[i0] / entry
        daily.iloc[i0] += (f - 1.0) if long_ else (1.0 - f)
        # intermediate bars: close-to-close
        for j in range(i0 + 1, i1):
            f = close.iloc[j] / close.iloc[j - 1]
            daily.iloc[j] += (f - 1.0) if long_ else (1.0 - f)
        # exit bar: last close to the exit fill
        f = exitp / close.iloc[i1 - 1]
        daily.iloc[i1] += (f - 1.0) if long_ else (1.0 - f)

    return daily


def stats(daily: pd.Series, ppy: float = 365.0) -> dict:
    d = daily.fillna(0.0)
    eq = (1.0 + d).cumprod()
    sd = d.std(ddof=1)
    return {
        "total_return": round(float(eq.iloc[-1] - 1.0), 4),
        "sharpe": None if sd == 0 else round(float(d.mean() / sd * math.sqrt(ppy)), 3),
        "max_drawdown": round(float((eq / eq.cummax() - 1.0).min()), 4),
        "ann_vol": round(float(sd * math.sqrt(ppy)), 4),
        "days_in_market": round(float((d != 0).mean()), 3),
    }


def main() -> int:
    print(f"fetching {len(BASES)} symbols @ {TF} x {BARS} from binance ...")
    panel = D.fetch_panel("binance", BASES, TF, BARS)
    any_df = next(iter(panel.values()))
    print(f"  window {any_df.index[0].date()} -> {any_df.index[-1].date()} ({len(any_df)} bars)")

    # ---- per (strategy, symbol) daily return series
    per_cell: dict[str, dict[str, pd.Series]] = {}
    for name, cfg in S.REGISTRY.items():
        per_cell[name] = {}
        for base, df in panel.items():
            sig = cfg["fn"](df)
            r = E.run_from_signals(df, sig, name, base, tp_atr=cfg["tp_atr"], sl_atr=cfg["sl_atr"],
                                   max_bars=cfg["max_bars"], costs=DEFAULT_COSTS, timeframe=TF,
                                   allow_short=cfg["allow_short"])
            per_cell[name][base] = strategy_daily_returns(df, r.trades, DEFAULT_COSTS)

    # ---- each strategy as an equal-weight book across symbols
    strat_daily = pd.DataFrame({s: pd.concat(v, axis=1).mean(axis=1) for s, v in per_cell.items()})

    # ---- combined book: equal capital across strategies
    combined = strat_daily.mean(axis=1)

    # ---- buy and hold, equal weight across symbols
    bh = pd.concat({b: df["close"].pct_change() for b, df in panel.items()}, axis=1).mean(axis=1)

    rows = {s: stats(strat_daily[s]) for s in strat_daily.columns}
    rows["COMBINED_equal_weight"] = stats(combined)
    rows["BUY_AND_HOLD_equal_weight"] = stats(bh)

    ranked = sorted(
        [(k, v) for k, v in rows.items() if k not in ("COMBINED_equal_weight", "BUY_AND_HOLD_equal_weight") and v["sharpe"] is not None],
        key=lambda kv: -kv[1]["sharpe"],
    )
    best_name, best = ranked[0] if ranked else (None, {"sharpe": None})
    comb = rows["COMBINED_equal_weight"]

    improvement = None
    if best.get("sharpe") and comb["sharpe"] is not None and best["sharpe"] > 0:
        improvement = round((comb["sharpe"] / best["sharpe"] - 1.0) * 100, 1)

    # ---- correlation matrix + diversification ratio (mechanism, not vibes)
    corr = strat_daily.corr().round(3)
    w = np.ones(len(strat_daily.columns)) / len(strat_daily.columns)
    vols = strat_daily.std(ddof=1).to_numpy() * math.sqrt(365)
    cov = strat_daily.cov().to_numpy() * 365
    port_vol = float(math.sqrt(w @ cov @ w))
    avg_vol = float(w @ vols)
    div_ratio = round(avg_vol / port_vol, 3) if port_vol > 0 else None

    # ---- how many strategies actually have a positive Sharpe?
    positive = [k for k, v in rows.items() if k in strat_daily.columns and (v["sharpe"] or 0) > 0]

    verdict = (
        "CLAIM DOES NOT REPRODUCE: the equally weighted combination is "
        f"{'better' if (comb['sharpe'] or -9) > (best.get('sharpe') or 0) else 'not better'} "
        f"than the best single strategy ({comb['sharpe']} vs {best.get('sharpe')}), "
        f"i.e. {improvement}% change, versus the claimed +30-50%."
        if improvement is not None
        else "UNSCORED: best single strategy has non-positive Sharpe, so a percentage improvement is meaningless."
    )

    out = {
        "test": "does combining the six pre-registered strategies improve risk-adjusted return?",
        "peer_claim": "combining strategies into one portfolio improved risk-adjusted returns by 30-50%",
        "venue": "binance", "timeframe": TF, "bars": BARS, "symbols": BASES,
        "window": {"start": str(any_df.index[0]), "end": str(any_df.index[-1])},
        "costs": DEFAULT_COSTS.as_dict(),
        "per_book": rows,
        "best_single": {"name": best_name, **best},
        "combined": comb,
        "improvement_vs_best_single_pct": improvement,
        "n_strategies_with_positive_sharpe": len(positive),
        "positive_sharpe_strategies": positive,
        "avg_pairwise_correlation": round(float(corr.where(~np.eye(len(corr), dtype=bool)).stack().mean()), 3),
        "diversification_ratio": div_ratio,
        "correlation_matrix": corr.to_dict(),
        "verdict": verdict,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")

    print(f"\n{'book':32s} {'total_ret':>10s} {'sharpe':>8s} {'maxDD':>8s} {'ann_vol':>8s} {'in_mkt':>7s}")
    for k, v in sorted(rows.items(), key=lambda kv: -(kv[1]["sharpe"] if kv[1]["sharpe"] is not None else -99)):
        print(f"{k:32s} {v['total_return']:>10.4f} {str(v['sharpe']):>8s} {v['max_drawdown']:>8.4f} "
              f"{v['ann_vol']:>8.3f} {v['days_in_market']:>7.3f}")
    print(f"\navg pairwise correlation: {out['avg_pairwise_correlation']}")
    print(f"diversification ratio:    {div_ratio}  (>1 means the mix is less volatile than its parts)")
    print(f"strategies with positive Sharpe: {len(positive)}/{len(strat_daily.columns)}")
    print(f"\nVERDICT: {verdict}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
