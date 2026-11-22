# Arena.ai (Chat mode, blind A/B) — proving a stock strategy works

Blind pair: model identities are hidden until a vote is cast, so the sections are labelled A and B.

## Assistant A


A defensible validation protocol
No test can prove that a market edge will persist. The strongest defensible claim is narrower: for a specified universe, implementation, and capital level, a frozen strategy beat a preselected, investable benchmark after costs by an economically worthwhile amount, in data not used to develop it, with quantified uncertainty and acceptable risk.

Define the strategy’s portfolio-level net return
r
t
S
r
t
S
​
, the matched benchmark’s net return
r
t
B
r
t
B
​
, and active return
a
t
=
r
t
S
−
r
t
B
a
t
​
=r
t
S
​
−r
t
B
​
. Before testing, set the minimum economically worthwhile annual active return
h
h, which may be zero or may include capital, operating, financing, and implementation hurdles. The primary hypothesis is:

H
0
:
E
[
a
t
]
≤
h
versus
H
1
:
E
[
a
t
]
>
h
.
H
0
​
:E[a
t
​
]≤hversusH
1
​
:E[a
t
​
]>h.
The strategy, benchmark, costs, risk limits, and statistical plan must all be fixed before the confirmatory data are examined.

1. Candidate discovery without self-deception
Discovery can be exploratory. Claims of validation cannot be. If a candidate was developed by examining a historical period, that period is development data—not an independent test set.

Stage	Required practice	What it prevents
State a mechanism	Write down why the signal should earn returns, what market participants or constraints create the opportunity, and when it should work or fail.	Inventing a story after seeing a profitable backtest.
Log all exploration	Record every signal, feature, universe, filter, lookback, rebalance rule, threshold, benchmark, cost assumption, and discarded variant. Save failures as well as winners.	Reporting only the best result and understating the search.
Keep a trial ledger	Include manual experiments, data transformations, alternative samples, subgroups, parameter grids, and “small tweaks.” Store code, outputs, timestamps, and data versions.	Treating human choices as if they were not tests.
Separate development from confirmation	Use development data for research and tuning. Use nested chronological validation for model selection. Reserve a later, untouched holdout—or future data—for the final confirmatory test.	Repeatedly reusing a “holdout” until it is no longer a holdout.
Pre-register the candidate	Before opening confirmatory data, timestamp the full strategy and test plan. A signed document, locked repository, or third-party timestamp can establish the date.	Retrospectively describing a test as pre-planned.
Freeze the implementation	Save code and data hashes, parameter values, environment, signal timestamps, order logic, and all risk limits. Have someone independent audit the implementation if possible.	Accidental leakage, undocumented changes, or irreproducible results.
The pre-registration should specify:

Exact signal formula, parameter values, position sizing, universe, rebalance frequency, and treatment of missing observations.
Data sources and availability timestamps; execution venue, order type, and earliest permissible fill.
Benchmark, return frequency, costs, leverage, financing, borrow assumptions, and planned capital.
The one primary performance endpoint, its economic hurdle
h
h, and the statistical test.
Secondary risk gates, robustness tests, sample-size target, power, multiple-testing procedure, and stopping rules.
Which analyses are exploratory. Any change made after examining confirmatory results creates a new candidate; those results become development data for that version.
If the trial history is incomplete, do not claim that a multiple-testing adjustment has solved the problem. The defensible remedy is a new, untouched test.

2. Backtest construction rules
A backtest is only as credible as its data and execution assumptions. The backtest should model what could actually have been known and traded at each timestamp.

Issue	Required rule	Useful audit
Point-in-time data	Use the value available to a trader at the decision time—not a later-revised or restated value. For fundamentals, estimates, index membership, borrow data, and corporate news, retain publication/availability timestamps and historical versions.	Rebuild a sample of signals from archived “as known then” records.
Survivorship and security history	Use the historical point-in-time universe, including delisted, bankrupt, acquired, and otherwise failed securities. Include delisting returns and historical identifier mappings. Do not apply today’s index constituents to past dates.	Reconcile historical membership and delisting treatment independently.
Look-ahead and timing	A signal can use information only after it became available. A signal computed using the closing price generally cannot fill at that same close unless the order was submitted before the applicable cutoff. Model reporting delays, time zones, release times, and execution latency.	Shift signals later by one bar or one trading day as a stress test; investigate any future-data “lead” signal.
Fills and trading costs	Simulate order timing and fills, not just close-to-close returns. Include spread, commissions, exchange fees, taxes, slippage, market impact, financing, and short borrow/locate costs. Model partial fills, missed fills, halts, and short-sale constraints where relevant.	Compare predicted costs with quote-level data, broker records, or a small live pilot.
Corporate actions	Use tradable prices for fills. Adjust positions for splits and corporate actions; account for dividends, mergers, delistings, spin-offs, rights, and cash-in-lieu. Avoid double-counting adjustments in prices and cash flows.	Reconstruct selected corporate-action periods from raw prices and event records.
Trading constraints	Enforce realistic lot sizes, leverage, margin, liquidity, short availability, borrow recalls, market hours, and position limits.	Re-run under stricter participation, borrow, and execution assumptions.
Time-series validation	Use chronological outer test periods. Tune only inside each training period. Purge observations whose outcomes overlap a split and embargo at least the label/holding horizon where appropriate. Do not rely on random train/test splits for a claim about future trading.	Keep a timestamped record of which dates were available to each model fit.
For stock strategies, use point-in-time prices and corporate-action handling carefully: a retrospectively adjusted price series can be useful for return calculations, but it must not silently give the signal information or trading prices that would not have existed then.

