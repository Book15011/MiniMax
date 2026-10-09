# Book weak-market selection evaluator

Read RESULTS.md for findings and limitations, and /home/ubuntu/test/MiniMax/.worktrees/book-book-bear-eval/docs/SCORE2.md for usage.

The published secondary board is /home/ubuntu/test/MiniMax/results/scoring/leaderboard_2.md. It has visible experimental ranks, actual after-cost 9/9.5/10-day returns, CS risk, paired e 20/cash uncertainty, downside/rebound controls, and a separate hourly short-onset table. Models start from cash at causally selected weak historical checkpoints.

Code lives on feature/book-bear-eval only. Data/results live in /home/ubuntu/test/MiniMax/results/book/20261009-weak-eval-v2. The main branch, original leaderboard and live bot are unchanged.

Preparation:
    .venv/bin/python -B -m research.book.weak_eval.run prepare

Import frozen registered models:
    .venv/bin/python -B -m research.book.weak_eval.run compare

Test a new registered model and update the secondary board:
    .venv/bin/python -B -m backtest.run --model book_NAME --score2

Add --score to update both boards. Use your own lock/tmux and nice 10 for heavy jobs.

Never overwrite frozen configurations/cases or silently advance the query. A new checkpoint must use a new output directory and the publisher-backed reference preparation. Fresh broad BCH coverage and forecast validation failures are retained; no threshold relaxation enables the old adaptive method. Minute/second execution and real-account switching remain UNVERIFIED.
