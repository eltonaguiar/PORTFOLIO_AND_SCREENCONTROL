# A Strategy Validation Protocol for a Retail Quant
### Version 1.0 · 22 Nov 2026 · Companion file: `validation_toolkit.py`

**Answer to the one-liner:** The **equity risk premium — the excess return of a diversified equity index over short-term government bills, roughly 4–6%/yr real across 120+ years of developed-market data, with a t-statistic near 4 on annual data and, uniquely among premia, out-of-sample support from markets and centuries that were never part of the original test — is the single strongest documented market risk premium** (with the caveat that "strongest" means strongest *documented*, not highest realised: momentum and value have produced larger peak returns on far thinner, more contested, and post-publication-decayed evidence; and a t≈4 over 100 years is still not the t>10 that a century of monthly compounding makes people imagine).

Everything below is written for one person, with one laptop, trading liquid US (and optionally Canadian) equities via a retail broker, with $50k–$5M of capital, using daily data. Where the answer changes for larger scale or different instruments, it is flagged.

---

## 0. The uncomfortable arithmetic you must accept before you start

A backtest is not evidence. It is a *maximum-likelihood summary of a search process*, and the search process is what generates the apparent edge. Three numbers define the game:

| Fact | Number | Consequence for you |
|---|---|---|
| Sampling error of a Sharpe ratio over *T* years ≈ `sqrt((1 + SR²/2)/T)` | SR 0.5 over 10 years → SE ≈ **0.33** | A "0.5 Sharpe, 10-year" backtest is statistically indistinguishable from zero |
| Years needed for t = SR·√T to reach 3.0 | SR 0.5 → **36 yrs**; SR 1.0 → **9 yrs**; SR 2.0 → **2.3 yrs** | Time-series data alone cannot prove a mediocre-Sharpe strategy |
| Published anomaly decay after discovery | **−26%** out-of-sample, **−58%** post-publication (McLean & Pontiff 2016); **65%** of 452 anomalies fail \|t\|>1.96, **82%** fail t>2.78 (Hou, Xue & Zhang 2020) | Assume a 30–60% haircut to any published premium *before* you test it |

The three legitimate ways to buy statistical power are therefore: **(a) breadth** (many independent instruments or bets per year), **(b) a strong prior** (a mechanism that must exist for structural reasons), and **(c) cost discipline** (an edge large relative to costs). Everything in this document is machinery for converting (a)–(c) into a defensible claim.

```
   IDEA  ──►  PRE-REGISTRATION  ──►  BACKTEST  ──►  [ GATES 1–17 ]
              (frozen spec,          (PIT, costs,        │
               N_trials,              purged CV)          │
               kill rules)                                ├── FAIL ──► kill, log trial
                                                          │
                                                          ▼  PASS
                                              PAPER PILOT (T1, 8–13 wks)
                                                          │ operational gate only
                                                          ▼
                                              MICRO-LIVE (T2, 6–12 mo, 5–10% size)
                                                          │ execution + no-falsifier gate
                                                          ▼
                                              SCALE-IN (T3) ──► kill criteria still armed
```

---

## 1. Phase 1 — Finding candidates without fooling yourself

### 1.1 Allowed hypothesis sources, ranked by informational value

Your prior probability that a hypothesis is real should be set *before* you look at data. Use this table as your prior.

| Tier | Source | Why the prior is non-zero | Expected post-publication decay | Example |
|---|---|---|---|---|
| **A** | **Structural/mechanical**: someone *must* trade for non-forecast reasons (index rebalancing, fund flows, forced selling, tax-loss selling, redemption, option hedging) | Price pressure must be absorbed by someone; if supply is inelastic, the absorber must be paid | 10–40% | Dec/Jan effect and index-add effects; post-2010 corporate-bond ETF NAV pressure; S&P 500 index inclusion drift; Russell reconstitution (much weaker since 2000s) |
| **A** | **Risk compensation**: you are paid for bearing a risk others cannot or will not hold (liquidity, crash, leverage constraint, career risk) | Must be paid in equilibrium; survives publication better than pure anomalies | 0–30% | Value, momentum (crash risk), BAB (leverage constraints), illiquidity premium, short-vol |
| **B** | **Behavioural with a limits-to-arbitrage story**: the mispricing persists because arbitrage is costly/risky | Must specify *why it hasn't been arbed out* — otherwise you're just mining | 40–70% | Post-earnings-announcement drift, accruals, analyst/estimate revisions, overreaction |
| **B** | **Cross-sectional logic transfer**: a documented effect in one market, tested in an untested market (Canada, small caps, sector-neutral variant, different horizon) | Publication bias is lower in untested corners | 20–50% | Momentum in Canadian energy mid-caps; value in TSX 60 with earnings-based definition |
| **C** | **Data-vendor or microstructure artifact** you can exploit legitimately (e.g., a survivorship-free dataset that others lack, true PIT fundamentals where the crowd uses restated) | Real but fragile; usually dies when others buy the same data | 50%+ | Hand-built PIT share-count series; short-interest with publication lag handled correctly |
| **D** | **Pure mining**: "I ran the grid and the best cell had a Sharpe of 1.8" | Prior = 1/N_trials. Assume zero until proven otherwise | ~100% | Any parameterised rule found by searching |

**Rule:** at least one sentence of *mechanism* per hypothesis, written before you test it. If you can't write the sentence, it's Tier D.

### 1.2 The pre-registration sheet (freeze this before touching data)

Fill every field. Store as `prereg/<hypothesis_id>.md`, timestamped, in a git repo whose history you cannot rewrite (or a signed commit).

| Field | What to write | Example |
|---|---|---|
| `hypothesis_id` | Immutable ID | `H-2026-014` |
| Claim | One falsifiable sentence | "Stocks with the largest 3-month increase in short interest (PIT, publication-lagged 10 business days) underperform by ≥3%/yr on a sector- and size-neutral basis" |
| Mechanism | Why the premium exists and who is on the other side | "Short sellers are informed; slow diffusion of short-interest data to retail; borrow costs cap arbitrage" |
| Universe | Exact tickers/screen + as-of rules | US common stocks, price >$5, ADV20 > $2M, ≥ 24 months of data, exchanges NYSE/NASDAQ/AMEX |
| Sample | **Fixed** in-sample window | 2005-01-01 → 2017-12-31 |
| Holdout | Sealed; not touched until Phase 3 passes | 2018-01-01 → 2025-12-31, then live |
| Signal definition | Formula, including every dirty detail (winsorisation, missing-data policy) | ΔSI = (SI_t − SI_{t−63})/shares_out, winsorise 1/99 pct, missing → 0 (neutral), sector-demeaned |
| Portfolio rule | Weights, neutrality, rebalance, buffer | Decile long-short, sector+beta neutral, equal-weight within decile, monthly rebalance, 20% turnover buffer |
| Execution | Signal date → trade date → price | Signal at close of t, trade at open of t+1 with 10 bp slippage |
| Cost model | Explicit, parameterised | 12 bp round trip + borrow; stressed 2× and 3× |
| Primary metric | **One** number that decides | Net-of-cost Sharpe, and its t-stat |
| Pass thresholds | Fixed in advance | net SR ≥ 0.60, t ≥ 3.0, DSR ≥ 0.95, PBO ≤ 0.20 |
| **Max trials** | Budget for this hypothesis family | **≤ 40 configurations** |
| Kill criteria | Pre-committed | See §5.4 |
| Date/shape of author | signature | — |

