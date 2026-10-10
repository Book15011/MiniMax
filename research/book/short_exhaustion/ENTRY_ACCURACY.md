# Short timing after simulated fills

Start with the win counts, firing-window count and then6haccuracy rank. This descriptive rank does not override the main return/risk/evidence table. Each profile includes all25fixed lookalikes, with cash windows visible through the firing denominator. All data is spent retrospective research.

One onset is the first actual shared-broker simulated OpenShort fill in an episode. Additions/partial covers are not new onsets. From that actual filled bid, hypothetically hold the first quantity unchanged for1/3/6h, cover at the publisher-minute as-of ask proxy and charge both0.10%fees plus spread. This timing label ignores the strategy's intervening real exits and additions. It is a fixed-horizon entry diagnostic, not actual completed-trade PnL, live-fill accuracy or a forecast. A horizon extending beyond the window or missing a fresh price is censored, never counted as a failure or win.

|Profile|Model|Firing windows|1h wins/n|3h wins/n|6h wins/n|6h accuracy|6h mean markout|6h accuracy rank|
|---|---|---|---|---|---|---|---|---|
|weak_archived|book_bear_guard|25/25|180/799|223/798|255/785|32.48%|-0.38%|4|
|weak_archived|book_short_volume_fade|16/25|9/42|17/40|17/39|43.59%|0.09%|3|
|weak_archived|book_short_range_fail|16/25|20/54|26/53|24/52|46.15%|-0.17%|2|
|weak_archived|book_short_shock_fade|11/25|7/20|10/19|9/19|47.37%|0.36%|1|
|weak_fresh_btc|book_bear_guard|25/25|164/732|218/731|255/722|35.32%|-0.38%|4|
|weak_fresh_btc|book_short_volume_fade|17/25|17/48|20/47|23/47|48.94%|0.18%|2|
|weak_fresh_btc|book_short_range_fail|19/25|28/67|32/67|30/66|45.45%|-0.03%|3|
|weak_fresh_btc|book_short_shock_fade|10/25|11/22|12/21|11/21|52.38%|0.31%|1|

The main short_leaderboard_2.csv separately labels hourly TARGET onsets; these rows start from simulated EXECUTED entries after delay/band/rounding. Completed episode accuracy and portfolio return are in leaderboard_short.md. Correlated entries, overlapping profiles and short holding horizons do not become independent market experiments. All raw labels and censoring counts are retained in the CSV files.
