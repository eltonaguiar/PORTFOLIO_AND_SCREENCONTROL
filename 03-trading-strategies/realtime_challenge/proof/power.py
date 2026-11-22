#!/usr/bin/env python3
"""Required sample size per strategy — the number that replaces "n >= 100".

`n >= 100` has been this project's forward-promotion gate. `BRACKET_P7.md` showed it cannot work:
a bracket needs 0.02-0.17pp of win-rate edge, which needs 1.2-28 million trades to verify. This
module computes the honest number for whatever was actually measured, so the gate can be stated
per strategy instead of as one arbitrary constant.

Method
------
To detect a per-trade mean `mu` against zero at significance `alpha` with power `1-beta`, on a
per-trade return series with standard deviation `sigma`:

    n = (z_{1-alpha/2} + z_{1-beta})^2 * (sigma / mu)^2

At alpha=0.05 and power=0.80 the constant is (1.95996 + 0.84162)^2 = 7.849. Costs are already
inside the per-trade returns, so the required n is the number of NET trades needed.

Where sigma is not stored, it is recovered from a reported 95% CI:
    sigma ~= (ci_hi - ci_lo) / (2 * 1.95996) * sqrt(n)

  python -m realtime_challenge.proof.power              # all available series
"""

from __future__ import annotations

import glob
import json
import math
import sys
from pathlib import Path

import numpy as np

RESULTS = Path(__file__).resolve().parent.parent / "results"
LEDGER = Path(__file__).resolve().parent.parent.parent / "ledger"
Z = (1.959964 + 0.841621) ** 2


def required_n(mu: float, sigma: float, alpha_z: float = 1.959964,
               beta_z: float = 0.841621) -> int | None:
    """Trades needed to detect `mu` at 80% power against zero."""
    if mu is None or sigma is None or mu == 0 or sigma <= 0:
        return None
    if mu < 0:
        mu = abs(mu)                       # same power to detect a loss
    n = (alpha_z + beta_z) ** 2 * (sigma / mu) ** 2
    return int(math.ceil(n)) if n < 1e12 else None


def from_series(name: str, xs) -> dict:
    x = np.asarray([v for v in xs if v is not None and math.isfinite(v)], dtype=float)
    if len(x) < 5:
        return {"name": name, "n": len(x), "note": "too few"}
    mu, sd = float(x.mean()), float(x.std(ddof=1))
    req = required_n(mu, sd)
    return {
        "name": name, "n": len(x),
        "mean_bps": round(mu * 1e4, 2), "sd_bps": round(sd * 1e4, 2),
        "required_n": req,
        "have_fraction": round(len(x) / req, 6) if req else None,
        "status": ("MEASURABLE NOW" if req and len(x) >= req else
                   "far below required n"),
    }


def live_books():
    out = []
    allr = []
    for f in sorted(glob.glob(str(LEDGER / "live*.jsonl"))):
        rets = []
        for line in Path(f).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if e.get("event") == "CLOSE" and isinstance(e.get("ret_pct"), (int, float)):
                rets.append(e["ret_pct"] / 100.0)
        if rets:
            out.append(from_series(Path(f).stem, rets))
            allr += rets
    if allr:
        out.append(from_series("ALL LIVE BOOKS (pooled)", allr))
    return out


def flagged_ledger_series():
    """A negative control: the flagged pairs are KILL/WEAK, so their required n to detect the
    observed (negative) effect is also reported — it shows how badly n=27 underpowers even a
    large effect."""
    p = RESULTS / "fx_census_latest.json"
    if not p.exists():
        return []
    d = json.loads(p.read_text(encoding="utf-8"))
    out = []
    for r in d.get("rows", []):
        if r.get("cost_bps_rt") != 5:
            continue
        lo, hi = (r.get("ci") or [None, None])
        n, mu = r.get("n"), r.get("mean_bps")
        if not all(isinstance(v, (int, float)) for v in (lo, hi, n, mu)) or n < 5:
            continue
        sigma_bps = (hi - lo) / (2 * 1.959964) * math.sqrt(n)
        out.append({
            "name": f"{r['strategy']}/{r['symbol']}",
            "n": n, "mean_bps": mu, "sd_bps": round(sigma_bps, 2),
            "required_n": required_n(mu / 1e4, sigma_bps / 1e4),
        })
    return out


def main() -> int:
    print("=" * 78)
    print("REQUIRED SAMPLE SIZE — what replaces 'n >= 100'")
    print("=" * 78)

    live = live_books()
    print("\nLIVE BOOKS (per-trade net returns, costs already inside)")
    print(f"  {'series':32s} {'n':>4s} {'mean bps':>9s} {'sd bps':>9s} {'required n':>12s}")
    for r in live:
        if "required_n" not in r:
            continue
        req = f"{r['required_n']:,}" if r["required_n"] else "unreachable"
        print(f"  {r['name']:32s} {r['n']:4d} {r['mean_bps']:>9.2f} {r['sd_bps']:>9.2f} "
              f"{req:>12s}")

    pooled = next((r for r in live if r["name"].startswith("ALL")), None)
    if pooled and pooled.get("required_n"):
        print(f"\n  Pooled live sample: n={pooled['n']}, needed {pooled['required_n']:,} "
              f"-> we have {pooled['have_fraction']*100:.4f}% of the required sample")

    fx = flagged_ledger_series()
    if fx:
        print("\nFX CENSUS (sigma recovered from each cell's reported 95% CI)")
        print(f"  {'cell':34s} {'n':>4s} {'mean bps':>9s} {'sd bps':>9s} {'required n':>12s}")
        for r in sorted(fx, key=lambda x: (x["required_n"] or 10**12))[:10]:
            req = f"{r['required_n']:,}" if r["required_n"] else "unreachable"
            print(f"  {r['name']:34s} {r['n']:4d} {r['mean_bps']:>9.2f} {r['sd_bps']:>9.2f} "
                  f"{req:>12s}")

    # the policy statement
    out = {
        "constant_alpha05_power80": round(Z, 3),
        "formula": "n = (z_a + z_b)^2 * (sigma/mu)^2",
        "live": live,
        "fx": fx,
        "policy": {
            "old_gate": "n >= 100 closed forward trades",
            "why_it_fails": ("a bracket needs 0.02-0.17pp of win-rate edge (BRACKET_P7.md); "
                             "verifying that needs 1.2-28M trades, so 100 cannot distinguish "
                             "an edge from zero"),
            "new_gate": ("promotion requires n >= required_n(mu, sigma) computed from that "
                         "strategy's own measured per-trade dispersion, reported alongside "
                         "the estimate — never a fixed constant"),
        },
    }
    (RESULTS).mkdir(parents=True, exist_ok=True)
    (RESULTS / "power_analysis.json").write_text(json.dumps(out, indent=1, default=str),
                                                 encoding="utf-8")
    print(f"\nwrote results/power_analysis.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
