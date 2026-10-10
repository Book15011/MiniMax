# Cost-filtered short entries and faster exits

This new cohort uses the corrected strict endpoint rule; prior selective v1 failures remain preserved. Entire batches starting at/after the endpoint are pending, not partly executed. The unchanged guard control is reused in normal scoring only after source/parameter/artifact verification.

No model clears all reliable-improvement checks. These are research ranks; live switching remains unsupported.

Read **Evidence** first, then **Return**, **Short wins/closed**, **Accuracy**, **P10/Worst**, **MDD** and **CS**. Rank1 alone is not a recommendation. The clone's85%trade agreement is a separate objective.

The four rows compare the unchanged bearish guard with three fixed hypotheses under the same25%gross/10%coin caps,1%daily-risk cap,hourly decisions,1h lag and1pp band. Cost_guard requires a new entry's past6hdecline to exceed1.5times estimated roundtripcost. Fast_exit adds EMA3and2hreturn exits. Trail_exit adds a rebound exit from the previous12hclosed-price low. These are past-price conditions, not profit estimates or stops tied to actual entry fills. Held positions inherit the guard's shrink-only rule. Cash remains valid.

The main rows average ALL25archive-weak windows of228hours(9.5days) from cash100k, including inactive cases. Recent-BTC lookalikes and216/240h horizons are additional fixed checks. These start-information-selected windows include later rebounds, not only falling markets. The228hperiod is a frozen benchmark, not today's remaining competition time. All history is spent retrospective research.

A completed short episode runs from flat to short to flat, aggregating partial covers. It is correct only if net profit after fees and spread is positive. Accuracy=wins/completed; open episodes are censored from accuracy but included at full closing cost in return. Tiny sample accuracy cannot establish reliability. The main scoreboard's1/3/6h onset precision is a separate fixed-horizon proxy.

Conservative rank sorts the worst of six profile/horizon quarter-cluster lower bounds on mean return. Bootstrap20000 and simultaneous adjustment use21declared short hypotheses(previous8minute+6price+4selective+these3new); repeated earlier research still limits inference. Accuracy rank uses the worst-profile90%interval lower bound at228h. Return rank sorts mean portfolio return. P10 and Worst describe losses; MDD is minute peak-to-trough loss; CS keeps0.4Sortino+0.3Sharpe+0.3Calmar. Mean gross is realised exposure, which can differ despite identical caps.

| Rank | Model | Lower return | Return | Median | P10 | Worst | Short wins/closed | Accuracy | Accuracy rank | Censored | MDD | CS | Mean gross | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | book_bear_cost_guard | -0.495% | -0.274% | -0.337% | -0.552% | -0.857% | 147/587 | 25.043% | 3 | 23 | 0.673% | -0.179 | 2.710% | FAIL |
| 2 | book_bear_guard | -0.565% | -0.357% | -0.368% | -0.677% | -0.962% | 179/775 | 23.097% | 4 | 24 | 0.746% | -0.219 | 2.898% | FAIL |
| 3 | book_bear_trail_exit | -0.747% | -0.399% | -0.332% | -0.760% | -1.961% | 164/654 | 25.076% | 2 | 19 | 0.729% | -0.213 | 2.477% | FAIL |
| 4 | book_bear_fast_exit | -1.078% | -0.651% | -0.525% | -1.136% | -2.147% | 243/969 | 25.077% | 1 | 6 | 0.840% | -0.324 | 1.656% | FAIL |

The unchanged guard benchmark must first reproduce all615 prior corrected ledgers byte-for-byte (events, cycles, minute path and endpoint). See control_reproduction_audit.json. The unchanged evidence checks require every profile/horizon lower bound>0,at least30completed shorts,12quarters and12firing windows, positive doubled-cost mean, nonnegative median and positive-control mean>=-1%. No thresholds were loosened. paired_control.csv shows within-window return differences from the equal-risk control; absolute profit and normal --score2 incumbent comparisons must also pass.

## When historical prices actually fell or rebounded

