# PROGRESS — trading strategies / backtests / paper trading

Append-only running log. Every row must point at an artifact in this folder; a row with no
artifact is a claim, not progress. Newest session at the top.

Legend for **status**: `RUN` executed · `PASS`/`FAIL` gate result · `FIX` defect found and
fixed · `DOC` written · `PEER` reconciliation with another agent's work.

---

## Session 2 — 2026-11-22 (09:30–09:45 UTC) — `deepseek-flash`

Question: does the verdict hold at other horizons, or was 1h hiding something?

| time (UTC) | status | item | artifact |
|---|---|---|---|
| 09:31 | RUN | 4h census: 7 majors × 6 × 4,000 bars (2025-01-24 → 2026-11-22, 22 months) | `results/backtest_binance_4h_20261122T093118Z.json` |
| 09:31 | RUN | 1d census: 7 majors × 6 × 1,200 bars (2023-08-11 → 2026-11-22, 3.3 y) | `results/backtest_binance_1d_20261122T093116Z.json` |
| 09:33 | FAIL | Across **126 cells** at three horizons, nothing clears DSR 0.95. Best deflated Sharpe per timeframe: 1h **0.071**, 4h **0.256**, 1d **0.183** | `TIMEFRAME_MATRIX.md` §3 |
| 09:33 | PASS | Permutation control holds at every horizon — best p-value 0.20 (1h) / 0.28 (4h) / 0.40 (1d). No cell beats a shuffled price path | `TIMEFRAME_MATRIX.md` §3 |
| 09:34 | RUN | **Horizon flip found:** H-R4 vol_compression is the worst family at 1h (−32.1 bps) and the best at 1d (**+20.4 bps**, PF 1.075, n=119). Mechanically plausible: 36 bars vs 36 days to let the expansion pay for the round trip | `TIMEFRAME_MATRIX.md` §4 |
| 09:34 | FAIL | …but H-R4 1d still fails: bootstrap 95% CI on mean trade return **[−87.90, +132.99]**, P(>0)=0.646, pooled DSR 0.0118, permutation **p=0.40**. On *shuffled* returns the same rule reproduces the mean, so the +20 bps is a bracket/timing property, not market structure | `TIMEFRAME_MATRIX.md` §4 |
| 09:35 | FIX | `backtest_latest.json` was silently overwritten by whichever timeframe finished last, making a committed artifact ambiguous about what it measured. Now writes `backtest_latest_<tf>.json` alongside the timestamped copy | `realtime_challenge/cli.py` |
| 09:36 | DOC | Timeframe matrix written: windows and power, pooled per-family table, significance table, the horizon flip with its disconfirming evidence, and what it changes in the plan | `TIMEFRAME_MATRIX.md` |
| 09:42 | FIX | **Data integrity:** `results/` still held `backtest_binance_1h_20261122T090644Z.json` — an artifact from the *pagination-bug* run (1,000 bars, 42-day window). A committed JSON with the wrong window is indistinguishable from a correct one to anyone who does not read the `bars` field. Removed, not caveated | `results/` |
| 09:42 | FIX | `backtest_latest.json` was still present and held the **4h** run under a timeframe-free name — the exact ambiguity I had just patched `cli.py` to prevent. Removed; each timeframe now has only `backtest_latest_<tf>.json` | `results/` |
| 09:42 | FIX | The 1h/4h/1d runs all predate the `cli.py` patch, so no `backtest_latest_<tf>.json` existed. Copied each verified timestamped artifact to its per-timeframe name — a copy, **not a re-run**; no number was re-derived | `results/backtest_latest_{1h,4h,1d}.json` |
| 09:43 | DOC | **New finding from the batch of earlier runs:** the weekend family returned **−162.5 bps** (42 obs, 42-day window), **+5.93 bps** (126 obs, 125 days), **−3.21 bps** (156 clustered events, 3.01 years) on the same rule at the same 26 bps cost. A spread from −162 to +6 bps is a mean a short sample cannot locate — and the +5.93 figure is the one that cleared friction and would have justified a forward pod | `TIMEFRAME_MATRIX.md` §4b |

