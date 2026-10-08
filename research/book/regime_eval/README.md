# Book market-regime evaluator

This is offline research in Book's isolated branch. It adds no live strategy, official score or registry change.

Remote worktree: /home/ubuntu/test/MiniMax/.worktrees/book-book-regime-eval
Branch: feature/book-regime-eval
Start with RESULTS.md for findings and RESEARCH.md for evidence and the protocol.
Raw outputs: /home/ubuntu/test/MiniMax/results/book/20261008-regime-eval/

The completed evaluation leaves adaptive weights disabled. The confirmation direction guard and current breadth/data-confirmation guards did not pass. Software tests and cache accounting checks passed; they do not establish a profitable trading strategy. The model table is descriptive historical continuation evidence, with production ranking disabled.

## Alignment and model coverage

The round used here is October 4 12:00 to October 18 12:00 UTC, from docs/EVALUATION.md and deploy/README.md (competition 538). Older AGENTS dates differ. The frozen checkpoint is October 8 12:00 UTC: a 96-hour prefix and 240-hour remainder.

Historical model runs retain their registered 336-hour horizon and original execution assumptions. Features are observed at t0 + 96 hours. Selection reads only features; outcomes and model returns are joined after selection. A training run must end before the query minus the 24-hour embargo. Each prior pool fits its own percentile transforms.

The model table includes all 38 compatible registered models: 31 candidates and seven references. Another 56 unregistered cache names are inventoried as unassessed. Each model continues its own historical holdings at hour 96. Switching from shared incumbent holdings remains unvalidated.

## Reproduction

Run remotely. Read main:AGENTS.md and work only in Book's worktree. Check scripts/status before heavy work; use an owned tmux session and lock for long runs.

    ssh metallurgy-server "cd /home/ubuntu/test/MiniMax/.worktrees/book-book-regime-eval && scripts/lock book-regime-eval -- nice -n10 .venv/bin/python -B -m pytest -q -p no:cacheprovider --basetemp results/book/20261008-regime-eval/pytest-review"
    ssh metallurgy-server "cd /home/ubuntu/test/MiniMax/.worktrees/book-book-regime-eval && scripts/lock book-regime-eval -- nice -n10 .venv/bin/python -B -m research.book.regime_eval.run --stage validate"
    ssh metallurgy-server "cd /home/ubuntu/test/MiniMax/.worktrees/book-book-regime-eval && scripts/lock book-regime-eval -- nice -n10 .venv/bin/python -B -m research.book.regime_eval.run --stage compare"

Validate reuses frozen snapshots, verifies their hashes and checks immutable historical data. registered_snapshot.json pins model selection; a later registry publication cannot change this checkpoint. Compare verifies registered score hashes, exact cache row order and dimensions, all original liquidated returns within 1e-12, and cache file hashes before and after reading. Subsequent comparison runs reject altered cache inputs. No network or trading API is called by these stages.

All research tunables are in config.yaml under book_regime_eval. Existing strategy and scoring blocks are unchanged. A new asof or protocol requires a separate output directory; preserve this failed checkpoint rather than overwrite it.

## Review files

| File | Purpose |
|---|---|
| RESEARCH.md | Frozen directional judgment, primary sources, contrary evidence and protocol |
| RESULTS.md / output REPORT.md | Completed decisions and all model summaries |
| validation.json / walkforward.csv | SCREEN choice, confirmation scores, intervals, skipped queries and gates |
| coverage_exclusions.csv | Five historical windows without adequate BTC outcome coverage |
| lookalikes.csv | Legacy descriptive cases, feature distances and explicit t0 + 96h state times |
| incumbent_case_windows.csv | Historical e20 prefixes and remainder returns, with paper-path differences |
| all_registered_models.csv | All model diagnostics, original gates and paired uncertainty |
| registered_snapshot.json / model_inventory.json | Exact selected registry entries, provenance and scratch inventory |
| input_manifest.json / cache_inputs.json | Frozen raw data and cached trajectory hashes |
| paper_prefix.csv | Exact 97-point paper path for the observed 96 hours |
| short_diagnostics.json / short_timing_table.csv | Separate short table with unvalidated status and missing metrics |
| verification.json / full_suite_final.log | Commands, exit codes, elapsed time and full test result |

## Limits that affect interpretation

The paper CSV is a replay from cash. Its "deployed live" column label does not verify the actual EC2 account, deployed code, fills or holdings. Current model source/parameter identity can match the saved cache, but the paper CSV does not embed immutable historical execution identity.

BCH is absent from the configured competition ticker universe. The frozen broad top-30 query therefore has 29 exact 48-hour endpoints. The unchanged 98% guard rejects breadth. Hourly data after the October 8 00:00 archive boundary are ticker-assisted and cannot pass the archive-confirmation guard. The broad universe was not restricted to force activation.

Existing legacy CORE matching provides 25 descriptive cases for the requested prefix comparison. Its within-day asset closes can be stale. It never repairs the new query's coverage failure or changes uniform fallback weights. Prefix resemblance uses already observed market data, so it is not an independent predictive test.

The 2,293 overlapping windows are not 2,293 independent episodes. Paired bootstrap draws use 76 calendar-month clusters; dependence across months can remain. Family-adjusted intervals are nominal bootstrap approximations and do not erase prior strategy-development search. They are not forecast confidence intervals for the remaining competition.

A faithful model switch requires shared holdings, accrued activity, pending orders, candidate state initialization and executable transition costs. No production ranking is enabled here.

The short metric requires executable entry bid and cover ask, both-side fees, positive entry and cover delays, and independent episodes. There is no validated executable candidate ledger. Minute OHLC cannot establish seconds ordering; recorded second quotes cover only about three days. Short capability remains UNVERIFIED, and the main HFT prohibition remains in force.

Reviewer sign-off and any future merge are separate. This branch has not been merged or deployed.
