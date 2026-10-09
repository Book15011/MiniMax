# Book short research: where to look and how to use it
Eight methods are now ranked. The slower breakdown ranks first by the conservative return bound and worst-profile mean, but its archive-full average is still -0.032%. Persistent flow ranks first for accuracy: 42/107 completed cycles (39.25%), versus the original flow 33/110 (30%). Its recent-prefix return improved from +0.493% to +0.596%, while its broader mean remains -0.076%. Every method failed the stronger-evidence rules; these are research leads, not verified live replacements.

Everything is remote under /home/ubuntu/test/MiniMax. Feature/book-intraday-short is Book's research branch; nothing here changes the live bot.

## Read these first
1. /home/ubuntu/test/MiniMax/results/scoring/leaderboard_2.md: unchanged conditional hourly model selection plus ranked short-proxy accuracy/return section. Registered models evaluated with --score2 update this automatically from this branch.
2. /home/ubuntu/test/MiniMax/results/book/20261010-intraday-short-v4/leaderboard_short.md: all eight minute short-only experiments, separate accuracy and return ranks, net returns, CS and risk. Publication waits for completed validation.
3. /home/ubuntu/test/MiniMax/results/book/20261010-intraday-short-v2/leaderboard_short.md: frozen first five methods and their original family adjustment.
4. /home/ubuntu/test/MiniMax/.worktrees/book-book-short-next/research/book/short_next/RESULTS.md: completed three registered short-capable models, same-period clone baseline, chronology/cost tests and verified limitations.
5. /home/ubuntu/test/MiniMax/.worktrees/book-book-clone-reconcile/research/book/clone_execution_fit/RESULTS.md: frozen reconstruction, all agreement misses, timing rules and tests. Literal matching remains19/33, below85%.

## What each minute number means
- **Rank** prioritizes experiments using the worst family-adjusted lower return bound across two causal weak-market profiles and216/228/240h. It does not promise profit. All tested methods remain counted.
- **Accuracy rank** uses lower90% completed-cycle hit rate across both weak profiles. **Return rank** uses the worse profile's mean228hreturn. They answer different questions.
- **Wins/closed** counts actual executed short episodes fully covered before the endpoint. A win is positive dollars after both fees/spreads. Adds are not extra episodes; these prototypes do not rebalance existing short quantities.
- **Censored** counts shorts still open at the horizon. Forced terminal covers enter return but not accuracy. Never read5/5 as stable100%accuracy.
- **Mean/median/P10/worst** include every window, including zero-trade windows. Returns use100k initial cash with at most25%intended short entry gross and10%percoin. They are not100%invested return or additive live-account contribution.
- **MDD** measures maximum sampled minute loss from a previous equity peak. **CS** retains daily0.4Sortino+0.3Sharpe+0.3Calmar FLOORED.V1 conventions, with sampled minute MDD in Calmar. CS UTC changes the dayclock. There is no separate implemented CSL.
- **Stronger evidence** requires all declared counts, quarters, lower return bounds and stress/control rules. A first place can still fail. No threshold is lowered to force a pass.

The original hourly short table measures unit-notional fixed1/3/6h directional proxies, even if a model already covered. The new minute table measures actual quantity-dependent cycle results. Do not mix them into one hit rate.

## Run or publish
Run from /home/ubuntu/test/MiniMax/.worktrees/book-book-intraday-short.

Registered hourly candidate: .venv/bin/python -B -m backtest.run --model MODEL_NAME --score2
This performs original gates and conditional scoring, registers the revision and regenerates leaderboard_2 including the ranked hourly short section. The checkpoint/metric stay frozen. Owners review before any main merge.

Frozen minute initial evaluation: .venv/bin/python -B -m research.book.intraday_short.run --score
Frozen minute persistent follow-up: .venv/bin/python -B -m research.book.intraday_short.run_persistent --score
These use a separate minute research protocol. Completed evaluation artifacts cannot be overwritten. Raw manifests, before/after hashes and per-case actual fill ledgers are saved.

One-command audited board publication after a completed run: .venv/bin/python -B -m research.book.intraday_short.score --score --phase slow
Use --phase initial for the preserved five-method board. This checks completed tests/data/evaluation, independently audits fills if needed, calculates ranks and refreshes the hourly-board link. It refuses incomplete/failed runs. Nothing auto-deploys.

A new minute model needs a new named pure hypothesis, version/output directory and frozen protocol before outcomes; reuse the same historical cohorts and verified input files. The current shared ModelSpec supports hours, not minutes, so these prototypes are not disguised as live-compatible registered hourly models. Shared-contract changes require all three owners under AGENTS.md.

## Execution and evidence
Signal checks every15completed minutes; every completed minute monitors active stops/targets; entry and cover execute one minute later. Three-minute latency and doubled fees/spreads are rerun, including changed fill paths. At mostthreepositions, residual cash. No inside-minute perfect stop/target fill claim.

Twenty APIcalls/minute/process is a ceiling, not a requirement to trade constantly. Public ticker can return allpairs once. Accountlimit30calls/min includes queries and other processes. This offline study makes no competition APIcalls; no existing bots or collectors were changed.

All68unique historical weak/control starts plus the recentprefix are retained. Primary cohorts have25each; returns are not selected on future decline. Four-coin dataset uses184publisher-checksummed archives and19,095,144independently reconstructed OHLCV/flow cells. V1five-coin plan failedSOLJuly2020 beforelisting; v2 removesSOLglobally before returns and keeps everywindow. Separate freshBCH29/30failure remains. Early-closed exchange-halt bars are used at nominal minute-end, conservatively later; initial stricter audit failure is preserved.

The recentprefix is spent; the clone was fitted on it. Papers in RESEARCH.md motivate hypotheses rather than validate our exact thresholds. Full risk, false/positive signals, costs, source hashes and all failures stay visible.

Slower-range experiment: .venv/bin/python -B -m research.book.intraday_short.run_slow --score. Its run_slow_all.py runs tests, evaluation, independent audit and publication in one locked batch. Completed source/evidence cannot be overwritten. The initial7 remain in v3 and v2.

Validation complete: 541 full-suite tests passed on the frozen worktree; independent archive audit matched 19,095,144 cells; 1,656 execution ledgers reconciled. The earlier Git clean/dirty determinism failure is preserved and was resolved by freezing the worktree before rerunning.

Operational scope: these are supplemental sleeves without an activity guard or verified live adapter. Roostoo ticker lacks taker-buy quote flow; flow models need another live feed. Completed minute OHLCV/flow availability on deployment is UNVERIFIED. No live feed, signed endpoint or running bot was changed.
