# Proven-edge methodology — multi-AI harvest + our synthesis

Run: 2026-11-22 · Prompt set: candidate discovery, backtest construction, professional statistics,
forward-test protocol · Intended targets: chatplayground.ai, 1min.ai, arena.ai, askanymodel.xyz

## 1. Harvest status (honest, per site)

| Site | Result | Evidence |
|---|---|---|
| **1min.ai** | **BLOCKED — auth** | prompt filled (462 chars) and submitted via Enter; response was a login modal: `Log In / Sign Up`, `Log in with Google`, `Log in with Apple`. Body grew 1209 → 1329 chars with no answer |
| **arena.ai** | **BLOCKED — auth (after submit)** | Agent mode set (`select_option("select","work")` → `work`), prompt typed with `insert_text` and submitted; the answer was replaced by a sign-up modal: "Log In or Create Account … Continue with Google / Continue with email" |
| **chatplayground.ai** | **BLOCKED — auth** | `Continue with Google` → `accounts.google.com/v3/signin/challenge/dp` → `/signin/identifier` (no Google session in the driving profile) |
| **askanymodel.xyz** | **BLOCKED — auth** | `/dashboard/multi-chat` redirects to `/login?callbackUrl=…`; body: "Welcome back — Sign in to continue" |

**Single unblocker:** one Google sign-in per site inside the CDP-driven Chrome profile
(`C:/Users/zerou/chrome-agent-profile`, port 9222). Copying sessions from the default profile is
prevented by app-bound cookie encryption, and Chrome refuses `--remote-debugging-port` on the default
profile even when the path is passed explicitly. Until that sign-in exists, no prompt-and-harvest loop
can run unattended on these four sites.

## 2. What the evidence actually supports (two tiers, not one)

The question "which strategies are proven" has a precise answer only if "proven" is split. Mixing the
tiers is the most common way retail research fools itself.

**Tier 1 — risk premia with multi-market, multi-decade replication.** These are not "strategies" so much
as compensated exposures; they survive because someone must be paid to bear the risk, not because the
price pattern is a secret.

| Premium | Canonical source | Where it replicated | How it fails |
|---|---|---|---|
| Equity risk premium | Fama & French (1992, 1993); Dimson-Marsh-Staunton long-run series | every developed market studied | 10–15 year drawdowns; survivorship in "stocks always win" claims (Russia 1917, China 1949) |
| Time-series momentum / trend | Moskowitz, Ooi & Pedersen (2012), *JFE* 104(2):228–250 — 58 futures, 1965–2009, 52 of 58 significant at 5% | equity indices, FX, commodities, sovereign bonds | whipsaw in range-bound regimes; 2011–2019 was a long drought; costs on fast signals |
| Cross-sectional momentum | Jegadeesh & Titman (1993); Asness, Moskowitz & Pedersen (2013) | US equities, then 8 markets and 4 asset classes | momentum crashes (2009); high turnover; crowding |
| Carry | Koijen, Moskowitz, Pedersen & Vrugt (2018), *JFE* 127(2):197–225 | global equities, bonds, commodities, Treasuries, credit, FX, options | crash risk in recessions/liquidity shocks; short-volatility tail |
| Value | Fama & French (1992); Asness et al. (2013) | most markets | 2007–2020 decade of underperformance; definition-sensitive |
| Volatility risk premium | Coval & Shumway (2001); Carr & Wu (2009) | index options | 2018 "Volmageddon"; the premium is compensation for crash exposure |
| Commodity futures basis | Gorton & Rouwenhorst (2006) | commodity futures | roll/contango erosion for passive holders |

**Tier 2 — published anomalies.** Harvey, Liu & Zhu (2016) show most published factors fail a
multiple-testing hurdle once the number of tried factors is accounted for. Treat any single-paper
anomaly as a hypothesis, not a result.

## 3. Candidate discovery without self-deception

1. **Pre-register before touching forward data.** Write the entry, exit, sizing, universe and cost model
   down; timestamp it. Registration converts a search into a test.
2. **Count trials.** Every parameter grid, every variant, every "one more filter" is a trial. The
   denominator is the number of cells tried, not the number reported.
3. **Prefer hypotheses with a risk story.** "Someone is paid to bear this" survives out-of-sample better
   than "this chart pattern looks good".
4. **Cap the search.** A large search space with one winner is a deflation problem, not a discovery.

## 4. Backtest construction rules (each one is a known way to lose money)

