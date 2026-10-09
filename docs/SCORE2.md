# Using the weak-market scoreboard

The secondary board is /home/ubuntu/test/MiniMax/results/scoring/leaderboard_2.md. Its reading guide is at the top. CSVs are leaderboard_2.csv and short_leaderboard_2.csv in the same directory. The original leaderboard.md and scoring algorithm retain their meaning.

This implementation lives in Book's /home/ubuntu/test/MiniMax/.worktrees/book-book-bear-eval, branch feature/book-bear-eval. Run from that worktree until a teammate reviews and merges it. No main merge or live deployment has happened.

## What the ranking answers

It compares models starting from cash in many past weak-market states similar to the dated competition context. The observed weak-state filter requires BTC 48h log return[-10%,0], market breadth<=40%, and BTC 24h<=1%. Matching only uses information available at the historical starting time. It does not choose cases because they later fell.

Two fixed profiles are used: a complete archived reference (Oct 8 00UTC) and a fresher BTC-only sensitivity (Oct 9 00UTC). The fresh broad 30-coin endpoints have 29/30 coverage; BCH is missing. The old failed adaptive forecast method remains failed. The sensitivity is explicitly a different price-only profile, not a disguised coverage pass.

Each primary profile contains 25 cases at least 14days apart and at most 3 in any 90days. Compare 216,228,240hours after each cash start.228hours matches Oct 9 00UTC to the documented Oct 18 12UTC finish. The checkpoint stays frozen as time passes. Historical starts 12UTC versus current reference 00UTC introduce a clock difference.

The Conservative score is the minimum joint 90% one-sided lower return-advantage bound over both profiles, all 3horizons, and both cash and the fixed original e 20. Higher is better. A negative score means underperformance remains plausible. This is historical conditional evidence, not a forecast or probability of winning. All compatible models get a visible experimental rank, even when no replacement is statistically supported. Original hard-gate failures stay visible.

The common resampling uses 20,000 fixed-seed calendar-quarter draws. Quarter labels sharing any replay interval are joined. One centered standardized maximum across currently compared models/contexts/baselines applies a multiple-comparison penalty. The standard error is fixed from bootstrap draws, so this is not a full bootstrap-t. Strengthened evidence requires a positive score, original eligibility, at least 12 raw quarters within each primary profile and 12 merged clusters globally. Unknown future-regime coverage, spent research and repeated tuning remain limits.

## Reading the numbers

Mean, median, p 10, worst 10%mean and worst are after-cost strategy returns, not the old hit-rate score. Trading fees/spreads and one-bar execution lag are already in compatible cached paths; the chosen horizon charges terminal liquidation once. p 10 is the bad-tail threshold. Worst 10%mean averages the lowest 10% including fractional boundary mass.

Delta e 20 is paired on the same historical cases against the fixed original e 20 runkey 0ec3cf0ca1185b36. A later same-name revision cannot silently replace that benchmark. Cash is a zero-return comparator in confidence bounds; the registered team_cash row may have tiny activity-guard costs.

CS uses the same FLOORED.V1 daily-raw formula as the original evaluator: .4Sortino+.3Sharpe+.3Calmar. It is recalculated on shortened paths, including terminal liquidation, with HKT 16UTC boundaries and partial first/last days. CS UTC is the alternate-clock sensitivity. CS_HIT_positive averages only profitable shortened cases and differs from original_cs_hit (the original 14-day LENIENT-clearing CS_HIT). Actual final competition formula remains organizer-dependent.

Down/rebound tables are stress diagnostics only: within archived weak cases they partition realized future BTC 240h return<=-2% or>=+2%. Strategy returns remain 228h, explicitly named. Positive-state controls use observed historical strength. None of these future partitions select or weight the main ranking.

## Separate short diagnostics

The short table counts actual window-specific cached entry/decision fills changing zero/long into short. Adding to an existing short is not another trigger. Guard onsets are separate.

Correct 1/3/6h means a unit short from that onset to the corresponding hourly price would earn a positive return after two 0.10% fees and a declared 0.05% half-spread per side. Wrong direction and a small fall that still loses after costs are separate. Missing prices and labels extending beyond the replay endpoint are unresolved, rather than invented wins/losses.

Those horizon labels examine market direction even if the actual strategy covered earlier. Cover behavior is separately exported. Additions and partial covers prevent exact position-size attribution: unit-short cover proxies are not actual account short PnL. Hourly TP/SL samples cannot resolve intrahour ordering; every barrier retains that ambiguity.

Use the number of historical windows with onsets as evidence support. Thousands of events within a few windows are correlated. Precision intervals resample quarterly clusters of counts, not independent-trade binomial trials. The CSV also has window-average precision, unit-short proxy return, cover/rebound/censor counts and minimum-onset status. This table does not enter the main ranking.

Minute/second strategies require a separate correctly time labelled executable bid/ask or finer-bar simulator, realistic signal and order delays, and out-of-sample episodes. Existing hourly caches and current live-only quotes cannot validate those historical timings. The pipeline does not convert a fast strategy into validated HFT; directional competition rules still apply.

## Test a new registered model

Implement/register your model using the existing project model contract. Keep its parameters in config.yaml. From Book's worktree run:

    .venv/bin/python -B -m backtest.run --model book_NAME --score2

This computes the ordinary full compatible scoring cache, appends the new revision to registry_2.jsonl, writes immutable permodel evidence, and regenerates the secondary Markdown/CSVs/ranks. It does not add that run to the original registry.

To publish the same computation to both boards:

    .venv/bin/python -B -m backtest.run --model book_NAME --score --score2

To rebuild the secondary tables without retraining:

    .venv/bin/python -B -m backtest.scoring leaderboard2

To import all models pinned in this study:

    .venv/bin/python -B -m backtest.scoring import-score2

Run heavy commands through your own scripts/lock, nice 10 and mm-book-* tmux session, respecting the server rules. A new model need not reproduce the old model's code, but must use the same scoring tool, data inputs, full window order, fee contracts and cache dimensions. Changed evaluation/data/window protocols or incomplete/corrupt artifacts fail closed.

The latest same-name model revision is displayed; earlier revisions remain in the append-only logical registry and immutable artifact directories. Every new included model can change simultaneous bounds and ranks. Multiple-comparison adjustment covers currently compared models, not every abandoned experiment. Record all attempts and reserve independent prospective paper testing.

## Evidence and implementation

Frozen inputs/cases: results/book/20261009-weak-eval-v2; full REPORT.md and model_windows.csv explain evidence. Cases are frozen before candidate scenario comparisons. Version 1 in results/book/20261009-weak-eval preserves source discrepancies; the October 8 failed generic evaluator remains results/book/20261008-regime-eval.

Code: research/book/weak_eval/prepare.py and run.py freeze inputs/cases; backtest/scoring/weak_stats.py selects cases and computes uncertainty; weak_risk.py computes money/risk metrics; weak_short.py builds onset labels; weak_board.py verifies compatible evidence and publishes; weak_render.py writes the reading guide.

Source scores, vectors and short ledgers are under results/scoring/score2/<protocol>/<model>/<runkey-scorehash>/. The checkpoint/code hashes define the protocol. New rows automatically update the board, while a new market checkpoint requires a separately frozen evaluation version.

The board is a fresh-cash research baseline. Current EC 2 holdings, executable switching cost, competition short permission and real account fills remain UNVERIFIED. A good historical rank supports further model testing, not an automatic live-bot switch.
