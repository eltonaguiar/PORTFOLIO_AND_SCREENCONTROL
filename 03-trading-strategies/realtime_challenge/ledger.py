"""Append-only ledger for the live paper-trading rounds.

Two files, one truth:
  ledger.jsonl : every event ever emitted (OPEN, CLOSE, SKIP, HEARTBEAT). Append-only.
  state.json   : materialised view — open positions + cash. Rebuilt from the JSONL,
                 so a corrupted state file can never invent a trade that did not happen.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

STATE_DIR = Path(__file__).resolve().parent / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Ledger:
    def __init__(self, run_id: str, starting_cash: float = 10_000.0):
        self.run_id = run_id
        self.path = STATE_DIR / f"{run_id}.jsonl"
        self.state_path = STATE_DIR / f"{run_id}_state.json"
        self.starting_cash = starting_cash
        self.events: List[dict] = []
        self._load()

    # ------------------------------------------------------------------ io
    def _load(self) -> None:
        if not self.path.exists():
            return
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    self.events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    def append(self, event: dict) -> dict:
        event = {"ts_utc": _ts(), "run_id": self.run_id, **event}
        self.events.append(event)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, default=str) + "\n")
            f.flush()
            os.fsync(f.fileno())
        return event

    def save_state(self, state: dict) -> None:
        tmp = self.state_path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(state, f, indent=1, default=str)
        tmp.replace(self.state_path)

    # --------------------------------------------------------------- views
    @property
    def open_positions(self) -> Dict[str, dict]:
        pos: Dict[str, dict] = {}
        for e in self.events:
            if e.get("event") == "OPEN":
                pos[e["symbol"]] = e
            elif e.get("event") == "CLOSE":
                pos.pop(e.get("symbol"), None)
        return pos

    @property
    def closed(self) -> List[dict]:
        return [e for e in self.events if e.get("event") == "CLOSE"]

    @property
    def skips(self) -> List[dict]:
        return [e for e in self.events if e.get("event") == "SKIP"]

    def equity(self, marks: Optional[Dict[str, float]] = None) -> float:
        """Cash + marked-to-market open positions. `marks` maps symbol -> last price."""
        marks = marks or {}
        cash = self.starting_cash
        for c in self.closed:
            cash += c.get("pnl", 0.0)
        for sym, p in self.open_positions.items():
            qty = p["qty"]
            px = marks.get(sym, p["entry_price"])
            if p["direction"] == "LONG":
                cash += qty * (px - p["entry_price"]) * p.get("size_frac", 1.0)
            else:
                cash += qty * (p["entry_price"] - px) * p.get("size_frac", 1.0)
        return cash

    def summary(self) -> dict:
        closed = self.closed
        pnls = [c["pnl"] for c in closed]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]
        gross_win = sum(wins)
        gross_loss = -sum(losses)
        return {
            "run_id": self.run_id,
            "starting_cash": self.starting_cash,
            "equity": round(self.equity(), 2),
            "n_closed": len(closed),
            "n_open": len(self.open_positions),
            "n_skips": len(self.skips),
            "win_rate": None if not closed else round(len(wins) / len(closed), 4),
            "profit_factor": None if gross_loss == 0 else round(gross_win / gross_loss, 4),
            "total_pnl": round(sum(pnls), 2),
            "gross_win": round(gross_win, 2),
            "gross_loss": round(gross_loss, 2),
            "fees_paid": round(sum(c.get("fees", 0.0) for c in closed), 2),
            "exit_mix": _counts([c.get("exit_reason", "?") for c in closed]),
            "skip_reasons": _counts([s.get("reason", "?") for s in self.skips]),
        }


def _counts(items: List[str]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for i in items:
        out[i] = out.get(i, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))