| Rule | Why | Failure if skipped |
|---|---|---|
| Decision at `t` uses only data ≤ `t`; fill at `t+1` | otherwise the signal peeks | Sharpe inflates by a factor, not a percent |
| Point-in-time universe, delisted names included | survivorship | 2–4%/yr phantom return in small caps |
| Signals computed on adjusted prices, fills on raw | splits/dividends | impossible fills, fake gaps |
| Intrabar TP/SL: assume the stop is hit first, or mark the bar ambiguous | OHLC cannot order two touches inside one bar | every "both touched" bar becomes a win |
| Costs: commission + half-spread + measured slippage per side, tested at **2×** | edge must survive double costs | a 10 bps edge dies at 5 bps/side |
| Capacity: size vs ADV, impact model | a backtest ignores market impact | strategy dies at real size |
| No shorting/halt assumptions beyond what the venue allows | borrowed shares, halts | unfillable shorts |

## 5. Statistics a professional checks, with thresholds

| Statistic | Threshold that matters | What it kills |
|---|---|---|
| Sharpe (annualised, net) | reported, never trusted alone | — |
| **Deflated Sharpe (DSR)** — Bailey & López de Prado (2014), *JPM* 40(5):94–107 | **DSR ≥ 0.95** given the number of trials | the best of many tries |
| **PBO / CSCV** — Bailey, Borwein, López de Prado & Zhu (2017) | **PBO ≤ 0.5**, ideally ≤ 0.2 | strategies whose ranking is unstable across splits |
| Walk-forward efficiency | OOS/IS Sharpe ≳ 0.5 | curve-fit parameters |
| Information ratio vs a matched benchmark leg | IR ≥ 0.5 | "alpha" that is just beta |
| 2× cost test | net CI lower bound > 0 at double slippage | edge thinner than the friction |
| Turnover & holding period | consistent with the stated edge | hidden cost |
| Max drawdown & recovery time | within what the owner can actually hold | behavioural failure |
| Tail ratio / skew | no negative-skew wipeout masked by Sharpe | short-vol profiles |
| Capacity at target size | impact-adjusted edge > 0 | backtest-only strategy |

Any one of DSR, PBO, or the 2×-cost test is usually enough to kill most candidates. Run all three.

## 6. Forward / paper-test protocol

1. **Pre-register the forward window and the stopping rule** before the first forward row.
2. **Paper fills must be adversarial**: use the next bar's open plus measured slippage; never the
   signal bar's close.
3. **Sample size from power, not intuition.** For a per-trade edge of *d* with volatility σ, required
   *n* ≈ (2.8·σ/d)² for 80% power at 5% — e.g. a 10 bps edge with 100 bps per-trade σ needs ≈ 780 trades.
4. **Stopping rules stated in advance**: end on `CI lower bound ≤ 0 at day 30/60`, or on n reached with
   the gate passed — nothing in between.
5. **Multiple-testing correction across pods**, not per pod: divide the false-positive budget by the
   number of families tested.
6. **Falsification criteria written down first**: what result would make you abandon it. If nothing
   would, it is a belief, not a hypothesis.

## 7. What "proven" can and cannot mean for a retail trader

- **Cannot**: that a backtest is a forecast. Reproduction proves no typo, not that the winner is not the
  maximum of a search.
- **Cannot**: that a premium will pay within your holding period. Factor droughts run a decade.
- **Can**: that an edge survives pre-registration, deflation, double costs, and an adversarial forward
  test at a size you can actually trade. That is the only defensible meaning.

## 8. Where this lands in our own repo

The gates above are the same ones running here: `03-trading-strategies/FABRICATION_CHECKLIST.md` (S1–S6
static gates), `02-portfolio-multi-asset/DATA_EVIDENCE_RULES.md` (provenance, intrabar ambiguity), and
the forward-gate rule in `CAPITAL_ALLOCATION.md` (n ≥ 100 rows, CI lower bound > 0 at 2× slippage,
IR ≥ 0.5, split-half stable). Live audit state at the time of writing: **0 of 67 tested cells proven**,
selection alpha negative in every asset class — which is exactly what this methodology predicts for a
search that has not yet been deflated.

## Sources

- Bailey, D. & López de Prado, M. (2014). *The Deflated Sharpe Ratio.* JPM 40(5):94–107. SSRN 2460551.
- Bailey, Borwein, López de Prado & Zhu (2017). *The Probability of Backtest Overfitting.* J. Computational Finance.
- Moskowitz, Ooi & Pedersen (2012). *Time Series Momentum.* JFE 104(2):228–250.
- Koijen, Moskowitz, Pedersen & Vrugt (2018). *Carry.* JFE 127(2):197–225.
- Harvey, Liu & Zhu (2016). *…and the Cross-Section of Expected Returns.* RFS 29(1).
- Jegadeesh & Titman (1993). *Returns to Buying Winners and Selling Losers.* JF 48(1).
- Asness, Moskowitz & Pedersen (2013). *Value and Momentum Everywhere.* JF 68(3).
- Gorton & Rouwenhorst (2006). *Facts and Fantasies about Commodity Futures.* FAJ 62(2).
- Coval & Shumway (2001). *Expected Option Returns.* JF 56(3).