Anything you change after freezing is not an edit — it's a **new hypothesis with a new ID and a new trial count**. Log the old one as rejected.

### 1.3 Trial accounting: the number that kills most strategies

Every specification you run counts as a trial: universe variant, winsorisation level, lookback, holding period, weighting scheme, neutralisation choice, momentum lookback — all of it. `N_trials` is the honest count of *everything you computed a Sharpe for*, including the ones you didn't like.

Two adjustments:

1. **Deflate for correlation.** Forty variations of the same signal are not forty independent tests. Compute the effective number via the participation ratio of the eigenvalue spectrum of the trial-returns correlation matrix: `N_eff = (Σλ)² / Σλ²`. A 100-config grid built from three latent drivers gives `N_eff ≈ 1.4`; a genuinely independent grid of 100 gives `N_eff ≈ 72`. Use `N_eff` in the Deflated Sharpe Ratio.
2. **Report the ratio.** Publish `N_trials` and `N_eff` next to your Sharpe. A Sharpe of 1.2 found after 400 trials is not evidence; a Sharpe of 0.8 found after 5 pre-registered trials is.

**Trial ledger** (CSV, append-only, one row per Sharpe you ever computed) — template at `trial_ledger_template.csv`:

```
trial_id,date_utc,hypothesis_id,prereg_id,universe,sample_start,sample_end,
signal_family,params_json,rebalance,weighting,cost_bps,gross_sr,net_sr,t_stat,
n_eff,decision,reject_reason,git_commit
```

Your `N_trials` is `len(ledger)` — not the number you remember. If you can't produce the ledger, assume `N_trials = 1000` and that your t-stat threshold is ~4.0.

### 1.4 The research firewall

- **Two data environments.** A *research vault* (full history, you may look freely) and a *holdout vault* (the last 20–30% of time, or a set of entire markets/countries you own but never open). Physically separate directories + a checksum you record in the pre-reg. Opening the holdout is a logged, deliberate act.
- **Prefer cross-market holdouts** (e.g., develop on US, validate on Canada/UK) to time-split holdouts — more independent information per observation, and immune to the "the world changed after my in-sample ended" objection.
- **Research budget:** at most *K* pre-registered hypotheses per month (K = 2–4). Not because more curiosity is bad, but because `N_trials` is the denominator of your evidence.
- **Never** tune on the holdout, even "just to check it works."

---

## 2. Phase 2 — Backtest construction rules

### 2.1 Point-in-time (PIT) data requirements

| Data type | PIT requirement | Common failure | Audit test |
|---|---|---|---|
| Fundamental accounting items | Value as *first reported*, keyed on **filing date**, not period end | Compustat/Sharadar restated values; `datadate` used as availability date | For 100 random firm-quarters, the value your backtest used must equal the value in the original 10-Q as of `filing date` (+1 day) |
| Universe/membership | Membership history, not today's list | Using current S&P 500 or current screener output | Count delisted names present in your panel: should be ≥ 5%/yr of the universe |
| Prices | Split/dividend adjusted **as of the day you trade**, i.e., unadjusted price × adjustment factor known then | Using today's fully-adjusted series to compute the *level* of price filters (e.g., "$5 minimum") | Recompute the $5 filter on raw prices; compare names selected |
| Shares outstanding / market cap | PIT share count (filed), not vendor-backfilled | Market cap computed with current share count → massive look-ahead in buybacks/issuance | Correlate your size deciles with a known PIT size series |
| Delisting returns | Include them | Dropping dead tickers | Mean delisting return in your panel should be ≈ −30% to −100% for performance-related delistings |
| Index/ETF constituent lists | Historical, dated | Current holdings files | Constituent count over time must vary |
| Analyst estimates, short interest, fund holdings | Respect the publication lag (short interest: ~8–10 business days; 13F: 45 days; holdings: 30–60 days) | Using as-of-date values on the as-of date | Shift every lagging series by its documented lag; re-run |
| Corporate-action-adjusted returns | **Total return** series for P&L; raw prices for filter/level logic | Using price return in a strategy that holds dividend payers | Compare your total return vs a benchmark total return over 10 yrs: difference should be < 5 bp |

**Verdict rule:** if you cannot certify ≥ 99% of universe-months as PIT-valid with delisting returns present, stop. You are not measuring a strategy; you are measuring data.

### 2.2 Survivorship and delisting

Handling rules, in order of importance:

1. Include **all** securities that existed in the window, including those later delisted, merged, or went to zero.
2. Delisting return: use the actual CRSP-style delisting return where available. If not available, apply the conservative convention: **−100%** for bankruptcy/liquidation, **−30%** for "dropped for cause"/unknown, **0** for mergers (the merger consideration is a real cash/stock exit).
3. Do **not** let a delisted name silently carry its last price forward — that is a hidden +∞ return for losers and a hidden −∞ for winners.
4. OTC/pink-sheet history matters: names that fell from NASDAQ to OTC often keep trading. Dropping the OTC period is survivorship bias with extra steps.

**Quantify it:** run the backtest twice, once with delisted names and once with them excluded (the naive dataset). `ΔSR = SR_full − SR_naive` should be **< 0.10**; if it is 0.3+, your edge is substantially a survivorship artifact.

### 2.3 The twelve look-ahead traps (checklist)

