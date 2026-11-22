# Review — SUB Q "further note" (the decided-stack version)

Input: pasted 2026-11-22, ~3.8k words, structured as a decided stack with per-row citations. Reviewed the same
day against the actual repositories (GitHub API), against the installed Hermes build, and against the
measurements in [`../01-screen-control-llm/MEASUREMENTS.md`](../01-screen-control-llm/MEASUREMENTS.md).

**Verdict: the best-shaped answer of the batch — it commits to specific tools instead of listing them — but its
numbers are stale and it repeats one hallucinated tool. Its operational advice on RustDesk, RDP, and browser
sessions is genuinely good and has been folded into the research doc.**

## Claim audit

| Claim | Verdict | Reality |
|---|---|---|
| Hermes Desktop is MIT and free | ✅ | `~/AppData/Local/hermes/hermes-agent/LICENSE` → "MIT License, Copyright (c) 2025 Nous Research" |
| Hermes `computer_use` drives the desktop in the background via `cua-driver`, cursor/focus untouched | ✅ | verified locally: `cua-driver 0.21.0`, UIAutomation ✅, Windows Graphics Capture ✅, background delivery by default |
| `agent-desktop` (Vercel Labs), Apache-2.0, CLI + C library, accessibility tree with stable refs, released Oct 30 | ✅ repo, ⚠️ detail | `vercel-labs/agent-desktop` Apache-2.0, **26,032★**, pushed 2026-11-21, npm `agent-desktop@1.3.1`. Its README describes exactly that snapshot → act-on-ref → re-snapshot loop. **"60 command names" is not supported** — the published CLI surface is small (`status`, `permissions`, `snapshot`, `click`, `type`, `scroll`, …) |
| `Browser MCP` connects agents to your real browser with existing logins | ✅ | `BrowserMCP/mcp` Apache-2.0, **7,398★**, pushed 2026-11-12 |
| Hermes `browser_exec` = headless Chromium via CDP | ✅ | matches the installed toolset; the desktop tool is deliberately desktop-only |
| `Workroom` plugin for Word/PowerPoint/Excel with byte-identical untouched parts | 🟡 unverified | no Workroom plugin installed here (`~/.hermes/plugins` has `advanced-delegation`, `job-search`); the byte-identity claim is strong and would need its own evidence, not a citation marker |
| `agent-rdp` (IronRDP): daemon per session, injects a PowerShell agent over a dynamic virtual channel | 🟡 real but tiny | `thisnick/agent-rdp` Apache-2.0, **28★** — treat as experimental, not production. `Devolutions/IronRDP` itself is solid (Apache-2.0, 3,323★) |
| `UIA-X` — cross-platform MCP with bearer/API-key auth and a mock backend | ❌ | **second appearance of this hallucination.** No repository matches; GitHub search returns only unrelated Android `uiautomator` viewers. Do not plan around it |
| Windows-MCP "~6,750★" | ⚠️ stale | actual: **11,997★**, pushed 2026-11-22. The 0.2–0.9 s latency figure was not measured here; ours shows the tool is fast but the number is unsourced |
| "PyAutoGUI only works on the primary monitor and keys go to the focused window" | ✅ | accurate, and disqualifying for multi-window work |
| "A desktop-control endpoint with no token is the most common security mistake" | ✅ | correct; folded into the research doc's guardrails |
| RustDesk: install as a **service**, not portable, for unattended access; service starts before login; portable .exe can't reach the UAC secure desktop | ✅ | correct in substance and the most useful line in the note. Folded into §4.2 |
| "Use agent-rdp when the target is a real RDP session… better than blind keystrokes" | ✅ principle | controlling the remote session natively beats driving a compressed viewer window. Where SSH exists, SSH still beats both |
| "RustDesk can kick an existing RDP session on a VM" | 🟡 plausible | community-reported behaviour on some Windows editions; verify on your own host before relying on either |
| "Backtrader for realistic validation" | ❌ poor pick | `mementum/backtrader` is **GPL-3.0, 23,776★, last push 2024-08-19** — effectively unmaintained. Recommending it as *the* validation engine in 2026 is a maintenance liability; `backtesting.py` (AGPL), LEAN, or Nautilus are better answers |
| "vectorbt for sweeps" | ✅ | correct role; note its GitHub licence reports **NOASSERTION** — read `LICENSE` before commercial use |
| "bt or QSTrader for the portfolio layer; OptimalPortfolios for construction" | ✅ | sensible split of allocation vs construction; both ideas are in `../02-portfolio-multi-asset/FRAMEWORK_MATRIX.md` |
| "Twelve Data 800/day, Alpha Vantage 25/day, Tiingo 1,000/day, Finnhub 60/min, EODHD 20/day, Polygon 5/min" | ⚠️ unverified + volatile | free-tier quotas change without notice; record the quota in your data manifest at run time instead of trusting a table |
| "Combining strategies improved risk-adjusted returns by 30–50%" | ⚠️ unverified | no source was inspectable; treat as a hypothesis to test on your own data |
| "OHLCV discards intrabar ordering, so a stop and a target in the same bar cannot be sequenced" | ✅ **important** | true and under-appreciated; now a mandatory gate in `DATA_EVIDENCE_RULES.md` |
| "A *multi-asset* run tests rules per symbol; a *portfolio* run has one cash account where holdings compete" | ✅ **important** | the cleanest statement of a distinction that determines engine choice; now in `FRAMEWORK_MATRIX.md` |
| Safety: don't run autonomous agents on the daily driver; microVM over container; scope credentials; separate browser identity; skill supply-chain risk | ✅ | consistent with the guardrails already in this repo; the "any `skill.md` is an instruction vector" point is worth keeping |
| "Hermes cron + goal mode" | ⚠️ partial | `hermes cron` exists (verified in CLI help); a "goal mode" was not verified in this build |
| `Trigger.dev` / `agent-task-queue` / `tasks.md` / `Paperclip` for durability | 🟡 unverified | same names as the earlier notes, still not checked. A bespoke supervisor + JSON ledger is the proportionate answer for one machine |

## What was folded into the repository

| Destination | Change |
|---|---|
| `01-screen-control-llm/PC_AGENT_CONTROL_RESEARCH.md` §4.2 | RustDesk **service vs portable** (unattended access, pre-login, UAC secure desktop), and RDP-style daemons (`agent-rdp`) as an alternative to driving a viewer window |
| `01-screen-control-llm/PC_AGENT_CONTROL_RESEARCH.md` §6 | "No unauthenticated desktop-control endpoint" as an explicit guardrail |
| `02-portfolio-multi-asset/DATA_EVIDENCE_RULES.md` §2 | **Gate 7: intrabar sequencing** — a stop and a target inside one bar cannot be ordered from OHLCV; validate stop-dependent strategies on tick/L2 for the critical periods |
| `02-portfolio-multi-asset/FRAMEWORK_MATRIX.md` | **multi-asset run vs portfolio run** section, plus a verified Backtrader row (GPL-3.0, last push 2024-08) so the "use Backtrader" advice is not repeated uncritically |

## What to ignore

- `UIA-X` (does not exist), `Workroom` byte-identity claims (unverified), the "60 commands" figure, the stale
  Windows-MCP star count, and every free-tier quota number — check the vendor page on the day you build.
