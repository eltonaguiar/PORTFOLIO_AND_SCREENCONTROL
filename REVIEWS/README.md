# REVIEWS

Source answers collected while researching this repo, each audited claim by claim against the actual
repositories (GitHub API), the installed software, or the measurements in
[`../01-screen-control-llm/MEASUREMENTS.md`](../01-screen-control-llm/MEASUREMENTS.md).

| Review | Input | Verdict |
|---|---|---|
| [`AGENT_MARKET_AUTOMATION_PLAYBOOK_REVIEW.md`](AGENT_MARKET_AUTOMATION_PLAYBOOK_REVIEW.md) | "Portable AI Agent Playbook" (Arena, 97 lines) | soundest of the batch; evidence rules adopted, one unverifiable citation removed |
| [`SUBQ_FURTHER_NOTE_REVIEW.md`](SUBQ_FURTHER_NOTE_REVIEW.md) | SUB Q "further note" (decided-stack version, ~3.8k words) | best-shaped answer, stale numbers, one repeated hallucination; RustDesk/RDP and intrabar advice adopted |
| [`PERPLEXITY_NOTE_REVIEW.md`](PERPLEXITY_NOTE_REVIEW.md) | Perplexity two-layer plan (~2.2k words) | most accurate on frameworks (the only answer that gets NautilusTrader's Rust core right); its twelve-tool MCP sketch became `01-*/TOOL_INTERFACE.md` |

Inputs are preserved verbatim in [`inputs/`](inputs/) where they were supplied as files, so the reviews can be
checked against the original wording.

## What the audits found, in aggregate

- **Recurring across answers:** accessibility-tree-first with a pixel fallback, MCP as a tool interface rather
  than a supervisor, and "the engine is not the data". All three are correct and are load-bearing here.
- **Recurring failures:** inflated or stale star counts, invented tools (`UIA-X` appeared twice with a detailed
  feature list and no repository), and confident performance numbers with no measurement behind them.
- **Encoding:** every review marks claims ✅ verified / 🟡 unverified / ❌ unsupported, and each ✅ names the
  artefact it was checked against.
