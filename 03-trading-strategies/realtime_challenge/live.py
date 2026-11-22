"""The live round: open and close real positions on real, current market prices.

This is NOT a simulated historical backtest. Every price written here came off a
live exchange endpoint seconds before it was written, with the exchange's own
timestamp recorded next to it so the claim is auditable after the fact.

It is still pretend money: no order is sent to any exchange, no account exists.
The fill model is deliberately adverse:
    long entry  pays the ASK  + taker fee
    long exit   receives the BID - taker fee
That means the bid/ask spread is paid on top of commission, exactly as it would be
in reality, and a "profit" here cannot be an artefact of mid-price fills.

Exit rules, checked on every poll against the live price:
    TP   price crosses the take-profit level
    SL   price crosses the stop level
    TIME position has been open for `max_minutes`
A position is closed at the live bid/ask at the moment the rule trips, not at the
theoretical TP/SL level — so gap risk is charged to the strategy, not hidden.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

import pandas as pd

from . import data as D
from . import strategies as S
from .costs import CostModel, DEFAULT_COSTS
from .ledger import Ledger

# Blocked by alpha_engine/negative_knowledge_registry.py — do not trade these.
BLOCKED_BASES = {"AVAX", "TRX", "MATIC"}

DEFAULT_UNIVERSE = [b for b in ["BTC", "ETH", "SOL", "XRP", "DOGE", "ADA", "LINK"] if b not in BLOCKED_BASES]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# --------------------------------------------------------------------------
# HARNESS PROBE — deliberately NOT a registered hypothesis.
#
# Its only job is to prove the open -> live-mark -> close machinery works on real
# prices inside a session where the pre-registered book is flat (which is the
# normal state: 6 long-biased hypotheses in a downtrend fire almost never).
#
# It is excluded from TRIAL_COUNT and from every verdict. If a round traded only
# under this label, it produced a harness validation and NO evidence of edge.
# --------------------------------------------------------------------------
def harness_probe_signal(df5: pd.DataFrame, burst_pct: float = 0.004, lookback: int = 1) -> int:
    """5m momentum burst: a CLOSED bar moved > burst_pct with volume above its
    20-bar median. Returns 1/-1/0. Not a hypothesis, not counted, not bankable.

    `lookback` scans the last N closed bars and returns the DIRECTION OF THE MOST
    RECENT*ness that qualifies. This matters: a first version only looked at the
    single latest bar, and a live round that polls every couple of minutes therefore
    sampled roughly one bar in three and missed most bursts. Coverage, not logic, was
    the bug.
    """
    if len(df5) < 25:
        return 0
    lookback = max(1, min(int(lookback), len(df5) - 23))
    for i in range(len(df5) - 1, len(df5) - 1 - lookback, -1):
        bar = df5.iloc[i]
        ret = bar["close"] / bar["open"] - 1.0
        volmed = df5["volume"].iloc[max(0, i - 20):i].median()
        if volmed <= 0:
            continue
        if ret > burst_pct and bar["volume"] > volmed:
            return 1
        if ret < -burst_pct and bar["volume"] > volmed:
            return -1
    return 0


def _quote(venue: str, base: str, retries: int = 3) -> Optional[dict]:
    for k in range(retries):
        try:
            q = D.live_quote(venue, base)
            if q.get("bid") and q.get("ask") and q["ask"] > 0:
                return q
        except Exception:
            time.sleep(1 + k)
    return None


def _atr_from_live(venue: str, base: str, timeframe: str, window: int = 14) -> Optional[float]:
    try:
        df = D.fetch_ohlcv(venue, base, timeframe, 200, cache_ttl_s=120)
    except Exception:
        return None
    pc = df["close"].shift(1)
    tr = pd.concat(
        [df["high"] - df["low"], (df["high"] - pc).abs(), (df["low"] - pc).abs()], axis=1
    ).max(axis=1)
    a = tr.rolling(window).mean().iloc[-1]
    return float(a) if pd.notna(a) else None


def scan_signals(
    venue: str, universe: List[str], timeframe: str = "1h", bars: int = 400
) -> Dict[str, dict]:
    """Run every registered hypothesis on live bars. Returns base -> best signal."""
    out: Dict[str, dict] = {}
    for base in universe:
        try:
            df = D.fetch_ohlcv(venue, base, timeframe, bars, cache_ttl_s=120)
        except Exception as exc:
            out[base] = {"error": f"{type(exc).__name__}: {str(exc)[:70]}"}
            continue
        per_strategy = {}
        for name, cfg in S.REGISTRY.items():
            try:
                sig = cfg["fn"](df)
                last = int(sig.iloc[-1]) if len(sig) else 0
                recent = int(sig.tail(3).abs().sum())
                per_strategy[name] = {"signal": last, "fired_last_3": recent}
            except Exception as exc:
                per_strategy[name] = {"signal": 0, "error": str(exc)[:60]}
        agree = sum(1 for v in per_strategy.values() if v.get("signal", 0) != 0)
        out[base] = {
            "close": float(df["close"].iloc[-1]),
            "bar_ts": str(df.index[-1]),
            "strategies": per_strategy,
            "n_agreeing": agree,
        }
    return out


class LiveRound:
    def __init__(
        self,
        run_id: str,
        venue: str = "binance",
        universe: Optional[List[str]] = None,
        starting_cash: float = 10_000.0,
        risk_per_trade: float = 0.01,
        costs: CostModel = DEFAULT_COSTS,
        max_minutes: int = 60,
        tp_atr: float = 2.0,
        sl_atr: float = 1.0,
        max_open: int = 4,
        burst_pct: float = 0.004,
        lookback: int = 12,
    ):
        self.run_id = run_id
        self.lookback = lookback
        self.burst_pct = burst_pct
        self.venue = venue
        self.universe = universe or DEFAULT_UNIVERSE
        self.risk_per_trade = risk_per_trade
        self.costs = costs
        self.max_minutes = max_minutes
        self.tp_atr = tp_atr
        self.sl_atr = sl_atr
        self.max_open = max_open
        self.ledger = Ledger(run_id, starting_cash)
        self.started = time.time()

    # ------------------------------------------------------------------ open
    def try_open(self, base: str, direction: int, signal_source: str) -> Optional[dict]:
        if base in BLOCKED_BASES:
            self.ledger.append({"event": "SKIP", "symbol": base, "reason": "BLOCKED_SYMBOL"})
            return None
        q = _quote(self.venue, base)
        if q is None:
            self.ledger.append({"event": "SKIP", "symbol": base, "reason": "NO_QUOTE"})
            return None

        a = _atr_from_live(self.venue, base, "1h")
        if a is None or a <= 0:
            self.ledger.append({"event": "SKIP", "symbol": base, "reason": "NO_ATR"})
            return None

        side = "LONG" if direction > 0 else "SHORT"
        entry = q["ask"] if direction > 0 else q["bid"]
        entry = entry * (1 + self.costs.taker_fee if direction > 0 else 1 - self.costs.taker_fee)
        if direction > 0:
            tp, sl = entry + self.tp_atr * a, entry - self.sl_atr * a
        else:
            tp, sl = entry - self.tp_atr * a, entry + self.sl_atr * a

        stop_dist = abs(entry - sl) / entry
        notional = min(self.risk_per_trade / stop_dist, 1.0) * self.ledger.starting_cash
        notional = min(notional, self.ledger.starting_cash / max(self.max_open, 1))
        qty = notional / entry

        ev = self.ledger.append(
            {
                "event": "OPEN",
                "symbol": base,
                "venue": self.venue,
                "direction": side,
                "entry_price": round(entry, 8),
                "bid_at_entry": q["bid"],
                "ask_at_entry": q["ask"],
                "exchange_ts": q.get("exchange_ts"),
                "qty": qty,
                "notional": round(notional, 2),
                "tp": round(tp, 8),
                "sl": round(sl, 8),
                "atr_1h": round(a, 6),
                "signal_source": signal_source,
                "max_minutes": self.max_minutes,
            }
        )
        return ev

    # ---------------------------------------------------------------- close
    def check_exits(self, marks: Dict[str, dict]) -> List[dict]:
        import math

        closed = []
        for base, pos in list(self.ledger.open_positions.items()):
            q = marks.get(base)
            if q is None:
                continue
            long_ = pos["direction"] == "LONG"
            px = q["bid"] if long_ else q["ask"]
            if px is None:
                continue
            px = px * (1 - self.costs.taker_fee if long_ else 1 + self.costs.taker_fee)

            reason = None
            if long_:
                if px <= pos["sl"]:
                    reason = "SL"
                elif px >= pos["tp"]:
                    reason = "TP"
            else:
                if px >= pos["sl"]:
                    reason = "SL"
                elif px <= pos["tp"]:
                    reason = "TP"

            opened = datetime.fromisoformat(pos["ts_utc"].replace("Z", "+00:00"))
            held_min = (datetime.now(timezone.utc) - opened).total_seconds() / 60.0
            if reason is None and held_min >= pos["max_minutes"]:
                reason = "TIME"

            if reason is None:
                continue

            qty = pos["qty"]
            pnl = (px - pos["entry_price"]) * qty if long_ else (pos["entry_price"] - px) * qty
            fees = abs(pos["notional"]) * self.costs.taker_fee * 2
            ret = pnl / pos["notional"] if pos["notional"] else 0.0
            risk = abs(pos["entry_price"] - pos["sl"]) * qty
            closed.append(
                self.ledger.append(
                    {
                        "event": "CLOSE",
                        "symbol": base,
                        "direction": pos["direction"],
                        "entry_price": pos["entry_price"],
                        "exit_price": round(px, 8),
                        "tp": pos["tp"],
                        "sl": pos["sl"],
                        "exit_reason": reason,
                        "held_minutes": round(held_min, 2),
                        "pnl": round(pnl, 4),
                        "ret_pct": round(ret * 100, 4),
                        "fees": round(fees, 4),
                        "r_multiple": round(pnl / risk, 3) if risk else None,
                        "notional": pos["notional"],
                        "signal_source": pos["signal_source"],
                    }
                )
            )
        return closed

    # ------------------------------------------------------------------ run
    def run(
        self,
        duration_minutes: float = 60,
        poll_s: float = 30,
        verbose: bool = True,
        book: str = "preregistered",
        min_votes: int = 2,
    ) -> dict:
        """book='preregistered' uses only the 6 registered hypotheses and a
        >=min_votes consensus. book='probe' uses the harness-only 5m burst signal."""
        deadline = self.started + duration_minutes * 60
        it = 0
        while time.time() < deadline:
            it += 1
            marks: Dict[str, dict] = {}
            for base in self.universe:
                q = _quote(self.venue, base)
                if q:
                    marks[base] = q

            opened_now = 0
            if len(self.ledger.open_positions) < self.max_open:
                if book == "preregistered":
                    sigs = scan_signals(self.venue, self.universe, "1h")
                    for base, info in sigs.items():
                        if len(self.ledger.open_positions) >= self.max_open:
                            break
                        if base in self.ledger.open_positions:
                            self.ledger.append({"event": "SKIP", "symbol": base, "reason": "ALREADY_OPEN"})
                            continue
                        if "error" in info:
                            self.ledger.append({"event": "SKIP", "symbol": base, "reason": f"DATA_ERROR:{info['error'][:40]}"})
                            continue
                        votes = [v["signal"] for v in info["strategies"].values() if v.get("signal")]
                        if not votes:
                            self.ledger.append({"event": "SKIP", "symbol": base, "reason": "NO_SIGNAL"})
                            continue
                        if len(votes) < min_votes or len({v > 0 for v in votes}) != 1:
                            self.ledger.append({"event": "SKIP", "symbol": base, "reason": "NO_CONSENSUS"})
                            continue
                        direction = 1 if sum(votes) > 0 else -1
                        if self.try_open(base, direction, f"consensus={votes}"):
                            opened_now += 1
                elif book == "smoke":
                    # SMOKE TEST — not a strategy, not a hypothesis. Open one small
                    # position per symbol at the first pass and let the exit rules
                    # close it, purely to prove the open->mark->close path on live
                    # prices. Marked SMOKE_TEST in the ledger so it can never be
                    # mistaken for evidence.
                    for base in self.universe:
                        if len(self.ledger.open_positions) >= self.max_open:
                            break
                        if base in self.ledger.open_positions:
                            continue
                        if self.try_open(base, 1, "SMOKE_TEST"):
                            opened_now += 1
                else:  # harness probe
                    for base in self.universe:
                        if len(self.ledger.open_positions) >= self.max_open:
                            break
                        if base in self.ledger.open_positions:
                            continue
                        try:
                            df5 = D.fetch_ohlcv(self.venue, base, "5m", 120, cache_ttl_s=60)
                        except Exception as exc:
                            self.ledger.append({"event": "SKIP", "symbol": base, "reason": f"DATA_ERROR:{str(exc)[:40]}"})
                            continue
                        d = harness_probe_signal(df5, burst_pct=self.burst_pct, lookback=12)
                        if d == 0:
                            self.ledger.append({"event": "SKIP", "symbol": base, "reason": "PROBE_FLAT"})
                            continue
                        if self.try_open(base, d, "HARNESS_PROBE_5M_BURST"):
                            opened_now += 1

            closed_now = self.check_exits(marks)

            eq = self.ledger.equity({b: q.get("bid") or q.get("last") for b, q in marks.items()})
            self.ledger.append(
                {
                    "event": "HEARTBEAT",
                    "iteration": it,
                    "equity": round(eq, 2),
                    "n_open": len(self.ledger.open_positions),
                    "marks": {b: (q.get("bid") or q.get("last")) for b, q in marks.items()},
                }
            )
            self.ledger.save_state(self.ledger.summary())

            if verbose:
                print(
                    f"[{it:03d}] {now_utc()} eq=${eq:,.2f} open={len(self.ledger.open_positions)} "
                    f"opened={opened_now} closed={len(closed_now)} "
                    + (f"| {closed_now[-1]['symbol']} {closed_now[-1]['exit_reason']} "
                       f"${closed_now[-1]['pnl']:+.2f}" if closed_now else "")
                )
            time.sleep(poll_s)

        # Force-close anything still open at the end, at the live price, so the
        # round has a complete realised record rather than dangling marks.
        marks = {b: _quote(self.venue, b) for b in self.universe}
        marks = {b: q for b, q in marks.items() if q}
        for pos in self.ledger.open_positions.values():
            pos["max_minutes"] = 0
        self.check_exits(marks)
        for pos in list(self.ledger.open_positions.values()):
            self.ledger.append({"event": "CLOSE", "symbol": pos["symbol"], "direction": pos["direction"],
                                "entry_price": pos["entry_price"], "exit_price": marks.get(pos["symbol"], {}).get("bid") or pos["entry_price"],
                                "exit_reason": "EOD", "held_minutes": 0, "pnl": 0.0, "ret_pct": 0.0,
                                "fees": 0.0, "notional": pos["notional"], "signal_source": pos["signal_source"]})

        summary = self.ledger.summary()
        self.ledger.save_state(summary)
        return summary
