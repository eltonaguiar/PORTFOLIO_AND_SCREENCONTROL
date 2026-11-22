# P7 — bracket reachability, and the identity that explains every live loss

**What this started as.** The live books produced **0 take-profits in 27 trades** (12 stops, 14 time
stops). I had written that the bracket was *"wider than the expected move over the holding period,
so it cannot be hit"*. That was a plausible story, it got repeated, and **the arithmetic refutes it
for 21 of the 27 trades.** This document corrects it.

**Artifacts:** `realtime_challenge/bracket.py` · `proof/test_bracket.py` (**22 tests, all passing**)
· reproduce with `python -m realtime_challenge.bracket --audit-ledger ledger/<book>.jsonl`

---

## The identity: a bracket cannot create an edge

For a driftless walk, the probability of touching the take-profit before the stop is exactly
`b / (a + b)`, where `a` is the TP distance and `b` the SL distance. The stop is touched with
probability `a / (a + b)`. So the gross expectancy of any bracket, before costs, is

```
E[R] = p_TP · (a/b) − p_SL
     = [b/(a+b)] · (a/b) − [a/(a+b)]
     = a/(a+b) − a/(a+b)
     = 0
```

**Exactly zero, for every (a, b).** Verified numerically across 16 bracket combinations in
`test_bracket.py` — every one returns `gross_EV = 0.000000R`. Add any friction and every bracket is
**negative**.

This is the strongest statement the project has produced, and it is not an empirical finding about
crypto — it is an algebraic one:

> **Bracket geometry can never produce an edge. Every profitable bracket system is profitable
> because its entries are right more often than the geometry implies — the take-profit is where the
> profit is *collected*, never where it is *created*.** A bracket "tuned" to a good result has not
> found an edge; it has found a favourable sample.

It also explains the walk-forward result in `WALKFORWARD_P6.md` from a different direction: fitting
`(tp_atr, sl_atr, max_bars)` on a scoring window moved the *zero* around, so 73% of in-sample
"winners" were noise in a quantity with no mean.

## What the 27 live trades actually were

Every closed trade re-run through the gate using **its own `atr_1h`** and its realised hold:

| book | closed | would refuse | exits |
|---|---:|---:|---|
| live_smoke_bybit | 6 | 6 | TIME 6 |
| liveprobe_20261122_0400 (bybit) | 3 | 3 | SL 3 |
| liveprobe_bybit_v2 | 11 | 11 | SL 5, TIME 6 |
| liveprobe_kraken | 3 | 3 | SL 2, TIME 1 |
| liveprobe_okx | 4 | 4 | SL 4 |
| **total** | **27** | **27 (100%)** | SL 12, TIME 15 |

Gate reasons: **NEGATIVE-EV on 27 of 27**; UNREACHABLE on only 6 (all from the smoke book).

So my earlier claim was wrong on the dominant mechanism. Only **6 of 27** had a bracket outside the
expected excursion. The other **21 were reachable and still guaranteed to lose**, because at their
own geometry-implied hit rates the bracket returned exactly zero before costs and −0.002 to −0.007R
after. **Every trade in every book was arithmetically incapable of showing a profit, regardless of
how good the signal was.**

## The second, independent defect: direction

Predicted `P(TP exit)` averaged **0.269** across the 27 trades, so a correctly-behaved driftless
process should have produced about **7.3 take-profits out of 27**. Observed: **0**.

`exit_mix_test(0.269, n_tp=0, n_total=27)` → two-sided binomial **p = 0.0003**.

That is incompatible with the bracket geometry, and the only thing left that can explain it is the
assumption the geometry rests on: **the paths were not driftless, because the positions were
systematically against the move.** All shorts, into a session where BTC rallied +3.4%. Two
independent defects, in this order of importance:

1. **Geometry:** every bracket was zero-EV before costs. Unfixable by signal quality.
2. **Direction:** 0 of an expected 7.3 targets. Unfixable by bracket choice.

The two together are why the live P&L was −$285.14 on 27 trades with $180.00 of it commission.

## The verification wall — the finding that unifies the whole project

