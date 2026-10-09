# Ranked minute short-only research

No model passed the declared stronger-evidence rules. Rank 1 is a research priority, not a validated replacement.

Read rank as a conservative experiment order. 7 retained hypotheses; five initial mechanisms and two targeted persistent-exit follow-ups when present. Follow-ups were chosen after observing initial regime-clear churn; all observations remain spent. Selection bound = worst of six weak-profile/horizon lower mean-return bounds; quarter bootstrap with 20,000 draws with Bonferroni adjustment across 7 models x 6 contexts. A negative bound does not establish reliable positive return.

Accuracy rank separately sorts worst-profile lower 90% completed-cycle accuracy; return rank sorts worst-profile mean 228h native-exposure return. These two ranks are descriptive, not independent selection evidence. Main displayed counts/returns/risk use archive-full 25 windows at 228h. Full second-profile/horizon details are in profile_summary.csv.

A signal counts only when a SHORT_OPEN filled. Accuracy = profitable fully closed cycles after both fees/spreads divided by completed cycles. Endpoint-forced closures are censored and excluded from accuracy, but included in return. All 25 windows, including no-trade windows, count in return. More signals in one window do not create independent market evidence.

Return is the entire short-only cash-start portfolio, with 25% maximum intended entry gross and 10% per coin, not a 100% invested short return or additive live-account contribution. Minute closes trigger exits, followed by one-minute market execution; a rebound gap can exceed the stop. Fees 0.10% and halfspread 0.05% each side. CS uses unchanged daily FLOORED.V1 HKT moments and weights, with sampled minute MDD in Calmar. CS UTC is in the CSV. This is a separate minute protocol, not hourly --score2 production registration.

| Rank | Model | Family90% lower return | Accuracy rank | Return rank | Wins/closed | Cycle accuracy | Firing windows | Censored | Mean return | Median | P10 | Worst | Mean MDD | CS | Doubled worst-profile mean | Stronger evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | book_m15_flow_breakout | -0.201% | 4 | 2 | 33/110 | +30.000% | 21/25 | 0 | -0.085% | -0.089% | -0.318% | -0.475% | +0.248% | -0.063 | -0.193% | NO |
| 2 | book_m15_volume_breakout | -0.218% | 3 | 3 | 39/143 | +27.273% | 23/25 | 0 | -0.095% | -0.094% | -0.328% | -0.582% | +0.288% | -0.069 | -0.231% | NO |
| 3 | book_m15_flow_persistent | -0.285% | 1 | 1 | 42/107 | +39.252% | 21/25 | 0 | -0.076% | -0.136% | -0.330% | -0.632% | +0.325% | -0.057 | -0.181% | NO |
| 4 | book_m15_volume_persistent | -0.308% | 2 | 4 | 50/138 | +36.232% | 23/25 | 0 | -0.121% | -0.144% | -0.378% | -0.803% | +0.393% | -0.082 | -0.253% | NO |
| 5 | book_m15_bounce_fade | -0.349% | 6 | 5 | 32/185 | +17.297% | 24/25 | 2 | -0.179% | -0.118% | -0.405% | -0.667% | +0.301% | -0.122 | -0.343% | NO |
| 6 | book_m15_failed_rebound | -0.621% | 7 | 6 | 54/338 | +15.976% | 25/25 | 0 | -0.305% | -0.310% | -0.603% | -0.961% | +0.427% | -0.187 | -0.696% | NO |
| 7 | book_m15_relative_weakness | -1.521% | 5 | 7 | 205/1016 | +20.177% | 25/25 | 3 | -1.017% | -1.024% | -1.947% | -2.487% | +1.308% | -0.398 | -2.001% | NO |

Stronger evidence requires all six lower bounds > 0; 30 completed cycles, 12 quarters and 12 firing nonoverlap windows in each context; doubled-cost mean > 0; median >= 0; positive-control mean >= -1%. None of these rules is relaxed. Passing remains retrospective evidence, not a profit forecast or live-switch approval.

