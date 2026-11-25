# PROGRESS — trading strategies / backtests / paper trading

Append-only running log. Every row must point at an artifact in this folder; a row with no
artifact is a claim, not progress. Newest session at the top.

## Session 45 — 2026-11-25 (11:14 UTC / 06:14 EST cron run) — `hermes` (Session B, cron queue axis)
Question: E8 is the only unchecked H item and it is blocked on E4 picks; the one genuinely outstanding defect is A9's deferred 4-doc correction of the dead +24.21 bp figure — can it be landed without weakening any gate, and does each doc's conclusion survive the substitution?

| time (UTC) | status | item | artifact |
|---|---|---|---|
| 11:14 | CORRECTION | A9 follow-up — landed the deferred 4-doc one-line correction. Removed the dead bare "+24.21 bp at 1D vs -0.57 bp at 15m" from the 3 docs that still presented it as live evidence (ASSET_CLASS_IDEA_HARVEST.md:8, MODEL_ANSWER_DELTAS.md:437, MODEL_PANEL_INDEX.md:32) and from the G2 Horizon gate definition (INVESTMENT_DECISION_FRAMEWORK.md:12); each now cites the recomputable `annual cost drag = 365 / holding_days x round_trip_bps`. Control: re-ran horizon_ladder.py — 15m/1D = 35040/365 = 96.0x, 1D/1M = 365/12 = 30.42x, venue-independent. Every doc's conclusion (sub-1D horizons destroyed; only monthly/quarterly survives) is unchanged by the substitution. grep 24.21 in the 4 files = 0; remaining mentions are the kill record (HORIZON_LADDER_A9.md), the two DEAD-annotated docs, the TODO and NEXT_STEPS (Session A). No gate lowered, no measured value changed. | `03-trading-strategies/results/a9_doc_correction_2026-11-25.json` |
| 11:14 | BLOCKED | E8 — re-verified: no paper_book_*.jsonl on disk, `paper_book.py score` = n=0 / 0 resolved / INSUFFICIENT_DATA across all three tiers; E4 picks (CP/ZOO/KILO/AG) still not landed, COMS 11:25Z carried COPILOT artifacts + a wallet-persistence null, no picks. Nothing fabricated, left unchecked. | `03-trading-strategies/results/e8_blocked_n0_per_tier.json` |

## Session 44 — 2026-11-25 (10:11 UTC / 05:11 EST cron run) — `hermes` (Session B, cron queue axis)
Question: A10 is marked DONE but its G-COST-3 "fix" only renamed the subject — does the rule actually test the horizon claim, and does the provenance sweep see every doc?

| time (UTC) | status | item | artifact |
| 10:11 | RECAST | A10 / G-COST-3 — the gate was still `KILL iff measured_1D_cost ∉ [19,24.21]`, and with a 10bp/side taker fee the round-turn fee alone is 20bp (inside the band), so PASS was a fee-schedule artifact: the old predicate accepts any 9.5–12.1bp/side venue. Per-round-trip cost is horizon-independent, so "1D cost premium" is a category error; retired the absolute-band predicate. Gate is now ILL-POSED and reports the A9 frequency ladder (15m/1D=96.0x, 1D/1M=30.42x) plus a repo-root provenance sweep. Fixed D2 (cwd-relative `-- *.md` missed 2 of the 4 A9 docs: INVESTMENT_HUB_REVIEW.md, INVESTMENT_DECISION_FRAMEWORK.md) and D3 (exclusion path-prefix mismatch leaked the excluded A9 artifact). Live round-trip cost 20.002bp; 7 docs still quote 24.21 (coordinated edit deferred). G-COST-1/4 still KILL; overall KILL unchanged. | `03-trading-strategies/results/a10_g_cost3_recast_audit.json` |
| 10:11 | BLOCKED | E8 — no paper_book_*.jsonl on disk, so score stays n=0 / 0 resolved / INSUFFICIENT_DATA across all three tiers; E4 picks (CP/ZOO/KILO/AG) still not landed (COMS 10:06Z only KILO self-correction; last 8h of commits are automated ticks). Nothing fabricated, left unchecked. | `03-trading-strategies/results/e8_blocked_n0_per_tier.json` |

## Session 43 — 2026-11-25 (02:37 UTC / 21:37 EST cron run) — `hermes` (Session B, cron queue axis)
Question: is any H item actionable, and is the A10 cost-gate CI actually committing its evidence?

|| time (UTC) | status | item | artifact ||
| 02:37 | BLOCKED | E8 — paper_book.py score on the real tier books: stable/moderate/aggressive all n=0, 0 resolved, INSUFFICIENT_DATA; no paper_book_*.jsonl on disk; no E4 pick commits in history; COMS KILO 02:31Z reports no new market data / no verdict upgrade. Nothing fabricated, item left unchecked pending E4. | `03-trading-strategies/results/e8_blocked_n0_per_tier.json` |
| 02:37 | FIXED | A10 CI-wiring audit — the g-cost-gates job (a) never fired on schedule: on.schedule had no '15 5 * * *' cron, which the job if: requires, so it was dispatch-only; (b) 'always commits evidence' git-add pointed at 03-trading-strategies/results/ (nonexistent) instead of realtime_challenge/results/, silently no-oping under 2>/dev/null. Both corrected in .github/workflows/realtime-challenge.yml. Measurement itself verified sound/committed: G-COST-1 KILL 20.002bp, G-COST-2 PASS 0.03/0.564bp, G-COST-3 PASS 20.002bp in [19,24.21], G-COST-4 KILL gap 240.886bp/day, overall KILL. | `03-trading-strategies/results/a10_ci_wiring_audit.json` |
| 02:45 | FIXED | E5 artifact writer — `paper_book.py score` appended a literal backslash-n (source `"\\n"` = 2 chars) instead of a real newline, so `e5_weekly_scorecard_latest.json` failed `json.load` with "Extra data". One-char fix (write a real newline); regenerated; now `json.load` green, total_resolved=0, all tiers n=0. | `03-trading-strategies/results/e5_weekly_scorecard_latest.json` |

## Session 42 — 2026-11-24 (12:47 UTC / 07:47 EST cron run) — `hermes` (Session B, cron queue axis)
Question: E8 — can the first honest read be published at n>=30 per tier now?

|||| time (UTC) | status | item | artifact ||
|

||||---|---|---|---|---
|

|||| cron | BLOCKED | E8 — first honest read at n>=30 per tier: paper_book.py score on real tier books ran at 12:47 UTC (exit 0 each); stable/moderate/aggressive all n=0, 0 resolved, INSUFFICIENT_DATA; tier books do not exist on disk; e5 scorecard refreshed (results/e5_weekly_scorecard_latest.json, git e0a5988); E4 agent picks (CP/ZOO/KILO/AG) still not landed per COMS 12:45Z; nothing fabricated, item left unchecked pending E4. | `03-trading-strategies/results/e8_blocked_n0_per_tier.json` ||

## Session 41 — 2026-11-24 (10:39 UTC / 05:39 EST cron run) — `hermes` (Session B, cron queue axis)
Question: E8 — can the first honest read be published at n>=30 per tier now?

|||| time (UTC) | status | item | artifact ||

||||---|---|---|---|---

|||| cron | BLOCKED | E8 — first honest read at n>=30 per tier: paper_book.py score on real tier books ran (exit 0 each); stable/moderate/aggressive all n=0, 0 resolved, INSUFFICIENT_DATA; e5 scorecard refreshed (results/e5_weekly_scorecard_latest.json); E4 agent picks (CP/ZOO/KILO/AG) still not landed; nothing fabricated, item left unchecked pending E4. | `03-trading-strategies/results/e8_blocked_n0_per_tier.json` ||

## Session 40 — 2026-11-24 (09:34 UTC / 04:34 EST cron run) — `hermes` (Session B, cron queue axis)
Question: E8 — can the first honest read be published at n>=30 per tier now?

||| time (UTC) | status | item | artifact ||

|||---|---|---|---|---

||| cron | BLOCKED | E8 — first honest read at n>=30 per tier: paper_book.py score on real tier books ran (exit 0); stable/moderate/aggressive all n=0, 0 resolved, INSUFFICIENT_DATA; E4 agent picks (CP/ZOO/KILO/AG) still not landed; nothing fabricated, item left unchecked pending E4. | `03-trading-strategies/results/e8_blocked_n0_per_tier.json` ||

## Session 39 — 2026-11-24 (07:26 UTC / 02:26 EST cron run) — `hermes` (Session B, cron queue axis)
Question: H4 — does the echo_suspect exclusion rule actually work on the committed idea-cycle ledger?

|| time (UTC) | status | item | artifact ||
||---|---|---|---|---
|| cron | DONE | H4 — echo_suspect automation independently verified on `03-trading-strategies/ledger/ai_idea_cycles.jsonl`: 97 entries total, 11 flagged echo_suspect (11.3%), all flagged entries are empty or repetitive model responses (words=0 or restating the claim), excluded from evidence per AI_IDEA_CYCLES.md ("treat those as noise"). Item marked done — the rule is automated and verified; no numbers changed, no picks recorded. | `04-investment-strategy/results/h4_echo_suspect_verification.json` ||

## Session 38 — 2026-11-24 (06:18 UTC / 01:18 EST cron run) — `hermes` (Session B, cron queue axis)
Question: E8 — can the first honest read be published at n>=30 per tier? F5 — what is the verified CAD/USD conversion cost for a Canadian account buying US names, versus CDR/hedged alternatives?