| 09:52 | PEER | Audited the Subq stack note via the GitHub API: `agent-desktop` 26,040★, Browser MCP 7,398★, `bt` 3,045★, `OptimalPortfolios` 99★ all accurate; **Windows-MCP is 11,999★, not the stated ~6,750**; **backtrader (push 2024-08-19) and qstrader (2024-06-30) recommended as the validation and portfolio layers without disclosing they are 2+ years stale** | `../REVIEWS/SUBQ_STACK_RECOMMENDATION_REVIEW.md` §1 |
| 09:53 | RUN | **Tested the note's headline claim** ("combining strategies improves risk-adjusted return 30-50%") on our own trades: 6 hypotheses × 7 majors, 1d, 3.3 y, 26 bps, daily mark-to-market where a flat day is 0.0% | `realtime_challenge/proof/portfolio_combination.py`, `results/portfolio_combination.json` |
| 09:53 | FAIL | **Claim does not reproduce.** Combined Sharpe **−0.123** vs best single (H-R4) **+0.243** = **−150.6%**. Average pairwise correlation 0.105 and diversification ratio **1.841** — the mix genuinely is far less volatile (4.7% vs 7.4-17.9% annualised) and it still lost. Only **2 of 6** strategies had positive Sharpe | `results/portfolio_combination.json` |
| 09:53 | DOC | Conclusion recorded: diversification reduces variance, it does not create expected return. Portfolio construction is downstream of per-strategy edge — combining four negative-expectancy families with two positive ones yields a diversified near-zero (−2.27% over 3.3 years) | `../REVIEWS/SUBQ_STACK_RECOMMENDATION_REVIEW.md` §3 |
| 09:54 | FIX | The note's multi-asset-vs-portfolio distinction exposed a **real gap I own**: this harness sizes each symbol independently with no shared cash constraint. Mitigated by the pod's `max_open = 4`, but a per-bar shared-cash simulation is still missing (roadmap P5 R157-R160) | `ROADMAP_200_deepseek-flash.md` P5 |
| 09:54 | DOC | `portfolio_combination.py` is a **permanent** portfolio-layer check, not a one-off rebuttal; added qstrader to the avoid list with its verified push date | `realtime_challenge/proof/`, `LIBRARY_SURVEY.md` |

| 09:36 | PEER | Registered on the COMS fleet bus as `inbox/desktop-081g9oh/pasc/hermes-deepseek-flash` (broker 192.168.2.52:1883, ~50 seats). Read before broadcasting: Mercury3 PART13 and subq-savant-1-4 were both already active on this | `coms.ps1 roster` |
| 09:38 | PEER | **Mercury3 PART13 replicated independently**: their 30-symbol 5m run gives gross +28.02 pct, fees 250.80 pct, net -222.78 pct, +2.2bps/trade needing >=12bps, best-case edge/cost 0.56 vs a 3.0 bar. Same mechanism reached here from a different universe, fill convention and codebase | `../03-trading-strategies/PEERCROSSCHECK_deepseek-flash.md` §11.1 |
| 09:58 | DOC | Broadcast to `mentions/all` (retained) with the four items PART13 does not have: the 126-cell census, the frequency answer (1h -32.1bps to 1d +20.4bps), the permutation disconfirmation (p=0.40), and the killed weekend survivor | COMS `mentions/all` |
| 10:02 | DOC | Long-form evidence published to retained topic `notes/pasc-subq-combine-claim-test-2026-11-22`; short non-retained pointers DM'd to `subq-savant-1-4` and `copilot-cli-moneyresearch` | COMS `notes/pasc-subq-combine-claim-test-2026-11-22` |
| 10:04 | FIX | Adopted Mercury3's reporting rule as a standing requirement: every sub-hourly strategy reports **gross / fees / net and the ratio** — if the fee line exceeds the gross line it is a donation, not a strategy | `ROADMAP_200_deepseek-flash.md` |
| 10:05 | PEER | Documented the two fleet-hygiene behaviours hit here: `coms.ps1` refuses `--retain` into another seat's inbox (last-writer-wins guard), and `check` without `-WorktreeName` resolves to the newest registered seat and misses a new worktree's inbox | `PEERCROSSCHECK_deepseek-flash.md` §11.3 |

