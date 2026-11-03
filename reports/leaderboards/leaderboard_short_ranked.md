# Short leaderboard: return, F1 and reliable accuracy


Score = return points (up to 50) + opportunity-F1 points (up to 30) + sample-aware completed-accuracy points (up to 20). Return points use the existing conservative after-cost return percentile among these 13 models. F1 points use the worse-profile quarter-cluster 90%lower bound. Accuracy points use the smaller of quarter-cluster and Wilson 90%lower bounds. A high rank can still lose money. These are exploratory weights, not a calibrated prediction of future profit.

Two wins from four and 25 from 50 have the same 50% raw accuracy; the second has a higher sample-size lower bound. The quarter check also reflects dependence between trades. Trade count is shown, and more trading is never rewarded by itself.

| Rank | Model | Score | Return /50 | F1 /30 | Accuracy /20 | Mean return | Wins/closed | Raw accuracy | Accuracy reliability | MDD | CS | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | book_short_shock_fade | 55.36 | 50.00 | 0.10 | 5.26 | 0.02% | 11/19 | 57.89% | 26.32% | 0.06% | 0.012 | FAIL |
| 2 | book_short_volume_fade | 53.22 | 45.83 | 0.51 | 6.88 | -0.00% | 21/39 | 53.85% | 34.38% | 0.12% | -0.003 | FAIL |
| 3 | book_short_range_fail | 50.60 | 41.67 | 0.47 | 8.46 | -0.00% | 30/52 | 57.69% | 42.31% | 0.11% | -0.005 | FAIL |
| 4 | book_short_ridge6 | 39.75 | 37.50 | 0.11 | 2.14 | -0.02% | 7/31 | 22.58% | 10.71% | 0.06% | -0.008 | FAIL |
| 5 | book_bear_pullback | 38.07 | 33.33 | 1.97 | 2.77 | -0.14% | 44/234 | 18.80% | 13.84% | 0.45% | -0.114 | FAIL |
| 6 | book_short_analogue12 | 35.82 | 29.17 | 1.82 | 4.83 | -0.13% | 108/345 | 31.30% | 24.17% | 0.22% | -0.080 | FAIL |
| 7 | book_bear_breakdown | 31.24 | 20.83 | 6.25 | 4.15 | -0.16% | 124/454 | 27.31% | 20.75% | 0.58% | -0.115 | FAIL |
| 8 | book_short_analogue6 | 29.62 | 25.00 | 0.47 | 4.15 | -0.08% | 29/113 | 25.66% | 20.77% | 0.15% | -0.033 | FAIL |
| 9 | book_bear_cost_guard | 27.57 | 16.67 | 7.06 | 3.84 | -0.27% | 147/587 | 25.04% | 19.19% | 0.67% | -0.179 | FAIL |
| 10 | book_bear_guard | 23.44 | 12.50 | 7.40 | 3.54 | -0.36% | 179/775 | 23.10% | 17.71% | 0.75% | -0.219 | FAIL |
| 11 | book_bear_trend_control | 19.96 | 8.33 | 9.88 | 1.75 | -0.26% | 66/517 | 12.77% | 8.73% | 0.97% | -0.168 | FAIL |
| 12 | book_bear_trail_exit | 14.91 | 4.17 | 6.75 | 3.99 | -0.40% | 164/654 | 25.08% | 19.96% | 0.73% | -0.213 | FAIL |
| 13 | book_bear_fast_exit | 8.45 | 0.00 | 4.06 | 4.38 | -0.65% | 243/969 | 25.08% | 21.92% | 0.84% | -0.324 | FAIL |

Mean return, completed trades, MDD and CS above describe all 25 archive lookalikes over 228 hours. Other profile and 216/240-hour endpoints remain in the immutable combined study. Main return points use the worst of all six conservative bounds with 27-hypothesis adjustment, not just the displayed mean. The horizon was fixed earlier and is not today's remaining competition time.

## How opportunity F1 works

For every benchmark coin, evaluate nonoverlapping 6-hour blocks after the common one-hour execution delay plus one-minute batch-settlement buffer. A positive opportunity is a fall large enough to profit after both fees and spread. A bot predicts that fall when its actual audited short at block start is at least 1% of account equity. Existing held shorts count; dust and cash do not. TP=short+profitablefall;FP=short+nonprofitableblock;FN=no meaningful short+profitablefall. Precision=TP/(TP+FP),recall=TP/(TP+FN),F1=2TP/(2TP+FP+FN). Incomplete endpoints are censored. Zero denominators score zero.

This measures coverage at fixed decision points. It is distinct from accuracy of new entries and completed-trade profit; it does not inspect every possible intrablock fall or account for position changes inside a block. Future labels are diagnostic only and never feed the bot or select windows.

