# PORTFOLIO_AND_SCREENCONTROL

Working research and reference implementation notes for two separate problems that keep getting
conflated in AI-agent discussions:

| Folder | Topic | What's in it |
|---|---|---|
| [`01-screen-control-llm/`](01-screen-control-llm/) | **Screen control via LLM / AI** — letting an agent perceive and drive *any* desktop surface (VS Code, browsers, consoles, JetBrains, RustDesk/RDP, games), and making vendor agents "stop stopping" | Architecture research, free-tool catalog with verified licenses, measured local benchmarks, supervisor design, fact-check of popular LLM answers |
| [`02-portfolio-multi-asset/`](02-portfolio-multi-asset/) | **Financial portfolio tracking for multiple asset classes** — stocks, ETFs, bonds, mutual funds, commodities, futures, FX, crypto | NautilusTrader v2 architecture deep-dive (from source), framework matrix with verified licenses, tracking/valuation stack, data-evidence rules |

## Provenance — how to read this repo

Everything here is one of three things, and each document says which:

1. **Measured on the author's machine** (Windows 11, RTX 5070 12 GB, Python 3.14, Ollama, `cua-driver` 0.21.0, Copilot CLI 1.0.49). Numbers are real, commands are given so you can reproduce them. → `01-screen-control-llm/MEASUREMENTS.md`
2. **Read from upstream source** (a shallow clone of `nautechsystems/nautilus_trader` at commit `ee642cc`, plus its `docs/concepts/architecture.md`) or from a vendor's own documentation. → `02-portfolio-multi-asset/NAUTILUS_ARCHITECTURE.md`
3. **Researched from the web and cited**, with license/star/last-push checked through the GitHub API on the date stamped in each file.

Claims that could not be verified are labelled **unverified** rather than quietly repeated — see
[`01-screen-control-llm/FACTCHECK.md`](01-screen-control-llm/FACTCHECK.md), which audits four popular
LLM answers (Grok, Mercury, SUB Q, Arena) line by line against the actual repositories.

## Ground rules used throughout

- **No live trading, no broker credentials, no order placement** by an agent. Research and paper only.
- **Structure before pixels.** Accessibility tree → DOM/CDP → text/OCR → element detection → raw coordinates. Every rung down costs roughly an order of magnitude in reliability.
- **The loop owns the goal, not the model.** Persist the plan and the evidence on disk; a chat history is not a task runner.
- **Verify every action.** Re-read the smallest thing that should have changed; never retry blindly.
- **Label evidence.** `observed` / `derived` / `assumed` — and say "not verified" when it isn't.

## Quick start

- Need to drive any app on screen? → [`01-screen-control-llm/README.md`](01-screen-control-llm/README.md)
- Need an agent that doesn't stop after one reply? → §5 of [`01-screen-control-llm/PC_AGENT_CONTROL_RESEARCH.md`](01-screen-control-llm/PC_AGENT_CONTROL_RESEARCH.md)
- Choosing a backtest engine? → [`02-portfolio-multi-asset/FRAMEWORK_MATRIX.md`](02-portfolio-multi-asset/FRAMEWORK_MATRIX.md)
- Understanding NautilusTrader's internals before adopting? → [`02-portfolio-multi-asset/NAUTILUS_ARCHITECTURE.md`](02-portfolio-multi-asset/NAUTILUS_ARCHITECTURE.md)
- Tracking a real multi-asset portfolio rather than backtesting one? → [`02-portfolio-multi-asset/PORTFOLIO_TRACKING.md`](02-portfolio-multi-asset/PORTFOLIO_TRACKING.md)

## Status

Research notes and design documents, not production code. The next engineering milestones are listed at
the end of each folder's README. Nothing in this repository is financial advice.