These conditional labels are diagnostic only: future240hBTCreturn<=-2% is down and>=+2% is rebound. Returns here remain the main228hportfolio endpoint. They do not select training windows, enter targets, alter the main rank or prove the next market direction. Neutral cases remain included in the full25windowtable. Small subgroup results are weaker evidence.

| Future case | Model | Windows | Mean return | P10 | Worst | Net wins/closed | Accuracy | MDD | CS |
|---|---|---|---|---|---|---|---|---|---|
| future_down | book_bear_guard | 7 | -0.242% | -0.557% | -0.574% | 83/298 | 27.852% | 1.093% | -0.149 |
| future_down | book_bear_cost_guard | 7 | -0.117% | -0.457% | -0.545% | 76/227 | 33.480% | 1.012% | -0.093 |
| future_down | book_bear_fast_exit | 7 | -0.986% | -1.597% | -2.147% | 124/411 | 30.170% | 1.366% | -0.363 |
| future_down | book_bear_trail_exit | 7 | -0.406% | -1.082% | -1.961% | 87/256 | 33.984% | 1.132% | -0.130 |
| future_rebound | book_bear_guard | 13 | -0.392% | -0.690% | -0.962% | 78/347 | 22.478% | 0.635% | -0.233 |
| future_rebound | book_bear_cost_guard | 13 | -0.334% | -0.586% | -0.857% | 57/275 | 20.727% | 0.565% | -0.204 |
| future_rebound | book_bear_fast_exit | 13 | -0.576% | -0.955% | -1.165% | 96/435 | 22.069% | 0.704% | -0.328 |
| future_rebound | book_bear_trail_exit | 13 | -0.414% | -0.768% | -0.869% | 60/305 | 19.672% | 0.605% | -0.248 |

Both profiles are retained in scenario_summary.csv.

## Early competition prefix: already used

October4 20:00HKT to October9 08:00HKT,100kseed. These conditional results do not provide held-out evidence.

| Model | Full return | MDD | Wins/closed | Censored | Net short USD | Orders |
|---|---|---|---|---|---|---|
| book_bear_guard | +0.291% | 0.475% | 4/11 | 3 | 290.84 | 25 |
| book_bear_cost_guard | +0.265% | 0.490% | 4/10 | 3 | 264.84 | 24 |
| book_bear_fast_exit | -0.290% | 0.549% | 9/30 | 0 | -290.12 | 60 |
| book_bear_trail_exit | +0.201% | 0.485% | 8/17 | 0 | 201.41 | 35 |

Earlier observed reference+5.2196%and prior clone+4.8661%use this common endpoint but different five-coin holdings and execution assumptions. They are conditional references, not equivalent-risk measurements.

Actual executed-entry timing has a separate table: entry_accuracy.md and entry_accuracy_1h_3h_6h.csv. It ranks fixed1/3/6h after-cost marks from simulated first fills, with endpoint censoring. This is distinct from completed-trade accuracy and the main hourly target-onset proxy.

## Files and reruns

leaderboard_short.csv has ranks. profile_summary.csv retains all six contexts and cost stress. window_results.csv contains every ledger outcome; cases.parquet gives checkpoint dates; paired_control.csv compares each model with the equal-risk guard control. cases/ contains full events, cycles and minute equity. independent_execution_audit.json checks accounting; evaluation_before/after.json pins source/data; status.json records tests and normal-score jobs.

From /home/ubuntu/test/MiniMax/.worktrees/book-book-bear-exit run .venv/bin/python -B -m backtest.run --model MODEL --score2 for automatic entry in /home/ubuntu/test/MiniMax/results/scoring/leaderboard_2.md. Rebuild this frozen report with .venv/bin/python -B -m research.book.bear_exit.score --score. The full batch refuses overwrite; new hypotheses need a new version. Normal --score2 includes the daily activity guard; this supplemental replay omits it. Both use the shared planner/PaperBroker. Historical minute execution prices here use0.05%halfspread proxies and0.10%fees each side; doubled-cost and2h lag runs are retained.

Source data limitations include the fixed modern four-coin cohort and current precision rules, proxy archive spreads, and the absence of the live account's inherited holdings. All adaptive gates remain unchanged, including BCHabsent29/30coverage. No main merge, signed API action or live bot change occurred.