| Rank | Model | TP | FP | Missed falls (FN) | Precision | Recall | F1 | Worst-profile F1 lower90 | Blocks | Censored |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | book_short_shock_fade | 6 | 11 | 1243 | 35.29% | 0.48% | 0.95% | 0.34% | 3700 | 100 |
| 2 | book_short_volume_fade | 16 | 28 | 1233 | 36.36% | 1.28% | 2.47% | 1.71% | 3700 | 100 |
| 3 | book_short_range_fail | 19 | 33 | 1230 | 36.54% | 1.52% | 2.92% | 1.56% | 3700 | 100 |
| 4 | book_short_ridge6 | 9 | 21 | 1240 | 30.00% | 0.72% | 1.41% | 0.35% | 3700 | 100 |
| 5 | book_bear_pullback | 76 | 177 | 1173 | 30.04% | 6.08% | 10.12% | 6.57% | 3700 | 100 |
| 6 | book_short_analogue12 | 61 | 87 | 1188 | 41.22% | 4.88% | 8.73% | 6.07% | 3700 | 100 |
| 7 | book_bear_breakdown | 238 | 396 | 1011 | 37.54% | 19.06% | 25.28% | 20.84% | 3700 | 100 |
| 8 | book_short_analogue6 | 17 | 33 | 1232 | 34.00% | 1.36% | 2.62% | 1.57% | 3700 | 100 |
| 9 | book_bear_cost_guard | 272 | 472 | 977 | 36.56% | 21.78% | 27.30% | 23.54% | 3700 | 100 |
| 10 | book_bear_guard | 295 | 555 | 954 | 34.71% | 23.62% | 28.11% | 24.66% | 3700 | 100 |
| 11 | book_bear_trend_control | 499 | 990 | 750 | 33.51% | 39.95% | 36.45% | 32.93% | 3700 | 100 |
| 12 | book_bear_trail_exit | 247 | 417 | 1002 | 37.20% | 19.78% | 25.82% | 22.51% | 3700 | 100 |
| 13 | book_bear_fast_exit | 135 | 246 | 1114 | 35.43% | 10.81% | 16.56% | 13.54% | 3700 | 100 |

Counts and pointF1above are the archive profile. The score uses the smaller lower bound from archive and recent-BTC profiles, resampling start-date quarters 20,000 times. Repeated and overlapping windows do not become independent experiments.

## Where to look and how to update

leaderboard_short_ranked.csv contains all components, sample counts, conservative-return rank, raw return/accuracy ranks, F1and unchanged evidence flags. opportunity_profiles.csv has both contexts; opportunity_cases.csv and opportunity_blocks.csv retain all classifications and censored counts. independent_metric_audit.json verifies exposure from actual orders, after-cost labels and F1denominators. manifest.json pins all source/evidence files.

The broader 13-model return/risk/entry-timing table remains /home/ubuntu/test/MiniMax/results/book/20261010-short-combined-v3/leaderboard_short.md. Normal registered-model scoring uses .venv/bin/python -B -m backtest.run --model MODEL --score2 in the model's Book worktree and automatically updates /home/ubuntu/test/MiniMax/results/scoring/leaderboard_2.md. This frozen short rank requires a new equally audited cohort before admitting a new model; it does not silently append scores from different protocols. Publish this version once with .venv/bin/python -B -m research.book.short_ranking.rank --score.

No threshold was relaxed and no live bot or main branch changed. The adaptive gate remains disabled with BCH absent, 29/30 endpoints. See research/book/short_ranking/PROTOCOL.md for every definition and limitation.


## F1 rank, shown separately

This rank sorts the worse-profile F1 lower bound. A model can cover more falls and still lose after trading costs; compare the return and evidence columns before selecting it.

| F1 rank | Model | Archive F1 | Worst-profile F1 lower bound | Mean portfolio return | Wins / completed |
|---|---|---|---|---|---|
| 1 | book_bear_trend_control | 36.45% | 32.93% | -0.265% | 66/517 |
| 2 | book_bear_guard | 28.11% | 24.66% | -0.357% | 179/775 |
| 3 | book_bear_cost_guard | 27.30% | 23.54% | -0.274% | 147/587 |
| 4 | book_bear_trail_exit | 25.82% | 22.51% | -0.399% | 164/654 |
| 5 | book_bear_breakdown | 25.28% | 20.84% | -0.155% | 124/454 |
| 6 | book_bear_fast_exit | 16.56% | 13.54% | -0.651% | 243/969 |
| 7 | book_bear_pullback | 10.12% | 6.57% | -0.143% | 44/234 |
| 8 | book_short_analogue12 | 8.73% | 6.07% | -0.131% | 108/345 |
| 9 | book_short_volume_fade | 2.47% | 1.71% | -0.004% | 21/39 |
| 10 | book_short_analogue6 | 2.62% | 1.57% | -0.078% | 29/113 |
| 11 | book_short_range_fail | 2.92% | 1.56% | -0.005% | 30/52 |
| 12 | book_short_ridge6 | 1.41% | 0.35% | -0.017% | 7/31 |
| 13 | book_short_shock_fade | 0.95% | 0.34% | +0.017% | 11/19 |

The CSV names opportunity_censored for incomplete six-hour labels and episode_censored for strategy positions still open at the portfolio endpoint. The original score file used censored for opportunity labels; the original portfolio counts remain preserved in the combined study. All original score components, ranks, returns and evidence flags reproduce exactly in this view.
