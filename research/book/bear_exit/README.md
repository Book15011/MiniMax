# How to use these short-strategy results

Start at /home/ubuntu/test/MiniMax/results/scoring/leaderboard_2.md for the main model comparison. The normal --score2 command updates it when a registered model finishes. The broad historical headline and the weak-market selection score answer different questions; a positive old headline does not make a negative weak-market return acceptable.

The detailed equal-risk comparison for these four candidates is /home/ubuntu/test/MiniMax/results/book/20261010-bear-exit-v1/leaderboard_short.md. It is published only after all model runs, 2,460 independent execution checks, terminal money/quantity checks, and exact reproduction of 615 unchanged guard-control ledgers pass. If that file is absent, the batch is still running or failed; batch.log and status.json show why.

Read the table in this order:

1. **Evidence:** FAIL means the model has not earned a reliable-improvement claim. Rank 1 with FAIL is still an unsupported live switch.
2. **Return, P10 and Worst:** mean return includes all 25 lookalikes, including cash/no-trade windows, after execution costs and endpoint closing costs. P10 and Worst show adverse outcomes.
3. **Wins/closed and Accuracy:** a naturally completed short is correct only when its total net profit after fees/spread is positive. Partial covers belong to the same episode. An open-at-end episode is censored from accuracy and still contributes closing-cost return.
4. **MDD and CS:** MDD is minute peak-to-trough equity loss. CS uses 0.4 Sortino + 0.3 Sharpe + 0.3 Calmar as the existing research risk measure; competition final formulas remain unofficial. Check mean realised gross exposure because identical target caps do not mean identical risk actually taken.
5. **Lower return:** conservative rank uses the worst simultaneously adjusted quarter-cluster lower bound across two profiles and three horizons. It is a historical research statistic, not a guaranteed future return.

The separate /home/ubuntu/test/MiniMax/results/book/20261010-bear-exit-v1/entry_accuracy.md tests entry timing. It starts at an actual simulated first Open Short fill, hypothetically holds the first quantity unchanged for 1/3/6 hours, then charges a hypothetical cover spread/fee. It ignores actual earlier exits and later additions. Its 6h accuracy rank can disagree with completed-trade accuracy and return. Read win counts and firing windows alongside the percentage. Neither is the clone's 85% same-coin/action/time/quantity agreement target.

All four candidates share 25% gross / 10% coin target caps and hourly decisions with 1h lag. Guard is the unchanged control. Cost_guard restricts fresh entries using the size of the previous 6h decline relative to estimated costs. Fast_exit adds faster price-reversal exits. Trail_exit adds exits after a rebound from the recent closed-price low. These are fixed hypotheses; no hidden entry-price stop or prediction of guaranteed profit is implied.

To rerun a registered model through the normal scoring interface:
~~~powershell
ssh metallurgy-server "cd /home/ubuntu/test/MiniMax/.worktrees/book-book-bear-exit && .venv/bin/python -B -m backtest.run --model book_bear_fast_exit --score2"
~~~
Replace the model name with another model already registered in this worktree and its config.yaml. This automatically updates the MAIN board and hourly target-onset proxy diagnostics.

To rebuild the completed frozen short table:
~~~powershell
ssh metallurgy-server "cd /home/ubuntu/test/MiniMax/.worktrees/book-book-bear-exit && .venv/bin/python -B -m research.book.bear_exit.score --score"
~~~
That command rerenders existing audited results; it does not silently add an arbitrary new model to this four-model experiment. A new actual-execution comparison needs a new version, declared candidate list, pinned parameters/data, all fixed windows/cost scenarios and independent checks. Never overwrite a prior batch to hide failures.

The main checkpoint remains October 9 00UTC, with a fixed 228h comparison horizon and 216/240h checks. These reruns do not mean 9.5 days still remain today or that current-market windows refreshed automatically. The fixed windows include later rebounds; future-down labels appear only in diagnostic stress tables. Adaptive activation remains disabled; missing BCH leaves 29/30 endpoints.

The prior selective v1 cutoff failure is retained; v2 fixes whole order-batch eligibility and passes all 2,460 ledgers. This new study uses the corrected rule and requires the guard execution artifacts to reproduce v2 exactly. The added control-reproduction publisher check was pinned before historical evaluation and does not change model behavior, scoring thresholds or normal metrics. See publisher_helper_freeze.json and control_reproduction_audit.json.

All history is spent retrospective research. The already-inspected actual-quote day, where the three new models stayed in cash, is a diagnostic rather than held-out profit evidence. No main merge, signed competition API call or live-bot change occurred.
