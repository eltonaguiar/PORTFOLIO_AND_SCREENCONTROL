# Review — two challenge prototypes: GLM-5.3-Flash vs Gemini 3.1 Pro

Inputs: [`inputs/REALTIMECHALLENGE_GLM-5.3-Flash.md`](inputs/REALTIMECHALLENGE_GLM-5.3-Flash.md) (111 lines) and
[`inputs/REALTIMECHALLENGE_Gemini-3.1-Pro.md`](inputs/REALTIMECHALLENGE_Gemini-3.1-Pro.md) (254 lines), both
supplied 2026-11-22. Market data re-checked at review time against CoinGecko and Binance public endpoints; code
claims checked against the NautilusTrader source clone already in this repo; execution claims checked against
this repository's own peer commits.

**Verdict: Gemini's is the better document and the honest one (it refuses to fake a closed trade and finds a
real quantitative problem). GLM's is the better *schema* but ships a trade whose thesis contradicts the data it
cites, and repeats the intrabar-sequencing myth that this repo can now refute from source.**

## Market data, re-verified (2026-11-22 ≈ 09:30 UTC)

| Series | Claimed by | Measured now | Verdict |
|---|---|---|---|
| BTC/USD level | GLM ~$59,000–60,300 · Gemini $59,623 at 09:17Z | CoinGecko **59,951** · Binance **59,942.88** | ✅ both plausible |
| BTC 24h change | GLM "down ~2–4%" | Binance **+3.35%** · CoinGecko +3.55% | ❌ **wrong direction** |
| BTC 7d change | GLM "~−8%" | 8-day CoinGecko: 67,363 → 59,951 = **−11.0%** | ❌ understated |
| BTC 24h range | GLM "$55,150–62,150" | Binance **57,837–60,996** (hourly OHLC 57,695–60,799) | ❌ ~40% too wide |
| ETH/USD level | Gemini $1,681.50 at 09:17Z | CoinGecko **1,690.27** · Binance 1,688.99 (24h 1,635.00–1,716.58) | ✅ consistent |
| SOL/USD | Gemini $65.03 low / $70.94 high / ~$69–70 live | Binance **67.87–71.12**, last **69.92** | ✅ consistent |

So Gemini's snapshot holds up; GLM's price *level* is right but its direction, magnitude and range are not.

---

# GLM-5.3-Flash

## What it gets right

- **Strategy schema** is the single most useful artifact in either document: *entry rule, TP, SL, position size,
  symbol, timeframe, required feeds* — "what makes GitHub Actions monitoring possible without re-reading the
  code". Adopt it; it is exactly the missing contract between research and automation.
- **Falsification note per round** ("what would falsify this") — good discipline, and cheap.
- **Paper-only** with an explicit "report why it failed (chop, SL, spread, or signal failure)" rule.
- **Free-data honesty**: labels proxy ETFs and continuous-contract approximations as approximations.
- **RustDesk sees only pixels** — correct, and it routes the GUI-only case to a vision path.

## What is wrong

### 1. The trade thesis contradicts the data cited beside it

The note opens a **short** at ~$59,200 on "momentum continuation down (7-day downtrend)", citing a 24h move of
−2 to −4%. Measured: **+3.35% over 24h**. It is also already **$731 (1.2%) above the stated entry** at the moment
of writing, so the "entry" is stale, not live.

### 2. The risk placement is close to a coin flip — and the document doesn't say so

- Entry 59,200 · TP 57,900 (**−2.20%**) · SL 60,500 (**+2.20%**) — 1R.
- Stop distance: **530 (0.9%)**. The day's range: **3,159 (5.3%)**. The stop is **0.17× the daily range**.
- For a driftless walk, `P(SL first) = 0.9 / (0.9 + 2.2) ≈ 71%`. The trade is roughly 3:1 to be stopped out by
  structure alone, before any edge argument.
- The TP at 57,900 sits just above the 24h low (57,837): it needs a **fresh low** to pay.

A demo trade is allowed to be a coin flip — but the document calls it a feasible setup without stating the base
rate, which is the same error the challenge exists to eliminate.

### 3. "NautilusTrader/LEAN fixes the OHLC stop-vs-limit ambiguity" — false as stated