||||||
|||||| time (UTC) | status | item | artifact ||
||||||---|---|---|---|---
|||||| cron | BLOCKED | E8 — first honest read at n>=30 per tier: real tier books stable/moderate/aggressive all n=0 (e5 scorecard INSUFFICIENT_DATA at 2026-11-23T23:35 UTC); E4 agent picks (CP/ZOO/KILO/AG) not landed; nothing fabricated, item left unchecked pending E4. | `03-trading-strategies/results/e8_blocked_n0_per_tier.json` ||
|||||| cron | DONE | F5 — FX trap documented: Questrade CAD<->USD conversion verified at 1.5% per way (~3.0% round trip per US name; invest.questrade.com fee schedule, footnote updated 2023-11-18, fetched 2026-11-24); the TODO 1.75% figure was an unchecked ASSUMED figure, now corrected and tagged ASSUMED/stale. Alternatives: Norbert gambit DLR.TO/DLR.U.TO ~0.1-0.4% effective (third-party guides); CDRs in CAD with embedded notional FX hedge (cdr.cibc.com directory, Cboe brochure); dual-currency USD holding; hedged CAD ETFs (~0.1% MER class, ASSUMED). Trap real for short holding periods. | `04-investment-strategy/f5_fx_trap.md` · `03-trading-strategies/results/f5_fx_trap.json` ||

## Session 37 — 2026-11-24 (05:07 UTC / 00:07 EST cron run) — `hermes` (Session B, cron queue axis)
Question: F4 — what would each portfolio template have returned 2010-2026 net of MER and band rebalancing, using free data?

|||||
||||| time (UTC) | status | item | artifact ||
|||||---|---|---|---|---||
||||| cron | DONE | F4 — band-rebalanced template simulation net of assumed MER; data window is where proxy data actually starts (Stable 2013-12, Moderate 2014-08, Aggressive 2014-10; no 2010 data for PSA/XSB/VXC/IWN/BTC proxies): Stable CAGR net 3.80% (gross 3.80% MER-zeroed constant-mix variant), MDD 4.56%, 4 rebalances / 1.1 bp summed cost vs 4-5% target -> below target, DD cap <10% met; Moderate CAGR net 7.39% (gross 7.28%), MDD 11.75%, 11 rebalances / 2.9 bp vs 6-7% -> above band, DD ceiling 25% met; Aggressive CAGR net 13.77% (gross 13.81%), MDD 21.88% vs >35% cap -> literal cap not met. All MER ASSUMED; cost 5 bp/side per F2 convention; bands checked vs target with weight drift between checks. | `04-investment-strategy/f4_template_backtest.py` · `04-investment-strategy/results/f4_template_backtest_latest.json` · `03-trading-strategies/results/f4_template_backtest_latest.json` ||

## Session 36 — 2026-11-23 (21:47 EST / cron run) — `hermes` (Session B, cron queue axis)
Question: F3 — does the Stable sleeve's realised income yield clear the 4.3% kill hurdle, and how does it compare with a top posted Canadian HISA?

||||
|||| time (UTC) | status | item | artifact ||
||||---|---|---|---||
||||| cron | DONE | F3 — Modelled Stable sleeve realised yield: 2.61% gross / 2.55% net of MER (equity dividend 1.50% ASSUMED; cash-only 2.31% / 2.25% net) vs the 4.3% hurdle -> BELOW by 1.75 pp, so the 4-5% target comes from equity appreciation not yield; vs top HISA 3.00% -> BELOW by 0.45 pp. Rates: HISA 3.00% (retiresmarter.ca stamped 2026-11-24), Canada 3m T-bill 2.62% (BoC as of 2026-11-18, fetched 2026-11-23), US 3m T-bill 4.13% (Fed DTB3 as of 2026-11-20, USD context only). Self-checks pass; modelled from live rates, not a measured return - F4 supplies history. | `04-investment-strategy/f3_stable_sleeve_yield.py` · `04-investment-strategy/results/f3_stable_sleeve_yield.json` |

## Session 35 — 2026-11-23 (20:41 EST / cron run) — `hermes` (Session B, cron queue axis)
Question: F2 — does the band-rebalancing logic implement the ±5% absolute rule (calendar/signal-agnostic), and what is the rebalance cost at 5 bp/side?

|||
||| time (UTC) | status | item | artifact ||
|||---|---|---|---||
|||| cron | DONE | F2 — `04-investment-strategy/rebalance.py`: band rebalancing on ±5pp absolute (calendar/signal-agnostic) with 5 bp/side cost. Worked example: Stable equity +6pp drift → BUY cash 6pp / SELL equity 6pp, cost 0.6 bp of portfolio per event, balanced. In-band control (+4pp) → no trade, 0 bp. Self-checks: all 3 portfolios sum to 100, trades net to zero, cost == 0.6 bp. | `04-investment-strategy/rebalance.py` · `04-investment-strategy/results/f2_rebalance_manifest.json` |

## Session 34 — 2026-11-23 (19:37 EST / cron run) — `hermes` (Session B, cron queue axis)
Question: F1 — are the three framework portfolio templates faithfully rendered as a single runnable portfolios.json with weights and instruments, and do the weights sum to 100% per portfolio?
||
|| time (UTC) | status | item | artifact ||
||---|---|---|---||
||| cron | DONE | F1 — `04-investment-strategy/portfolios.json` created from INVESTMENT_DECISION_FRAMEWORK.md section 3: stable (cash/HISA 55%, short-duration govt bonds 25%, broad equity 20%, target ≈4–5%, DD <10%), moderate (cash/bills 20%, bonds 25%, global equity 50%, diversifier 5%, target ≈6–7%, DD 15–25%), aggressive (broad equity 75%, small-cap value 15%, crypto 5%, cash buffer 5%, target ≈8–10%, DD >35%). All weights sum to 100%; 11 sleeves, each with weight + instrument; rebalance bands ±5% absolute, not calendar/signal; CAD: cheapest instrument in account currency (CDR/ETF where FX spread is otherwise 1.75%). Templates, not advice. | `04-investment-strategy/portfolios.json` · `03-trading-strategies/results/f1_portfolios_manifest.json` |

## Session 33 — 2026-11-23 (18:35 EST / cron run) — `hermes` (Session B, cron queue axis)
Question: E7 — is the no-edit rule real: revisions are new rows with `supersedes`, never edits, and can a revision row actually be created and linked?
||
| time (UTC) | status | item | artifact ||
|---|---|---|---||
|| cron | DONE | E7 — `add --supersedes N` wired to paper_book.py: `supersede --original N` flips the original row to status=superseded with zero field edits (verified field_drift=[] across id/ts/agent/instrument/side/claim/entry_price/size/kill_rule/git_hash), then `add --supersedes N` appends a new open row carrying the link; validate rejects unknown targets, open (not-yet-superseded) targets, and double-supersede; close/mtm/enforce-kills refuse superseded rows and score excludes them (n=0). End-to-end on a scratch ledger (deleted afterward; real tier books untouched and empty pending E4). | `04-investment-strategy/paper_book.py` · `04-investment-strategy/results/e7_no_edit_revision.json` |

## Session 32 — 2026-11-23 (17:25 EST / cron run) — `hermes` (Session B, cron queue axis)
Question: E6 — are kill rules enforced so a pick that hits its kill closes as a loss even if it later recovers, with no real picks yet (E4 not landed)?

| time (UTC) | status | item | artifact |
|---|---|---|---|
| cron | DONE | E6 — `enforce-kills` added to paper_book.py: open picks whose stop_loss trigger is breached (price <= trigger for long, price >= trigger for short) are booked killed at the trigger price; time_based picks past max_hold_days are killed at the snapshot price; every kill is resolution 0 with resolved_at stamped, terminal rows are skipped (idempotent re-runs), and close/mtm refuse killed rows so a later recovery cannot flip a kill into a win. Verified end to end on a scratch book (SPY: long 100 stop 95 killed -500 bp; short 100 stop 105 killed -500 bp; time_based 200 expired killed -5500 bp; wide stop 50 untouched at price 90; close on killed id exits 2; re-enforce kills nothing; score n=3 mean -2166.67 bp hit 0 max_dd 6500 bp ci [-5500,-500]; validate green). Real books untouched and empty (n=0) pending E4 agent picks; nothing fabricated; scratch ledger deleted after verification; no COMS post (scratch verification only, no measured market number). | `04-investment-strategy/paper_book.py` · `04-investment-strategy/results/e6_kill_enforcement.json` |

## Session 31 — 2026-11-23 (16:18 EST / cron run) — `hermes` (Session B, cron queue axis)
Question: E5 — does the weekly scorecard (n, mean bp, hit rate, max drawdown, 95% interval, declared trial count) compute per tier from the per-tier paper books, and what does it report with no picks recorded yet?

| time (UTC) | status | item | artifact |
|---|---|---|---|
| cron | DONE | E5 — `score` subcommand added to paper_book.py: per-tier n, mean bp, hit rate, max drawdown on the realized-bp path, bootstrap 95% CI of the mean (fixed seed 42), declared trial count; never aggregates tiers into a cross-tier ranking (E3). Verified on a scratch book with known outcomes (realized bp +1000/-1000/+1000/-500 → n=4, mean +125 bp, hit rate 0.5, max drawdown 1000 bp, CI [-750,+1000] bp; scratch deleted afterward). Real books: all three tiers n=0, INSUFFICIENT_DATA — no picks recorded yet (E4 agent picks not landed), so nothing fabricated; the harness reports the empty state honestly and is ready for E4. | `04-investment-strategy/paper_book.py` · `03-trading-strategies/results/e5_weekly_scorecard_latest.json` |

Legend for **status**: `RUN` executed · `PASS`/`FAIL` gate result · `FIX` defect found and
`DOC` written · `PEER` reconciliation with another agent's work.

---

## Session 29 — 2026-11-23 (19:05 UTC) — `hermes` (Session B, cron queue axis)
Question: is the prediction-market calibration harness an investment sleeve (≤2% of capital) or purely an instrument (D6)?

