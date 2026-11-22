# REALTIME CHALLENGE — `deepseek-flash` — 2026-11-22 03:56 EST

**Model:** deepseek-flash
**Started:** 2026-11-22 03:56 EST (08:56 UTC)
**Venue:** crypto spot, 24/7, public exchange endpoints (no API keys)
**Harness:** `realtime_challenge/` in this folder
**Live market state at start:** BTC ≈ $59,797 (+3.4% on the day), down −27% over the prior 25 days
**US equities:** closed (Sunday). **FX:** closed until 17:00 EST. **Crypto:** open — this is the only class that can be traded live right now, which is why the challenge is denominated in crypto.

> Nothing here is financial advice. No real order is ever sent by this code. Every price
> is a real public exchange tick; every dollar is pretend.

---

## 1. Why this challenge exists

The repo's own verdict doc (`reports/2026-11-22-capital-allocation-verdict.md`) states
the problem precisely: 34 pre-registered cells across 10 asset classes, exactly **one**
clears the backtest gates, and it has **zero closed forward trades**. The bottleneck is
not strategy ideas. The bottleneck is that **nothing accumulates forward evidence**.

So this challenge is not "find a strategy that backtests well". It is:

> Generate **forward evidence a stranger can audit** — ≥100 closed trades, net of 26 bps
> round turn, with a bootstrap CI on mean trade return excluding zero, and positive
> excess versus buy-and-hold on the same window — for at least one asset class. Or
> document, with numbers, why none exists.

A clean "no class qualifies, here is the proof" is an accepted terminal outcome. A
headline win rate on n=2 is not.

---

## 2. The prototype — what was actually built and run

### 2.1 Harness modules

| module | job |
|---|---|
| `costs.py` | friction as a first-class object: 10 bps taker + 3 bps slippage per side = **26 bps round turn**, plus a 5-point cost grid to expose the breakeven cost |
| `data.py` | ccxt public OHLCV, paginated forward, cached to CSV per run; 5-venue live quote consensus |
| `engine.py` | event-driven bar replay, ~200 lines, pessimistic by construction (below) |
| `strategies.py` | **6 pre-registered hypotheses**, one frozen parameter set each |
| `stats.py` | profit factor, expectancy in R, bootstrap CI, **deflated Sharpe** (Bailey–López de Prado), permutation control |
| `live.py` | the live pretend-trading round: real bid/ask, taker fee both legs, TP/SL/time-stop |
| `ledger.py` | append-only JSONL + materialised state; state is rebuildable from the log so a corrupt file cannot invent a trade |
| `worker/forward_supervisor.py` | one non-interactive pass for a GitHub Actions cron |
| `proof/test_harness.py` | the 5 tests that make the engine allowed to say "no" |
| `proof/weekend_test.py` | the clustered, controlled re-test of the only surviving family |

### 2.2 Non-negotiable execution rules (all enforced in code)

1. **Signals on closed bars only; fills at the NEXT bar's open.** `engine.run_from_signals`
   starts its fill loop at `signal_index + 1`.
2. **Taker fee + slippage on both legs, always.** No zero-cost backtest is reachable.
3. **If a bar touches both TP and stop, the STOP fills first.** OHLC bars do not encode
   visit order; any engine that resolves the tie as a win is inventing it.
4. **Risk-normalised sizing:** 1% of equity risked at the stop, capped at 1× notional.
5. **No parameter sweeps.** Six hypotheses, frozen params, trial count recorded and fed
   into the deflation.
6. **The desk's own denylist is wired in:** no AVAX/TRX/MATIC, no entries in UTC hours
   {2, 8, 13, 20}, and `tp/sl ≤ 2.5` asserted at import.

### 2.3 The six pre-registered hypotheses

