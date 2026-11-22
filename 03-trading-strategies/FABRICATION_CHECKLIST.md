# Fabrication checklist — ten checks for any claimed trade or backtest

Use this on any document, message or report that presents a **result**. It is the peer cross-check protocol in
executable form, and every check is cheap: minutes, no trust required.

The reference case is [`../REVIEWS/QWEN_PLUS_CHALLENGE_REVIEW.md`](../REVIEWS/QWEN_PLUS_CHALLENGE_REVIEW.md):
a document that reports a completed BTC trade at $61,200 on 2024-06-15, on a day BTC never traded below
$65,857. It fails checks 1, 2, 3, 4, 5, 6 and 10 — a full-house fabrication.

## 0. Static gates — four checks that need no data and no trust

Before any result is quoted, grep the code that produced it. All four cost seconds and each one has already
caught a real document in this collection (`REVIEWS/CLAUDE_OPUS_CHALLENGE_REVIEW.md` fails 1, 2, 3 and 4).

| # | Gate | What to look for | Failure means |
|---|---|---|---|
| S1 | **Causality** | the signal index is strictly less than the fill index (`sig.shift(1)`, `iloc[i-1]`), or a fill at `open[i]` from `close[i-1]` | same-bar look-ahead; numbers are fiction |
| S2 | **Exit ordering** | SL/TP compared against `low`/`high`, not `close`, and the stop booked when both are touched | optimistic bias |
| S3 | **Annualisation** | `sqrt(bars_per_year)` derived from the interval, not hard-coded 252 | Sharpe off by √(bars) |
| S4 | **Trials** | every sweep counts and reports the number of variants evaluated | selection effect; the "best" is the maximum of a search |
| S5 | **Schedule** | cron expressions are UTC and are described as UTC; a "9 AM" comment next to `0 9 * * *` is a bug | the job runs at the wrong time, silently |
| S6 | **Landing** | the workflow declares `permissions: contents: write` and its commit step verifiably lands (check for the artifact after a run) | green run, nothing written — the failure that looks like success |

## 1. Does the timestamp precede the question?

A document dated before the brief it answers cannot contain an execution. Check the file date, the prompt date,
and the price levels against *that* date's market.

```bash
git log -1 --format=%cI -- path/to/REALTIMECHALLENGE_*.md
```

## 2. Can the price be verified at that minute?

Every claimed fill needs a venue, a symbol and a timestamp fine enough to look up. If you cannot reproduce the
price from a public archive, the claim is unsupported.

```python
# Binance public klines — no key, works from a residential IP
start = int(datetime(2024,6,15,18,45,tzinfo=timezone.utc).timestamp()*1000)
end   = int(datetime(2024,6,15,19,30,tzinfo=timezone.utc).timestamp()*1000)
GET https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=5m&startTime={start}&endTime={end}
```

## 3. Was the fill inside the bar's range?

An entry, stop or target outside `[low, high]` of the bar it claims to have executed in did not happen.
For the Qwen case: entry 61,200 against a daily low of **65,857** — a 7.5% impossibility.

## 4. Do the exits contradict each other?

A position takes profit **or** stops out. If a document reports both for the same position, or reports "SL not
hit" after the TP already closed the trade, at least one row is invented.

## 5. Does the P&L reconcile?

`PnL = notional × (exit/entry − 1) − fees − slippage`. Recompute it. A +1.5% move on a stated notional that
yields a number that does not match is a sign the number was chosen, not calculated. Check the sign too: shorts
invert.

## 6. Is there an artifact?

A result must name something a third party can open: a JSON run file, a ledger line, a transcript, a run ID, a
commit. In this repository that is provenance category 4 — `03-trading-strategies/results/*.json`,
`03-trading-strategies/ledger/*.jsonl`, `01-screen-control-llm/transcripts/*.json`. No artifact, no result.

## 7. Could the claimed environment have reached the venue?

Some venues refuse datacentre traffic. This repository's own commit `7cfb713` records Bybit and OKX rejecting
GitHub Actions (Azure US) IPs, with a failover to Kraken/Coinbase/Binance. A CI-produced "live fill" from a
blocking venue needs an explanation.

## 8. Does the claim survive the resolution limit?

TP and SL inside the same bar cannot be ordered from OHLCV. If a document claims a precise sequence, ask for the
resolution (1m? tick?) and the rule used when both are touched. Correct answer: book the **stop**
(`03-*/HARNESS_CERTIFICATION.md` T3).

## 9. Were the thresholds declared before the test?

"Win rate ≥65%, Sharpe >1.2" is a target that can be reached by searching. If the thresholds appear only after
the results, they were fitted. See `02-*/DATA_EVIDENCE_RULES.md` §6 (trial counting, holdout, deflation).

## 10. Are placeholders presented as facts?

`github.com/user/trading-challenge-peer-review`, `YOUR_USER` in a path, `$API_KEY` in a result, "sample action"
instead of a run URL. A placeholder in the *evidence* section means there is no evidence.

---

## Fast triage: any two of these and you stop reading it as evidence

| Red flag | What it usually means |
|---|---|
| Round numbers that would be statistically lucky (`+1.5%` exactly, `+$918`) | the number was written, not booked |
| A result with no venue, no timestamp, no size | it is a scenario |
| P&L without fees, or fees mentioned but not subtracted | the author never ran it |
| "Simulated SL … not hit (profit secured)" | the author does not know how a position closes |
| Dated in the past, answering a present question | template reuse |
| CI "real-time" fills | the scheduler was never timed |

## What to do with a failure

1. Do not "correct" the document — mark it `rejected` with the check that failed.
2. Keep it. It is the most useful artifact in a research repo: a calibrated example of what to catch.
3. If the author is an agent, add the failing check to its brief before it runs again.