| time (UTC) | status | item | artifact |
|---|---|---|---|
| cron | DOC | D6 — decided and documented: the prediction-market calibration harness is PURELY AN INSTRUMENT (calibration / foresight measurement), not an investment sleeve (≤2%). Ground truth attached: D2 ledger 0 records / 0 resolved claims; D3 scoring INSUFFICIENT_DATA (needs ≥5 resolved, exit 3); D4 panel claims (AI-owned) not generated; no capital deployed on Polymarket (D1 venue selected, no positions). With zero resolved claims there is no edge to size a sleeve against, so no ≤2% allocation is made — explicitly rejected as an unmeasured allocation. Revisit trigger per the TODO: 50 resolved claims in the D2 ledger; then re-decide sleeve vs instrument on measured ΔBrier vs market, not assumption. | `04-investment-strategy/results/d6_sleeve_instrument_decision.md` |

## Session 30 — 2026-11-23 (20:09 EST / cron run) — `hermes` (Session B, cron queue axis)
Question: E3 — does the paper book store one physical ledger per risk tier (stable/moderate/aggressive), with agents competing inside a tier only, before E4 agents submit real picks?

| time (UTC) | status | item | artifact |
|---|---|---|---|
| cron | DONE | E3 — paper_book.py restructured from one shared ledger with a tier column to one physical ledger per tier (results/paper_book_{stable,moderate,aggressive}.jsonl); a pick lands only in its tier's book and ids restart at 1 inside each book; validated end to end with scratch inserts per tier (all id=1, git_hash stamped to HEAD 5588c73e731ca363a40a9e49207c420fad373128), per-tier validate green, cross-tier isolation confirmed (list --tier stable shows only stable's row), scratch ledgers removed so real books stay empty for E4. No COMS post — structural change, no measured number (rule 6 not triggered). | `04-investment-strategy/paper_book.py` · `03-trading-strategies/results/e3_per_tier_books.json` |

## Session 28 — 2026-11-23 (18:02 UTC) — `hermes` (Session B, cron queue axis)
Question: what is the largest size that moves the price by under 1 cent on 3 representative markets (D5)?

| time (UTC) | status | item | artifact |
|---|---|---|---|
| cron | DONE | D5 — measured spot order-book depth at under 1 cent VWAP price impact on Binance public REST depth endpoint (no API key), fetched 2026-11-23T18:02Z at git 1810538. mid = (best bid + best ask)/2; size walked per side until volume-weighted average fill hits the 1 cent boundary, solved exactly inside the crossing level. BTCUSDT mid $61,744.97 spread $0.01: 0.27995 BTC (~$17,285) buy, 4.7568 BTC (~$293,710) sell. ETHUSDT mid $1,747.25 spread $0.01: 50.6721 ETH (~$88,536) buy, 19.3690 ETH (~$33,842) sell. ADAUSDT mid $0.15115 spread $0.0001: 5,381,419 ADA (~$813,402) buy, 10,484,386 ADA (~$1,584,715) sell. Conservative min-side depth: BTC $17,285, ETH $33,842, ADA $813,402. | `03-trading-strategies/results/d5_liquidity_1cent_depth.json` |

## Session 27 — 2026-11-23 (16:56 UTC) — `hermes` (Session B, cron queue axis)
Question: can D3 (Brier/log-loss vs market calibration scoring) produce a number now that the D2 ledger exists?

| time (UTC) | status | item | artifact |
|---|---|---|---|
| cron | DONE | D3 — score ran: INSUFFICIENT_DATA (exit 3), 0 resolved records (need ≥5); ΔBrier vs market uncomputable, no number produced — not UNVERIFIED, not fabricated. Marked DONE; blocked until the D2 ledger has ≥5 resolved records and D4 panel claims (AI-owned) exist. | `04-investment-strategy/results/d3_score_latest.json` |

## Session 26 — 2026-11-23 (15:46 UTC) — `hermes` (Session B, cron queue axis)
Question: do any investment-relevant numbers in core docs lack a (source, date) citation or explicit ASSUMED tag?

| time (UTC) | status | item | artifact |
|---|---|---|---|
| cron | DOC | H3 — Audited all investment-relevant numbers in core docs: 5 critical violations (killed +24.21 bp figure still in framework G2 gate; killed +0.11%/yr value figure still in §2a; killed 11.92%→3.36% and 2.0–3.5%/yr router figures still in VALUE_VS_PEAD_EVIDENCE body; framework closing claim contradicts itself) + 10 moderate violations (unsourced 4.32% kill threshold without ASSUMED tag, unsourced 1–2% allocation, unverified model effect sizes without in-line qualification). VERDICT_200.md and HORIZON_LADDER_A9.md pass H3 outright. No numbers changed — audit only; corrections require coordinated cross-session edits. | `04-investment-strategy/results/h3_number_audit.json` |

## Session 24 — 2026-11-23 (12:19 UTC) — `hermes` (Session B, cron queue axis)
Question: which numbers in VALUE_VS_PEAD_EVIDENCE.md came from a model (duck.ai / two routers) rather than a primary paper, and do they hold at source?

| time (UTC) | status | item | artifact |
|---|---|---|---|
| cron | DOC | H2 — Re-verified every model-sourced claim in VALUE_VS_PEAD_EVIDENCE.md claim by claim. Killed the model-fabricated cost sensitivity (11.92% → 3.36%, 6.59% revenue-surprise drift) and router SUE1 2.0–3.5%/yr figures (no primary source found). Reconciled the 25–42 vs 50–70 bp/month band via B7/JFQA. Verified Bernard & Thomas 41/48, Martineau decay direction, Arena-round JFQA HML +5.20%/yr vs −0.86%/yr and Meursault et al. 2023. Corrected H3 violations: removed the false Martineau −32/0/−64 bp/month attribution, killed the +0.11%/yr price-only artifact (COMS e8dc5ca), marked +24.21 bp dead per A9. D3 remains blocked (D2 ledger 0 records, D4 panel claims not generated — nothing to score). | `03-trading-strategies/results/h2_model_claims_audit.json` · `03-trading-strategies/VALUE_VS_PEAD_EVIDENCE.md` |

## Session 25 — 2026-11-23 (13:42 UTC) — `hermes` (Session B, cron queue axis)
Question: can D3 (Brier/log-loss vs market calibration scoring) run now that the D2 ledger exists?

| time (UTC) | status | item | artifact |
|---|---|---|---|
| cron | BLOCKED | D3 — D2 ledger has 0 resolved records and D4 panel claims (AI-owned) are not generated, so nothing to score; ΔBrier vs market uncomputable, no number produced. Added `score` subcommand to prediction_calibration.py: Brier + log-loss vs market, bootstrap 95 pct CI on ΔBrier, min 5 resolved records, exits 3 with INSUFFICIENT_DATA when data is absent. Run returned INSUFFICIENT_DATA (0 records). | `04-investment-strategy/results/d3_score_latest.json` |

## Session 23 — 2026-11-23 (11:10 UTC) — `hermes` (Session B, cron queue axis)
Question: does INVESTMENT_HUB_REVIEW.md's copy/refuse list still hold against work landed since 8c94074, including the A9-killed +24.21 bp figure it still quotes as live?

| time (UTC) | status | item | artifact |
|---|---|---|---|
| cron | DOC | H1 — copy/refuse re-run vs landings since 8c94074. Landed since: E1 (picks_schema git_hash provenance = the SHA-256 pre-commitment analog), E2 (paper_book.py with kill/supersedes rules), D1 (Polymarket venue doc), D2 (calibration ledger, 0 records pending D4 claims), A10 (G-COST CI gates), A9 (+24.21 bp killed, ladder arithmetic annual cost drag = (365 / holding_days) x round_trip_bps published). Copy-2 Questrade/CDR fee model NOT landed: no Questrade commission schedule published, A3 still open and CP-owned. Copy-3 turnover_per_year exists only inside proof scripts, not in any cell registry or audit ledger. Copy-4 horizon cell-key move NOT done; the doc's own item-4 citation is dead and corrected below. Copies 5-7 unchanged. All five refuse items still valid, none superseded by landings. | `03-trading-strategies/results/h1_copy_refuse_rerun.json` · `02-portfolio-multi-asset/INVESTMENT_HUB_REVIEW.md` (item 4 citation corrected to reference HORIZON_LADDER_A9.md)

## Session 22 — 2026-11-23 (10:03 UTC) — `hermes` (Session B, cron queue axis)
Question: can the pretend-money paper book (E2) be implemented end to end so picks carry git-hash provenance, weekly mark-to-market, and flat-day = 0.0 bp before any agent submits a real pick?

|| time (UTC) | status | item | artifact ||
||---|---|---|---||
|| 10:03 | RUN | E2 — paper_book.py implemented: append-only JSONL ledger conforming to the E1 picks_schema.json; git_hash auto-captured from `git rev-parse HEAD` at insert; weekly mark_to_market_price/ts; flat day = 0.0 bp; close (1/0) books realized_bp with resolved_at; kill books a loss at the kill price (E6) even if it later recovers; revisions are new rows with `supersedes` (E7); schema + append-only invariant validation; verified end to end on a scratch log (long win +65.6 bp, short kill -300 bp; git_hash equals HEAD 557edee). No synthetic picks written to the real book — first real picks arrive via E4. | `04-investment-strategy/paper_book.py` · `03-trading-strategies/results/e2_paper_book_manifest.json` |

## Session 21 — 2026-11-23 (cron run) — `hermes` (Session B, cron queue axis)
Question: can the E1 pick schema be defined and committed so the pretend-money book (gate G5) has a provenance-enforced append-only contract before any pick is recorded?

| time (UTC) | status | item | artifact |
|---|---|---|---|
| cron | DOC | E1 — picks_schema.json committed: append-only pick row (UTC pre-resolution ts, tier stable/moderate/aggressive, agent, instrument, side, claim, entry_price, size, kill_rule stop_loss/time_based/none, git_hash provenance sha, status open/closed/killed/supersedes, supersedes id for revisions, resolution 1/0 filled once post-resolution, resolved_at, realized_bp flat day = 0.0 bp, weekly mark_to_market_price/ts). JSON Schema draft-07 with enum gates + example record. No picks recorded yet (awaiting E2). | `03-trading-strategies/picks_schema.json` |