| 10:08 | PEER | Perplexity note audit: a peer review of the **same** note already existed (`REVIEWS/PERPLEXITY_NOTE_REVIEW.md`, 5 matching tool names), so I re-verified its factual table instead of duplicating it - Windows-MCP 11,999 stars MIT, SayDoneAI/Screenhand 0 stars, screen-use no match, Eigent 15,867, open-cowork 2,283, nuphus-mcp 336 all confirmed | `../REVIEWS/PERPLEXITY_NOTE_REVIEW.md` addendum A0 |
| 10:10 | DOC | Appended a backtesting-half addendum: **four undisclosed licences** (`backtesting.py` AGPL-3.0, `LumiBot` GPL-3.0, `NautilusTrader` LGPL-3.0, vectorbt NOASSERTION) and `vectorbt.pro` has no public repo to audit | `../REVIEWS/PERPLEXITY_NOTE_REVIEW.md` A1 |
| 10:10 | FAIL | Its proposed gate list (OOS, costs, slippage, position limits, drawdown limits, data quality, reproducible artifacts) is **necessary and not sufficient**: all seven were implemented here across 126 cells and **0 qualified**. The missing gates are trial accounting / deflated Sharpe and a permutation control | `../REVIEWS/PERPLEXITY_NOTE_REVIEW.md` A2, `TIMEFRAME_MATRIX.md` |
| 10:11 | DOC | Recorded that engine choice is not the binding constraint: NautilusTrader over vectorbt changes how faithfully you simulate an edge smaller than 26bps; it does not create one. Mercury3 PART13 reaches the same place from a different codebase (fees 9x gross edge) | `../REVIEWS/PERPLEXITY_NOTE_REVIEW.md` A3 |

| 10:14 | PEER | Audited a peer's claimed profitable live trade (ETH/USD long, +0.449% net, 8 min) leg by leg against **1-minute bars from Kraken and Binance**, not against prose | `../REVIEWS/GEMINI_TRADE_0001_AUDIT.md` |
| 10:14 | FAIL | **Cross-venue splice:** entry 1681.50 @09:17 is inside Kraken's bar (1680.76-1681.92) but 0.13 pct BELOW Binance's low; exit 1690.73 @09:25 is 0.14 pct ABOVE Kraken's bar high (1688.43) but inside Binance's. Each leg real on one book, no single venue supports both. On Kraken the price traded at **09:23**, two minutes before the claimed exit | `../REVIEWS/GEMINI_TRADE_0001_AUDIT.md` §2 |
| 10:15 | FAIL | **The profit is the fee assumption.** Claimed 10bps round trip = 5bps/side, below every retail spot taker. Repriced at Kraken base (52bps RT) the best honest exit nets **+0.001 pct - exactly zero**. Same mechanism as Mercury3 PART13 (fees 9x gross) and my 126-cell census (5 of 6 families negative) | `../REVIEWS/GEMINI_TRADE_0001_AUDIT.md` §3 |
| 10:15 | FAIL | **Its OPEN trade is mispriced:** TRADE_0002 entry 1690.73 @09:26 is 0.26 pct above Kraken's high (1686.36) and 0.10 pct above Binance's (1689.35) - unattainable on both, and it is still accumulating | `../REVIEWS/GEMINI_TRADE_0001_AUDIT.md` §4 |
| 10:16 | PASS | Confirmed two design choices in my own harness were the right ones: venue is fixed on the trade at open (a fallback would mark it unverified, never re-price it), and the ledger is append-only JSONL with state rebuilt from it, not a mutable JSON document | `realtime_challenge/ledger.py`, `live.py` |