The benchmark should also be investable and fixed in advance. Match relevant exposures such as market, sector, size, leverage, currency, cash, and financing as appropriate. A strategy that merely loads on a known factor or market beta has not demonstrated incremental value over a suitable alternative.

3. Professional performance and robustness checks
The numerical bands below are a preregisterable example policy, not universal laws or guarantees. DSR, PBO, and walk-forward efficiency are diagnostics; none replaces a properly powered confirmatory test. The primary endpoint and all thresholds must be chosen before results are examined.

Check	Definition and example decision bands
Deflated Sharpe Ratio (DSR)	Apply the DSR to the metric actually used to select strategies—Sharpe versus cash, or active-return Sharpe/information ratio versus the benchmark. Green: DSR
≥
0.95
≥0.95;
≥
0.99
≥0.99 is stronger. Caution: 0.90–0.95. Red:
<
0.90
<0.90.
Probability of Backtest Overfitting (PBO), via CSCV	Green:
<
10
%
<10%. Caution: 10–20%. Red:
>
20
%
>20%. These are policy bands, not formal universal cutoffs. PBO diagnoses selection fragility; it does not establish profitability.
Walk-forward efficiency (WFE)	Define it in advance. Example: median across chronological outer folds of
I
R
OOS
/
I
R
IS
IR
OOS
​
/IR
IS
​
, using net active IR. Green: WFE
≥
0.50
≥0.50 and at least 75% of outer folds have positive OOS active returns. Caution: WFE 0.25–0.50 or fewer positive folds. Red: WFE
<
0.25
<0.25 or aggregate OOS performance is negative.
Information ratio versus matched benchmark	Annualized net active return divided by annualized tracking error, with uncertainty adjusted for serial dependence. Example screen: Green if OOS IR
≥
0.50
≥0.50 and the one-sided 95% lower confidence bound on mean active return exceeds
h
h. Caution: positive but below the hurdle, or a confidence interval that still overlaps it. No-go: after a powered test, the upper confidence bound is at or below
h
h. An IR threshold such as 0.50 is an example, not a universal standard.
2× cost test	Rerun the strategy with assumed variable trading frictions doubled—spread, slippage, impact, borrow, and financing as appropriate. Green: stressed net active return remains above
h
h and retains at least half of the baseline edge above
h
h. Caution: still positive but retains less than half. Red: stressed edge is at or below
h
h. Re-simulate the fills; do not merely subtract a constant from the reported result.
Capacity	Estimate the largest AUM
A
max
⁡
A
max
​
at which the strategy still clears its predeclared net-return hurdle under conservative market-impact and liquidity assumptions. Green:
A
max
⁡
≥
2
A
0
A
max
​
≥2A
0
​
, where
A
0
A
0
​
is intended capital, and performance at
A
0
A
0
​
clears the hurdle. Caution:
A
0
≤
A
max
⁡
<
2
A
0
A
0
​
≤A
max
​
<2A
0
​
. Red:
A
max
⁡
<
A
0
A
max
​
<A
0
​
. A conservative initial equity screen is to keep ordinary participation around or below 5% of ADV per security per day; smaller stocks or close-auction trades may require much lower limits.
Tail ratio and tail risk	Define tail ratio explicitly, for example (TR=Q_{0.95}(r_{\text{net}})/
Definitions that matter
DSR. One common form first computes the Probabilistic Sharpe Ratio against a selection-adjusted benchmark
S
R
∗
SR
∗
:

P
S
R
(
S
R
∗
)
=
Φ
⁣
(
(
S
R
^
−
S
R
∗
)
T
−
1
1
−
γ
^
3
S
R
^
+
γ
^
4
−
1
4
S
R
^

2
)
,
PSR(SR
∗
)=Φ
​

1−
γ
​

3
​

SR
+
4
γ
​

4
​
−1
​

SR

2

​

(
SR
−SR
∗
)
T−1
​

​

​
,
where
T
T is the number of return observations,
γ
^
3
γ
​

3
​
is skewness, and
γ
^
4
γ
​

4
​
is ordinary kurtosis. A common selection adjustment is

S
R
∗
=
μ
^
S
R
+
σ
^
S
R
[
(
1
−
γ
E
)
Φ
−
1
(
1
−
1
/
N
)
+
γ
E
Φ
−
1
(
1
−
1
/
(
N
e
)
)
]
,
SR
∗
=
μ
​

SR
​
+
σ

SR
​
[(1−γ
E
​
)Φ
−1
(1−1/N)+γ
E
​
Φ
−1
(1−1/(Ne))],
where
N
N is the number of effectively independent trials,
μ
^
S
R
μ
​

SR
​
and
σ
^
S
R
σ

SR
​
describe the trial Sharpe estimates, and
γ
E
γ
E
​
is the Euler–Mascheroni constant. The DSR is the PSR evaluated at this adjusted threshold.

Use the full trial ledger, not just the surviving candidates. Report sensitivity to the number of trials; do not reduce
N
N opportunistically because variants are correlated. A maximum-statistic bootstrap over the candidate family is a useful complement. The formula above does not, by itself, fix serial dependence or nonstationarity; use dependence-aware inference or block bootstrap methods as well. A DSR of 0.95 is not a 95% probability that the strategy will be profitable in the future.

PBO via CSCV. Start with a performance matrix for the complete candidate family. Divide the history into an even number of contiguous blocks—often 10–16 when the history permits—and, for every split into equal halves, select the best candidate on one half and rank it on the other. PBO is the fraction of splits in which the in-sample winner ranks below the OOS median. Purge or embargo overlapping outcomes as needed. CSCV is a selection-overfitting diagnostic, not a chronological trading simulation; it does not replace walk-forward testing.

Walk-forward efficiency. Definitions vary, so lock one before testing. One usable definition is

W
F
E
=
median
⁡
j
(
I
R
O
O
S
,
j
I
R
I
S
,
j
)
,
WFE=median
j
​
(
IR
IS,j
​

IR
OOS,j
​

​
),
where each IR is calculated net of costs against the same benchmark. Report every fold, the aggregate OOS IR, and the fraction of positive OOS folds. If an in-sample IR is nonpositive or near zero, the ratio is undefined or unstable; do not drop that fold to make WFE look better.

Information ratio. For active returns
a
t
=
r
t
S
−
r
t
B
a
t
​
=r
t
S
​
−r
t
B
​
, the ordinary annualized estimate is
K

a
ˉ
/
s
a
K
​

a
ˉ
/s
a
​
, where
K
=
252
K=252 for daily US equity returns. With serial dependence, estimate long-run variance

Ω
^
=
γ
^
0
+
2
∑
ℓ
=
1
L
w
ℓ
γ
^
ℓ
Ω
=
γ
​

0
​
+2
ℓ=1
∑
L
​
w
ℓ
​

γ
​

ℓ
​

and use
K

a
ˉ
/
Ω
^
K
​

a
ˉ
/
Ω

​
, or use a block-bootstrap confidence interval. Test the mean active return against
h
h, not just whether a point-estimate IR looks large.

Capacity. Estimate it from actual anticipated orders, participation, spread, volatility, turnover, and calibrated market impact. A common impact model uses a term proportional to
σ
Q
/
V
σ
Q/V
​
, where
Q
Q is order size and
V
V is market volume; its parameters should be calibrated, not assumed. Include borrow availability for shorts. Define
A
max
⁡
A
max
​
as the capital level where the strategy stops meeting the preregistered hurdle under the chosen conservative cost scenario—not merely the level where it can still place orders.

Tail ratio. State the return frequency and formula. Quantile estimates are noisy, particularly with short samples. A high ratio does not rule out severe drawdowns, and a low ratio can be inherent in strategies such as carry or short-volatility approaches. If accepting intentional negative skew, preregister the compensating return hurdle and strict expected-shortfall and drawdown limits.

4. Forward or paper test: power, multiplicity, and stopping
A forward test should be a frozen experiment, not a new tuning period.

Lock the code and protocol. Save the code/data hashes, parameters, benchmark, costs, and test plan. Log every signal and intended order with timestamps.
Use real-time information. Signals must be generated only from data available then. Record intended fills, actual or conservatively modelled fills, and realized slippage.
Do not mistake paper fills for live capacity. Paper trading can test data timing and software. It cannot establish market impact or passive-order fill rates reliably. A small-capital pilot is stronger evidence about execution.
Keep one primary endpoint. For example, mean net active return versus a specified benchmark, tested against
h
h. Treat other performance and risk metrics as preregistered gates or diagnostics—not alternative chances to declare success.
Set sample size before starting. Use strategy-level portfolio returns; do not count correlated stock-days or individual trades as independent observations.
Run for both sufficient information and sufficient calendar coverage. A calendar floor—often at least 12 months for a daily equity strategy—helps cover seasonality but is not a substitute for statistical power. Slower strategies may require substantially longer.
For a one-sided test of
H
0
:
μ
≤
h
H
0
​
:μ≤h at significance
α
α, with power
1
−
β
1−β to detect an alternative
h
+
δ
h+δ, a simple independent-observation approximation is

n
≈
(
(
z
1
−
α
+
z
1
−
β
)
σ
δ
)
2
.
n≈(
δ
(z
1−α
​
+z
1−β
​
)σ
​
)
2
.
For daily returns and an annualized active IR above the hurdle of
I
R
ann
IR
ann
​
, this becomes approximately

n
≈
252

(
z
1
−
α
+
z
1
−
β
)
2
I
R
ann
2
.
n≈
IR
ann
2
​

252(z
1−α
​
+z
1−β
​
)
2

​
.
At one-sided
α
=
0.05
α=0.05 and 80% power, an idealized illustration is:

Annualized active IR above hurdle	Approx. daily observations	Approx. trading years
0.25	24,900	99
0.50	6,230	24.7
0.75	2,770	11.0
1.00	1,560	6.2
1.50	690	2.7
2.00	390	1.5
These are optimistic iid calculations, not recommended horizons. Serial correlation, volatility clustering, heavy tails, regime changes, and uncertainty in costs can increase the required sample. Use Newey–West/HAC inference or, preferably, block-bootstrap or simulation-based power that preserves dependence. If there are many genuinely independent bets, they can contribute information—but stock-days sharing common market risk are not independent replicates.

When testing multiple candidates on the same confirmatory sample, control family-wise error: use Holm’s step-down procedure or a maximum-statistic bootstrap that preserves dependence between strategies; Bonferroni is a conservative fallback. For example, ten independent confirmatory tests with Bonferroni correction reduce the per-test level to 0.005 and require roughly 1.9 times as many observations as the one-test illustration. DSR and PBO help diagnose historical selection; they do not replace correction for multiple confirmatory tests.

Monitoring rule	Example preregistered rule
Fixed endpoint	Specify the information target and maximum sample size in advance. Do not extend the test just because the result is nearly significant.
Interim efficacy looks	Prefer no inferential peeking. If interim looks are necessary, use a group-sequential alpha-spending design. For a one-sided total
α
=
0.05
α=0.05, O’Brien–Fleming-style boundaries are approximately
z
=
2.33
,

1.90
,

1.645
z=2.33, 1.90, 1.645 at 50%, 75%, and 100% information; calculate exact boundaries for the actual design. Require a minimum calendar duration as well.
Futility	Optionally stop for futility if preregistered conditional power falls below, for example, 10% at or after 50% information. This is a no-go, not evidence of success.
Safety or operational failure	Stop immediately for data-integrity failures, unmodeled execution problems, or breached risk limits. Record the result as a failure or interrupted test; do not erase the period and restart the same test.
End of test	If the maximum sample is reached without passing, report “not validated” or “inconclusive.” A revised strategy is a new candidate and needs new confirmatory data.
5. What would falsify the strategy?
Pre-register falsifiers as carefully as the success criteria.

Observation	Interpretation
The edge disappears when using point-in-time data, delisted securities, correct timestamps, or plausible fills.	The original backtest was not a tradable result; a material data or implementation defect is a hard no-go.
After the powered confirmatory test, the one-sided 95% upper confidence bound on net active return is at or below
h
h.	Evidence against the strategy meeting its declared economic hurdle.
The confidence interval still overlaps
h
h at the planned endpoint.	Not necessarily proof of no edge, but it is not validation. Do not deploy on the claim that it works.
Performance vanishes at 2× costs, at intended capital, or under realistic borrow and fill assumptions.	The apparent edge is not economically implementable at the stated scale.
A matched benchmark or simple factor/sector exposure explains the returns, leaving no incremental active return.	The strategy has not demonstrated value over the preselected alternative.
A future-signal placebo predicts returns, or randomized/placebo signals perform similarly.	Evidence of leakage, confounding, or an effect unrelated to the stated mechanism.
Results depend on one parameter value, one security, one short period, or a few exceptional days—and this fragility was not predicted by the thesis.	Strong evidence of selection or concentration risk. Define concentration checks in advance; for example, flag if a small number of days or names generate more than half of total profits. This is a warning requiring explanation, not a universal automatic rejection rule.
OOS performance fails in the strategy’s preregistered operating conditions, or the stated regime filter only works after being chosen retrospectively.	The claimed mechanism or operating rule has not survived the test.
Actual pilot slippage, borrow costs, drawdowns, or fills fall materially outside the preregistered model or risk limits.	The strategy fails implementation or risk validation, even if the historical return test passed.
Use three outcomes, not two:

Pass: the locked, multiplicity-controlled confirmatory test clears the economic hurdle, and the capacity and risk gates also pass.
Fail: a hard data, implementation, capacity, risk, or adequately powered performance criterion fails.
Inconclusive: the result is too imprecise to establish either success or failure. Inconclusive is not permission to lower the hurdle, change the metric, or keep testing until a favorable result appears.
In short: historical diagnostics can expose overfitting, but the strongest evidence is a frozen, adequately powered forward test at realistic costs and intended capital. No single Sharpe, PBO, or backtest plot can substitute for that evidence.


## Assistant B


This is educational methodology, not investment advice. You cannot prove a strategy works. You can subject it to severe tests it should fail if false, account for every trial you ran, and pre-commit to what would kill it.

What "works" means for a professional: net of costs, out-of-sample, after correcting for how many things you tried, with a risk-matched benchmark, with capacity to trade, and with a live kill rule.

0. The stage-gate
Do not go live unless all gates pass. One fail = stop or restart with new pre-registration.

Gate	Test	Pass threshold to continue
0	Economic rationale + pre-registration	Written before seeing OOS
1	Backtest integrity	All Table 2 = PASS
2	Multiple-testing adjusted significance	DSR >=0.95, PBO <=0.20
3	Robustness	WFE >=0.50, IR >=0.50, 2x-cost Sharpe >0.5 & >50% of base, Tail Ratio >1.0, Capacity >20x intended size
4	Forward/paper + live incubation	Pre-specified N, alpha-spending, no peeking
5	Live monitoring	No falsification trigger in Table 7
Harvey-Liu-Zhu rule of thumb: for a new claimed factor/strategy, require t > 3.0, not 2.0, because finance has tried thousands of things.

1. Candidate discovery without self-deception
1.1 Pre-register before you backtest. One page, timestamped, immutable.

Table 1: Pre-registration template - example: US large-cap overnight reversal

Field	Concrete entry
Hypothesis + why it should exist	Overnight overreaction + market-maker inventory mean-reversion; short-term reversal documented, overnight vs intraday split
Universe	Russell 1000 as of date t, price >$5, ADV 20d >$10M, exclude ETFs/ADRs, include delisted history
Signal exact formula	Signal_t = - (Close_t - VWAP_t)/sigma_20d, z-scored within sector, only if |z|>1.0
Portfolio	Dollar-neutral, sector-neutral +/-2%, max 2% per name, 200 long / 200 short
Holding / rebalance	Enter MOC day t, exit MOC t+1. 1-day hold.
Execution assumption	Enter at t+1? No: signal uses data available by 15:55, trade MOC t, settle t+1. State lag.
Costs model	0.5bp commission + half-spread from TAQ + borrow 2% ann + impact sqrt-model
Sample	IS: 2010-2018, Validation: 2019-2021, OOS lockbox: 2022-2025. One OOS touch.
Primary metric / target	Net Sharpe 0.8 after costs, IR vs beta/sector-matched benchmark >0.5
Falsification	Kill if DSR<0.90, PBO>0.30, forward 1-yr Sharpe <0, drawdown > 1.5x IS 99% quantile
Trials budget	Max 50 parameter combos, grid pre-listed. Stop after.
If you change anything, new version + reason. Old version stays.

1.2 Trial accounting. Selection bias scales with N. Count everything.

Table 2: Trial log - you must be able to produce this on audit

Trial #	Date	Change vs base	IS Net Sharpe	Notes
1-10	2026-01-02	threshold 0.5,1.0,1.5...	0.4-0.9	grid
11-30	2026-01-05	lookback 10,20,40d, sector vs universe neutralization	...	grid
31-42	2026-01-07	tried delay 0 vs 1 day, MOC vs next open	...	delay 0 is look-ahead, discarded
...	...	...	...	...
N=142	total		variance of trial Sharpes V=0.18	N=142 enters DSR
Rule: N = all backtests with same-ish data that informed your decision, including failures, abandoned ideas, and other researchers' tests on same data you saw. If you can't state N, assume N=1000. Never report best Sharpe without N.

Hold out a true lockbox: e.g., last 2-3 years + most recent regime never used for selection, parameter choice, or stopping. One touch only, after Gate 2-3 pass.

2. Backtest construction rules
Most "Sharpe 2.0" strategies are bugs.

Table 3: Build checklist - FAIL on any row = invalid backtest

Bias	Rule	Concrete implementation
Point-in-time	Only data known at decision time	Fundamentals lagged: Q filings +45d (large) / +90d, earnings date from announcement file, not fiscal end. Index membership, analyst data as-of date. Corporate actions PIT-adjusted. No revised macro series.
Survivorship	Universe includes dead stocks	Use CRSP/Compustat survivorship-free file. Include delisted returns: use delisting return, else -30% for performance delists. Backtest must be able to hold Lehman, SVB to zero. Test: % of 2010 universe still listed in 2025 should be ~60-70%, not 100%.
Look-ahead	Signal(t) -> trade(t+1)	If signal uses Close_t, you cannot trade Close_t. Trade next open/MOC t+1 + 1-day delay for fundamentals. Timestamp every input: available_at. Use merge_asof. Audit: shift signal +1 day, performance should not collapse to zero/negative if correct; shifting -1 day should not explode.
Corporate actions	Total return, not price return	Use split/dividend adjustment factor dated ex-date, applied PIT. Shorts pay dividends, pay borrow. Splits: adjust shares overnight. Test with AAPL 4:1 2020, TSLA, large special dividends. Never use Yahoo Adj Close naively - it is revised backwards.
Costs - must model 3 layers	Commission + spread + impact + short/finance	Example US large-cap: commission 0.5-1bp one-way, half-spread max(1bp, quoted_spread/2 from TAQ / 5bp fixed if no intraday), borrow: 2% general + DCB list for hard-to-borrow (kill if >10% shorts hard), financing: Fed funds +50bp on long, -rebate on short. Impact: square-root: bps = 10 * daily_vol * sqrt(Q / ADV_dollar) . Turnover 800% ann * 5bp = 40bp drag - compute explicitly.
Liquidity / feasibility	No fantasy fills	Participation <5% of 20d ADV per name for large-cap, <1-2% for small-cap. No buying at high/low, no fills on halted/limit-up days, volume cap, open-auction cap 10% of auction volume. Borrow availability check.
Overfitting controls	Embargo + purging	No random k-fold on time series. Use purged, embargoed walk-forward: purge training observations whose label overlaps test, embargo 5-10 trading days after each test block.
Run diagnostics: turnover, gross/net exposure, number of positions, concentration (top 10% weight), long vs short contribution. If 5 stocks drive 80% of P&L, you have no strategy.

3. Statistics a professional checks
Table 4: Master decision table - compute on net, post-cost returns

Metric	What it catches	Compute on	Reject / Marginal / Accept
Deflated Sharpe DSR	Lucky best of N tries	Full IS+Validation net daily returns	<0.90 reject, 0.90-0.95 marginal, >=0.95 accept
PBO via CSCV	IS optimization doesn't transfer OOS	IS strategy returns, S=16 blocks	>0.50 reject, 0.20-0.50 suspect, <0.20 accept, <0.10 strong
Walk-Forward Efficiency WFE	Degradation in rolling OOS	Rolling IS/OOS walks	<0.30 reject, >=0.50 accept, >=0.75 strong, >60% walks positive
Information Ratio vs matched benchmark	Just beta/style exposure	Active = Strat - risk-matched bench	IR<0.30 reject, IR>=0.50 + t>=2.0 accept, FF5+MOM alpha t>3 ideal
2x Cost test	Cost illusion	Re-run with all costs x2	Sharpe_2x <=0 or <50% base = reject
Capacity	Untradable at size	Impact model	Capacity <10x target = reject, >20-100x accept
Tail Ratio + drawdown	Picking up pennies	Daily net returns	Tail <=1.0 reject, >1.0-1.1 accept, Calmar <1 suspect
a) Deflated Sharpe Ratio - Bailey & Lopez de Prado 2014

