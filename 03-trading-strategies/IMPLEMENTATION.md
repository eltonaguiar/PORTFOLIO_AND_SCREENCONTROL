# Financial portfolio tracking — multiple asset classes

Backtesting, paper trading and portfolio evidence for stocks, bonds, ETFs, mutual funds,
commodities, FX — **and right now, crypto**, because it is the only class open 24/7 and
therefore the only one that can be traded live on a Sunday at 04:00 EST.

## Contents

```
realtime_challenge/
  costs.py       friction as a first-class object (26 bps round turn default)
  data.py        ccxt public OHLCV, paginated, cached; 5-venue live quote consensus
  engine.py      event-driven replay, pessimistic by construction
  strategies.py  6 pre-registered hypotheses, frozen params, desk denylist wired in
  stats.py       PF, expectancy in R, bootstrap CI, deflated Sharpe, permutation control
  live.py        the live paper round (real bid/ask, taker fee both legs)
  ledger.py      append-only JSONL + rebuildable state
  worker/        forward_supervisor.py — one non-interactive pass for GitHub Actions
  proof/         test_harness.py (5 certifications) · weekend_test.py (3-year clustered)
docs/            challenge write-up · 200-round roadmap · certification · peer cross-check · library survey
results/         every JSON artifact the numbers above were read from
ledger/          the live rounds' append-only event logs
```

## The execution convention (non-negotiable, and why)

| rule | reason |
|---|---|
| signal on the **close** of bar *t*, fill at the **open of bar *t+1*** | same-bar fills are the single largest source of fake intraday edge |
| taker fee **and** slippage on **both** legs, always | a zero-cost backtest is not a backtest |
| a bar touching both TP and SL resolves to the **stop** | OHLC bars do not encode visit order; resolving the tie as a win is inventing it |
| risk 1% of equity at the stop, capped at 1× notional | position sizing is part of the strategy, not an afterthought |
| no parameter sweeps; the trial count is recorded and deflates every Sharpe | the trial count is the number nobody records |
| benchmark is buy-and-hold **scaled by time-in-market** | being flat in a crash is not alpha |

## Quick start

```bash
# 1. certify the engine (must be 5/5 before any number is quoted)
python -m realtime_challenge.proof.test_harness

# 2. the 1h matrix: 7 symbols x 6 hypotheses, cost grid, permutation control
python -m realtime_challenge.cli backtest --bars 3000 --permutations 100 --verbose

# 3. the clustered 3-year re-test of the only surviving family
python -m realtime_challenge.proof.weekend_test

# 4. what the book says right now
python -m realtime_challenge.cli scan

# 5. a live paper round (opens and closes real positions on real prices)
python -m realtime_challenge.cli live --book smoke --minutes 9 --max-minutes 6
python -m realtime_challenge.cli live --book probe --burst 0.0018 --minutes 22
```

No API keys are required for any of the above: every price is a public exchange endpoint,
and no order is ever sent.

## Asset-class coverage plan

| class | measurable now? | note |
|---|---|---|
| crypto spot (1h/4h/1d) | **yes**, 24/7 | this run |
| crypto funding / basis | yes, needs funding endpoints | roadmap R21–R23 |
| FX majors | **opens 17:00 EST Sunday** | roadmap R24–R27; needs session-aware bars |
| US equity ETFs | opens Mon 09:30 EST | roadmap R28–R31; overnight gap is the whole story |
| single-name equities | yes, with borrow/short constraints | roadmap R32–R34 |
| commodities via ETFs | contaminated by roll | roadmap R35–R36 — repair or formally retire |
| bonds / rates | yes, low vol, friction-sensitive | roadmap R37–R38 |
| prediction markets | structurally zero-sum for a taker | roadmap R39 — test maker-only or drop |

## The one rule

If a number does not name its execution convention, its cost model and its sample size, it
is not a result. It is an anecdote wearing a percentage sign.

Nothing here is financial advice.
