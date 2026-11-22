# Data and evidence rules — mandatory for anything labelled "research"

Adapted from the user-supplied handoff playbook (Arena, 2026-11-22) and extended with the failure modes found
while auditing real backtest pipelines. The point is not bureaucracy: **an agentic system amplifies bad inputs
instead of failing gracefully**, so the gate has to sit before the reasoning, not after the report.

## 1. Every series carries provenance

A price series without these fields is not usable in a report:

```json
{
  "series_id": "VFV.TO:close:2020-01-02..2026-11-21",
  "symbol": "VFV.TO",
  "venue": "TSX",
  "instrument_type": "etf",
  "currency": "CAD",
  "frequency": "1d",
  "price_type": "nav|close|mid|trade|settlement|mark",
  "adjustment": "split_and_dividend|split_only|none",
  "source": "yfinance|broker_export|exchange_archive|provider_x",
  "retrieved_at": "2026-11-22T14:03:11Z",
  "status": "historical|delayed|realtime",
  "measured_delay_seconds": null,
  "missing_bars": 0,
  "stale_check": "last_bar_utc == previous_session_close",
  "licence": "vendor terms — no redistribution",
  "snapshot_hash": "sha256:…"
}
```

Hard rules:

1. **`retrieved_at` in UTC, always.** Local time in a data record is a bug waiting for a DST boundary.
2. **`price_type` is not optional.** A fund NAV and a last trade are different instruments for return purposes.
3. **Adjustment policy stated.** Splits and distributions change history; an unadjusted series produces fake gaps and fake returns.
4. **Venue and timezone stated.** "AAPL" is not an instrument; `AAPL:NASDAQ:USD` is.
5. **Licence recorded.** Many feeds prohibit redistribution; storing that fact with the series prevents an accidental public artifact.

## 2. Stale-data and quality gates (run before any analysis)

```
gate 1  schema      all required fields present, types valid
gate 2  continuity  no gaps > 1 session for daily data; holiday calendar respected
gate 3  staleness   last observation within one session of "now" for live claims
gate 4  sanity      |return| > 50% in one bar → require explanation (split? error? halt?)
gate 5  range       OHLC invariants: low ≤ open,close ≤ high; no negative volume
gate 6  coverage    each asset class in scope has ≥ 1 validated series, not just the easy one
gate 7  intrabar    if the strategy uses both a stop and a target, OHLCV cannot order the two inside one
                    bar — validate the critical periods on tick/L2 data, or reframe the rule
```

If any gate fails: **stop the cycle and report**, do not reason on the data. This single habit prevents most
confidently-wrong market claims.

## 3. Every claim is labelled

| Label | Means | Example |
|---|---|---|
| **observed** | returned by a tool/API/file, with a timestamp and a locator | "AAPL closed at 231.14 on 2026-11-21 (source: vendor, retrieved 14:03Z)" |
| **derived** | computed from observed inputs by a named method | "TWR 2025 = 11.8% (daily chaining, fees included)" |
| **assumed** | a modelling choice, not a fact | "slippage = 2 bps per side; borrow cost ignored" |
| **not verified** | could not be proven with available tools | "fund distribution history could not be confirmed" |

A live quote is not evidence of future behaviour. A backtest is a conditional statement about the past under
stated assumptions — write it that way, or it becomes a sales pitch.

## 4. Every backtest ships a manifest

```yaml
strategy: ema_cross_v3
code_ref: git:9f2c1ab            # exact commit, not "latest"
data_snapshot: sha256:…          # immutable reference, not a mutable path
universe: [VFV.TO, XEQT.TO, AAPL]
period: {start: 2018-01-02, end: 2026-11-21, timezone: America/Toronto}
costs: {commission: 0.0, spread_bps: 3, slippage_bps: 2, borrow_bps_pa: 0}
assumptions: [no shorting, dividends reinvested at close, fills at next open]
benchmark: SPY total return
results:
  cagr: 0.084
  vol: 0.132
  max_drawdown: -0.187
  sharpe: 0.64
  trades: 412
  exposure_avg: 0.71
oos: {method: walk_forward, folds: 6, cagr_range: [0.02, 0.11]}
```

Rules:

- **No out-of-sample, no claim.** In-sample numbers are a hypothesis generator.
- **Report failures.** The strategy that lost money is data; hiding it is how bad systems get funded.
- **Costs before conclusions.** A strategy whose edge disappears at 3 bps of spread has no edge.
- **Survivorship and look-ahead**: use point-in-time universes where possible; state the compromise when not.
- **Reproducibility**: same `code_ref` + same `data_snapshot` + same costs must reproduce the numbers, or the manifest is decorative.

## 5. What the agent must do at the boundary

1. Check provenance and gates **before** calling any model.
2. Never fabricate or interpolate a missing value into a reported result; report the gap.
3. Never cite a simulated feed, a test fixture, or a stale cache as real market data.
4. When a check fails, escalate with the failing artifact — not with a summary of it.
5. Finish with: `status (done|blocked|failed)`, evidence links, artifact/run IDs, checks passed/failed, remaining work, next action.

## 6. Scope boundary

This repository is research and paper-trading infrastructure. **No agent places live orders, changes broker
logins, moves money, or handles credentials.** Those actions require an explicit, scoped, human approval step
outside the agent loop — and a person accountable for the outcome.