| id | rule | long/short |
|---|---|---|
| H-R1 `trend_pullback` | EMA50 > EMA200, price dips to EMA20 with RSI(14) < 45, then reclaims | long only |
| H-R2 `donchian_breakout` | 20-bar Donchian break — classic TSMOM | both |
| H-R3 `bollinger_meanrev` | low touches the lower Bollinger band with close > SMA200 | long only |
| H-R4 `vol_compression` | ATR(14) in the bottom quintile of 168 bars, then clears the 12-bar high | long only |
| H-R5 `weekend_effect` | enter Fri 20:00 UTC, exit Sun 20:00 UTC | long only |
| H-R6 `rsi2_pullback` | RSI(2) < 10 with close > SMA200 (Connors, ported to 24/7) | long only |

---

## 3. Result 1 — the 1-hour matrix: 42 cells, all negative

**Setup:** 7 symbols (BTC, ETH, SOL, XRP, DOGE, ADA, LINK) × 6 hypotheses, 3,000 × 1h
bars, **2026-07-20 → 2026-11-22** (125 days), 26 bps round turn, deflated Sharpe at
n_trials = 42.

| strategy | best cell | n | PF | ret | exposure | DSR |
|---|---|---:|---:|---:|---:|---:|
| H-R5 weekend_effect | XRP | 18 | 1.56 | +0.5% | 18% | **0.0485** |
| H-R3 bollinger_meanrev | ADA | 31 | 1.19 | +3.9% | 4% | **0.0425** |
| H-R6 rsi2_pullback | ADA | 45 | 1.26 | +3.8% | 9% | **0.0710** |
| H-R2 donchian_breakout | SOL | 137 | 0.76 | −20.0% | 16% | 0.0003 |
| H-R1 trend_pullback | ETH | 19 | 0.69 | −3.0% | 2% | 0.0046 |
| H-R4 vol_compression | LINK | 24 | 0.81 | −2.4% | 1% | 0.0058 |

**Nothing clears DSR 0.95.** The best cell in 42 reaches **0.071**. For comparison, the
certification test T4 shows pure noise cells reaching 0.0017 — so 0.071 is a little above
noise and far below significance.

**Permutation control:** every strategy's realised mean return sat inside the shuffled
distribution. p-values: 0.20, 0.43, 0.51, 0.53, 0.79, 0.89. No cell beat the
shuffled p95.

### The cost grid — where each family dies

| strategy | 0 bps | 14 bps | **26 bps** | 40 bps | breakeven |
|---|---:|---:|---:|---:|---:|
| H-R5 weekend_effect | +37.18 | +14.60 | **+5.93** | −3.85 | **≈ 35 bps** |
| H-R6 rsi2_pullback | +12.50 | −3.47 | **−16.45** | −28.31 | ≈ 10 bps |
| H-R3 bollinger_meanrev | +0.23 | −17.91 | **−28.16** | −39.14 | ≈ 0 bps |
| H-R2 donchian_breakout | −3.26 | −16.30 | **−27.41** | −39.23 | never positive |
| H-R4 vol_compression | −7.56 | −19.14 | **−32.11** | −46.31 | never positive |
| H-R1 trend_pullback | −15.55 | −30.82 | **−40.26** | −55.75 | never positive |

*(mean net return per trade, in bps, pooled across symbols)*

**Reading:** four of six families are negative **before any costs at all**. Only the
weekend effect survives retail friction, and only by ~6 bps per trade — a margin thinner
than one bad fill.

### A metric correction I had to make

The first version of this table reported `excess_vs_bh` and handed H-R2 a **+28% "excess
return"** — because the window was a −29% crypto bear market and H-R2 was in the market
only 13% of the time. Being flat in a crash is not alpha. The table now reports
`excess_scaled = strategy return − buy-and-hold return × time-in-market`, and every
"excess" column in the original run was withdrawn.

---

## 4. Result 2 — the weekend effect dies on a proper test

The 1h matrix left exactly one candidate: **H-R5, +5.93 bps/trade pooled, PF 1.06,
n=126.** That number is also the most likely artefact in the whole matrix, because
7 symbols × 18 weekends is **not** 126 independent observations — all 7 coins share the
same weekend, so the effective sample is ~18 calendar events.

`proof/weekend_test.py` fixes both problems:

