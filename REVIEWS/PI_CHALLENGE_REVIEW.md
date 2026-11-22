# Review — Pi.ai challenge document

Input: pasted 2026-11-22, ~1.1k words, no code. Audited against the GitHub API, OANDA's own API docs, the
GitHub Actions scheduler, and arithmetic on the strategy it proposes.

**Verdict: an honest sketch with a wrong licence, a timezone bug, a job that cannot push, and a strategy that
cannot produce a single signal in the session it specifies.** It is the shortest of the twelve and, credit where
due, the only one that says "I'll run this live next session and report back" instead of claiming a result.

## Factual errors

| Claim | Reality |
|---|---|
| "backtrader … **MIT-licensed**" | **GPL-3.0** (23,776★, last push 2024-08-19). This is not pedantry: GPL-3.0 in a shipped product is a distribution obligation, and the licence is the first thing a reviewer checks |
| "Built-in support for … **walk-forward analysis**" | backtrader ships `optstrategy` (grid optimisation). Walk-forward analysis is something **you** write around it; it is not a feature |
| "Oanda v20 **doesn't support streaming** — use REST polling" | **Wrong.** v20 exposes a pricing stream endpoint served by OANDA's streaming URLs, and the Python wrapper ships `PricingStream`. What may lack a stream is a particular client, not the API |
| `cron: '0 9 * * 1-5'  # 9 AM EST` | GitHub Actions cron is **UTC**. `0 9` runs at **04:00–05:00 Eastern**, not 9 AM. Either use `0 14 * * 1-5` (EDT) or state "09:00 UTC" |
| "**MCP (Model Control Protocol)**" | Model **Context** Protocol — the same mis-expansion that appeared in the GPT-4.1 mini document |
| "`goose` … Apache 2.0" · "Agent S3" | ✅ correct: `block/goose` Apache-2.0, 56,864★; `simular-ai/Agent-S` Apache-2.0, 13,017★ |

## Three defects that stop it running

1. **The workflow cannot push.** No `permissions: contents: write`. Since GitHub made `GITHUB_TOKEN` read-only by
   default for public repos, the "Commit and push results" step returns 403. The job looks healthy and silently
   leaves nothing behind — the worst kind of CI failure, because a green run implies success.

2. **The script does not exist.** `run: python backtest_sma_cross.py` references a file that is not in the
   document. Nothing to run.

3. **The strategy cannot fire in the stated session.** SMA cross 10/30 on **15-minute** bars, run **09:30–16:00**.
   That window is **26 bars**; a 30-period SMA needs **30 closed bars** before it produces a value. The slow
   average is `NaN` for the entire session, so no crossover can occur and the trade log is empty by
   construction — not because the market was quiet, but because the parameters and the window are incompatible.

Add that the rules state TP 2% / SL 1% with **no commission, spread or slippage**, and the proposed experiment
could not have measured anything even if it had run.

## What is right

- Names real, current tools: `ccxt`, OANDA, `goose`, Agent-S, Alpaca, IB.
- Uses **RustDesk for unattended control** and states the goal as "agents keep going until the goal is met" —
  the correct framing, even without the mechanism (harness continuation beats a supervisor that only re-prompts;
  see `01-*/PC_AGENT_CONTROL_RESEARCH.md` §5).
- Proposes peer cross-checking by shared `REALTIMECHALLENGE_*.md` files.
- Does not fabricate a result. Compared with the Qwen document, that alone puts it above the median here.

## Minimal fix list

1. Change the licence line to GPL-3.0, or switch the engine to `backtesting.py` (AGPL) / LEAN (Apache-2.0).
2. Add `permissions: contents: write` and `workflow_dispatch` to the workflow.
3. Ship `backtest_sma_cross.py`, or delete the step.
4. Either widen the session to ≥ 8 hours of 15-minute bars, drop the slow SMA to 20, or use 5-minute bars.
5. Add fees, spread and slippage to the rules before any comparison.
6. Record the run timestamp in UTC, and state bar-close vs next-open fill.

## Scoreboard position (twelve documents)

Short, honest, unrun — above the two documents that claimed results they did not have (Qwen: invented prices;
Claude 4.5 Opus: real prices, false completion), and below the four that shipped something executable. Its most
useful contribution is negative: it demonstrates in three lines how a cron timezone, a missing permission and an
incompatible bar count each silently produce an empty or unlanded result.
