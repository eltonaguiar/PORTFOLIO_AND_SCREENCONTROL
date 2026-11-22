# 03 — Trading strategies, backtests and paper trading

The **evidence layer**. Everything here answers one question and refuses to answer a
different one:

> Would this rule have made money under realistic costs, and is that answer real — or is it
> the maximum of a search?

It is deliberately separate from [`../02-portfolio-multi-asset/`](../02-portfolio-multi-asset/),
which answers "what do I own and what is it worth". A portfolio tracker and a strategy
harness are different instruments, and the most common error in this domain is quoting a
tracker's profit factor as evidence of edge.

---

## Contents

| file / dir | what it is |
|---|---|
| [`realtime_challenge/`](realtime_challenge/) | the running harness: costs · data · engine · 6 pre-registered strategies · stats · live round · ledger · GH Actions worker · 2 proof suites |
| [`REALTIMECHALLENGE_deepseek-flash_2026-11-22_0356_EST.MD`](REALTIMECHALLENGE_deepseek-flash_2026-11-22_0356_EST.MD) | **the challenge write-up** — setup, results, the live round, the verdict |
| [`TIMEFRAME_MATRIX.md`](TIMEFRAME_MATRIX.md) | **the class census** — 126 cells across 1h/4h/1d, per-family results, the horizon flip, and what it changes in the plan |
| [`ROADMAP_200_deepseek-flash.md`](ROADMAP_200_deepseek-flash.md) | 200 rounds, 10 phases, explicit gates and kill conditions |
| [`HARNESS_CERTIFICATION.md`](HARNESS_CERTIFICATION.md) | the 5 tests that make the engine allowed to say "no" |
| [`PEERCROSSCHECK_deepseek-flash.md`](PEERCROSSCHECK_deepseek-flash.md) | line-level audit of prior work + reconciliation with peers that landed mid-session |
| [`LIBRARY_SURVEY.md`](LIBRARY_SURVEY.md) | 20 backtesting/paper-trading repos, star/push/licence verified via the GitHub API |
| [`IMPLEMENTATION.md`](IMPLEMENTATION.md) | how to run it, and its honest limitations |
| [`PROGRESS.md`](PROGRESS.md) | **the running log** — appended every session |
| `results/`, `ledger/` | every JSON and every append-only event log a number was read from |

---

## The six rules the harness enforces in code

1. **Signals on closed bars only; fills at the next bar's open.** Same-bar fills are the
   single largest source of fake intraday edge.
2. **Taker fee + slippage on both legs, always.** 26 bps round turn by default. No
   zero-cost backtest is reachable.
3. **A bar touching both TP and SL resolves to the STOP.** OHLC bars do not encode visit
   order; resolving the tie as a win is inventing it.
4. **Risk 1% of equity at the stop**, capped at 1× notional.
5. **No parameter sweeps.** Six hypotheses, frozen parameters, and the trial count is
   recorded and fed into a deflated Sharpe.
6. **The benchmark is buy-and-hold scaled by time-in-market.** Being flat in a crash is
   not alpha.

Each of these has a failing test that proves it works — see
[`HARNESS_CERTIFICATION.md`](HARNESS_CERTIFICATION.md). 5/5 currently pass, including a
60-cell pure-noise calibration that produces **0** false positives.

---

## Result after the first run — a clean negative

| question | answer |
|---|---|
| Any asset class back-test proven profitable? | **No.** **126 cells** (7 majors × 6 hypotheses × 3 timeframes), 0 above deflated Sharpe 0.95, 0 beating the permutation control. Best DSR per horizon: 0.071 / 0.256 / 0.183 |
| Anything survive 26 bps friction? | One family: the crypto weekend effect, +5.9 bps/trade, breakeven ≈35 bps |
| Did it survive a proper test? | **No.** 3.0 years, bootstrapped **by calendar weekend**, with all 42 other 48-hour windows as controls → **−3.21 bps**, CI [−67.3, +64.5], rank **#15 of 42** |
| Did the live paper round trade? | The pre-registered book opened **0** trades — correctly, the market was 25 days into a −27% decline and every long filter was false |
| Did the forced books make money? | **No.** The no-signal book lost **−0.278%** (0/6 winners, $40 fees — exactly the friction); the signal book lost **−0.56%** shorting a 5-min dip inside a +3.4% day |
| Did any horizon hide an edge? | **No, but one flip is real and disconfirmed.** H-R4 vol-compression goes from −32 bps at 1h to **+20 bps at 1d** — and its permutation p=0.40 says the effect reproduces on shuffled prices, i.e. it is the bracket, not the market |

The negative is the deliverable. It is cheaper than discovering it live with money.

---

## Run it

```bash
cd 03-trading-strategies
python -m realtime_challenge.proof.test_harness        # must be 5/5 before quoting anything
python -m realtime_challenge.cli backtest --bars 3000 --permutations 100 --verbose
python -m realtime_challenge.proof.weekend_test        # 3-year clustered test + 42 controls
python -m realtime_challenge.cli scan                  # what the book says right now
python -m realtime_challenge.cli live --book smoke --minutes 9 --max-minutes 6
```

No API keys. No order is ever sent. Every price is a public exchange endpoint.

## Continuous operation

`.github/workflows/realtime-challenge.yml` runs the forward pod **hourly**: it marks open
positions, enforces TP/SL/time-stop, opens at most one new position on the pre-registered
book, and commits the ledger back to this repository. Venue failover covers cloud IPs being
blocked by Bybit/OKX (GitHub runners reach **kraken**; verified).

Because the pod supervises hourly, brackets must be *survivable across one supervision gap*
— see the rule in [`ROADMAP_200_deepseek-flash.md`](ROADMAP_200_deepseek-flash.md) P7. A
bracket narrower than the move the market can make while nobody is watching is not a stop.

## Assets covered and planned

Crypto spot is measured now (24/7). FX opens 17:00 EST Sunday; US equities Monday 09:30.
Bonds, mutual funds, commodities and prediction markets are scheduled in
`ROADMAP_200_deepseek-flash.md` P1 with an explicit measurability test per class.

Nothing here is financial advice.

---

## Contract before any run

Every strategy in this folder must satisfy [`STRATEGY_SPEC.md`](STRATEGY_SPEC.md) before it can be
backtested, monitored or paper-traded: a declared hypothesis, a data snapshot hash, a cost model, gates
G1–G8 (causality, cost drag, intrabar conflict, purged walk-forward, deflation, plateau, portfolio), and a
manifest next to every result.

Rules that apply to every round:

1. **No live orders, no credentials.** Paper only.
2. **Every result carries a manifest** — code ref, data snapshot, period, costs, assumptions, benchmark, OOS.
3. **Count your trials** — a leaderboard row without its denominator is not a result.
4. **Label evidence** `observed` / `derived` / `assumed`, and say "not verified" when it isn't.
5. **A failed round is still a result** — publish it with the reason (chop, stop-out, data gap, fee drag).

## Plan reviews from other models

[`GPT5NANO_REVIEW.md`](GPT5NANO_REVIEW.md) audits the GPT-5-nano challenge plan against this repo's harness
and evidence rules. Model-answer audits (Grok, Mercury, SUB Q, Arena, Perplexity, GLM, Gemini) live in
[`../REVIEWS/`](../REVIEWS/).
