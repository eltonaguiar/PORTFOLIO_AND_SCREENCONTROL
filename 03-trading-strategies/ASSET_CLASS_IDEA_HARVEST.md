# Asset-class idea harvest — 10 classes, 3 models, 0 adopted wholesale

Method: one question to three different free models through the local router, each covering a different
slice of the estate so no single model's blind spot chose the class. Every answer was required to give a
**table of test + kill rule** per risk-appetite tier (capital-preservation / balanced / aggressive).
State injected: 10 classes under one proof contract, 67/374 cells tested, 0 proven, 10 killed, lag-0 fill
worth +2.54 bp and not executable, honest next-open +12.43 bp gross / +8.79 bp with 5 bp adverse, cost
horizon: annual cost drag = 365 / holding_days × round_trip_bps (15m→1D ratio 96×, venue-independent), FX live spread 8.0 bp, vol-target gap 2.3 vs 10.7 bp/day,
zero forward observations.

Run 2026-11-22, all three returned HTTP 200 in ~9–10 s. Raw: `asset_class_harvest_20261122.json`.

## Verdicts

| Model (router alias) | Classes | Verdict |
|---|---|---|
| `ULTRA_FREE_CLOUD_LARGE` | CRYPTO, EQUITY, ETF | **REJECT** — generic retail strategy names with non-measurements as kill rules ("3 consecutive daily losses", "5% decline in dividend yield", "10% loss in leverage over 2 weeks"). Nothing here is a pre-registerable test |
| `ULTRA_FREE_OPENROUTER` | BOND, FOREX, COMMODITY | **REJECT — echo failure.** It returned my own prompt statistics as if they were findings: "BOND / capital-preservation / lag-0 fill 2.54 bp edge", "COMMODITY / FX live top-of-book 8 bp spread capture". A crypto/FX measurement was relabelled onto bonds and commodities. This is worse than a wrong answer because it *looks* grounded |
| `ULTRA_FREE_NVIDIA` | FUTURES, MUTUAL_FUND, PRIVATE_CREDIT | **PARTIAL — 2 usable ideas**, because it specified n, horizon, lot size and a numeric tolerance instead of a stop-loss |

## The two ideas worth building on

1. **NAV-staleness in mutual funds.** Test: does a fund's closing price diverge from the next day's
   published NAV by more than 2%, and is the divergence tradable after the Questrade $9.95 fee and the
   front/back load? Kill rule as offered: *"execution lag > 1 day erodes edge"* — too vague; the
   pre-registered version is **kill if the T+1 NAV gap minus fees is ≤ 0 bp across ≥ 30 fund-days**.
   Why it is real: mutual-fund NAVs are struck once daily, so the price is mechanically stale — this is
   the one class where our measured 0.08% slippage is not the binding cost, the fee schedule is.
2. **Interval-fund / tender-offer timing.** Test: submit redemption at quarter-end and measure the
   acceptance rate and queue length. Kill rule as offered: *"acceptance < 50% or queue > 4 quarters"* —
   that one is already a measurement. Why it matters: it is a **liquidity** edge, not a price edge, so it
   is not in competition with the cost wall that killed everything else. It also needs data we may not
   have (tender history), which is the first thing to check.

Both are small, cheap and falsifiable. Neither is a recommendation to trade.

## The meta-finding: an echo is a new fabrication pattern

The `ULTRA_FREE_OPENROUTER` answer is the clearest example in this programme of a model **returning the
prompt's own statistics as its findings**, with the labels permuted onto the wrong asset classes. It
passes a casual read because every number is real — just not about the thing it claims.

Add to the fabrication checklist: *recompute every number in an answer; if it equals a number that
appeared in the prompt, treat it as an echo until proven otherwise.* A model that cannot produce a figure
independent of the prompt has not measured anything.

Corollary for harvest design: **never put your own measured results in the prompt** if you want
independent ideas. Batching all ten classes with the state block guaranteed at least one echo. The better
pattern is to state the *constraint* ("round-trip cost 12–20 bp, deflated-Sharpe gate, paper only") and
withhold the table.

## What the harvest actually changed

- Nothing was adopted as a strategy.
- Two mutual-fund tests were promoted to candidate hypotheses, both requiring a data-availability check
  first.
- One new checklist rule (echo detection) came out of a failure, which is the useful part.
- Confirmed: **expanding asset classes does not fix answer quality.** Breadth across models buys volume;
  the filtering is still the work, and two of three models produced nothing usable.
