# Short timing after simulated fills

Start with the win counts, firing-window count and then6haccuracy rank. This descriptive rank does not override the main return/risk/evidence table. Each profile includes all25fixed lookalikes, with cash windows visible through the firing denominator. All data is spent retrospective research.

One onset is the first actual shared-broker simulated OpenShort fill in an episode. Additions/partial covers are not new onsets. From that actual filled bid, hypothetically hold the first quantity unchanged for1/3/6h, cover at the publisher-minute as-of ask proxy and charge both0.10%fees plus spread. This timing label ignores the strategy's intervening real exits and additions. It is a fixed-horizon entry diagnostic, not actual completed-trade PnL, live-fill accuracy or a forecast. A horizon extending beyond the window or missing a fresh price is censored, never counted as a failure or win.

|Profile|Model|Firing windows|1h wins/n|3h wins/n|6h wins/n|6h accuracy|6h mean markout|6h accuracy rank|
|---|---|---|---|---|---|---|---|---|
|weak_archived|book_bear_trend_control|25/25|110/552|155/550|175/544|32.17%|-0.30%|3|
|weak_archived|book_bear_guard|25/25|180/799|223/798|255/785|32.48%|-0.38%|2|
|weak_archived|book_bear_pullback|24/25|52/236|77/236|75/235|31.91%|-0.31%|4|
|weak_archived|book_bear_breakdown|25/25|115/472|144/472|172/464|37.07%|-0.25%|1|
|weak_fresh_btc|book_bear_trend_control|25/25|106/537|159/535|188/530|35.47%|-0.27%|3|
|weak_fresh_btc|book_bear_guard|25/25|164/732|218/731|255/722|35.32%|-0.38%|4|
|weak_fresh_btc|book_bear_pullback|24/25|51/211|71/210|76/209|36.36%|-0.36%|1|
|weak_fresh_btc|book_bear_breakdown|25/25|113/444|150/444|158/441|35.83%|-0.26%|2|

The main short_leaderboard_2.csv separately labels hourly TARGET onsets; these rows start from simulated EXECUTED entries after delay/band/rounding. Completed episode accuracy and portfolio return are in leaderboard_short.md. Correlated entries, overlapping profiles and short holding horizons do not become independent market experiments. All raw labels and censoring counts are retained in the CSV files.
