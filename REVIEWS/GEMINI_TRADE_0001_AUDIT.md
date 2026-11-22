# Review — Gemini-3.1-Pro "TRADE_0001" live trade + Round 1A/1B, 2026-11-22

Input: a supplied Gemini-3.1-Pro response claiming a **closed profitable live paper trade**
(`TRADE_0001`, ETH/USD long, entry 04:17 AM EST, exit 04:25 AM EST, net `+0.449%`), plus a
GitHub Actions TP/SL monitor, a paper-portfolio state schema, and a Windows anti-stall
supervisor daemon.

**Verdict: the trade's direction was right and its entry price is real on Kraken — but the
exit price is not a Kraken price, the round trip therefore splices two venues, and the entire
claimed profit sits inside a fee assumption that is 2x to 5x too low. Repriced at Kraken's
actual retail taker fee the same trade nets `+0.001%`: exactly zero. Separately, the trade it
currently records as OPEN is priced at a level that never traded on either venue.**

Everything below was checked against **1-minute bars from Kraken and Binance** pulled on
2026-11-22 for the exact window, not against prose.

---

## 1. The claim

| field | claimed |
|---|---|
| instrument | ETH/USD spot (Kraken pair `ETHUSD`) |
| entry | `2026-11-22T09:17:00Z` @ **$1,681.50** |
| exit | `2026-11-22T09:25:00Z` @ **$1,690.73** |
| hold | 8 minutes |
| gross | +0.549% |
| fees | **−0.100% round trip** (`fee_bps_round_trip: 10.0`) |
| net | **+0.449%** ($4.49 per $1,000) |

## 2. Leg-by-leg verification

### Entry — real, on Kraken only

| venue | 09:17 bar | is $1,681.50 reachable? |
|---|---|---|
| **Kraken ETHUSD** | 1681.44 / **1681.92** / **1680.76** / 1680.76 | ✅ **inside the bar** |
| Binance ETH/USDT | 1684.29 / 1684.62 / **1683.64** / 1683.64 | ❌ **0.13% below the bar low** |

Credit where due: the entry is a genuine Kraken print. It is not a fabricated number.

### Exit — not a Kraken price

| venue | 09:25 bar | is $1,690.73 reachable? |
|---|---|---|
| **Kraken ETHUSD** | **1688.43** / **1688.43** / **1686.37** / 1686.37 | ❌ **0.14% above the bar HIGH** |
| Binance ETH/USDT | 1691.70 / 1691.70 / 1689.35 / 1689.36 | ✅ inside the bar |

The Kraken 09:25 bar never exceeds **1688.43**. On Kraken, $1,690.73 was last traded in the
**09:23** bar (high 1692.21) — two minutes before the claimed exit.

**So the round trip takes its entry from Kraken's book and its exit from Binance's.** Each leg
is individually real; no single venue supports both at the stated times. That is a
**cross-venue price splice**, not a fill.

The mechanism is in the provided code, and it is one line:

```python
if trade.get("asset_class") == "crypto" and trade.get("kraken_pair"):
    try:
        bars = fetch_kraken_5m_bars(trade["kraken_pair"], since_epoch)
        if bars:
            return bars
    except Exception as exc:
        print(f"[WARN] Kraken fetch failed for {trade['symbol']}: {exc}. Falling back to yfinance.")
return fetch_yfinance_5m_bars(trade["symbol"], opened_dt)
```

The venue is chosen **per evaluation, not per trade**. A Kraken outage on one tick silently
moves that tick's TP/SL test onto a different price series, and the trade's P&L then comes
from two books. The fix is to record the venue *on the trade at entry* and refuse to evaluate
it against a different source; a fallback should mark the trade `UNVERIFIED`, not re-price it.
The observed Kraken↔Binance basis here was **~17 bps** at 09:17 — larger than the claimed
entire net profit.

## 3. The fee assumption is the whole result