| # | Trap | Test that catches it |
|---|---|---|
| 1 | Signal computed with `t`'s close, executed at `t`'s close | Shift execution to t+1 open; SR must not halve |
| 2 | Using `close_t` from a *restated* dataset where the value changed later | Compare snapshot datasets at two vendor vintages |
| 3 | Restated fundamentals / backfilled Compustat | Spot-check 100 filings vs EDGAR |
| 4 | Universe built from a current screener (survivor + look-ahead) | Rebuild from historical membership |
| 5 | Sector/industry classification as-of today applied historically | Use a classification vintage; check reclassification of e.g. payment processors (Tech→Financials) |
| 6 | Index inclusion known before announcement | Use announcement date, not effective date |
| 7 | Sample-wide normalisation (z-scoring the whole panel incl. future) | Compute all normalisation expanding-window/rolling |
| 8 | Feature engineering on the full panel then splitting (scaling, PCA, imputation) | Fit transforms inside each CV fold only |
| 9 | Overlapping labels / non-purged CV (train and test share days) | Purged K-fold with embargo ≥ label horizon |
| 10 | Liquidity filter using future ADV | Rolling 20-day ADV up to t only |
| 11 | Bankruptcy/exchange delisting known in advance (e.g., "exclude names that went to zero") | Only exclude on information available at t |
| 12 | Implicit "peeking" via many specs and keeping the survivor | Trial ledger + DSR |

### 2.4 Corporate actions

| Action | Correct handling | Failure mode if wrong |
|---|---|---|
| Split / reverse split | Adjust *prices and share counts* consistently; P&L is invariant | Reverse splits (−90% price) trigger false "dip" signals in unadjusted data |
| Cash dividend | Use total-return series for P&L; ex-date price drop is not a return | Ex-div drops look like 1–2% losses; creates phantom short profits for dividend payers |
| Special dividend / return of capital | Treat as total return, not as price change | Large specials generate phantom alpha |
| Merger (cash) | Position exits at deal terms on the closing date; reinvest proceeds | Holding the acquirer's last price forever = hidden return |
| Merger (stock) | Convert to acquirer shares at the exchange ratio; recompute weights | Silent unintended concentration |
| Spin-off | Receive child shares, then treat as a forced sale at first tradable price (or hold with an explicit rule) | Spin-offs show up as free money in unadjusted data |
| Rights issue / tender | Model the dilution (−) and the subscription (+); do not treat as a price drop | Phantom short profits |
| Ticker change / re-IPO of the same CUSIP | Map by **permanent identifier (PERMNO/ISIN/CUSIP+date)**, not ticker | Two entities merged into one return series |

**Rule:** you trade on `permno`-like identity, not on ticker. Any panel keyed on ticker is broken.

### 2.5 Execution and cost model

**Execution assumptions that are defensible for retail:**

| Choice | Defensible default | Unacceptable |
|---|---|---|
| Signal → trade lag | Signal at close t, trade at **open t+1** (or VWAP t+1) | Signal and trade both at close t |
| Price | Open, or the day's VWAP with a 0.3–0.5 × daily-range penalty | The day's low for buys / high for sells |
| Fill assumption | Full fill at price + slippage; **cap participation at 1–5% of ADV** | Infinite liquidity |
| Shorting | Assume 30–50% of shorts unavailable (hard-to-borrow); apply borrow fee | Assume unlimited borrow at 0% |
| T+1 settlement | Cash available next day; buying power via margin | Free intraday recycling of unsettled cash |

**Cost formula (per side, in bp of notional):**

```
cost_bp = commission_bp + 0.5 × spread_bp + impact_bp + borrow/financing
impact_bp ≈ Y × σ_daily_bp × sqrt(Q / ADV),   Y ∈ [0.3, 0.5]
```

**Parameter table (US equities, 2025–26 retail reality):**

| Liquidity bucket | Median full spread | Commission (IBKR-style) | Round-trip all-in assumption | Stress 2× |
|---|---|---|---|---|
| Mega/large cap, ADV > $500M | 1–3 bp | $0.0035/sh, min $0.35 | **8 bp** | 16 bp |
| Large cap, ADV $50–500M | 3–8 bp | same | **12 bp** | 24 bp |
| Mid cap, ADV $5–50M | 8–20 bp | same | **25 bp** | 50 bp |
| Small cap, ADV $1–5M | 20–50 bp | same | **60 bp** | 120 bp |
| Micro, ADV < $1M | 50–200 bp | min ticket dominates | **150 bp** | 300 bp |
| Short leg add-on | borrow | GC 0.25–0.5%; HTB 5–30%; squeeze 50%+ | + annual % of short notional | 2× borrow |

Sanity check on commissions: at $0.0035/share and a $30 stock, that is **11.7 bp per side** — retail commission is *the* binding cost for small accounts and it scales with price, not notional. Add the minimum-ticket effect: a $1 min with a 100-share order of a $30 stock is 3.3 bp, but a 20-share order is 16 bp.

**Two mandatory variants of every backtest:** `net(1×)` and `net(2×)`. Report both. A strategy that only clears costs at 1× is a strategy that dies on the first bad month.

### 2.6 Portfolio accounting details people get wrong

- **Turnover:** annual turnover = `mean(Σ|Δw|) × periods/yr`. Report it in the same breath as Sharpe; a 0.9 Sharpe at 900% turnover is a cost-model bet, not an alpha bet.
- **Cash and financing:** long-short at 2× gross needs margin; apply broker margin rate (currently ~5–6.5% for retail) to the debit balance, and rebates to short proceeds (~0.5–1% below the rate).
- **Borrow:** short-side return must be net of borrow, and the borrow must be *time-varying* (HTB fees spike before squeezes).
- **Weight drift:** rebalance to target weights; don't silently assume continuous rebalancing (free turnover).
- **Dollar neutrality vs beta neutrality:** dollar-neutral long-short in a high-beta long book is a long-beta strategy. Report the realised market beta of the P&L and its regression alpha.

### 2.7 Leakage audit — five mechanical tests you run on every backtest

| Test | Procedure | Expected result if clean |
|---|---|---|
| **Timestamp audit** | Assert `max(feature_timestamp) < execution_timestamp` for every row; log violations | Zero violations |
| **Time-shuffle (placebo)** | Permute returns *in time* (destroy signal-return alignment), re-run whole pipeline | SR distribution centred on 0, 95th pct ≈ 0.4 for 10y |
| **Universe placebo** | Run the identical pipeline on a universe where the effect cannot exist (synthetic random-walk tickers, or a market with no such data) | SR ≈ 0 |
| **Progressive rebuild** | Recompute each feature from raw data with an expanding window; diff against production feature | Max abs diff = 0 |
| **Holdout seal test** | Attempt to load the sealed window; assert exception raised in production code path | Raises |

If a backtest fails the placebo and the pipeline still produces SR > 1, the bug is in the pipeline. Fix it; don't celebrate.

