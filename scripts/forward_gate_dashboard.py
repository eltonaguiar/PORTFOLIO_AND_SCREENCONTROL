"""Forward-gate dashboard for the audit3 evidence ledger.

Reads https://findtorontoevents.ca/audit3/audit3_ledger.json live and prints,
per pod: status, forward rows (n/min_n), and the binding gate clause with the
reasons the pod is not eligible to promote. Writes a machine-readable snapshot
to 03-trading-strategies/results/forward_gate_<UTC>.json.

No secrets, no credentials, no writes to the live surface — read-only fetch.
"""

from __future__ import annotations

import json
import urllib.request
from datetime import datetime, timezone

from pathlib import Path

LEDGER_URL = "https://findtorontoevents.ca/audit3/audit3_ledger.json"
REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = str(REPO_ROOT / "03-trading-strategies" / "results")


_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Hermes pasc-progress cron; +https://github.com/eltonaguiar/PORTFOLIO_AND_SCREENCONTROL"


def fetch_ledger(url: str, timeout: int = 60) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        if r.status != 200:
            raise RuntimeError(f"ledger fetch failed HTTP {r.status}")
        return json.loads(r.read().decode("utf-8"))


def gate_clause(fg: dict) -> str:
    return fg.get("rule", "")


def pod_rows(fg: dict) -> list[dict]:
    out = []
    for name, p in (fg.get("pods") or {}).items():
        out.append(
            {
                "pod": name,
                "status": p.get("status"),
                "since": p.get("since"),
                "hypothesis_id": p.get("hypothesis_id"),
                "n_forward": p.get("n_forward"),
                "min_n": p.get("min_n"),
                "eligible": p.get("eligible"),
                "blocked_reasons": p.get("reasons") or [],
                "binding_gate_clause": gate_clause(fg),
                "gate": {
                    k: p.get(k)
                    for k in (
                        "net_mean_pct",
                        "net_pf",
                        "pf_ci_lb",
                        "ir",
                        "intrabar_first_touch_all",
                        "benchmark_coverage",
                        "excess_vs_benchmark_pct",
                    )
                    if k in p
                },
                "promotion_blocked_by_status": p.get("promotion_blocked_by_status"),
            }
        )
    out.sort(key=lambda r: r["pod"])
    return out


def main() -> None:
    ledger = fetch_ledger(LEDGER_URL)
    fg = ledger.get("forward_gate") or {}
    rows = pod_rows(fg)
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%MZ")

    report = {
        "generated_at": now.isoformat().replace("+00:00", "Z"),
        "source_url": LEDGER_URL,
        "source_generated_at": ledger.get("source_generated_at"),
        "ledger_generated_at": ledger.get("generated_at"),
        "fingerprint": fg.get("fingerprint"),
        "enforced": fg.get("enforced"),
        "n_forward_rows_in_ledger": fg.get("n_rows"),
        "binding_gate_clause": gate_clause(fg),
        "n_pods": len(rows),
        "n_eligible": sum(1 for r in rows if r["eligible"]),
        "pods_by_status": {s: sum(1 for r in rows if r["status"] == s) for s in sorted({r["status"] for r in rows})},
        "pods": rows,
    }

    print("forward-gate dashboard (live audit3 ledger)")
    print(f"  source: {LEDGER_URL}")
    print(f"  ledger generated_at: {report['ledger_generated_at']} | source_generated_at: {report['source_generated_at']}")
    print(f"  rule: {report['binding_gate_clause']}")
    print(f"  pods: {report['n_pods']} | eligible: {report['n_eligible']} | by status: {report['pods_by_status']}")
    print(f"  {'pod':30} {'status':16} {'rows':7} {'eligible':9} {'blocked by'}")
    for r in rows:
        print(f"  {r['pod']:30} {r['status']:16} {r['n_forward']}/{r['min_n']:<5} {str(r['eligible']):9} {'; '.join(r['blocked_reasons'])}")

    out_path = f"{OUT_DIR}/forward_gate_{stamp}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"  wrote {out_path}")


if __name__ == "__main__":
    main()