## Spent recent-prefix diagnostic

October 4 at 20:00 HKT to October 9 at 08:00 HKT, starting with $100,000 cash. This ends 75 minutes before the prior clone/observed full-prefix report, so do not compare its returns to that longer endpoint. A separate common-endpoint comparison is saved when available.

| Model | Short-only return | MDD | Wins/closed | Censored | Orders |
|---|---|---|---|---|---|
| book_m15_volume_breakout | +0.493% | +0.167% | 5/5 | 0 | 10 |
| book_m15_failed_rebound | -0.043% | +0.122% | 1/3 | 0 | 6 |
| book_m15_bounce_fade | +0.132% | +0.067% | 2/2 | 0 | 4 |
| book_m15_relative_weakness | +0.025% | +0.583% | 8/22 | 0 | 44 |
| book_m15_flow_breakout | +0.493% | +0.167% | 5/5 | 0 | 10 |
| book_m15_flow_persistent | +0.596% | +0.241% | 3/5 | 0 | 10 |
| book_m15_volume_persistent | +0.596% | +0.241% | 3/5 | 0 | 10 |

### Same dates: frozen full-portfolio references

These references use the same dates and $100,000 starting capital, but five/broader assets and accepted recorded quotes/archive 1bp proxy; prototypes use four assets and 5bp stress. The clone was calibrated on this period and retains 19/33 literal agreement. Observed ledger keeps its literal deficit and fee assumptions. This table is conditional comparison, not identical-execution or prospective evidence.

| Model/reference | Full portfolio return | MDD |
|---|---|---|
| observed_literal_ledger | +5.220% | +2.867% |
| frozen_calibrated_reconstruction | +4.866% | +2.842% |
| baitoey_ovl_brk_dual | -8.785% | +12.489% |
| book_cashshort_confirm | -8.670% | +11.808% |
| book_cashshort_pullback | -8.790% | +12.487% |
| book_transition_short | -6.642% | +8.878% |

## Down and rebound scenarios, labeled after the fact

This answers how shorts behaved when the historical market subsequently fell or rebounded. It does not estimate that such a move will happen now. These future labels never admit the main lookalikes or change the main rank. BTC following 240h <=-2% is down, >=+2% is rebound; displayed strategy outcomes are 228h. Counts are small and this horizon difference is intentional.