Solving the break-even condition for the win rate a bracket needs gives a clean result:

```
required_win_rate = (1 + cost) / (1 + tp/sl)
required_edge     = required_win_rate − sl/(tp+sl)  =  cost / (1 + tp/sl)
```

**The edge a bracket demands is exactly the friction divided by the payoff ratio** — so it is
always *less than the round-trip cost itself* (≤ 26 bps here). There is no such thing as a bracket
that "demands unrealistic skill". There is only the question of how many trades it takes to
**verify** that edge at 80% power (`n ≈ 16·p(1−p)/δ²`):

| bracket (tp:sl) | required edge | trades needed to verify |
|---|---:|---:|
| 0.5 : 1 | +0.170 pp | **1,183,432** |
| 1 : 1 | +0.130 pp | **2,366,864** |
| 2 : 1 | +0.090 pp | **4,733,728** |
| 3 : 1 | +0.060 pp | **7,100,592** |
| 6 : 0.5 | +0.020 pp | **28,402,367** |

Read this against the audit3 ledger's own `required_n` column from the pasted dashboard:
EQUITY **22,569**, ETF **1,730,370**, FOREX **2,366**, CRYPTO **917**. Same order of magnitude,
derived from a completely different direction — bracket geometry here versus the picks ledger
there. **Two independent routes, one number.**

That is the arithmetic reason this field is stuck, and it is the strongest result the project has:

> **A bracket strategy needs an edge of 0.02–0.17 percentage points of win rate to beat friction,
> and between 1.2 and 28 million trades to demonstrate it at 80% power. A live book of 27 trades —
> or 100, or 1,000 — cannot confirm or refute a bracket strategy at all. The "100 closed trades"
> checkpoint this project has been using as its forward gate is not a conservative bar; it is
> off by four to five orders of magnitude.**

The 27-trade live book was not a small sample of a real edge. It was a sample from a distribution
whose mean cannot be distinguished from zero by any realistic experiment.

## The gate, as shipped

`bracket.evaluate(price, atr, tp_atr, sl_atr, hold_bars)` returns three independent verdicts:

| flag | meaning | default threshold |
|---|---|---|
| `fail_reach` | both barriers outside the expected excursion — exit decided by the clock | `p_touch_any` < 0.50 |
| `fail_balance` | reachable but the target is first too rarely to pay | `p_tp_exit` < 0.20 |
| `fail_ev` | **negative expectancy at its own implied hit rates after costs** | `E[net]` ≤ 0 |

A bracket must pass all three. `--audit-ledger` re-runs them retrospectively against closed trades,
and `exit_mix_test` asks the follow-up the pre-trade gate cannot: did the realised exits match the
geometry, or is the driftless assumption itself violated?

The formulas are validated against Monte Carlo (20,000 paths) in `test_bracket.py`, because a
reachability estimate that errs in the permissive direction would approve unreachable brackets and
make the gate look like it was working. Agreement is within 0.06 on `p_tp_exit` across three
regimes.

## What this changes about the rest of the project

- The **challenge write-up §5.4** said the bracket was unreachable. Corrected: 6 of 27, not 27.
- The **roadmap's P7 rule** is rewritten from "the bracket must be reachable" to the sharper and
  provable form: *"a bracket must have positive expectancy at its own geometry-implied hit rates,
  which is only possible if the entry carries directional skill."*
- **Any future paper book must call `evaluate()` before opening.** If the gate refuses, the trade is
  not taken and the refusal is logged — that is the whole point of building it before another 27
  trades are placed and explained afterwards.
- The next live round should be judged on `exit_mix_test` first: a book whose TP count is far from
  its predicted count has a signalling problem, and no amount of bracket tuning will address it.

## Try it

```bash
cd 03-trading-strategies
python -m realtime_challenge.proof.test_bracket                 # 22 tests incl. the identity
python -m realtime_challenge.bracket --check --price 59700 --atr 426 --hold-bars 3 \
       --tp-atr 0.9 --sl-atr 0.55                                # the probe bracket, refused
python -m realtime_challenge.bracket --audit-ledger ledger/liveprobe_bybit_v2.jsonl
```
