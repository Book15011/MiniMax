# Combined short leaderboard: seven comparable hourly models

Read Evidence first. All seven fail the reliable-profit checks; rank 1 is an experiment priority, not a validated live replacement. Clone trade agreement is a separate objective. This table reuses 4,305 audited outcomes from two completed cohorts; it performs no new fitting or trade replay. The shared guard is counted once and all 615 control ledgers reproduced exactly across the cohorts.

All rows use the same 25 archive lookalikes, 228-hour cash-start portfolios, 25% gross / 10% coin intended caps, hourly decisions, one-hour lag, 0.10% fees and 0.05% halfspread each side. Recent-BTC lookalikes, 216/240-hour horizons, doubled costs and two-hour lag remain in the files. All 25 cases, including cash and later rebounds, count. Realised exposure can differ. The 228-hour horizon was frozen earlier; it is not the remaining competition time today.

Conservative rank sorts the worst of six profile/horizon quarter-cluster lower bounds on mean return, using 20,000 resamples and the same 21-hypothesis correction for every row. Completed accuracy is net-profitable fully closed short episodes / completed episodes, including partial covers within an episode. Forced endpoint closes are censored from accuracy and included in return with full closing costs. Accuracy rank sorts the worst-profile 90% lower bound at 228 hours. Return rank sorts archive mean return. CS retains 0.4 Sortino + 0.3 Sharpe + 0.3 Calmar; MDD uses minute equity.

| Rank | Model | Lower return | Return rank | Mean return | Median | P10 | Worst | Wins/closed | Accuracy | Accuracy rank | Censored | MDD | CS | Mean gross | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | book_bear_pullback | -0.307% | 1 | -0.143% | -0.145% | -0.375% | -0.649% | 44/234 | 18.80% | 6 | 2 | 0.45% | -0.114 | 1.26% | FAIL |
| 2 | book_bear_breakdown | -0.426% | 2 | -0.155% | -0.196% | -0.599% | -0.880% | 124/454 | 27.31% | 2 | 18 | 0.58% | -0.115 | 2.45% | FAIL |
| 3 | book_bear_cost_guard | -0.495% | 4 | -0.274% | -0.337% | -0.552% | -0.857% | 147/587 | 25.04% | 4 | 23 | 0.67% | -0.179 | 2.71% | FAIL |
| 4 | book_bear_guard | -0.565% | 5 | -0.357% | -0.368% | -0.677% | -0.962% | 179/775 | 23.10% | 5 | 24 | 0.75% | -0.219 | 2.90% | FAIL |
| 5 | book_bear_trend_control | -0.661% | 3 | -0.265% | -0.270% | -0.972% | -1.280% | 66/517 | 12.77% | 7 | 36 | 0.97% | -0.168 | 5.90% | FAIL |
| 6 | book_bear_trail_exit | -0.747% | 6 | -0.399% | -0.332% | -0.760% | -1.961% | 164/654 | 25.08% | 3 | 19 | 0.73% | -0.213 | 2.48% | FAIL |
| 7 | book_bear_fast_exit | -1.078% | 7 | -0.651% | -0.525% | -1.136% | -2.147% | 243/969 | 25.08% | 1 | 6 | 0.84% | -0.324 | 1.66% | FAIL |

Evidence requires all six lower return bounds > 0, at least 30 completed episodes, 12 quarters and 12 firing windows in each context, positive doubled-cost mean, nonnegative median and positive-control mean >= -1%. Thresholds were not relaxed. Retrospective passes would still need future evaluation. Full model definitions and individual ledgers remain in the two source cohorts.

## Short entry timing, ranked separately

These labels start at the first simulated executed short fill after lag/band/rounding. They hypothetically hold that entry unchanged for 1/3/6 hours and charge entry/exit fees and spread, regardless of the strategy actual exit. They measure entry timing rather than completed-strategy profit. Horizons outside the window are censored. The descriptive rank uses 6-hour accuracy; it does not change the evidence flag.

| 6h rank | Model | Firing windows | 1h wins/n | 3h wins/n | 6h wins/n | 6h accuracy | 6h mean after-cost mark | 6h censored |
|---|---|---|---|---|---|---|---|---|
| 1 | book_bear_breakdown | 25/25 | 115/472 | 144/472 | 172/464 | 37.07% | -0.249% | 8 |
| 2 | book_bear_trail_exit | 25/25 | 155/673 | 206/672 | 236/658 | 35.87% | -0.308% | 15 |
| 3 | book_bear_cost_guard | 25/25 | 138/610 | 185/610 | 213/596 | 35.74% | -0.312% | 14 |
| 4 | book_bear_fast_exit | 25/25 | 234/972 | 297/968 | 328/955 | 34.35% | -0.310% | 20 |
| 5 | book_bear_guard | 25/25 | 180/799 | 223/798 | 255/785 | 32.48% | -0.377% | 14 |
| 6 | book_bear_trend_control | 25/25 | 110/552 | 155/550 | 175/544 | 32.17% | -0.297% | 9 |
| 7 | book_bear_pullback | 24/25 | 52/236 | 77/236 | 75/235 | 31.91% | -0.314% | 1 |

