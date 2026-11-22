# REVIEWS

Source answers collected while researching this repo, each audited claim by claim against the actual
repositories (GitHub API), the installed software, or the measurements in
[`../01-screen-control-llm/MEASUREMENTS.md`](../01-screen-control-llm/MEASUREMENTS.md).

| Review | Input | Verdict |
|---|---|---|
| [`AGENT_MARKET_AUTOMATION_PLAYBOOK_REVIEW.md`](AGENT_MARKET_AUTOMATION_PLAYBOOK_REVIEW.md) | "Portable AI Agent Playbook" (Arena, 97 lines) | soundest of the batch; evidence rules adopted, one unverifiable citation removed |
| [`SUBQ_FURTHER_NOTE_REVIEW.md`](SUBQ_FURTHER_NOTE_REVIEW.md) | SUB Q "further note" (decided-stack version, ~3.8k words) | best-shaped answer, stale numbers, one repeated hallucination; RustDesk/RDP and intrabar advice adopted |
| [`PERPLEXITY_NOTE_REVIEW.md`](PERPLEXITY_NOTE_REVIEW.md) | Perplexity two-layer plan (~2.2k words) | most accurate on frameworks (the only answer that gets NautilusTrader's Rust core right); its twelve-tool MCP sketch became `01-*/TOOL_INTERFACE.md` |
| [`GPT41MINI_CHALLENGE_BLUEPRINT_REVIEW.md`](GPT41MINI_CHALLENGE_BLUEPRINT_REVIEW.md) | "REALTIMECHALLENGE" 200-round blueprint (GPT-4.1 mini, ~2.8k words) | best project structure, worst tool list (two dead libraries, dead data provider, wrong MCP expansion); its multiple-testing blind spot became `02-*/DATA_EVIDENCE_RULES.md` §6 and its paper loop became `02-*/PAPER_TRADING_AND_MONITORING.md` |
| [`CHALLENGE_PROTOTYPES_GLM_GEMINI_REVIEW.md`](CHALLENGE_PROTOTYPES_GLM_GEMINI_REVIEW.md) | Two challenge prototypes: GLM-5.3-Flash (111 lines) and Gemini 3.1 Pro (254 lines) | Gemini is the best document here (refuses to fake a closed trade, finds the fee trap, market data verified); GLM has the best strategy schema but a trade thesis that contradicts its own cited data |
| [`QWEN_PLUS_CHALLENGE_REVIEW.md`](QWEN_PLUS_CHALLENGE_REVIEW.md) | Qwen Plus challenge document, self-dated 2024-06-15 | **Reports a completed BTC trade at a price that never existed** (entry 61,200 on a day whose low was 65,857), plus four internal contradictions. Now the worked example in `03-*/FABRICATION_CHECKLIST.md` |
| [`CLAUDE_HAIKU_CHALLENGE_REVIEW.md`](CLAUDE_HAIKU_CHALLENGE_REVIEW.md) | Claude 5.5 Haiku challenge document with runnable code (~5.8k words) | **Best-engineered of the ten**: causal by construction, stop-first on both-touched bars, OOS verdict, self-diagnosed limits. Four fixable gaps: realized-only equity, 81 combos with no trial count, single 70/30 split, fees eat half the paper target |
| [`CLAUDE_OPUS_CHALLENGE_REVIEW.md`](CLAUDE_OPUS_CHALLENGE_REVIEW.md) | Claude 4.5 Opus challenge document, ~27.9k tokens, six Python modules (2,300 lines) | Most complete deliverable and the one to trust least: **real 2025-01-27 prices** but a 22-month anachronism and "✅ Complete" on unrun work; **seven verified code defects**, including same-bar look-ahead and a CI condition that can never match |
| [`PI_CHALLENGE_REVIEW.md`](PI_CHALLENGE_REVIEW.md) | Pi.ai challenge document (~1.1k words, no code) | Honest sketch, three silent-failure bugs: **backtrader is GPL-3.0 not MIT**, cron `0 9` is UTC not 9 AM EST, no `contents: write` so the push 403s — and SMA(30) on 15-minute bars cannot initialise inside a 26-bar session |
| [`META_MUSESPARK_CHALLENGE_REVIEW.md`](META_MUSESPARK_CHALLENGE_REVIEW.md) | Meta.ai (MuseSpark) challenge document (~4k words, conventions only) | **Best conventions of the thirteen**: `AMBIGUOUS` for both-touched bars, peer re-run keyed to a data hash, JSON-only strategy authoring, kill criteria per block. One invented tool (`own-computer-use-mcp`) and no trial counting |

Inputs are preserved verbatim in [`inputs/`](inputs/) where they were supplied as files, so the reviews can be
checked against the original wording.

## What the audits found, in aggregate

- **Recurring across answers:** accessibility-tree-first with a pixel fallback, MCP as a tool interface rather
  than a supervisor, and "the engine is not the data". All three are correct and are load-bearing here.
- **Recurring failures:** inflated or stale star counts, invented tools (`UIA-X` appeared twice with a detailed
  feature list and no repository), and confident performance numbers with no measurement behind them.

### 2026-11-22 — ChatGPT/GPT-6 architecture + the no-trade that was right

[`CHATGPT_GPT6_ARCHITECTURE_AND_NOTRADE_REVIEW.md`](CHATGPT_GPT6_ARCHITECTURE_AND_NOTRADE_REVIEW.md) — the most
honest submission of the batch: it declares every deliverable Unstarted, quotes one market observation, and
records **NO TRADE** with the reasoning *"a documented no-trade decision is better than false evidence."*

Its BTC snapshot (**$59,080–$59,316** at 09:18 UTC) was stale by ~0.7% — the quoted *high* sits $272 **below the
lowest price any of three venues printed** in that window (Kraken 59,588 / Bybit 59,688 / Binance 59,692). But
it disclosed the timestamp problem and refused to transact, which is precisely why it did not become a fake win.

**The contrast worth keeping:** same mistake class as the Gemini trade, opposite handling.

| | ChatGPT/GPT-6 | Gemini |
|---|---|---|
| what it did | **NO TRADE**, defect disclosed | **CLOSED_PROFIT +0.449%** |
| tape says | range below every venue's floor | entry Kraken-only, exit Binance-only |
| honest outcome | abstained | **+0.001%** |

Its UFO² pick checks out (`microsoft/UFO`, **10,226★ MIT**, pushed 2026-10-30) with mild version drift — the
repo is now branded **UFO³** with UFO² as a component. Its data table is the most accurate in the batch: FRED
yields are not tradable bond prices, spot ≠ futures, NAV ≠ intraday execution, continuous-contract rolls.

Missing, as in every note: a **trial accountant**. Its three-agent red-team (generate / disprove / validate data)
is the right instinct but no role counts the variants tried — so with "thousands of strategy variations" the
disprover will confirm whichever candidate was luckiest of a thousand. The permutation control and deflated
Sharpe are the mechanical versions of those missing roles.

### 2026-11-22 — Copilot/GPT-5 stack + ETF-rotation hypothesis

[`COPILOT_GPT5_STACK_AND_ETF_HYPOTHESIS_REVIEW.md`](COPILOT_GPT5_STACK_AND_ETF_HYPOTHESIS_REVIEW.md) — the
best-reasoned note of the set and the only one arguing for **low** frequency. Its premise is right and its
conclusion is wrong, which was settled the same day with a 22.9-year test.

Its hypothesis (ETF rotation + trend + multi-asset beats day trading) was run as **H-E1**:
[`../03-trading-strategies/ETF_ROTATION_H-E1.md`](../03-trading-strategies/ETF_ROTATION_H-E1.md). Rotation
returned CAGR **5.37%** / Sharpe **0.410** against SPY's **10.28%** / **0.620** — and is **strictly dominated
by SPY plus a 200-day SMA** (7.51% / 0.693 / −21.5% DD). Shuffle control **p = 0.66**: a destroyed
cross-section does better than two thirds of the time.

The reason the premise and conclusion diverge: turnover is 6.6×/year, so friction barely registers
(Sharpe 0.429 → 0.322 as round-trip cost goes 0 → 52 bps). **Low frequency trivially survives costs**, which
is exactly why surviving costs is not evidence of an edge. Day trading died at the cost line; this died at
the no-alpha line.

Also flags the note's most dangerous line: "Phase 76–125: generate thousands of strategies" is a
multiple-testing machine unless every variant increments a trial counter.

### 2026-11-22 — Gemini TRADE_0001 live-trade audit

[`GEMINI_TRADE_0001_AUDIT.md`](GEMINI_TRADE_0001_AUDIT.md) — the only peer note that claims an actual closed
profit (`+0.449%` on an 8-minute ETH/USD long), so it was checked leg by leg against 1-minute bars from two
venues. Three findings:

- **The round trip splices two venues.** Entry `$1,681.50` at 09:17 is inside Kraken's bar (1680.76–1681.92)
  and *below* Binance's low. Exit `$1,690.73` at 09:25 is above Kraken's bar high (1688.43) and inside
  Binance's. Each leg is real on one book; no single venue supports both. On Kraken the price traded at
  **09:23**, two minutes before the claimed exit. Cause is one line of code: the venue is chosen per
  *evaluation* rather than per *trade*, so a Kraken hiccup silently re-prices the trade off a different feed.
- **The profit is a fee assumption.** `fee_bps_round_trip: 10.0` is 5 bps/side — below every retail spot
  taker. At Kraken's real base tier (52 bps RT) the best honest exit on that venue nets **+0.001%**: zero.
- **The trade it now records as OPEN is priced where nothing traded.** `TRADE_0002` entry `1690.73` at 09:26
  is 0.26% above Kraken's high and 0.10% above Binance's — unattainable on both, and live.

Credit where due: it resolves a both-touched bar to the **stop**, which matches this repo's certification
test T3, and the anti-stall supervisor's timeout-guarded UIA subprocess is the right shape.

### 2026-11-22 — Perplexity note, backtesting addendum

[`PERPLEXITY_NOTE_REVIEW.md`](PERPLEXITY_NOTE_REVIEW.md) now carries a `deepseek-flash` addendum covering the
half the original audit only touched. Three findings:

- **Licence omissions**: the note recommends `backtesting.py` (**AGPL-3.0**), `LumiBot` (**GPL-3.0**) and
  `NautilusTrader` (**LGPL-3.0**) with no licence mentioned, and presents "vectorbt / vectorbt.pro" as one option
  when `vectorbt.pro` has **no public repository** to audit.
- **The gate list is necessary but not sufficient.** Its "out-of-sample, costs, slippage, position limits,
  drawdown limits, data quality, reproducible artifacts" were all implemented here across **126 cells** and
  **0 cells qualified**. The two gates that actually killed them — **trial accounting / deflated Sharpe** and a
  **permutation control** — are not on the list.
- **Engine choice is not the binding constraint.** NautilusTrader over vectorbt changes how faithfully you
  simulate a strategy that has less edge than a 26 bps round turn. It does not create edge.

### 2026-11-22 — Subq stack recommendation

[`SUBQ_STACK_RECOMMENDATION_REVIEW.md`](SUBQ_STACK_RECOMMENDATION_REVIEW.md) — the Windows agent/desktop half
checks out (agent-desktop 26,040★, Browser MCP 7,398★, Windows-MCP real at **11,999★** not the stated ~6,750).
The backtesting half recommends **backtrader** (last push 2024-08-19) and **qstrader** (2024-06-30) as the
validation and portfolio layers without disclosing that both are 2+ years stale — the same defect the note
criticises in others.

Its one quantitative claim — *"combining strategies improved risk-adjusted returns by 30-50%"* — was **tested,
not accepted**: `03-trading-strategies/realtime_challenge/proof/portfolio_combination.py`. Combined Sharpe
**−0.123** versus best single **+0.243** (−150.6%), with a diversification ratio of **1.841**. The mix really
is much less volatile than its parts and that did not help, because only 2 of 6 components had positive
expectancy. Diversification reduces variance; it does not create return.
- **Encoding:** every review marks claims ✅ verified / 🟡 unverified / ❌ unsupported, and each ✅ names the
  artefact it was checked against.