Probabilistic Sharpe PSR(SR0) = probability true Sharpe > benchmark SR0 accounting for skew/kurtosis and track length.

DSR = PSR with SR0 = expected best Sharpe under null of zero true Sharpe after N tries:

SR0 = sqrt(V) * [ (1-γ) Φ^{-1}(1-1/N) + γ Φ^{-1}(1-1/(N e)) ]

V = variance of Sharpe ratios across N trials, γ=0.5772 Euler, Φ^{-1}= inverse normal.

DSR = Φ[ (SR_hat - SR0)sqrt(T-1) / sqrt(1 - skewSR_hat + (kurt-1)/4 * SR_hat^2 ) ]

T = number of return periods, SR_hat annualized, skew/kurt from non-annualized returns but SR_hat annualized consistently - use same frequency conversion.

Worked example:
Base: 5y daily, T=1260, SR_hat=1.2 net, skew=-0.2, kurt=4.5, N=200, V=0.04 (std 0.2)
SR0 = 0.2*[0.42282.576 + 0.57722.878] = 0.55
DSR = Φ[(1.2-0.55)*35.48 / sqrt(1+0.24+1.26)] = Φ[14.6] ≈ 1.00 -> PASS

Same strategy but you tried N=1000 with V=0.25 (std 0.5): SR0 ≈ 1.62 > SR_hat 0.8 -> DSR ≈ 0.02 -> REJECT. This is how data mining dies.