## When the historical market subsequently fell, rebounded or stayed neutral

Future BTC 240-hour return labels: down <= -2%, rebound >= +2%, neutral between. Strategy outcomes still use the 228-hour endpoint. These labels use future information and are diagnostic only: they never select the main windows, enter strategies, change the main rank or estimate the next market direction. Conditional ranks alone must not select a live model.

### future_down

| Conditional return rank | Model | Windows | Mean return | Wins/closed | Accuracy | MDD | CS |
|---|---|---|---|---|---|---|---|
| 1 | book_bear_trend_control | 7 | +0.369% | 34/150 | 22.67% | 1.30% | 0.103 |
| 2 | book_bear_breakdown | 7 | +0.162% | 67/174 | 38.51% | 0.88% | 0.065 |
| 3 | book_bear_pullback | 7 | +0.033% | 18/80 | 22.50% | 0.73% | -0.029 |
| 4 | book_bear_cost_guard | 7 | -0.117% | 76/227 | 33.48% | 1.01% | -0.093 |
| 5 | book_bear_guard | 7 | -0.242% | 83/298 | 27.85% | 1.09% | -0.149 |
| 6 | book_bear_trail_exit | 7 | -0.406% | 87/256 | 33.98% | 1.13% | -0.130 |
| 7 | book_bear_fast_exit | 7 | -0.986% | 124/411 | 30.17% | 1.37% | -0.363 |

### future_rebound

| Conditional return rank | Model | Windows | Mean return | Wins/closed | Accuracy | MDD | CS |
|---|---|---|---|---|---|---|---|
| 1 | book_bear_pullback | 13 | -0.183% | 25/115 | 21.74% | 0.35% | -0.127 |
| 2 | book_bear_breakdown | 13 | -0.232% | 47/209 | 22.49% | 0.47% | -0.154 |
| 3 | book_bear_cost_guard | 13 | -0.334% | 57/275 | 20.73% | 0.56% | -0.204 |
| 4 | book_bear_guard | 13 | -0.392% | 78/347 | 22.48% | 0.64% | -0.233 |
| 5 | book_bear_trail_exit | 13 | -0.414% | 60/305 | 19.67% | 0.60% | -0.248 |
| 6 | book_bear_trend_control | 13 | -0.461% | 28/272 | 10.29% | 0.85% | -0.237 |
| 7 | book_bear_fast_exit | 13 | -0.576% | 96/435 | 22.07% | 0.70% | -0.328 |

### future_neutral

| Conditional return rank | Model | Windows | Mean return | Wins/closed | Accuracy | MDD | CS |
|---|---|---|---|---|---|---|---|
| 1 | book_bear_pullback | 5 | -0.286% | 1/39 | 2.56% | 0.31% | -0.201 |
| 2 | book_bear_cost_guard | 5 | -0.338% | 14/85 | 16.47% | 0.48% | -0.231 |
| 3 | book_bear_trail_exit | 5 | -0.351% | 17/93 | 18.28% | 0.49% | -0.239 |
| 4 | book_bear_fast_exit | 5 | -0.378% | 23/123 | 18.70% | 0.46% | -0.259 |
| 5 | book_bear_breakdown | 5 | -0.399% | 10/71 | 14.08% | 0.42% | -0.266 |
| 6 | book_bear_guard | 5 | -0.426% | 18/130 | 13.85% | 0.55% | -0.281 |
| 7 | book_bear_trend_control | 5 | -0.640% | 4/95 | 4.21% | 0.80% | -0.367 |

## Read and reproduce

leaderboard_short.csv has the primary ranks; entry_accuracy_1h_3h_6h.csv has both timing profiles; scenario_summary.csv retains all conditional groups and profiles; profile_summary.csv contains all six contexts. window_results.csv retains every unique outcome. manifest.json pins both parent reports, audit proofs, inputs and outputs. This presentation does not combine the earlier minute-exit or 100%-gross cohorts as equal-protocol models.

Normal registered-model scoring remains .venv/bin/python -B -m backtest.run --model MODEL --score2 in Book worktree, which automatically updates /home/ubuntu/test/MiniMax/results/scoring/leaderboard_2.md. The combined frozen study is a separate cohort and does not automatically admit a new model. A new strategy needs a new frozen batch with the same cases/execution and appropriate expanded hypothesis adjustment before joining a new combined version. This report can be generated once with .venv/bin/python -B -m research.book.bear_exit.combine --score; publication refuses overwrite.

All history is spent research. Supplemental replay omits the daily activity guard; normal --score2 includes it. Historical spreads are proxies. Archived modern coin selection and present precision rules limit inference. The adaptive BCH-absent 29/30 coverage failure remains unchanged. No main merge, competition API or live bot change occurred.
