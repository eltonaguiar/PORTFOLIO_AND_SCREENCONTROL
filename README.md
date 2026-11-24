# PORTFOLIO_AND_SCREENCONTROL/AUTONOMOUS CONTROL OF VS CODE AI AGENT SESSIONS VIA HERMES & WEB SCRAPER INVESTIGATION

**A multi-AI research project with two running implementations.** Ten models were given the same two questions;
their answers were audited claim-by-claim against real repositories, real prices and real source code, then
merged into specifications — and two of the results now run as code with committed artifacts.

The two questions:

1. **PC control via AI** — a free, local, agent-agnostic alternative in kind to a macro recorder like
   **Jitbit Macro Recorder** (but driven by a model, not a recording), and to browser/PC agents like
   **Comet Browser (Perplexity)** and **BrowserOS / Browser Neo** — with the thing those products sell that a
   chat window doesn't have: **persistence across long, multi-step work** ("stop stopping").
2. **Trading portfolio tracker + paper trading** — what do I own across stocks, ETFs, bonds, funds,
   commodities, futures, FX and crypto, what is it worth, and — separately — would a given rule have made money
   under realistic costs, and is that answer real or the maximum of a search?

> Not a benchmarked replacement for any commercial product: nothing here was compared head-to-head against
> Comet, BrowserOS, Browser Neo or Jitbit. It is an open, inspectable stack that does the same job from free
> components, and it documents where every claim came from.

| Folder | Topic | What's in it | Progress |
|---|---|---|---|
| [`01-screen-control-llm/`](01-screen-control-llm/) | **Screen control via LLM / AI** — letting an agent perceive and drive *any* desktop surface, and making vendor agents "stop stopping" | Architecture research, free-tool catalog with verified licences, measured local benchmarks, supervisor design, fact-check of popular LLM answers — **plus a running implementation** (`screen_control/`) | [`PROGRESS.md`](01-screen-control-llm/PROGRESS.md) |
| [`02-portfolio-multi-asset/`](02-portfolio-multi-asset/) | **Portfolio tracking and valuation** — what do I own, what is it worth in my base currency, how did it perform | NautilusTrader architecture read from source, framework matrix with verified licences, tracking/valuation stack, data-evidence rules, paper-trading/monitoring design | — |
| [`03-trading-strategies/`](03-trading-strategies/) | **Trading strategies, backtests, paper trading** — would this *rule* have made money, and is that answer real | A running harness (`realtime_challenge/`), 6 pre-registered hypotheses, deflated Sharpe + permutation control, live paper round, hourly forward pods, 200-round roadmap | [`PROGRESS.md`](03-trading-strategies/PROGRESS.md) |
| [`SCRAPING/`](SCRAPING/) | **Web harvesting that survives contact** — which sources actually return data for GTA console availability and Canadian ServiceNow/Salesforce jobs | Full probe matrix with HTTP codes, 12 documented failure modes, a scored shortlist, and **runnable scripts proven against live sites** | [`FINALS/`](SCRAPING/FINALS/) |
| [`REVIEWS/`](REVIEWS/) | **Source-answer audits** — user-supplied agent playbooks and peer challenge prototypes reviewed claim by claim, with the originals kept alongside | Review + input copy | — |
| [`TRACKING.md`](TRACKING.md) | **Generated index** of every folder and document, with the status of the folder split | Folder/file tables, rebuilt by `scripts/update_index.py` (also runs on a schedule) | — |

## Topic 1 — PC control via AI (what it actually gives you)

