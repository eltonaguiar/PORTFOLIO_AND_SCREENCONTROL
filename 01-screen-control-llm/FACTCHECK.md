# Fact-check — four LLM answers on PC control, audited against the actual repositories

Four answers were collected on 2026-11-22 (Grok, Mercury, SUB Q, Arena) and they overlap heavily. Instead of
picking a favourite, each named tool was checked: does the repository exist, what is its license, how many
stars, when was it last pushed (GitHub API, 2026-11-22), and does its own README support the claim made about
it?

Legend: ✅ verified · 🟡 plausible but not verified here · ❌ claim not supported / likely invented.

## Desktop-control tools

| Tool (as claimed) | Claim | Reality | Verdict |
|---|---|---|---|
| `vercel-labs/agent-desktop` | "Apache-2.0, ~26k stars, accessibility tree, background control, `agent-desktop mcp`" | Exists: `vercel-labs/agent-desktop`, **Apache-2.0, 26,032★**, pushed 2026-11-21. npm `agent-desktop@1.3.1`, self-described as *"Reliable computer use for AI agents — observe and operate desktop apps via native accessibility trees"* | ✅ |
| `Munim Computer Use` | "similar accessibility + background + MCP + signed-in Chrome tab support" | Exists: `munimtechnologies/munim-computer-use`, **Apache-2.0**, 41 tools in v0.14.0, Rust on Windows/Linux + Swift on macOS, background input, Chrome tab *adoption* (`browser_use_tab`) | ✅ |
| `trycua/cua` (Cua Driver) | "accessibility-first + true background control + MCP; Hermes ships it as `computer_use`" | Exists: **MIT, 32,764★**, pushed 2026-11-22. Verified locally: `cua-driver 0.21.0` healthy, UIA + D3D capture ✅ | ✅ |
| `CursorTouch/Windows-MCP` | "Windows UIA, ~19 tools, 2M users" | Exists: **MIT, 11,997★**, pushed 2026-11-22, UIA-based, `--tools`/`--exclude-tools` allowlists. The "2M users" figure is marketing — unverified | ✅ repo / 🟡 user count |
| `xa11y` | "MIT, Rust core with Python and JS bindings, Playwright-style selectors" | Exists: `xa11y/xa11y`, **MIT, 94★** (plus `xa11y/strands-xa11y`). Far smaller than implied | 🟡 real but tiny |
| `UIA-X` | "MIT, MCP server over stdio/SSE/HTTP with API-key auth" | No repository matches this description; GitHub search returns only unrelated Android `uiautomator` viewers | ❌ |
| `Screenhand` | "feature-dense, ~50 ms native actions, ~10 ms Chrome ops" | Only `SayDoneAI/Screenhand` (0★, MIT) and `manushi4/Screenhand` (15★, AGPL-3.0). Nothing supporting the perf claims | ❌ as described |
| `AutoGUI` | "ReAct loop over shell/filesystem/pixel/a11y, Playwright, FastAPI REST surface" | No matching repository; the closest hits are unrelated `omniparser-autogui-mcp` (71★) and `qwen_autogui` (47★) | ❌ as described |
| `computer-use-linux` | "MIT, ~600★, AT-SPI + RemoteDesktop/Screenshot portals, ydotool fallback" | Exists: `agent-sh/computer-use-linux`, **MIT, 918★** | ✅ |
| `Peekaboo` | "macOS 15+, accessibility + screenshots, 24 MCP tools" | Exists: `openclaw/Peekaboo`, **MIT, 5,508★** | ✅ |
| `PyAutoGUI` | "primary monitor only, unreliable multi-monitor, keys go to focused window" | Accurate — documented behaviour; disqualifies it for multi-window orchestration | ✅ |
| `Playwright MCP` / `chrome-devtools-mcp` / `browser-use` | standard browser paths | All exist and are large: Playwright MCP **Apache-2.0, 39,989★**; Chrome DevTools MCP **Apache-2.0, 58,741★**; browser-use **MIT, 121,713★** | ✅ |

## Remote desktop claims

| Claim | Reality | Verdict |
|---|---|---|
| "IronRDP ships `ironrdp-agent`, a long-lived RDP daemon with short-lived CLI invocations" | `Devolutions/IronRDP` exists (**Apache-2.0, 3,323★**); the `ironrdp-agent` component was not verified | 🟡 |
| "RDPTools is an AutoHotkey class library that automates `mstsc.exe`" | `evilC/RDPTools` exists (15★, no licence file) | 🟡 real, unmaintained/obscure |
| "RustDesk can be driven if it exposes accessibility, else screenshots" | Correct in shape: RustDesk is a **pixel surface**; synthetic input is forwarded, but there is no RustDesk-specific automation API. Control the remote session over SSH when it exists | ✅ |
| "Use a community `rustdesk-mcp-bridge` from a Glama listing" | Unverified third-party listing; no repository or maintenance evidence checked | ❌ as evidence |

