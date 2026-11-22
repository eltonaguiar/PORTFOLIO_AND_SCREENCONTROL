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

Inputs are preserved verbatim in [`inputs/`](inputs/) where they were supplied as files, so the reviews can be
checked against the original wording.

## What the audits found, in aggregate

- **Recurring across answers:** accessibility-tree-first with a pixel fallback, MCP as a tool interface rather
  than a supervisor, and "the engine is not the data". All three are correct and are load-bearing here.
- **Recurring failures:** inflated or stale star counts, invented tools (`UIA-X` appeared twice with a detailed
  feature list and no repository), and confident performance numbers with no measurement behind them.

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