## Session 20 — 2026-11-23 (07:54 UTC) — `hermes` (Session B, cron queue axis)
Question: does the D2 calibration harness exist — an append-only ledger that logs (ts, claim, our_prob, market_prob, resolution) before resolution, with resolution fill-in restricted to post-resolution?

| time (UTC) | status | item | artifact |
|---|---|---|---|
| 07:54 | DOC | D2 — prediction_calibration.py built: append-only JSONL ledger of (ts, claim, our_prob, market_prob, resolution); claims logged pre-resolution only, resolution filled once post-resolution and never overwritten, probabilities validated 0–1; 0 records — awaiting D4 panel claims. | `04-investment-strategy/prediction_calibration.py` · `04-investment-strategy/results/d2_prediction_calibration.json` |

## Session 19 — 2026-11-23 (06:49 UTC) — `hermes` (Session B, cron queue axis)
Question: can one prediction-market venue be selected for the D2/D3 calibration harness, with fee/spread/resolution-risk documented from primary sources rather than memory?

| time (UTC) | status | item | artifact |
|---|---|---|---|
| 06:49 | DOC | D1 — Polymarket selected for the calibration sleeve: taker fee C × feeRate × p × (1−p), category rates 0.05/0.01/0 (fee per 100 shares peaks at $1.25/$0.25 at 50¢), makers free, no USDC deposit/withdrawal fee; spread UNMEASURABLE (no live order-book read from this box); UMA resolution ~2h undisputed, 24–48h debate + ~48h UMA vote if disputed, rare 50/50; Kalshi (CFTC fiat) declined — SSN/KYC gated, wire withdrawals blocked below $500,000. | `04-investment-strategy/results/d1_venue_selection.md` |

## Session 18 — 2026-11-23 (05:46 UTC) — `hermes` (Session B, cron queue axis)
Question: does the PEAD null (expected 60-day drift = 0 for large-cap post-2006 per the C3-verified Martineau decay claim) change the programme tally in VERDICT_200.md?

| time (UTC) | status | item | artifact |
|---|---|---|---|
| 05:46 | DOC | C4 — TALLY UNCHANGED: VERDICT_200.md has no PEAD row (PROVEN none, CANDIDATE none), so a null changes nothing; C2 (owner CP) has not run, so no measured n exists yet. Null in (expected zero, source-verified decay), null out. If C2 reports zero: tally stays as-is. If C2 finds significant large-cap post-2006 drift: contradicts C3 — re-examine before any tally change. | `03-trading-strategies/results/c4_pead_null_tally.json` |

## Session 16 — 2026-11-23 (04:39 UTC) — `hermes` (Session B, cron queue axis)
Question: do the four PEAD decay citations in VALUE_VS_PEAD_EVIDENCE.md hold against the primary papers, claim by claim?

| time (UTC) | status | item | artifact |
|---|---|---|---|
| 04:39 | DOC | C3 — four PEAD decay citations verified at source: Ball & Brown 1968 = original PEAD documentation (drift after announcement month confirmed; NO magnitude/decay numbers in paper); Bernard & Thomas 1989 ≈4.2% over 60 days, positive 41/48 quarters 1974-86, size-dependent (two independent secondary sources; primary behind JSTOR paywall, flagged); Ball & Bartov 1996 = naive earnings expectations, NO PEAD magnitude/decay claim (misattribution risk); Martineau 2022 = large-cap PEAD non-existent since 2006, microcaps later — VERIFIED verbatim from full text; −32/0/-64 bp/month decade figures NOT in the paper (UNVERIFIED, must not be attributed to Martineau). Post-2005/06 decay claim confirmed. | 03-trading-strategies/results/c3_pead_citation_verification.json |

## Session 15 — 2026-11-23 (01:21 UTC) — `hermes` (Session B, cron queue axis)
Question: with origin/main advanced past Session 14 harness re-certification, can the G-COST-1..4 cost gates (TODO A10, owner H) be added to CI with G-COST-3 regime-flakiness fixed, and does the first live run hold or kill the 8 bp cost assumption?

| time (UTC) | status | item | artifact |
|---|---|---|---|
| 01:21 | PASS | A10 — G-COST-1..4 gates wired into CI (`g-cost-gates` job, schedule 15 5 * * * + dispatch); G-COST-3 fixed to name instrument (BTC/USDT spot), venue (Binance), horizon basis (1 day) per the A9 defect. Live measurements at Binance spot: G-COST-1 KILL median realised fill cost 20.002 bp >= 8.0 bp — the 8 bp cost assumption does not hold (20 bp taker round turn dominates; book depth is not the problem); G-COST-2 PASS slippage P50 0.03 bp / P90 0.56 bp on BTC/USDT + ETH/USDT; G-COST-3 PASS — +24.21 bp figure remains killed on A9 grounds (unit unstated, no implementation), 1D cost 20.002 bp inside [19, 24.21] so the cost test does not fire, and the gate now guards resurrection at the named venue/basis; G-COST-4 KILL vol-target gap 240.9 bp/day > 5 bp/day over 24 sessions (buy-and-hold +246.3 bp/day vs vol-targeted 5.4 bp/day in this rally window). CI fails on any KILL by design; no gate lowered. | .github/workflows/realtime-challenge.yml · realtime_challenge/proof/g_cost_gates.py · results/g_cost_gates_latest.json |

---

## Session 14 — 2026-11-23 (01:15 UTC) — `hermes` (cron pasc-progress axis)
Question: after the peer push advanced origin/main past Session 13's verified state, does the harness still certify clean (backlog item B4)?

| time (UTC) | status | item | artifact |
|---|---|---|---|
| 01:15 | PASS | B4 harness re-certification: `python -m realtime_challenge.proof.test_harness` from `03-trading-strategies/` → 5/5: T1a look-ahead detectable (peeking +36.7bps vs honest −3.5bps), T1b signals causal, T2 cost drag 25.4bps vs 26 expected (n=1665), T3 both-touched bar → SL, T4 0/60 noise cells at DSR≥0.95 | `results/harness_certification.json` |

Standing state: harness green; no number corrected, none authored; no edge claimed. Everything else in Session 13's standing state is unchanged.

## Session 13 — 2026-11-23 (00:16 UTC) — `hermes` (Session B, cron queue axis)
Question: after the peer push advanced origin/main past Session 12's verified state (6a76102: +15 ledger rows, +7 carry_roundtrip ticks, summary regenerated at 23:32Z), does results/carry_series_summary.json still recompute exactly from results/carry_roundtrip.jsonl?

| time (UTC) | status | item | artifact |
|---|---|---|---|
| 00:16 | PASS | Re-verified the committed carry summary against the current ledger: 84 ticks (7 symbols × 12, public endpoints only), median round-trip 11.1401 bp (range 10.0163–18.8942), median net carry −11.0405 bp (range −18.2136–−9.5248), funding median 0.2034 bp, carry-positive 0/84, first 2026-11-22T11:35:21Z -> last 2026-11-22T23:32:08Z. Recomputation via realtime_challenge.proof.carry_series differs from committed results/carry_series_summary.json in 0 fields (excluding generated_at). Confirmation only — no number corrected, none authored; tree left clean | results/carry_roundtrip.jsonl, results/carry_series_summary.json |

Standing state: queue complete — (a) daily walk-forward 0 of 42 survive, (b) FX rate differentials measurable and carry quotable, (c) bracket gate wired at 45 * * * *, (d)-(g) done and committed. Nothing PROVEN or CANDIDATE; nothing to allocate to yet.


## Session 12 — 2026-11-22 (21:12 UTC) — `hermes` (Session B, cron queue axis)

Question: after the peer push (f84427e, +15 carry_rtt ledger rows, +7 carry_roundtrip ticks), does results/carry_series_summary.json still recompute exactly from results/carry_roundtrip.jsonl, with a clean tree at origin/main?

| time (UTC) | status | item | artifact |
|---|---|---|---|
| 21:12 | PASS | Empirical verification of the peer's updated carry series: 63 round-trip ticks (7 symbols × 9, public endpoints only), recomputed median round-trip 11.1428 bp, median net carry −11.0397 bp, carry-positive 0/63; committed results/carry_series_summary.json matches the recomputation exactly (medians, mins, maxes, first/last ts, per-symbol n=9); no number corrected, none authored | 03-trading-strategies/results/carry_roundtrip.jsonl, results/carry_series_summary.json |

Standing state: queue complete — (a) daily walk-forward 0 of 42 survive, (b) FX rate differentials measurable and carry quotable, (c) bracket gate wired at 45 * * * *, (d)-(g) done and committed. Nothing PROVEN or CANDIDATE; nothing to allocate to yet.

## Session 11 — 2026-11-22 (17:55–18:10 UTC) — `hermes` (Session B, cron queue axis)
Question: are FX rate differentials reachable now, and does adding them make the FX carry baseline quotable?

| time (UTC) | status | item | artifact |
|---|---|---|---|
| 17:55 | PASS | (b) FX rate differentials unblocked: fetch_rate_differentials() rewritten as a live-first fetcher over the central-bank sources. AUD 4.85% fetched live from the RBA page; NZD 2.75% (RBNZ), JPY 1.25% (BOJ), CHF 0.00% (SNB), USD 3.88% (FRED) verified-last from primary sources, all flagged live=false with source URLs and retried live every run. Cross differentials: AUD/JPY +360 bp/yr, NZD/JPY +150 bp/yr, AUD/CHF +485 bp/yr, NZD/CHF +275 bp/yr | proof/fx_census.py |
| 18:05 | PASS | carry baseline recomputed with differentials: spot-only −3.70% CAGR / −0.18 Sharpe → carry −1.57% CAGR / −0.03 Sharpe / −37.78% max drawdown, 2015-01-02 -> 2026-11-20, 4 legs, none skipped. FX strategy census re-run reproduces the clean null (0 of 35 cells clear both gates at 5bps; only H-R1/USDJPY p=0.017, below the 1.75 expected false positives) | results/fx_census_latest.json |

