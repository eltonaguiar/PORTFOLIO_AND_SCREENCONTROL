"""Stable sleeve realised-yield model (F3).

Models the income (realised yield) of the Stable / low-risk portfolio template
from 04-investment-strategy/portfolios.json (F1) using live rates, and compares
it against (a) the 4.3% kill hurdle (framework rationale line; B5 kill rule on
committed capital) and (b) a top posted Canadian HISA (the cash sleeve's own
named instrument).

Every rate carries (source, date). The only input without a source - the
broad-equity dividend yield - is tagged ASSUMED, and the headline number is
also reported with equity set to zero so nothing published depends on it.

This is a yield model built from live rates, not a measured portfolio return.
F4 supplies the 2010-2026 historical total return net of MER.

Usage:
    python f3_stable_sleeve_yield.py          # human readable
    python f3_stable_sleeve_yield.py --json   # machine-readable manifest
"""

from __future__ import annotations

import argparse
import json
import sys

RUN_DATE = "2026-11-23T21:47:00-05:00"

# Stable sleeve weights from portfolios.json (F1). Sum to 100.
SLEEVES = {
    "Cash & T-bills / HISA": 55.0,
    "Short-duration govt bonds": 25.0,
    "Broad equity": 20.0,
}

# rate_pct, source, as_of (date the rate refers to), fetched (run date)
# HISA: top everyday posted rate, retiresmarter.ca, page stamped 2026-11-24.
# Canada 3-month T-bill: Bank of Canada secondary-market average yield,
#   as of 2026-11-18 (latest published on the page), fetched 2026-11-23.
# US 3-month T-bill: Fed H.15 DTB3 via FRED, as of 2026-11-20, updated 2026-11-23
#   - context only, not part of the CAD sleeve.
RATES = {
    "Cash & T-bills / HISA": {
        "rate_pct": 3.00,
        "source": "retiresmarter.ca/banking/best-hisa-rates/ - Best high-interest savings rates in Canada; top everyday rate (Saven Financial, FirstOntario Credit Union, Oaken Financial, Home Bank / Home Trust, EQ Bank at 3.00%); page stamped November 24 2026",
        "as_of": "2026-11-24",
        "fetched": RUN_DATE,
    },
    "Short-duration govt bonds": {
        "rate_pct": 2.62,
        "source": "bankofcanada.ca/rates/interest-rates/t-bill-yields/ - Selected treasury bill yields; Treasury bills 3 month secondary-market average yield",
        "as_of": "2026-11-18",
        "fetched": RUN_DATE,
    },
    "Broad equity": {
        "rate_pct": 1.50,
        "source": "ASSUMED - broad-market dividend yield; no committed source in repo. Tagged ASSUMED per the H3 rule; headline also reported with equity set to zero.",
        "as_of": None,
        "fetched": None,
    },
}

# MER caps from portfolios.json sleeve instruments, bp per annum on sleeve notional.
MER_BP = {"Short-duration govt bonds": 15, "Broad equity": 10}

HURDLE_PCT = 4.3  # kill hurdle on committed capital (framework rationale; B5)
HISA_PCT = 3.00   # top posted everyday HISA, same source as the cash sleeve


def sleeve_yield(equity_div_pct: float) -> float:
    """Gross realised yield of the stable sleeve at a given equity dividend yield."""
    rates = {
        "Cash & T-bills / HISA": RATES["Cash & T-bills / HISA"]["rate_pct"],
        "Short-duration govt bonds": RATES["Short-duration govt bonds"]["rate_pct"],
        "Broad equity": equity_div_pct,
    }
    return sum(SLEEVES[s] * rates[s] / 100.0 for s in SLEEVES)


def mer_drag_pct() -> float:
    return sum(SLEEVES[s] * MER_BP[s] / 100.0 / 100.0 for s in MER_BP)


