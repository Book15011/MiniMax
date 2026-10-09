# Independent chronological validation of fixed short candidates

Owner: Book. Branch: feature/book-short-validation, based on commit 9fb7b1f.
This helper reads compatible published caches and writes only its dedicated results/book directory. It does not train, retune, publish a leaderboard, modify a registry, refresh a checkpoint, or deploy.

## Fixed diagnostic design

Models are frozen before these results are read. There is no fitting or parameter selection within folds. All available historical observations are spent. These are retrospective chronological robustness diagnostics, not an untouched holdout or prospective validation.

The eight six-month blocks run from 2022H2 through 2026H1. A single global schedule starts at 2022-07-01 12:00 UTC and advances 14 days. Each 228-hour cash-start path must fit wholly inside a block; paths crossing boundaries are excluded. The resulting schedule has 97 cases: 13 in 2022H2 and 12 in each later block. Missing scheduled starts fail closed. Direct return-path overlap is absent; broader market dependence remains.

Comparators are exact zero-return cash, BTC hold (run 5b0347ac404fbc72), fixed e20 (pol_switch_vt_tl_e20v45, run 0ec3cf0ca1185b36), and equal-weight long (team_ew_daily, run cc675a2b2acfc99f). Equal-weight long is a negative control for the bearish hypothesis; it is not an equal-weight short strategy.

## Run after ordinary score2 publication

First run each registered candidate through the unchanged scorer from the short-study worktree:

    scripts/lock harness-book-weak-score -- nice -n 10 .venv/bin/python -B -m backtest.run --model book_NAME --score2

Omit --score to preserve the original board. Never rerun prepare or change the frozen query, horizons, fees, or global harness settings.

Then run this helper from book-book-short-validation, supplying explicit final run keys:

    scripts/lock book-short-validation -- nice -n 10 .venv/bin/python -B -m research.book.short_validation.run --candidate book_short_trend=RUNKEY --candidate book_short_rebound=RUNKEY --candidate book_short_breakdown=RUNKEY --out /home/ubuntu/test/MiniMax/results/book/20261009-short-validation

Each RUNKEY contains 16 lowercase hexadecimal characters. No candidate module is imported, so this helper cannot accidentally train or evaluate different current code. Candidate cache hashes must match score2 publication attestations. Every original full-cache liquidation return must reproduce published R_liq. Fixed comparator scores and caches are checked against their frozen manifests. Sources are hashed before and after analysis.

## Outputs and definitions

- fixed_cases.csv: exact starts, block boundaries, and 228-hour endpoints.
- window_metrics.csv: return, MDD, CS, UTC-CS, component ratios, and shortened activity, turnover, and costs.
- fold_summary.csv: eight blocks and pooled ALL; mean, median, P10, worst-10% mean, worst, positive share, risk, and trading activity.
- paired_summary.csv: same-window return advantages against each comparator, including the distribution of paired differences.
- manifest.json: explicit revisions, source/cache hashes, protocol and analysis identities, and limitations.
- REPORT.md: reading guide and pooled descriptive results.

Cached trading fees and spreads are already in equity. Endpoint liquidation is charged exactly once using the existing risk functions.

CS is unchanged FLOORED.V1 daily raw HKT: 0.4 Sortino + 0.3 Sharpe + 0.3 Calmar. Daily standard/downside deviation floors are 0.001; MDD is floored at 0.002. Calmar uses daily mean return divided by MDD. UTC sensitivity is separate. Actual competition formulas remain organizer-dependent. This CS does not substitute original 14-day CS_HIT or weak-board CS_HIT_positive.

Activity is reconstructed from truncated ledger fills using HKT days bounded at 16:00 UTC. Exact-endpoint fills affect costs, turnover, and equity but lie outside activity buckets, matching the existing scorer. A day with both guard and strategy fills is a strategy day. Turnover sums absolute changes in cached asset weights; a sign flip counts as two orders. Fees and spreads are divided by initial capital.

Cost stress is not fabricated by scaling final returns. A genuine stress requires executable replay with changed fees/spreads and a separate protocol. These chronological tables do not create a new rank or replace the frozen weak-market score.

