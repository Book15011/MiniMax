# Score2: automatic checkpoint comparison

Owner: Book. Implementation branch: feature/book-score2. This feature has not been merged into main. Use a worktree containing this implementation.

Score2 adds the familiar model-run workflow to a separate historical continuation table. It preserves the original leaderboard and the frozen October 8 research study.

## Commands

Execute through ssh metallurgy-server and work in Book's feature worktree:

    cd /home/ubuntu/test/MiniMax/.worktrees/book-book-score2

New secondary board only:

    scripts/lock harness-book-score2 -- nice -n 10 .venv/bin/python -B -m backtest.run --model book_NAME --score2

Both existing and secondary boards, sharing one scoring computation:

    scripts/lock harness-book-score2 -- nice -n 10 .venv/bin/python -B -m backtest.run --model book_NAME --score --score2

Refresh the secondary board from its already published rows:

    scripts/lock harness-book-score2 -- nice -n 10 .venv/bin/python -B -m backtest.scoring leaderboard2

Import the original frozen 38 registered models:

    scripts/lock harness-book-score2 -- nice -n 10 .venv/bin/python -B -m backtest.scoring import-score2

Check scripts/status before heavy work and run long jobs in an owned mm-book-* tmux session. The outer harness lock differs from the publisher's internal scoring-score2 lock.

--score alone keeps its original behavior. --score2 alone does not append to the primary registry or regenerate leaderboard.md. It still computes the full competition-style score/cache required for compatibility and writes normal harness/score reports, followed by a per-model -score2.md report.

No scoring option opens the holdout. No publication deploys a model, changes the live bot or calls a signed competition API.

## Where to read

| File | Purpose |
|---|---|
| /home/ubuntu/test/MiniMax/results/scoring/leaderboard_2.md | Reading guide, evidence gates, all latest compatible model summaries and paper-prefix comparison |
| /home/ubuntu/test/MiniMax/results/scoring/leaderboard_2.csv | Detailed numeric table for analysis |
| /home/ubuntu/test/MiniMax/results/scoring/registry_2.jsonl | Separate append-only history of published score2 runs |
| /home/ubuntu/test/MiniMax/results/scoring/score2/ | Content-addressed source scores and immutable remaining-return vectors |
| /home/ubuntu/test/MiniMax/results/scoring/leaderboard.md | Existing team full-round leaderboard; separate scoring system |
| /home/ubuntu/test/MiniMax/results/book/20261008-regime-eval/ | Preserved original market study, validation, raw snapshots and 38-model evidence |
| /home/ubuntu/test/MiniMax/results/book/20261009-score2/ | Integration verification and end-to-end test logs |

The new board updates automatically after a successful --score2 publication. It displays the latest run of each model for this protocol, while its registry retains previous attempts. Exact repeat publication is idempotent. Ineligible full models remain visible with failed original gates.

The board's update is about MODEL RESULTS. The market checkpoint is frozen at October 8 12:00 UTC / 20:00 Shanghai. It does not move to the current time when a new model is scored.

## How to interpret Score2

The model's historical path starts from cash at hour zero. Its checkpoint is hour 96, with another 240 hours to run. Score2 measures:

    remaining return = E_336 * (1 - close_fee * gross_336) / E_96 - 1

Existing cached paths already include historical trading costs and execution lag. The additional terminal liquidation charges 0.1% on final gross notional. It does not erase losses in the initial four days or charge a fictional fee to close cash.

Every model continues its OWN historical holdings. This comparison does not simulate switching models from identical incumbent holdings, pending orders and accrued activity.