| Problem with the alternatives | What this stack does instead |
|---|---|
| A macro recorder replays fixed coordinates: one layout change and it clicks the wrong thing | Reads the **accessibility tree first** (UIA / AT-SPI / DOM), falls back to text/OCR, then a grounding model, and only then raw coordinates |
| Browser agents are tied to one browser or one vendor | Any surface: Electron apps, native Win32, Java/Swing, terminals (tmux), browsers (CDP), remote desktops (RustDesk/RDP pixels) |
| Desktop automation steals the mouse and focus | Background input: the agent clicks without moving your cursor (`cua-driver`) |
| Vendor agents stop after one reply and need a human to type "continue" | Harness-native continuation first (`copilot --autopilot`, Copilot SDK `session.idle`, Claude Code `Stop` hook), then a supervisor that **classifies the stop** and injects the missing fact — never a timer that types "continue" |
| Long tasks lose the plot after context compaction | The plan and evidence live on disk (`TASK.md` + ledger), re-injected every cycle; context is a cache, not the state |

Free components only: `cua-driver` (MIT), Windows-MCP (MIT), Playwright / Chrome DevTools MCP (Apache-2.0),
RapidOCR (Apache-2.0), local VLMs via Ollama, and a supervisor you own (~200 lines).

Start here: [`01-screen-control-llm/README.md`](01-screen-control-llm/README.md) ·
contract: [`TOOL_INTERFACE.md`](01-screen-control-llm/TOOL_INTERFACE.md) ·
measurements: [`MEASUREMENTS.md`](01-screen-control-llm/MEASUREMENTS.md) ·
anti-stall design: §5 of [`PC_AGENT_CONTROL_RESEARCH.md`](01-screen-control-llm/PC_AGENT_CONTROL_RESEARCH.md).

## How the screen-control runs were actually driven

Every automation run behind this repo used the same five-rung ladder, in order, and every rung was
measured rather than assumed:

| Rung | What it means | When it won |
|---|---|---|
| **1. App API / CDP** | the app's own interface: a browser's DOM over the DevTools protocol, a CLI, a process's stdout | any page with a debug port — selectors, `value` setters, exact text |
| **2. Accessibility tree** | UIA on Windows, AT-SPI on Linux, AX on macOS; elements addressed by handle, not by pixel | native windows, most Electron apps, browser pages once the renderer's tree is awake |
| **3. Text layer** | the a11y text pattern, or OCR over a **crop** | when the tree exposes containers but no useful nodes |
| **4. Element detection** | a grounding model (ShowUI / UI-TARS / OmniParser) returns labelled boxes | canvas-like surfaces with no tree at all |
| **5. Raw coordinates** | click at (x, y) from a screenshot | last resort, and the least reliable |

**Tools used:** `cua-driver` through a `computer_use` tool (window-scoped capture, element handles,
background input), Playwright over CDP for DOM work, RapidOCR for text, and local VLMs only for
reading labels. Nothing paid, nothing cloud.

**Rules this project learned the hard way — each with a number behind it:**

- **Element handles, never coordinates.** Handing the driver `(3108, 739)` produced a click at
  `(5029, 798)` — outside the window, silently. Clicking element `#87` landed at `(3127, 746)` and
  worked. A coordinate click outside the window bounds is a no-op at best and can destroy state at
  worst; one early misfire cleared a live conversation.
- **A cold accessibility tree is not a dead surface.** The first capture of a Chromium window returned
  **24** elements (tabs and window buttons only, no page); after one further capture the same window
  exposed **95–129** nodes including the composer and per-message controls. Retry once before falling
  down the ladder.
- **Background input has a hard split.** Clicks and `set_value` (UIA ValuePattern) deliver without
  stealing focus; **keyboard and mouse-wheel are refused** by the renderer (`background_unavailable`)
  and need a brief foreground raise, which should be budgeted and announced, never looped.
- **Rich-text editors need insert-text, not keystrokes.** Typing character-by-character into a
  ProseMirror/TipTap composer **dropped characters** ("sentence" → "sence", "single" → "ingle");
  `insert_text` wrote the same string intact. And clear the editor first — a leftover draft
  concatenates onto the new prompt.