| 10:21 | RUN | **First equity/ETF class test (roadmap P1, R28-R31).** H-E1 dual-momentum rotation: 10 ETFs across 6 classes, 12-1m momentum, top-2, 10m SMA filter, monthly rebalance, month-end signal -> next-day OPEN fill, 5bps/side, 2004-2026 (22.9 y) | `realtime_challenge/proof/etf_rotation.py`, `results/etf_rotation.json` |
| 10:21 | FAIL | H-E1 vs buy-and-hold: CAGR **5.37 pct vs 10.28 pct**, Sharpe **0.410 vs 0.620**, maxDD -32.8 pct vs -55.2 pct. Gives up 4.9 points of CAGR and 0.21 of Sharpe | `ETF_ROTATION_H-E1.md` |
| 10:22 | FAIL | **Permutation control kills it:** shuffle each ETF's returns independently (destroys the cross-section, keeps each series' volatility) -> real Sharpe 0.408, shuffled **p95 0.741**, **p = 0.66**. A destroyed cross-section does better than two thirds of random draws | `results/etf_rotation.json` |
| 10:22 | RUN | **Strictly dominated by one line of code:** SPY + 200d SMA = CAGR 7.51 pct, Sharpe **0.693**, maxDD -21.5 pct; SPY + 100d = 7.34 pct, **0.702**, -19.3 pct. H-E1 loses on all three axes | `ETF_ROTATION_H-E1.md` |
| 10:23 | PASS | **Reproduced the repo's own benchmark independently:** peer verdict quotes SPY 10.27 pct CAGR / -55.2 pct DD (2006-2026); this separately written script gets **10.28 pct / -55.19 pct** on 2004-2026. Two decimals of agreement. Peer's trend-overlay row (8.37 pct / -20.5 pct) vs mine (7.51 pct / -21.54 pct) is a 0.9-point gap -> roadmap R191-R192 | `ETF_ROTATION_H-E1.md` |
| 10:23 | RUN | Sub-period decay: rotation beat SPY in 2004-2012 (Sharpe 0.465 vs 0.331) and lost badly after (0.096 vs 1.102 in 2013-2019). A 2004-start test alone would have proven it; a 2013-start test alone would have killed it | `results/etf_rotation.json` |
| 10:24 | DOC | Cost was never the constraint: turnover 6.6x/yr, Sharpe 0.429 at 0bps -> 0.322 at 52bps. **Low frequency trivially survives costs** - so surviving costs is not evidence of edge. Day trading died at the cost line; this dies at the no-alpha line. Frequency is necessary, not sufficient | `ETF_ROTATION_H-E1.md` |
| 10:25 | DOC | H-E1 archived with its test. The only thing beating buy-and-hold risk-adjusted is the slow trend overlay (timed beta, not alpha) - which agrees with the peer capital-allocation verdict | `../REVIEWS/COPILOT_GPT5_STACK_AND_ETF_HYPOTHESIS_REVIEW.md` |

| 10:31 | PEER | Audited the ChatGPT/GPT-6 note. It is the **only submission that abstained**: NO TRADE, with every deliverable marked unstarted and the reason stated as 'a documented no-trade decision is better than false evidence' | `../REVIEWS/CHATGPT_GPT6_ARCHITECTURE_AND_NOTRADE_REVIEW.md` §1 |
| 10:31 | FAIL | Its BTC snapshot (59,080-59,316 at 09:18 UTC) was stale ~0.7 pct: the quoted HIGH is **$272 below the lowest print on any of three venues** in that minute (Kraken 59,588 / Bybit 59,688 / Binance 59,692) | `../REVIEWS/CHATGPT_GPT6_ARCHITECTURE_AND_NOTRADE_REVIEW.md` §2 |
| 10:32 | PASS | **But it disclosed the timestamp defect and refused to trade on it** - which is exactly why a stale quote did not become a fake win. Same mistake class as the Gemini trade, opposite handling: one abstained, the other booked +0.449 pct that nets +0.001 pct at real fees | `../REVIEWS/CHATGPT_GPT6_ARCHITECTURE_AND_NOTRADE_REVIEW.md` §2 |
| 10:33 | PEER | Verified its UFO² recommendation: `microsoft/UFO` **10,226 stars, MIT, pushed 2026-10-30**, HostAgent/AppAgents/MCP all confirmed in the README. Mild version drift - the repo is now branded **UFO³** with UFO² a component, so the pick is valid but one generation back | `../REVIEWS/CHATGPT_GPT6_ARCHITECTURE_AND_NOTRADE_REVIEW.md` §3 |
| 10:34 | DOC | Recorded the batch-wide gap: its three-agent red-team (generate / disprove / validate data) has no **trial accountant**, so 'thousands of variations' will yield the luckiest candidate as a confirmed winner. Permutation control + deflated Sharpe are the mechanical versions of those roles | `../REVIEWS/CHATGPT_GPT6_ARCHITECTURE_AND_NOTRADE_REVIEW.md` §5 |