| Profile | Scenario | Scenario return rank | Model | N | Mean short-only return | Wins/closed | Censored | Mean MDD |
|---|---|---|---|---|---|---|---|---|
| weak_archived | future_down | 1 | book_m15_flow_persistent | 7 | +0.032% | 27/56 | 0 | +0.503% |
| weak_archived | future_down | 2 | book_m15_volume_persistent | 7 | -0.012% | 33/73 | 0 | +0.591% |
| weak_archived | future_down | 3 | book_m15_volume_breakout | 7 | -0.022% | 23/75 | 0 | +0.390% |
| weak_archived | future_down | 4 | book_m15_flow_breakout | 7 | -0.034% | 21/57 | 0 | +0.357% |
| weak_archived | future_down | 5 | book_m15_bounce_fade | 7 | -0.239% | 18/95 | 1 | +0.486% |
| weak_archived | future_down | 6 | book_m15_failed_rebound | 7 | -0.410% | 39/189 | 0 | +0.669% |
| weak_archived | future_down | 7 | book_m15_relative_weakness | 7 | -0.939% | 118/477 | 2 | +1.738% |
| weak_archived | future_rebound | 1 | book_m15_flow_breakout | 13 | -0.118% | 10/45 | 0 | +0.246% |
| weak_archived | future_rebound | 2 | book_m15_flow_persistent | 13 | -0.122% | 13/43 | 0 | +0.294% |
| weak_archived | future_rebound | 3 | book_m15_volume_breakout | 13 | -0.138% | 14/59 | 0 | +0.296% |
| weak_archived | future_rebound | 4 | book_m15_volume_persistent | 13 | -0.177% | 15/56 | 0 | +0.365% |
| weak_archived | future_rebound | 5 | book_m15_bounce_fade | 13 | -0.181% | 11/75 | 1 | +0.258% |
| weak_archived | future_rebound | 6 | book_m15_failed_rebound | 13 | -0.251% | 13/109 | 0 | +0.324% |
| weak_archived | future_rebound | 7 | book_m15_relative_weakness | 13 | -1.119% | 68/417 | 0 | +1.205% |
| weak_fresh_btc | future_down | 1 | book_m15_volume_persistent | 9 | +0.090% | 48/93 | 0 | +0.687% |
| weak_fresh_btc | future_down | 2 | book_m15_volume_breakout | 9 | +0.024% | 34/100 | 0 | +0.506% |
| weak_fresh_btc | future_down | 3 | book_m15_flow_persistent | 9 | +0.011% | 37/75 | 0 | +0.638% |
| weak_fresh_btc | future_down | 4 | book_m15_flow_breakout | 9 | -0.012% | 28/77 | 0 | +0.397% |
| weak_fresh_btc | future_down | 5 | book_m15_bounce_fade | 9 | -0.314% | 31/151 | 0 | +0.643% |
| weak_fresh_btc | future_down | 6 | book_m15_failed_rebound | 9 | -0.603% | 62/289 | 0 | +0.937% |
| weak_fresh_btc | future_down | 7 | book_m15_relative_weakness | 9 | -1.017% | 155/606 | 0 | +1.818% |
| weak_fresh_btc | future_rebound | 1 | book_m15_volume_breakout | 13 | -0.033% | 6/28 | 0 | +0.169% |
| weak_fresh_btc | future_rebound | 2 | book_m15_flow_breakout | 13 | -0.046% | 4/22 | 0 | +0.133% |
| weak_fresh_btc | future_rebound | 3 | book_m15_flow_persistent | 13 | -0.073% | 5/22 | 0 | +0.173% |
| weak_fresh_btc | future_rebound | 4 | book_m15_bounce_fade | 13 | -0.093% | 4/37 | 0 | +0.156% |
| weak_fresh_btc | future_rebound | 5 | book_m15_volume_persistent | 13 | -0.097% | 6/28 | 0 | +0.239% |
| weak_fresh_btc | future_rebound | 6 | book_m15_failed_rebound | 13 | -0.172% | 8/80 | 0 | +0.249% |
| weak_fresh_btc | future_rebound | 7 | book_m15_relative_weakness | 13 | -0.671% | 45/277 | 1 | +0.868% |

The family adjustment covers these seven minute hypotheses only; it does not undo adaptive choices informed by earlier hourly/clone research or create an untouched holdout. No scenario result upgrades the stronger-evidence flag.


## Reproduce/read evidence

Remote Book worktree: /home/ubuntu/test/MiniMax/.worktrees/book-book-intraday-short. Source/research: research/book/intraday_short/{PROTOCOL.md,RESEARCH.md,engine.py,run.py,audit.py,report.py}. Evaluate this frozen initial batch with .venv/bin/python -B -m research.book.intraday_short.run --score; persistent follow-ups use run_persistent --score; audited publication uses research.book.intraday_short.score --score --phase persistent (existing artifacts intentionally prevent overwrite). New experiments require a new output/version and frozen plan before outcomes. Hourly registered models continue to use --score2 and automatically regenerate the ranked hourly short section.

Data: 184 checksummed archives, four fixed coins: BTC, ETH, BNB and XRP; all historical weak/control dates retained. Initial five-coin plan failed a pre-listing SOL July 2020 control and is preserved under v1; four-coin amendment preceded any minute outcome. Fresh BCH 29/30 query remains unrepaired. Some publisher zero-volume halt bars close early; nominal minute-end timestamp delays their use conservatively. Original overstrict interval-audit failure is retained. No recorded order-book execution, funding, borrow or API-latency reconstruction is claimed. Three-minute latency stress is in window_results.csv.
