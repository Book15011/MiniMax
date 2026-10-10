# Purged historical-state short forecasts

This new cohort uses the corrected strict endpoint rule; prior selective v1 failures remain preserved. Entire batches starting at/after the endpoint are pending, not partly executed. The unchanged guard control is reused in normal scoring only after source/parameter/artifact verification.

No model clears all reliable-improvement checks. These are research ranks; live switching remains unsupported.

Read **Evidence** first, then **Return**, **Short wins/closed**, **Accuracy**, **P10/Worst**, **MDD** and **CS**. Rank1 alone is not a recommendation. The clone's85%trade agreement is a separate objective.

The unchanged guard is compared with three fixed past-state forecasts: analogue6h, analogue12h and ridge6h. Each hourly fit uses only matured lagged outcomes from the prior60days. Signals estimate after-cost unit short returns from own-price/volatility/BTC-state features. Entry needs a0.15%expected net mark and55%estimated profitable fraction. These estimates are not calibrated probabilities. Intended held shorts only shrink; forecasts below the fixed exit hurdle close. Same25%gross/10%coin and1%daily-risk caps apply. Actual lagged full-strategy outcomes remain separate from the training labels.

The main rows average ALL25archive-weak windows of228hours(9.5days) from cash100k, including inactive cases. Recent-BTC lookalikes and216/240h horizons are additional fixed checks. These start-information-selected windows include later rebounds, not only falling markets. The228hperiod is a frozen benchmark, not today's remaining competition time. All history is spent retrospective research.

A completed short episode runs from flat to short to flat, aggregating partial covers. It is correct only if net profit after fees and spread is positive. Accuracy=wins/completed; open episodes are censored from accuracy but included at full closing cost in return. Tiny sample accuracy cannot establish reliability. The main scoreboard's1/3/6h onset precision is a separate fixed-horizon proxy.

Conservative rank sorts the worst of six profile/horizon quarter-cluster lower bounds on mean return. Bootstrap20000 and simultaneous adjustment use24declared short hypotheses(previous8minute+6price+4selective+3exit+these3forecast); repeated earlier research still limits inference. Accuracy rank uses the worst-profile90%interval lower bound at228h. Return rank sorts mean portfolio return. P10 and Worst describe losses; MDD is minute peak-to-trough loss; CS keeps0.4Sortino+0.3Sharpe+0.3Calmar. Mean gross is realised exposure, which can differ despite identical caps.

| Rank | Model | Lower return | Return | Median | P10 | Worst | Short wins/closed | Accuracy | Accuracy rank | Censored | MDD | CS | Mean gross | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | book_short_ridge6 | -0.105% | -0.017% | +0.000% | -0.024% | -0.309% | 7/31 | 22.581% | 4 | 0 | 0.056% | -0.008 | 0.065% | FAIL |
| 2 | book_short_analogue12 | -0.324% | -0.131% | -0.094% | -0.345% | -0.794% | 108/345 | 31.304% | 1 | 8 | 0.225% | -0.080 | 0.554% | FAIL |
| 3 | book_short_analogue6 | -0.344% | -0.078% | -0.016% | -0.225% | -1.237% | 29/113 | 25.664% | 2 | 1 | 0.146% | -0.033 | 0.153% | FAIL |
| 4 | book_bear_guard | -0.566% | -0.357% | -0.368% | -0.677% | -0.962% | 179/775 | 23.097% | 3 | 24 | 0.746% | -0.219 | 2.898% | FAIL |

The unchanged guard benchmark must first reproduce all615 prior corrected ledgers byte-for-byte (events, cycles, minute path and endpoint). See control_reproduction_audit.json. The unchanged evidence checks require every profile/horizon lower bound>0,at least30completed shorts,12quarters and12firing windows, positive doubled-cost mean, nonnegative median and positive-control mean>=-1%. No thresholds were loosened. paired_control.csv shows within-window return differences from the equal-risk control; absolute profit and normal --score2 incumbent comparisons must also pass.

## When historical prices actually fell or rebounded