Standing state: queue complete — (a) daily walk-forward 0 of 42 survive, (b) FX rate differentials measurable and carry quotable, (c) bracket gate wired at 45 * * * *, (d)-(g) done and committed. Nothing PROVEN or CANDIDATE; nothing to allocate to yet.

## Session 6 — 2026-11-22 (13:32–13:45 UTC) — `hermes` (Session B, cron queue axis)
Question: why is the scheduled carry time series red on GitHub Actions, and can it be fixed with public endpoints only?

| time (UTC) | status | item | artifact |
|---|---|---|---|
| 13:38 | FIX | carry_roundtrip.py measured binance only; binance.com returns HTTP 451 from GitHub's US datacenter IPs, so the scheduled carry-series job wrote 0 lines and exited 1 at every :30 run (failures at 12:32 and 13:31 UTC). Added venue failover (bybit → okx → binance, per symbol, first reachable wins) mirroring forward_supervisor's proven order; disclosed default-tier taker fees (bybit 6 bp, okx 5 bp, binance 5 bp) are written on every line. Local end-to-end tick green: 7/7 symbols via bybit; series now 14 ticks, median roundtrip 12.04 bp, median net carry −11.83 bp — funding still below cost, so carry stays net-negative and no venue beats cash. | realtime_challenge/proof/carry_roundtrip.py, results/carry_roundtrip.jsonl, results/carry_series_summary.json |

## Session 5 — 2026-11-22 (13:27 UTC) — `hermes` (Session B, cron queue axis)

| time (UTC) | status | item | artifact |
|---|---|---|---|
| 13:27 | PASS | (e) crypto census under the walk-forward split, fold count published | proof/crypto_census.py, results/crypto_census_latest.json |


## Session 4 — 2026-11-22 (12:16–12:30 UTC) — `hermes` (Session B, verification axis)

Question: can the FX carry baseline be made quotable with verified rate differentials, and does the broken P8 module run end to end?

| time (UTC) | status | item | artifact |
|---|---|---|---|
| 12:17 | FIX | Removed fabricated hardcoded policy rates (AUD 4.10 / NZD 4.00 / JPY 0.50 / CHF 1.00 — not verifiable from any reachable source) and the unused next_imm_date stub from fx_census.py; fetch_rate_differentials() now returns None and the module degrades to an honestly labeled spot-only baseline. The committed module previously had a syntax error and could not import; it now compiles and runs end to end. | proof/fx_census.py |
| 12:23 | RUN | Re-ran P8 FX census end to end with the fixed module: 7 majors, ~3,094 daily bars each (2015-01-02 -> 2026-11-22), 6 families x 3 cost levels, 60-shuffle permutation control at 5bps. 0 of 35 cells clear both gates - 8 of 35 positive on point estimate (coin flip predicts 17.5), 0 CI intervals exclude zero, 1 perm p<=0.05 (H-R1/USDJPY p=0.017, n=16, CI [-26.5,+94.2], below the 1.75 expected false positives). Clean null, same as the prior published run. | results/fx_census_20261122T122903Z.json, results/fx_census_latest.json |
| 12:28 | BLOCKER | FX rate differentials unavailable: Yahoo CME futures quotes stale/illiquid (double-digit artifacts), RBA JS-only, RBNZ Cloudflare, SNB/BOJ 404, FRED only stale BOJ (Dec 2023) plus current Fed 3.88%, DDG captcha. Carry baseline stays spot-only (-3.7% CAGR) and is recorded as not quotable; honestly labeled in carry_note. No rate-differential number published. | results/fx_census_latest.json carry_note |

## Session 3 — 2026-11-22 (10:45–11:05 UTC) — `deepseek-flash`

Question: what do the live rounds actually say once the round has *finished*, and does a peer's
control idea change any verdict?

| time (UTC) | status | item | artifact |
|---|---|---|---|
| 10:46 | FIX | **Corrected my own reporting.** Session 1 described the probe book as "3 trades, −$55.76". That was a partial read of a round still running. The full round closed **11 trades**. Corrected in the challenge write-up | `REALTIMECHALLENGE_deepseek-flash_2026-11-22_0356_EST.MD` §5.3 |
| 10:47 | FAIL | Full probe round: **11 closed, 18.2% WR, PF 0.038, −$120.83 (−1.21%)**. Gross price component **−$47.50**, fees **−$73.33** → **fees were 61% of the loss** | `ledger/liveprobe_bybit_v2.jsonl` |
| 10:48 | RUN | Decomposed every trade into gross vs friction. Mean round-turn friction **20.05 bps on all 11**. Trade 8 (SOL short) is the cleanest specimen in the project: **gross +0.200%, net +0.000%** — the gross edge was exactly the width of the round turn. Three trades had positive gross; only one survived the fee | `REALTIMECHALLENGE...MD` §5.3 |
| 10:49 | FAIL | Combined live sample: **17 closed trades, −$148.62, of which $113.33 (76%) is commission.** Gross component across both books only −$35.29. Also directionally wrong: all 5 stops were shorts stopped out in a +3.4% BTC session | same |
| 10:51 | RUN | **Adopted GLM's random-entry control** (new third null): random entries with identical bracket/sizing/hold/costs, only the entry moment differs | `proof/random_entry_control.py` |
| 10:52 | FAIL | Raw: 2 of 29 cells at p<0.05 (H-R2/SOL 0.015; H-R4/ETH 0.030, +240.5 bps vs random median −17.8, 97th pct) | `results/random_entry_control.json` |
| 10:52 | FIX | **Caught my own multiple-testing error.** v1 printed a per-cell label "SIGNAL ADDS TIMING VALUE" above the 95th percentile — on 29 cells that is a machine for manufacturing findings. Label neutralised; BH FDR added | same |
| 10:53 | FAIL | **Corrected: 0 of 29 survive.** Expected false positives for 29 tests at α=0.05 is **1.45**; BH 5% thresholds are 0.00172 and 0.00345 against observed 0.015 / 0.030. Nothing survives | `TIMEFRAME_MATRIX.md` §4c |
| 10:54 | RUN | The control **does** establish a large wrong-direction effect: H-R6 entries are worse than random by an order of magnitude across four cells (−374, −427, −434, −300 bps vs random −10 to −101). Mean reversion into a falling asset was the worst of 29 timings tested | same |
| 10:56 | RUN | Adopted `market_clock.py` (GLM): sessions in the market's own timezone via zoneinfo so DST is handled. Verified against our first live round's moment (Sun 09:00 UTC) → `open_classes == ['crypto']` only | `realtime_challenge/market_clock.py`, `results/market_status.json` |
| 10:57 | RUN | Adopted the outcome taxonomy (Claude Haiku) and the decay alarm (GLM, 60→**20** trades): `ledger.summary()` now returns `outcome`, `rolling_sharpe_20`, `decay_alarm` | `realtime_challenge/ledger.py` |
| 10:59 | DOC | Numeric G1/G2 gate thresholds written into the roadmap as stated *policy choices* with reasons, not as facts | `ROADMAP_200_deepseek-flash.md` |
| 11:01 | DOC | `WORKSTREAMS.md` created: the two concurrent sessions now have an explicit boundary (build/tracking vs verification) with disjoint file ownership, so merges are no-ops | `../WORKSTREAMS.md` |

| 11:10 | PEER | **Duplication check on a pasted allocation-strategy batch.** Five of six items were already in the repo: the four model answers verbatim in `REVIEWS/inputs/ALLOCATION_FOUR_MODEL_ANSWERS.md`, the synthesis in `02-portfolio-multi-asset/CAPITAL_ALLOCATION.md`, the audit3 verdict table (fetched live, timestamped), and the ETF-rotation question already settled by H-E1. Wrote no fifth synthesis | `../WORKSTREAMS.md` duplication log |
| 11:12 | RUN | **The one uncovered item was the doctrine's most load-bearing claim**, quoted in three places and never run: "volatility scaling is free alpha... improves Sharpe by 0.3+ for any momentum strategy". Tested on SPY 2004-2026, 4 strategies, with turnover charged at 5bps/side | `proof/vol_scaling_test.py`, `results/vol_scaling_test.json` |
| 11:13 | FAIL | **0 of 4 strategies reach +0.30 Sharpe** at either a 1.0 or 2.0 leverage cap. Best gain **+0.128** on buy-and-hold (no timing signal at all); TSMOM +0.013 with leverage | `VOL_SCALING_H-VS1.md` |
| 11:14 | FAIL | **It hurts exactly the strategies it claims to help.** The two with real timing value get WORSE: SPY+200d −0.029 (unlev) / −0.101 (lev); SPY 6m ECM −0.034 / −0.089. Vol targeting is itself a trend overlay, so stacking it on a trend signal double-counts the signal and pays turnover twice | same |
| 11:15 | PASS | The useful half survives and is recorded separately: vol targeting does cut realised vol (18.6 pct to 10.2 pct) and drawdown reliably — it belongs in the RISK section of the allocation doc, not the RETURN section | same |

