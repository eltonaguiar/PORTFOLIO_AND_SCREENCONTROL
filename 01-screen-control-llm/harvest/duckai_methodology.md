# Duck.ai — proving a stock strategy works

Surface: duck.ai, model `GPT-6 Luna`, Fast mode, **no account and no API key**. Harvested with gutter-click + Ctrl+A/C.

## GPT-6 Luna (Duck.ai)

A strategy is credible only if it survives a documented search, realistic simulation, genuinely untouched evaluation, and prospective trading. No single statistic proves an edge; the thresholds below are practical gates to preregister, not universal laws. DSR adjusts a Sharpe for selection and non-normal returns; CSCV estimates how often an in-sample winner ranks poorly out of sample. Neither replaces a final untouched test.
ssrn.com
1
Stage	Protocol	Evidence to retain
1. Discover without fooling yourself	State the economic rationale, universe, signal, holding period, sizing, rebalance schedule, benchmark, risk limits, and intended use before examining results. Separate exploratory research from confirmatory testing. Preregister the final rule, primary metric, test period, costs, exclusions, and pass/fail criteria in a timestamped, immutable record.	Versioned code and data snapshots; dated hypotheses; every result and decision; a trial ledger.
2. Count all trials	Count every strategy family, parameter set, indicator, universe, timeframe, filter, cost assumption, and manual variation that influenced selection—including abandoned and unpublished runs. Record which trials are materially correlated; estimate effective trials for DSR, but preserve the raw count and method. Do not “reset” the count after changing the strategy.	Full trial ledger, including failures, and a description of how effective trial count was estimated.
3. Build the backtest	Use point-in-time data: only information actually available at each decision time, including realistic publication and vendor delays. Define the tradable universe as it existed then; include delisted and failed firms. Enforce signal-to-order timing so a bar’s close or later information cannot produce a fill at that same close. Model splits, dividends, mergers, spin-offs, symbol changes, and delisting proceeds consistently.	Data provenance, timestamps, corporate-action treatment, universe membership history, and tests for look-ahead and survivorship bias.
4. Model implementation	Simulate orders, fills, spread, commissions, exchange and regulatory fees, market impact, borrow availability/fees, financing, partial fills, and liquidity constraints. Apply costs to actual turnover and position sizes; stress them by at least 2×. Use conservative fill assumptions, especially for limit orders and illiquid names.	Gross and net returns; turnover; cost breakdown; fill assumptions; capacity curve by capital and participation rate.
5. Validate, then test prospectively	Use chronological train/validation/test partitions; purge overlapping labels or positions and add an embargo where leakage is possible. Freeze the strategy before opening the final holdout. Run rolling or expanding walk-forward tests using only past data for each fit. After historical gates pass, paper trade the frozen rules without discretionary overrides.	Dated forecasts/orders, simulated or actual fills, slippage, rejected trades, exceptions, and comparison with the preregistered model.
Statistical review and example gates
Choose one primary endpoint in advance—usually net excess return or information ratio—and report confidence intervals, not just point estimates. Use dependence-aware inference (for example, block bootstrap or appropriately adjusted standard errors) because returns are autocorrelated and overlapping positions reduce the effective sample size.
Check	What it answers	Example preregistered gate
Deflated Sharpe Ratio (DSR)	Does the observed Sharpe remain persuasive after accounting for non-normality and the search that selected it? Supply the return frequency, skew, kurtosis, track record, trial count/effective trials, and selection benchmark.	DSR ≥ 0.95 as a strong-evidence gate; below that, treat the result as provisional. The DSR framework specifically addresses selection bias and non-normal returns.
ssrn.com
PBO via CSCV	Across combinatorial train/test partitions, how often does the in-sample winner land below the median out-of-sample? Apply it to the candidate set, not a single strategy in isolation.	Prefer PBO < 0.20; regard ≥ 0.50 as a serious warning. These are governance cutoffs, not universal statistical constants. CSCV was proposed for estimating backtest overfitting in investment simulations.
ssrn.com
Walk-forward efficiency (WFE)	Does performance persist in sequential, out-of-sample windows? Define it beforehand, e.g. aggregate net OOS Sharpe ÷ aggregate net IS Sharpe; report each window too.	Illustrative gate: WFE ≥ 0.50, with positive net excess return in a majority of windows and no single window dominating total profits. Ratios are unstable if IS Sharpe is near zero; show the numerator and denominator.
Information ratio vs matched benchmark	Is active return worth its active risk relative to a benchmark with the same universe, exposure, frequency, and investability?	Require positive net IR and a dependence-adjusted 95% confidence interval for mean active return that excludes zero in the confirmatory test. Match market, size, sector, and other material exposures where relevant.
2× cost test	Is the edge robust to cost misspecification?	At twice the preregistered all-in trading costs, require positive net expectancy and acceptable risk-adjusted performance; otherwise reject or reduce the claimed capacity.
Capacity	Does the edge survive at the capital you plan to trade?	Specify target capital before testing. Require returns at that capital to clear the same net gates, with conservative volume/participation limits and impact assumptions. Report the capacity curve, not one favorable AUM estimate.
Tail ratio and drawdowns	Is performance dependent on rare gains while losses are poorly controlled?	Define tail ratio as a consistent gain-tail quantile divided by the absolute loss-tail quantile (for example, 95th-percentile gain ÷ absolute 5th-percentile loss). Set a minimum consistent with the strategy’s mandate; also bound max drawdown, expected shortfall, and gap risk. No universal tail-ratio cutoff is defensible across strategies.
Treat these gates as a conjunctive review, not a score to average: a high Sharpe should not compensate for failed costs, capacity, or tail-risk tests. A result that passes many variants of the same test is not independent confirmation.
Forward / paper-test protocol
Item	Practical protocol
Freeze	Hash and archive signal code, data inputs, parameters, sizing, execution logic, benchmark, and rules for missing data or outages. Any change that could affect returns starts a new version and is logged as another trial.
Duration and observations	Set the test length from power, not convenience. Estimate the minimum detectable net effect
δ
δ, the variability and serial dependence of returns, significance level, and desired power before launch. For independent observations, a rough two-sided mean-test approximation is
n
≈
(
(
z
1
−
α
/
2
+
z
1
−
β
)
σ
/
δ
)
2
n≈((z
1−α/2
​
+z
1−β
​
)σ/δ)
2
; trading data usually require a dependence-aware method and more observations. For illustration, 5% significance and 80% power require about
7.84
(
σ
/
δ
)
2
7.84(σ/δ)
2
independent observations. Convert that to calendar time using the strategy’s actual trade rate and effective sample size.
Power target	Preregister a primary hypothesis and use a realistic minimum effect—net of costs—that would justify deployment. Target at least 80% power (often 90% for costly decisions). If the expected sample cannot distinguish that effect from noise, the test is underpowered, not a pass.
Multiple testing	Prefer one primary hypothesis. If several strategies or endpoints are confirmatory, predefine family-wise error control (e.g. Holm) or false-discovery-rate control as appropriate. Include interim looks, variants, and any tuning in the trial record and correction. DSR and PBO are useful diagnostics, not permission to keep testing until something passes.
Stopping	Set a fixed end date/sample size and review schedule before starting. Do not stop early because results look good. If interim monitoring is necessary, preregister a sequential-testing method and its error spending. Stop immediately for predefined operational, data-integrity, or risk-limit breaches; classify those separately from statistical success.
Decision	Pass only if the preregistered primary net metric and risk/implementation gates pass on the prospective record. Report all trades and the full result, including any deviations. A paper test validates process and expected execution more than live market impact; scale cautiously and keep monitoring.
What would falsify the strategy?
Falsifying evidence	Consequence
The edge disappears with point-in-time data, delisted securities included, or corrected signal timing.	The original result was contaminated; reject it.
Net performance is zero or negative under realistic costs, or fails the 2× cost test.	No investable edge at those assumptions.
The frozen strategy fails the preregistered prospective test, or its confidence interval rules out the minimum worthwhile effect.	Reject or materially revise; any revision is a new hypothesis requiring fresh validation.
Results depend on one asset, era, event, parameter point, or a handful of trades; nearby reasonable settings collapse.	Evidence of fragility or selection, not a robust effect.
PBO is high, DSR is weak after the full trial count, or walk-forward results repeatedly reverse.	The historical winner is plausibly overfit; do not promote it on the backtest alone.
Performance vanishes at target capital, under conservative fills, or after accounting for borrow, impact, and capacity.	The strategy may be statistically interesting but not tradable at the intended scale.
Unrecorded overrides, data leaks, or unreproducible results are found.	Evidence is invalid until independently rebuilt and retested.
The standard is not “a backtest that looks good.” It is a frozen, reproducible strategy that survives realistic implementation, selection-aware validation, and a sufficiently powered prospective test.
