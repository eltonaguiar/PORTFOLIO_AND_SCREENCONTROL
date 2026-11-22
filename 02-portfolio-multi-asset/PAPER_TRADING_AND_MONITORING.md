# Paper trading and signal monitoring — the loop between backtest and money

A backtest is a claim. Paper trading is the audit. It catches the things backtests structurally cannot: feed
outages, latency, fills that never happen, and rules that only work when the bar is already closed.

Scope: **simulated execution against live data. No live orders, no broker credentials, no money movement.**

## Pipeline

```
feed (quote/tick or 1m bars)
      │
      ▼
  aggregator ──► strategy (SAME code as the backtest) ──► order intent
                                                            │
                                                            ▼
                                                   paper broker / fill model
                                                            │
                        ┌───────────────────────────────────┼──────────────────┐
                        ▼                                   ▼                  ▼
                 position ledger                     TP/SL monitor        risk gate
                        │                                   │                  │
                        └──────────────► append-only event log (JSONL) ◄───────┘
                                                    │
                                                    ▼
                                        report + alerts (on TP/SL, gaps, halts)
```

If your backtest and paper loop do not share the strategy class, you are testing two different programs.

## Fill model — write down what you assume

| Order type | Paper rule | Trap |
|---|---|---|
| Market | fill at next bar open (or next quote) ± half-spread | filling at the *signal* bar's close is look-ahead |
| Limit | fill only if price **trades through** the limit (not merely touches) | touch-fills inflate every mean-reversion result |
| Stop | trigger on trade-through, then fill as market ± slippage | bar-only data cannot tell you the order of stop vs target inside one bar |
| Stop-limit | trigger, then limit rules | can go unfilled entirely — model that outcome |
| Partial fills | cap size at a fraction of bar volume | ignoring this is how a "scalable" strategy becomes untradeable |

Costs to include from day one: commission per side, spread, slippage, financing/swap for FX and perps, borrow
for shorts. If a strategy only works at zero cost, it does not work.

## TP/SL monitoring with the data you actually have

- **Quote/tick stream:** evaluate TP and SL on every update; record which was touched first. This is the only
  honest way to sequence them.
- **1-minute bars only:** you cannot order a stop and a target inside one bar. Two acceptable options —
  (a) report both outcomes and the range, (b) assume the pessimistic one (SL first) everywhere. Never assume
  the optimistic one, which is what most naive scripts do.
- **Stale-feed guard:** if no update for `N × expected interval`, halt the loop and mark the session as
  degraded — do not carry a position through a data gap believing you are watching it.

## Event log (append-only JSONL, one line per event)

```json
{"ts_utc":"2026-11-22T14:31:02.114Z","kind":"signal","signal_id":"s-0042","instrument":"BTCUSDT-PERP","side":"BUY","reason":"ema5>ema15","bar":{"open":91240.5,"close":91268.0}}
{"ts_utc":"2026-11-22T14:31:02.160Z","kind":"intent","signal_id":"s-0042","qty":0.01,"type":"MARKET","tp":92181.7,"sl":90811.4}
{"ts_utc":"2026-11-22T14:31:02.402Z","kind":"fill","signal_id":"s-0042","px":91270.0,"qty":0.01,"slippage_bps":0.22}
{"ts_utc":"2026-11-22T15:04:11.900Z","kind":"exit","signal_id":"s-0042","reason":"TP","px":92182.0,"pnl_base":9.12}
```

Fields that let you audit the run later: `signal_id` joins everything; decision→submit→fill timestamps give
latency; `slippage_bps` gives the gap between assumption and reality.

## What to measure in paper (not just PnL)

| Metric | Why it matters |
|---|---|
| signal→decision→fill latency (p50/p95) | tells you whether the strategy is even executable at your update rate |
| realised vs assumed slippage | the most common reason a backtest is optimistic |
| fill rate on limits | a strategy that only works when filled is a strategy that doesn't |
| TP/SL touched-but-not-filled count | the intrabar conflict, quantified |
| data gaps / feed reconnects per day | if this is > 0, your monitoring is fiction during those windows |
| positions held through a halt | the risk you did not model |

## Scheduling — pick a real scheduler

| Option | Fit |
|---|---|
| Local worker (systemd timer on Linux, Task Scheduler on Windows, `pm2`/`supervisord`) | ✅ the default for intraday; you control restarts, logs and uptime |
| tmux/screen + a supervisor loop | ✅ fine on a workstation; survives disconnect |
| **GitHub Actions `schedule:`** | ⚠️ **nightly/batch only.** Minimum interval is 5 minutes, runs are routinely delayed under load, and scheduled workflows **disable themselves after ~60 days of repository inactivity** on public repos. Never use it to watch TP/SL |
| Cloud VM + cron | ✅ when the workstation sleeps |

Whatever you choose: the scheduler starts the process, the process owns the loop, and an external watchdog
restarts it (crash-only design, same as the trading engines).

## Kill switches (before you need them)

- max daily loss and max drawdown → halt and flatten, no "one more trade";
- max concurrent positions and max notional per instrument;
- stale-data and clock-skew guards;
- a `STOP` file checked each cycle, plus a signal-safe shutdown that writes the final ledger line;
- paper-only credentials, and a hard check that the broker client is **not** in live mode.

## What paper trading still cannot tell you

Queue position, adverse selection, venue rejects under stress, exchange outages mid-position, and how *you*
behave when a real loss is on the screen. Treat a clean paper run as "not yet disproven", never as "proven".