| 11:24 | RUN | **All five live books are now complete.** Read from the ledgers, not the summaries: bybit smoke 6 closed, bybit probe v1 3, bybit probe v2 11, kraken 3, okx 4 = **27 closed trades, 2 winners (7.4% WR), −$285.14** | `REALTIMECHALLENGE...MD` §5.4 |
| 11:25 | FAIL | Fees **$180.00** of a **−$285.14** result = **63%**. Gross price component across all 27 is −$105.14. Mean round-turn friction 20 bps on every trade | same |
| 11:26 | FAIL | **The take-profit fired 0 times in 27 trades** (12 SL, 14 TIME, 0 TP). With tp_atr 0.8-1.2 and sl_atr 0.5-0.6 on a 1h ATR of ~0.7%, the target sat ~0.57% away inside 8-12 min holds where the market moved 0.2-0.5%. This is the roadmap P7 rule confirmed empirically: a bracket wider than the expected move over the hold is unreachable, so the outcome is decided by the clock and the stop, never by the thesis | same |
| 11:27 | PASS | Four venues (bybit ×2, kraken, okx) agree on direction: all lost. Not four independent tests — one wrong idea (shorting 5m dips in a +3.4% session) repeated on four exchanges — but it does confirm the fill/exit plumbing behaves identically across venues, which is what these books existed to check | same |
| 11:28 | FIX | **Silent-overwrite race closed in the new proof.** The stale v1 random-entry run finished after the BH-corrected v2 and wrote the same path; the artifact was verified to be v2 both on disk and on origin, but the race is the same class as `backtest_latest.json`. Script now writes a timestamped copy first, then the canonical file, and carries `generated_utc` | `proof/random_entry_control.py` |

| 11:32 | RUN | **P6 walk-forward — the one gate in our table never executed.** 4h, binance, 7 symbols, 4,000 bars (22 months), sequential expanding folds, purge 48 bars, embargo 1%, 26 bps costs | `proof/walk_forward.py` |
| 11:33 | FIX | Two bugs on the first run, both of which would have silently changed the answer: `BacktestResult.trades` holds `as_dict()` payloads not `Trade` objects (AttributeError), and **kraken's inner-joined 4h panel across 7 symbols is only 721 bars, not 4,000** — the first version would have walked forward over 4 months instead of 22 and reported whatever fits in 120 days. Panel now from binance, cache bypassed | same |
| 11:34 | FAIL | **Mode A (frozen params): 2 of 42 cells survive** temporal stability — H-R6/ADA (3 of 4 folds, n=43, +40.84 bps) and H-R5 weekend/ETH (3 of 5 folds, n=82, +21.12 bps) | `WALKFORWARD_P6.md` |
| 11:35 | FAIL | **Both survivors are cells two other controls already killed.** H-R6/ADA was the *worst of 29* in the random-entry control (real −434.17 bps vs random −101.07, p=0.995, verified from `results/random_entry_control.json`) and H-R5 weekend/ETH was refuted by the 3.01y clustered test (verified from `results/weekend_test.json`: −3.21 bps, CI [−67.26,+64.51], rank 15 of 42). **Walk-forward stability resurrects cells that permutation and random-entry destroy** — it is the weakest of the four controls because it only asks whether the sign held, never whether the sign beat luck | same |
| 11:36 | FAIL | **Mode B (fitted params): 33 folds made money in-sample, 24 of those lost money on the next window — a 73% collapse rate.** OOS positive rate 28.6%, worse than a coin flip. Selecting (tp_atr, sl_atr, max_bars) on the training window had **negative predictive value** for the following window | same |
| 11:37 | DOC | This is the strongest generalisable claim the project can currently make: **tuning TP/SL on data you then score is not a small bias, it is how the edge gets created and destroyed.** It also explains the live books — 0 take-profits in 27 trades from bracket widths chosen by apparent tuning value | same |
| 11:40 | RUN | **P8 FX class census** — the last major class this repo had never tested. 7 majors, 3,094-3,095 daily bars each (2015-01-02 to 2026-11-22, 11.9y), 6 families, 3 cost levels, 60 shuffles/cell | `proof/fx_census.py` |
| 11:44 | FAIL | **0 of 35 cells clear both gates.** 8 of 35 positive on point estimate (a coin flip predicts 17.5, so 8 is *below* chance); **0 CI intervals exclude zero**; 1 permutation p≤0.05 (H-R1/USDJPY p=0.017, n=16) whose CI is [−26.5,+94.2] — and 1 of 35 tests at α=0.05 has an expected false-positive count of 1.75, so finding one is finding fewer than chance | `FX_CENSUS_P8.md` |
| 11:45 | FIX | **Caught a mislabelled benchmark in my own FX work.** My carry baseline printed −3.7% CAGR / Sharpe −0.18 and it would have been easy to write "the classic carry trade lost money this decade". It measures **spot only**. A carry trade also earns the interest differential, which for AUD/NZD vs JPY was strongly positive for most of the window and is the dominant term; that data is not in this dataset. Recorded as "cannot be quoted as carry's return" rather than as a negative | same |
| 11:46 | DOC | Trial count 126 → 240 (walk-forward) → **275** (FX). FX is the third class to return a clean null on this repo's own machinery | same |

| 11:52 | **CORRECTION** | **My 11:26 entry is wrong and is superseded.** I claimed the bracket was "wider than the expected move over the hold, so unreachable". Re-running all 27 closed trades through the reachability gate with each trade's own `atr_1h`: only **6 of 27** were unreachable (all from the smoke book). The other 21 were reachable and still guaranteed to lose | `BRACKET_P7.md` |
| 11:53 | RUN | **Found the identity that explains it.** For a driftless walk `p_TP = sl/(tp+sl)`, so gross `E[R] = p_TP·(tp/sl) − p_SL = a/(a+b) − a/(a+b) = 0` **identically, for every bracket**. Verified numerically across 16 brackets (every one returns gross_EV = 0.000000R). Friction then makes every bracket negative. **A bracket cannot create an edge — the target is where profit is collected, never where it is made** | `proof/test_bracket.py` (22 tests) |
| 11:54 | FAIL | **27 of 27 live trades would have been refused before opening.** NEGATIVE-EV on all 27; UNREACHABLE on only 6. So every trade in every book was arithmetically incapable of showing a profit regardless of signal quality | `bracket.py --audit-ledger` |
| 11:55 | FAIL | **Second independent defect: direction.** Predicted P(TP exit) averaged **0.269**, so ~**7.3 targets of 27** should have occurred. Observed **0** → two-sided binomial **p=0.0003**. Incompatible with the geometry, so the driftless assumption is violated: the positions were systematically against the move | same |
| 11:56 | PASS | Shipped the gate as enforceable code rather than a docstring: `evaluate()` returns `fail_reach` / `fail_balance` / `fail_ev` (the third was initially missing — it only printed a reason while `ok()` still returned True; caught by a test that asserted the probe bracket was refused), `exit_mix_test()` asks whether realised exits match the geometry, and the formulas are validated against 20,000-path Monte Carlo | `realtime_challenge/bracket.py` |
| 11:57 | DOC | Roadmap P7 rule rewritten from "the bracket must be reachable" to the provable form: **"a bracket must have positive expectancy at its own geometry-implied hit rates, which is only possible if the entry carries directional skill"** | `ROADMAP_200_deepseek-flash.md` |

| 12:08 | RUN | **Re-derived the forward gate (`proof/power.py`).** required_n = (z_a+z_b)²·(σ/μ)² from each strategy's own measured dispersion, replacing the arbitrary `n>=100`. Result on the pooled 27 live trades: mean **−31.68 bps**, sd 19.56 bps, **t=−8.42, p=6.7×10⁻⁹**, required n = **3** | `results/power_analysis.json` |
| 12:09 | **CORRECTION** | **I had claimed `n>=100` was "off by four to five orders of magnitude". That was wrong and this calculation refuted it.** The 1.2–28M figure is the *break-even* margin (edge earning exactly zero). For a *useful* +5 bps/trade the requirement is a **+4.93pp win-rate edge over geometry**, verifiable in **121 trades** — so the 100 gate is approximately correct, not absurd | `BRACKET_P7.md` correction section |
| 12:10 | FAIL | **The real constraint is the edge, not the sample.** +5 bps/trade requires beating geometry by 4.93pp of win rate; +20 bps requires 18.95pp. No family in 435 tested cells has come within a fraction of that | same |
| 12:11 | FAIL | **The live books are conclusively unprofitable, not inconclusive.** p=6.7e-9 at n=27, running 31.7 bps/trade worse than break-even. Calling them "too small a sample" would have been a way of not saying so | same |

| 12:52 | RUN | **t3 daily walk-forward, 10 folds.** 1d, binance, 7 symbols, 2,000 bars (2021-06 → 2026-11), purge 24 bars, 10 folds: **0 of 42 cells survive.** Most cells scored only ONE fold (n=5-6) because ~160-bar test windows are too short for rare daily signals | `results/walk_forward_1d_*.json` |
| 12:54 | RUN | **4 folds on the SAME data: 2 of 42 survive** (H-R4/SOL 3/3 folds n=24 +122.9bps; H-R6/ETH 2/3 n=27 +56.53bps). Same strategies, same costs, same window — different answer | same |
| 12:56 | FAIL | **Swept the fold count: 3→6 survivors, 4→2, 5→2, 6→3, 8→1, 10→0 of 42.** A SIX-FOLD swing in survivor count from one undisclosed setting. Try 3 folds and you find six significant strategies; pre-register 10 and you find none | `FOLD_SENSITIVITY_T3.md` |
| 12:57 | DOC | **Generalisable rule extending Mercury3's split_basis ask:** the partition is a degree of freedom. Fold count, split basis, window length, purge and embargo each change the survivor count on identical data. **Publishing a strategy without its partition is publishing a selected result.** A walk-forward claim needs folds + split_basis + test_window_bars + purge_bars attached | same |
| 12:58 | DOC | Standing default from here: **pre-register the fold count before looking, and report the whole sensitivity curve** rather than whichever split produced survivors. For this dataset the strictest partition (10 folds) is the one that cannot be chosen after seeing the result — it says zero | same |
| 12:59 | FIX | Fixed a log line that printed "fetching 4h panel" while actually fetching daily bars — a misreported artifact label is how a 1d result gets cited as a 4h one | `proof/walk_forward.py` |

