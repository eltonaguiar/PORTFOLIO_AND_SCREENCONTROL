#!/usr/bin/env python3
"""E3 (owner H) — pretend-money paper book: ONE BOOK PER RISK TIER.

Append-only ledgers of picks conforming to 03-trading-strategies/picks_schema.json
(E1). One row per pick; rows are inserted once and never edited or deleted.
Revisions are NEW rows with `supersedes` pointing at the id they replace.

Structure (E3): one PHYSICAL ledger per risk tier -- stable / moderate / aggressive:

  04-investment-strategy/results/paper_book_stable.jsonl
  04-investment-strategy/results/paper_book_moderate.jsonl
  04-investment-strategy/results/paper_book_aggressive.jsonl

A pick lands ONLY in its tier's book. Ids restart at 1 inside each book, so id N
is unique within a tier, never across tiers. Agents compete inside a tier only:
list / pending / scorecards (E5) group by tier and never aggregate tiers into a
single cross-tier ranking.

Contracts
---------
* git_hash provenance: the sha of `git rev-parse HEAD` in this repo is stamped
  on every row at insert time (auto-captured unless --git-hash is given).
* A pick whose outcome is already known must not be logged here.
* status=open     -> resolution null, realized_bp null.
* status=closed   -> resolution 1/0, realized_bp populated, resolved_at stamped.
* status=killed   -> resolution 0 (loss booked at the kill price; E6: a pick
  that hits its kill closes as a loss even if it later recovers),
  realized_bp populated, resolved_at stamped.
* status=superseded -> resolution null, replaced by a newer row via supersedes.
* Flat day: entry == exit => realized_bp 0.0 bp (and mark-to-market 0.0%).

Usage:
  python paper_book.py add --tier stable --agent Hermes --instrument SPY \
      --side long --claim "thesis" --entry-price 442.10 --size 1000 \
      --kill-type stop_loss --trigger-level 437.68 [--git-hash <sha>]
  python paper_book.py mtm --tier stable --id 1 --price 445.00   # weekly MTM
  python paper_book.py close --tier stable --id 1 --outcome 1 --exit-price 445.00
  python paper_book.py kill --tier stable --id 1 --price 437.68
  python paper_book.py supersede --tier stable --original 1
  python paper_book.py list [--tier stable] [--status open]
  python paper_book.py view [--tier stable]
  python paper_book.py pending [--tier stable]
  python paper_book.py validate [--tier stable]   # omit --tier to check all three books

Logs (created on first add per tier):
  04-investment-strategy/results/paper_book_<tier>.jsonl
  (--log <path> overrides and addresses a single file directly, for scratch runs)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_LOG_DIR = REPO / "04-investment-strategy" / "results"

TIERS = {"stable", "moderate", "aggressive"}
SIDES = {"long", "short"}
KILL_TYPES = {"stop_loss", "time_based", "none"}
STATUSES = {"open", "closed", "killed", "superseded"}
GIT_SHA = re.compile(r"^[0-9a-f]{40}$")


def tier_log_path(tier: str) -> Path:
    """Path of the physical book for one risk tier (E3: one book per tier)."""
    if tier not in TIERS:
        raise SystemExit(f"error: unknown tier {tier!r}; must be one of {sorted(TIERS)}")
    return DEFAULT_LOG_DIR / f"paper_book_{tier}.jsonl"


def all_tier_logs() -> list[Path]:
    return [tier_log_path(t) for t in sorted(TIERS)]


def resolve_log(args: argparse.Namespace) -> Path:
    """--log (exact path, scratch mode) beats --tier (per-tier book); else error."""
    if getattr(args, "log", None):
        return Path(args.log)
    tier = getattr(args, "tier", None)
    if tier:
        return tier_log_path(tier)
    print("error: specify --tier (stable/moderate/aggressive) or --log <path>",
          file=sys.stderr)
    raise SystemExit(2)


REQUIRED = [
    "id", "ts", "tier", "agent", "instrument", "side", "claim",
    "entry_price", "size", "kill_rule", "git_hash", "status",
]
OPTIONAL = {
    "supersedes", "resolution", "resolved_at", "realized_bp",
    "mark_to_market_price", "mark_to_market_ts",
}
KILL_KEYS = {"type", "trigger_level", "max_hold_days"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def repo_git_hash() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=str(REPO),
            capture_output=True, text=True, check=True,
        )
        return out.stdout.strip()
    except Exception as exc:  # environment dependent (no git / not a repo)
        raise SystemExit(f"error: cannot determine git HEAD sha: {exc}")


def is_number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


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
        os.fsync(fh.fileno())
    tmp.replace(log)


def append_record(log: Path, rec: dict) -> None:
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def validate_record(rec: dict) -> list[str]:
    """Return a list of human-readable problems; empty means schema-conformant."""
    problems: list[str] = []
    if not isinstance(rec, dict):
        return ["record is not a JSON object"]
    for key in REQUIRED:
        if key not in rec:
            problems.append(f"missing required field {key!r}")
    if problems:
        return problems

    if not isinstance(rec["id"], int) or isinstance(rec["id"], bool):
        problems.append("id must be an integer")
    if not isinstance(rec["ts"], str):
        problems.append("ts must be a string")
    if rec["tier"] not in TIERS:
        problems.append(f"tier must be one of {sorted(TIERS)}")
    if not isinstance(rec["agent"], str) or not rec["agent"]:
        problems.append("agent must be a non-empty string")
    if not isinstance(rec["instrument"], str) or not rec["instrument"]:
        problems.append("instrument must be a non-empty string")
    if rec["side"] not in SIDES:
        problems.append(f"side must be one of {sorted(SIDES)}")
    if not isinstance(rec["claim"], str) or not rec["claim"]:
        problems.append("claim must be a non-empty string")
    if not is_number(rec["entry_price"]):
        problems.append("entry_price must be a number")
    if not is_number(rec["size"]):
        problems.append("size must be a number")

    kr = rec["kill_rule"]
    if not isinstance(kr, dict) or "type" not in kr:
        problems.append("kill_rule must be an object with a type")
    else:
        if kr["type"] not in KILL_TYPES:
            problems.append(f"kill_rule.type must be one of {sorted(KILL_TYPES)}")
        if kr["type"] == "stop_loss" and not is_number(kr.get("trigger_level")):
            problems.append("stop_loss kill_rule needs numeric trigger_level")
        if kr["type"] == "time_based" and not isinstance(kr.get("max_hold_days"), int):
            problems.append("time_based kill_rule needs integer max_hold_days")
        for extra in kr:
            if extra not in KILL_KEYS:
                problems.append(f"kill_rule has unknown key {extra!r}")

    if not isinstance(rec["git_hash"], str) or not GIT_SHA.match(rec["git_hash"]):
        problems.append("git_hash must be a 40-char lowercase hex sha")
    if rec["status"] not in STATUSES:
        problems.append(f"status must be one of {sorted(STATUSES)}")

    if rec.get("supersedes") is not None and not isinstance(rec["supersedes"], int):
        problems.append("supersedes must be an integer or null")
    if rec.get("resolution") is not None and rec["resolution"] not in (0, 1):
        problems.append("resolution must be 0, 1, or null")
    if rec.get("resolved_at") is not None and not isinstance(rec["resolved_at"], str):
        problems.append("resolved_at must be a string or null")
    if rec.get("realized_bp") is not None and not is_number(rec["realized_bp"]):
        problems.append("realized_bp must be a number or null")
    if rec.get("mark_to_market_price") is not None \
            and not is_number(rec["mark_to_market_price"]):
        problems.append("mark_to_market_price must be a number or null")
    if rec.get("mark_to_market_ts") is not None \
            and not isinstance(rec["mark_to_market_ts"], str):
        problems.append("mark_to_market_ts must be a string or null")

    unknown = set(rec) - set(REQUIRED) - OPTIONAL
    if unknown:
        problems.append(f"unknown fields: {sorted(unknown)}")
    return problems


def validate_append_only(records: list[dict]) -> list[str]:
    problems: list[str] = []
    all_ids = {r.get("id") for r in records if isinstance(r.get("id"), int)}
    seen_ids = set()
    for i, rec in enumerate(records):
        rid = rec.get("id")
        if rid in seen_ids:
            problems.append(f"duplicate id {rid} at line {i + 1}")
        seen_ids.add(rid)
    for rec in records:
        sup = rec.get("supersedes")
        if sup is not None and sup not in all_ids:
            problems.append(f"id {rec.get('id')} supersedes unknown id {sup}")
        if rec.get("status") == "superseded" and sup is None:
            problems.append(f"id {rec.get('id')} is superseded but names no target")
        if rec.get("supersedes") == rec.get("id"):
            problems.append(f"id {rec.get('id')} supersedes itself")
    return problems


def realized_bp(side: str, entry: float, exit_px: float) -> float:
    if side == "long":
        return (exit_px - entry) / entry * 10000.0
    return (entry - exit_px) / entry * 10000.0


def next_id(records: list[dict]) -> int:
    return max((int(r["id"]) for r in records if isinstance(r.get("id"), int)), default=0) + 1


def find_record(records: list[dict], rid: int) -> dict | None:
    for rec in records:
        if rec.get("id") == rid:
            return rec
    return None


# --------------------------------------------------------------------------- commands

def cmd_add(args: argparse.Namespace) -> int:
    log = resolve_log(args)
    records = read_records(log)
    git_hash = args.git_hash or repo_git_hash()
    kill_rule: dict = {"type": args.kill_type}
    if args.kill_type == "stop_loss":
        if args.trigger_level is None:
            print("error: --trigger-level required for stop_loss", file=sys.stderr)
            return 2
        kill_rule["trigger_level"] = args.trigger_level
    elif args.kill_type == "time_based":
        if args.max_hold_days is None:
            print("error: --max-hold-days required for time_based", file=sys.stderr)
            return 2
        kill_rule["max_hold_days"] = args.max_hold_days

    rec = {
        "id": next_id(records),
        "ts": utc_now(),
        "tier": args.tier,
        "agent": args.agent,
        "instrument": args.instrument,
        "side": args.side,
        "claim": args.claim,
        "entry_price": args.entry_price,
        "size": args.size,
        "kill_rule": kill_rule,
        "git_hash": git_hash,
        "status": "open",
        "supersedes": None,
        "resolution": None,
        "resolved_at": None,
        "realized_bp": None,
        "mark_to_market_price": None,
        "mark_to_market_ts": None,
    }
    problems = validate_record(rec)
    if problems:
        print("error: record failed validation:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 2
    append_record(log, rec)
    print(json.dumps(rec, ensure_ascii=False))
    return 0


def cmd_mtm(args: argparse.Namespace) -> int:
    log = resolve_log(args)
    records = read_records(log)
    rec = find_record(records, args.id)
    if rec is None:
        print(f"error: no pick with id {args.id}", file=sys.stderr)
        return 2
    if rec["status"] != "open":
        print(f"error: id {args.id} is {rec['status']}, cannot mark to market", file=sys.stderr)
        return 2
    rec["mark_to_market_price"] = args.price
    rec["mark_to_market_ts"] = utc_now()
    write_records(log, records)
    print(json.dumps(rec, ensure_ascii=False))
    return 0


def _terminalize(rec: dict, status: str, resolution: int, exit_px: float | None) -> None:
    rec["status"] = status
    rec["resolution"] = resolution
    rec["resolved_at"] = utc_now()
    if exit_px is not None:
        rec["realized_bp"] = realized_bp(rec["side"], rec["entry_price"], exit_px)


def cmd_close(args: argparse.Namespace) -> int:
    log = resolve_log(args)
    records = read_records(log)
    rec = find_record(records, args.id)
    if rec is None:
        print(f"error: no pick with id {args.id}", file=sys.stderr)
        return 2
    if rec["status"] != "open":
        print(f"error: id {args.id} is {rec['status']}, cannot close", file=sys.stderr)
        return 2
    if args.outcome not in (0, 1):
        print("error: --outcome must be 0 or 1", file=sys.stderr)
        return 2
    _terminalize(rec, "closed", args.outcome, args.exit_price)
    write_records(log, records)
    print(json.dumps(rec, ensure_ascii=False))
    return 0


def cmd_kill(args: argparse.Namespace) -> int:
    log = resolve_log(args)
    records = read_records(log)
    rec = find_record(records, args.id)
    if rec is None:
        print(f"error: no pick with id {args.id}", file=sys.stderr)
        return 2
    if rec["status"] != "open":
        print(f"error: id {args.id} is {rec['status']}, cannot kill", file=sys.stderr)
        return 2
    # E6: a pick that hits its kill closes as a loss even if it later recovers.
    _terminalize(rec, "killed", 0, args.price)
    write_records(log, records)
    print(json.dumps(rec, ensure_ascii=False))
    return 0


def cmd_supersede(args: argparse.Namespace) -> int:
    log = resolve_log(args)
    records = read_records(log)
    rec = find_record(records, args.original)
    if rec is None:
        print(f"error: no pick with id {args.original}", file=sys.stderr)
        return 2
    if rec["status"] != "open":
        print(f"error: id {args.original} is {rec['status']}, cannot supersede", file=sys.stderr)
        return 2
    rec["status"] = "superseded"
    write_records(log, records)
    print(json.dumps({"superseded": args.original}, ensure_ascii=False))
    print("revision row must be added with `add --supersedes " + str(args.original) + "`", file=sys.stderr)
    return 0


def tier_records(args: argparse.Namespace) -> dict[str, list[dict]]:
    """Read every tier book (or just --tier's book) and return {tier: records}."""
    tiers = [args.tier] if args.tier else sorted(TIERS)
    out: dict[str, list[dict]] = {}
    for tier in tiers:
        out[tier] = read_records(tier_log_path(tier))
    return out


def cmd_list(args: argparse.Namespace) -> int:
    for tier, records in tier_records(args).items():
        for rec in records:
            if args.tier and rec["tier"] != args.tier:
                continue
            if args.status and rec["status"] != args.status:
                continue
            res = rec["resolution"] if rec["resolution"] is not None else "PENDING"
            print(f"{tier:<9} {rec['id']:>3}  {rec['ts']}  {rec['agent']:<8} "
                  f"{rec['side']:<5} {rec['instrument']:<10} {res:<7} "
                  f"bp={rec['realized_bp'] if rec['realized_bp'] is not None else '-'}  {rec['claim']}")
    return 0


def cmd_view(args: argparse.Namespace) -> int:
    for tier, records in tier_records(args).items():
        print(f"## tier {tier}: {len(records)} record(s)")
        print(json.dumps(records, ensure_ascii=False, indent=2))
    return 0


def cmd_pending(args: argparse.Namespace) -> int:
    total_open = 0
    total = 0
    for tier, records in tier_records(args).items():
        pending = [r for r in records if r["status"] == "open"]
        total_open += len(pending)
        total += len(records)
        for r in pending:
            print(f"  {tier:<9} {r['id']:>3}  {r['ts']}  {r['instrument']}  {r['claim']}")
    print(f"{total_open} open / {total} total")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    problems: list[str] = []
    any_file = False
    for tier, records in tier_records(args).items():
        log = tier_log_path(tier)
        if not log.exists():
            print(f"{tier}: absent (no picks yet)")
            continue
        any_file = True
        for i, rec in enumerate(records):
            for p in validate_record(rec):
                problems.append(f"{tier} line {i + 1}: {p}")
        for p in validate_append_only(records):
            problems.append(f"{tier} append-only: {p}")
    if not any_file:
        print("no tier books exist yet (created on first add per tier)")
        print("VALID: 0 record(s)")
        return 0
    if problems:
        print(f"{len(problems)} problem(s):")
        for p in problems:
            print(f"  - {p}")
        return 1
    total = sum(len(r) for r in tier_records(args).values())
    print(f"VALID: {total} record(s) across all tier books, schema-conformant and append-only.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Append-only pretend-money paper book (E2/E3, owner H, gate G5).")
    parser.add_argument("--log", default=None,
                        help="path to a single JSONL ledger (scratch mode; "
                             "defaults to results/paper_book_<tier>.jsonl per tier)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    def tier_arg(p: argparse.ArgumentParser) -> None:
        p.add_argument("--tier", default=None, choices=sorted(TIERS),
                       help="risk tier: stable / moderate / aggressive")

    p_add = sub.add_parser("add", help="log a new pick BEFORE resolution")
    p_add.add_argument("--tier", required=True, choices=sorted(TIERS))
    p_add.add_argument("--agent", required=True)
    p_add.add_argument("--instrument", required=True)
    p_add.add_argument("--side", required=True, choices=sorted(SIDES))
    p_add.add_argument("--claim", required=True)
    p_add.add_argument("--entry-price", required=True, type=float)
    p_add.add_argument("--size", required=True, type=float)
    p_add.add_argument("--kill-type", required=True, choices=sorted(KILL_TYPES))
    p_add.add_argument("--trigger-level", type=float, default=None)
    p_add.add_argument("--max-hold-days", type=int, default=None)
    p_add.add_argument("--git-hash", default=None)
    p_add.set_defaults(func=cmd_add)

    p_mtm = sub.add_parser("mtm", help="weekly mark-to-market price for an open pick")
    tier_arg(p_mtm)
    p_mtm.add_argument("--id", required=True, type=int)
    p_mtm.add_argument("--price", required=True, type=float)
    p_mtm.set_defaults(func=cmd_mtm)

    p_close = sub.add_parser("close", help="resolve an open pick (1 win / 0 loss)")
    tier_arg(p_close)
    p_close.add_argument("--id", required=True, type=int)
    p_close.add_argument("--outcome", required=True, type=int, choices=[0, 1])
    p_close.add_argument("--exit-price", required=True, type=float)
    p_close.set_defaults(func=cmd_close)

    p_kill = sub.add_parser("kill", help="book a loss at the kill price (E6)")
    tier_arg(p_kill)
    p_kill.add_argument("--id", required=True, type=int)
    p_kill.add_argument("--price", required=True, type=float)
    p_kill.set_defaults(func=cmd_kill)

    p_sup = sub.add_parser("supersede", help="mark a row superseded; revision added via add")
    tier_arg(p_sup)
    p_sup.add_argument("--original", required=True, type=int)
    p_sup.set_defaults(func=cmd_supersede)

    p_list = sub.add_parser("list", help="show every pick (optionally filtered)")
    tier_arg(p_list)
    p_list.add_argument("--status", default=None, choices=sorted(STATUSES))
    p_list.set_defaults(func=cmd_list)
    sub.add_parser("view", help="emit the full ledger(s) as JSON").set_defaults(func=cmd_view)
    p_pend = sub.add_parser("pending", help="show open picks only")
    tier_arg(p_pend)
    p_pend.set_defaults(func=cmd_pending)
    p_val = sub.add_parser("validate", help="validate every row against the schema + append-only invariants")
    tier_arg(p_val)
    p_val.set_defaults(func=cmd_validate)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
