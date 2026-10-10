# Short timing after simulated fills

Start with the win counts, firing-window count and then6haccuracy rank. This descriptive rank does not override the main return/risk/evidence table. Each profile includes all25fixed lookalikes, with cash windows visible through the firing denominator. All data is spent retrospective research.

One onset is the first actual shared-broker simulated OpenShort fill in an episode. Additions/partial covers are not new onsets. From that actual filled bid, hypothetically hold the first quantity unchanged for1/3/6h, cover at the publisher-minute as-of ask proxy and charge both0.10%fees plus spread. This timing label ignores the strategy's intervening real exits and additions. It is a fixed-horizon entry diagnostic, not actual completed-trade PnL, live-fill accuracy or a forecast. A horizon extending beyond the window or missing a fresh price is censored, never counted as a failure or win.

|Profile|Model|Firing windows|1h wins/n|3h wins/n|6h wins/n|6h accuracy|6h mean markout|6h accuracy rank|
|---|---|---|---|---|---|---|---|---|
|weak_archived|book_bear_guard|25/25|180/799|223/798|255/785|32.48%|-0.38%|4|
|weak_archived|book_short_analogue6|20/25|29/114|46/114|38/113|33.63%|-0.55%|3|
|weak_archived|book_short_analogue12|23/25|82/353|127/347|137/345|39.71%|-0.15%|2|
|weak_archived|book_short_ridge6|8/25|10/31|11/31|14/31|45.16%|0.16%|1|
|weak_fresh_btc|book_bear_guard|25/25|164/732|218/731|255/722|35.32%|-0.38%|4|
|weak_fresh_btc|book_short_analogue6|22/25|35/128|52/128|46/127|36.22%|-0.50%|3|
|weak_fresh_btc|book_short_analogue12|23/25|84/366|132/357|160/355|45.07%|-0.08%|1|
|weak_fresh_btc|book_short_ridge6|8/25|14/53|17/53|23/53|43.40%|-0.08%|2|

The main short_leaderboard_2.csv separately labels hourly TARGET onsets; these rows start from simulated EXECUTED entries after delay/band/rounding. Completed episode accuracy and portfolio return are in leaderboard_short.md. Correlated entries, overlapping profiles and short holding horizons do not become independent market experiments. All raw labels and censoring counts are retained in the CSV files.