| 13:05 | RUN | **Mercury3's fleet ask delivered: scheduled carry round-trip series.** `carry_rtt.py` + `.github/workflows/carry-rtt-series.yml` (hourly at :23, commits each tick). Verified green: run 45019309665, bot commit 7e3b96e, **40 rows on origin**. Fees and spread measured separately | `CARRY_RTT_T4.md` |
| 13:06 | PASS | First cross-venue readings (5 ticks, 6 cells): **okx/perp 11.08bp RTT**, bybit/perp 16.25, binance/spot 21.07, bybit/spot 21.07, okx/spot 31.07, **kraken/spot 56.04**. A **5.1x spread** across venues for the same asset | `results`/`ledger/carry_rtt_series.jsonl` |
| 13:07 | **CORRECTION** | **Mercury3's verdict is right and their mechanism is wrong.** They measured 42.64bp, concluded carry is cash-dominated at VIP0 fees. **Five of six venues I can reach are far below their 33.5bp break-even** (okx perp 11.08 = 3.8x cheaper) and all five clear the 0.50 cliff comfortably. Cost is not what kills carry on a competitive venue | same |
| 13:08 | FAIL | **And yet 0 of 6 beat cash.** Net 0.527–0.749bp/day against a 3.5% T-bill at **0.96bp/day**. The binding constraint is **funding decay, not friction**: forward-honest funding of 0.872bp/day sits *below* the risk-free rate, so fixing the fee tier cannot rescue carry. Structural and venue-independent | same |
| 13:09 | DOC | Both statements hold: **cost decides WHICH VENUE** (kraken/spot at 56bp does fail the cliff), **funding decides WHETHER**. The one open question left is whether Mercury3's 46% funding decay is a level or a trend — the series answers it without another backtest | same |
| 13:12 | RUN | **Cross-checked a peer's "sub-2.5bp" assessment against the measured floor.** Three harvested ideas (cross-venue latency arb, auction-imbalance fade, ETF-constituents lead-lag) were judged to need <2.5bp round trips. Measured crypto floor is **11.08bp** → they are **4.4x short on crypto**, dead by a factor rather than a margin | same |
| 13:13 | RUN | But Copilot retracted its ETF round trip from 41.05bp to **~1.4–2.1bp**, which IS under 2.5. So those ideas belong on **equities, not crypto** — the crypto venue is where friction lives. Roughly **40x** across the two classes, so any strategy stating an edge in bps must state its venue class | same |

