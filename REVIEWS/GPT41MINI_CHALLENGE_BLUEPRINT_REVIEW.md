# Review — GPT-4.1 mini "REALTIMECHALLENGE" blueprint (200-round plan)

Input: pasted 2026-11-22 as `REALTIMECHALLENGE_GPT4_2024-06-16_1500_EST.MD` (~2.8k words). Audited the same day
against the GitHub API, vendor documentation, and the methodology in
[`../02-portfolio-multi-asset/DATA_EVIDENCE_RULES.md`](../02-portfolio-multi-asset/DATA_EVIDENCE_RULES.md).

**Verdict: the best *project plan* of the six and the worst *tool list*. It has phases, deliverables and
acceptance criteria — genuinely useful structure — but it recommends two dead libraries, one dead data
provider, one wrong acronym, and a methodology (200 rounds of search) that will manufacture false positives
unless it is paired with a holdout discipline.**

## Factual errors

| Claim | Verdict | Reality |
|---|---|---|
| "MCP (**Multipurpose** Control Protocol) Server" | ❌ | MCP is the **Model Context Protocol** |
| "PyAlgoTrade … possible use of QuantConnect LEAN or PyAlgoTrade" | ❌ dead | `gbeced/pyalgotrade` is **archived**, last push 2026-11-13, licence NOASSERTION, 4,679★. Do not start there |
| "backtrader: mature, multi-asset, event-driven, good community" | ⚠️ stale | `mementum/backtrader` — GPL-3.0, 23,776★, **last push 2024-08-19**. Still runs; nobody fixes bugs. Fine to maintain, wrong to build new on |
| "zipline (less active but good for equities)" | ⚠️ understated | `quantopian/zipline` last push **2024-02-13** — upstream is dead. The maintained fork is `stefan-jansen/zipline-reloaded` (Apache-2.0, 2,020★) |
| "Futures: Quandl (free datasets)" | ❌ | Quandl became **Nasdaq Data Link** and the free WIKI datasets were discontinued; community free datasets were largely paywalled in the rebrand |
| "Forex: … TrueFX (free)" | 🟡 likely stale | TrueFX's free tick programme is not what it was; verify current terms before designing around it. Dukascopy's free historical tick export is still real |
| "Vision fallback: SikuliX" | ⚠️ | SikuliX upstream **archived March 2026**; the MIT continuation is **Oculix**. Use a grounding model (ShowUI/UI-TARS) before image templates anyway |
| "agent-rdp: PowerShell-based CLI utilities to control UI over RDP" | 🟡 | Real (`thisnick/agent-rdp`, Apache-2.0, **28★**) and it does inject a PowerShell agent over a virtual channel — experimental, not a foundation |
| "GitHub Actions … monitoring live or near-live signals on TP/SL" | ⚠️ **wrong tool for real-time** | Scheduled workflows have a **5-minute minimum**, routinely run late under load, and **disable themselves after ~60 days of repository inactivity** on public repos. Fine for a nightly backtest; not for intraday TP/SL watching |
| "alpaca-py (paper trading available)" | ✅ | real and appropriate for equities paper trading |
| "Binance Testnet" | ✅ | real; spot testnet has its own quirks (separate keys, resets) |
| "vectorbt for sweeps + event-driven engine for realism" | ✅ | correct two-tier split — the same conclusion this repo reaches |
| "BacktestLoop / custom NLP→Backtrader compiler" for AI-generated strategies | 🟡 | `BacktestLoop` unverified; the *idea* (LLM emits strategy code, harness runs it) is fine, the reverse direction (strategy → code → claimed result) is exactly where overfitting enters |
| "tp=1%, sl=0.5%" MA crossover prototype | ⚠️ incomplete | 2:1 reward/risk on a 5/15-min MA cross with **no commission, no spread, no slippage, and no intrabar ordering** — a stop and a target inside one bar cannot be sequenced from OHLCV (gate 7). The prototype as written will overstate results by a wide margin |
| A6 "no human approval" + A7 "trusted code only" | ⚠️ inconsistent | Autonomy without approval **and** without isolation is the combination that ends badly. Needs a VM/microVM, scoped credentials, an egress allowlist, and a documented panic path — which the plan mentions but does not design |

## Methodological problem: 200 rounds is a multiple-testing machine

The plan's core loop — generate variants, sweep parameters, keep the winners, repeat 200 times — produces a
**selection effect**, not evidence. With `R` rounds × `P` parameter sets you are taking a maximum over thousands
of trials; the expected best in-sample Sharpe rises with the number of trials even when every strategy is
noise. Without a holdout and a trial count, "round 187 found a profitable strategy" is a statement about the
search, not the market.

What makes the plan defensible (added to the evidence rules, §6):

1. **Count your trials.** Log every variant evaluated, including the ones you discarded. `R × P` is the number
   that inflates your result.
2. **Pre-register before you look.** Write the hypothesis and the acceptance test first; a rule invented after
   seeing the equity curve is a fitted parameter.
3. **Hold out a final period** and touch it once, at the end. If a round's winner is confirmed on the holdout,
   the *next* round's holdout must be different data, not the same slice reused.
4. **Report deflated metrics**, not raw Sharpe: probability of backtest overfitting (PBO) via combinatorially
   symmetric cross-validation, or a deflated Sharpe ratio that accounts for trials, skew and kurtosis.
5. **Prefer parameter plateaus to peaks.** A Sharpe that survives neighbouring settings is a signal; a spike
   surrounded by losses is a fitting artefact.
6. **Two runs: multi-asset, then portfolio.** A rule that works per-symbol can still lose money once positions
   compete for one cash balance (see `FRAMEWORK_MATRIX.md`).

## What was adopted

| Idea | Where it landed |
|---|---|
| Phase/deliverable structure with explicit acceptance criteria | reflected in the build order in `01-screen-control-llm/README.md` |
| Paper-trading loop (signal → simulated fill → TP/SL watch → log → report) | written up properly as [`../02-portfolio-multi-asset/PAPER_TRADING_AND_MONITORING.md`](../02-portfolio-multi-asset/PAPER_TRADING_AND_MONITORING.md), with the fill assumptions and a scheduler that is actually suitable |
| "Share results for peer cross-validation" | this repo's `REVIEWS/` and the manifest requirement in `DATA_EVIDENCE_RULES.md` |
| Multiple-testing blind spot | new §6 in `DATA_EVIDENCE_RULES.md` (trial counting, holdout, PBO/deflated Sharpe, plateaus) |

## What to ignore

The tool list (§"Suggested Framework and Tools"), the MCP expansion, the Quandl/TrueFX/PyAlgoTrade
recommendations, GitHub Actions as an intraday scheduler, and any claim that N rounds of search constitutes
evidence.
