# Current comparison

Use /home/ubuntu/test/MiniMax/results/scoring/leaderboard_short_ranked.md for the new 50% conservative return / 30% opportunity F1 / 20% sample-aware accuracy score and separate F1 rank. The current full equal-protocol comparison is /home/ubuntu/test/MiniMax/results/book/20261010-short-combined-v3/leaderboard_short.md: thirteen models, 7,995 unique outcomes, 27 uniform hypotheses. All evidence flags remain FAIL. The older ten-model v2 below is preserved history.

# Read the updated comparison
The new ten-model equal-protocol comparison is:
 /home/ubuntu/test/MiniMax/results/book/20261010-short-combined-v2/leaderboard_short.md

It combines all seven prior hourly portfolios and the three purged historical-state forecasts, counts the shared guard once, and recomputes every row under the same24hypothesis correction. All6,150unique outcomes remain saved. No candidate clears every reliable-profit gate. The ranking is descriptive research, not a validated live switch.

The normal board automatically received book_short_analogue6,book_short_analogue12 andbook_short_ridge6:
 /home/ubuntu/test/MiniMax/results/scoring/leaderboard_2.md

Read the Evidence flag before the rank. Mean return averages all25archive-weak windows, including inactive cases and rebounds. Accuracy is naturally closed, net-profitable short episodes divided by completed episodes.1/3/6hfirst-fill marks in entry_accuracy.md measure a different hypothetical fixed hold. The forecast profitable fractions are estimated from past outcomes, not calibrated probabilities.

Documentation correction: the last rerun paragraph of the frozen score.py-generated report inherited the bear-exit worktree path. For the three forecast models use /home/ubuntu/test/MiniMax/.worktrees/book-book-short-forecast, then:
 .venv/bin/python -B -m backtest.run --model book_short_analogue6 --score2
To rebuild the same frozen report:
 .venv/bin/python -B -m research.book.short_forecast.score --score
The full batch refuses overwrite. The original frozen source, helper hashes and result files were preserved; this guide corrects only the instruction path.

All541projecttests and16focusedtests passed.2,460full-strategy ledgers passed accounting, terminal-short closure and source-freeze checks. The guard exactly reproduced615priorledgers and2,460artifact pairs. These checks confirm implementation, not predictive superiority. No live model, main branch or secret was changed.