- **For long answers, the clipboard beats both the tree and OCR.** `Ctrl+A`/`Ctrl+C` recovered
  **36.6 KB** of a three-panel answer set where the accessibility tree yielded **2.2 KB** — the tree
  only exposes the rendered viewport. OCR on a full 1456×818 frame cost **18.99 s** for 106 boxes and
  mangled digits (`2006-11-30` → `2886-11-38`), so OCR is for *state* ("is a Stop button present"),
  never for numbers.
- **Window identity is part of the target.** Captures must be addressed by `(pid, window_id)`: a second
  browser instance (or an OS profile-picker window) makes app-name targeting ambiguous, and element
  indices only mean anything inside one window and one snapshot.
- **Verify after every state change.** Re-read the smallest thing that should have changed. An
  "unverifiable" verdict is not a success — it is a prompt to look before doing anything else.

**Consequence, stated plainly:** where the API rung is unavailable — a browser with no debug port,
driving a profile whose sessions cannot be transplanted because of app-bound cookie encryption — the
run is UIA-only, and custom controls (a bespoke mode selector, a canvas, a virtualised long answer)
may simply be unreachable. That is a property of the surface, and the honest response is to report the
gate rather than to thrash at pixels.

## Topic 2 — portfolio tracking and paper trading

Start here: [`PORTFOLIO_TRACKING.md`](02-portfolio-multi-asset/PORTFOLIO_TRACKING.md) ·
engines: [`FRAMEWORK_MATRIX.md`](02-portfolio-multi-asset/FRAMEWORK_MATRIX.md) ·
evidence gates: [`DATA_EVIDENCE_RULES.md`](02-portfolio-multi-asset/DATA_EVIDENCE_RULES.md) ·
paper loop: [`PAPER_TRADING_AND_MONITORING.md`](02-portfolio-multi-asset/PAPER_TRADING_AND_MONITORING.md) ·
strategy contract: [`STRATEGY_SPEC.md`](03-trading-strategies/STRATEGY_SPEC.md).

Tracking and backtesting are different instruments, and quoting one as evidence for the other is where most bad
numbers come from:

### Why 02 and 03 are separate folders

They answer different questions and the confusion between them is where most bad numbers
come from:

| | `02-portfolio-multi-asset` | `03-trading-strategies` |
|---|---|---|
| Question | *What do I own and what is it worth?* | *Would this rule have made money, and is that real?* |
| Output | positions, valuation, TWR/MWR | expectancy, drawdown, deflated Sharpe, forward trades |
| Failure mode | NAV ≠ return; missing distributions | in-sample fitting; multiple testing; look-ahead |
| Wrong substitution | using a tracker's P/L as evidence of edge | using a backtest as a valuation |

## This is multi-AI research — who contributed what

Ten model answers were collected on 2026-11-22 for the same two questions, then audited rather than merged
blindly. Each contributed something real; each also got something wrong, and the audits say which.

| Source | Contributed | Landed in |
|---|---|---|
| **Arena** "Portable AI Agent Playbook" | evidence discipline, least-privilege framing, "MCP is not a supervisor" | `02-*/DATA_EVIDENCE_RULES.md` |
| **Perplexity** two-layer plan | the twelve-tool MCP interface + task-ledger fields; correct Rust-core description of NautilusTrader | `01-*/TOOL_INTERFACE.md` |
| **SUB Q** (two notes) | RustDesk service-vs-portable, RDP daemons, intrabar-sequencing warning | `01-*/PC_AGENT_CONTROL_RESEARCH.md` §4.2, evidence gate 7 |
| **Gemini 3.1 Pro** challenge | the fee trap (0.10% round turn = 16.8% of a 0.59% target), refusal to fake a closed trade | [`REVIEWS/CHALLENGE_PROTOTYPES_GLM_GEMINI_REVIEW.md`](REVIEWS/CHALLENGE_PROTOTYPES_GLM_GEMINI_REVIEW.md) |
| **GLM 5.3 Flash** challenge | the strategy emission schema (entry/exit/TP/SL/size/timeframe/feeds) | `03-*/STRATEGY_SPEC.md` |
| **GPT-4.1 mini** blueprint | the round/phase plan structure — and the multiple-testing blind spot it exposed | `02-*/DATA_EVIDENCE_RULES.md` §6 |
| **GPT-5 nano** plan | the smallest executable MVP step list | `03-*/GPT5NANO_REVIEW.md` |
| **Grok**, **Mercury** | broad tool catalog + the clearest goal-loop sketch | `01-*/FACTCHECK.md` |
| **deepseek-flash** (peer agent) | both running implementations, harness certification, the 42-cell negative result | `01-*/screen_control/`, `03-*/realtime_challenge/` |

