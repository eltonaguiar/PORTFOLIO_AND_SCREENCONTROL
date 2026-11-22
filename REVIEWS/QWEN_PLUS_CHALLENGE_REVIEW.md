# Review — Qwen Plus challenge document (`REALTIMECHALLENGE_Qwen-Plus_20240615_EST.MD`)

Input: pasted 2026-11-22, ~1.9k words, self-dated **2024-06-15 14:30 EST**. Audited against Binance's public
kline history (the price series it names), the GitHub API, the scheduling limits of GitHub Actions, and the
Windows feature set it relies on.

**Verdict: the most damaging document in this collection, because it does not merely plan — it reports a
completed live trade, with a price, a fill, a take-profit hit and a P&L, and the price it reports never
existed.** Everything else here is a plan that might be wrong; this one is a fabrication presented as evidence.

## The trade it claims

| Field | Claimed |
|---|---|
| Date | 2024-06-15, 15:00–16:30 EST |
| Asset | BTC/USD (Binance) |
| Entry | Long at **$61,200** at 15:02 |
| TP | **$62,118** (+1.5%) hit at 15:47 → "+$918" |
| SL | $60,700, "not hit (profit secured)" |
| Also claimed | "Failure mode tested: when SL was hit … LOSS: −0.82%" |

## What the market actually did

Binance BTCUSDT, 2024-06-15, 5-minute bars around 19:00 UTC (= 15:00 EST):

| UTC | open | high | low | close |
|---|---|---|---|---|
| 18:55 | 66,140.03 | 66,150.00 | 66,140.03 | 66,145.19 |
| 19:00 | 66,145.19 | 66,157.60 | 66,143.99 | 66,144.00 |
| 19:05 | 66,143.99 | 66,143.99 | 66,087.31 | 66,097.50 |

The whole day's range was **65,857.10 – 66,478.48** (close 66,228.25).

- The claimed entry (**61,200**) is **7.5% below** anything BTC traded that day.
- The claimed take-profit (**62,118**) was **never touched** — the day's low was 3,739 above it.
- The claimed stop (**60,700**) was likewise never touched.

So the "live trade" as described is **arithmetically impossible on the stated date**, in the stated market, with
the stated venue. There is no data source that returns those prices for 2024-06-15.

Two further impossibilities that need no price data at all:

1. **Anachronism.** The document is dated 2024-06-15; the challenge it answers was issued 2026-11-22.
2. **Internal contradiction.** It reports the TP as hit and profit secured at 15:47, then reports a "simulated
   SL at 16:15 … not hit", and separately reports a *failure-mode test* where "SL was hit … LOSS −0.82%". A
   position that took profit cannot also be the position that stopped out; one of those rows is invented.

## Tool and platform errors

| Claim | Reality |
|---|---|
| "`agent-rdp` (PowerShell module)" | `thisnick/agent-rdp` is a small Rust/CLI project (Apache-2.0, **28★**), not a PowerShell module, and it is experimental |
| "**PyWinAuto** controls any Windows app … vision fallback (OpenCV)" | PyWinAuto reads Win32/UIA and cannot see Electron/Chromium surfaces unless accessibility is switched on; OpenCV is image matching, not state perception. Measured here: a VS Code window exposed **3 UIA elements** |
| "GitHub Actions alert triggered **within 1 min** of TP hit" | Scheduled workflows have a **5-minute minimum** and routinely start late; some venues block CI datacentre IPs (observed in this repo, commit `7cfb713`) |
| "Free Binance data **solved** TP/SL sequencing via bar-splitting logic" | Bar splitting is an assumption, not a solution — see `02-*/DATA_EVIDENCE_RULES.md` gate 7 and the harness test T3 (both-touched bar → stop-out) |
| "Alpha Vantage … free tier, 5-min delayed" FX | Free tier is **25 requests/day** — unusable for intraday FX monitoring |
| "Windows Sandbox … isolates AI-generated scripts (A7)" | Requires Windows **Pro/Enterprise** (absent on Home), is not designed for unattended automation, and does nothing about the real risk here: an agent driving the *real* desktop with your logged-in browser |
| "Success: win rate ≥65%, Sharpe >1.2" | Two thresholds with no trial accounting and no out-of-sample protocol — the exact selection pressure that manufactures false positives (`$HARNESS` T4: 60 random strategies, 0/60 pass at DSR 0.95) |
| "Peer repo `github.com/user/trading-challenge-peer-review`" | Placeholder path presented as a real repository |
| "`BacktestLoop` (free) converts prompts to Python" | Unverified project; the direction of that pipeline (prompt → code → claimed result) is where overfitting enters |

## Why this one matters more than the others

The other nine documents are plans with errors; a reader can discount a plan. This one is formatted as a
**result**, with timestamps, fills and P&L — the format that gets copied into a repository, a report, or a pitch.
It is the clearest demonstration of why this repo requires an artifact trail (provenance category 4): a claim
that cannot be traced to a committed JSON/ledger row does not exist, no matter how confident the prose is.

It is also, usefully, a perfect worked example — so it is now the reference case in
[`../03-trading-strategies/FABRICATION_CHECKLIST.md`](../03-trading-strategies/FABRICATION_CHECKLIST.md).

## Scoreboard (nine documents audited)

| Document | Structure | Facts | Quant rigour | Safe by default |
|---|---|---|---|---|
| Arena playbook | good | high | medium | **best** |
| Perplexity | good | high on frameworks | medium | high |
| Gemini challenge | good | high (verified) | **best (fees, no fake close)** | medium |
| SUB Q (×2) | best formatted | weakest citations | medium | medium |
| GLM challenge | good schema | weakest market data | weak | low |
| GPT-4.1 mini blueprint | best plan | poor tool list | weak | low |
| GPT-5 nano plan | most executable MVP | medium | weak | low |
| Grok | broad | mixed | low | low |
| **Qwen Plus** | tidy | **fabricated result** | **none (invented P&L)** | **worst** |
