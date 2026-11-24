# F5 — FX trap for a Canadian account: brokerage conversion vs CDR / hedged alternatives

**Item:** F5 `H` — gate G1 (cost). Owner: Hermes (Session B). Run: 2026-11-24 06:18 UTC / 01:18 EST cron.
**Status:** DONE. Artifact: `03-trading-strategies/results/f5_fx_trap.json`.
**H3 rule:** every number carries (source, fetch date) or an explicit `ASSUMED` tag.

## The trap

A CAD account that buys a US-listed name (stock or ETF) converts CAD to USD on the buy and USD to CAD on the sell. The broker embeds its fee in the exchange rate, so it is never itemized as a commission.

**Questrade, published:** Currency Conversion (USD/CAD) = **1.5%**, built into the exchange rate, each direction.
- Source: https://invest.questrade.com/pricing/self-directed-commissions-plans-fees/transaction (fee schedule; footnote 10: fee last updated 2023-11-18).
- Fetched: 2026-11-24.
- Commissions on stocks/ETFs: $0 (since Feb 2025, same page).

**Round trip per US name:** 1.5% in + 1.5% out = **~3.0% of capital** (derived from the two published one-way figures). Before any market edge, 3.0 percentage points must be earned back from price movement alone. That is the trap: it dwarfs intraday/swing edges and compounds on every US-name round trip.

**Discrepancy corrected:** this TODO and `04-investment-strategy/portfolios.json` (F1 note) previously carried **1.75%** as the per-conversion FX figure. That figure appears nowhere on Questrade's current published schedule; it is an unchecked ASSUMED figure carried from earlier docs. It is now replaced by the verified 1.5% and tagged `ASSUMED/stale` wherever it still appears (A3, CP-owned, remains open to re-publish the full schedule with source URL + fetch date).

## Alternatives

| Alternative | Mechanism | Effective cost | Source / status |
|---|---|---|---|
| Brokerage conversion (Questrade) | Embedded in CAD<->USD rate on each trade | 1.5% per way, ~3.0% round trip | invest.questrade.com fee schedule, fetched 2026-11-24 (verified) |
| Dual-currency account | Hold USD cash; journal CAD<->USD instead of converting per trade; avoids repeated conversion when USD balance suffices | journal fee $9.95/request at Questrade (free with Questrade Plus); $0 ETF commissions | Questrade fee schedule + third-party broker guides (hahninvest.com, savvynewcanadians.com), fetched 2026-11-24 (third-party summary of Questrade schedule) |
| Norbert's gambit | Buy DLR.TO (CAD line), journal to DLR.U (USD line), sell DLR.U; same fund, two TSX listings | ~0.1-0.4% effective on small conversions (bid-ask spread ~0.2% round trip plus commissions/journal), vs 2.0-3.5% big-bank markup | thelongmath.com, hahninvest.com, canadianmoneysaver.ca, fetched 2026-11-24 (third-party figures; DLR rebranded from Horizons to Global X in May 2024 per hahninvest.com) |
| CDR (Cboe Canada / TSX) | Canadian Depositary Receipts: fractional interest in US stocks, trade in CAD, embedded notional FX hedge (CDR ratio adjusts daily against an FX forward), TFSA/RRSP-qualified | no per-trade conversion; per-series embedding cost not verified here | cboe.com CDR brochure (2024-09), cdr.cibc.com directory, fetched 2026-11-24 (mechanism verified; cost figures ASSUMED/unverified) |
| Hedged CAD ETFs (XSP/VSP class) | Trade in CAD with embedded currency hedge | MER in the ~0.1% class | ASSUMED — not fetched from a fund fact sheet in this run |

## Verdict

The FX trap is real at Canadian retail brokerages: ~3.0% round trip at Questrade's published rate swallows short-horizon edge entirely. Alternatives cut effective FX cost roughly 5-10x (gambit ~0.1-0.4%; CDR/hedged ETFs trade in CAD with embedded hedge, no per-trade conversion). For position sizes where the gambit's fixed journal fee dominates, CDR/hedged CAD instruments are the cheaper path; for larger sizes the gambit approaches the spread floor.

All figures above carry a source URL and fetch date, or an explicit ASSUMED tag, per H3.