### 2.8 What a backtest must output (the reporting pack)

One folder per trial: daily and monthly return series (gross, net 1×, net 2×), turnover series, portfolio holdings snapshots (monthly), the cost decomposition (commission / spread / impact / borrow / financing), exposure time series (beta, size, value, momentum, sector), the trial ledger row, and `git commit` hash + data-vendor snapshot date. **No result without a reproducible artifact.**

---

## 3. Phase 3 — The statistics a professional actually checks

All of the below are implemented in `validation_toolkit.py`. Thresholds assume a **single pre-registered strategy family with ≤ 40 configurations**; tighten every threshold if your `N_trials` is larger (see the `N_eff` column in §3.11).

### 3.1 Sharpe ratio, its standard error, and the honest confidence interval

```
SE(SR_ann) ≈ sqrt( (1 + SR²/2) / T_years )          [Lo 2002]
95% CI      ≈ SR ± 1.96 × SE
```

| Observed SR (10-year backtest) | SE | 95% CI | Verdict |
|---|---|---|---|
| 0.3 | 0.323 | [−0.33, 0.93] | Indistinguishable from zero |
| 0.5 | 0.335 | [−0.16, 1.16] | Cannot reject 0 |
| 0.8 | 0.363 | [0.09, 1.51] | Barely rejects 0 |
| 1.2 | 0.415 | [0.39, 2.01] | Rejects 0; still consistent with a true 0.4 |

Prefer a **stationary bootstrap** CI (Politis–Romano, block ≈ T^{1/3}) over the analytic one — it handles autocorrelation, vol clustering, and fat tails. Always report the CI, never the point estimate alone.

### 3.2 Probabilistic Sharpe Ratio (PSR) and Minimum Track Record Length (MinTRL)

PSR answers "what is P(true SR > benchmark SR\*), given skew, kurtosis, and track length?" It is the correct replacement for "is my t-stat > 2."

```
PSR(SR*) = Φ[ (ŜR − SR*)·√(T−1) / √(1 − γ₃·ŜR + ¼(γ₄−1)·ŜR²) ]      (ŜR per-period)
MinTRL   = 1 + [1 − γ₃ŜR + ¼(γ₄−1)ŜR²] · (z_conf / (ŜR − SR*))²
```

| Situation | PSR(0) | MinTRL at 95% | Interpretation |
|---|---|---|---|
| SR 0.50/yr, 5 yrs, normal | 0.87 | 11.0 yrs | Not proven — need ~11 yrs of data |
| SR 0.50/yr, 10 yrs, normal | 0.94 | 11.0 yrs | Just short of the 0.95 bar |
| SR 0.50/yr, 20 yrs, normal | 0.99 | 11.0 yrs | Passes |
| SR 0.50/yr, 10 yrs, skew −1.0, kurt 8 | 0.93 | 12.9 yrs | Negative skew **raises** the bar |
| SR 0.80/yr, 10 yrs, normal | 0.99 | 4.4 yrs | Passes comfortably |
| SR 1.00/yr, 5 yrs, skew −1.5, kurt 10 | 0.96 | 4.5 yrs | Passes, but the tail is now your main risk |

Note the pedagogical point: **MinTRL depends on the Sharpe level, not on how much data you have.** For SR 0.50/year and 95% confidence it is ~11 years whether you have 5 years or 20. Adding more years of the same mediocre Sharpe does not prove it — you need a higher Sharpe, more breadth, or a stronger prior.

**Threshold: PSR(0) ≥ 0.95, and MinTRL ≤ available sample length.** For short-volatility / negative-skew strategies, require PSR(0) ≥ 0.99 — the formula penalises skew only mildly relative to the real-world ruin risk.

### 3.3 Deflated Sharpe Ratio (DSR) — the trial-count tax

DSR is PSR measured against the Sharpe you *would expect to see from the best of N trials even if nothing was real*:

```
SR₀ = √V[SR_trials] · [ (1−γ)·Φ⁻¹(1 − 1/N) + γ·Φ⁻¹(1 − 1/(N·e)) ],  γ = 0.5772
DSR = PSR(SR₀)      with N = N_eff
```

Worked example (from the toolkit): a 20-year backtest with a per-period SR consistent with 0.51/yr, trial-SR dispersion 0.35/yr, `N_eff = 200` → `E[max SR given null] = 0.97/yr` → **DSR = 0.018**. Your "0.51 Sharpe" is *worse than what pure noise would have produced* in that search. This is the single most important number in the packet.

| `N_eff` | sd(SR across trials) | E[best SR given null], annualised | Best-SR you need for DSR ≥ 0.95 |
|---|---|---|---|
| 1 | — | 0 | ~0.25 + MinTRL constraint |
| 10 | 0.30 | 0.50 | ~1.05 |
| 50 | 0.30 | 0.75 | ~1.30 |
| 200 | 0.35 | 0.97 | ~1.55 |
| 1000 | 0.35 | 1.20 | ~1.80 |
| 1000 | 0.50 | 1.71 | ~2.30 |

**Threshold: DSR ≥ 0.95** (≥ 0.99 if you intend to lever the strategy).

### 3.4 Probability of Backtest Overfitting (PBO) via CSCV

CSCV splits the timeline into S = 16 contiguous blocks, forms all C(16,8) = 12,870 combinations of "in-sample" vs "out-of-sample" halves, picks the IS-best configuration in each split, and measures how often that winner lands in the **bottom half** out-of-sample. PBO is that frequency.

| PBO | Meaning | Action |
|---|---|---|
| ≤ 0.10 | Selection generalises | Pass |
| 0.10–0.25 | Acceptable with caution | Pass only if DSR ≥ 0.97 |
| 0.25–0.40 | Selection is substantially noise | Fail |
| > 0.40 | You have fit the sample | Kill |

Demo results from the toolkit (40 configs × 240 months): pure-noise family → **PBO 0.51**; family with a real 4%/yr edge → **0.46** (not enough edge to survive selection); real 8%/yr edge → **0.20**.

**Critical implementation rule:** the N columns must be the *actual competing configurations you searched* — not synthetic variants. PBO computed on a curated "nice" grid is theatre. Use `S ∈ {10, 14, 16}` and report the range.

### 3.5 Walk-forward efficiency and purged cross-validation

