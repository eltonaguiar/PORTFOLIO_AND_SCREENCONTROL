# PORTFOLIO_AND_SCREENCONTROL

Working research and reference implementation notes for two separate problems that keep getting
conflated in AI-agent discussions:

| Folder | Topic | What's in it | Progress |
|---|---|---|---|
| [`01-screen-control-llm/`](01-screen-control-llm/) | **Screen control via LLM / AI** — letting an agent perceive and drive *any* desktop surface, and making vendor agents "stop stopping" | Architecture research, free-tool catalog with verified licences, measured local benchmarks, supervisor design, fact-check of popular LLM answers — **plus a running implementation** (`screen_control/`) | [`PROGRESS.md`](01-screen-control-llm/PROGRESS.md) |
| [`02-portfolio-multi-asset/`](02-portfolio-multi-asset/) | **Portfolio tracking and valuation** — what do I own, what is it worth in my base currency, how did it perform | NautilusTrader architecture read from source, framework matrix with verified licences, tracking/valuation stack, data-evidence rules, paper-trading/monitoring design | — |
| [`03-trading-strategies/`](03-trading-strategies/) | **Trading strategies, backtests, paper trading** — would this *rule* have made money, and is that answer real | A running harness (`realtime_challenge/`), 6 pre-registered hypotheses, deflated Sharpe + permutation control, live paper round, hourly forward pods, 200-round roadmap | [`PROGRESS.md`](03-trading-strategies/PROGRESS.md) |
| [`REVIEWS/`](REVIEWS/) | **Source-answer audits** — user-supplied agent playbooks and peer challenge prototypes reviewed claim by claim, with the originals kept alongside | Review + input copy | — |
| [`TRACKING.md`](TRACKING.md) | **Generated index** of every folder and document, with the status of the folder split | Folder/file tables, rebuilt by `scripts/update_index.py` (also runs on a schedule) | — |

### Why 02 and 03 are separate folders

They answer different questions and the confusion between them is where most bad numbers
come from:

| | `02-portfolio-multi-asset` | `03-trading-strategies` |
|---|---|---|
| Question | *What do I own and what is it worth?* | *Would this rule have made money, and is that real?* |
| Output | positions, valuation, TWR/MWR | expectancy, drawdown, deflated Sharpe, forward trades |
| Failure mode | NAV ≠ return; missing distributions | in-sample fitting; multiple testing; look-ahead |
| Wrong substitution | using a tracker's P/L as evidence of edge | using a backtest as a valuation |

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

Research notes **plus two running implementations** (added 2026-11-22), in three topic folders. The research and design documents
are unchanged; alongside them now sit code that was executed and measured:

| folder | implementation | verified |
|---|---|---|
| `01-screen-control-llm/` | `screen_control/` — guarded observe→decide→act→verify loop over CDP | **9/9** mechanics tests, **4/4** steps on a live page |
| `03-trading-strategies/` | `realtime_challenge/` — backtest engine, 6 pre-registered hypotheses, live paper round, GH Actions forward pod | **5/5** harness certifications, 42 backtest cells, 2 live rounds |

The rest of each folder is still research. The next engineering milestones are listed at the end of each
folder's README.

### Four provenance categories (the fourth is new)

The three categories above are joined by a fourth, and every file says which it is:

4. **Executed on this machine, 2026-11-22** — the two implementations. Their numbers come from artifacts
   committed next to them: `03-trading-strategies/results/*.json`,
   `03-trading-strategies/ledger/*.jsonl`, `01-screen-control-llm/transcripts/*.json`. If a claim is not
   in one of those files, it is not a measurement.

### Headline result of the first execution run (a clean negative)

42 cells across 7 crypto majors and 6 hypotheses, 3,000×1h bars, 26 bps round turn: **0** clear deflated
Sharpe 0.95, **0** beat the permutation control. The single family that survived friction — the crypto
weekend effect, +5.9 bps/trade — **died** when re-tested over 3 years with clustering by calendar weekend and
42 control windows (−3.21 bps, CI [−67.3, +64.5], rank #15 of 42). A live paper round opened and closed real
positions on real bid/ask and lost exactly the friction. Full write-up:
[`03-trading-strategies/REALTIMECHALLENGE_deepseek-flash_2026-11-22_0356_EST.MD`](03-trading-strategies/REALTIMECHALLENGE_deepseek-flash_2026-11-22_0356_EST.MD).

Nothing in this repository is financial advice.