## Independent model audit

audit_models.py reads the frozen study worktree and checks causal data truncation, partial/missing prices, discontinuous clocks, missing/negative volume, holding state, re-entry, exact clock phases, risk limits, and source fingerprint coverage. Expected trading cases explicitly require nonempty targets.

    nice -n 10 .venv/bin/python -B research/book/short_validation/audit_models.py --study-root /home/ubuntu/test/MiniMax/.worktrees/book-book-short-study --expected-commit 02b06ff --out /home/ubuntu/test/MiniMax/results/book/20261009-short-validation-model-audit.json

Audit of 02b06ff passed 38 assertions. The three wrapper constructors and shared helper enter three distinct source fingerprints. Source files and HEAD remained unchanged during the audit. This validates specified behavior, not future profitability or executable fills.

## Source and scoring audit

Read-only preflight confirmed protocol 603da2948b68ee0f5c8a and scoring tool 3036a0d8bfdaa6a0. Historical sources in /home/ubuntu/test/MiniMax/data/validation:

- panel_close_1h.parquet: dca38811d268d2c8a47c2adb47d2caef99bbe477bd38fe9dffbcedd4581b3294
- panel_quote_volume_1h.parquet: aafb8d2f0ed3c7eeebf1b40e4cbd20934827c622f7717251d51a48d59d5afa0a

Existing score2.signature and tool_version use data notes rather than raw panel bytes. This helper independently enforces those frozen source hashes and records current universe/spread hashes. The original frozen manifest does not supply a universe-byte hash; that remains a limitation. Growing live stores are not expected to retain their old hashes; the dated query uses immutable snapshots.

Historical universes are point-in-time liquidity selections filtered to the current configured Roostoo list. Static modern spread snapshots are proxies. Minimum-order skipping is approximate in the hourly weight simulator. Shared planner/paper-broker replay remains necessary for minute-level sizing comparisons.

The unchanged harness anchors schedules at 16:00 UTC. A 09:00 HKT model therefore uses hourly cadence and gates decisions at 01:00 UTC, including bootstrap. Execution still has the scorer's one-hour lag. This cannot certify the separate ±2-minute execution target.

The frozen weak checkpoint remains results/book/20261009-weak-eval-v2. It contains two cohorts of 25 causal weak-state cases, an archived broad profile and a separate fresh BTC sensitivity. BCH absence preserves 29/30 fresh breadth coverage and the old adaptive failure.

The 216/228/240-hour contexts, cash/fixed-e20 comparisons, 20,000 shared quarter bootstrap draws, overlap-cluster merging, and simultaneous current-model penalty remain unchanged. Repeated abandoned research is not fully corrected by that penalty.

## Competition endpoint conflict

AGENTS.md contains older Oct17 and start-clock text. The original dated report, reports/review/20261001-realtest-findings.md:32, records public GET /v1/competition_list for competition 538 as 2026-10-04 12:00 UTC to 2026-10-18 12:00 UTC. deploy/README.md:95 and docs/EVALUATION.md:40 agree.

The frozen 228-hour horizon runs from Oct9 00:00 UTC to Oct18 12:00 UTC. One unsigned, credential-free public listing request during this audit returned HTTP451/non-JSON. The endpoint is documented October1 API evidence, not fresh organizer verification. Never silently change it or the frozen protocol.

## Requirements for later strategy walk-forward selection

src/validation/walkforward.py evaluates lookalike forecast CRPS, not candidate strategy performance. If later work selects parameters per fold, train only on preceding observations; purge all 14-day label paths crossing the test boundary and add a 24-hour embargo. Record every attempted variant and selection rule. Test outcomes must not choose that fold's model. Reserve new post-freeze paper sessions for prospective confirmation. This helper intentionally performs no fold selection.

## Observed-portfolio comparison limits

The supplied ledger is an actual-period benchmark. It cannot be replayed historically as an identified strategy until its rules are recovered. The supplied history and already inspected Oct8-9 checks are spent.

