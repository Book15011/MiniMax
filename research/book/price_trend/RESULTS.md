# Price-based long/short and short-only research

No candidate passed all supplemental stronger-evidence rules. The task of finding a reliable improvement remains incomplete.

Start with **Evidence**, then compare **Short wins/closed**, **Return mean**, **P10/Worst**, **MDD** and **CS**. A rank is a descriptive ordering; FAIL means the candidate has not earned a reliable-improvement claim. The clone85%execution-agreement target is a different measure from profitable-short accuracy.

**What period is measured?** The main rows average all 25 previously selected archive-weak lookalike windows,228 hours (9.5 days) each, starting from cash 100k. Include every selected window, even when the model stays inactive. A separate recent-BTC lookalike profile and216/240 hour endpoints check sensitivity. Those cohorts were selected from information known at their start; they are not filtered to keep only later price falls. The window dates are in cases.parquet.

**What is a correct short?** One episode begins when a coin first becomes short and ends when it becomes completely flat. Additions and partial covers belong to that episode. A win has positive net PnL after opening/closing fees and spread. Accuracy=winning completed episodes/completed episodes. Still-open episodes are censored from accuracy and remain included in portfolio return and net short PnL. Many orders or correlated coins do not create independent market experiments.

**What do return and risk mean?** Return is the whole100kportfolio after all fees, spread and analytical endpoint closing costs. Signed models include both longs and shorts; short-only versions show whether shorting alone helps. Median describes the middle selected window; P10 is the10th percentile; Worst is the lowest return. MDD measures the biggest peak-to-trough loss in minute equity. CS uses the existing0.4 Sortino+0.3 Sharpe+0.3 Calmar formula and daily convention, with minute MDD in Calmar. Higher CS is better, but it is not a percentage or an accuracy rate. Mean net short $ includes all short openings/covers plus endpoint costs; positive means shorting contributed profit. Mean gross shows how much capital exposure was used.

**How are models ranked?** Conservative rank sorts the worst of six profile/horizon lower bounds on mean return. Quarter-cluster bootstrap 20,000 uses an adjustment across 14 hypotheses: previous 8 minute candidates plus these 6. Accuracy rank separately uses the worst-profile lower bound from the central90%completed-short accuracy interval at 228h. This correction does not undo repeated research on spent data. The unchanged main --score2 remains authoritative for competition ranking and also compares candidates against the incumbent. These100% gross-cap portfolios differ from old 25% minute sleeves, so raw returns are not equal-risk comparisons.

| Rank | Model | Lower return | Return mean | Median | P10 | Worst | Short wins/closed | Short accuracy | Accuracy rank | Censored | Mean MDD | CS | Mean gross | Mean net short $ | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | book_price_fast_short | -2.157% | -0.730% | -1.212% | -3.428% | -3.966% | 73/399 | +18.296% | 1 | 35 | +3.566% | -0.137 | +24.073% | -729.65 | FAIL |
| 2 | book_price_channel_short | -2.826% | -1.137% | -1.137% | -4.172% | -4.875% | 74/359 | +20.613% | 3 | 36 | +4.100% | -0.179 | +29.448% | -1136.76 | FAIL |
| 3 | book_price_fast_signed | -2.843% | -0.625% | -1.211% | -3.877% | -5.758% | 79/418 | +18.900% | 2 | 35 | +5.080% | -0.038 | +46.133% | -729.88 | FAIL |
| 4 | book_price_slow_short | -2.850% | -0.827% | -1.190% | -3.270% | -5.567% | 20/131 | +15.267% | 5 | 36 | +4.130% | -0.133 | +41.832% | -826.73 | FAIL |
| 5 | book_price_slow_signed | -3.266% | -0.603% | -1.929% | -4.908% | -6.774% | 20/131 | +15.267% | 5 | 36 | +5.619% | -0.029 | +65.907% | -839.16 | FAIL |
| 6 | book_price_channel_signed | -3.602% | -1.452% | -2.059% | -4.544% | -6.485% | 76/403 | +18.859% | 4 | 43 | +5.638% | -0.110 | +55.803% | -1143.27 | FAIL |