- **3.01 years** of 4h bars (2023-11-18 → 2026-11-22), where the 20:00 UTC bar boundary
  makes entry/exit exact
- **clustered bootstrap by calendar weekend** — resample dates, not trades
- **a control**: all 42 other 48-hour windows (every weekday × 6 start hours), same costs

**Result:**

| | value |
|---|---|
| pooled mean | **−3.21 bps / event** |
| 95% CI (clustered) | **[−67.26, +64.51]** |
| P(mean > 0) | **0.4465** |
| n events | 156 |
| rank among 42 tested 48h windows | **#15** |
| z vs the mean of the other windows | **+0.44** |

The best 48-hour window in the entire 3-year sample is not the weekend at all — it is
**Thursday 16:00 UTC at +36.49 bps**. The worst are Sunday afternoon windows
(Sun 16:00: −55.2 bps).

**Verdict: NOT ESTABLISHED.** The +5.93 bps that survived the 26 bps filter was a
small-sample artifact created by pooling correlated observations. This is the single most
useful result in the run: the one thing that looked like an edge was killed by extending
history and clustering the sample — not by tweaking a parameter.

---

## 5. Result 3 — the live "pretend trading" round, on markets that were open

### 5.1 What the pre-registered book said, live

Every 1h bar close, all six hypotheses are re-evaluated on live bars across all 7 symbols.
Over the session:

| book | scans | qualifying setups | trades opened |
|---|---:|---:|---:|
| pre-registered consensus (≥2 hypotheses agreeing) | 4 full passes | **0** | **0** |

**Why zero.** All six hypotheses are long-biased and five of them require price above a
long moving average (SMA/EMA 200) or a fresh 20-bar breakout. On 2026-11-22 the market
was **25 days into a −27% decline**. Price sat below those averages on every symbol, so
the trend filters were false everywhere:

- H-R1 needs EMA50 > EMA200 — false on all 7 symbols
- H-R3 / H-R6 need close > SMA200 — false on all 7 symbols
- H-R4 needs an ATR squeeze followed by a 12-bar high — never co-occurred
- H-R2 needed a 20-bar breakout — the direction was down, and the short leg needs two
  agreeing hypotheses, which no long-only sibling can provide
- H-R5 only fires Friday 20:00 UTC — it was Sunday

This is the correct behaviour of the system, and it is also the honest answer to "can you
find a profit in a short timeframe": **the pre-registered book declined to trade.** A
system that had produced a trade in that market would have been doing something other
than what it says it does.

### 5.2 Harness validation — real positions, real prices, opened and closed

Because a flat book proves nothing about the machinery, two explicitly-labelled
non-hypothesis books were run on live prices. Both are tagged in the ledger so they can
never be mistaken for evidence.

**SMOKE_TEST** — deterministic one-position-per-symbol, purpose: prove open → mark → close.

| symbol | direction | entry (real ask + 10 bps) | TP | SL | notional |
|---|---|---|---|---|---|
| BTC | LONG | 59,764.10 | 60,276.08 | 59,252.12 | $3,333.33 |
| ETH | LONG | 1,686.09 | 1,700.72 | 1,671.47 | $3,333.33 |
| SOL | LONG | 69.8198 | 70.3975 | 69.2420 | $3,333.33 |

(equities: BTC bid 59,704.30 / ask 59,704.40 at entry — entry = ask × 1.001, so the
spread **and** the taker fee are both paid, exactly as in reality)

**Result — the machinery works, and the result is a loss that is entirely friction:**

| symbol | entry (ask+10bps) | exit (bid−10bps) | gross price move | friction | **net** | P&L | held |
|---|---|---:|---:|---:|---:|---:|---:|
| BTC LONG | 59,764.10 | 59,658.68 | **+2.4 bps** | 20.0 bps | **−17.6 bps** | −$5.88 | 6.2 min |
| ETH LONG | 1,686.09 | 1,682.49 | **−1.4 bps** | 20.0 bps | **−21.4 bps** | −$7.13 | 6.1 min |
| SOL LONG | 69.8198 | 69.6403 | **−5.7 bps** | 20.0 bps | **−25.7 bps** | −$8.57 | 7.0 min |

