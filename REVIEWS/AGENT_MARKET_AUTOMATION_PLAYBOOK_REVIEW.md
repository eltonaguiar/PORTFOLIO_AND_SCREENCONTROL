# Review — "Portable AI Agent Playbook: Desktop Control, Persistent Work, and Market Research"

Input: [`inputs/AGENT_MARKET_AUTOMATION_PLAYBOOK.md`](inputs/AGENT_MARKET_AUTOMATION_PLAYBOOK.md) (Arena,
2026-11-22, 97 lines, user-supplied). Reviewed the same day against the actual repositories and against the
measurements in [`../01-screen-control-llm/MEASUREMENTS.md`](../01-screen-control-llm/MEASUREMENTS.md).

**Verdict: the most sound of the four answers collected — right instincts, no numbers, one weak citation.**
Roughly 80 % of it survives review unchanged, and its evidence discipline (§"Data and evidence rules") was
adopted into [`../02-portfolio-multi-asset/DATA_EVIDENCE_RULES.md`](../02-portfolio-multi-asset/DATA_EVIDENCE_RULES.md).

## Claim-by-claim

| Claim | Verdict | Note |
|---|---|---|
| "Build a local agent runner + adapters, not one giant prompt or one universal desktop-control server" | ✅ correct | Matches the five-layer split used here; the layer boundaries are the load-bearing idea |
| "MCP is the tool interface, not the supervisor; it does not keep an agent working" | ✅ correct | The single best sentence in any of the four answers |
| "Playwright MCP for browsers, structured accessibility over pixels" | ✅ correct | Playwright MCP is Apache-2.0, 39,989★ (verified); for Chrome-specific work DevTools MCP is a better fit when you need network/console/frames |
| "Run the computer-use adapter in the interactive session on the remote target" | ✅ correct, and the most important operational point | Confirmed by measurement: an inaccessible Electron tree is a bitmap, so an adapter *on the target host* beats driving a compressed RustDesk window. Where SSH exists, use it for control and RustDesk for eyeballs |
| "A community RustDesk bridge illustrates that deployment shape — validate maintenance, platform support, and permissions" | 🟡 weak citation | The linked Glama listing could not be substantiated; no repository or maintenance evidence was found. Correct to hedge, but this should not be a design input |
| "Temporal for durable workflows; LangGraph for lighter Python agent workflows" | ✅ real, 🟡 heavy | Both exist and fit the description. For one machine and one supervisor, a 200-line runner with a JSON ledger and a `STOP` file covers the same ground; adopt Temporal when the work genuinely spans hours and must survive restarts |
| "Do not retry side-effecting UI actions blindly: inspect state first" | ✅ correct | This is the verify→escalate rule; in cua-driver terms, read the structured verdict and re-capture before repeating an action |
| "Define task_id, deadline, stop conditions, heartbeat, bounded retries, verification gate" | ✅ correct | Directly informs the supervisor design in `01-*/PC_AGENT_CONTROL_RESEARCH.md` §5 |
| "LEAN for conventional multi-asset; NautilusTrader for backtest-to-live parity, custom instruments, multi-venue" | ✅ correct | Verified: LEAN Apache-2.0 22,651★; Nautilus LGPL-3.0 31,734★. Missing nuance: Nautilus's **stable PyPI is still v1 (1.231.0)** while v2.0.0 is RC-only on `develop` — see `02-*/NAUTILUS_ARCHITECTURE.md` |
| "Mutual funds are not a first-class asset class in LEAN; supply NAV data yourself" | ✅ correct | Also true of Nautilus; neither ships a mutual-fund adapter |
| "vectorbt is fast research, not a universal event-driven simulator" | ✅ correct | Add: its GitHub licence reports NOASSERTION — read `LICENSE` before commercial use |
| "Data rules: source, retrieval timestamp, venue, timezone, price type, live/delayed/historical, adjustment, rolls, survivorship, licences, costs" | ✅ excellent | Adopted nearly verbatim; extended with stale-data gates, OHLC sanity, and a machine-readable manifest |
| "Label facts observed / derived / assumed, and say 'not verified'" | ✅ excellent | Adopted |
| "The engine is not the data" | ✅ correct | Worth repeating in every backtest report |
| Handoff prompt (§"Host-neutral handoff prompt") | ✅ useful as-is | Its clause "do not claim to be running unless the runner reports a live heartbeat" is a neat guard against an agent narrating continuity it doesn't have |
| "Keep live execution disconnected; consider paper trading only after validation" | ✅ correct | Same boundary enforced in `DATA_EVIDENCE_RULES.md` §6 |

## What this repository adds that the playbook lacks

1. **Measured numbers.** The playbook says "prefer accessibility"; it cannot tell you that this specific VS
   Code window exposed **three** UIA elements, that OCR took **19 s** per frame, or that a 4B local VLM returns
   **nothing** when asked for a coordinate.
2. **The stop taxonomy.** The playbook says "monitored workflow, not an endless loop". It does not enumerate the
   eight ways an agent stops (turn limit, approval reflex, genuine question, loop, no-progress, quota/auth,
   network, done) or what to do for each — which is the actual implementation work.
3. **A concrete injection ladder.** Harness flags → SDK events → UIA textbox → pixels, with the verified
   Copilot CLI flags and the `session.idle` / `task_complete` distinction.
4. **Asset-class plumbing.** NAV vs return, clean vs dirty bond prices, futures rolls, crypto transfers — the
   places where a "multi-asset" portfolio silently becomes wrong.
5. **A fact-check of the tools it names**, so a reader can tell which project to clone and which to ignore.

## Net changes made to the playbook's recommendations

| Playbook says | This repo does instead | Why |
|---|---|---|
| Temporal as the default durable runner | Bespoke supervisor first; Temporal only when work spans hours across restarts | proportionality for a single-machine setup |
| "Run an adapter on the remote target" | Same, plus: prefer SSH over any pixel channel, RustDesk only for watching | verified that pixel-only perception loses the tree, exit codes, and transcript |
| LEAN as the default engine | Decision path with 8 engines keyed to paradigm and asset class | one engine cannot be best at sweeps, microstructure, and live parity |
| RustDesk bridge as an illustration | Removed as a design input | unverifiable citation |