Report: SR_hat, t-stat, PSR(0), DSR, N, V, T, skew, kurt, Min Track Record Length.

b) PBO via Combinatorial Symmetric Cross-Validation

Split IS history into S=16 equal contiguous blocks.
Form all train/test splits: choose S/2 blocks for IS, rest OOS. That's C(16,8)/2 = 6435 splits.
For each split: find strategy configuration with best IS Sharpe, record its OOS Sharpe rank among all configs (logit = log rank/(1-rank)).
PBO = fraction of splits where best IS rank is below OOS median (logit <0).
Interpretation: P( IS winner disappoints OOS ). You want low.
Also plot: IS vs OOS scatter should slope up; performance degradation slope; probability of loss OOS.

Threshold: <0.10 excellent, <0.20 acceptable for live with haircut, >0.50 means memorization - invert your selection.

Needs at least ~3-5y daily to have stable blocks. Do not shuffle days.

c) Walk-Forward Efficiency

Rolling, not one IS/OOS split. Example: 3y IS train -> 1y OOS test, step 1y forward, embargo 5d. Anchored or rolling both OK, rolling stricter.

For each walk w: optimize only on IS_w, lock params, record OOS_w Sharpe.

WFE = median(OOS Sharpe_w) / IS full-sample Sharpe. Alternative: mean OOS return / mean IS return.

