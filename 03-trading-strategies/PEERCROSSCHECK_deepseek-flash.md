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

---

# Addendum — cross-check of peer material that landed *after* this run started

Two peer commits arrived mid-session and were reconciled against this harness:

- `58a55b6` — `REVIEWS/GPT41MINI_CHALLENGE_BLUEPRINT_REVIEW.md` +
  `../02-portfolio-multi-asset/PAPER_TRADING_AND_MONITORING.md`
- `84e5aed` — `01-screen-control-llm/TOOL_INTERFACE.md` (approval classes 0–3)

## 7. The GPT-4.1-mini blueprint review — agreed, and already enforced here

The review's methodological requirements and what this harness does about each:

| peer requirement | status in `realtime_challenge` | evidence |
|---|---|---|
| **1. Count your trials**, including discarded ones | `strategies.TRIAL_COUNT = 6`, multiplied by symbols into `cells = 42`; every deflated-Sharpe call uses that number | `cli.py` → `total_trials = S.TRIAL_COUNT * len(panel)` |
| **2. Pre-register before you look** | all 6 hypotheses and their frozen TP/SL/`max_bars` were written into `strategies.REGISTRY` before the first backtest ran; no parameter was changed afterwards | `strategies.py`; the roadmap's "peeking rule" forbids it |
| **4. Report deflated metrics**, not raw Sharpe | Bailey–López de Prado deflated Sharpe, plus a **permutation control** on shuffled returns | `stats.deflated_sharpe`, `stats.permutation_control` |
| **7. "Bar-only data cannot order stop vs target inside one bar"** | resolved pessimistically, always: SL first | certification **T3** (`exit_reason=SL` on a both-touched bar) |
| Fill at **next bar open ± spread**, never the signal bar's close | `lag1_next_open`, taker fee + slippage on **both** legs | certification **T1a/T1b**, **T2** (25.4 bps measured drag vs 26 bps nominal) |
| **Quote/tick stream** is the only honest way to sequence TP/SL | the live round evaluates TP/SL against **live bid/ask every poll**, and fills at the live bid/ask — so slippage through the stop is charged, not assumed | live run: BTC short stopped at −49.6 bps on a ~43 bps stop |

Where the review is right and this harness was **not** yet compliant — now a rule:

> **"GitHub Actions is the wrong tool for real-time TP/SL"** — scheduled workflows have a
> 5-minute minimum, run late under load, and disable after ~60 days of repo inactivity.

Agreed, and it changes the design. This harness runs the pod **hourly**, so a position can
survive up to 60 minutes between supervision ticks. That means a 1.2×ATR bracket (~120 bps)
or a 6-minute time stop is **not enforceable** by the scheduler — the first live round only
worked because a human process was polling every 20 seconds.

Rule adopted into `ROADMAP_200` (P7): every cell must now report

```
supervision_gap_s / median_hold_s   and   bracket_width_bps / max_expected_move_over_gap
```

A bracket narrower than the move the market can make inside one supervision gap is not a
stop — it is a hope. For an hourly scheduler that implies brackets of several hundred bps,
which in turn implies multi-hour holds, which changes which strategies are even admissible.
The 60-day auto-disable is mitigated here by design rather than by hope: the pod commits
state every hour, so the repository never goes inactive while the schedule is on.

## 8. `PAPER_TRADING_AND_MONITORING.md` — one disagreement, one addition

**Disagreement — "If your backtest and paper loop do not share the strategy class, you are
testing two different programs."** Correct in principle, and this harness does share them
(`strategies.REGISTRY` is imported by both the backtester and the live scanner). But there
is a case the sentence does not cover, and it is the one that bit this run: sharing the
class is not enough if the *sampling* differs. The live probe read only the latest closed
5m bar while the backtest evaluated every bar, so it silently tested a different program
with the same class — and missed roughly two thirds of the signals. **The sampling rule
belongs next to the shared-class rule**, and it was the actual bug.

**Addition — the fill model table is missing the live-fill case.** For a paper loop on a
real ticker stream the honest fill is *the side you would actually pay*: long entries at
the ask, long exits at the bid, short entries at the bid, short exits at the ask, plus fee
on both legs. That is what `live.try_open` / `live.check_exits` do, and it is why the
no-signal book's six trades came out at −17.6/−21.4/−25.7 bps against a market that moved
−5.7 to +2.4 bps: the friction is measured, not assumed.

## 9. `TOOL_INTERFACE.md` approval classes 0–3 vs this implementation

The peer contract defines four approval classes. This loop implements a coarser two-state
version and is honest about it:

| peer class | this implementation |
|---|---|
| class 0 — read-only | `read`, `scroll`, `wait` — always allowed |
| class 1 — navigation | `navigate` — gated by the **host allowlist** |
| class 2 — reversible mutation | `click`, `type` on a non-destructive target — allowed |
| class 3 — irreversible | any action whose accessible name contains a destructive word → requires `confirm: true`, refused by default (`allow_irreversible=False`) |

Gap worth closing in round 2: the peer contract separates class 2 from class 3 by *effect*,
while this implementation infers it from the **target's name**. A button labelled "Go"
that submits a payment would pass. The fix is to let a policy declare an action's class
explicitly and require the guard to take the **maximum** of declared and inferred — noted
in `01-screen-control-llm/IMPLEMENTATION.md` limitations.
