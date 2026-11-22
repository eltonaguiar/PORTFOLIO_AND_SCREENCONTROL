# Review — GPT-5 nano challenge plan

Input: pasted 2026-11-22 (~3k words), a plan plus a draft `REALTIMECHALLENGE_GPT4NANO_*.MD`. Audited against the
GitHub API, the measurements in [`../01-screen-control-llm/MEASUREMENTS.md`](../01-screen-control-llm/MEASUREMENTS.md),
and the evidence rules in [`../02-portfolio-multi-asset/DATA_EVIDENCE_RULES.md`](../02-portfolio-multi-asset/DATA_EVIDENCE_RULES.md).

**Verdict: a competent outline with no numbers, one dead dependency, and a success metric that measures luck.**
It is the only document in the batch that states an MVP in executable steps (which is genuinely useful), but it
repeats the same two structural mistakes as the others: no isolation for unattended automation, and no trial
accounting for a many-round search.

## What it gets right

- **MVP scoped to what can be finished**: drive a browser + two desktop apps, 2–3 assets, a small parameter grid,
  one 5–10 minute paper trade. That is the right size for round 1.
- **Separate "pretend-live" module** with an explicit paper-only flag and no order placement.
- **Vetting requirement** for external code before it runs (matches the trust boundary in `01-*`).
- **Data honesty**: free sources only, read-only access, "with caution about rate limits".

## Errors and omissions

| Claim | Problem |
|---|---|
| "pyautogui for cross-app mouse/keyboard actions" | PyAutoGUI sends input to whatever holds focus (and is documented as unreliable on multi-monitor). It cannot orchestrate several windows — the exact requirement. Use an accessibility-tree driver (`cua-driver`, Windows-MCP, `agent-desktop`) with background delivery. |
| "Backtrader-like engine" | `mementum/backtrader` — GPL-3.0, **last push 2024-08-19**. Fine to read, wrong to build a 200-round programme on. |
| "Vision fallback: OpenCV/Tesseract" | Weakest link in the stack: Tesseract on anti-aliased UI text is measurably poor, and image templates break on theme/DPI changes. Use a grounding model (ShowUI/UI-TARS/OmniParser) or a11y text before templates. |
| "Options" listed as an asset class, no data plan for it | The data section covers equities/crypto/FX only. Free historical option chains are scarce — say so, or drop options from the MVP. |
| "OANDA demo" as a free FX feed | Requires an account and API token; not "free public data". Either accept the signup or use Dukascopy/yfinance FX. |
| "Success metric: positive P/L in at least some trials" | Measures the coin, not the strategy. With 200 rounds and thousands of parameter sets, *something* will show positive P/L by chance — that is the definition of the multiple-testing problem. Replace with: passes gates G1–G8 of [`../03-trading-strategies/STRATEGY_SPEC.md`](../03-trading-strategies/STRATEGY_SPEC.md), with `trials` declared. |
| "GitHub Actions … run a small pretend-live round on a timer" | Fine at nightly cadence; **not** a real-time executor (5-minute minimum, delays, 60-day auto-disable on inactive public repos), and some venues block CI datacentre IPs — observed in this repo at commit `7cfb713`. |
| Unattended, no human approval, no isolation | Same gap as the other plans: a shared machine, the user's browser profile, and a desktop-control endpoint add up to a code-execution path. Needs a separate Windows account or VM, allowlisted egress, and a panic path. |
| No cost model in the pretend-live loop | The 5–10 minute trade is exactly the case where fees eat the target (Gemini computed 16.8% of gross for a 0.59% target; at Binance standard 10 bps it goes negative). State the fee assumption before the trade, not after. |

## What was kept

- The MVP step list — folded into the round-1 checklist implied by
  [`../03-trading-strategies/README.md`](../03-trading-strategies/README.md) and `STRATEGY_SPEC.md`.
- The "pretend-live module, paper-only flag" separation, which matches
  [`../02-portfolio-multi-asset/PAPER_TRADING_AND_MONITORING.md`](../02-portfolio-multi-asset/PAPER_TRADING_AND_MONITORING.md).

## Scoreboard (eight documents audited)

| Document | Structure | Facts | Quant rigour | Safe by default |
|---|---|---|---|---|
| Arena playbook | good | high | medium | **best** |
| Perplexity | good | high on frameworks | medium | high |
| Gemini challenge | good | high (verified) | **best (fees, no fake close)** | medium |
| SUB Q (×2) | best formatted | weakest citations | medium | medium |
| GLM challenge | good schema | weakest market data | weak | low |
| GPT-4.1 mini blueprint | best plan | poor tool list | weak | low |
| **GPT-5 nano plan** | **most executable MVP** | medium (one dead lib) | **weak (success metric)** | low |
| Grok | broad | mixed | low | low |