All clocks use completed hourly signals,4h decisions,1 hour execution lag, fixed 5pp band, shared planner/PaperBroker,0.10% fee plus0.05% halfspread each side. The historical minute quotes are publisher proxies. Doubled-cost and2 hour lag reruns are in window_results.csv. Supplemental replay omits daily activity guard; ordinary --score2 includes it. Therefore these are trading-mechanism diagnostics, not complete live simulations. Fixed modern four-coin membership and current precision rules are historical proxy limitations.

The unchanged stronger-evidence checks require all six lower bounds>0,30 completed shorts,12 quarters,12 firing windows in every context, positive doubled-cost mean, nonnegative median, and positive-control mean>=-1%. A descriptive first place never overrides a failed check. Full --score2 and live eligibility remain separate.

## Same spent competition prefix

October 4 20:00 HKT to October 9 08:00 HKT,100k seed. Current four-coin models use1h lag and5bp halfspread. Earlier observed/clone five-coin references use their own actual/fitted clocks and recordedquotes/1bp proxy. This is a common-period conditional comparison, not identical execution or unseen validation.

| Model | Full return | MDD | Short wins/closed | Censored | Net short $ | Orders |
|---|---|---|---|---|---|---|
| book_price_fast_signed | +2.861% | +2.325% | 0/7 | 4 | 3682.29 | 52 |
| book_price_fast_short | +3.796% | +2.323% | 0/6 | 4 | 3796.25 | 29 |
| book_price_slow_signed | +3.166% | +2.455% | 0/0 | 4 | 3866.74 | 32 |
| book_price_slow_short | +3.894% | +2.455% | 0/0 | 4 | 3894.07 | 13 |
| book_price_channel_signed | +3.254% | +3.097% | 0/6 | 4 | 4177.76 | 69 |
| book_price_channel_short | +4.203% | +2.330% | 0/7 | 4 | 4202.72 | 44 |

Earlier common-endpoint references: observed+5.2196%, prior clone+4.8661%; full provenance and risks in /home/ubuntu/test/MiniMax/results/book/20261010-intraday-short-v4/common_prefix_baselines.csv. The observed ledger retains its initial capital deficit and unconfirmed fee assumptions beyond T001.

## Future-down scenarios are diagnostics

scenario_summary.csv labels following 240h BTC return<= -2% as down and>= +2% as rebound. They never select main lookalikes or enter targets. profile_summary.csv shows every profile and216/228/240h outcome and doubled-cost mean. No fresh market forecast is implied.

## Entry timing is a separate accuracy question

The main scoreboard also saves /home/ubuntu/test/MiniMax/results/scoring/short_leaderboard_2.csv. Its precision_1h/3h/6h measures whether an onset would profit after a fixed holding horizon and assumed costs, using hourly prices. It is an HOURLY_PROXY_DESCRIPTIVE diagnostic, not the actual completed-episode hit rate above. For example, a profitable short still open at the competition-prefix endpoint contributes return here but is censored from completed accuracy. Keep these denominators and periods separate.

## Separate newly inspected quote day

All six fixed candidates also ran on October 9 08:00 HKT to October 10 08:00 HKT, from cash 100k, with recorded unsigned bid/ask and the same1h lag. Actual-cost returns ranged from-0.9365%to-0.4663%; no candidate was profitable. Earliest/latest same-timestamp quote controls gave identical targets and fills. All36cost/lag/control ledgers passed independent accounting. This one-day check is newly inspected retrospective evidence, not a prospective trial, and is not mixed into the9.5 day lookalike score. Detail: /home/ubuntu/test/MiniMax/results/book/20261010-price-new-block-v2/RESULTS.md. The failed initial duplicate-quote attempt remains in the v1 folder.

## Reproduce and add models

Remote worktree /home/ubuntu/test/MiniMax/.worktrees/book-book-intraday-short. Registered candidates use .venv/bin/python -B -m backtest.run --model MODEL_NAME --score2 and automatically enter /home/ubuntu/test/MiniMax/results/scoring/leaderboard_2.md from this branch. All-six batch: .venv/bin/python -B -m research.book.price_trend.run --score. Audited short table: .venv/bin/python -B -m research.book.price_trend.score --score. Existing batches refuse overwrite; new hypotheses need a new version/protocol. Publication from older teammates' branches may replace the sharedMarkdown link until reviewed integration. No main merge or live bot change was performed.
