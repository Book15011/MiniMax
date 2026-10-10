# Book's selective short study: where to look

Start with the main scoreboard:
`/home/ubuntu/test/MiniMax/results/scoring/leaderboard_2.md`.

The four new registered models are `book_bear_trend_control`, `book_bear_guard`, `book_bear_pullback`, and `book_bear_breakdown`. The ordinary `--score2` command adds each completed run there automatically. Main original and stronger gates still apply. Research rank alone is not a recommendation to replace the live bot.

For these four models' actual short performance, use:
`/home/ubuntu/test/MiniMax/results/book/20261010-bear-selective-v1/leaderboard_short.md`.
Its CSV and reading guide contain conservative rank, mean/median/P10/worst return, completed short wins/closed, accuracy rank, minute MDD, CS and realised exposure. All four have the same 25% gross and 10% coin target ceilings. A low-use strategy can still have lower realised exposure. No-trade windows remain included.

For “did the entry catch the fall?”, use `entry_accuracy.md` or `entry_accuracy_1h_3h_6h.csv` in that same result folder. These start from the simulated short's actual first fill after delay, rounding and band checks. They measure a hypothetical fixed 1, 3 or 6 hour hold after both fees and spread. An entry near the test endpoint may lack a full outcome and is censored. The separate main `short_leaderboard_2.csv` uses hourly TARGET onsets; its denominator can differ.

For “did the whole short trade make money?”, use completed episode accuracy in `leaderboard_short.md`. An episode aggregates additions and partial covers until flat. A win means net profit after costs. For example, 18/50 would mean 18 winning completed episodes out of 50, or 36%; it would not mean 36% portfolio return or clone agreement. Still-open episodes contribute to total portfolio return after endpoint closing costs, but are excluded from completed accuracy. Always read the censored count.

For “what if the market actually falls?”, use `scenario_summary.csv` and its down/rebound table in the guide. These subgroup labels use later historical BTC prices and are explicitly retrospective diagnostics. They never choose the main windows or enter model decisions. The main table averages all 25 fixed archive-weak lookalikes, not only hindsight winners, over 228 hours (9.5 days). A second recent-BTC profile and 216/240 hour endpoints check sensitivity. The 228 hours are a frozen benchmark; they are not today's remaining competition time.

Risk and evidence matter alongside accuracy. MDD is the largest peak-to-trough portfolio loss; lower is better. CS keeps the existing 0.4 Sortino + 0.3 Sharpe + 0.3 Calmar formula; higher is better, and it is not a percentage. Conservative rank uses the worst lower return bound across both profiles and all three horizons. FAIL means the model did not satisfy the full evidence rules. A strategy that stays in cash can rank well descriptively and still fail the required signal-count and positive-improvement tests.

These new models make hourly decisions with a one-hour execution lag. The earlier minute hypotheses remain separately at:
`/home/ubuntu/test/MiniMax/results/book/20261010-intraday-short-v4/leaderboard_short.md`.
The new minute price records improve valuation and label resolution; they do not make the new models second-level or minute-level entry strategies.

The actual-quote October 9 diagnostic is at:
`/home/ubuntu/test/MiniMax/results/book/20261010-bear-quote-day-v1/RESULTS.md`.
It was already inspected and is not a holdout. The earlier model fee/rebound loss attribution is at:
`/home/ubuntu/test/MiniMax/results/book/20261010-price-loss-diagnostics-v1/RESULTS.md`.
Its best sampled exit values use hindsight and cannot be treated as attainable trading rules.

A genuinely future October 11-12 UTC comparison is preregistered under `research/book/bear_selective/forward`. It has no scores yet and is not an active scheduled job. The clone's 85% same-coin/action/time/quantity target remains separate; its frozen October 10 predictions have not changed.

To test another registered model, run remotely in this Book worktree:

```bash
cd /home/ubuntu/test/MiniMax/.worktrees/book-book-intraday-short
.venv/bin/python -B -m backtest.run --model NEW_MODEL --score2
```

That automatically updates the main secondary scoreboard. Use a Book tmux session, `scripts/lock`, and `nice -n 10` for long runs. The supplemental study is a frozen cohort: adding another model requires a new declared version/output directory, not overwriting this batch. Configuration is in root `config.yaml` and `research/book/bear_selective/config.yaml`. It must pass the model/causality/money tests, shared-broker replay and unchanged evidence checks.

Batch status and failure logs are in the result folder. Complete publication requires all normal-score jobs, the 2460 historical ledgers, terminal cash/quantity reconciliation and report manifest. A running or failed batch must not be called a reliable result. No main merge, live change, signed competition API call, or threshold relaxation is part of this work.