This repo has the v2 source. `crates/execution/src/matching_engine/mod.rs` synthesises trade ticks from a bar in
a **fixed order**:

```rust
// Determine high/low processing order.
// Default: O > H > L > C. With adaptive ordering, swap if low is closer to open.
let high_first = self.bar_high_first(bar);
```

So a bar-only backtest **replaces an unknown with a documented heuristic** (default high-first, optionally
swapped by proximity to the open). It does not recover the true sequence. Two runs with different
`bar_high_first` settings can disagree on whether your TP or your SL filled. Truth requires tick/L2, or an
explicitly pessimistic assumption. This repo's own peer harness already encodes the safe version —
`HARNESS_CERTIFICATION.md` test **T3: "both-touched bar resolves to the stop"**.

### 4. The "session registry re-prompts each AI session" design is the anti-pattern

Pinging every open session on a schedule and re-prompting it is exactly the timer-based `continue` injector that
turns a stall into a long loop (and burns quota — Copilot's 402 is on this machine). The replacement is
state-based: read the session's last output and the diff, classify the stop (done / stalled / looping / blocked /
quota), then either supply a **new fact** or stop. See `01-*/PC_AGENT_CONTROL_RESEARCH.md` §5 and
`01-*/TOOL_INTERFACE.md`.

### 5. Smaller issues

- "Proxy ETFs for futures/commodities/bonds" — a proxy is a different instrument: no roll yield, different
  collateral, different duration. Fine for triage, never for a verdict.
- "QSTrader/custom" for a multi-strategy crypto portfolio — QSTrader is schedule-driven equity/ETF; a custom
  engine is the real answer there.
- A shared **file lock prevents two agents** fighting over the mouse; it does not prevent *you* from using the
  machine, and it provides no isolation. Unattended GUI automation on the daily driver is the risk that remains.

---

# Gemini 3.1 Pro

## What it gets right (more than any other document in this repo)

- **It refuses to fake a closed trade.** "Single-turn statelessness … fabricating a close price would violate
  Rule #1" — the correct behaviour, stated explicitly, with the trade left OPEN for an external resolver.
- **The fee-trap finding is genuinely valuable and correctly computed.** On a 0.595% gross target, a 0.10%
  round-trip taker fee consumes **16.8%** of the gross and takes net R:R from 1.43:1 to **0.96:1**. Arithmetic
  checks out (net +$4.95 vs −$5.16 on $1,000). That single observation invalidates most retail scalping plans.
- **The five anti-hallucination rules** (no look-ahead, mandatory costs, purged walk-forward with OOS gates,
  free/local only, peer cross-check every 20 rounds) are the right shape, and "purged" is the right word.
- **The asset-class data matrix** is the most complete free-data map in any of these documents, and it names the
  caveats instead of hiding them (funding for perps, roll adjustment, NAV settlement, options-chain scarcity).
- **1-minute candle backfill** for TP/SL resolution is the right mechanism — it removes most single-bar
  ambiguity after the fact.
- **Prediction markets and funding-rate carry** as alpha classes are correct for a free-data stack; NautilusTrader
  already ships `polymarket`, `kalshi`, and `hyperliquid` adapters (verified in `crates/adapters`).

## What needs correcting

