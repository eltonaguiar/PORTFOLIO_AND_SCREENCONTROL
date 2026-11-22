#!/usr/bin/env python3
"""Is our 26 bps cost model portable? The self-criticism Mercury3's retraction forces.

Mercury3 published and then retracted a "SPY breakout is POST-2010 ONLY" claim, and the retraction
carried the more useful finding:

    "at 10bp/side only 4/7 pre-2010 positive and nothing significant — the family is as much a
     cost arbitrage as a signal (real at <=8bp round trip, gone at 20bp)."

Our standard cost model is `taker_fee=0.0010 + slippage=0.0003` per side = **26 bps round turn**.
That was calibrated on CRYPTO: a 10 bp retail taker fee plus slippage. It is then applied unchanged
to equity and ETF cells — where SPY trades at a ~0.3 bp spread, most brokers charge zero
commission, and a market order in a trillion-dollar ETF does not pay 10 bps.

Two possibilities, and they cannot both be true:

  A) every equity/ETF cell here is genuinely dead, or
  B) our cost model overstates equity friction ~4x, and some cells were killed by the assumption
     rather than by the market.

This runs equity/ETF strategies across a cost grid and reports the break-even cost of each.

Costs are charged on POSITION CHANGES, never on return changes
--------------------------------------------------------------
The first version of this module charged cost whenever the *return* differed from the prior
return. For buy-and-hold every day differs, so it paid 26 bps every single day and Sharpe fell
from 0.62 to -2.90 — an obviously impossible result for a strategy with one entry and no exit.
A return series is not a position series. Each strategy therefore returns an explicit weight
series w_t and the drag is `|w_t - w_{t-1}| * cost`, where a full 0->1->0 cycle charges exactly
one round turn.

  python -m realtime_challenge.proof.cost_portability
"""

from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

RESULTS = Path(__file__).resolve().parent.parent / "results"
COSTS_BPS_RT = [0, 2, 4, 8, 14, 20, 26, 40]
START = "2004-01-01"


def sharpe(r: pd.Series) -> float | None:
    r = r.dropna()
    if len(r) < 250:
        return None
    sd = r.std(ddof=1)
    return round(float(r.mean() / sd * math.sqrt(252)), 3) if sd else None


def cagr(r: pd.Series) -> float | None:
    r = r.dropna()
    if len(r) < 250:
        return None
    eq = (1 + r).cumprod()
    return round(float(eq.iloc[-1] ** (252 / len(r)) - 1), 4)


def build(px: dict[str, pd.Series]) -> dict[str, tuple[pd.Series, pd.Series]]:
    """name -> (weights w_t, asset returns r_t). Gross return is w.shift(1)*r."""
    spy = px["SPY"]
    r = spy.pct_change()
    out: dict[str, tuple[pd.Series, pd.Series]] = {}

    # 1. buy and hold: weight 1 forever, so turnover is a single entry over the whole window
    out["SPY buy-and-hold"] = (pd.Series(1.0, index=spy.index), r)

    # 2. 12-month TSMOM on SPY: weight 0 or 1, flips a few times a year
    mom12 = (spy / spy.shift(252) - 1).shift(1)
    out["SPY 12m TSMOM"] = ((mom12 > 0).astype(float), r)

    # 3. 200-day SMA overlay
    sma200 = spy.rolling(200).mean()
    out["SPY + 200d SMA"] = ((spy > sma200).shift(1).fillna(False).astype(float), r)

    # 4. multi-asset TSMOM, vol-scaled — the Moskowitz/Ooi/Pedersen construction the peer
    #    document cites (52 of 58 futures significant). Portfolio return is the mean of leg
    #    returns; gross exposure is the sum of leg weights so turnover counts every leg.
    leg_w, leg_r = [], []
    for k, s in px.items():
        if k == "SPY":
            continue
        rr = s.pct_change()
        m = (s / s.shift(252) - 1).shift(1)
        sig = rr.rolling(60).std().shift(1) * math.sqrt(252)
        w = (0.10 / sig).clip(0.0, 3.0).where(m > 0, 0.0)   # long-only TSMOM, vol-capped
        leg_w.append(w.rename(k))
        leg_r.append(rr.rename(k))
    if leg_w:
        W = pd.concat(leg_w, axis=1)
        R = pd.concat(leg_r, axis=1)
        port_w = W.sum(axis=1)                       # gross exposure across legs
        port_r = (W.shift(1) * R).sum(axis=1) / W.shape[1]
        out["Multi-asset TSMOM (vol-scaled)"] = (port_w.fillna(0.0), port_r.fillna(0.0))

    return out


