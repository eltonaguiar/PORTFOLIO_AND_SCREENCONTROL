# Review — Claude 5.5 Haiku challenge document (the runnable prototype)

Input: pasted 2026-11-22 (~5.8k words), containing a full 200-round plan, a repository layout, and **actual
Python**: `backtest_core.py`, `run_backtest.py`, `paper_trader.py`, plus a GitHub Actions workflow. Audited by
reading the code line by line, checking its claims against the market, and comparing its rules with this repo's
evidence gates.

**Verdict: the best-engineered document in the collection.** It is the only one that (a) ships code that would
run, (b) is causal by construction, (c) books the stop first when a bar touches both, (d) splits in-sample and
out-of-sample, and (e) states its own limitations unprompted. Its weaknesses are statistical rather than
mechanical: a single 70/30 split, no trial accounting for an 81-combination grid, and realized-only equity that
understates both drawdown and Sharpe.

## What it gets right (and the others did not)

| Detail | Why it matters |
|---|---|
| Signals computed on bar close, fill at **next bar open** (`sig = signal.shift(1)`) | the single most common look-ahead bug, avoided by construction |
| **Stop first** when a bar touches both (`if l[i] <= sl` before `elif h[i] >= tp`) | matches this repo's harness test T3 (both-touched bar → stop-out) instead of an optimistic guess |
| Costs charged **both sides** (fee + slippage on entry and exit), and stated per asset class | most documents omit or hand-wave this |
| 70/30 in-sample / out-of-sample split, verdict only from OOS | better than every other plan here except the peer harness |
| **≥30 trades** before a result counts | kills the "one lucky session" claim |
| Neighbour-parameter stability required (not a single sharp spike) | the honest anti-overfit check, stated as a pass condition |
| Explicitly says a **single profitable paper session is not evidence** | correct, and rare |
| `paper_state.json` + `paper_ledger.csv` with timestamps | an artifact trail, so results are auditable |
| Honest caveat: "realized equity understates drawdown while a position is open" | self-diagnosed flaw, scheduled for round 9 |
| Honest expected outcome: "most simple technical strategies fail after costs, and that is a valid result" | the correct prior |

## Verifiable claims

| Claim | Check |
|---|---|
| Binance public klines, no key, paged with `limit=1000`, `sleep(0.2)` | correct; the endpoint and pagination are as described |
| `BARS_PER_YEAR` {1m: 525600, 1h: 8760, 1d: 365} | correct for 24/7 crypto |
| "GitHub's scheduled workflows can run late under load, so the ledger timestamps are the source of truth, not the cron schedule" | correct, and the right conclusion (5-minute minimum, delayed starts) |
| OANDA practice account as the free FX intraday source | real, requires signup — stated, unlike other documents |
| "LinkedIn's terms prohibit automated scraping … use only manual-assisted or saved-page extraction" | correct and responsible; consistent with this repo's browser rules |
| Windows Sandbox for untrusted code | real, but Windows **Pro/Enterprise** only — see corrections |

## Defects worth fixing before round 1

1. **Realized-only equity.** `eq[i]` never marks to market, so a long open position shows zero return until
   exit. Consequences: drawdown is understated (they know), and **Sharpe is understated too** — flat stretches
   dilute `r.std()`. Fix: mark to market at each close using the current price, as the peer harness does.

2. **81 combinations, no trial count.** The grid is 3 fast × 3 slow × 3 TP × 3 SL = **81** parameter sets, and
   the best in-sample Sharpe is selected from them. That selection inflates the expected OOS result, and the
   document does not account for it. Fix: record `trials: 81` in the result and compare the winner against the
   **distribution** of all 81 (or a permutation control), not against zero. See `02-*/DATA_EVIDENCE_RULES.md` §6.

3. **One 70/30 split is a weak OOS test.** It gives a single verdict from one period; a rule that only works in
   the last 30% of one regime passes. Fix: purged walk-forward with ≥5 folds, and report the spread.

4. **The paper trader's economics.** 0.4% target / 0.2% stop with a **0.2% round-trip cost** means costs consume
   half the gross target — the same trap Gemini quantified (16.8% of a 0.59% target). The document says the edge
   is likely low; the arithmetic says it is likely negative. State that up front rather than as an expectation.

5. **`backtesting.py` is AGPL-3.0** (named for simple checks). Fine for personal use; a licence trap if any of
   this ships inside a product.

6. **Windows SmartScreen / Sandbox caveat**: Windows Sandbox needs Pro/Enterprise — the plan should say so, and
   fall back to a separate low-privilege account (which the document also proposes, so this is a note, not a gap).

7. **The supervisor's timeout rule** ("sends 'continue from the last step in PROGRESS.md' up to 3 retries") is
   still a timed nudge. It is better than a bare timer because it carries state, but it should first *read* the
   lane's output and classify the stop (done / stalled / looping / blocked) before re-sending. See
   `01-*/PC_AGENT_CONTROL_RESEARCH.md` §5.

## Peer cross-check protocol (adopt as-is)

Its section 7 is the best-written cross-check checklist of the ten documents: data source reproducible, costs
stated, OOS reported, trade count, reproduction, live claims must cite ledger rows with timestamps, desktop
claims must cite a `PROGRESS.md` line plus a file hash or screenshot. That is the same standard as
[`../03-trading-strategies/FABRICATION_CHECKLIST.md`](../03-trading-strategies/FABRICATION_CHECKLIST.md),
expressed in prose — use them together.

## Scoreboard (ten documents audited)

| Document | Structure | Facts | Quant rigour | Ship-ready code | Safe by default |
|---|---|---|---|---|---|
| Arena playbook | good | high | medium | no | **best** |
| Perplexity | good | high on frameworks | medium | no | high |
| Gemini challenge | good | high (verified) | **high (fee trap, no fake close)** | snippet | medium |
| **Claude 5.5 Haiku** | **best plan** | high | **high, with fixable gaps** | **yes (runnable)** | **best of the challenge docs** |
| SUB Q (×2) | best formatted | weakest citations | medium | no | medium |
| GLM challenge | good schema | weakest market data | weak | no | low |
| GPT-4.1 mini | best project structure | poor tool list | weak | no | low |
| GPT-5 nano | most executable MVP | medium | weak | no | low |
| Qwen Plus | tidy | **fabricated result** | none | no | **worst** |
| Grok | broad | mixed | low | no | low |

## Bottom line

If one of these documents should be ported into `03-trading-strategies/` as a second harness, it is this one —
after four changes: mark-to-market equity, `trials: 81` plus a permutation control, purged walk-forward instead
of one split, and a paper-trader configuration whose target is not half-consumed by fees.