| Method | Definition | Threshold | Caveat |
|---|---|---|---|
| WFE | `mean(OOS SR) / mean(IS SR)` across ≥ 3 sequential folds | **≥ 0.60** pass; 0.40–0.60 marginal; < 0.40 fail | WFE > 1.0 is a red flag (usually leakage); single-fold WFE is noise |
| Purged K-fold | K-fold with purge window = label horizon and embargo = 1–2% of T | Mean OOS SR within 50% of IS | Only valid if you purge overlapping labels |
| CPCV | Combinatorial purged CV: `C(N,k)` train/test paths → distribution of OOS SR | 5th percentile OOS SR > 0 | Gives a *distribution*, not a point |
| Anchored walk-forward | Expanding IS window, rolling OOS | Report every fold, not the mean | Preferred for regime-shift diagnosis |

### 3.6 Information ratio versus a *matched* benchmark (the alpha test)

Comparing to SPY is not a test; it's a beta measurement. The professional version:

1. Regress strategy returns on `FF5 + UMD + sector dummies` (or, for a long-only book, on a **characteristic-matched portfolio**: same size/value/momentum/industry weights, no signal).
2. Report: **alpha**, its Newey–West t-stat (lag 3–6 for monthly), **IR = alpha / σ(residual)**, and the R².
3. Also report the **beta-adjusted** result for long-only strategies: `IR_matched = (SR_strategy − SR_benchmark·ρ) / sqrt(1−ρ²)`.

| Test | Pass | Marginal | Fail |
|---|---|---|---|
| Alpha t-stat (NW) vs FF6+industry | ≥ 3.0 | 2.0–3.0 | < 2.0 |
| IR vs matched benchmark | ≥ 0.50 | 0.30–0.50 | < 0.30 |
| R² of the factor regression | ≤ 0.70 | 0.70–0.85 | > 0.85 (you are a factor clone) |
| Alpha after removing best sector | ≥ 60% of headline alpha | 40–60% | < 40% |

If your edge disappears when you neutralise momentum and small-cap, you have discovered that small caps with momentum went up — a Tier D result with a Tier A story attached.

### 3.7 The 2× cost test and the break-even cost

Two numbers, both mandatory:

- **Net SR at 2× costs** ≥ **0.50** and ≥ **60% of the 1× net SR**.
- **Break-even round-trip cost** = `annual gross return (bps) / annual turnover` — the cost level at which the strategy earns zero. Require **break-even ≥ 4× your modelled cost**.

Worked example (toolkit §F): 8.5%/yr gross, 300% annual turnover → break-even **284 bp** round trip. At a modelled 12 bp you keep ~8.2%/yr; at 80 bp you keep 6.1%. That strategy is a cost-tolerant strategy. By contrast, a 200%/yr-turnover strategy with a 2% gross alpha has a break-even of **~50 bp** — it is a bet that your spread assumptions are right.

| Strategy archetype | Annual turnover | Gross alpha needed to survive 25 bp round trip | Verdict |
|---|---|---|---|
| Monthly cross-sectional, 100 names, buffered | 150–400% | ≥ 1.0% | Viable |
| Weekly rebalance | 800–1,500% | ≥ 2.5% | Marginal at retail |
| Daily/intraday | 3,000%+ | ≥ 7.5% | Only with institutional costs |
| Buy-and-hold factor tilt | 20–60% | ≥ 0.2% | Robust |

### 3.8 Capacity

Capacity is where net alpha halves (or where the cost drag equals 50% of gross alpha). Compute it explicitly with an impact model, not by intuition:

```
net_alpha(AUM) = gross_alpha − turnover × [0.5·spread + Y·σ_daily·sqrt(Q/ADV)] − borrow − financing
Solve net_alpha(AUM*) = 0.5 × gross_alpha
```

| Intended AUM | Capacity requirement | Note |
|---|---|---|
| < $250k | capacity ≥ 10× AUM | Almost always fine; commission-per-share dominates |
| $250k–$2M | capacity ≥ 5× AUM | Small caps may bind; check per-name ADV vs position size |
| $2M–$10M | capacity ≥ 3× AUM | Micro-cap strategies usually fail here |
| > $10M | explicit impact model + borrow inventory check | Retail structure stops being viable |

Participation cap: **never assume > 2% of ADV per day for a multi-day position, > 5% for a single opportunistic entry.** Position size ≤ 1% of ADV is the retail-safe rule for names under $50M ADV.

### 3.9 Tails, drawdown, and path metrics

| Metric | Formula / definition | Pass | Fail |
|---|---|---|---|
| Tail ratio | `\|q95\| / \|q05\|` | ≥ 1.0 | < 0.8 |
| Skewness of monthly returns | — | > −0.5 | < −1.0 (short-vol profile) |
| CVaR 95% (monthly) | mean of worst 5% | ≤ 1.5 × σ_monthly | > 2.5 × σ |
| Max drawdown vs tolerance | backtest MDD ÷ your real tolerance | ≤ 0.5 | > 0.75 |
| Ulcer index | `sqrt(mean(DD²))` | — | use for ranking, not gating |
| Time under water | longest peak-to-recovery | ≤ 0.4 × sample | > 0.6 × sample |
| Best-month share of total P&L | max(month) / total return | ≤ 25% | > 40% (one event) |
| Profit concentration | top 5% of trades' share of gross P&L | ≤ 50% | > 70% |

A strategy whose entire edge is one month, one sector, or one event is not a strategy; it is a historical anecdote with a Sharpe ratio attached.

### 3.10 Regime and stability diagnostics

| Diagnostic | Test | Pass |
|---|---|---|
| Sub-period consistency | SR in each decade / each of ≥ 3 regimes (e.g., 2008, 2010–19 bull, 2020–21, 2022–25) | All > 0, or ≤ 1 negative with a mechanistic explanation |
| Parameter stability | SR across ±20% perturbations of every parameter | Coefficient of variation of SR ≤ 0.3; no single-parameter cliff |
| Parameter *surface* | SR heat map over 2-D grid | Broad plateau, not a spike (a spike is the definition of overfit) |
| Cross-market replication | Same rule in CA/UK/JP/AU | SR ≥ 50% of US result, same sign |
| Novelty test | SR restricted to post-publication period | ≥ 50% of headline SR |
| Signal decay (IC) | IC by horizon | Monotone or peak beyond your holding period, not before |

### 3.11 The master gate sheet (print this)

A strategy goes live only if **every mandatory gate passes**. No averaging, no "8 out of 11."

