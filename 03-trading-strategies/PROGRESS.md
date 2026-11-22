# PROGRESS — trading strategies / backtests / paper trading

Append-only running log. Every row must point at an artifact in this folder; a row with no
artifact is a claim, not progress. Newest session at the top.

Legend for **status**: `RUN` executed · `PASS`/`FAIL` gate result · `FIX` defect found and
fixed · `DOC` written · `PEER` reconciliation with another agent's work.

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