`fee_bps_round_trip: 10.0` means **5 bps per side**. That is below essentially every retail
spot taker fee in existence:

| schedule | round trip | per side |
|---|---:|---:|
| **claimed** | **10 bps** | 5 bps |
| Binance spot standard | 20 bps | 10 bps (0.10%) |
| Kraken base tier | **52 bps** | 26 bps (0.26%) |
| measured in my own live ledger | 20 bps | 10 bps, entry at ask +10 bps, exit at bid −10 bps |

Repricing the **same trade at the same prices** under each schedule, and under the honest
exit each scenario allows:

| exit scenario | gross | @20 bps | **@52 bps** |
|---|---:|---:|---:|
| Kraken 09:25 high (impossible-perfect) | +0.412% | +0.212% | **−0.108%** |
| Kraken 09:25 close (honest at the stated time) | +0.290% | +0.090% | **−0.230%** |
| **Kraken 09:23 close (where 1690.73 actually traded)** | +0.521% | +0.321% | **+0.001%** |
| Kraken 09:23 high (best case) | +0.637% | +0.437% | **+0.117%** |
| Binance 09:25 high | +0.607% | +0.407% | +0.087% |

**The headline number is a fee assumption, not an edge.** At Kraken's real base taker fee the
best honest exit on that venue nets **+0.001%** — identical to zero. The claimed +0.449% is
`+0.549% − 0.100%`; replace 0.100 with 0.520 and the result is arithmetic, not opinion.

This is the same mechanism Mercury3's PART13 measured independently (fee line 9× the gross
edge) and the same one my 126-cell census found (fee line larger than the gross line in 5 of 6
families). Three independent measurements, one conclusion.

## 4. The trade it reports as OPEN is priced at a level that never traded

`TRADE_0002` is recorded as:

```
"entry_price": 1690.73, "opened_at_utc": "2026-11-22T09:26:00Z"
```

| venue | 09:26 bar range | 1690.73 reachable? |
|---|---|---|
| Kraken ETHUSD | 1684.44 – **1686.36** | ❌ 0.26% above the high |
| Binance ETH/USDT | 1686.99 – **1689.35** | ❌ 0.10% above the high |

**Unattainable on both venues at the stated time.** It inherits `TRADE_0001`'s exit price as
its entry, so the splice propagates: every mark, every TP/SL test and every future P&L row on
the open position is measured against a price nobody could have transacted. This is the more
serious defect of the two, because it is live and still accumulating.

## 5. Code defects found by reading it

| # | defect | consequence |
|---|---|---|
| 1 | **Venue chosen per evaluation, not per trade** (§2) | cross-venue splice; P&L from two books |
| 2 | `fee_bps_round_trip = 10.0` (§3) | understates friction 2x–5.2x; turns a breakeven into a "win" |
| 3 | **The entry bar is included in the SL/TP scan.** `fetch_*_bars(since=open_time)` returns the bar *containing* the entry, whose high/low span price action from **before** the position existed | a stop can trigger on a move that happened before entry — look-ahead in the pessimistic direction, which hides as bad luck rather than as a bug |
| 4 | Time stop returns `last_bar["close"]` but stamps `closed_at = now` | the fill time and the price come from different moments |
| 5 | Workflow has `git add state/... \|\| true` then `git push` with **no retry** | on any concurrent push the job goes red and the tick's state is lost; `\|\| true` also hides a missing `state/` directory |
| 6 | `paper_trades.json` is a **mutable JSON document**, not an append-only log | the state is the only record; a partial write corrupts history, and there is no way to rebuild it. My harness keeps an append-only JSONL and rebuilds state from it for exactly this reason |

## 6. What the design gets right

Not everything here is wrong, and the good parts are worth copying:

- **SL-first on a same-bar tie** (`if sl_hit and tp_hit: return sl, "STOP_LOSS_SAME_BAR_CONSERVATIVE"`).
  This matches certification test **T3** in this repo and is the correct pessimistic choice —
  most implementations resolve it as a win.
