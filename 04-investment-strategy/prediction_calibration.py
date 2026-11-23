#!/usr/bin/env python3
"""D2 (owner H) — prediction-calibration harness: log claims BEFORE they resolve.

Append-only ledger of predictions for the D2/D3 calibration sleeve
(venue: Polymarket, selected in D1). Each record is the 5-tuple

    (ts, claim, our_prob, market_prob, resolution)

with `resolution` null until the claim resolves, then 0/1.

Append-only contract:
  * predictions are inserted once and never edited or deleted;
  * resolution is filled in later, stamped with resolved_at — the only
    permitted mutation on an existing record, and it can happen once;
  * a claim whose resolution is already known must not be logged here
    (that is a D3 scoring input, not a D2 input).

Log (created on first add): 04-investment-strategy/results/prediction_calibration.jsonl

Usage:
  python prediction_calibration.py add "claim text" --our 0.6 --market 0.55 [--venue Polymarket]
  python prediction_calibration.py resolve <id> 1|0
  python prediction_calibration.py list
  python prediction_calibration.py view
  python prediction_calibration.py pending
"""

from __future__ import annotations

import argparse
import json
import math
import random
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_LOG = REPO / "results" / "prediction_calibration.jsonl"

VALID_OUTCOMES = {
    "1": 1, "0": 0,
    "true": 1, "false": 0,
    "yes": 1, "no": 0,
    "y": 1, "n": 0,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_records(log: Path) -> list[dict]:
    if not log.exists():
        return []
    records = []
    with log.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def write_records(log: Path, records: list[dict]) -> None:
    log.parent.mkdir(parents=True, exist_ok=True)
    tmp = log.with_suffix(log.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        fh.flush()
        import os
        os.fsync(fh.fileno())
    tmp.replace(log)


def append_record(log: Path, rec: dict) -> None:
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        fh.flush()
        import os
        os.fsync(fh.fileno())


def prob(value: str) -> float:
    try:
        p = float(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"probability must be a number, got {value!r}")
    if not 0.0 <= p <= 1.0:
        raise argparse.ArgumentTypeError(f"probability must be in [0, 1], got {p}")
    return p


def cmd_add(args: argparse.Namespace) -> int:
    log = Path(args.log)
    records = read_records(log)
    next_id = max((int(r["id"]) for r in records if str(r.get("id", "")).isdigit()), default=0) + 1
    rec = {
        "id": next_id,
        "ts": utc_now(),
        "claim": args.claim.strip(),
        "our_prob": args.our,
        "market_prob": args.market,
        "market_venue": args.venue,
        "resolution": None,
        "resolved_at": None,
    }
    if not rec["claim"]:
        print("error: claim must not be empty", file=sys.stderr)
        return 2
    append_record(log, rec)
    print(json.dumps(rec, ensure_ascii=False))
    return 0


def cmd_resolve(args: argparse.Namespace) -> int:
    log = Path(args.log)
    records = read_records(log)
    if not records:
        print("error: log is empty", file=sys.stderr)
        return 2
    target = None
    for rec in records:
        if str(rec.get("id")) == args.id:
            target = rec
            break
    if target is None:
        print(f"error: no prediction with id {args.id}", file=sys.stderr)
        return 2
    if target["resolution"] is not None:
        print(f"error: id {args.id} already resolved at {target['resolved_at']} — refusing to overwrite", file=sys.stderr)
        return 2
    outcome = VALID_OUTCOMES.get(args.outcome.strip().lower())
    if outcome is None:
        print(f"error: outcome must be one of {sorted(VALID_OUTCOMES)}, got {args.outcome!r}", file=sys.stderr)
        return 2
    target["resolution"] = outcome
    target["resolved_at"] = utc_now()
    write_records(log, records)
    print(json.dumps(target, ensure_ascii=False))
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    for rec in read_records(Path(args.log)):
        res = rec["resolution"] if rec["resolution"] is not None else "PENDING"
        print(f"{rec['id']:>3}  {rec['ts']}  p_ours={rec['our_prob']}  p_market={rec['market_prob']}  resolution={res}  {rec['claim']}")
    return 0


def cmd_view(args: argparse.Namespace) -> int:
    out = []
    for rec in read_records(Path(args.log)):
        out.append({
            "id": rec["id"],
            "ts": rec["ts"],
            "claim": rec["claim"],
            "our_prob": rec["our_prob"],
            "market_prob": rec["market_prob"],
            "market_venue": rec["market_venue"],
            "resolution": rec["resolution"],
            "resolved_at": rec["resolved_at"],
        })
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    """D3: Brier + log-loss vs market for resolved records.

    Refuses to produce a number when there are too few resolved records
    (default < 5) — an empty ledger is INSUFFICIENT_DATA, not a score.
    """
    log = Path(args.log)
    records = read_records(log)
    resolved = [r for r in records if r.get("resolution") is not None]
    pending = [r for r in records if r.get("resolution") is None]

    try:
        git_hash = subprocess.check_output(
            ["git", "-C", str(REPO), "rev-parse", "HEAD"], stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        git_hash = "UNKNOWN"

    result = {
        "item": "D3 H — score with Brier and log-loss vs market; require ΔBrier > 0 with CI",
        "status": None,
        "run_at": utc_now(),
        "git_hash": git_hash,
        "log": str(log),
        "records": len(records),
        "resolved": len(resolved),
        "pending": len(pending),
        "min_resolved": args.min_resolved,
        "bootstrap_resamples": args.bootstrap,
    }

    def brier(ps: list[float], ys: list[float]) -> float:
        return sum((p - y) ** 2 for p, y in zip(ps, ys)) / len(ps)

    def logloss(ps: list[float], ys: list[float], eps: float = 1e-12) -> float:
        total = 0.0
        for p, y in zip(ps, ys):
            q = min(max(p, eps), 1.0 - eps)
            total += math.log(q) if y else math.log(1.0 - q)
        return -total / len(ys)

    if len(resolved) < args.min_resolved:
        result["status"] = "INSUFFICIENT_DATA"
        result["message"] = (
            f"D3 cannot score: {len(resolved)} resolved records (need {args.min_resolved}). "
            "The D2 ledger is empty and D4 panel claims (AI-owned) are not generated, so there is "
            "nothing to score. No Brier/log-loss number produced — not UNVERIFIED, not fabricated."
        )
    else:
        ours = [float(r["our_prob"]) for r in resolved]
        market = [float(r["market_prob"]) for r in resolved]
        ys = [float(r["resolution"]) for r in resolved]

        brier_ours = brier(ours, ys)
        brier_market = brier(market, ys)
        delta = brier_market - brier_ours  # > 0 means we beat the market
        ll_ours = logloss(ours, ys)
        ll_market = logloss(market, ys)

        # Bootstrap 95% CI on ΔBrier, fixed seed for reproducibility.
        rng = random.Random(20261123)
        n = len(resolved)
        boots = []
        for _ in range(args.bootstrap):
            idx = [rng.randrange(n) for _ in range(n)]
            boots.append(brier([market[i] for i in idx], [ys[i] for i in idx])
                         - brier([ours[i] for i in idx], [ys[i] for i in idx]))
        boots.sort()
        lo = boots[int(0.025 * len(boots))]
        hi = boots[int(0.975 * len(boots))]

        if delta > 0 and lo > 0:
            verdict = "PASS: our probabilities beat the market (ΔBrier > 0, 95% CI excludes 0)"
        elif delta > 0:
            verdict = "INCONCLUSIVE: ΔBrier > 0 but 95% CI includes 0"
        else:
            verdict = "FAIL: ΔBrier <= 0"

        result.update({
            "status": "COMPUTED",
            "brier_ours": brier_ours,
            "brier_market": brier_market,
            "delta_brier": delta,
            "delta_brier_ci95": [lo, hi],
            "logloss_ours": ll_ours,
            "logloss_market": ll_market,
            "verdict": verdict,
        })

    artifact = Path(__file__).resolve().parent / "results" / "d3_score_latest.json"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    out = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    artifact.write_text(out, encoding="utf-8")
    print(out)
    return 0 if result["status"] == "COMPUTED" else 3


def cmd_pending(args: argparse.Namespace) -> int:
    records = read_records(Path(args.log))
    pending = [r for r in records if r["resolution"] is None]
    print(f"{len(pending)} pending / {len(records)} total")
    for r in pending:
        print(f"  {r['id']:>3}  {r['ts']}  {r['claim']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Append-only prediction-calibration ledger (D2, owner H).")
    parser.add_argument("--log", default=str(DEFAULT_LOG), help="path to the JSONL log (default: results/prediction_calibration.jsonl)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add", help="log a new prediction BEFORE resolution")
    p_add.add_argument("claim", help="the claim being predicted")
    p_add.add_argument("--our", required=True, type=prob, help="our probability (0-1)")
    p_add.add_argument("--market", required=True, type=prob, help="market probability (0-1)")
    p_add.add_argument("--venue", default="Polymarket", help="market venue (default: Polymarket)")
    p_add.set_defaults(func=cmd_add)

    p_res = sub.add_parser("resolve", help="fill in resolution for a known id (once, never overwritten)")
    p_res.add_argument("id", help="prediction id")
    p_res.add_argument("outcome", help="0/1 (true/false, yes/no)")
    p_res.set_defaults(func=cmd_resolve)

    sub.add_parser("list", help="show every record").set_defaults(func=cmd_list)
    sub.add_parser("view", help="emit the full ledger as JSON").set_defaults(func=cmd_view)
    p_score = sub.add_parser("score", help="Brier and log-loss vs market for resolved records")
    p_score.add_argument("--log", default=str(DEFAULT_LOG), help="path to the JSONL log (default: results/prediction_calibration.jsonl)")
    p_score.add_argument("--min-resolved", type=int, default=5, help="minimum resolved records required to score (default 5)")
    p_score.add_argument("--bootstrap", type=int, default=2000, help="bootstrap resamples for the delta-Brier 95 pct CI (default 2000)")
    p_score.set_defaults(func=cmd_score)

    sub.add_parser("pending", help="show unresolved predictions only").set_defaults(func=cmd_pending)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
