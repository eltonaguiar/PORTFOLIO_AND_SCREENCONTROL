"""Pre-registered candidate strategies.

RULES FOR THIS FILE
  * One frozen parameter set per hypothesis. No sweeps, no per-symbol tuning.
  * Each builder is a PURE function of a price DataFrame: signal[i] may only use
    bars <= i. The engine fills at i+1, so there is no look-ahead by construction.
  * 6 hypotheses are registered here. That number is the multiple-testing input
    (`TRIAL_COUNT`) and it is not allowed to grow silently: adding a strategy
    creates a new trial and must raise the deflation bar for every other one.
  * Families already killed by alpha_engine/negative_knowledge_registry.py are not
    re-entered: no Keltner x altcoin, no unproven SHORT-only systems, no R:R > 2.5,
    and no entries stamped in the blocked UTC hours {2, 8, 13, 20}.

Each builder returns an int Series: 1 = long, -1 = short, 0 = flat.
"""

from __future__ import annotations

from typing import Callable, Dict

import numpy as np
import pandas as pd

TRIAL_COUNT = 6

BLOCKED_UTC_HOURS = (2, 8, 13, 20)
MAX_RR = 2.5


# ---------------------------------------------------------------- indicators
def ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()


def rsi(s: pd.Series, n: int = 14) -> pd.Series:
    d = s.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    rs = up / dn.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    pc = df["close"].shift(1)
    tr = pd.concat(
        [df["high"] - df["low"], (df["high"] - pc).abs(), (df["low"] - pc).abs()], axis=1
    ).max(axis=1)
    return tr.rolling(n).mean()


def _block_hours(sig: pd.Series) -> pd.Series:
    """Apply the desk's documented dead-hour denylist (UTC)."""
    hours = sig.index.hour
    mask = np.isin(hours, BLOCKED_UTC_HOURS)
    sig = sig.copy()
    sig[mask] = 0
    return sig


# ---------------------------------------------------------------- hypotheses
def h_r1_trend_pullback(df: pd.DataFrame) -> pd.Series:
    """H-R1: trend-following pullback. EMA50 > EMA200 (uptrend), price dips to
    EMA20 while RSI(14) < 45, enter on the reclaim. Long only."""
    c = df["close"]
    u, d = ema(c, 50), ema(c, 200)
    e20 = ema(c, 20)
    r = rsi(c, 14)
    uptrend = u > d
    dip = (c <= e20 * 1.002) & (r < 45)
    reclaim = c > e20
    sig = (uptrend.fillna(False) & dip.shift(1).fillna(False).astype(bool) & reclaim.fillna(False)).astype(int)
    return _block_hours(sig)


def h_r2_donchian_breakout(df: pd.DataFrame) -> pd.Series:
    """H-R2: classic time-series momentum. Break the 20-bar high -> long; break the
    20-bar low -> short. Both directions, because the short leg is the hypothesis."""
    hh = df["high"].rolling(20).max().shift(1)
    ll = df["low"].rolling(20).min().shift(1)
    sig = pd.Series(0, index=df.index, dtype=int)
    sig[df["close"] > hh] = 1
    sig[df["close"] < ll] = -1
    return _block_hours(sig)


def h_r3_bollinger_meanrev(df: pd.DataFrame) -> pd.Series:
    """H-R3: mean reversion into the lower Bollinger band, but only with the
    long-term trend (close > SMA200). Long only."""
    c = df["close"]
    sma20 = c.rolling(20).mean()
    sd20 = c.rolling(20).std(ddof=0)
    lower = sma20 - 2 * sd20
    trend = c > c.rolling(200).mean()
    touch = (df["low"] <= lower) & (c > lower)
    sig = (trend.fillna(False) & touch.shift(1).fillna(False).astype(bool)).astype(int)
    return _block_hours(sig)


