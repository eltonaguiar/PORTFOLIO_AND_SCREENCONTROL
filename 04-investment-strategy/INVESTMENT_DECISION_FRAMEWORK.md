# Investment decision framework — what is actually worth money (2026-11-23)

Written after 9 asset classes, 67 tested cells, 0 proven, and a measured cost wall. This is the honest
answer to "what should we invest in to beat the market", plus how a risk-profile portfolio would be
built and how the agents' pretend-money book should be run.

## 1. The decision procedure (apply in this order, stop at the first failure)

| Gate | Question | Kills |
|---|---|---|
| **G1 Cost** | Does gross edge exceed **2× measured round-trip cost**, on our own fills? | ~everything intraday |
| **G2 Horizon** | Does it survive at **≥1 day** holding (ladder: annual cost drag = 365 / holding_days × round_trip_bps, so the 15m→1D cost ratio is exactly 96×, venue-independent)? | scalping, HFT, most intraday |
| **G3 Selection** | Is the trial count known, and does it pass **deflated Sharpe** at that N? | the 115-algorithm hub, every "best strategy" list |
| **G4 Capital** | Is the return measured on **committed capital including cash collateral** vs a 4.3% T-bill? | most market-neutral long/short claims |
| **G5 Provenance** | Can the result be reproduced from a **recorded pick**, written before the outcome? | H-119-style backfills |

Nothing in this estate currently passes G1 on a liquid market at retail cost. That is the finding, and
it is why the honest allocation today is **floor first, risk premia second, strategies zero**.

## 2. What is worth money, by asset class

| Class | Our measured state | Verdict for real money |
|---|---|---|
| **Cash / T-bills / HISA** | 4.3% risk-free, no cost, no model | **The benchmark. Fund this first.** |
| **Broad index equity (low-MER ETF)** | Not a strategy, a beta purchase; ~market return minus ~5 bp MER | **The only dependable return stream here.** Hold it, don't trade it |
| **Bonds (govt, short duration)** | Carry measured **negative** after fees (42.64 bp round trip, 94% fees); T-bill beats it at VIP0 | Only as duration hedge, not as carry |
| **ETFs (sector/factor rotation)** | Breakout 4.7 bp gross vs 5.1 bp cost; momentum/rotation fail G1 | No edge found; use as cheap beta instead |
| **Crypto (spot/perp)** | Gross ~2.5–12.8 bp vs 12–20 bp cost; carry net **−11 bp/tick** across 63 ticks | **Do not trade directionally.** Costs eat it |
| **Forex** | Live top-of-book **8.0 bp** full spread; carry −3.70% CAGR with differentials | Structural loser for retail flow |
| **Commodities** | Selection alpha **−3.57%** (CI −5.51, −2.05), n=40 | Negative selection; avoid |
| **Mutual funds** | Fees dominate (front/back load + $9.95 + MER); NAV stale once daily | Only **no-load index** funds, held long |
| **Options** | Not yet measured here; premium selling is short-vol beta | Unexplored — see TODO O-1 |
| **Prediction markets** | Not yet measured; binary settlement, clean calibration | **Best test harness we have** — see §4 |

**The uncomfortable summary:** the things that reliably make money for a retail-sized account are
*floor + beta + behaviour* (not selling in a drawdown, low fees, long horizon). Every "strategy" this
programme has measured has failed net of costs.

## 2a. UPDATE 2026-11-23 — value (HML) is now DEAD too, measured

The one family that was "untested and plausibly alive" has since been measured and refuted:

| | Result |
|---|---|
| Universe | 186 names, **44 monthly rebalances** |
| Gross | **+0.11%/yr** |
| Net of measured cost | **+0.02%/yr** |
| Hurdle | 4.32% T-bill |

It did not die of cost — it died because **the gross premium is absent**. That closes the last open
research line, and it means the framework's earlier "run the value test as the single research bet" is
superseded by the entry below.

Also measured the same day: **EQUITY round-trip cost is 1–5 bp** (191 names, 238,810 daily + 356,271
minute bars, participation 0.008% of ADV). The repo had been carrying two constants 5× apart (5.0 vs
25.0 bp) and the 25 bp one overstated cost by ~5×; the old Questrade model's 175 bp per trade is simply
wrong (buy/sell $0 commission, ECN $0 on smart-routed orders, FX 1.5% and only on conversion).

## 2b. THE ONE BET LEFT, AND HOW TO PROVE IT