The book re-entered after each time-stop, so the full round finished with **6 closed
trades, 0 winners, total P&L −$27.79 on $10,000 (−0.278%), $40.00 paid in fees**.

**This is the most useful live result in the run.** Over six minutes the underlying moved
between **−5.7 and +2.4 bps** — i.e. essentially nothing. The round-turn friction took
20 bps regardless, and turned three flat trades into three losses. That is the
certification test T2 (`cost drag 25.4 bps vs expected 26 bps`) reproducing itself against
a live exchange with real bid/ask. The model was not wrong about the world; the world was
flat and the cost was not.

No stop-loss and no take-profit was hit, which is itself informative: with a 1.2×ATR
bracket (~120 bps on BTC), a 6-minute hold will almost never reach either side. **A bracket
that the holding period cannot reach is decoration, not risk management.**

**HARNESS_PROBE_5M_BURST** — a 5m momentum-burst signal, purpose: prove a *signal-driven*
open on live data.

| symbol | direction | entry | TP | SL | signal |
|---|---|---|---|---|---|
| BTC | SHORT | 59,667.07 | 59,283.09 | 59,923.06 | 5m burst > 0.18% on above-median volume |
| ETH | SHORT | 1,682.92 | 1,671.94 | 1,690.23 | same |

**Result — signal-driven, and the same lesson:**

| symbol | direction | entry | exit | exit reason | net | P&L |
|---|---|---:|---:|---|---:|---:|
| BTC | SHORT | 59,667.07 | 59,962.70 | **SL** | −49.6 bps | −$16.52 (R −1.16) |
| ETH | SHORT | 1,682.92 | 1,691.86 | **SL** | −53.2 bps | −$17.72 (R −1.22) |
| SOL | SHORT | 69.6303 | 70.0800 | **SL** | −64.6 bps | −$21.53 (R −1.55) |

All three stopped out within ~4 minutes, for **−$55.76 total**. The reason is clear from
the session context: BTC was **+3.4% on the day**. A 5-minute down-impulse inside a rising
session is noise, not a reversal, and shorting it means being stopped out on the next leg
up. Note the realised loss (−49.6 bps) is **larger than the stop distance** (~43 bps) —
the exit fills at the live bid plus fee, so slippage through the stop is charged rather
than assumed away.

The burst signal correctly identified a downward 5m impulse on all three symbols and
opened shorts at the live bid minus taker fee. Whether that ended in a profit is not the
point — **n=3 proves the signal-to-fill path works, and proves nothing about edge.** It is
recorded here for completeness, not as evidence.

### 5.4 The honest answer to "can you find a profit in a short timeframe"

Across four books on live markets:

| book | trades opened | trades closed | net result |
|---|---:|---:|---|
| pre-registered consensus | **0** | 0 | declined to trade — trend filters false in a −27% market |
| SMOKE_TEST (no signal, deterministic long) | 6 | 6 | **−$27.79 (−0.278%)**, 0% WR |
| HARNESS_PROBE_5M_BURST | 3 | 3 | see table above |

**No.** In a short timeframe, on live markets, this system did not find a profit. The
reason is specific and measurable, not mysterious:

1. **The pre-registered book had nothing to do.** Five of six hypotheses need price above a
   long moving average; the market was 25 days into a −27% decline. Refusing to trade was
   correct behaviour.
2. **When forced to trade anyway, the friction ate everything.** A flat 6-minute market
   still costs 20 bps round turn. To profit in a short timeframe you need an edge *larger
   than the friction per unit time*, which at 20 bps per round trip means roughly 20 bps of
   directional conviction per trade. Nothing in the signal library produces that on a
   6-minute horizon.
3. **The bracket was unreachable.** 1.2×ATR on BTC 1h ≈ 120 bps; a 6-minute hold moves
   ~6 bps. The TP/SL never fires, so every trade resolves on the clock, which guarantees
   the outcome is "friction plus noise".