| # | Gate | Metric | Pass | Marginal | Fail | Mandatory? |
|---|---|---|---|---|---|---|
| 1 | Data integrity | % PIT-valid universe-months with delisting returns | ≥ 99% | 95–99% | < 95% | ✔ |
| 2 | Survivorship sensitivity | SR(full) − SR(naive) | < 0.10 | 0.10–0.30 | > 0.30 | ✔ |
| 3 | Leakage audit | Time-shuffle placebo SR (95th pct) / violations | ≤ 0.4 / zero | — | any violation | ✔ |
| 4 | Trial accounting | `t` vs HLZ hurdle for `N_eff` | t ≥ 3.0 (N≤10), 3.5 (N≤100), 4.0 (N>100) | −0.5 | below marginal | ✔ |
| 5 | Deflated Sharpe | DSR | ≥ 0.95 | 0.90–0.95 | < 0.90 | ✔ |
| 6 | Backtest overfitting | PBO (S=16) | ≤ 0.10 | 0.10–0.25 | > 0.25 | ✔ |
| 7 | Walk-forward | WFE over ≥ 3 folds | ≥ 0.60 | 0.40–0.60 | < 0.40 | ✔ |
| 8 | True alpha | Alpha t-stat vs FF6+industry (NW) | ≥ 3.0 | 2.0–3.0 | < 2.0 | ✔ |
| 9 | Matched IR | IR vs characteristic-matched benchmark | ≥ 0.50 | 0.30–0.50 | < 0.30 | ✔ |
| 10 | Cost stress | Net SR at 2× costs (% of 1× net SR) | ≥ 0.50 (≥60%) | 0.20–0.50 | < 0.20 | ✔ |
| 11 | Break-even cost | Break-even ÷ modelled cost | ≥ 4× | 2–4× | < 2× | ✔ |
| 12 | Capacity | Capacity ÷ intended AUM | ≥ 5× | 2–5× | < 2× | ✔ |
| 13 | Tails | Tail ratio / skew / best-month share | ≥1.0 / >−0.5 / ≤25% | — | any fail | ✔ |
| 14 | Stability | SR CV over ±20% params | ≤ 0.30 | 0.30–0.50 | > 0.50 | ✔ |
| 15 | Regime | Negative-SR sub-periods | 0 | 1 (explained) | ≥ 2 | ✔ |
| 16 | Out-of-market | Cross-market or post-publication SR | ≥ 50% of headline | 25–50% | < 25% | ✔ (if data exists) |
| 17 | Track length | MinTRL ≤ available sample | ✔ | — | exceeds | ✔ |

**Scoring for the record:** count passes; 17/17 = green, 15–16/17 with no mandatory fail = amber (paper trade only), any mandatory fail = red (kill, log, move on). Do not fudge mandatory gates — that is how retail quants donate their capital to market makers.

---

## 4. Phase 4 — The forward / paper-test protocol

### 4.1 First, accept what a forward test can and cannot prove

Required years to reject SR = 0 at one-sided 5% with 80% power (`T = ((1.645 + 0.842)/SR)²`):

| True annual SR | Years of forward data for 80% power | Years for raw t = 3 |
|---|---|---|
| 0.25 | **98.9** | 144.0 |
| 0.50 | **24.7** | 36.0 |
| 0.75 | **11.0** | 16.0 |
| 1.00 | **6.2** | 9.0 |
| 1.50 | **2.7** | 4.0 |
| 2.00 | **1.5** | 2.2 |
| 3.00 | **0.7** | 1.0 |

**Conclusion:** a 6–12 month paper test has essentially **zero power** to confirm a Sharpe-0.5 strategy. Anyone who says "the paper test confirmed the strategy" after a quarter is describing a coin flip that landed heads. Therefore:

- **The statistical burden must be carried by the backtest** (Phase 3, with deflation), the economic prior, and cross-market/cross-sectional replication.
- **The forward test's job is operational, not statistical:** prove the plumbing, discover the cost model's error, and catch the failure modes a backtest cannot see (data feed delays, borrow availability, halts, corporate-action handling, index events, broker rejects).

Design the forward test to *falsify*, not to confirm.

### 4.2 The two-track protocol

| Track | Duration | Purpose | Pre-registered success metric | Decision |
|---|---|---|---|---|
| **T1 — Shadow/paper** | 8–13 weeks (≥ 100 signal-generated trades, ≥ 3 monthly rebalances) | Data plumbing, signal reproducibility, timing | 100% of signals reproduced bit-identically from live feed; zero missing corporate actions; execution timestamps within spec | Pass/fail only — **no alpha judgement** |
| **T2 — Micro-live** | 6–12 months, ≥ 150 round trips, capital = 5–10% of target | Cost-model calibration, borrow, real slippage, operational incidents | Realised slippage within 1.5× of modelled; fill rate ≥ 95%; tracking error to paper book ≤ 30 bp/month | Scale if in-spec; pause if out |
| **T3 — Scale-in** | 12–24 months, capital 10% → 100% in 4 steps | Confirm no degradation as size grows | Net SR ≥ 0.6 × backtest net SR; slippage scaling exponent ≤ 0.6 | Kill if breached |

**T1→T2 gate:** operational only. **T2→T3 gate:** operational + the "no-falsification-evidence" check in §5. **T3→full size:** cumulative evidence, not a single number.

### 4.3 Sample size and monitoring design (do this *before* starting T2)

Pre-register a **group-sequential design** rather than a fixed-horizon test, so that stopping early does not itself inflate the false-positive rate:

| Element | Pre-specified choice | Why |
|---|---|---|
| Primary endpoint | Net annualised SR measured on micro-live book | One number, decided in advance |
| Monitoring cadence | Monthly, at fixed dates only (never after a bad week) | Removes discretionary stopping |
| Alpha spending | O'Brien–Fleming boundary (conservative early, ≈ nominal late): `α(t/T) ≈ 2 − 2Φ(z_{α/2}/√(t/T))` | Preserves overall 5% |
| Total sample | 24 monthly observations (2 years) unless killed earlier | Consistent with §4.1 for SR ≈ 0.75–1.0 |
| Futility boundary | Stop if cumulative net SR < 0 at month 12, or < 0.25 at month 18 | Prevents burning 2 years on a dead strategy |
| Borrow/shortfall endpoint | Realised slippage − modelled slippage | Independent t-test, one-sided, α = 0.05, n ≥ 150 fills |
| Interim looks | 4 (months 6, 12, 18, 24) | Enough to catch disasters, few enough to preserve power |

**Power for the operational endpoint** (this is where a forward test *does* have power): slippage distributions are far less noisy than returns. With `n = 150` fills, a one-sided t-test detects a 5 bp mean slippage shortfall against a 20 bp per-fill standard deviation at ~92% power (and a 10 bp shortfall at >99%). This is why the pilot is worth running.

### 4.4 Stopping rules (pre-registered, no discretion)