Full audits — including the invented tools (`UIA-X` appeared twice, with a feature list, and does not exist):
[`REVIEWS/`](REVIEWS/) and [`01-*/FACTCHECK.md`](01-screen-control-llm/FACTCHECK.md).

## Provenance — four categories, and every file says which

Everything here is one of four things, and each document says which:

1. **Measured on the author's machine** (Windows 11, RTX 5070 12 GB, Python 3.14, Ollama, `cua-driver` 0.21.0, Copilot CLI 1.0.49). Numbers are real, commands are given so you can reproduce them. → `01-screen-control-llm/MEASUREMENTS.md`
2. **Read from upstream source** (a shallow clone of `nautechsystems/nautilus_trader` at commit `ee642cc`, plus its `docs/concepts/architecture.md`) or from a vendor's own documentation. → `02-portfolio-multi-asset/NAUTILUS_ARCHITECTURE.md`
3. **Researched from the web and cited**, with license/star/last-push checked through the GitHub API on the date stamped in each file.
4. **Executed here, 2026-11-22** — the two implementations. Their numbers come from artifacts committed next to
   them: `03-trading-strategies/results/*.json`, `03-trading-strategies/ledger/*.jsonl`,
   `01-screen-control-llm/transcripts/*.json`. If a claim is not in one of those files, it is not a measurement.

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
- Writing a strategy that has to survive review? → [`03-trading-strategies/STRATEGY_SPEC.md`](03-trading-strategies/STRATEGY_SPEC.md)
- Want to know what exists right now? → [`TRACKING.md`](TRACKING.md)

## Status

Research notes **plus two running implementations** (added 2026-11-22), in three topic folders. The research and design documents
are unchanged; alongside them now sit code that was executed and measured:

| folder | implementation | verified |
|---|---|---|
| `01-screen-control-llm/` | `screen_control/` — guarded observe→decide→act→verify loop over CDP | **9/9** mechanics tests, **4/4** steps on a live page |
| `03-trading-strategies/` | `realtime_challenge/` — backtest engine, 6 pre-registered hypotheses, live paper round, GH Actions forward pod | **5/5** harness certifications, 42 backtest cells, 2 live rounds |

The rest of each folder is still research. The next engineering milestones are listed at the end of each
folder's README.

### Headline result of the first execution run (a clean negative)

42 cells across 7 crypto majors and 6 hypotheses, 3,000×1h bars, 26 bps round turn: **0** clear deflated
Sharpe 0.95, **0** beat the permutation control. The single family that survived friction — the crypto
weekend effect, +5.9 bps/trade — **died** when re-tested over 3 years with clustering by calendar weekend and
42 control windows (−3.21 bps, CI [−67.3, +64.5], rank #15 of 42). A live paper round opened and closed real
positions on real bid/ask and lost exactly the friction. Full write-up:
[`03-trading-strategies/REALTIMECHALLENGE_deepseek-flash_2026-11-22_0356_EST.MD`](03-trading-strategies/REALTIMECHALLENGE_deepseek-flash_2026-11-22_0356_EST.MD).

Nothing in this repository is financial advice.
