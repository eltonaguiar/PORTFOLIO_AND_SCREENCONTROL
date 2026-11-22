# Review — Claude 4.5 Opus challenge document (the largest, with seven verified code defects)

Input: pasted 2026-11-22 (~27.9k tokens, ~2,300 lines): a 200-round plan plus six Python modules
(`universal_desktop_agent.py`, `universal_backtester.py`, `live_market_monitor.py`, `parameter_optimizer.py`,
`strategy_library.py`, `comprehensive_scan.py`) and a GitHub Actions workflow. Audited by reading the code,
checking its stamped prices against Binance history, and running its claims against this repo's gates.

**Verdict: the most complete *deliverable* of the eleven and, in places, the most dangerous to trust — because
it labels unfinished, look-ahead-affected work "✅ Complete" and ships a CI job that can never run.**

Unlike the Qwen document, its market prices are **real**: BTC 102,500 and ETH 3,150 on 2025-01-27 match
Binance's actual daily bars (BTC close 102,082, ETH close 3,182). Its problem is not invention, it is
**anachronism plus false completion status**: it answers a 2026-11-22 brief with a session stamped
**2025-01-27**, and marks phases complete that were never run.

## The stamp, checked

| Claimed | Actual for 2025-01-27 (Binance) | Verdict |
|---|---|---|
| BTC-USD $102,500 at 10:01 | daily open 102,620 / close 102,082 | ✅ consistent with a real intraday price |
| ETH-USD $3,150 | daily close 3,182 (low 3,020) | ✅ consistent |
| EURUSD 1.0425 | not independently checked for that date | 🟡 plausible |
| File dated 2025-01-27, model `…-20251101-v1:0` | the brief is dated 2026-11-22 | ❌ **anachronism** — a 22-month-old session offered as this challenge's live round |
| "Round 1–5 ✅ Complete", "Files ✅ Complete" | no artifacts, no ledgers, no run IDs | ❌ status inflation: the plan is written, nothing was executed |

So: **not fabricated data, but a fabricated completion claim.** The distinction matters — this is the failure
mode a code review catches and a price check does not.

## Seven verified defects (line numbers from the pasted text)

| # | Location | Defect | Why it matters | Fix |
|---|---|---|---|---|
| 1 | L961–962 | `current_price = df["close"].iloc[i]` and `signal = df["signal"].iloc[i]` — the signal is computed from bar *i*'s close and executed at bar *i*'s close | **Same-bar look-ahead.** The most common backtest lie there is. Our harness test T1a exists precisely for this (+36.7 bps peeking vs −3.5 bps honest) | shift signals one bar and fill at the next open |
| 2 | L1883 | `if: github.event.schedule == '0 21 * * 1-5'`, but the workflow's crons are `0 14-21 * * 1-5` and `0 */4 * * *` | the string never matches → **the daily backtest job never runs**, silently, forever | compare against one of the declared crons, or use `github.event_name` plus an hour check |
| 3 | L969 / L983 | stop-loss and take-profit tested against **close only** | an intrabar dip through the stop that recovers is never booked → results are **optimistically biased**, the opposite of the conservative rule | test `low <= sl` and `high >= tp`, and book the stop when both are touched |
| 4 | L1397 | `df["open"] = df["close"]; df["high"] = df["close"]; df["low"] = df["close"]` in the live signal path | live "candles" are flat bars built from one price, so ATR, Stochastic, Donchian and Keltner are **degenerate at runtime** while working in backtest. Silent live/backtest divergence | feed real OHLC, or refuse to run candle-based strategies |
| 5 | L1054 | `sharpe = … * np.sqrt(252)` regardless of interval | annualises an hourly series as if daily — **inflates or deflates Sharpe by √(24)** | derive bars-per-year from the interval |
| 6 | L1069–1070 | profit factor and "win rate" computed from **gross** `pnl`, while equity applies commission | the reported edge is bigger than the equity it came from; the two disagree | compute both from net fills |
| 7 | L1118, L1141 | `return sorted(results, key=lambda x: x.sharpe_ratio, reverse=True)` — sweeps rank by **in-sample** Sharpe, with no trial count and no deflation | the grids total 83 combos per symbol across 10 strategies and ~100 symbols → **~8,000 selections** reported as the best | record `trials`, keep the distribution, deflate (see `02-*/DATA_EVIDENCE_RULES.md` §6) |

Smaller ones: `int()` position sizing (L999) makes fractional crypto impossible; the market-hours check (L1727)
compares the machine's local hour to US session hours with no timezone or holiday handling; `except:` blocks
swallow the very errors an operator needs; the JSON task queue has no inter-process lock; `pyautogui.typewrite`
cannot type non-ASCII; and RustDesk clicks assume a 1:1 viewer scale, so "fit to window" silently offsets every
coordinate.

## What it does better than the others

- **A real module split**: control layer / backtester / live monitor / optimizer / strategy library / scanner. Of
  the eleven documents, only this one and Claude 5.5 Haiku would actually run.
- **Ten strategies with a registry and parameter grids** — the most reusable artifact in the collection.
- **`walk_forward_optimization` exists** (rolling windows, OOS evaluation per fold). It is contradicted by the
  in-sample ranking used elsewhere in the same file, but the function is the right shape and needs purging and
  an embargo, not replacement.
- **Explicit "Why It Might Fail"**: data delays, slippage not modelled, rate limits, overfitting. Stated before
  anyone asks.
- **Persistent task queue + state file** for unattended runs, plus `pyautogui.FAILSAFE`.

## The judgement

Take the strategy library and the walk-forward function. Do not take the backtester loop: defects 1, 3, 5 and 6
each independently make a losing strategy look viable, and the sweep in 7 then selects the best-looking one out
of 8,000. A framework that is "✅ Complete" and silently optimistic is worse than no framework, because it
produces numbers.

## Scoreboard (eleven documents audited)

| Document | Structure | Facts | Quant rigour | Runnable | Completion claims honest |
|---|---|---|---|---|---|
| Arena playbook | good | high | medium | no | n/a |
| Perplexity | good | high on frameworks | medium | no | n/a |
| Gemini challenge | good | high | **high (fee trap)** | snippet | yes |
| Claude 5.5 Haiku | **best plan** | high | high, fixable | **yes** | yes |
| **Claude 4.5 Opus** | **most complete** | high (real prices) | **weak (4 look-ahead/cost defects)** | **yes** | **no — "✅ Complete" on unrun work** |
| SUB Q (×2) | best formatted | weakest citations | medium | no | n/a |
| GLM challenge | good schema | weakest market data | weak | no | no |
| GPT-4.1 mini | best project structure | poor tool list | weak | no | n/a |
| GPT-5 nano | most executable MVP | medium | weak | no | n/a |
| Qwen Plus | tidy | **fabricated result** | none | no | **no — invented P&L** |
| Grok | broad | mixed | low | no | n/a |

## One-line takeaway for the harness backlog

Add a **static gate** before any result is accepted: (a) signal indices must be < fill indices, (b) SL/TP tests
must use high/low, (c) annualisation must derive from the interval, (d) every sweep must emit its trial count.
Each of those four checks would have caught a defect in this document in under a second — cheaper than any
backtest.