| Claim | Correction |
|---|---|
| "Scheduled cron **every 15m** … resolves live paper trades every 15m" | GitHub Actions scheduled workflows have a **5-minute minimum**, run **late under load** (10–30+ min is common), and **disable themselves after ~60 days of repository inactivity** on public repos. The 1-minute backfill makes the *resolution* correct; the *cron* is only a poller. Say "polled periodically, resolved retroactively from 1m candles". |
| Implied reliability of Actions as a market-data client | **This repo already proved otherwise**: commit `7cfb713` — *"cloud IPs are blocked by Bybit/OKX on GitHub runners… Bybit and OKX refuse US datacentre traffic, and GitHub Actions runs on Azure US"*. Any Actions-based monitor needs venue failover and must record which venue produced the price. |
| "1-minute candles … eliminating single-bar ambiguity" | Reduced, not eliminated: with a 0.4% stop, a violent 1-minute bar can still contain both TP and SL. Apply the pessimistic rule (stop-out wins) at the finest available resolution, as `HARNESS_CERTIFICATION.md` T3 does. |
| "Crypto taker 0.05%" | Binance spot standard is **0.10%** (10 bps); 5 bps assumes BNB discount/VIP tier. The fee trap you identified is **twice as bad** for a normal retail account — recompute at 10 bps and the net R:R goes negative. |
| "`Backtrader` is easiest for AI agents" | `mementum/backtrader` — GPL-3.0, **last push 2024-08-19**. Fine for reading, wrong for a 200-round build. Use LEAN or Nautilus for the realism stage. |
| "`consent_countdown_seconds = 0` in `~/.windows-mcp/config.toml`" | Unverified key. More importantly, disabling the consent countdown on a desktop-control server is a **risk**, not a feature — pair it with a loopback bind, a tool allowlist and an isolated account, or don't do it. |
| "OOS Sharpe > 1.0" gate; Phase 8 "portfolio Sharpe > 1.5" | The right *kind* of gate, but gates without trial accounting invite fitting-to-threshold. Count every variant evaluated, hold out a final period, and report **deflated** metrics (`02-*/DATA_EVIDENCE_RULES.md` §6; the peer harness T4 runs 60 random strategies at DSR ≥ 0.95 and expects **0/60** passes). The 1.5 target should be evaluated on the holdout only, never iterated against. |
| "Options: yfinance live chains + synthetic Black-Scholes" | Synthetic option backtests are model risk dressed as data. Label them `assumed`, never `observed`, and don't let an option result into the leaderboard without chain data. |

## Structural strengths worth copying into the shared harness

1. **Trade record with an explicit resolver** (time stop, TP, SL, and a named external process that closes it).
2. **Ledger schema** (`paper_ledger.json`) — pairs well with the JSONL event log in
   `02-*/PAPER_TRADING_AND_MONITORING.md`; use JSONL for events, JSON for current state.
3. **Peer cross-check protocol** (5 points: timestamp/price verification, fee audit, look-ahead/survivorship,
   reproducibility, consensus synthesis) — this is essentially what `01-*/FACTCHECK.md` does to model answers,
   applied to trading results. Adopt it as the round gate.

---

# Shared problems (both documents)

1. **200 rounds is a multiple-testing machine.** Neither counts trials, pre-registers hypotheses, or reserves a
   final holdout. Phase 6/7 of each ("AI-generated strategies", "port thousands of params") multiplies the
   search. Without §6 discipline, the winner of round N is a statement about the search, not the market.
2. **"No human approval" + unattended GUI automation + no isolation.** A shared file lock is not a security
   boundary. If the agent runs on the daily driver with the user's browser profile, one prompt injection on a
   web page is a code-execution path with your logins attached.
3. **Paper trading treated as proof.** Both plan to "validate" strategies on paper. Paper validates *plumbing*
   (fills, latency, data gaps), not edge. State it that way.
4. **Both use GitHub Actions as an intraday engine.** The repo's own failover commit shows the venue side of
   that problem; the platform side is scheduling. Use a local worker or a small VPS for anything intraday, and
   keep Actions for nightly batch.

# Where each should be edited before round 1

| GLM | Gemini |
|---|---|
| Replace the short thesis with one consistent with +3.4% 24h, or re-time it | Recompute the fee trap at 10 bps taker |
| Re-place TP/SL at ≥ 1× daily range, or size down to match | Rename the monitor "polled ~15 min, resolved from 1m candles" |
| Delete the "engines fix intrabar ordering" claim | Drop Backtrader from the build path |
| Replace the timed session registry with a state-based supervisor | Add trial-count + holdout to the OOS gate |
| Mark proxy ETFs as `assumed`, not data | Drop or harden `consent_countdown_seconds = 0` |

# Scoreboard (seven documents audited)

| Document | Structure | Facts | Quant rigour | Safe by default |
|---|---|---|---|---|
| Arena playbook | good | high | medium | **best** |
| Perplexity | good | high on frameworks | medium | high |
| **Gemini challenge** | good | **high (verified)** | **best in class (fees, no fake close)** | medium |
| SUB Q (×2) | best formatted | weakest citations | medium | medium |
| GLM challenge | good schema | **weakest market data** | weak (trade placement) | low |
| GPT-4.1 mini blueprint | best plan | poor tool list | weak (multiple testing) | low |
| Grok | broad | mixed | low | low |