Also require: % OOS windows >0 >=60%, no 2 consecutive windows with Sharpe <-1, parameter stable across walks (e.g., lookback 15-25d always chosen, not jumping 5d to 100d).

Example: IS Sharpe 1.1, median OOS Sharpe 0.45 -> WFE=0.41 -> REJECT/MARGINAL. Haircut live expectation to 0.45, not 1.1.

d) Information Ratio vs matched benchmark

Never vs S&P 500 if you are dollar-neutral. Build matched bench:

Beta-hedge: regress strat excess on market, size (SMB), value (HML), momentum (UMD), short-term reversal, sector ETFs. Or construct benchmark portfolio with same sector/beta exposures rebalanced like strat but without signal (e.g., random / equal-weight within same universe/neutrality).
Active_t = R_strat,t - R_bench,t. IR = mean(Active)*252 / std(Active)*sqrt(252).

Require IR >=0.50 net, t = IR*sqrt(Years) >=2.0, and FF5+MOM alpha >0 with t>2.5-3.0. Decompose: how much return from market timing, sector bets, size tilt? True alpha should survive.

Example: Strat Sharpe 1.0 but beta 0.3 to momentum, momentum did well -> Active IR 0.15 -> REJECT, you rediscovered momentum.

e) 2x cost test

Double everything: commission x2, spread x2, impact coefficient x2, borrow x2, add 1-day delay slippage.

