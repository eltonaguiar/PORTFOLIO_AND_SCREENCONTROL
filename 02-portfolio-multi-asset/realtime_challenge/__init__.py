"""REALTIME CHALLENGE — a forward-evidence generator, not a trading signal.

Goal: produce pre-registered, cost-aware, multiple-testing-corrected evidence about
whether any *rule-based, fully specified* strategy has a real edge in a class that
trades 24/7 (crypto spot), plus a live paper-trade round that opens and closes
positions on real current market prices.

Design rules (from the project proof standard):
  R1  Signals are computed on CLOSED bars only. Fills happen on the NEXT bar open
      (execution_convention = "lag1_next_open"). No same-close fills, ever.
  R2  Every trade pays taker fee + slippage on both legs. Default round-turn
      friction is 26 bps and the fee is a parameter, never an afterthought.
  R3  If a bar's high and low touch BOTH take-profit and stop-loss, the stop is
      assumed to fill first ("conservative_intrabar"). This removes the single
      largest source of fake intraday edge.
  R4  Parameters are frozen in config; there are no sweeps. The trial count is
      the number of registered hypotheses, and it is recorded so Sharpe can be
      deflated.
  R5  Every strategy is judged against buy-and-hold on the same symbol set and
      the same window, plus a permuted-returns control.
  R6  A clean negative result is a deliverable.

Nothing here is financial advice and nothing here may be described as "profitable"
without forward evidence at n >= 100 closed trades.
"""

__version__ = "1.0.0"
MODEL_NAME = "deepseek-flash"