| Column | Meaning |
|---|---|
| score2_mean | Weighted mean remaining-period historical return |
| score2_median | Weighted middle result |
| score2_p10 | 10th-percentile bad-tail threshold |
| score2_worst | Worst observed remaining-period return |
| delta_vs_incumbent | Paired average difference versus the FIXED original e20 cache |
| delta_lower90 / delta_upper90 | Paired calendar-month bootstrap interval |
| delta_lower_family | Nominal multiple-candidate adjusted lower difference bound |
| original_eligible | Original scoring hard gates, not deployment eligibility |
| original_headline_ret | Original average return-threshold success score, not percentage profit |
| attempts | Published attempts under this score2 protocol |
| look_* | Legacy descriptive-case results; these do not repair failed adaptive gates |
| paper_* | Frozen paper-replay comparison, only for the model revision selected in the original study |

Decimal 0.02 means +2%; -0.10 means -10%. A positive mean is not a forecast for the coming ten days. Overlapping windows are not independent observations. Month clusters can remain dependent across months, and finite bootstrap tails are approximate. Multiple-model adjustment does not undo earlier strategy-development search.

The fixed incumbent remains the original cache even when the same model name is rescored with changed code or parameters. Revised model aliases do not inherit the old revision's paper-replay identity.

## What "adaptive disabled" means

The intended adaptive method puts extra weight on historical windows resembling the current market. That extra weight is allowed only after separate checks establish forecast usefulness, sufficient current coverage, confirmed input data and stability.

At this frozen checkpoint:

1. Average forecast-distribution skill improved, mainly for volatility and drawdown.
2. Direction nondegradation was not established. Brier degradation was -0.002326 on average, but its 90% interval was [-0.015777, +0.010862], still allowing harm. This does not prove the method worsened direction.
3. BCH has no competition ticker row at the checkpoint, leaving 29/30 exact breadth endpoints. The unchanged 98% coverage guard fails.
4. The archive was complete only through October 8 00:00 UTC; the 12:00 query includes ticker-assisted observations.
5. A common-account switch simulation and executable short-timing ledger have not been validated.

Consequently active alpha is zero and every historical window has uniform baseline weight. We can compute and publish historical diagnostics, but blank rank cells and production_eligible=false prevent presenting them as a validated production ranking.

Software tests establish implementation correctness. They cannot establish that the market matcher predicts direction or that a model will profit.

## What can improve the evidence

Book can investigate verified public archive backfills and construct a NEW checkpoint/version with complete, causal data. Preserve the failed snapshot. Missing BCH must not be imputed or removed merely to meet the guard. A revised competition-tradable universe is a separate declared method with consistent historical treatment and fresh validation.

Even complete data cannot automatically clear the statistical direction guard. Improving the matcher requires a defensible revised protocol and chronological/prospective evidence; changing thresholds or repeatedly searching this same confirmation period cannot manufacture reliability.

For switching models, the team can supply sanitized state exported by the running bot: holdings, pending orders, fills, accrued activity and deployed model identity. No secrets or manual competition-key API calls are needed or permitted for this research. Those records allow an account-aware transition study.

For a fast-short candidate, provide a causal trigger/cover implementation and executable quote/event ledger with latency, spread, both-side fees and separate independent episodes. The short table stays separate from the main score. HFT remains prohibited.

No additional information is required to use the new --score2 publication workflow.

## Integrity, versions and concurrency

Before expensive work, --score2 checks the configured frozen checkpoint. Publication requires a full run with the same scoring tool, data/input signature, ordered window set and compatible cached dimensions. It reproduces every original liquidated return within 1e-12 and checks cache hashes before/after reading.

Protocol identity fingerprints the checkpoint and metric/publisher source files. Changed scoring definitions cannot silently mingle with old rows. After an intentional scorer revision, run import-score2 to seed the new protocol's existing model set.

Source score files and remaining-return vectors are immutable and content-addressed. A separate lock serializes registry publication and board regeneration. Corrupt or incompatible inputs are rejected before registry/board mutation. Markdown and CSV files use atomic replacement.

--score --score2 publishes to two independent systems: if the secondary compatibility check fails after a valid primary publication, the primary result remains published and the secondary board remains unchanged.

Changing the market asof requires a separately reviewed checkpoint/protocol. The command deliberately does not rewrite the original snapshot or its registered_snapshot.json to admit new models.
