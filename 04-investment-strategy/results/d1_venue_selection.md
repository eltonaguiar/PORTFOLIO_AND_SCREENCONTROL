# D1 — Prediction-market venue selection (calibration sleeve)

Status: DONE — 2026-11-23. Owner: H (Hermes). Serves gates G3 (selection) and G5 (provenance).

## Venue picked: Polymarket

Polymarket (polymarket.com): USDC on Polygon; prediction markets resolved through the UMA Optimistic Oracle. Picked because it is reachable without US-person KYC/SSN and because its full fee and resolution documentation is public.

Alternative considered and declined: Kalshi (CFTC-regulated event exchange, fiat). Not pursued: account opening is identity/SSN-gated (effectively US-person focused), so it is not accessible from this jurisdiction; Kalshi also does not support wire withdrawals below $500,000. Kalshi remains the regulated fiat alternative if eligibility changes.

## Fee structure — Polymarket

Source: https://docs.polymarket.com/trading/fees (fetched 2026-11-23).

- Taker fee = C × feeRate × p × (1 − p), where C = shares traded and p = price in dollars.
- Makers are never charged; only takers pay; cancelling a resting order is free.
- Category fee rates (taker): 0.05 — Sports (incl. NFL/college football), Finance, Tech, Politics—elections, Crypto BTC 5- and 15-minute up/down, Combos, Other/General; 0.01 — other Crypto, Politics—non-election, Economics, Culture, Weather, Mentions; 0 — Geopolitics (fee-free).
- Fee per 100 shares peaks at 50¢ probability: $1.25 at the 0.05 rate, $0.25 at the 0.01 rate; symmetric around 50¢, falling toward 1¢/99¢.
  - Example: 100 shares at 50¢ in a 0.05 category cost $50.00 + $1.25 fee = $51.25; break-even win chance 51.25% (vs 50% before fees).
- No Polymarket fee to deposit or withdraw USDC; intermediaries (e.g., Coinbase, MoonPay) may charge their own. Polymarket does not charge a separate fee on winnings; the taker fee is taken at match time.
- Fees rounded to 5 decimals; minimum chargeable fee 0.00001 USDC.

## Spread

Not measured. No live order-book read was taken from this box, and spread varies per market and over time, so no number is quoted. Spread is recorded here as UNMEASURABLE — it must be read off both sides of the order book before any trade, and never substituted with a guess. (Programme convention: if it cannot be recomputed or measured, it is not evidence.)

## Resolution risk

Source: https://docs.polymarket.com/concepts/resolution (fetched 2026-11-23).

- Prediction markets use the UMA Optimistic Oracle; up-down markets use Chainlink TWAP (not relevant to this sleeve).
- Resolution flow: anyone may propose an outcome with a bond (typically $750 pUSD); 2-hour challenge period. Undisputed → market resolves (~2 hours total). Disputed → new proposal round; second dispute → 24–48h debate period; still disputed → UMA token-holder vote (~48h).
- Rare outcome: market can resolve 50/50 (each token redeems $0.50) when the outcome is unknown or not applicable.
- Each market carries pre-defined resolution rules (outcome source, end date, edge cases); the market title is not the rule — rules must be read before trading.
- Resolution delay and dispute risk are genuine: capital can be locked from ~2h to several days, and a disputed resolution can turn against the traded position. Polymarket may also publish clarifications that bind voters.

## What this does not claim

- No live spread or slippage number (unmeasured).
- No profitability or edge claim — this is documentation for the D2/D3 calibration harness, not a signal.

Done condition: venue, fee schedule (with source + fetch date), spread treatment, and resolution risk documented above; every number carries (source, date).
