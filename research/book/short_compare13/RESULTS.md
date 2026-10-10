# Combined short leaderboard: thirteen comparable hourly models

Read Evidence first. All thirteen fail the reliable-profit checks; rank 1 is an experiment priority, not a validated live replacement. Clone trade agreement is a separate objective. This table reuses 7,995 audited outcomes from four completed cohorts; it performs no new fitting or trade replay. The shared guard is counted once and all 615 control ledgers reproduced exactly across the cohorts.

All rows use the same 25 archive lookalikes, 228-hour cash-start portfolios, 25% gross / 10% coin intended caps, hourly decisions, one-hour lag, 0.10% fees and 0.05% halfspread each side. Recent-BTC lookalikes, 216/240-hour horizons, doubled costs and two-hour lag remain in the files. All 25 cases, including cash and later rebounds, count. Realised exposure can differ. The 228-hour horizon was frozen earlier; it is not the remaining competition time today.

Conservative rank sorts the worst of six profile/horizon quarter-cluster lower bounds on mean return, using 20,000 resamples and the same 27-hypothesis correction for every row. Completed accuracy is net-profitable fully closed short episodes / completed episodes, including partial covers within an episode. Forced endpoint closes are censored from accuracy and included in return with full closing costs. Accuracy rank sorts the worst-profile 90% lower bound at 228 hours. Return rank sorts archive mean return. CS retains 0.4 Sortino + 0.3 Sharpe + 0.3 Calmar; MDD uses minute equity.

| Rank | Model | Lower return | Return rank | Mean return | Median | P10 | Worst | Wins/closed | Accuracy | Accuracy rank | Censored | MDD | CS | Mean gross | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | book_short_shock_fade | -0.067% | 1 | +0.017% | +0.000% | -0.064% | -0.163% | 11/19 | 57.89% | 3 | 3 | 0.06% | 0.012 | 0.10% | FAIL |
| 2 | book_short_volume_fade | -0.072% | 2 | -0.004% | +0.000% | -0.112% | -0.249% | 21/39 | 53.85% | 2 | 3 | 0.12% | -0.003 | 0.24% | FAIL |
| 3 | book_short_range_fail | -0.079% | 3 | -0.005% | +0.000% | -0.158% | -0.243% | 30/52 | 57.69% | 1 | 2 | 0.11% | -0.005 | 0.27% | FAIL |
| 4 | book_short_ridge6 | -0.105% | 4 | -0.017% | +0.000% | -0.024% | -0.309% | 7/31 | 22.58% | 12 | 0 | 0.06% | -0.008 | 0.06% | FAIL |
| 5 | book_bear_pullback | -0.309% | 7 | -0.143% | -0.145% | -0.375% | -0.649% | 44/234 | 18.80% | 11 | 2 | 0.45% | -0.114 | 1.26% | FAIL |
| 6 | book_short_analogue12 | -0.330% | 6 | -0.131% | -0.094% | -0.345% | -0.794% | 108/345 | 31.30% | 4 | 8 | 0.22% | -0.080 | 0.55% | FAIL |
| 7 | book_short_analogue6 | -0.350% | 5 | -0.078% | -0.016% | -0.225% | -1.237% | 29/113 | 25.66% | 6 | 1 | 0.15% | -0.033 | 0.15% | FAIL |
| 8 | book_bear_breakdown | -0.431% | 8 | -0.155% | -0.196% | -0.599% | -0.880% | 124/454 | 27.31% | 7 | 18 | 0.58% | -0.115 | 2.45% | FAIL |
| 9 | book_bear_cost_guard | -0.500% | 10 | -0.274% | -0.337% | -0.552% | -0.857% | 147/587 | 25.04% | 9 | 23 | 0.67% | -0.179 | 2.71% | FAIL |
| 10 | book_bear_guard | -0.566% | 11 | -0.357% | -0.368% | -0.677% | -0.962% | 179/775 | 23.10% | 10 | 24 | 0.75% | -0.219 | 2.90% | FAIL |
| 11 | book_bear_trend_control | -0.671% | 9 | -0.265% | -0.270% | -0.972% | -1.280% | 66/517 | 12.77% | 13 | 36 | 0.97% | -0.168 | 5.90% | FAIL |
| 12 | book_bear_trail_exit | -0.756% | 12 | -0.399% | -0.332% | -0.760% | -1.961% | 164/654 | 25.08% | 8 | 19 | 0.73% | -0.213 | 2.48% | FAIL |
| 13 | book_bear_fast_exit | -1.081% | 13 | -0.651% | -0.525% | -1.136% | -2.147% | 243/969 | 25.08% | 5 | 6 | 0.84% | -0.324 | 1.66% | FAIL |

