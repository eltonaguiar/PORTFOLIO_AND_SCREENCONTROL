# Methodology: proving a stock strategy works (discovery, backtest, statistics, forward test, falsification)

## ChatGPT-6 Luna

No finite backtest can prove a strategy will keep working. The goal is to make the claim
auditable and falsifiable
: define what “works” means in advance, test it on data that could have been known at the time, account for every research trial, and then seek independent forward evidence.
The thresholds below are practical starting gates, not universal laws. Set them before seeing the final test results, and tighten or adapt them to the strategy’s horizon, risk, liquidity, and intended capital.
Write a short protocol that specifies:
Economic rationale:
Eligible instruments and dates:
Signal and execution rules:
Primary outcome:
Benchmark and risk limits:
Decision gates:
Permitted changes:
Timestamp the protocol, code version, and data snapshot—for example, in an immutable repository or independent registry. Keep final holdout data inaccessible during development.
Count every meaningful attempt, not just published candidates.
Trying many variants and reporting only the winner creates selection bias even if each individual backtest is computed correctly. Treat manual tuning and informal experimentation as trials too. If a result inspires a new rule, that rule is a new hypothesis—not a confirmation of the old one.
Discovery, validation, and confirmation should be separate.
Use discovery data to develop ideas, validation data to choose among frozen alternatives, and a final untouched period or forward test for confirmation. If the final result prompts another change, retire that holdout for the revised strategy.
Archive the cleaned inputs, transformation code, cost assumptions, and trade-level outputs. A result that cannot be independently reproduced is weak evidence.
, against a benchmark chosen in advance. Report estimates and uncertainty, not just a pass/fail statistic.
Run the primary tests on
net returns
Close
Minimise
Restore
Chrome
Chrome Remote Desktop
Display on another screen – pinned
E
Extensio
Extensions
LastPass
Has access to this site
Bookmark this tab
Install ChatPlayground AI
Model: ChatGPT-6 Luna. Change model
Maximize ChatGPT-6 Luna panel
Messages
Collapse sidebar
