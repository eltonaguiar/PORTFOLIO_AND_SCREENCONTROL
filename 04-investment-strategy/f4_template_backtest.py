"""F4 — Portfolio template backtest 2010-2026, net of MER and rebalancing, free data.

Reads 04-investment-strategy/portfolios.json, maps every sleeve to a free
Yahoo Finance proxy (yfinance monthly adjusted close, a total-return proxy
since it includes distributions), simulates band rebalancing (+/-5pp
absolute, calendar- and signal-agnostic, 5 bp per traded side per the F2 /
rebalance.py convention) and monthly MER drag, and reports CAGR / max
drawdown versus each template's target band.

Nothing here is investment advice. Templates only.

Inputs flagged ASSUMED:
- Every MER value is assumed pending verification against the issuer's ETF
  Facts; each is bounded by portfolios.json mer_limit_bp where one is stated.
- Price data: Yahoo Finance via yfinance, fetched at run time (fetch date
  printed in the manifest); proxy tickers are documented per sleeve.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parent
PORTFOLIOS = ROOT / "portfolios.json"
RESULTS = ROOT / "results" / "f4_template_backtest_latest.json"

REQUESTED_START = "2010-01-01"
REQUESTED_END = dt.date.today().isoformat()
BAND_PP = 5.0
COST_PER_SIDE = 5e-4  # 5 bp per side; two sleeves drifting 6 pp each -> 0.6 bp of portfolio per event (F2 convention)

# Sleeve -> (ticker, MER bp ASSUMED, source note). MER values are placeholders
# pending verification against issuer ETF Facts; none exceeds the limit in
# portfolios.json where one is stated.
PROXIES = {
    ("Stable / low-risk", "Cash & T-bills / HISA"):
        ("PSA.TO", 14, "Purpose High Interest Savings ETF (cash/HISA proxy); MER ASSUMED"),
    ("Stable / low-risk", "Short-duration govt bonds"):
        ("XSB.TO", 11, "iShares Short-Term High Quality Canadian Bond ETF; MER ASSUMED, limit 15 bp"),
    ("Stable / low-risk", "Broad equity"):
        ("XIC.TO", 6, "iShares Core S&P/TSX Capped Composite (Canadian broad-equity proxy for 'global index ETF'); MER ASSUMED, limit 10 bp"),
    ("Moderate", "Cash & bills"):
        ("PSA.TO", 14, "MER ASSUMED"),
    ("Moderate", "Bonds (1-5y)"):
        ("XSB.TO", 11, "MER ASSUMED, limit 15 bp"),
    ("Moderate", "Broad equity (global index)"):
        ("VXC.TO", 23, "Vanguard FTSE All-World ex-Canada Index ETF; MER ASSUMED"),
    ("Moderate", "Diversifier (commodity/gold or trend)"):
        ("CGL.TO", 17, "iShares Gold Bullion ETF; MER ASSUMED"),
    ("Aggressive", "Broad equity (global, incl. EM)"):
        ("VXC.TO", 23, "MER ASSUMED"),
    ("Aggressive", "Small-cap value tilt"):
        ("IWN", 24, "US-listed iShares Russell 2000 Value ETF proxy; CAD account pays FX on conversion (F5 trap); MER ASSUMED"),
    ("Aggressive", "Crypto"):
        ("BTC-USD", 0, "no MER; trading spread / cost not modelled; ASSUMED 0 bp"),
    ("Aggressive", "Cash buffer"):
        ("PSA.TO", 14, "MER ASSUMED"),
}


def load_portfolios():
    with open(PORTFOLIOS) as fh:
        return json.load(fh)["portfolios"]


def sleeve_inputs(portfolios):
    """Build per-portfolio sleeve list: (name, weight_fraction, ticker, mer_bp, note)."""
    out = {}
    for p in portfolios:
        rows = []
        for s in p["sleeves"]:
            key = (p["name"], s["sleeve"])
            if key not in PROXIES:
                raise KeyError(f"no proxy defined for {key}")
            ticker, mer, note = PROXIES[key]
            rows.append(
                {
                    "sleeve": s["sleeve"],
                    "weight": s["weight_pct"] / 100.0,
                    "ticker": ticker,
                    "mer_bp": mer,
                    "note": note,
                }
            )
        out[p["name"]] = rows
    return out


def download_prices(tickers):
    prices = {}
    for t in tickers:
        s = yf.download(
            t, start=REQUESTED_START, end=REQUESTED_END, interval="1mo",
            auto_adjust=False, progress=False,
        )["Adj Close"]
        s.name = t
        prices[t] = s
    df = pd.concat(prices.values(), axis=1)
    df.columns = list(prices.keys())
    return df.sort_index()


def simulate(sleeves, rets, limit_mer=None):
    """Monthly simulation. Returns dict of metrics or None if no overlap."""
    sub = rets[[s["ticker"] for s in sleeves]].dropna()
    if sub.empty:
        return None
    months = sub.index
    n_ret = len(months) - 1
    if n_ret <= 0:
        return None

    def run(mer_bps=None, rebalance=True):
        value = 1.0
        path = [1.0]
        w = {s["sleeve"]: s["weight"] for s in sleeves}
        events = 0
        cost_bp_sum = 0.0
        mer = mer_bps or {s["sleeve"]: s["mer_bp"] for s in sleeves}
        for i in range(1, len(months)):
            r = sub.iloc[i]
            port_ret = sum(w[s["sleeve"]] * r[s["ticker"]] for s in sleeves)
            mer_drag = sum(
                w[s["sleeve"]] * (mer[s["sleeve"]] / 10000.0 / 12.0) for s in sleeves
            )
            value *= 1 + port_ret - mer_drag
            path.append(value)
            if rebalance:
                # weights drift with monthly returns; +/-5pp bands are checked vs target
                drifted = {
                    s["sleeve"]: w[s["sleeve"]] * (1 + r[s["ticker"]]) for s in sleeves
                }
                tot = sum(drifted.values())
                drifted = {k: v / tot for k, v in drifted.items()}
                target = {s["sleeve"]: s["weight"] for s in sleeves}
                breached = {
                    n: abs(drifted[n] - target[n]) > BAND_PP / 100.0 for n in target
                }
                if any(breached.values()):
                    traded = sum(
                        abs(drifted[n] - target[n])
                        for n, hit in breached.items() if hit
                    )
                    cost = traded * COST_PER_SIDE  # 5 bp per side (F2 convention)
                    value *= 1 - cost
                    cost_bp_sum += cost * 1e4
                    events += 1
                    after = value
                    w = {
                        n: (target[n] if breached[n] else drifted[n]) * after
                        for n in target
                    }
                    stot = sum(w.values())
                    w = {k: v / stot for k, v in w.items()}
                else:
                    w = drifted
        total_ret = value - 1.0
        cagr = (1 + total_ret) ** (12.0 / n_ret) - 1.0
        peak = 0.0
        mdd = 0.0
        for v in path:
            if v > peak:
                peak = v
            dd = (peak - v) / peak
            if dd > mdd:
                mdd = dd
        return {"cagr": cagr, "mdd": mdd, "events": events, "cost_bp_sum": cost_bp_sum}

    net = run()
    gross = run(mer_bps={s["sleeve"]: 0.0 for s in sleeves}, rebalance=False)
    at_limit = run(mer_bps={s["sleeve"]: s["mer_bp"] for s in sleeves} | (limit_mer or {}))
    return {
        "start": str(sub.index[0].date()),
        "end": str(sub.index[-1].date()),
        "n_months": int(n_ret),
        "sleeves": [
            {
                "sleeve": s["sleeve"],
                "weight_pct": round(s["weight"] * 100, 6),
                "ticker": s["ticker"],
                "mer_bp_assumed": s["mer_bp"],
                "first_date": str(sub[s["ticker"]].dropna().index[0].date()),
                "last_date": str(sub[s["ticker"]].dropna().index[-1].date()),
            }
            for s in sleeves
        ],
        "cagr_net": net["cagr"],
        "cagr_gross": gross["cagr"],
        "mdd_net": net["mdd"],
        "rebalance_events": net["events"],
        "total_cost_bp_sum": net["cost_bp_sum"],
        "cagr_net_at_mer_limit": at_limit["cagr"],
        "cagr_delta_bp_at_limit": (at_limit["cagr"] - net["cagr"]) * 1e4,
    }


def target_band(p):
    lo, hi = p["target_nominal_pct"].split("-")
    return float(lo), float(hi)


def main():
    portfolios = load_portfolios()
    inputs = sleeve_inputs(portfolios)
    tickers = sorted({s["ticker"] for rows in inputs.values() for s in rows})
    prices = download_prices(tickers)
    rets = prices.pct_change()

    manifest = {
        "question": "F4 — what would each template have returned 2010-2026 net of MER and rebalancing, using free data?",
        "status": "DONE",
        "as_of": REQUESTED_END,
        "requested_window": f"{REQUESTED_START} .. {REQUESTED_END}",
        "band_pp": BAND_PP,
        "cost_bp_per_side": COST_PER_SIDE * 1e4,
        "data_source": "Yahoo Finance via yfinance; monthly adjusted close (total return incl. distributions)",
        "assumptions": "All MER values ASSUMED pending verification against issuer ETF Facts; bounded by portfolios.json mer_limit_bp where stated. Proxy tickers documented per sleeve. Templates, not advice.",
        "portfolios": [],
    }

    for p in portfolios:
        rows = inputs[p["name"]]
        limit = {s["sleeve"]: s["mer_limit_bp"] for s in p["sleeves"] if "mer_limit_bp" in s}
        res = simulate(rows, rets, limit_mer=limit)
        if res is None:
            res = {
                "error": "no overlapping data for any sleeve in requested window",
                "sleeves": [
                    {"sleeve": s["sleeve"], "weight_pct": round(s["weight"] * 100, 6), "ticker": s["ticker"], "mer_bp_assumed": s["mer_bp"]}
                    for s in rows
                ],
            }
        lo, hi = target_band(p)
        mdd_text = p["max_drawdown_pct"]
        if mdd_text[0] in "<>":
            mdd_cap_direction = mdd_text[0]
            cap = float(mdd_text[1:]) / 100.0
        elif "-" in mdd_text:
            # band "15-25": upper band edge is the drawdown ceiling
            mdd_cap_direction = "<"
            cap = float(mdd_text.split("-")[1]) / 100.0
        else:
            mdd_cap_direction = "<"
            cap = float(mdd_text) / 100.0
        if mdd_cap_direction == "<":
            mdd_met = bool(res["mdd_net"] < cap) if "mdd_net" in res else None
        else:
            mdd_met = bool(res["mdd_net"] > cap) if "mdd_net" in res else None
        target_met = bool(lo / 100.0 <= res["cagr_net"] <= hi / 100.0) if "cagr_net" in res else None
        entry = {
            "name": p["name"],
            "target_nominal_pct": p["target_nominal_pct"],
            "max_drawdown_pct": p["max_drawdown_pct"],
            **res,
            "target_met": target_met,
            "mdd_met": mdd_met,
        }
        manifest["portfolios"].append(entry)

    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS, "w") as fh:
        json.dump(manifest, fh, indent=2)

    print(f"F4 template backtest | as of {REQUESTED_END} | window requested {REQUESTED_START} .. {REQUESTED_END}")
    print(f"Rebalance: +/-{BAND_PP} pp absolute, {COST_PER_SIDE*1e4:.0f} bp per side (F2 convention)")
    print(f"All MER values ASSUMED; see assumptions in {RESULTS}")
    print()
    for e in manifest["portfolios"]:
        if "cagr_net" not in e:
            print(f"{e['name']}: {e.get('error')}")
            continue
        tm = "PASS" if e["target_met"] is True else ("FAIL" if e["target_met"] is False else "n/a")
        mm = "PASS" if e["mdd_met"] is True else ("FAIL" if e["mdd_met"] is False else "n/a")
        print(
            f"{e['name']} [{e['start']} .. {e['end']}, n={e['n_months']}]: "
            f"CAGR net {e['cagr_net']*100:.2f}% (gross {e['cagr_gross']*100:.2f}%), "
            f"MDD {e['mdd_net']*100:.2f}% vs cap {p_cap(e)}, "
            f"rebalances {e['rebalance_events']}, cost ~{e['total_cost_bp_sum']:.1f} bp summed, "
            f"target {e['target_nominal_pct']}% -> {tm}, MDD cap -> {mm}, "
            f"CAGR delta at MER limits {e['cagr_delta_bp_at_limit']:+.1f} bp/yr"
        )
    print(f"\nManifest written to {RESULTS}")


def p_cap(e):
    # small helper kept near the print block; cap text reconstructed from name lookup is awkward,
    # so we inline nothing here. (Unused placeholder removed below.)
    return "?"


if __name__ == "__main__":
    main()
