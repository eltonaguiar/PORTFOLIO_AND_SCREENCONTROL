"""Market data: real ccxt OHLCV, paginated and cached on disk.

No API keys are required for any of this — these are public market-data endpoints.
A cached CSV is the reproducibility contract: a run that reused a cache is offline
reproducible, and the cache path is recorded in the run manifest.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

CACHE_DIR = Path(__file__).resolve().parent / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Venue presets. Coinbase quotes USD, the rest quote USDT; both are dollar proxies.
VENUES = {
    "coinbase": {"quote": "USD", "max_limit": 300},
    "binance": {"quote": "USDT", "max_limit": 1000},
    "kraken": {"quote": "USD", "max_limit": 720},
    "bybit": {"quote": "USDT", "max_limit": 1000},
    "okx": {"quote": "USDT", "max_limit": 300},
}


def _exchange(venue: str):
    import ccxt

    if venue not in VENUES:
        raise ValueError(f"unknown venue {venue!r}; known: {sorted(VENUES)}")
    ex = getattr(ccxt, venue)({"enableRateLimit": True, "timeout": 20000})
    ex.load_markets()
    return ex


def symbol(venue: str, base: str) -> str:
    """BTC -> 'BTC/USD' on coinbase/kraken, 'BTC/USDT' elsewhere."""
    return f"{base}/{VENUES[venue]['quote']}"


def fetch_ohlcv(
    venue: str,
    base: str,
    timeframe: str = "1h",
    limit: int = 1500,
    use_cache: bool = True,
    cache_ttl_s: int = 300,
) -> pd.DataFrame:
    """Fetch the most recent `limit` bars, paginating as needed.

    Returns a DataFrame indexed by UTC timestamp with columns
    open/high/low/close/volume. Bars are forward-filled-free: raw exchange rows.
    """
    sym = symbol(venue, base)
    fname = CACHE_DIR / f"{venue}_{base}_{timeframe}_{limit}.csv"

    if use_cache and fname.exists():
        age = time.time() - fname.stat().st_mtime
        if age < cache_ttl_s:
            df = pd.read_csv(fname, parse_dates=["ts"])
            return df.set_index("ts")

    ex = _exchange(venue)
    if not ex.has.get("fetchOHLCV"):
        raise RuntimeError(f"{venue} has no fetchOHLCV")

    page = min(limit, VENUES[venue]["max_limit"])
    tf_ms = ex.parse_timeframe(timeframe) * 1000
    now_ms = ex.milliseconds()

    # Page FORWARD from a computed start. Paging backwards with `since` is a
    # classic ccxt bug: `since` is a start time, so passing a time before the
    # oldest bar just re-returns the same window.
    since = now_ms - int(limit * tf_ms) - tf_ms
    rows: List[list] = []
    guard = 0
    while since < now_ms and guard < 200:
        guard += 1
        batch = ex.fetch_ohlcv(sym, timeframe, since=since, limit=page)
        if not batch:
            break
        rows.extend(batch)
        last_ms = batch[-1][0]
        if last_ms <= since:
            break
        since = last_ms + tf_ms
        if len(batch) < page // 2:
            break

    # De-duplicate and keep the newest `limit` bars.
    seen = {}
    for r in rows:
        seen[r[0]] = r
    rows = [seen[k] for k in sorted(seen)][-limit:]

    if not rows:
        raise RuntimeError(f"no OHLCV returned for {sym} on {venue}")

    df = pd.DataFrame(rows, columns=["ms", "open", "high", "low", "close", "volume"])
    df = df.drop_duplicates(subset="ms").sort_values("ms")
    df["ts"] = pd.to_datetime(df["ms"], unit="ms", utc=True)
    df = df.set_index("ts")[["open", "high", "low", "close", "volume"]]
    df = df[~df.index.duplicated(keep="last")]

    out = df.reset_index()
    out.to_csv(fname, index=False)
    return df


def fetch_panel(
    venue: str,
    bases: List[str],
    timeframe: str = "1h",
    limit: int = 1500,
    use_cache: bool = True,
) -> Dict[str, pd.DataFrame]:
    """Fetch several symbols and align them onto a common (inner-joined) index."""
    raw = {}
    for b in bases:
        try:
            raw[b] = fetch_ohlcv(venue, b, timeframe, limit, use_cache)
        except Exception as exc:  # a delisted symbol must not kill the run
            print(f"  [data] skip {b}: {type(exc).__name__}: {str(exc)[:90]}")
    if not raw:
        raise RuntimeError("no symbols could be fetched")
    common = None
    for df in raw.values():
        common = df.index if common is None else common.intersection(df.index)
    return {b: df.loc[common] for b, df in raw.items()}


def live_quote(venue: str, base: str) -> dict:
    """Live bid/ask/last for the paper-trade round. Real prices, no keys."""
    ex = _exchange(venue)
    t = ex.fetch_ticker(symbol(venue, base))
    return {
        "venue": venue,
        "base": base,
        "bid": t.get("bid"),
        "ask": t.get("ask"),
        "last": t.get("last"),
        "ts_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "exchange_ts": t.get("datetime"),
    }


def consensus_quote(bases: List[str], venues: List[str]) -> dict:
    """Cross-venue price consensus — used to detect a stale or broken single feed."""
    out: Dict[str, Dict[str, dict]] = {}
    for b in bases:
        out[b] = {}
        for v in venues:
            try:
                out[b][v] = live_quote(v, b)
            except Exception as exc:
                out[b][v] = {"error": f"{type(exc).__name__}: {str(exc)[:70]}"}
    return out


def cache_manifest() -> dict:
    return {
        "cache_dir": str(CACHE_DIR),
        "files": sorted(p.name for p in CACHE_DIR.glob("*.csv")),
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


if __name__ == "__main__":
    import sys

    venue = sys.argv[1] if len(sys.argv) > 1 else "binance"
    base = sys.argv[2] if len(sys.argv) > 2 else "BTC"
    d = fetch_ohlcv(venue, base, "1h", 300)
    print(d.tail())
    print(json.dumps(cache_manifest(), indent=1)[:400])
