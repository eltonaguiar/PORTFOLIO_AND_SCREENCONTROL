# Harness certification — can this engine be trusted to say "no"?

Run: `python -m realtime_challenge.proof.test_harness`
Artifact: `results/harness_certification.json`
Last run: **2026-11-22, 5/5 passed**

A backtester that cannot return a negative is worthless, and one whose defaults are
optimistic will manufacture a positive. So before any strategy verdict is quoted, the
engine itself is tested. Each test below can fail, and each failure means the same
thing: no number produced downstream is publishable.

| test | what it proves | result |
|---|---|---|
| **T1a** look-ahead is detectable | a rule that peeks at the next bar scores dramatically better than the honest version of the same rule — which proves the honest version is not accidentally peeking | **PASS** — peeking `+36.7bps`/trade vs honest `−3.5bps` |
| **T1b** signals are causal | truncating all bars after `i` leaves every signal at `≤ i` unchanged | **PASS** |
| **T2** cost drag matches the round turn | a zero-information coin-flip strategy loses ≈ the 26 bps round turn per trade. Too little loss = friction not charged; too much = double counting | **PASS** — drag `25.4bps` vs expected `26bps`, n=1665 |
| **T3** both-touched bar resolves to the stop | a bar whose high clears the take-profit and whose low clears the stop is booked as a **stop-out**, not a win | **PASS** — `exit_reason=SL` |
| **T4** pure noise almost never clears the significance bar | 60 random strategies, deflated Sharpe at 0.95. If noise passes, the statistics layer is broken | **PASS** — `0/60` at DSR ≥ 0.95, max DSR `0.0017` |

## Why each of these exists

**T1 (look-ahead).** The single most common way a trading backtest lies. Common forms:
using the signal bar's own close as the fill price; `shift(-1)` anywhere; computing a
rolling statistic over a window that includes the future; rebalancing on a bar that has
not closed. The engine avoids all of these structurally — the fill loop starts at
`signal_index + 1` and reads `open[i+1]` — and T1 proves the avoidance rather than
asserting it.

**T2 (costs).** At retail crypto cost (10 bps taker + 3 bps slippage each side) a
strategy pays ~26 bps per round trip. A daily-turnover strategy therefore needs ~26 bps
of gross edge per trade before it is even flat. T2 confirms the engine actually charges
it. The measured 25.4 bps rather than 26.0 is expected: the TP/SL bracket truncates the
return distribution, so the arithmetic mean drag is slightly below the nominal cost.

**T3 (intrabar ambiguity).** OHLC bars do not tell you the *order* in which the high and
low were visited. Any engine that resolves a both-touched bar in favour of the
take-profit is quietly inventing a win. This one resolves it as a loss, always. The cost
of that choice is real — some genuine wins are booked as losses — and it is the right
direction to be wrong in.

**T4 (multiple testing).** 42 cells were tested in the 1h matrix and 156 weekend events
in the 3-year test. At that width, some cells *will* look good by chance. The deflated
Sharpe penalises the observed Sharpe by the expected maximum Sharpe from N independent
trials. T4 shows the implementation actually rejects noise; without it, a DSR of 0.07
would be uninterpretable.

## What the certification does NOT prove

- **No slippage calibration.** 3 bps per side is an assumption, not a measurement. Live
  pods record real bid/ask so this can be replaced with observed data later.
- **No maker-fill modelling.** Everything is a taker fill. A maker strategy would need
  queue-position modelling (see `nkaz001/hftbacktest` in `LIBRARY_SURVEY.md`).
- **Adjusted vs raw prices.** Crypto has no splits/dividends, so this is clean here.
  Equities are *not* clean — unadjusted closes will corrupt any equity test.
- **Survivorship.** The universe is 7 majors chosen today. That is a selection, and it
  is stated rather than hidden.