Require: Sharpe_2x >0.5 AND Sharpe_2x >0.5Sharpe_base, MaxDD_2x <1.5MaxDD_base, turnover unchanged. If strategy dies at 8bp vs 4bp, edge was microstructure illusion.

f) Capacity

Square-root impact: MI_bps ≈ Y * sigma_daily(%) * sqrt( participation ), Y~5-10. Participation = Order_value / ADV_dollar.

Procedure: scale AUM 10M -> 50M -> 200M -> 1B, re-simulate with impact, plot net Sharpe vs AUM. Capacity = AUM where net Sharpe = 0.5* base or IR <0.3.

Rule: live at <5% of capacity, <5% ADV per name large-cap, <1% small-cap. Require capacity >20x intended capital, >100x ideal. Report largest 10 positions' days-to-liquidate at 20% volume.

g) Tail Ratio

Tail = p95(daily net return) / |p5|. >1.0 means right tail bigger than left. Want >1.05.

Also check: skewness > -1.0, Sortino / Sharpe >1.0, max drawdown duration <18 months for daily strategy, 99% Expected Shortfall vs Normal VaR, best vs worst month asymmetry. Calmar = CAGR / |MaxDD| >1.0 preferred. If Sharpe 1.5 but Tail 0.7 and skew -2, you are short vol.

