# Portfolio tracking across asset classes — the stack that survives contact with reality

Backtesting asks "would this rule have worked?". Tracking asks "what do I own, what is it worth, and how did
*my* money do?". They need different tools, and the tracker is the one that stays useful for decades.

## 1. The source of truth: a double-entry ledger

Not a spreadsheet, not a broker's dashboard, not a notes app. A ledger where every movement has two sides:

```
2026-03-14 * "Buy 100 VFV" "TFSA"
  Assets:Brokerage:TFSA:VFV      100 VFV @ 145.20 CAD
  Assets:Brokerage:TFSA:Cash    -14,520.00 CAD
  Expenses:Commission                  0.00 CAD

2026-04-02 * "VFV dividend"
  Assets:Brokerage:TFSA:Cash       62.10 CAD
  Income:Dividends:VFV            -62.10 CAD

2026-05-30 * "Buy 500 XEQT" "RRSP"
  Assets:Brokerage:RRSP:XEQT     500 XEQT @ 31.04 CAD
  Assets:Brokerage:RRSP:Cash   -15,520.00 CAD
```

Why this shape:

- **Multi-currency is native.** A USD purchase is two postings plus an FX rate; the ledger keeps both the original amount and the base-currency value.
- **Transfers are not trades.** Moving 1 BTC between wallets must not create a taxable event or a gain — a double-entry transfer can't accidentally do that; a holdings spreadsheet does it all the time.
- **Every report is a query**, not a manual reconciliation. Positions, cost basis, realised gains, income, FX exposure are all derivable.
- **It version-controls.** Plain text diffs in git; audit trail for free.

Tools: **Beancount** (GPL-2.0, 6,194★) with `bean-query`/`fava`, or **hledger** (GPL-3.0, 4,832★) if you prefer
a CLI with strong multi-currency reports. Portfolio Performance (**buchen/portfolio**, EPL-1.0, 4,183★) is the
best GUI alternative and imports broker statements, but its data file is a binary-ish XML that you cannot code
against easily.

## 2. Prices: one store, one schema, explicit timestamps

| Asset class | Practical source | Caveat |
|---|---|---|
| Stocks / ETFs | `yfinance` (Apache-2.0) or broker exports | unofficial API, rate limits, adjust for splits/dividends |
| Mutual funds | fund company / provider NAV feed, broker export | **NAV is not return** — you must add distributions |
| Bonds | broker marks, FRED yields for context | clean vs dirty price; accrued interest belongs in valuation, not price |
| Commodities / futures | exchange settlement prices, continuous series | roll rules must be explicit and consistent |
| FX | central-bank daily fix (BoC, ECB) or broker quotes | pick one convention and record it; weekend/holiday gaps |
| Crypto | `ccxt` (MIT) or exchange archives | funding costs on perps; exchange-specific symbols |
| Cash | bank statements | interest accrual, multi-currency accounts |

Store prices with: `symbol, venue, currency, date (UTC), price_type (trade|quote|mid|nav|mark), source,
retrieved_at`. Anything without `price_type` and `retrieved_at` will bite you in a backtest later.

## 3. Valuation (the arithmetic that actually matters)

```
position_value_base = quantity × price × fx_rate(base/quote, as_of)
portfolio_value     = Σ position_value_base + cash_base
```

Rules that prevent most reporting bugs:

1. **One base currency, one as-of timestamp.** Convert at the *valuation* rate, not the purchase rate. Keep the purchase rate separately for cost basis.
2. **Income is not price.** Dividends, coupons, and fund distributions are cash flows; a "total return" series that ignores them understates everything.
3. **Cost basis has a method.** FIFO, LIFO, or average cost — choose per jurisdiction, record it, and never mix methods between reports.
4. **Futures rolls are not gains.** A roll is closing one contract and opening another; treating the price gap as profit is the classic futures-tracking error.
5. **Bond valuation** = clean price × face/100 + accrued interest, with the day-count convention stated (30/360 vs ACT/ACT changes the number).
6. **Crypto transfers are not disposals.** Wallet-to-wallet movements need matching transfer postings.

## 4. Performance measurement — TWR vs MWR

Both are correct; they answer different questions.

- **Time-weighted return (TWR)** removes the effect of your deposits/withdrawals — it measures the *strategy*.
  Chain sub-period returns across every external cash flow:
  `TWR = Π(1 + rᵢ) − 1`, where `rᵢ = (V_end − CF) / V_start − 1` for each sub-period between flows.
- **Money-weighted return (MWR / IRR)** measures *your* outcome including timing — solve
  `Σ CFₜ / (1+IRR)^t = 0` over dated cash flows.

Report both, plus: max drawdown, volatility, exposure by asset class and currency, realised vs unrealised PnL,
income by type, and fees. A single "return %" number with no method is not a report.

## 5. The pipeline

```
broker/fund/exchange exports ──► normalise (OFX/CSV/JSON → postings)
                                        │
                                        ▼
                             ledger (Beancount/hledger)  ◄── manual entries for cash, fees, transfers
                                        │
      price store (daily close per instrument, per currency) ──┘
                                        │
                                        ▼
                        report generator (positions, TWR/MWR, exposure, tax lots)
                                        │
                     ┌──────────────────┴──────────────────┐
                     ▼                                     ▼
             static HTML/PDF                        Ghostfolio API (optional UI)
```

- **Daily cadence is enough** for a personal portfolio; intraday adds cost with no decision value.
- **Reconcile monthly** against the broker statement: quantity per position and cash balance must match exactly. A silent mismatch invalidates every return number after it.
- **Snapshot the ledger** (`git tag portfolio-2026-11`) before any bulk import.

## 6. When to add a dashboard

Ghostfolio (**AGPL-3.0**, 9,757★, self-hosted) is the best free web UI for multi-asset holdings with
multi-currency and allocation views. Use it as a *view* over data you already trust, not as the source of
truth — and note AGPL obligations if you modify and host it for others.

## 7. What not to do

- ❌ One spreadsheet with prices pasted by hand — no audit trail, breaks silently on splits and FX.
- ❌ Broker dashboards as history — they change, they lie about cost basis across transfers, and they vanish when you switch brokers.
- ❌ "Return" computed as `(end − start) / start` on a portfolio you contributed to — that is mostly a measure of your deposits.
- ❌ Mixing fund NAV with total return and comparing them to an ETF's price return.
- ❌ Tracking crypto by exchange balance only — transfers between venues double-count.
