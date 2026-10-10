# Selective short entries and rebound exits

Version2 corrects the endpoint-batch eligibility issue; v1 failed diagnostics and partial results are preserved. Normal --score2 results are reused only after model-source, parameter and published-artifact hash checks. Entire batches starting at/after the endpoint are pending, not partly executed.

No model clears all reliable-improvement checks. These are research ranks; live switching remains unsupported.

Read **Evidence** first, then **Return**, **Short wins/closed**, **Accuracy**, **P10/Worst**, **MDD** and **CS**. Rank1 alone is not a recommendation. The clone's85%trade agreement is a separate objective.

All four candidates use the same25%gross/10%coin caps,1%conservative daily-risk cap,hourly decisions,1h execution lag and1pp rebalance band. Trend control uses a simple negative EMA6/24forecast. Guard adds a BTC96h/breadth bear gate, held-position hysteresis and rebound exits. Pullback additionally requires a3h bounce and latest-hour rejection; breakdown requires a new12h close low without excessive extension. An existing selective short may shrink but cannot be added to until flat. Cash is a valid decision.

The main rows average ALL25archive-weak windows of228hours(9.5days) from cash100k, including inactive cases. Recent-BTC lookalikes and216/240h horizons are additional fixed checks. These start-information-selected windows include later rebounds, not only falling markets. The228hperiod is a frozen benchmark, not today's remaining competition time. All history is spent retrospective research.

A completed short episode runs from flat to short to flat, aggregating partial covers. It is correct only if net profit after fees and spread is positive. Accuracy=wins/completed; open episodes are censored from accuracy but included at full closing cost in return. Tiny sample accuracy cannot establish reliability. The main scoreboard's1/3/6h onset precision is a separate fixed-horizon proxy.

Conservative rank sorts the worst of six profile/horizon quarter-cluster lower bounds on mean return. Bootstrap20000 and simultaneous adjustment use18declared short hypotheses(previous8minute+6price+these4); repeated earlier research still limits inference. Accuracy rank uses the worst-profile90%interval lower bound at228h. Return rank sorts mean portfolio return. P10 and Worst describe losses; MDD is minute peak-to-trough loss; CS keeps0.4Sortino+0.3Sharpe+0.3Calmar. Mean gross is realised exposure, which can differ despite identical caps.

| Rank | Model | Lower return | Return | Median | P10 | Worst | Short wins/closed | Accuracy | Accuracy rank | Censored | MDD | CS | Mean gross | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | book_bear_pullback | -0.307% | -0.143% | -0.145% | -0.375% | -0.649% | 44/234 | 18.803% | 3 | 2 | 0.450% | -0.114 | 1.261% | FAIL |
| 2 | book_bear_breakdown | -0.422% | -0.155% | -0.196% | -0.599% | -0.880% | 124/454 | 27.313% | 1 | 18 | 0.577% | -0.115 | 2.453% | FAIL |
| 3 | book_bear_guard | -0.562% | -0.357% | -0.368% | -0.677% | -0.962% | 179/775 | 23.097% | 2 | 24 | 0.746% | -0.219 | 2.898% | FAIL |
| 4 | book_bear_trend_control | -0.655% | -0.265% | -0.270% | -0.972% | -1.280% | 66/517 | 12.766% | 4 | 36 | 0.969% | -0.168 | 5.902% | FAIL |

The unchanged evidence checks require every profile/horizon lower bound>0,at least30completed shorts,12quarters and12firing windows, positive doubled-cost mean, nonnegative median and positive-control mean>=-1%. No thresholds were loosened. paired_control.csv shows within-window return differences from the equal-risk control; absolute profit and normal --score2 incumbent comparisons must also pass.

## When historical prices actually fell or rebounded

These conditional labels are diagnostic only: future240hBTCreturn<=-2% is down and>=+2% is rebound. Returns here remain the main228hportfolio endpoint. They do not select training windows, enter targets, alter the main rank or prove the next market direction. Neutral cases remain included in the full25windowtable. Small subgroup results are weaker evidence.