def h_r4_vol_compression(df: pd.DataFrame) -> pd.Series:
    """H-R4: volatility squeeze breakout. ATR(14) in the bottom quintile of the last
    168 bars, then price clears the prior 12-bar high. Long only."""
    a = atr(df, 14)
    pct = a.rolling(168).rank(pct=True)
    squeezed = pct < 0.20
    hh = df["high"].rolling(12).max().shift(1)
    sig = (squeezed.shift(1).fillna(False).astype(bool) & (df["close"] > hh).fillna(False)).astype(int)
    return _block_hours(sig)


def h_r5_weekend_effect(df: pd.DataFrame) -> pd.Series:
    """H-R5: calendar anomaly. Crypto trades 24/7, so the equity 'weekend effect'
    is testable cleanly: enter at Friday 20:00 UTC, exit at Sunday 20:00 UTC.
    Signal fires once, on the Friday bar."""
    idx = df.index
    fri = (idx.dayofweek == 4) & (idx.hour == 20)
    sig = pd.Series(0, index=idx, dtype=int)
    sig[fri] = 1
    return sig


def h_r6_rsi2_pullback(df: pd.DataFrame) -> pd.Series:
    """H-R6: Connors-style RSI(2) oversold bounce in an uptrend (close > SMA200).
    This is the family the desk already trades on equities; here it is ported to
    24/7 crypto with no parameter change."""
    c = df["close"]
    r2 = rsi(c, 2)
    trend = c > c.rolling(200).mean()
    sig = (trend.fillna(False) & (r2 < 10).fillna(False)).astype(int)
    return _block_hours(sig)


REGISTRY: Dict[str, Dict] = {
    "H-R1_trend_pullback": {
        "fn": h_r1_trend_pullback, "tp_atr": 2.0, "sl_atr": 1.0, "max_bars": 48,
        "allow_short": False, "family": "trend_pullback",
        "hypothesis": "In an uptrend, a shallow EMA20 pullback with RSI<45 resumes upward.",
    },
    "H-R2_donchian_breakout": {
        "fn": h_r2_donchian_breakout, "tp_atr": 2.0, "sl_atr": 1.0, "max_bars": 48,
        "allow_short": True, "family": "tsmom_breakout",
        "hypothesis": "20-bar TSMOM breakouts continue in both directions over days.",
    },
    "H-R3_bollinger_meanrev": {
        "fn": h_r3_bollinger_meanrev, "tp_atr": 1.5, "sl_atr": 1.0, "max_bars": 24,
        "allow_short": False, "family": "mean_reversion_band",
        "hypothesis": "Lower-band touches inside an uptrend revert to the mean.",
    },
    "H-R4_vol_compression": {
        "fn": h_r4_vol_compression, "tp_atr": 2.0, "sl_atr": 1.0, "max_bars": 36,
        "allow_short": False, "family": "vol_squeeze_breakout",
        "hypothesis": "Compressed ATR precedes an expansion that pays for the breakout.",
    },
    "H-R5_weekend_effect": {
        "fn": h_r5_weekend_effect, "tp_atr": 3.0, "sl_atr": 2.0, "max_bars": 48,
        "allow_short": False, "family": "calendar_anomaly",
        "hypothesis": "Friday 20:00 UTC -> Sunday 20:00 UTC holds a positive drift in crypto.",
    },
    "H-R6_rsi2_pullback": {
        "fn": h_r6_rsi2_pullback, "tp_atr": 1.5, "sl_atr": 1.0, "max_bars": 24,
        "allow_short": False, "family": "mean_reversion_rsi",
        "hypothesis": "RSI(2)<10 inside an uptrend mean-reverts within a day.",
    },
}

# Guard: TP:SL must stay inside the desk's anti-predictive R:R block.
for _name, _cfg in REGISTRY.items():
    _rr = _cfg["tp_atr"] / _cfg["sl_atr"]
    assert _rr <= MAX_RR, f"{_name} R:R {_rr} exceeds blocked threshold {MAX_RR}"


def builders() -> Dict[str, Callable[[pd.DataFrame], pd.Series]]:
    return {k: v["fn"] for k, v in REGISTRY.items()}
