# Short rebound protection: result and reading guide

## Decision
No verified upgrade. Both new guards failed the original improvement rules. Do not switch live from this study.
The useful research lead is book_recovery_allshort24; its recent and weak-profile averages improved, but its
full-history mean/median and some short-horizon downside outcomes were worse.
The finite two-model batch is done. The overall goal of finding a reliable better strategy remains unmet.

## What is new
The earlier 24-hour short filter only affected the extra shorts funded from unused cash.
These guards also cover shorts from the main DOWN-mode trend strategy.

- book_recovery_allshort24: close a parent short when its own completed 24-hour return is positive.
- book_recovery_rebound: close all parent shorts when BTC is up 48 hours and more than half the valid liquid
  universe is also up 48 hours. Missing selected prices invalidate the signal.
- Neither opens a new position or increases gross targets. Closing a short can remove a hedge, so a
  mandatory 30-day covariance check scales the remaining book down if its estimated risk would increase.
  Incomplete covariance means retain the exact parent. All tunables were frozen before outcomes.

These are hypotheses motivated by momentum-rebound research, not a replication or market-direction forecast.
PROTOCOL.md and RESEARCH_SOURCES.md contain the source links and exact fixed rules.

## Results
Historical cash-start14-day windows, including fees, spreads,1-hour execution lag, guard and terminal liquidation.
The 2298 overlapping windows are not 2298 independent samples.

| Model | Mean14d | Median14d | Bad10% | Mean drawdown | CS |
|---|---:|---:|---:|---:|---:|
| book_e20combo_brk_cash | +3.7316% | +0.2833% | -11.5222% | 10.7700% | 0.152300 |
| book_recovery_allshort24 | +3.6702% | -0.0066% | -11.0302% | 10.4829% | 0.139817 |
| book_recovery_rebound | +3.6267% | -0.0188% | -11.4583% | 10.6767% | 0.144757 |

Higher return and CS are better; lower positive drawdown is better.
Bad10% is the 10th percentile of returns, not an executed short win rate. CS is the existing research composite, not a verified official live competition score.

The 2024-on 14-day mean improved from 2.3785% to 2.5842% for allshort24, a 0.2056 percentage-point increase.
Its recent bad10% improved from -13.1801% to -12.3042%.
However, full-history mean fell 0.0614 percentage points; median fell below zero.
The 12-hypothesis purged-quarter mean-difference lower bound is -0.5737 percentage points, not a confirmed edge.
It improved all six old weak-profile9–10-day means, but worsened bad10% in three of four weak 7/8-day comparisons.
That prevents calling the gain reliable for the user's remaining-time objective.
The broad rebound guard failed recent and weak mean conditions too.
Neither qualified for the prespecified 2x-cost/+1h-lag stress phase; it was not run.

## Updated comparison table
Public Markdown: /home/ubuntu/test/MiniMax/results/scoring/leaderboard_recovery.md
Numeric table: /home/ubuntu/test/MiniMax/results/scoring/leaderboard_recovery.csv
All twelve recovery trials: /home/ubuntu/test/MiniMax/results/scoring/recovery_trials.csv

This table now contains 133 models, retaining the SAME 25 spaced BTC-only historical cases and Oct11 01HKT query.
It is not a refreshed market forecast. Rank orders the lower7/8-day mean return point estimate.
No model passed the joint 133-model, two-horizon diagnostic check. The bound uses 23 purged cases in 14 quarters.
Adaptive remainsOFF; the original broad query failed with BCH absent,29/30 endpoints.
The twelve new recovery models have not passed the full original competition hard gates.

| Model | Diagnostic rank | 7d mean | 8d mean | 7d bad10% | 8d bad10% |
|---|---:|---:|---:|---:|---:|
| allshort24 | 20 | +2.9627% | +3.2127% | -8.4157% | -9.6984% |
| rebound | 24 | +2.8436% | +3.0115% | -7.3208% | -9.2798% |
| parent baseline | 32 | +2.7904% | +2.9900% | -7.3208% | -10.0732% |

A better rank is not a verified improvement. Allshort24's7-day tail is worse despite a higher average.
CS and drawdown are in the CSV. No short-only profitability F1 or clone-agreement statistic is inferred from
whole-book return. The existing frozen short-only and clone studies remain separate and unchanged.
--score updates the original primary board; this separate diagnostic is refreshed by this study's publisher,
not automatically for every future model.

## Evidence and reproduction
Core source ea93ce2 on feature/book-rebound-recovery, Book's remote worktree.
Results: /home/ubuntu/test/MiniMax/results/book/20261011-rebound-recovery-v1
Immutable current table: /home/ubuntu/test/MiniMax/results/book/20261011-rebound-current-context-v1
First read decision.base.json and comparison.base.csv.
285 tests PASS. Seven focused money/risk/causality tests preceded implementation.
independent_audit.json reconstructs 41,364 model/horizon outcomes with zero return/drawdown/CS error.
real_bar_causality_audit.json checks 12 registered decisions on real data for future invisibility, risk and gross limits.
Publication independently checks new raw results, unchanged 131 previous model summaries, hashes and original score2.
The near-high study's uncached baseline replay matched all numerical arrays and windows/targets/trades exactly.

From THIS worktree, reproduce the frozen historical cohort with:
.venv/bin/python -B -m research.book.rebound_recovery.run
Then run_tests, audit and publish_review in that order.
No original engine, harness, scorer, baseline model, live config, service or main checkout was changed.
The original baseline simulator can drift above 100% marked gross between rebalances despite bounded targets.
Actual EC2 positions/deployment, live feed, endgame and same-account switch performance remain UNVERIFIED.

## Future evidence
Before these two guards' historical outcomes were read, all thirteen models (baseline plus twelve recovery
hypotheses) were frozen for Oct 12 00 UTC to Oct 15 00 UTC,08 HKT to08 HKT.
Every candidate is included; no future cohort selection based on winning this batch.
Sources, parameters, costs, spreads and endpoint are hashed. No partial returns are produced.
The seven clock-integrity checks pass; preflight is WAITING for complete data.
Run .venv/bin/python -B -m research.book.rebound_recovery.forward from THIS worktree only after data is complete.
No automatic run or scheduled job was created. One 3-day future path cannot statistically certify a live upgrade.
Both earlier future worktrees/cohorts remain untouched. This common cohort overlaps their periods and is not an
independent replicate of those paths.
Do not edit this worktree's runtime/config/forward files. Further research needs another Book feature worktree.