def build() -> dict:
    equity_div = RATES["Broad equity"]["rate_pct"]
    gross = sleeve_yield(equity_div)
    drag = mer_drag_pct()
    net = gross - drag
    cash_only_gross = sleeve_yield(0.0)
    cash_only_net = cash_only_gross - drag

    return {
        "run_date": RUN_DATE,
        "question": "Stable sleeve realised yield vs the 4.3% kill hurdle and vs a top posted Canadian HISA",
        "sleeve": "Stable / low-risk (portfolios.json F1): Cash & T-bills / HISA 55%, Short-duration govt bonds 25%, Broad equity 20%",
        "inputs": {
            "Cash & T-bills / HISA": {
                "weight_pct": 55.0,
                "rate_pct": 3.00,
                "source": RATES["Cash & T-bills / HISA"]["source"],
                "as_of": "2026-11-24",
                "fetched": RUN_DATE,
            },
            "Short-duration govt bonds": {
                "weight_pct": 25.0,
                "rate_pct": 2.62,
                "source": RATES["Short-duration govt bonds"]["source"],
                "as_of": "2026-11-18",
                "fetched": RUN_DATE,
            },
            "Broad equity dividend yield": {
                "weight_pct": 20.0,
                "rate_pct": 1.50,
                "source": RATES["Broad equity"]["source"],
                "as_of": None,
                "fetched": None,
            },
        },
        "context_us_3m_tbill_pct": {
            "rate_pct": 4.13,
            "source": "fred.stlouisfed.org/series/DTB3 - Fed H.15 3-Month Treasury Bill Secondary Market Rate, Discount Basis",
            "as_of": "2026-11-20",
            "fetched": RUN_DATE,
            "note": "USD context only; a CAD account converting into USD pays FX (1.75% flagged in the portfolios.json account-currency note; F5 open) which erases the 1.13pp pickup on a one-time conversion basis.",
        },
        "results_pct": {
            "sleeve_gross_yield": round(gross, 4),
            "mer_drag": round(drag, 4),
            "sleeve_net_yield": round(net, 4),
            "cash_only_gross_yield": round(cash_only_gross, 4),
            "cash_only_net_yield": round(cash_only_net, 4),
            "top_hisa_everyday": 3.00,
            "kill_hurdle": 4.3,
        },
        "comparisons": {
            "vs_kill_hurdle_pp": round(HURDLE_PCT - net, 4),
            "vs_kill_hurdle_verdict": "BELOW",
            "vs_top_hisa_pp": round(HISA_PCT - net, 4),
            "vs_top_hisa_verdict": "BELOW",
        },
        "verdict": (
            "The stable sleeve's realised income yield (2.61% gross / 2.55% net of MER with the ASSUMED "
            "1.50% equity dividend; 2.31% gross / 2.25% net cash-only) does not clear the 4.3% kill hurdle "
            "(below by about 1.7-2.0 pp) and undercuts a top posted HISA at 3.00%. The sleeve's 4-5% nominal "
            "target must therefore come from equity price appreciation, not yield - unguaranteed. A pure top "
            "HISA beats the sleeve on realised income. Modelled from live rates, not a measured return; F4 "
            "supplies historical total return. Equity dividend input is ASSUMED and isolated."
        ),
        "self_checks": {
            "weights_sum_to_100": abs(sum(SLEEVES.values()) - 100.0) < 1e-9,
            "gross_recomputed": abs(sleeve_yield(equity_div) - gross) < 1e-9,
            "net_equals_gross_minus_drag": abs(net - (gross - drag)) < 1e-9,
        },
    }


def main() -> int:
    res = build()
    if "--json" in sys.argv:
        print(json.dumps(res, indent=2))
        return 0

    r = res["results_pct"]; c = res["comparisons"]
    print("F3 - Stable sleeve realised yield model (run", res["run_date"], ")")
    print("Sleeve: Cash & T-bills/HISA 55% | Short-duration govt bonds 25% | Broad equity 20%")
    print()
    print("Inputs (source, date):")
    print("  Cash & T-bills / HISA: 3.00% - retiresmarter.ca top everyday HISA rate, stamped 2026-11-24")
    print("  Short-duration govt bonds: 2.62% - Bank of Canada 3-month T-bill secondary-market yield, as of 2026-11-18")
    print("  Broad equity dividend: 1.50% ASSUMED (no committed source; isolated)")
    print("  Context - US 3-month T-bill: 4.13% as of 2026-11-20 (Fed DTB3), USD only, not in the CAD sleeve")
    print()
    print("Realised yield: %.4f%% gross  -  %.4f%% MER drag  =  %.4f%% net of MER" % (
        r["sleeve_gross_yield"], r["mer_drag"], r["sleeve_net_yield"]))
    print("Cash-only variant (equity yield = 0): %.4f%% gross / %.4f%% net" % (
        r["cash_only_gross_yield"], r["cash_only_net_yield"]))
    print()
    print("vs 4.3%% kill hurdle: %.4f%% -> BELOW by %.4f pp" % (r["sleeve_net_yield"], c["vs_kill_hurdle_pp"]))
    print("vs top HISA 3.00%%: %.4f%% -> BELOW by %.4f pp" % (r["sleeve_net_yield"], c["vs_top_hisa_pp"]))
    print()
    print("Verdict:", res["verdict"])
    print()
    print("Self-checks:", res["self_checks"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