| Trigger | Threshold | Action | Reversible? |
|---|---|---|---|
| **Slippage blowout** | Realised − modelled > 25 bp per fill for 2 consecutive months, or > 3σ | Halt, recalibrate, restart T2 clock | Yes |
| **Tracking error** | Live-vs-paper monthly return diff > 100 bp for 2 months | Halt; audit for implementation error | Yes |
| **Drawdown** | Live DD > 1.5 × backtest max DD | Cut to 25% size; audit | Only with new evidence |
| **Statistical futility** | Cumulative net SR < 0 at month 12 | Kill | No |
| **Regime break** | Realised IC < 0 for 6 consecutive months | Kill or re-pre-register | No |
| **Data/ops** | Any unresolved PIT/look-ahead defect, or a corporate action mishandled | Immediate halt | Yes after fix |
| **Borrow loss** | > 20% of short positions become unborrowable | Re-run without short leg; if long-only fails, kill | Yes |
| **Capacity** | Position size > 2% ADV on > 10% of days | Reduce size or universe | Yes |
| **Personal** | Strategy violates your stated risk tolerance for 1 month | Reduce to zero | Yes |

**Anti-tampering rule:** the stopping rules are stored in `prereg/` and evaluated by a script that writes an append-only log. If you find yourself *reinterpreting* a rule, that is the moment the strategy has already failed.

### 4.5 Multiple testing across live strategies

Testing happens at the portfolio level too. If you run *m* strategies:

1. **FDR control (Benjamini–Hochberg, q = 10%)** on the p-values of the net-SR tests across all live candidates. This is the right tool when you're screening many strategies and can tolerate some false positives.
2. **Familywise control (Holm/Bonferroni)** when the cost of a false positive is a blown-up account — i.e., for the one strategy you're about to lever.
3. **Re-run the DSR at the portfolio level** with `N_eff` computed across *all strategies ever tested*, not just the live ones. This is the number your capital allocation should respect.
4. **Reality Check / SPA test** (White 2000, Hansen 2005) when comparing several variants against a benchmark: bootstrap the *maximum* statistic, not each statistic separately.

Practical rule of thumb for a retail quant running 3–5 strategies: assume your best strategy's true Sharpe is `0.6 × observed Sharpe`, and size accordingly. That is the empirical version of the McLean–Pontiff haircut.

### 4.6 Execution metric contract (measure these from day 1)

| Metric | Definition | Target |
|---|---|---|
| Implementation shortfall | (arrival mid − fill price) × side, in bp | Within model |
| Realised vs modelled spread | per fill | Ratio ≤ 1.5 |
| Market impact vs participation | bp per 1% ADV | Exponent ≤ 0.6 |
| Fill rate / partial fills | filled qty ÷ ordered qty | ≥ 95% |
| Time-to-fill | minutes from order to fill | Within spec |
| Borrow availability / fee | % of short notional, by name | ≤ modelled fee |
| Reject / cancel rate | — | < 1% |
| Signal-to-order latency | seconds | < 60s after close |
| Corporate-action exceptions | count/month | 0 |

---

## 5. Phase 5 — The specific evidence that would falsify the strategy

Falsification evidence is pre-registered, measurable, and *sufficient* — not "adds doubt." Written before T2 begins.

### 5.1 The falsifier table

| # | Falsifier | Concrete test | Kill threshold | What it means |
|---|---|---|---|---|
| F1 | **Selection was the edge** | DSR with full `N_eff` | DSR < 0.90 | The best of your trials is what noise produces |
| F2 | **Selection doesn't generalise** | PBO over the real grid | PBO > 0.25 | IS winner is bottom-half OOS |
| F3 | **It's a factor clone** | FF6+industry regression | α t < 2.0, or R² > 0.85 | You found size/value/momentum/beta |
| F4 | **It dies at realistic costs** | 2× and 3× cost runs | net SR ≤ 0.20 at 2×, or negative at 3× | You are trading your broker's revenue |
| F5 | **It dies at your size** | Impact model + ADV cap | capacity < 2× intended AUM | Not implementable |
| F6 | **Edge is one event/period** | Best-month share, sub-period SRs | > 40% of P&L in one month; ≥ 2 negative decades | Anecdote, not strategy |
| F7 | **Parameter cliff** | ±20% perturbation, 2-D surface | SR → 0 or sign flip; SR CV > 0.5 | Fitted to the sample |
| F8 | **Signal decay is faster than holding period** | IC by horizon | IC ≤ 0 before your first rebalance | You cannot capture your own signal |
| F9 | **Only the short leg works and you can't short** | Leg decomposition + borrow test | Long-only SR < 0.3 | Unimplementable |
| F10 | **It's a data artifact** | Placebo universe, timestamp audit, vendor-vintage diff | Any leakage violation, placebo SR > 0.4 | Bug, not alpha |
| F11 | **Survivorship is the alpha** | Full vs naive panel | ΔSR > 0.30 | You're shorting dead companies you never saw |
| F12 | **Out-of-sample decay** | Sealed holdout, or post-publication subsample | OOS SR < 0.4 × IS SR over ≥ 3 years | Published-and-arbed-away |
| F13 | **Regime dependency** | Exclude the dominant regime | SR excluding best regime < 0.2 | One-off macro wind |
| F14 | **No cross-market support** | Same rule, ≥ 2 other markets | SR < 0 or < 25% of US in both | Local artifact / luck |
| F15 | **Live diverges from paper** | Tracking error T2 | > 100 bp/month for 2 months | Implementation or model error |
| F16 | **Borrow/short squeeze** | HTB fee series on short book | Fees erode > 40% of short-leg P&L | Not a repeatable trade |
| F17 | **Statistically indistinguishable** | MinTRL vs sample; bootstrap CI | CI includes 0 | Not yet proven — do not scale |

### 5.2 The "kill interview" — five questions to answer in writing

1. If I had tested the *opposite* sign of this signal, would the result have been significant too? (If yes: the signal is measuring noise or a proxy for volatility/liquidity.)
2. Does the strategy still work if I replace my signal with a random variable that has the same autocorrelation and cross-sectional distribution? (Placebo test — should fail.)
3. Which single observation, removed, reduces total P&L by > 20%? If one exists, name it and justify why it will recur.
4. What am I trading against, and *why does that counterparty keep losing*? If the answer is "nobody, I'm just early," you're late.
5. If a competent stranger read my pre-registration and my code, would they agree I tested one hypothesis? Or would they count 40?

### 5.3 The "cheap falsifiers" you should run first

Before the expensive statistics, run these five in an afternoon — they kill most ideas:

