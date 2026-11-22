# Review — Meta.ai (MuseSpark) challenge document

Input: pasted 2026-11-22, ~4k words, no runnable code but a complete set of conventions. Audited against the
GitHub API, the Actions scheduler, and this repo's gates.

**Verdict: the best *methodological* document of the thirteen.** It is the only one that independently arrives at
the same four controls this repo had to build by measurement — tree-first then OCR, `AMBIGUOUS` for a bar that
touches both exits, peer reproduction keyed to a data hash, and a JSON-only strategy contract so an agent cannot
invent its own harness. One invented tool name and one missing statistical gate keep it from being adoptable
as-is.

## What it gets right, and why it matters

| Convention | Why it is the correct call |
|---|---|
| **Two problems, split** ("desktop orchestration" vs "trading pipeline") | the same separation this repo settled on after a folder fight; conflation is what produced the earlier mess |
| **File queue with heartbeat + requeue on staleness** (`tasks.jsonl`, `heartbeats.jsonl`, 10-min timeout) | durable, inspectable, and survives an agent dying mid-task — the property a chat loop lacks |
| **`AMBIGUOUS` when one bar touches TP and SL**, "do not count as win" | exactly this repo's gate 7 and harness test T3 (both-touched bar → stop-out). Independently derived, same answer |
| **Strategy as JSON → template → harness; "if the agent can't express it in JSON, it doesn't run"** | the strongest anti-hallucination rule in any of the thirteen documents: it removes free-form code generation from the path that produces numbers |
| **Peer re-run keyed to `data_hash`**, and "if not reproduced, the round does NOT count as profitable" | the only peer-check in the batch that is a gate rather than a suggestion |
| **Kill criteria per 20-round block** | turns 200 rounds into ten falsifiable experiments instead of one long search |
| **`n=10` is a candidate, not proof**; "0 trades is also a result" | correct framing, and the opposite of the Qwen document |
| **Allowlist + audit log** under "no approval" | the right compensation for removing the human |
| **Cites the "signal generated on a candle that already moved" failure** | names the same-bar look-ahead that Claude 4.5 Opus's code actually contains |

## What is wrong

| Claim | Reality |
|---|---|
| "`own-computer-use-mcp` — self-hosted MCP server with OCR, mouse, keyboard, clipboard" | **No such repository.** GitHub search returns unrelated projects. The nearest real thing is `domdomegg/computer-use-mcp` (MIT, 407★) |
| "`Windows-MCP` — lightweight, open-source" | ✅ correct: `CursorTouch/Windows-MCP`, MIT, 11,999★ |
| "**Validation engine: `backtrader`** … where you add slippage, fees, spread, and intrabar TP/SL sequencing" | backtrader is **GPL-3.0**, last push **2024-08-19**, and it does not resolve intrabar ordering either — no bar-based engine can. Use LEAN / NautilusTrader, or a small bar-replay you own |
| "vectorbt … the open version ships a yfinance wrapper" | documented behaviour (`vbt.YFData`), not verified here — vectorbt is not installed on this machine |
| "Alpha Vantage: 25 req/day · Twelve Data: 800 · Finnhub: 60/min" | plausible and consistent with other documents, unverified; quotas move |
| "monitor.yml: every 30 min during market hours" | no `permissions: contents: write` specified (the commit will 403 on read-only defaults), cron is UTC, and 5 minutes is the platform floor |
| "10 paper trades **in 4 hours** on 15m BTC" | 4 hours is **16 bars**. Ten trades needs a cross roughly every 1.6 bars — the acceptance criterion is unreachable by construction. Express the target in bars of observation, not trades per session |

## The one missing gate: trial counting

It prescribes "thousands of parameter combos", then "keep top 5 by out-of-sample Sharpe", and a peer reproduction
check — but never counts the trials. With thousands of combos the expected best OOS Sharpe rises even when every
strategy is noise, and a peer re-running *the winner* reproduces the number without validating the selection.
Add: record `trials` in every `results/R###.json`, and deflate (see `02-*/DATA_EVIDENCE_RULES.md` §6). That is
the difference between "reproducible" and "real", and this document is one line away from having it.

Also absent: purging and an embargo in the walk-forward (Block 9 mentions walk-forward but not leakage), and
per-asset-class cost defaults (10 bps fee / 5 bps slippage is a crypto figure; FX spread, futures commission and
bond markup are different animals).

## What was adopted into this repo

- **The agent-authoring rule** — "if it cannot be expressed in the declaration, it does not run" — is now in
  [`../03-trading-strategies/STRATEGY_SPEC.md`](../03-trading-strategies/STRATEGY_SPEC.md) §1 as a hard constraint.
- The **`AMBIGUOUS` naming** is already gate 7 / T3 here; the review notes the independent convergence rather
  than adding a duplicate.

## Scoreboard (thirteen documents)

| Document | Structure | Facts | Quant rigour | Runnable | Honest about completion |
|---|---|---|---|---|---|
| **Meta.ai (MuseSpark)** | **best conventions** | high (one invented tool) | **high, minus trial counting** | no | yes |
| Arena playbook | good | high | medium | no | n/a |
| Perplexity | good | high on frameworks | medium | no | n/a |
| Gemini | good | high | high (fee trap) | snippet | yes |
| Claude 5.5 Haiku | best plan | high | high, fixable | **yes** | yes |
| Claude 4.5 Opus | most complete | high (real prices) | weak (4 defects) | **yes** | no |
| SUB Q (×2) | best formatted | weakest citations | medium | no | n/a |
| GLM | good schema | weakest market data | weak | no | no |
| GPT-4.1 mini | best project structure | poor tool list | weak | no | n/a |
| GPT-5 nano | most executable MVP | medium | weak | no | n/a |
| Pi.ai | short | one licence error | low | no | yes |
| Qwen Plus | tidy | **fabricated result** | none | no | no |
| Grok | broad | mixed | low | no | n/a |