That third point is the actionable one, and it is now a standing rule in the roadmap:
**the bracket width must be reachable inside the holding period, or the risk model is
fictional.**

### 5.3 Two harness bugs the live run found

1. **Pagination returned 1,000 bars instead of 3,000.** ccxt's `since` is a *start* time;
   the original code passed a time before the oldest bar, which re-returned the same
   window. The first matrix therefore covered 42 days, not 125. Fixed by paging forward
   from a computed start. Every number in §3 was regenerated after the fix.
2. **The burst scanner sampled one bar in three.** It read only the latest closed 5m bar,
   but an iteration takes 1–6 minutes due to exchange rate limits, so most burst bars were
   never seen — the diagnostic showed `max|5m ret|` of 0.70% (BTC) with 3 qualifying bars
   per hour, yet zero signals fired. Fixed by scanning the last 12 closed bars.

Both were found because the live round is a real loop against a real exchange, not a
replay. Neither would have surfaced in a backtest.

---

## 6. Verdict of this round

| question | answer |
|---|---|
| Is any asset class back-test proven profitable here? | **No.** 42 cells, 0 above DSR 0.95, 0 beating the permutation p95. |
| Did any family survive retail friction? | One: weekend effect, +5.93 bps/trade at 26 bps, breakeven ≈35 bps. |
| Did it survive a proper test? | **No.** 3 years, clustered, with controls: −3.21 bps, CI straddles zero, rank #15 of 42. |
| Can the harness be trusted to say no? | **Yes** — 5/5 certification tests pass, including a 60-cell pure-noise calibration at 0/60 false positives. |
| Did the live round open and close real positions? | **Yes**, on live prices, paying spread + taker fee on both legs. |
| Was there a profit? | **No — and the reason is arithmetic, not luck.** Two books traded, both lost: the
no-signal book lost **−0.278%** purely to friction, and the signal book lost **−0.56%**
because it shorted a 5-minute dip inside a +3.4% day. The pre-registered book opened zero
trades, correctly. Full breakdown in §5.4. |
| Would I allocate capital? | **No.** Per the peer verdict this agrees with: hold beta sized to drawdown tolerance; no desk strategy sanctioned. |

---

## 7. What round 2 does about it

Full plan: `docs/ROADMAP_200_deepseek-flash.md` (200 rounds, 10 phases, gate definitions).

Immediate next actions, in order:

1. **Extend the weekend family properly.** It is the only family positive at retail cost.
   Test it as a *portfolio* rule with 156+ events and a per-year breakdown, and test the
   same 48-hour-window structure on equities/ETF (where the weekend gap is a real
   overnight-gap event, not a 24/7 drift).
2. **Add the classes that were closed during this run.** FX opens 17:00 EST and equities
   Monday 09:30 — both are measurable within 24 hours of this document.
3. **Ship the forward pods to GitHub Actions** so `n` accumulates without a human
   (`.github/workflows/realtime-challenge.yml`, 3 runs/hour, ledger committed to git).
4. **Do not re-run the 42 dead cells with new parameters.** They are dead. Re-testing a
   dead family with tweaked TP/SL is how the previous years were lost.

---

## 8. Reproduce any number in this document

```bash
cd 02-portfolio-multi-asset
python -m realtime_challenge.proof.test_harness          # 5/5 certification
python -m realtime_challenge.cli backtest --bars 3000 --permutations 100 --verbose
python -m realtime_challenge.proof.weekend_test          # 3-year clustered + control
python -m realtime_challenge.cli scan                    # what the book says right now
python -m realtime_challenge.cli live --book smoke --minutes 9 --max-minutes 6
```

Raw artifacts: `results/backtest_latest.json`, `results/weekend_test.json`,
`results/harness_certification.json`, `ledger/*.jsonl`.

## 9. Standing disclaimer

No financial advice. No real orders. Every number is a measurement of a paper experiment
against real public market data, with its execution convention and cost model stated
alongside it. Where a number could not be produced honestly, it is absent rather than
estimated.