| Cheap falsifier | Time | Kill signal |
|---|---|---|
| Shuffle test (returns in random time order) | 30 min | Placebo SR > 40% of real SR |
| Sector-neutralise | 1 hr | Alpha drops > 60% |
| Long-only vs long-short split | 1 hr | All P&L in one leg |
| Exclude top/bottom 10% of names by size | 1 hr | Alpha vanishes → micro-cap artifact |
| Cost stress 3× | 30 min | Negative net return |

---

## 6. The evidence packet (what you keep on file)

For each strategy that reaches T2, one folder containing:

```
packet/
  00_prereg.md                 # frozen, signed, dated
  01_data_certification.md     # PIT validity %, delisting coverage, vendor snapshot IDs
  02_leakage_audit.md          # 5 tests + outputs
  03_backtest_report.pdf       # net 1x/2x, turnover, exposures, cost decomposition
  04_statistics.md             # SR + bootstrap CI, PSR, MinTRL, DSR (with N_eff), PBO, WFE,
                               #   alpha t vs FF6+ind, matched IR, break-even, capacity, tails
  05_gate_sheet.md             # the 17 gates, pass/fail, signatures
  06_falsifiers.md             # the 17 falsifiers, measured values, verdict
  07_forward_protocol.md       # T1/T2 design, monitoring dates, stopping rules
  08_trial_ledger.csv          # every trial ever run
  09_code/                     # git repo with tag == the reported run
  10_postmortem.md             # filled in when it dies (it will)
```

The presence of `08_trial_ledger.csv` and `10_postmortem.md` is what separates a process from a hobby.

---

## 7. Practical notes specific to a Toronto-based retail quant

| Item | Detail |
|---|---|
| Broker/account | US-listed stocks/ETFs trade cheapest in a US-dollar account; **TFSA cannot be margined or shorted**, so long-short work must live in a margin (non-registered) account |
| Currency | Convert in large, infrequent tranches (Norbert's gambit for CAD↔USD at $10k+); retail FX spreads are 15–40 bp and will silently eat a 5%/yr strategy |
| Withholding tax | 15% US dividend withholding applies in taxable and TFSA accounts; the Canada–US treaty reduces/exempts it in an **RRSP**. A dividend-capture or high-dividend strategy has a materially different after-tax return in each account type |
| Shorting | No US-style PDT rule for Canadian-regulated accounts, but most brokers impose their own minimum equity and margin requirements; borrow inventory is thinner than US brokers' |
| Settlement | T+1 on US trades; ensure your backtest's cash accounting matches |
| Tax | Capital gains taxed at 50% inclusion for individuals (verify current-year rules — inclusion-rate proposals have changed recently). **Model after-tax returns**: a high-turnover strategy that looks like SR 1.2 pre-tax can be SR 0.7 after tax |
| Data | Vendors that support PIT + delisting: Norgate ($, survivorship-free + delisted), Sharadar SF1/SFP via Nasdaq Data Link (PIT-ish fundamentals, includes delisted), CRSP via WRDS (academic/institutional), EODHD/Tiingo/Polygon (prices ok, weak PIT fundamentals). **Yahoo/yfinance is not survivorship-free and is not PIT — never use it for validation** |
| Benchmarks | Use total-return indices (e.g., `SPY`/`IVV` TR, `XIC.TO` TR), not price-only |

---

## Appendix A — Formula reference

```
Annualised Sharpe           SR = mean(r)/sd(r) · √ppy
Standard error              SE(SR) ≈ √((1 + SR²/2)/T_years)
t-statistic                 t ≈ SR · √T_years  (large-sample)
PSR                         Φ[(ŜR − SR*)√(T−1) / √(1 − γ₃ŜR + ¼(γ₄−1)ŜR²)]
MinTRL                      1 + [1 − γ₃ŜR + ¼(γ₄−1)ŜR²](z/(ŜR − SR*))²
E[max SR | null]            √V[SR]·[(1−γ)Φ⁻¹(1−1/N) + γΦ⁻¹(1−1/(Ne))]
DSR                         PSR evaluated at SR* = E[max SR | null]
PBO (CSCV)                  P(rank_OOS(best_IS) ≤ N/2) over all C(S,S/2) splits
N_eff (trials)              (Σλᵢ)² / Σλᵢ²   over eigenvalues of trial-return correlation
IR (Fundamental Law)        IR ≈ IC · √BR · TC
Break-even cost (bp)        annual gross return (bp) / annual turnover
Impact                      Y·σ_daily·√(Q/ADV),  Y ∈ [0.3, 0.5]
Required years (power)      ((z_{1−α} + z_{power}) / SR)²
Annual turnover             mean(Σ|Δw|) × periods per year
```

## Appendix B — Using the toolkit

```bash
python3 validation_toolkit.py          # self-test + worked demo
```

```python
from validation_toolkit import (sharpe, block_bootstrap_sr_ci, psr, min_trl,
                                dsr, effective_n_trials, pbo_cscv, wfe,
                                breakeven_cost_bps, required_years, bh_fdr)

# Phase 3 gate 5
sr_m  = sharpe(r_monthly) / 12**0.5
d, sr0 = dsr(sr_m, T=len(r), var_sr_trials=np.var(trial_srs_monthly),
             n_trials=effective_n_trials(trial_matrix),
             skew=skew(r), kurt=kurtosis(r, fisher=False))

# Phase 3 gate 6
print(pbo_cscv(trial_matrix, S=16))

# Phase 3 gate 11
print("break-even round trip bp:", breakeven_cost_bps(gross_r, turnover))

# Phase 4 power budget
print(required_years(0.75))    # -> 11.0 years for 80% power
```

## Appendix C — Trial accounting: what counts as a trial

| Counts as a trial | Does not count |
|---|---|
| Every Sharpe computed during exploration (even from a throwaway notebook) | Reading a paper (but log the *hypothesis* it generated) |
| Parameter grid cells | Bug fixes that make the code correct (log them) |
| Universe / filter variants | Re-running the identical spec to check it reproduces |
| Winsorisation, weighting, neutralisation, lag choices | Changing chart colours |
| Re-testing an old idea after the sample extends | — (this *does* count, actually) |
| Every "let me just check one more thing" | — |

**If in doubt, it counts.** The DSR machinery is cheap to run and brutally informative; a self-flattering trial count is neither.

---

*Prepared as a working protocol, not legal or investment advice. All thresholds are defaults calibrated to retail-scale US equity strategies with monthly-to-daily rebalancing; tighten them as your trial count, leverage, or universe size grows.*
