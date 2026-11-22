"""Event-driven bar replay with lagged fills and conservative intrabar resolution.

The engine is deliberately small and deliberately pessimistic. Every choice below
is the choice that makes a strategy look *worse*, because the failure mode of this
whole domain is a backtest that looks good for the wrong reason.

Execution convention
--------------------
  signal on close of bar t   ->  entry fill at open of bar t+1
  entry price                = open * (1 + per_side)   for longs
                             = open * (1 - per_side)   for shorts
  exit at TP (bar high >= tp)->  fill at tp * (1 - per_side)   for longs
  exit at SL (bar low <= sl) ->  fill at sl * (1 - per_side)   for longs
  both touched in one bar    ->  SL is assumed to fill first (conservative)
  time stop after max_bars   ->  fill at that bar's close, cost applied

A trade is a dict; the exit reason is one of TP / SL / TIME / EOD.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .costs import CostModel, DEFAULT_COSTS


@dataclass
class Trade:
    symbol: str
    direction: str            # LONG | SHORT
    entry_ts: str
    entry_price: float
    tp: float
    sl: float
    size: float = 1.0         # fraction of equity at risk-normalised size
    exit_ts: Optional[str] = None
    exit_price: Optional[float] = None
    exit_reason: Optional[str] = None
    gross_ret: Optional[float] = None   # price move, no costs
    net_ret: Optional[float] = None     # after both legs of friction
    bars_held: Optional[int] = None
    r_multiple: Optional[float] = None

    def as_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "direction": self.direction,
            "entry_ts": self.entry_ts,
            "entry_price": round(self.entry_price, 8),
            "tp": round(self.tp, 8),
            "sl": round(self.sl, 8),
            "exit_ts": self.exit_ts,
            "exit_price": None if self.exit_price is None else round(self.exit_price, 8),
            "exit_reason": self.exit_reason,
            "gross_ret": None if self.gross_ret is None else round(self.gross_ret, 6),
            "net_ret": None if self.net_ret is None else round(self.net_ret, 6),
            "bars_held": self.bars_held,
            "r_multiple": None if self.r_multiple is None else round(self.r_multiple, 4),
        }


@dataclass
class BacktestResult:
    strategy: str
    symbol: str
    timeframe: str
    execution_convention: str
    costs: dict
    trades: List[dict] = field(default_factory=list)
    equity_curve: List[float] = field(default_factory=list)
    equity_ts: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


def run_from_signals(
    df: pd.DataFrame,
    signals: pd.Series,
    strategy: str,
    symbol: str,
    *,
    tp_atr: float = 2.0,
    sl_atr: float = 1.0,
    max_bars: int = 24,
    atr_window: int = 14,
    costs: CostModel = DEFAULT_COSTS,
    timeframe: str = "1h",
    allow_short: bool = True,
) -> BacktestResult:
    """Replay bars. `signals` is an int Series (1 long, -1 short, 0 flat) indexed
    exactly like `df`, and MUST already be shifted so that value at index i is
    known at the close of bar i (the engine fills at i+1)."""
    if not df.index.equals(signals.index):
        raise ValueError("signals index must equal df index")

    res = BacktestResult(
        strategy=strategy,
        symbol=symbol,
        timeframe=timeframe,
        execution_convention="lag1_next_open | conservative_intrabar (SL first) | taker+slippage both legs",
        costs=costs.as_dict(),
    )

    o = df["open"].to_numpy(float)
    h = df["high"].to_numpy(float)
    l = df["low"].to_numpy(float)
    c = df["close"].to_numpy(float)
    sig = signals.to_numpy(int)

    tr = pd.Series(h - l, index=df.index)
    pc = df["close"].shift(1)
    tr = pd.concat([tr, (df["high"] - pc).abs(), (df["low"] - pc).abs()], axis=1).max(axis=1)
    atr = tr.rolling(atr_window).mean().to_numpy(float)

    n = len(df)
    idx = df.index
    per_side = costs.per_side

    equity = 1.0
    res.equity_curve.append(equity)
    res.equity_ts.append(str(idx[0]))

    i = 0
    while i < n - 1:
        s = sig[i]
        if s == 0 or not np.isfinite(atr[i]) or atr[i] <= 0:
            i += 1
            continue
        if s < 0 and not allow_short:
            i += 1
            continue

        direction = "LONG" if s > 0 else "SHORT"
        entry_bar = i + 1
        raw_entry = o[entry_bar]
        if not np.isfinite(raw_entry) or raw_entry <= 0:
            i += 1
            continue

        entry = raw_entry * (1 + per_side) if s > 0 else raw_entry * (1 - per_side)
        a = atr[i]
        if s > 0:
            tp = entry + tp_atr * a
            sl = entry - sl_atr * a
        else:
            tp = entry - tp_atr * a
            sl = entry + sl_atr * a

        trade = Trade(
            symbol=symbol,
            direction=direction,
            entry_ts=str(idx[entry_bar]),
            entry_price=entry,
            tp=tp,
            sl=sl,
        )

        exit_price = None
        exit_reason = None
        j = entry_bar
        last = min(n - 1, entry_bar + max_bars)
        while j <= last:
            if s > 0:
                hit_sl = l[j] <= sl
                hit_tp = h[j] >= tp
            else:
                hit_sl = h[j] >= sl
                hit_tp = l[j] <= tp

            if hit_sl:  # conservative: stop wins the tie
                exit_price = sl * (1 - per_side) if s > 0 else sl * (1 + per_side)
                exit_reason = "SL"
                break
            if hit_tp:
                exit_price = tp * (1 - per_side) if s > 0 else tp * (1 + per_side)
                exit_reason = "TP"
                break
            j += 1

        if exit_price is None:
            j = last
            exit_price = c[j] * (1 - per_side) if s > 0 else c[j] * (1 + per_side)
            exit_reason = "TIME" if last < n - 1 else "EOD"

        gross = (exit_price - entry) / entry if s > 0 else (entry - exit_price) / entry
        risk_frac = (sl_atr * a) / entry
        trade.exit_ts = str(idx[j])
        trade.exit_price = exit_price
        trade.exit_reason = exit_reason
        trade.gross_ret = gross
        trade.net_ret = gross  # friction already inside the fill prices
        trade.bars_held = j - entry_bar
        trade.r_multiple = (gross / risk_frac) if risk_frac > 0 else 0.0

        # Risk-normalised sizing: each trade risks 1% of equity at the stop.
        pos = (0.01 / risk_frac) if risk_frac > 0 else 1.0
        pos = min(pos, 1.0)  # never lever above 1x notional
        equity *= (1.0 + trade.net_ret * pos)
        res.trades.append(trade.as_dict())
        res.equity_curve.append(equity)
        res.equity_ts.append(str(idx[j]))
        i = j + 1  # no pyramiding, no overlapping trades per symbol

    if not res.trades:
        res.notes.append("no trades generated")
    # Time actually in the market — needed to compare against buy-and-hold fairly.
    bars_in = sum(t["bars_held"] or 0 for t in res.trades)
    res_exposure = bars_in / max(n - 1, 1)
    res.notes.append(f"exposure_frac={res_exposure:.4f}")
    res.exposure_frac = res_exposure  # type: ignore[attr-defined]
    return res


def buy_and_hold(df: pd.DataFrame, costs: CostModel = DEFAULT_COSTS) -> dict:
    """The benchmark every strategy must beat after costs, same window."""
    first = float(df["open"].iloc[0]) * (1 + costs.per_side)
    last = float(df["close"].iloc[-1]) * (1 - costs.per_side)
    ret = last / first - 1.0
    eq = df["close"] / df["close"].iloc[0]
    peak = eq.cummax()
    dd = float((eq / peak - 1.0).min())
    return {
        "symbol": str(df.attrs.get("symbol", "")),
        "total_return": round(ret, 6),
        "max_drawdown": round(dd, 6),
        "bars": int(len(df)),
        "start": str(df.index[0]),
        "end": str(df.index[-1]),
    }
