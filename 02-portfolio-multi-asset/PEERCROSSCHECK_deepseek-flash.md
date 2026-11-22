# Peer cross-check — `deepseek-flash`, 2026-11-22

The instruction was: *"your peers will also be doing the same, so part of your plan
cross-check their work too."* This file records what existed, what was checked, and where
this work disagrees with it. Numbers are read out of files with paths; nothing is quoted
from a prior chat.

## 1. What was already in the repo when this run started

| artifact | path | verdict |
|---|---|---|
| 2-hour challenge, V1 | `2hour_challenge.py` | superseded |
| 2-hour challenge, live | `2hour_challenge_live.py` | **flawed — see §2** |
| 2-hour challenge, V2/V3 | `alpha_engine/challenge_v2.py`, `challenge_v3.py` | **flawed — see §2** |
| challenge result | `REAL_CHALLENGE_FINAL.md` | **not evidence — see §2** |
| challenge report | `PROP_FIRM_CHALLENGE_STRATEGIES.md` | strategy catalogue, no verdict |
| capital-allocation verdict | `reports/2026-11-22-capital-allocation-verdict.md` (commit `1bfc7c6bab`) | **agreed with, see §3** |
| negative-knowledge denylist | `alpha_engine/negative_knowledge_registry.py` | **adopted into this harness, see §4** |
| live workflow | `.github/workflows/2hour_challenge.yml` | runs the flawed script |

No `REALTIMECHALLENGE_*.MD` file existed from any peer at the time of writing, so this
document cross-checks the *prior* challenge implementation and the current verdict docs
rather than a sibling challenge file.

## 2. The existing challenge is not evidence — line-level findings

`REAL_CHALLENGE_FINAL.md` reports a winner:

> 🥇 WINNER: VWAP_Scalping_AAPL — Final P&L: $123.32, Return +1.23%, **Total Trades: 2**

and the full standings show the other three strategies at **0 trades** and one at 1 trade
(`REAL_CHALLENGE_RESULTS.json` confirms `"trades": 0` for `news_scalping` and
`funding_arb`).

That is a selection artefact, and it is the exact failure mode this whole programme
exists to prevent:

1. **n = 2.** Two trades cannot distinguish +1.23% from luck. The standard error on a
   2-trade sample of a process with ~1% per-trade volatility is ~0.7%, so the result is
   ~1.7σ — not significant even before correcting for four strategies being compared.
2. **It "won" by being the only entrant that traded.** Three of four strategies were
   flat. The ranking compares a 2-trade sample against three 0-trade samples.
3. **No cost model.** `grep -cnE '0\.001|fee|commission|slippage|spread'` returns **0**
   occurrences in `alpha_engine/challenge_v3.py`. The +1.23% is gross. At 26 bps round
   turn, two round trips cost 0.52% — a third of the reported P&L would disappear.
4. **Entries are priced at the signal bar's own price.** `2hour_challenge_live.py` uses
   `'entry_price': data['price']` where `price` is the current mid/last, with no
   next-bar lag. That is a same-time fill and is the classic look-ahead for intraday
   rules.
5. **Fixed-percentage brackets, not volatility-scaled.** `stop = price * 0.985`,
   `target = price * 1.03` — identical for BTC and for a small-cap, which is not a
   risk model.

**Conclusion:** the +1.23% headline is an anecdote. It should not be quoted as a win
rate, an edge, or a comparison. It is not evidence of anything, positive or negative.

## 3. Agreement with the peer capital-allocation verdict

`reports/2026-11-22-capital-allocation-verdict.md` (commit `1bfc7c6bab`) states:
34 pre-registered cells across 10 classes, one (`EQUITY xsmom_top3_6m`, H-201) clearing
the backtest gates with **zero closed forward trades**; SPY buy-and-hold at 10.27% CAGR
with a −55.2% drawdown; **no desk strategy sanctioned for real capital**.

This work **agrees** and adds one independent data point to it:

| claim | peer | this run | agrees? |
|---|---|---|---|
| No crypto strategy has forward evidence | stated | 42 cells tested, **0** with DSR > 0.95, **0** with permutation p < 0.05 | **yes** |
| Friction kills intraday cells | stated | every 1h family is negative at 26 bps; the one positive pooled family (weekend) dies by 40 bps | **yes** |
| The only defensible default is beta sized to drawdown tolerance | stated | not re-tested here — outside this run's scope | n/a |

Three of the peer's rows were flagged as non-reproducing in their own doc (SPY terminal
value, max drawdown, trend-overlay result). This run did **not** re-derive them; they
remain open in `ROADMAP_200` rounds R191–R192.

## 4. Adopting the denylist (closing the "audit only deletes" gap)

`alpha_engine/negative_knowledge_registry.py` documents dead families:

- `BLOCKED_SYMBOLS` includes `AVAXUSDT` (PF 0.82, n=37, intrabar replay), `TRXUSDT`, `MATICUSDT`
- `BLOCKED_HOURS_UTC = {2, 8, 13, 20}` — those hours had < 35% WR historically
- `RR_BLOCK_THRESHOLD = 2.5` — R:R above 2.5 was anti-predictive (30.6% WR)

All three are **enforced in code** in this harness rather than merely described:

- `live.BLOCKED_BASES = {"AVAX", "TRX", "MATIC"}` — refused at open, logged as `SKIP:BLOCKED_SYMBOL`
- `strategies._block_hours()` — zeroes any signal stamped in the dead hours
- `strategies.py` asserts `tp_atr / sl_atr <= 2.5` at import time, so a future author
  cannot quietly add a 3:1 bracket

That import-time assertion is the mechanism that prevents the exact regression the
registry was written to stop.

## 5. Where this work contradicts the repo's own habits

| repo habit | this harness | why |
|---|---|---|
| Report WR/PF on n as low as 2 | refuses to compute DSR below n=10; reports CI instead of a point estimate | a point estimate at n=2 is a coin flip wearing a percentage |
| Compare a flat strategy to buy-and-hold in a falling market | reports `excess_scaled` = strategy return − B&H × time-in-market | otherwise "did nothing" scores as +28% alpha in a bear window |
| Pool trades across symbols into one n | clusters calendar-driven signals by the calendar event | 7 coins sharing one weekend are ~1 observation, not 7 |
| Sweep parameters until something passes | 6 hypotheses, frozen params, trial count recorded | the trial count is the number nobody records |
| Dashboard PF as the headline | ledger with a computed timestamp, reconciled per trade | a doc can be months old; the ledger is today |

## 6. Peer-work checklist for the next round

- [ ] Re-read `reports/` for any verdict published after 2026-11-22 09:00 UTC
- [ ] Diff this run's `weekend_test.json` against any peer weekend/crypto result
- [ ] If a peer publishes a `REALTIMECHALLENGE_*.MD`, reconcile the live ledger numbers,
      not the prose
- [ ] Refuse to merge a peer's PF into this book without a matching `execution_convention`
      and `round_turn` field
