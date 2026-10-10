# Start with the current short leaderboard

Open /home/ubuntu/test/MiniMax/results/scoring/leaderboard_short_ranked.md for the 13-model score combining conservative return (50%), opportunity F1 (30%) and sample-aware completed-short accuracy (20%). Its CSV includes separate F1, return and accuracy ranks. Full definitions are in /home/ubuntu/test/MiniMax/.worktrees/book-book-daily-channel/research/book/short_ranking/PROTOCOL.md.

For all equal-protocol portfolio results and six context/horizon checks, use /home/ubuntu/test/MiniMax/results/book/20261010-short-combined-v3/leaderboard_short.md. It counts the shared guard once: 7,995 unique outcomes, uniformly corrected for 27 declared hypotheses. All evidence flags remain FAIL.

This worktree supplies book_short_volume_fade, book_short_range_fail and book_short_shock_fade. Read RESULTS.md for their fixed entry/exit rules, risk and completed-episode statistics; ENTRY_ACCURACY.md describes separate after-cost marks at 1/3/6 hours from simulated first fills. These hypothetical marks can disagree with actual-exit accuracy.

The shock model's archive point mean is +0.0171%, with 11 profitable episodes from 19 and only 11 firing windows out of 25. That is insufficient evidence: its conservative lower return bound is negative and its fresh-profile doubled-cost mean is negative. In the already inspected early competition prefix all three new models stayed in cash. Neither a positive point estimate nor avoiding trades proves a better live strategy.

All 2,460 cohort ledgers passed independent accounting and terminal checks. The guard reproduced 615 earlier ledgers and 2,460 artifacts exactly. 541 project and 14 focused tests passed. Audits validate the implementation, not predictive profit.

From this Book worktree run .venv/bin/python -B -m backtest.run --model book_short_shock_fade --score2 to refresh that registered model's normal leaderboard entry. The normal board updates automatically. A new model does not automatically enter the frozen 13-model supplemental rank: it requires a new complete equal-protocol audit and expanded multiple-testing correction. Frozen full batches refuse overwrite.