The binding constraint is not signal discovery but **multiple-testing debt**: 146 pre-registered
hypotheses, 0 PROVEN, and **0/55 strategies survive deflation at SR\* 1.014 / σ_SR 0.439**. Every extra
backtest raises the bar for the next one. So the only rational move is to stop mining history and prove
**one** rule forward, where the trial count stays at 1.

**ETF trend / tactical allocation**
- Universe: the 24 liquid ETFs already held (SPY QQQ IWM EFA EEM TLT IEF LQD HYG GLD XLE XLF XLK XLV …)
- Signal: 12-month absolute momentum per ETF, monthly rebalance, hold top-k else cash
- Costs: **measured 1–2 bp + $0 commission**, not assumed
- No short leg → zero borrow (the blocker that killed HML); no FX if CAD-listed equivalents are used
- **Frozen kill rule**: annualised net ≤ 4.32% **or** the one-sided 95% upper bound ≤ 4.32%
- **Proof = forward clock only.** Start it, publish monthly, do not backtest it again

If trend on a diversified ETF basket cannot beat 4.32% net of 1–2 bp, then nothing runnable at this size
can — and holding cash is itself a real, provable answer.

## 2c. Cross-check of this framework by the model panel (2026-11-23)

Three models were asked, with no shared numbers, to name the claim most likely to be **wrong**, what is
missing, and the one addition that would most improve the framework.

| Model | Most-likely-wrong claim | Proposed addition | Verdict |
|---|---|---|---|
| `qwen3:8b` (local) | (2) "every class fails net of cost" — too absolute | "integrate a risk-adjusted framework (Sharpe)" | **Noise.** Sharpe/Sortino/MDD/DSR are already the reporting set; the model didn't read them |
| `ULTRA_FREE_CLOUD_LARGE` | (2) same claim | stress testing + behavioural analysis | **Fair but vague** — stress testing is legitimate, "market sentiment" is not a measurable gate |
| `ULTRA_FREE_OPENROUTER` | **(4) ETF 12-month momentum** | vol-scaled sizing that cuts to zero once trailing 21-day realised vol > 1.5%/mo | **Specific and worth recording** — but see the trap below |

The third critique has a real mechanism behind it: the 4.32% kill rule is **unconditional**, and it does
not distinguish "trend failed" from "trend had nothing to work with" (2017–2020 style low-vol drift where
absolute momentum repeatedly whipsaws).

**The trap:** implementing that suggestion adds a parameter — a vol threshold — which is **+1 trial**,
and multiple-testing debt is precisely the binding constraint (0/55 survive deflation). A filter chosen
because a model suggested it is still a filter chosen by looking at the data.

**Resolution adopted here:** keep the frozen rule as ONE trial, and treat volatility regimes as a
**reported diagnostic**, not a sizing input. That means the ETF test publishes a table of
`vol_regime → net return` so a regime dependence is *visible*, without letting the regime become a knob
we tuned. If the diagnostic shows the rule only works in one regime, that is a finding to report — not a
licence to add a filter and quietly reset the trial count.

**Meta-lesson worth keeping:** a model's advice to "add a filter" is advice to increase multiplicity. When
the constraint is trial count, the correct response to almost every suggestion is *report it, don't wire
it*.

## 3. Three risk-profile portfolios (concrete, cheap, no exotic access)

These are **templates, not advice**. All instruments should be the cheapest available in the account's
currency; for a Canadian account that means CDR/ETF equivalents where the FX spread is otherwise 1.75%.

### Stable / low-risk — target ≈4–5% nominal, drawdown <10%
| Sleeve | Weight | Instrument |
|---|---|---|
| Cash & T-bills / HISA | 55% | 1–12 month bills, or HISA at the best posted rate |
| Short-duration govt bonds | 25% | 1–5y aggregate, MER <0.15% |
| Broad equity | 20% | Global index ETF, MER <0.10% |

Rationale: at 4.3% risk-free, a stable portfolio's job is **not to lose**, and 20% equity is the
smallest allocation that still beats inflation over a decade.

### Moderate — target ≈6–7%, drawdown 15–25%
| Sleeve | Weight |
|---|---|
| Cash & bills | 20% |
| Bonds (1–5y) | 25% |
| Broad equity (global index) | 50% |
| Diversifier (commodity/gold or trend) | 5% |

