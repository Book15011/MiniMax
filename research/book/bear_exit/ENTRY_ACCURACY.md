# Short timing after simulated fills

Start with the win counts, firing-window count and then6haccuracy rank. This descriptive rank does not override the main return/risk/evidence table. Each profile includes all25fixed lookalikes, with cash windows visible through the firing denominator. All data is spent retrospective research.

One onset is the first actual shared-broker simulated OpenShort fill in an episode. Additions/partial covers are not new onsets. From that actual filled bid, hypothetically hold the first quantity unchanged for1/3/6h, cover at the publisher-minute as-of ask proxy and charge both0.10%fees plus spread. This timing label ignores the strategy's intervening real exits and additions. It is a fixed-horizon entry diagnostic, not actual completed-trade PnL, live-fill accuracy or a forecast. A horizon extending beyond the window or missing a fresh price is censored, never counted as a failure or win.

|Profile|Model|Firing windows|1h wins/n|3h wins/n|6h wins/n|6h accuracy|6h mean markout|6h accuracy rank|
|---|---|---|---|---|---|---|---|---|
|weak_archived|book_bear_guard|25/25|180/799|223/798|255/785|32.48%|-0.38%|4|
|weak_archived|book_bear_cost_guard|25/25|138/610|185/610|213/596|35.74%|-0.31%|2|
|weak_archived|book_bear_fast_exit|25/25|234/972|297/968|328/955|34.35%|-0.31%|3|
|weak_archived|book_bear_trail_exit|25/25|155/673|206/672|236/658|35.87%|-0.31%|1|
|weak_fresh_btc|book_bear_guard|25/25|164/732|218/731|255/722|35.32%|-0.38%|4|
|weak_fresh_btc|book_bear_cost_guard|25/25|132/581|179/580|213/572|37.24%|-0.34%|3|
|weak_fresh_btc|book_bear_fast_exit|25/25|220/940|313/935|352/923|38.14%|-0.26%|2|
|weak_fresh_btc|book_bear_trail_exit|25/25|152/654|214/652|249/644|38.66%|-0.24%|1|

The main short_leaderboard_2.csv separately labels hourly TARGET onsets; these rows start from simulated EXECUTED entries after delay/band/rounding. Completed episode accuracy and portfolio return are in leaderboard_short.md. Correlated entries, overlapping profiles and short holding horizons do not become independent market experiments. All raw labels and censoring counts are retained in the CSV files.