4. Forward / paper-test protocol
Paper is not live, but must be pre-committed like a clinical trial.

4.1 Sample size and power - pre-compute how long you must run

Test H0: true Sharpe <=0 vs H1: Sharpe = SR_target (haircut IS by 50%).

Approx years needed: Y ≈ ((z_{1-α}+z_{1-β}) / SR_target)^2, n_days=252*Y, where z_{1-α}=1.645 for α=5% one-sided, z_{1-β}=0.842 for 80% power, sum=2.487.

Table 5: Minimum forward duration for 80% power, α=5% one-sided

Haircut target SR_ann	Years needed	Trades needed if per-trade edge μ/σ=0.10
0.50	24.7 y - impossible	~620 independent trades
0.75	11.0 y	~620 trades
1.00	6.2 y	~620 trades
1.50	2.7 y	~620 trades
2.00	1.5 y	~620 trades
Implication: daily Sharpe <1 cannot be proven by 6-month paper alone. You need:

Minimum 6-12 months plus minimum 300-1000 independent bets (trades / (1+autocorr)), covering 2 volatility regimes, OR
Combine backtest + forward via Bayesian haircut, but never shorten forward because early P&L looks good.
Pre-specify primary endpoint: e.g., net Sharpe on daily paper returns, or mean net P&L per trade. Pre-specify SR_target = 0.5* IS net Sharpe. Compute required N_trades = ((2.487)*σ_trade/μ_trade)^2. Example: μ=$12/trade, σ=$120 -> μ/σ=0.10 -> need 619 trades. At 5 trades/day -> ~6 months minimum.

