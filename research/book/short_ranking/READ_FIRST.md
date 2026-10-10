# Start here: short-strategy score

Open /home/ubuntu/test/MiniMax/results/scoring/leaderboard_short_ranked.md. The explanation is above the ranked table. The CSV beside it contains the numerical components and separate F1, return and accuracy ranks.

The combined research score is 50% conservative after-cost return, 30% coverage of profitable six-hour falls (F1), and 20% completed-trade accuracy adjusted for sample size and dependence. Two wins from four do not carry the same confidence as 25 from 50. A held short can cover a fall without placing another order.

Read Evidence first. Every current model still says FAIL: no reliable live replacement has been established. A high rank shows where research should continue, not permission to switch the bot. The separate 85% target is trade-log agreement and is not this score.

F1 labels use future outcomes only to evaluate past decisions. They never choose the historical windows or enter a model. This F1 evaluates fixed block-start holdings; entry timing and actual completed-trade profit remain different tables.

The full definitions are in PROTOCOL.md. Original immutable scores, 559 independently checked ledgers and 82,732 block classifications are in /home/ubuntu/test/MiniMax/results/book/20261010-short-ranked-v1. The original censored column means incomplete opportunity blocks; the current-view CSV clarifies opportunity_censored and separately restores episode_censored from the portfolio ledger summary.

Normal model testing remains .venv/bin/python -B -m backtest.run --model MODEL --score2 from that model's Book worktree. It automatically updates leaderboard_2.md. Admission to this frozen short comparison requires a new equally audited cohort with the same cases, execution and expanded multiple-testing correction; model registration alone does not add a comparable short score.