## Continuation / orchestration claims

| Claim | Reality | Verdict |
|---|---|---|
| "MCP doesn't keep agents working; you need a durable runner" | Correct, and the strongest point in all four answers | ✅ |
| "Temporal for durable workflows, LangGraph for stateful LLM graphs" | Both real and appropriate, though heavy for a single-machine supervisor; the 200-line supervisor in `PC_AGENT_CONTROL_RESEARCH.md` §5 covers the same ground without a cluster | ✅ / 🟡 over-engineered |
| "`Trigger.dev`, `AgentRQ`, `agent-task-queue`, `Paperclip`, `future-os`, `jinka`" | Not verified; several look like plausible names rather than checked projects | ❌ unverified |
| "Copilot CLI has autopilot continuation" (implied by several) | Verified on the machine: `--autopilot`, `--max-autopilot-continues`, `/goal … --max-ai-credits`, and the CLI's synthetic `task_complete` nudge are documented and present in 1.0.49 | ✅ |
| "Claude Code `Stop` hooks can block the turn from ending" | Correct; guard with `stop_hook_active` — Claude Code force-ends after 8 consecutive continuations | ✅ |
| Grok/Mercury: "just give agents explicit continuation instructions" | Insufficient on its own: a plan-only turn is a model behaviour, and prompting against it works only until context compaction. Harness-level continuation first, prompt second, GUI injection last | 🟡 partial |

## Backtesting claims

| Claim | Reality | Verdict |
|---|---|---|
| "NautilusTrader: Rust core + Python API, event-driven, backtest/live parity" | True, but **only for v2** (2.0.0 RCs on `develop`). Stable PyPI is **1.231.0**, which is Cython/Python-core. All four answers describe v1 without saying so | 🟡 correct only for v2 |
| "LEAN: Apache-2.0, C# core, Python API, multi-asset, local or cloud" | Correct: `QuantConnect/Lean`, **Apache-2.0, 22,651★** | ✅ |
| "VectorBT: fastest for parameter sweeps; huge feature set" | Correct in role; the OSS repo is **NOASSERTION** on GitHub — read `LICENSE` before commercial use, and note the actively developed product is `vectorbtpro` (paid) | ✅ / ⚠️ licence |
| "Backtrader: maintenance stalled since ~2020–2023" | Correct — `mementum/backtrader` has had no meaningful release since 2023 | ✅ |
| "Zipline-reloaded for equity factor research" | Correct: **Apache-2.0, 2,020★**, US equities focus | ✅ |
| "backtesting.py is AGPL-3.0" | Correct: **AGPL-3.0, 9,275★** — a real constraint for closed products | ✅ |
| "Bonds/mutual funds are 'just price series'" | Half true and dangerous: NAV series need distribution handling, bond prices need clean-vs-dirty + accrual + calendars | 🟡 oversimplified |
| "Agentic trading frameworks work today for live trading" | Out of scope for this repo; an LLM placing live orders is a risk decision, not a tooling decision | ❌ policy |

## Where all four answers agree, and are right

1. **Accessibility tree before pixels.** Faster, cheaper in tokens, far less flaky.
2. **Background input matters** (no cursor theft) if a human shares the machine.
3. **MCP is the tool interface, not the supervisor.** Continuation needs state, not another prompt.
4. **The engine is not the data.** Every backtest claim is downstream of data quality, costs, and assumptions.

## Where they diverge, and who wins

- Grok named the most real projects (`agent-desktop`, `munim`, `cua`, Windows-MCP) but padded with
  unverified ones and drifted into an unasked quant survey.
- Mercury's four-layer goal loop (`snapshot → ask → act → log → sleep`) is the clearest architecture sketch,
  but it treats a chat VLM as the actor and ignores grounding models entirely.
- SUB Q has the best layering vocabulary and the worst citation hygiene — several tools in its tables do not
  exist as described.
- Arena's answer is the most conservative and the most correct on policy (no live orders, evidence rules),
  but gives no implementation detail.

The merged position used in this repository: **cua-driver as actuator, accessibility → OCR → grounding as the
perception ladder, harness-native continuation first, a small bespoke supervisor for judgement, and CDP/tmux/SSH
as channel upgrades wherever they exist.**