- **15-minute cron with 5-minute intrabar candles** is a sensible cadence: fine enough to
  sequence TP vs SL on one bar, coarse enough that GitHub Actions' 5-minute minimum is not the
  bottleneck.
- **A closed-trade CSV ledger appended separately from the JSON state** is the right instinct,
  even though §5.6 shows the source of truth should be the log.
- **The multi-asset plan via `yfinance` fallback** is reasonable coverage, with the caveat in §2.
- **The anti-stall supervisor's core idea is correct**: isolate every UIA/COM nudge in a
  timeout-guarded subprocess (`subprocess.run(..., timeout=...)`) so a hung Electron window
  cannot take down the supervisor, and keep the PC awake with `SetThreadExecutionState`. That
  is a real failure mode and the mitigation is the right shape.
- **The `desktop_control` consent countdown set to 0** is the correct setting for unattended
  runs — and worth flagging as the one place where this design deliberately removes a human
  gate, which is only acceptable because nothing in that loop touches money.

## 7. Reproduce this audit

```bash
# Kraken 1m, the venue the trade claims
curl -s "https://api.kraken.com/0/public/OHLC?pair=ETHUSD&interval=1&since=$(date -d '2026-11-22T09:05:00Z' +%s)" \
  | python -c "import sys,json;d=json.load(sys.stdin)['result'];k=[x for x in d if x!='last'][0];[print(r) for r in d[k][:40]]"

# Binance 1m, an independent venue
python -c "import ccxt,pandas as pd,datetime as dt;ex=ccxt.binance();b=ex.fetch_ohlcv('ETH/USDT','1m',since=int(dt.datetime(2026,11,22,9,10,tzinfo=dt.timezone.utc).timestamp()*1000),limit=30);print(pd.DataFrame(b).to_string())"
```

Bars used, quoted verbatim:

```
Kraken ETHUSD 1m
09:17  1681.44  1681.92  1680.76  1680.76     <- entry 1681.50 is INSIDE
09:23  1689.94  1692.21  1689.94  1690.26     <- 1690.73 traded HERE on Kraken
09:25  1688.43  1688.43  1686.37  1686.37     <- claimed exit time: high is 1688.43
09:26  1686.36  1686.36  1684.44  1684.44     <- TRADE_0002 entry 1690.73 NOT reachable

Binance ETH/USDT 1m
09:17  1684.29  1684.62  1683.64  1683.64     <- entry 1681.50 NOT reachable (below low)
09:25  1691.70  1691.70  1689.35  1689.36     <- exit 1690.73 IS reachable here
09:26  1689.35  1689.35  1686.99  1687.18     <- TRADE_0002 entry NOT reachable
```

## 8. What this repository does differently, and why it matters here

| this repo | Gemini's monitor |
|---|---|
| 26 bps round turn as the *default*, plus a 5-point cost grid to expose the breakeven cost | 10 bps, hard-coded, below any real venue |
| venue recorded on the trade at open; a fallback marks the row unverified | venue re-chosen on every evaluation |
| append-only JSONL ledger; state is rebuilt from it | mutable JSON as the only record |
| both-touched bar → stop (certified by test T3) | same rule ✅ |
| every result carries n, execution convention and cost in the same row | `net_return_pct` with no fee provenance |

## 9. Verdict

**A correctly-directioned trade reported at a price no single venue could have filled, whose
profit exists only because the fee was set 5× too low.** Repriced honestly at the venue it
names, it nets **+0.001%**. The open position it is now tracking is priced 0.10–0.26% above
what either venue traded at the stated minute.

This is not a fabricated trade — the entry print is real and ETH genuinely rallied. It is the
more common and more insidious thing: **a real move, measured on spliced prices, with friction
assumed away.** That combination produces exactly the kind of "+0.449% win" that a 200-round
program would then try to reproduce for months.
"""