Evidence requires all six lower return bounds > 0, at least 30 completed episodes, 12 quarters and 12 firing windows in each context, positive doubled-cost mean, nonnegative median and positive-control mean >= -1%. Thresholds were not relaxed. Retrospective passes would still need future evaluation. Full model definitions and individual ledgers remain in the four source cohorts.

## Short entry timing, ranked separately

These labels start at the first simulated executed short fill after lag/band/rounding. They hypothetically hold that entry unchanged for 1/3/6 hours and charge entry/exit fees and spread, regardless of the strategy actual exit. They measure entry timing rather than completed-strategy profit. Horizons outside the window are censored. The descriptive rank uses 6-hour accuracy; it does not change the evidence flag.

| 6h rank | Model | Firing windows | 1h wins/n | 3h wins/n | 6h wins/n | 6h accuracy | 6h mean after-cost mark | 6h censored |
|---|---|---|---|---|---|---|---|---|
| 1 | book_short_shock_fade | 11/25 | 7/20 | 10/19 | 9/19 | 47.37% | +0.363% | 3 |
| 2 | book_short_range_fail | 16/25 | 20/54 | 26/53 | 24/52 | 46.15% | -0.175% | 2 |
| 3 | book_short_ridge6 | 8/25 | 10/31 | 11/31 | 14/31 | 45.16% | +0.163% | 0 |
| 4 | book_short_volume_fade | 16/25 | 9/42 | 17/40 | 17/39 | 43.59% | +0.092% | 3 |
| 5 | book_short_analogue12 | 23/25 | 82/353 | 127/347 | 137/345 | 39.71% | -0.154% | 8 |
| 6 | book_bear_breakdown | 25/25 | 115/472 | 144/472 | 172/464 | 37.07% | -0.249% | 8 |
| 7 | book_bear_trail_exit | 25/25 | 155/673 | 206/672 | 236/658 | 35.87% | -0.308% | 15 |
| 8 | book_bear_cost_guard | 25/25 | 138/610 | 185/610 | 213/596 | 35.74% | -0.312% | 14 |
| 9 | book_bear_fast_exit | 25/25 | 234/972 | 297/968 | 328/955 | 34.35% | -0.310% | 20 |
| 10 | book_short_analogue6 | 20/25 | 29/114 | 46/114 | 38/113 | 33.63% | -0.549% | 1 |
| 11 | book_bear_guard | 25/25 | 180/799 | 223/798 | 255/785 | 32.48% | -0.377% | 14 |
| 12 | book_bear_trend_control | 25/25 | 110/552 | 155/550 | 175/544 | 32.17% | -0.297% | 9 |
| 13 | book_bear_pullback | 24/25 | 52/236 | 77/236 | 75/235 | 31.91% | -0.314% | 1 |

## When the historical market subsequently fell, rebounded or stayed neutral

Future BTC 240-hour return labels: down <= -2%, rebound >= +2%, neutral between. Strategy outcomes still use the 228-hour endpoint. These labels use future information and are diagnostic only: they never select the main windows, enter strategies, change the main rank or estimate the next market direction. Conditional ranks alone must not select a live model.

### future_down

| Conditional return rank | Model | Windows | Mean return | Wins/closed | Accuracy | MDD | CS |
|---|---|---|---|---|---|---|---|
| 1 | book_bear_trend_control | 7 | +0.369% | 34/150 | 22.67% | 1.30% | 0.103 |
| 2 | book_bear_breakdown | 7 | +0.162% | 67/174 | 38.51% | 0.88% | 0.065 |
| 3 | book_short_shock_fade | 7 | +0.053% | 5/8 | 62.50% | 0.12% | 0.036 |
| 4 | book_bear_pullback | 7 | +0.033% | 18/80 | 22.50% | 0.73% | -0.029 |
| 5 | book_short_range_fail | 7 | +0.024% | 15/27 | 55.56% | 0.20% | 0.011 |
| 6 | book_short_volume_fade | 7 | +0.018% | 8/15 | 53.33% | 0.21% | 0.010 |
| 7 | book_short_ridge6 | 7 | -0.047% | 3/14 | 21.43% | 0.15% | -0.017 |
| 8 | book_bear_cost_guard | 7 | -0.117% | 76/227 | 33.48% | 1.01% | -0.093 |
| 9 | book_short_analogue6 | 7 | -0.234% | 14/55 | 25.45% | 0.35% | -0.083 |
| 10 | book_bear_guard | 7 | -0.242% | 83/298 | 27.85% | 1.09% | -0.149 |
| 11 | book_short_analogue12 | 7 | -0.258% | 42/116 | 36.21% | 0.37% | -0.132 |
| 12 | book_bear_trail_exit | 7 | -0.406% | 87/256 | 33.98% | 1.13% | -0.130 |
| 13 | book_bear_fast_exit | 7 | -0.986% | 124/411 | 30.17% | 1.37% | -0.363 |

### future_rebound

