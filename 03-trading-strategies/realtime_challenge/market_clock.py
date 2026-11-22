"""Market clock — is this asset class actually open right now?

Adopted from a peer proposal (GLM 5.3 Flash: `market_open.py` picks what is open *right
now* in UTC). It closes a real hole this project hit on its first live round: at 04:00 EST
on a Sunday, equities, FX and futures are all closed, and only crypto can legitimately be
traded. Nothing in the harness enforced that — it was noticed by a human reading a calendar.

Sessions are defined in the **market's own timezone** and converted to UTC, so DST is handled
by zoneinfo rather than by a hard-coded offset. That matters: a fixed `UTC-5` would silently
shift every US session by an hour twice a year.

Honesty about precision
-----------------------
  crypto     EXACT   — 24/7/365, no session, no holiday.
  fx         EXACT   — 17:00 Sunday to 17:00 Friday, America/New_York.
  us_equity  APPROX  — Mon-Fri 09:30-16:00 ET. No holiday calendar, no half-days, no halts.
  futures    APPROX  — Sun 18:00 to Fri 17:00 ET with a daily 17:00-18:00 break. No holiday
                       calendar and no exchange-specific product hours.

Anything marked APPROX must not be used to claim a fill. Use it to refuse trading a closed
class, and check the venue's own calendar before treating an APPROX-open session as tradeable.

  python -m realtime_challenge.market_clock
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, time, timedelta, timezone
from typing import Dict, Optional
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")
UTC = timezone.utc


@dataclass
class Session:
    asset_class: str
    open: bool
    precision: str          # EXACT | APPROX
    detail: str
    next_open_utc: Optional[str] = None
    next_close_utc: Optional[str] = None

    def as_dict(self) -> dict:
        return asdict(self)


def _ny(dt: datetime) -> datetime:
    return dt.astimezone(NY)


def _at(day, hh: int, mm: int = 0) -> datetime:
    return datetime.combine(day, time(hh, mm), tzinfo=NY)


def crypto_status(now: datetime) -> Session:
    return Session("crypto", True, "EXACT", "24/7/365 — no session, no holiday")


def fx_status(now: datetime) -> Session:
    """17:00 Sunday -> 17:00 Friday, New York time."""
    n = _ny(now)
    wd = n.weekday()                      # Mon=0 .. Sun=6
    t = n.time()
    if wd == 5:                           # Saturday
        nxt = _at(n.date() + timedelta(days=1), 17, 0)
        return Session("fx", False, "EXACT", "Saturday — FX closed",
                       next_open_utc=nxt.astimezone(UTC).isoformat(timespec="seconds"))
    if wd == 6 and t < time(17, 0):       # Sunday before 17:00
        nxt = _at(n.date(), 17, 0)
        return Session("fx", False, "EXACT", "Sunday before 17:00 ET open",
                       next_open_utc=nxt.astimezone(UTC).isoformat(timespec="seconds"))
    if wd == 4 and t >= time(17, 0):      # Friday after 17:00
        nxt = _at(n.date() + timedelta(days=2), 17, 0)
        return Session("fx", False, "EXACT", "Friday after 17:00 ET close",
                       next_open_utc=nxt.astimezone(UTC).isoformat(timespec="seconds"))
    return Session("fx", True, "EXACT", "inside the 17:00 Sun - 17:00 Fri ET session")


def us_equity_status(now: datetime) -> Session:
    """Mon-Fri 09:30-16:00 ET. APPROX: no holiday calendar, no half-days."""
    n = _ny(now)
    wd, t = n.weekday(), n.time()
    if wd >= 5:
        days = 7 - wd
        nxt = _at(n.date() + timedelta(days=days), 9, 30)
        return Session("us_equity", False, "APPROX", "weekend",
                       next_open_utc=nxt.astimezone(UTC).isoformat(timespec="seconds"))
    if t < time(9, 30):
        nxt = _at(n.date(), 9, 30)
        return Session("us_equity", False, "APPROX", "pre-open (before 09:30 ET)",
                       next_open_utc=nxt.astimezone(UTC).isoformat(timespec="seconds"))
    if t >= time(16, 0):
        nxt = _at(n.date() + timedelta(days=1 if wd < 4 else 3), 9, 30)
        return Session("us_equity", False, "APPROX", "after 16:00 ET close",
                       next_open_utc=nxt.astimezone(UTC).isoformat(timespec="seconds"))
    close = _at(n.date(), 16, 0)
    return Session("us_equity", True, "APPROX",
                   "regular session (holiday calendar NOT checked)",
                   next_close_utc=close.astimezone(UTC).isoformat(timespec="seconds"))


def futures_status(now: datetime) -> Session:
    """Sun 18:00 -> Fri 17:00 ET, daily 17:00-18:00 ET break. APPROX."""
    n = _ny(now)
    wd, t = n.weekday(), n.time()
    if wd == 5:
        nxt = _at(n.date() + timedelta(days=1), 18, 0)
        return Session("futures", False, "APPROX", "Saturday — closed",
                       next_open_utc=nxt.astimezone(UTC).isoformat(timespec="seconds"))
    if wd == 6 and t < time(18, 0):
        nxt = _at(n.date(), 18, 0)
        return Session("futures", False, "APPROX", "Sunday before 18:00 ET",
                       next_open_utc=nxt.astimezone(UTC).isoformat(timespec="seconds"))
    if wd == 4 and t >= time(17, 0):
        nxt = _at(n.date() + timedelta(days=2), 18, 0)
        return Session("futures", False, "APPROX", "Friday after 17:00 ET",
                       next_open_utc=nxt.astimezone(UTC).isoformat(timespec="seconds"))
    if time(17, 0) <= t < time(18, 0):
        nxt = _at(n.date(), 18, 0)
        return Session("futures", False, "APPROX", "daily 17:00-18:00 ET maintenance break",
                       next_open_utc=nxt.astimezone(UTC).isoformat(timespec="seconds"))
    return Session("futures", True, "APPROX", "inside the session (holiday calendar NOT checked)")


REGISTRY = {
    "crypto": crypto_status,
    "fx": fx_status,
    "us_equity": us_equity_status,
    "futures": futures_status,
}


def market_status(now: Optional[datetime] = None) -> Dict[str, Session]:
    now = now or datetime.now(UTC)
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)
    return {k: fn(now) for k, fn in REGISTRY.items()}


def open_classes(now: Optional[datetime] = None) -> list[str]:
    return [k for k, s in market_status(now).items() if s.open]


def assert_tradeable(asset_class: str, now: Optional[datetime] = None) -> Session:
    """Raise if the class is closed — the guard the first live round was missing.

    Live rounds must call this before opening anything. APPROX-open is allowed but the
    caller records the precision, because an APPROX session has no holiday calendar behind it.
    """
    st = market_status(now).get(asset_class)
    if st is None:
        raise ValueError(f"unknown asset class {asset_class!r}; known: {sorted(REGISTRY)}")
    if not st.open:
        raise RuntimeError(
            f"{asset_class} is CLOSED ({st.detail}). Next open: {st.next_open_utc}. "
            f"Open now: {open_classes(now)}"
        )
    return st


if __name__ == "__main__":
    now = datetime.now(UTC)
    print(f"UTC now: {now.isoformat(timespec='seconds')}   "
          f"(New York: {_ny(now).isoformat(timespec='seconds')})\n")
    for name, st in market_status(now).items():
        flag = "OPEN  " if st.open else "closed"
        print(f"  {flag} {name:10s} [{st.precision:6s}] {st.detail}")
        if st.next_open_utc:
            print(f"          next open: {st.next_open_utc}")
        if st.next_close_utc:
            print(f"          closes at: {st.next_close_utc}")
    print(f"\nTradeable right now: {open_classes(now)}")