These conditional labels are diagnostic only: future240hBTCreturn<=-2% is down and>=+2% is rebound. Returns here remain the main228hportfolio endpoint. They do not select training windows, enter targets, alter the main rank or prove the next market direction. Neutral cases remain included in the full25windowtable. Small subgroup results are weaker evidence.

| Future case | Model | Windows | Mean return | P10 | Worst | Net wins/closed | Accuracy | MDD | CS |
|---|---|---|---|---|---|---|---|---|---|
| future_down | book_bear_guard | 7 | -0.242% | -0.557% | -0.574% | 83/298 | 27.852% | 1.093% | -0.149 |
| future_down | book_short_analogue6 | 7 | -0.234% | -0.642% | -1.237% | 14/55 | 25.455% | 0.354% | -0.083 |
| future_down | book_short_analogue12 | 7 | -0.258% | -0.660% | -0.794% | 42/116 | 36.207% | 0.374% | -0.132 |
| future_down | book_short_ridge6 | 7 | -0.047% | -0.136% | -0.309% | 3/14 | 21.429% | 0.148% | -0.017 |
| future_rebound | book_bear_guard | 13 | -0.392% | -0.690% | -0.962% | 78/347 | 22.478% | 0.635% | -0.233 |
| future_rebound | book_short_analogue6 | 13 | -0.017% | -0.177% | -0.241% | 12/45 | 26.667% | 0.079% | -0.014 |
| future_rebound | book_short_analogue12 | 13 | -0.058% | -0.167% | -0.200% | 57/153 | 37.255% | 0.161% | -0.045 |
| future_rebound | book_short_ridge6 | 13 | -0.009% | -0.025% | -0.079% | 1/4 | 25.000% | 0.016% | -0.007 |

Both profiles are retained in scenario_summary.csv.

## Early competition prefix: already used

October4 20:00HKT to October9 08:00HKT,100kseed. These conditional results do not provide held-out evidence.

| Model | Full return | MDD | Wins/closed | Censored | Net short USD | Orders |
|---|---|---|---|---|---|---|
| book_bear_guard | +0.291% | 0.475% | 4/11 | 3 | 290.84 | 25 |
| book_short_analogue6 | -0.012% | 0.028% | 0/3 | 0 | -11.81 | 6 |
| book_short_analogue12 | +0.000% | -0.000% | 0/0 | 0 | 0.00 | 0 |
| book_short_ridge6 | +0.000% | -0.000% | 0/0 | 0 | 0.00 | 0 |

Earlier observed reference+5.2196%and prior clone+4.8661%use this common endpoint but different five-coin holdings and execution assumptions. They are conditional references, not equivalent-risk measurements.

Actual executed-entry timing has a separate table: entry_accuracy.md and entry_accuracy_1h_3h_6h.csv. It ranks fixed1/3/6h after-cost marks from simulated first fills, with endpoint censoring. This is distinct from completed-trade accuracy and the main hourly target-onset proxy.

## Files and reruns

leaderboard_short.csv has ranks. profile_summary.csv retains all six contexts and cost stress. window_results.csv contains every ledger outcome; cases.parquet gives checkpoint dates; paired_control.csv compares each model with the equal-risk guard control. cases/ contains full events, cycles and minute equity. independent_execution_audit.json checks accounting; evaluation_before/after.json pins source/data; status.json records tests and normal-score jobs.

From /home/ubuntu/test/MiniMax/.worktrees/book-book-bear-exit run .venv/bin/python -B -m backtest.run --model MODEL --score2 for automatic entry in /home/ubuntu/test/MiniMax/results/scoring/leaderboard_2.md. Rebuild this frozen report with .venv/bin/python -B -m research.book.short_forecast.score --score. The full batch refuses overwrite; new hypotheses need a new version. Normal --score2 includes the daily activity guard; this supplemental replay omits it. Both use the shared planner/PaperBroker. Historical minute execution prices here use0.05%halfspread proxies and0.10%fees each side; doubled-cost and2h lag runs are retained.

Source data limitations include the fixed modern four-coin cohort and current precision rules, proxy archive spreads, and the absence of the live account's inherited holdings. All adaptive gates remain unchanged, including BCHabsent29/30coverage. No main merge, signed API action or live bot change occurred.