def net_after_costs(w: pd.Series, r: pd.Series, cost_bps_rt: float) -> pd.Series:
    """w.shift(1)*r minus |dw| * half a round turn, so 0->1->0 charges exactly one round turn."""
    gross = w.shift(1).fillna(0.0) * r.fillna(0.0)
    per_unit = (cost_bps_rt / 1e4) / 2.0
    turn = w.diff().abs().fillna(w.abs())
    return gross - turn * per_unit


def main() -> int:
    import yfinance as yf

    tickers = ["SPY", "EFA", "EEM", "TLT", "IEF", "GLD", "DBC", "UUP"]
    print(f"loading {len(tickers)} ETFs from {START} ...")
    px: dict[str, pd.Series] = {}
    for t in tickers:
        try:
            d = yf.download(t, start=START, auto_adjust=True, progress=False)["Close"].squeeze()
            if len(d) > 500:
                px[t] = d
        except Exception as exc:
            print(f"  {t}: skip ({type(exc).__name__})")
    print(f"  {len(px)} loaded: {list(px)}\n")

    strat = build(px)
    rows = []
    for name, (w, r) in strat.items():
        turns = float(w.diff().abs().fillna(w.abs()).sum())
        entry = {"strategy": name, "turnover_units": round(turns, 1),
                 "turnover_per_year": round(turns / max(1, len(w)) * 252, 2)}
        for cb in COSTS_BPS_RT:
            net = net_after_costs(w, r, cb)
            d = net.dropna()
            entry[f"sharpe@{cb}"] = sharpe(net)
            entry[f"cagr@{cb}"] = cagr(net)
            entry[f"mean_bps@{cb}"] = round(float(d.mean() * 1e4), 3) if len(d) else None
        be = next((cb for cb in COSTS_BPS_RT
                   if (entry[f"mean_bps@{cb}"] is not None
                       and entry[f"mean_bps@{cb}"] <= 0)), None)
        entry["breaks_at_or_below_bps"] = be
        rows.append(entry)

    print(f"{'strategy':32s} {'turn/yr':>7s}  " +
          "  ".join(f"{c:>6d}" for c in COSTS_BPS_RT) + "   breaks at")
    for e in rows:
        vals = "  ".join(f"{e[f'sharpe@{c}']:>6.2f}" for c in COSTS_BPS_RT)
        be = e["breaks_at_or_below_bps"]
        print(f"{e['strategy']:32s} {e['turnover_per_year']:>7.2f}  {vals}   "
              f"{'<= %d bps' % be if be is not None else 'survives 40'}")

    print("\nNet Sharpe by round-trip cost (bps).")

    # sanity: buy-and-hold has ONE entry over 23 years, so cost must be ~irrelevant to it
    bh = next(e for e in rows if e["strategy"].startswith("SPY buy"))
    flat = all(bh[f"sharpe@{c}"] is not None
               and abs(bh[f"sharpe@{c}"] - bh["sharpe@0"]) < 0.05 for c in COSTS_BPS_RT[1:3])
    print(f"\n  sanity: buy-and-hold must be ~flat across costs -> "
          f"{'OK' if flat else 'STILL WRONG'}")
    print(f"    @0={bh['sharpe@0']}  @4={bh['sharpe@4']}  @26={bh['sharpe@26']}   "
          f"(one entry over 23y, so cost is negligible)")

    surv = {cb: [e["strategy"] for e in rows
                 if e[f"mean_bps@{cb}"] is not None and e[f"mean_bps@{cb}"] > 0]
            for cb in COSTS_BPS_RT}
    for cb in (4, 8, 26):
        print(f"  survivors @{cb:>2d}bps RT: {surv[cb]}")

    out = {
        "question": "is the 26bps crypto-calibrated cost model portable to equity/ETF cells?",
        "trigger": ("Mercury3 retraction: 'real at <=8bp round trip, gone at 20bp'; our model is "
                    "26bps RT, calibrated on a 10bp crypto taker fee"),
        "method_note": ("costs charged on POSITION changes; a first version charged them on RETURN "
                        "changes, which made buy-and-hold pay 26bps/day and was visibly impossible"),
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "costs_bps_rt": COSTS_BPS_RT, "rows": rows,
        "survivors_by_cost": {str(k): v for k, v in surv.items()},
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    body = json.dumps(out, indent=1, default=str)
    (RESULTS / f"cost_portability_{stamp}.json").write_text(body, encoding="utf-8")
    (RESULTS / "cost_portability_latest.json").write_text(body, encoding="utf-8")
    print("\nwrote results/cost_portability_latest.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
