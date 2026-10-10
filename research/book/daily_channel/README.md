# Daily channel research baseline
This registers the audited 23/33 quantity-match calibration as a pure directional model named book_daily_channel. It has not met 85% clone agreement. The original private strategy has not been identified.

Five October sessions informed calibration. Historical results are retrospective portability checks, not a clean prospective test. The fitted allocation is shared across coins and dates. Every parameter is in config.yaml.

The normal harness evaluates daily at 16 UTC with one-hour execution lag, usual fees/spreads, point-in-time investability, cash starts and the activity guard. This differs from the separate observed-time clone reconstruction at 01 UTC with its minute workload clock. Do not equate normal scores with literal trade agreement. History is truncated to 4,608 closed hours for finite computation; selected missing history returns cash.

From /home/ubuntu/test/MiniMax/.worktrees/book-book-daily-channel run:
.venv/bin/python -B -m backtest.run --model book_daily_channel --score2
Results automatically enter /home/ubuntu/test/MiniMax/results/scoring/leaderboard_2.md. No live switch or main merge.
