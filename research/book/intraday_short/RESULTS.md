# Ranked minute short-only research

Read rank as a conservative experiment order. Five frozen hypotheses; no parameter tuning from these returns. Selection bound = worst of six weak-profile/horizon lower mean-return bounds; quarter bootstrap20,000 draws with Bonferroni family adjustment across5models x6contexts. A negative bound does not establish reliable positive return. All history is spent.

Accuracy rank separately sorts worst-profile lower90% completed-cycle accuracy; return rank sorts worst-profile mean228h native-exposure return. These two ranks are descriptive, not independent selection evidence. Main displayed counts/returns/risk use archive-full25windows at228h. Full second-profile/horizon details are in profile_summary.csv.

A signal counts only when a SHORT_OPEN filled. Accuracy = profitable fully closed cycles after both fees/spreads divided by completed cycles. Endpoint-forced closures are censored and excluded from accuracy, but included in return. All25windows, including no-trade windows, count in return. More signals in one window do not create independent market evidence.

Return is the entire short-only cash-start portfolio, with25%maximum intended entry gross and10%percoin, not a100%invested short return or additive live-account contribution. Minute closes trigger exits, followed by one-minute market execution; a rebound gap can exceed the stop. Fees0.10% and halfspread0.05%each side. CS uses unchanged daily FLOORED.V1 HKT moments and weights, with sampled minute MDD in Calmar. CS UTC is in theCSV. This is a separate minute protocol, not hourly --score2 production registration.

| Rank | Model | Family90% lower return | Accuracy rank | Return rank | Wins/closed | Cycle accuracy | Firing windows | Censored | Mean return | Median | P10 | Worst | Mean MDD | CS | Doubled worst-profile mean | Stronger evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | book_m15_flow_breakout | -0.197% | 2 | 1 | 33/110 | +30.000% | 21/25 | 0 | -0.085% | -0.089% | -0.318% | -0.475% | +0.248% | -0.063 | -0.193% | NO |
| 2 | book_m15_volume_breakout | -0.213% | 1 | 2 | 39/143 | +27.273% | 23/25 | 0 | -0.095% | -0.094% | -0.328% | -0.582% | +0.288% | -0.069 | -0.231% | NO |
| 3 | book_m15_bounce_fade | -0.340% | 4 | 3 | 32/185 | +17.297% | 24/25 | 2 | -0.179% | -0.118% | -0.405% | -0.667% | +0.301% | -0.122 | -0.343% | NO |
| 4 | book_m15_failed_rebound | -0.610% | 5 | 4 | 54/338 | +15.976% | 25/25 | 0 | -0.305% | -0.310% | -0.603% | -0.961% | +0.427% | -0.187 | -0.696% | NO |
| 5 | book_m15_relative_weakness | -1.506% | 3 | 5 | 205/1016 | +20.177% | 25/25 | 3 | -1.017% | -1.024% | -1.947% | -2.487% | +1.308% | -0.398 | -2.001% | NO |

Stronger evidence requires all six lower bounds>0;30completed cycles,12quarters and12firing nonoverlap windows in each context; doubled-cost mean>0; median>=0; positive-control mean>=-1%. None of these rules is relaxed. Passing remains retrospective evidence, not a profit forecast or live-switch approval.

## Spent recent-prefix diagnostic

Oct4 20HKT toOct9 08HKT,100000cash. This ends75minutes before the prior clone/observed full-prefix report, so do not compare its returns to that longer endpoint. A separate common-endpoint comparison is saved when available.

| Model | Short-only return | MDD | Wins/closed | Censored | Orders |
|---|---|---|---|---|---|
| book_m15_volume_breakout | +0.493% | +0.167% | 5/5 | 0 | 10 |
| book_m15_failed_rebound | -0.043% | +0.122% | 1/3 | 0 | 6 |
| book_m15_bounce_fade | +0.132% | +0.067% | 2/2 | 0 | 4 |
| book_m15_relative_weakness | +0.025% | +0.583% | 8/22 | 0 | 44 |
| book_m15_flow_breakout | +0.493% | +0.167% | 5/5 | 0 | 10 |

## Reproduce/read evidence

Remote Book worktree: /home/ubuntu/test/MiniMax/.worktrees/book-book-intraday-short. Source/research: research/book/intraday_short/{PROTOCOL.md,RESEARCH.md,engine.py,run.py,audit.py,report.py}. Evaluate this frozen batch with .venv/bin/python -B -m research.book.intraday_short.run --score (existing artifacts intentionally prevent overwrite). New experiments require a new output/version and frozen plan before outcomes. Hourly registered models continue to use --score2 and automatically regenerate the ranked hourly short section.

Data:184checksummedarchives, four fixed coinsBTC/ETH/BNB/XRP; all historical weak/control dates retained. Initial five-coin plan failed a pre-listingSOLJuly2020 control and is preserved under v1; four-coin amendment preceded any minute outcome. Fresh BCH29/30query remains unrepaired. Some publisher zero-volume halt bars close early; nominal minute-end timestamp delays their use conservatively. Original overstrict interval-audit failure is retained. No recorded order-book execution, funding, borrow or API-latency reconstruction is claimed. Three-minute latency stress is in window_results.csv.