| Future case | Model | Windows | Mean return | P10 | Worst | Net wins/closed | Accuracy | MDD | CS |
|---|---|---|---|---|---|---|---|---|---|
| future_down | book_bear_trend_control | 7 | +0.369% | -0.224% | -0.232% | 34/150 | 22.667% | 1.305% | 0.103 |
| future_down | book_bear_guard | 7 | -0.242% | -0.557% | -0.574% | 83/298 | 27.852% | 1.093% | -0.149 |
| future_down | book_bear_pullback | 7 | +0.033% | -0.354% | -0.369% | 18/80 | 22.500% | 0.733% | -0.029 |
| future_down | book_bear_breakdown | 7 | +0.162% | -0.482% | -0.685% | 67/174 | 38.506% | 0.884% | 0.065 |
| future_rebound | book_bear_trend_control | 13 | -0.461% | -0.975% | -1.280% | 28/272 | 10.294% | 0.854% | -0.237 |
| future_rebound | book_bear_guard | 13 | -0.392% | -0.690% | -0.962% | 78/347 | 22.478% | 0.635% | -0.233 |
| future_rebound | book_bear_pullback | 13 | -0.183% | -0.374% | -0.579% | 25/115 | 21.739% | 0.350% | -0.127 |
| future_rebound | book_bear_breakdown | 13 | -0.232% | -0.437% | -0.668% | 47/209 | 22.488% | 0.472% | -0.154 |

Both profiles are retained in scenario_summary.csv.

## Early competition prefix: already used

October4 20:00HKT to October9 08:00HKT,100kseed. These conditional results do not provide held-out evidence.

| Model | Full return | MDD | Wins/closed | Censored | Net short USD | Orders |
|---|---|---|---|---|---|---|
| book_bear_trend_control | +0.891% | 0.705% | 1/8 | 4 | 891.27 | 51 |
| book_bear_guard | +0.291% | 0.475% | 4/11 | 3 | 290.84 | 25 |
| book_bear_pullback | +0.421% | 0.367% | 4/6 | 2 | 421.49 | 14 |
| book_bear_breakdown | +0.349% | 0.487% | 4/8 | 3 | 348.51 | 19 |

Earlier observed reference+5.2196%and prior clone+4.8661%use this common endpoint but different five-coin holdings and execution assumptions. They are conditional references, not equivalent-risk measurements.

Actual executed-entry timing has a separate table: entry_accuracy.md and entry_accuracy_1h_3h_6h.csv. It ranks fixed1/3/6h after-cost marks from simulated first fills, with endpoint censoring. This is distinct from completed-trade accuracy and the main hourly target-onset proxy.

## Files and reruns

leaderboard_short.csv has ranks. profile_summary.csv retains all six contexts and cost stress. window_results.csv contains every ledger outcome; cases.parquet gives checkpoint dates; paired_control.csv compares each model with the equal-risk trend control. cases/ contains full events, cycles and minute equity. independent_execution_audit.json checks accounting; evaluation_before/after.json pins source/data; status.json records tests and normal-score jobs.

From /home/ubuntu/test/MiniMax/.worktrees/book-book-short-exit run .venv/bin/python -B -m backtest.run --model MODEL --score2 for automatic entry in /home/ubuntu/test/MiniMax/results/scoring/leaderboard_2.md. Rebuild this frozen report with .venv/bin/python -B -m research.book.bear_selective.score --score. The full batch refuses overwrite; new hypotheses need a new version. Normal --score2 includes the daily activity guard; this supplemental replay omits it. Both use the shared planner/PaperBroker. Historical minute execution prices here use0.05%halfspread proxies and0.10%fees each side; doubled-cost and2h lag runs are retained.

Source data limitations include the fixed modern four-coin cohort and current precision rules, proxy archive spreads, and the absence of the live account's inherited holdings. All adaptive gates remain unchanged, including BCHabsent29/30coverage. No main merge, signed API action or live bot change occurred.