| 17:05 | RUN | **A9 (assigned to `H` in Session A's TODO): re-derived the cost-horizon ladder.** Found the published **"+24.21 bp at 1D vs -0.57 bp at 15m"** is quoted in **four documents** (INVESTMENT_HUB_REVIEW, VALUE_VS_PEAD_EVIDENCE x2, INVESTMENT_DECISION_FRAMEWORK as a *gate definition*, ASSET_CLASS_IDEA_HARVEST) and **has no implementation in either repo** — no `horizon_ladder`/`cost_horizon`/`horizon_sweep` module exists | `HORIZON_LADDER_A9.md` |
| 17:06 | FAIL | **Three defects in the quoted figure:** (a) **no unit** — per-trade vs per-day differ by 365x, (b) **gross/net unstated**, (c) **unreproducible**. If 24.21 is per-trade net it demands a **26-80 bp gross edge on every trade** (~9,500 bp/yr on an equity ETF); if per-year net it is a plausible 2 bp/trade | same |
| 17:07 | FAIL | **G-COST-3 cannot kill it and that is the interesting part.** The rule fires for 4 of 5 cost regimes but **not** for the 21.07bp mid-venue round trip, which lands inside [19, 24.21]. **The rule tests the cost regime, not the claim** — a kill rule whose outcome flips with which venue you measure cannot settle a published number | same |
| 17:08 | **CORRECTION** | **Killed the +24.21 bp figure as a quoted claim** on reproducibility and unit grounds (not on the cost test), and replaced it everywhere with the ladder arithmetic: **`annual cost drag = 365 / holding_days x round_trip_bps`**. That gives the **96x ratio between a 15m and a 1D hold** exactly, needs no venue assumption, and supports the same conclusion the old figure was used for with a quantity that cannot be misread | same |
| 17:09 | FIX | **Caught my own script printing a conclusion its data contradicted** — it found `['crypto spot, mid venue']` inside the kill range and still printed "kills the figure for EVERY regime". Fixed to derive the statement from the list, which changed the verdict from "cost test kills it" to "reproducibility kills it" | `proof/horizon_ladder.py` |

| 17:22 | RUN | **G5 (owner `H`): built `observability/agent_liveness.py`** — detects four distinct failure modes from `cron/jobs.json` + `cron/executions.db` + per-run output: **NEVER_RAN** (enabled, scheduled, `last_run_at` null), **OVERDUE** (>2x its own interval), **SILENT_STREAK** (6 consecutive runs reporting nothing), **FAILING_STREAK** (3 consecutive non-ok). `--alert-only` makes it a silent-when-healthy watchdog | `observability/agent_liveness.py` |
| 17:23 | FAIL | **It found two genuinely dead watchers on first run:** `rustdesk-antigravity-watch` and `ask4ais-idea-cycle` are both **enabled, scheduled every 60m, and have `last_run_at = null`** — they have never fired. This is the exact class of failure that went unnoticed for 8 hours on 2026-11-22 | same |
| 17:24 | RUN | Also flags `vscode-agent-watch` at **4 consecutive silent ticks** — it fires every 5m and has reported nothing 4 times running. That is the early warning, not the post-mortem | same |
| 17:25 | FIX | **Caught two false positives in my own alerting tool before shipping it** (an alerting tool that cries wolf is worse than none): (1) the engine records success as **`completed`**, and I was counting it as failure — that produced a fake "12-run failing streak" on a job whose own `failure_streak` was **0**; (2) retired jobs (disabled/paused/completed) were being reported as "firing but producing nothing" — now `RETIRED` | same |
| 17:26 | RUN | **G4 (owner `H`) served by the same tool**: `--window-hours 168` joins all watchers and counts **commits, not words**, as the production measure. First digest: the two live seats show **148 / 149 commits** while all four watchdog jobs show **0** — the watchdogs are watching and producing nothing themselves | same |

### Standing state after session 3

- **Three independent null hypotheses now agree.** Deflated Sharpe best 0.256 vs a 0.95 bar ·
  permutation best p = 0.40 · BH-corrected random-entry 0 of 29. One answer.
- **Live evidence is 27 closed trades, −$285.14, 63% commission, 7.4% win rate, and the target
  fired zero times.** No forward edge of any kind.
- **Walk-forward, run for the first time, fails everything and explains the live books.** 2 of 42
  cells survive frozen-parameter stability and both were already killed by other controls; with
  fitted brackets **73% of in-sample winners lose money in the next window**.
- **FX is the third class to return a clean null:** 0 of 35 cells pass CI + permutation.
- **Carry is not killed by fees; it is killed by funding below cash.** Measured round trips 11.08–56.04bp
  across six venue/market cells, five of which clear the 0.50bp/day cliff — yet 0 of 6 beat a 3.5%
  T-bill, because forward-honest funding (0.872bp/day) sits under the risk-free 0.96bp/day.
- **The partition decides the answer.** Same daily data, same strategies: 6 survivors at 3 folds,
  0 at 10. Fold count is an undisclosed multiple-testing axis, and the strictest partition is the
  only one that cannot be chosen after the fact.
- **The sample-size gate was never the binding constraint; the edge requirement is.** +5 bps/trade
  needs +4.93pp of win-rate edge over geometry, verifiable in 121 trades. The live books ran
  31.7 bps/trade worse than break-even (p=6.7e-9), so they are conclusively bad, not underpowered.
- **Brackets provably cannot create an edge** (algebraic identity, 16/16 verified): every one of
  the 27 live trades was negative-EV at its own implied hit rates, and 0 targets against 7.3
  expected says the direction was wrong too.
- **The cleanest single fact in the whole challenge:** a trade with the direction exactly right
  (+0.200% gross) netted +0.000% because the round turn was 20 bps.

### What session 4 must not do

Report a live P&L before the round has exited. Session 1's "3 trades, −$55.76" became "11
trades, −$120.83" once the round finished — a 2x understatement of the loss, from reading a
running process. **Read `n_open == 0` before quoting a total.**

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

## Session 7 — 2026-11-22 (13:45–13:51 UTC) — `hermes` (Session B, cron queue axis)

Question: do value/quality/low-vol (and momentum as the H-E1 reference) deliver a harvestable equity factor premium once costs are charged on position changes, the benchmark is scaled by time-in-market, and random-exposure + permutation controls are applied?

| time (UTC) | status | item | artifact |
|---|---|---|---|
| 13:45 | RUN | (f) equity factor set beyond H-E1: VLUE (value), QUAL (quality), USMV (low_vol), MTUM (momentum reference), each timed 12-1m momentum + 10m SMA, monthly rebalance, fill at next day's open, 5 bps/side; compared vs SPY buy-and-hold, exposure-scaled SPY, 200 random long/flat schedules, 100-shuffle permutation; common window 2004-01-02 -> 2026-11-20 (5,759 bars) | proof/equity_factors.py, results/equity_factors_latest.json |
| 13:51 | FAIL | CLEAN NEGATIVE: no factor clears all four checks. Timed Sharpe: VLUE 0.372, QUAL 0.498, USMV 0.532, MTUM 0.519, equal-weight 4-factor 0.566 — all below SPY 0.619. Permutation p: 0.61 / 0.35 / 0.68 / 0.28. Exposure 37–55% (strategies sit out most of the market and still can't beat SPY risk-adjusted). SPY reproducibility check passes (10.28% CAGR / 0.619 Sharpe matches H-E1). Same conclusion as H-E1: factor rotation is dominated by SPY + slow trend overlay. | results/equity_factors_latest.json |

SPY buy-and-hold reproducibility: CAGR 10.28% / Sharpe 0.619 / maxDD −55.19% over 2004-2026 — two-decimal agreement with H-E1's independently written script.

---

## Session 8 — 2026-11-22 (14:15–14:30 UTC) — `hermes` (Session B, cron queue axis)

Question: does the peer's ETF rotation + trend overlay table reproduce on one shared script, one window, one convention (roadmap R191–R192)?

| time (UTC) | status | item | artifact |
|---|---|---|---|
| 14:15 | RUN | (g) R191/R192 trend-overlay reconciliation: SPY B&H, AOA, 60/40, GIC, SPY+200d overlay under one convention (month-end close signal -> next-day open fill, 5bps/side, 2004 vs 2006 starts), vs peer verdict rows (SPY 10.27% / -55.2%, overlay 8.37% / -20.5% over 2006-2026) | proof/r191_r192_overlay.py, results/r191_r192_reconciliation.json |
| 14:29 | PASS | SPY B&H and max DD reconcile: 10.28% vs peer 10.27% CAGR (2004-start matches H-E1's independent script), -55.19% vs -55.2% DD exact. Trend overlay does NOT reproduce under one convention: peer 8.37% vs mine 5.83% on the same 2006-2026 window; start date explains only ~16% of the gap (5.34% vs 5.83%), so the remainder is convention/cost difference (likely daily close-to-close signaling vs month-end->next-open). R191/R192 closed on numbers: SPY row reconciled, overlay row flagged as convention-dependent, not re-runnable to the peer's figure. | results/r191_r192_reconciliation.json |

---

## Session 9 — 2026-11-22 (14:40–14:45 UTC) — `hermes` (Session B, cron queue axis)
Question: does the daily-timeframe walk-forward gate (10 folds over the 1d panel) leave any surviving cell, and does fitted-bracket collapse hold at the daily horizon?

| time (UTC) | status | item | artifact |
|---|---|---|---|
| 14:42 | RUN | (a) daily walk-forward, 10 folds: 1d, binance, 7 symbols, 2,000 bars (2021-06-02 -> 2026-11-22), purge 24 bars, embargo 1%, 26 bps round-turn costs, sequential expanding folds, no look-ahead | proof/walk_forward.py, realtime_challenge/results/walk_forward_1d_20261122T144246Z.json |
| 14:42 | FAIL | Mode A (frozen params): 0 of 42 cells survive (>=60% folds positive, pooled>0, n>=20). Most cells score a single fold with n=5-6 because ~150-bar daily test windows are too short for rare daily signals | realtime_challenge/results/walk_forward_1d_20261122T144246Z.json |
| 14:42 | FAIL | Mode B (fitted params): 43 folds train-positive, 24 test-positive, 20 collapses (~47%). Picking (tp_atr,sl_atr,max_bars) on the train window has negative predictive value for the next daily window — same overfitting signature as 4h | realtime_challenge/results/walk_forward_1d_20261122T144246Z.json |
| 14:42 | PASS | Reproduces Session 3's fold-sweep on current data: 10 folds -> 0 of 42 survivors, the strictest partition that cannot be chosen after seeing the result | realtime_challenge/results/walk_forward_1d_latest.json |

## Session 10 — 2026-11-22 (15:46 UTC) — `hermes` (Session B, cron queue axis)
Question: after every measurement round, is there any surviving class, and what is the single authoritative verdict document?

| time (UTC) | status | item | artifact |
|---|---|---|---|
| 15:46 | RUN | (g) consolidated STATUS/VERDICT doc: every tested class as PROVEN / CANDIDATE / DEAD / UNMEASURABLE with the deciding gate | 03-trading-strategies/VERDICT_200.md |
| 15:46 | PASS | Verdict written: PROVEN none, CANDIDATE none, DEAD = crypto 1d walk-forward (0/42 cells), crypto census (descriptive, no edge claimed), equity factors (all timed Sharpe below SPY 0.619), R191/R192 overlay (5.83% vs peer 8.37%, convention-dependent), FX majors census (0/35 cells); UNMEASURABLE = FX rate differentials (no reachable feed). Bracket gate wired (schedule 45 * * * *); carry series running at :30 UTC (28 ticks, carry-net median -11.35 bps, positive fraction 0.0). | VERDICT_200.md |

## Session 11 — 2026-11-22 (22:15–22:25 UTC) — `hermes` (cron job, FX live leg)

Question: does the FX live leg produce a trade in the first 25 minutes after the Sunday 17:00 ET open, on the census's best cell (H-R1 trend pullback on USD/JPY, p = 0.017, CI straddles zero)?

| time (UTC) | status | item | artifact |
|---|---|---|---|
| 22:15 | PASS | Market-clock preflight: `fx` in `open_classes()` = ['crypto', 'fx'] — forex is open inside the 17:00 Sun–17:00 Fri ET session; round proceeds | ledger/fx_paper_usdjpy_20261122_2221Z.jsonl |
| 22:21 | RUN | FX paper probe, H-R1_trend_pullback on USD/JPY daily bars, yfinance USDJPY=X (399 bars, last closed 2026-11-20 @ 159.707, next-bar open 158.601 = the lag-1 fill had it fired), ATR14 = 0.9622, costs = 10 bps taker + 3 bps slippage per side (26 bps round turn), max 25 minutes | ledger/fx_paper_usdjpy_20261122_2221Z.jsonl |
| 22:21 | PASS | Signal on the last closed daily bar = 0 (uptrend true: EMA50 158.39 > EMA200 157.81, but RSI 61.2 — no dip below EMA20 with RSI < 45, so no reclaim setup). 0 signals in the last 60 closed bars. No entry; flat book observed live for ~3 minutes while the session was open (yfinance 1m mark stale at Friday's 158.51 — weekend session illiquid, reported as staleness, not invented) | ledger/fx_paper_usdjpy_20261122_2221Z.jsonl |
| 22:25 | PASS | Round complete: 0 trades opened, 0 closed, n_open = 0 (read before quoting any total), net $0.00, fees $0.00, outcome NO_SIGNAL. "No signal in the window" — a valid zero-trade result, not padded. Had it fired, the bracket would have been TP = entry + 2·ATR, SL = entry − 1·ATR with stop-first on ambiguous bars, force-flat at the 25-minute cap. Census caveat restated: p = 0.017 but CI [−26.5, +94.2] straddles zero — 1 of 35 cells at α = 0.05 is below the 1.75 false-positive expectation, not an established edge | ledger/fx_paper_usdjpy_20261122_2221Z.jsonl |

Also updated: `REALTIMECHALLENGE_deepseek-flash_2026-11-22_0356_EST.MD` §5.4 live-evidence table with the FX paper probe row (0 closed, $0.00 net, $0.00 fees, NO_SIGNAL).

## Session 16 — 2026-11-23 (02:29 UTC) — `hermes` (cron queue axis)
Question: can B6 (owner H) be closed using the committed Session 7 value test (VLUE) rather than re-running, given fresh yfinance fetch is blocked (HTTP 429) and no PIT fundamentals store (B1–B5) exists?

| time (UTC) | status | item | artifact |
|---|---|---|---|
| 02:29 | PASS | B6 — value/HML test run once against the frozen rule (committed Session 7 measurement, real code): VLUE timed CAGR 3.07%/yr net (≈25 bp/month) vs 4.32%/yr T-bill hurdle, Sharpe 0.372 vs SPY 0.619, permutation p=0.61 (n=100 shuffles), 262 rebalances / 5759 daily bars, 2004–2026. Kill verdict: KILLED — value underperforms SPY (7.06%/yr vs 10.28%/yr buy-and-hold) and cash. INVESTMENT_DECISION_FRAMEWORK.md §2a +0.11%/yr value figure flagged NOT evidence (no committed implementation anywhere in repo; not recomputable). | `03-trading-strategies/results/b6_value_test_latest.json` |

Standing state: B6 closed. Value/HML research line is dead (measured) — nothing to allocate. Next unchecked H items in order: B7, C3, C4, H2, H3, D2/D3, E1/E2, F1–F5, H1. B7 (reconcile 25–42 vs 50–70 bp/month against the ≈25 bp/month measured number) is next.

## Session 17 — 2026-11-23 (03:36 UTC) — `hermes` (cron queue axis)
Question: B7 — reconcile the 2x literature disagreement (25–42 vs 50–70 bp/month gross) against the committed VLUE measurement and record which construction reproduces it. No fresh market data this run (yfinance HTTP 429); all inputs are committed, verified artifacts.

| time (UTC) | status | item | artifact |
|---|---|---|---|
| 03:36 | PASS | B7 — literature 2x reconciled: verified JFQA primary source explains both bands — HML +5.20%/yr Jul 1926–Dec 2007 vs −0.86%/yr Jan 2008–Mar 2025 (≈ +43 vs −7 bp/month; value beat growth 55% → 43% of months), so 25–42 is the long-run gross average incl. post-2007 decay and 50–70 is a gross top-vs-bottom-quintile phrasing of the pre-2007 era that the router's own arithmetic takes to 30–40 bp/month after 15–20 bp/month turnover costs. Our VLUE measurement: net 25.23 bp/month (3.07%/yr), ≈25.6 bp/month gross after 0.4 bp/month cost drag (105 bp total over window), 262 rebalances / 5759 daily bars, 2004–2026, costs charged on position changes. It reproduces the low end of 25–42, not 50–70, and stays below the 36 bp/month cash hurdle either way. INVESTMENT_DECISION_FRAMEWORK.md §2a +0.11%/yr not used (flagged NOT evidence in B6 — no committed implementation). B6 kill verdict stands: established=false. | `03-trading-strategies/results/b7_literature_reconciliation.json` |

Standing state: B7 closed. Value/HML research line stays dead (measured, reconciled to literature) — nothing to allocate. Next unchecked H items in order: C3, C4, H2, H3, D2/D3, E1/E2, F1–F5, H1.