Rationale: this is close to the 60/40 shape, and note the measured caveat — the P03-style
**book-level trend overlay** is the only combination in this programme that improved risk-adjusted
return *and* cut drawdown 77%, and it only worked because both legs had positive standalone expectancy.

### Aggressive — target ≈8–10% with real drawdown, >35%
| Sleeve | Weight |
|---|---|
| Broad equity (global, incl. EM) | 75% |
| Small-cap value tilt | 15% |
| Crypto | 5% (sized to be *lost*, not traded) |
| Cash buffer | 5% |

Rationale: aggression is achieved with **more beta**, not with more trading. Every measured
cost-bearing strategy in this estate destroyed value; leverage or option overlays would compound that.

**The one non-obvious rule across all three:** rebalance on **bands** (e.g. ±5% absolute), not on a
calendar, and never on a signal from this programme until something passes G1–G5.

## 4. Should we look at Polymarket / Kalshi?

**Yes — but as a measurement harness, not as an investment.** Reasoning:

- **They are the cleanest calibration test available.** Binary, unambiguous settlement, no cost-model
  ambiguity, and a live market price that *is* a probability. That makes them the ideal place to ask
  the only question that matters: *does our model beat the market's implied probability?*
- **The edge test is trivial and brutal:** log every forecast with its market-implied probability before
  resolution, then compute Brier score and log-loss against the market. Beating the market needs
  `ΔBrier > 0` with a confidence interval, out of sample. No cost model to argue about.
- **Economics differ from trading.** Kalshi is CFTC-regulated (US, fiat rails); Polymarket is
  crypto-collateralised. Both charge fees/spread on entry, and **resolution risk** (rules
  interpretation, oracle disputes) is a real loss mode that has no analogue in equity trading.
- **Liquidity is thin outside headline markets**, so a profitable signal may not scale past a few
  thousand dollars. Treat any edge as capacity-limited until measured.
- **Where it genuinely helps even without edge:** hedging a real exposure (e.g. buying "recession" or
  "rate cut" contracts as a cheap tail hedge), and as a **cheap forward test** for hypotheses that would
  need years of equity data to validate.

**Verdict:** open a small, capped experimental allocation (say 1–2% of the aggressive sleeve) *only* after
the calibration test above shows `ΔBrier > 0`. Do not trade them for excitement; they are a measuring
instrument that happens to pay.

## 5. The pretend-money tracker (what the agents should maintain)

The failure mode to avoid is a leaderboard of hindsight. Design:

1. **Declare before resolution.** Each agent (Copilot, Zoo Code, Kilo, Antigravity swarm, and each AI
   harvest model) writes a pick row *before* the outcome: `ts`, `agent`, `asset_class`, `tier`
   (stable/moderate/aggressive), `instrument`, `direction`, `entry_ref`, `horizon`, `thesis` (≤1 line),
   `kill_rule`, `data_hash`. The row is committed and gets a git hash — that hash is the proof it
   predates the outcome.
2. **One book per tier, not per agent.** Score agents *within* a tier so a cowboy taking 40% vol doesn't
   "win" the aggressive book by luck.
3. **Mark to market weekly**, using the same price source for everyone, with a flat day = 0.0% (never a
   missing observation). Report: n, mean bp per pick, hit rate, max drawdown, and **the 95% interval**.
4. **Deflate by declared trials.** An agent that makes 200 picks must clear a higher bar than one that
   makes 20. Publish the trial count next to the score, always.
5. **Kill rule enforcement.** A pick that hits its kill rule is closed as a loss even if it later
   recovers. Otherwise the book teaches the wrong lesson.
6. **No editing.** A revision is a new row referencing the old one (`supersedes`), never an edit —
   the same rule that caught H-119.

Minimum honest sample before any agent is called "good": **≥30 resolved picks per tier**, and even then
report it as a candidate, not a result.

## 6. What I would actually decide today

1. **Fund the floor** (bills/HISA) to the level of the stable sleeve. That is the only certain return.
2. **Buy beta cheaply** for the moderate/aggressive sleeves — index ETFs, low MER, band rebalancing.
3. **Zero to the strategy book**, until one candidate passes G1–G5 with ≥30 forward picks.
4. **Run the value (HML) test** as the single research bet, because it is the only family not yet
   knocked down and it is monthly (the horizon that survives cost).
5. **Run the prediction-market calibration test** because it is the cheapest possible forward test of
   whether any model here has genuine foresight.

Nothing in this document is investment advice, and every number in it came from a measurement or is
labelled as an assumption.