### Verdict changes after session 2

- **Trial count: 42 → 126.** Every deflated Sharpe quoted from here deflates against 126.
- **H-R1, H-R3, H-R6 archived across all horizons.** Negative at every timeframe and every
  cost level. Not to be re-run with new parameters.
- **H-R2 survives only at 1d and only at breakeven** (+4.77 bps, CI [−72.2, +81.2]).
- **H-R4 is the single cell family worth a forward pod, at 1d only** — with its permutation
  p=0.40 disclosed next to any PF it is ever quoted with.
- **The 1h window is low-power** (125 days). Quote 4h and 1d results.
- **Portfolio combination is not a rescue.** Combined Sharpe −0.123 vs best single +0.243 on
  a book where only 2 of 6 families have positive expectancy. Do not present diversification
  as a path to profitability while the components are negative.

### What session 3 must not do

Promote H-R4 on the strength of the sign flip. The shuffle control already says the effect
is reproducible without any market structure, and a forward pod that ignores that is
measuring the bracket, not the market.

---

## Session 1 — 2026-11-22 (08:56–09:35 UTC) — `deepseek-flash`

Topic split: this folder was created out of `02-portfolio-multi-asset/` so that
**strategy/backtest evidence** stops living next to **portfolio valuation**. `02` keeps the
tracking/valuation research; everything measured lives here.

### Harness built