4.2 Execution protocol

Item	Rule
Environment	Paper engine with real-time data, real halts, borrow locate fails, queue position. Log intended vs simulated fill. No manual overrides.
Size	Trade intended size from start, or 1/10 size live incubation after paper - do not paper trade 100 shares then claim capacity for 100k.
Duration	Fixed in pre-reg: e.g., 12 months or 800 trades, whichever later.
Looks	2-3 interim looks max, with alpha-spending. Example O'Brien-Fleming: α1=0.0006 at 1/3, α2=0.015 at 2/3, α3=0.047 final. If you peek daily on Bloomberg without adjustment, your p-value is garbage.
Multiple testing	If paper-testing M=5 variants, Holm correction: test smallest p at α/M. Or joint White Reality Check / Hansen SPA bootstrap for all variants vs benchmark. Report family-wise p.
Stopping	Efficacy stop only if crosses OBF boundary. Futility stop: kill if conditional power <20% given data so far + target. Pre-write both.
Example stopping rule: After 400 trades, compute t = mean/std*sqrt(n). Stop for success if t>3.5 (early OBF), stop for futility if 95% CI for Sharpe still includes 0 and projected final power <20%. Otherwise continue to 800.

Do not reset clock after a drawdown. A restart = new trial, N+1, must be disclosed.

5. What would falsify it - kill rules
Write these before live. A strategy without a killer is a hobby.

Table 6: Falsification triggers - breach of any = halt, reduce to incubation, or retire

Evidence	Concrete trigger example
Live Sharpe incompatible with claim	12-mo live net Sharpe <0 and 95% CI excludes pre-reg target 0.8; or live t-stat < -1.5
Alpha explained	FF5+MOM regression alpha t drops <1.5 and loading explains >70% of return; IR vs matched bench <0.2
Overfitting realized	Live return below 5th percentile of CSCV OOS distribution; WFE realized <0.2
Risk break	Drawdown > 1.5x worst IS drawdown or >99% bootstrap quantile; Tail Ratio live <0.85; 3 consecutive walk windows negative
Cost/capacity break	Realized slippage >2x modeled for 3 months; borrow becomes hard on >15% shorts; participation >5% ADV to deploy target
Regime/invariant break	Pre-registered invariant violated: e.g., long/short beta spread >0.2, sector neutrality breached, turnover 2x model, crowdedness (pairwise correlation of holdings) doubles
Bug found	Any PIT, survivorship, corporate-action error that removes >20% of backtest Sharpe on fix = invalidate all prior tests
Better null	Hansen SPA / White Reality Check p >0.10 across family; DSR recomputed with true N including forward tweaks <0.90
Final reporting pack to claim "works":

Pre-reg + trial log with N, V
PIT/survivorship/cost code + audit tests
Net equity, drawdown, monthly table, turnover, exposures
DSR, PBO + CSCV histogram, walk-forward table, IR + factor regression, 2x-cost, capacity curve, Tail/Skew/Kurt/Calmar
Forward pre-analysis plan, power calc, fills log, sequential p-values with correction
Signed kill rules and live dashboard
Pass all, survive 12+ months live small-size with IR intact, then - and only then - scale.

Give a rigorous methodology for proving a stock trading strategy actually works: (1) candidate discovery without self-deception, including pre-registration and trial accounting; (2) backtest construction rules: point-in-time data, survivorship, look-ahead, costs, corporate actions; (3) the statistics a professional checks with decision thresholds: deflated Sharpe DSR, PBO via CSCV, walk-forward efficiency, information ratio versus a matched benchmark, 2x cost test, capacity, tail ratio; (4) a forward/paper-test protocol with sample size and power, stopping rules, multiple-testing correction; (5) the evidence that would falsify the strategy. Use tables and be concrete.