| Conditional return rank | Model | Windows | Mean return | Wins/closed | Accuracy | MDD | CS |
|---|---|---|---|---|---|---|---|
| 1 | book_short_shock_fade | 13 | +0.018% | 5/7 | 71.43% | 0.03% | 0.014 |
| 2 | book_short_volume_fade | 13 | -0.007% | 10/17 | 58.82% | 0.09% | -0.005 |
| 3 | book_short_ridge6 | 13 | -0.009% | 1/4 | 25.00% | 0.02% | -0.007 |
| 4 | book_short_analogue6 | 13 | -0.017% | 12/45 | 26.67% | 0.08% | -0.014 |
| 5 | book_short_range_fail | 13 | -0.031% | 9/17 | 52.94% | 0.08% | -0.022 |
| 6 | book_short_analogue12 | 13 | -0.058% | 57/153 | 37.25% | 0.16% | -0.045 |
| 7 | book_bear_pullback | 13 | -0.183% | 25/115 | 21.74% | 0.35% | -0.127 |
| 8 | book_bear_breakdown | 13 | -0.232% | 47/209 | 22.49% | 0.47% | -0.154 |
| 9 | book_bear_cost_guard | 13 | -0.334% | 57/275 | 20.73% | 0.56% | -0.204 |
| 10 | book_bear_guard | 13 | -0.392% | 78/347 | 22.48% | 0.64% | -0.233 |
| 11 | book_bear_trail_exit | 13 | -0.414% | 60/305 | 19.67% | 0.60% | -0.248 |
| 12 | book_bear_trend_control | 13 | -0.461% | 28/272 | 10.29% | 0.85% | -0.237 |
| 13 | book_bear_fast_exit | 13 | -0.576% | 96/435 | 22.07% | 0.70% | -0.328 |

### future_neutral

| Conditional return rank | Model | Windows | Mean return | Wins/closed | Accuracy | MDD | CS |
|---|---|---|---|---|---|---|---|
| 1 | book_short_range_fail | 5 | +0.021% | 6/8 | 75.00% | 0.04% | 0.016 |
| 2 | book_short_ridge6 | 5 | +0.002% | 3/13 | 23.08% | 0.03% | 0.002 |
| 3 | book_short_analogue6 | 5 | -0.019% | 3/13 | 23.08% | 0.03% | -0.014 |
| 4 | book_short_volume_fade | 5 | -0.023% | 3/7 | 42.86% | 0.06% | -0.018 |
| 5 | book_short_shock_fade | 5 | -0.036% | 1/4 | 25.00% | 0.04% | -0.028 |
| 6 | book_short_analogue12 | 5 | -0.140% | 9/76 | 11.84% | 0.18% | -0.100 |
| 7 | book_bear_pullback | 5 | -0.286% | 1/39 | 2.56% | 0.31% | -0.201 |
| 8 | book_bear_cost_guard | 5 | -0.338% | 14/85 | 16.47% | 0.48% | -0.231 |
| 9 | book_bear_trail_exit | 5 | -0.351% | 17/93 | 18.28% | 0.49% | -0.239 |
| 10 | book_bear_fast_exit | 5 | -0.378% | 23/123 | 18.70% | 0.46% | -0.259 |
| 11 | book_bear_breakdown | 5 | -0.399% | 10/71 | 14.08% | 0.42% | -0.266 |
| 12 | book_bear_guard | 5 | -0.426% | 18/130 | 13.85% | 0.55% | -0.281 |
| 13 | book_bear_trend_control | 5 | -0.640% | 4/95 | 4.21% | 0.80% | -0.367 |

## Read and reproduce

leaderboard_short.csv has the primary ranks; entry_accuracy_1h_3h_6h.csv has both timing profiles; scenario_summary.csv retains all conditional groups and profiles; profile_summary.csv contains all six contexts. window_results.csv retains every unique outcome. manifest.json pins all four parent reports, audit proofs, inputs and outputs. This presentation does not combine the earlier minute-exit or 100%-gross cohorts as equal-protocol models.

Normal registered-model scoring remains .venv/bin/python -B -m backtest.run --model MODEL --score2 in Book worktree, which automatically updates /home/ubuntu/test/MiniMax/results/scoring/leaderboard_2.md. The combined frozen study is a separate cohort and does not automatically admit a new model. A new strategy needs a new frozen batch with the same cases/execution and appropriate expanded hypothesis adjustment before joining a new combined version. This report can be generated once with .venv/bin/python -B -m research.book.short_compare13.combine --score; publication refuses overwrite.

All history is spent research. Supplemental replay omits the daily activity guard; normal --score2 includes it. Historical spreads are proxies. Archived modern coin selection and present precision rules limit inference. The adaptive BCH-absent 29/30 coverage failure remains unchanged. No main merge, competition API or live bot change occurred.