| time (UTC) | status | item | artifact |
|---|---|---|---|
| 08:56 | RUN | Challenge defined; venue = crypto spot (the only class open at 04:00 EST Sunday) | `REALTIMECHALLENGE_deepseek-flash_2026-11-22_0356_EST.MD` §2 |
| 09:00 | DOC | 6 pre-registered hypotheses with frozen params; desk denylist wired in (no AVAX/TRX/MATIC, no UTC 2/8/13/20, `tp/sl ≤ 2.5` asserted at import) | `realtime_challenge/strategies.py` |
| 09:04 | PASS | Harness certification 5/5 — look-ahead detectable, signals causal, cost drag 25.4 bps vs 26 expected, both-touched bar → SL, 0/60 noise cells at DSR 0.95 | `results/harness_certification.json` |
| 09:06 | FIX | ccxt pagination bug: `since` is a *start* time, so paging "backwards" re-returned the same 1,000 bars. The first matrix covered 42 days, not 125. All numbers regenerated | `realtime_challenge/data.py` |
| 09:08 | FAIL | 1h matrix, 42 cells, 26 bps: **0** above deflated Sharpe 0.95 (best 0.071), **0** beating the permutation control (p = 0.20–0.89) | `results/backtest_latest.json` |
| 09:08 | FIX | Metric defect: `excess_vs_bh` credited H-R2 with **+28% "alpha"** for being flat in a −29% bear window. Replaced with `excess_scaled` = strategy − B&H × time-in-market; every excess figure in the first run withdrawn | `realtime_challenge/cli.py` |
| 09:09 | FAIL | Weekend effect re-test, 3.01 y, **clustered by calendar weekend**, 42 control windows: **−3.21 bps**, CI [−67.26, +64.51], P(>0) 0.4465, rank **#15 of 42**, z +0.44 → NOT ESTABLISHED | `results/weekend_test.json` |
| 09:11 | RUN | Live round 1 (SMOKE_TEST): 3 real positions opened on Bybit at real ask + 10 bps | `ledger/live_smoke_bybit.jsonl` |
| 09:18 | FAIL | Live round 1 closed: **6 trades, 0 winners, −$27.79 (−0.278%)**, $40.00 fees. Market moved −5.7 to +2.4 bps; friction took 20 bps. Live reproduction of certification T2 | `ledger/live_smoke_bybit.jsonl`, `results/live_smoke_bybit_summary.json` |
| 09:16 | RUN | Live round 2 (HARNESS_PROBE_5M_BURST): 3 shorts opened on a real 5m impulse signal | `ledger/liveprobe_bybit_v2.jsonl` |
| 09:20 | FAIL | Live round 2 closed: all 3 stopped out at **−49.6/−53.2/−64.6 bps** for −$55.76. Shorting a 5-min dip inside a +3.4% day. Realised loss exceeded the stop distance — slippage through the stop charged, not assumed | `ledger/liveprobe_bybit_v2.jsonl` |
| 09:12 | FIX | Burst scanner sampled only the latest closed 5m bar while each iteration takes 1–6 min, so it saw ~1 bar in 3 and missed most signals (diagnostic: `max\|5m ret\|` 0.70%, 3 qualifying bars/hour, 0 signals fired). Now scans the last 12 closed bars | `realtime_challenge/live.py` |
| 09:24 | FIX | GitHub Actions pod failed: `venue bybit returned no quotes` — Bybit/OKX refuse US datacentre IPs and runners are Azure US. Added venue failover (kraken → coinbase → bybit → okx → binance), single-symbol probe first, venue recorded in the pass summary | `realtime_challenge/worker/forward_supervisor.py` |
| 09:26 | PASS | GHA dispatch green: supervisor picked **kraken**, equity $10,000.00, ledger committed by the bot (`rtc: forward pod pass 2026-11-22T09:26Z`) | Actions run 45007519943 |
| 09:22 | PASS | `screen-control-tests` green on GitHub's Ubuntu runner (9/9) — CI-enforced | Actions run 45007260204 |
| 09:30 | PEER | Audited the repo's prior 2-hour challenge: `REAL_CHALLENGE_FINAL.md` declares a winner on **n=2 trades**, gross of any fee (`grep` for fee/commission/slippage in `challenge_v3.py` → **0** hits), entries priced at the signal bar's own price. Not evidence. Also agreed with the capital-allocation verdict | `PEERCROSSCHECK_deepseek-flash.md` §2–§3 |
| 09:33 | PEER | Reconciled the mid-session peer commits (GPT-4.1-mini blueprint review, paper-trading design, TOOL_INTERFACE approval classes). Adopted their GHA caveat as a rule: hourly supervision ⇒ the bracket must be survivable across a 60-min gap | `PEERCROSSCHECK_deepseek-flash.md` §7–§9 |
| 09:34 | DOC | Roadmap gains the supervision-gap rule; 200 rounds across 10 phases with kill conditions | `ROADMAP_200_deepseek-flash.md` |
| 09:35 | DOC | Library survey: 20 repos, star/last-push/licence verified via the GitHub API on 2026-11-22 | `LIBRARY_SURVEY.md` |

### Standing state after session 1

- **No asset class is proven profitable.** 42 cells, 0 clearing deflated Sharpe 0.95.
- **One family cleared friction and then failed a proper test** (weekend effect).
- **Forward evidence count: 0 qualifying trades** from the pre-registered book. The pods
  are live and hourly; `n` starts accumulating from here.
- **Kilometre zero for the 200-round plan:** P0 (harness integrity) complete; P1 (class
  census) next, with FX opening 17:00 EST and equities Monday 09:30.

### What session 2 must not do

Re-run the 42 dead cells with new TP/SL. They are dead. A parameter change after seeing
results is a new hypothesis with a new id and a fresh forward clock.

---

## Session template (copy for each new session)

```
## Session N — <date> (<start>–<end> UTC) — <agent>
<one line: what question this session answered>

| time (UTC) | status | item | artifact |
|---|---|---|---|
| | | | |

Standing state: <cells / forward n / verdicts changed>
```
