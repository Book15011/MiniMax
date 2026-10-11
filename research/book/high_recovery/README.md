# Near-high selection: reading guide and evidence

## Decision
Neither new model passed the frozen improvement gates. No live switch is recommended.
The finite experiment is complete; the overall return-improvement objective remains unmet.
Core results source c67c093;278 tests PASS; independent41,364-outcome reconstruction PASS with zero
return/drawdown/CS error. Twelve real-bar decisions also passed future invisibility and conditional short checks.
Fresh uncached baseline replay reproduced all equity/gross/net/day arrays and windows/targets/trades exactly.
An initial parquet index-frequency assertion failure was preserved and corrected; no numerical result changed.

## What the models do
book_recovery_high prefers coins that remain closest to their highest hourly close over7/14days.
book_recovery_high_blend averages that ranking equally with ordinary risk-adjusted momentum.
They only reselect longs in parent UP mode, keep parent shorts and conditional positive budget, and match risk downward.
Hourly-close maxima are a proxy for the paper's intraday highs; market-cap filters could not be reproduced.
See PROTOCOL.md and RESEARCH_SOURCES.md for the frozen rules, motivation and limitations.

| Model | Mean14d return | Median14d | Bad10% | Mean drawdown | CS |
|---|---:|---:|---:|---:|---:|
| book_e20combo_brk_cash | +3.7316% | +0.2833% | -11.5222% | 10.7700% | 0.152300 |
| book_recovery_high | +3.1530% | +0.0547% | -10.0434% | 9.9148% | 0.143437 |
| book_recovery_high_blend | +3.4100% | +0.0914% | -10.5660% | 10.3051% | 0.150265 |

These are2298 historical cash-start14-day windows with fees, spread,1h lag and terminal liquidation.
Higher return/CS is better; lower positive drawdown is better. Bad10% is the10th percentile, not a probability forecast.
Reduced downside with reduced average returns does not satisfy this user's return-recovery objective.
Ten-hypothesis conditional bounds remain negative; neither qualifies for the prespecified stress phase.
All history is spent. Quarter clusters reduce dependence but do not control all prior project-wide selection.

## Where to look
Published table: /home/ubuntu/test/MiniMax/results/scoring/leaderboard_recovery.md
Numeric table: /home/ubuntu/test/MiniMax/results/scoring/leaderboard_recovery.csv
All ten recovery trials: /home/ubuntu/test/MiniMax/results/scoring/recovery_trials.csv
This experiment: /home/ubuntu/test/MiniMax/results/book/20261011-high-recovery-v1
Frozen131-model context: /home/ubuntu/test/MiniMax/results/book/20261011-high-current-context-v1
Start with decision.base.json and comparison.base.csv; independent_audit.json validates the calculations.
fresh_baseline_audit.json verifies uncached replay; panel_cross_study_audit.json checks shared panel content.
real_bar_causality_audit.json and forward_clock_checks.json provide additional checks.

The current-context ranking uses the SAME frozen Oct11 01HKT BTC-only query and25spaced cases as earlier boards.
Rank is the lower7/8-day mean return point estimate. Zero diagnostic passes; no case reselection.
This is not a refreshed market forecast or certified best strategy. BCH29/30 broad-query failure persists; adaptiveOFF.
The ten new recovery models lack full original competition hard-gate validation.
--score updates the original board; it does not automatically publish this separate research diagnostic.
To reproduce this fixed cohort use .venv/bin/python -B -m research.book.high_recovery.run, then run_tests,
audit and publish_review in that order. The raw baseline replay is fresh_baseline_audit.

## Exposure and actual-account limits
baseline_exposure_diagnostic.json shows the matched7-day paths averaged76.8%long and13.48%short.
Those are marked historical exposures, not PnL attribution or live positions.
The baseline's marked gross peaked108.10% despite target gross<=100%; the frozen simulator allows drift
between rebalances. This is a research-engine limitation, not proof of an actual live violation.
first_decisions_not_converged means a cash-start path stayed distinct from shared history; its own decisions
were still replayed throughout the window. It is not an optimizer or a numerical convergence failure.
Actual EC2 holdings/deployment, live feed, endgame and same-account switch outcomes remain UNVERIFIED.

## Genuine future evidence
The original seven-model cohort/worktree remains untouched.
A separate five-model cohort was frozen before new outcome reads: baseline, the two residual variants and
the two near-high variants. Period Oct12 00UTC to Oct15 00UTC (08HKT to08HKT). Names, source, parameters,
spreads and endpoint are fixed; all five are evaluated together only after complete data.
Run .venv/bin/python -B -m research.book.high_recovery.forward from THIS worktree after complete data.
Current preflight WAITING; no partial return, scheduled job or automatic run exists.
Its seven clock-integrity checks pass. Initial import-path launch failure is preserved; no scores were produced.
One3-day path cannot statistically certify superiority or authorize a live switch.
Do not edit this worktree's runtime source or configuration: its future source hashes are now frozen.
