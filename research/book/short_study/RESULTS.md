# Research and tested short models — Book

**Decision: reject these three new candidates as a reliable replacement. All are now on leaderboard_2.md. The 85% execution clone target is still unmet.**

Research led to three fixed mechanisms rather than another unrestricted indicator sweep. The implementation and validation work is complete. The results do not establish a profitable replacement; no strategy has been deployed. All history is spent and no prospective performance is claimed.

## Where to look first

- Shared updated board: /home/ubuntu/test/MiniMax/results/scoring/leaderboard_2.md
- Machine-readable rank/risk rows: /home/ubuntu/test/MiniMax/results/scoring/leaderboard_2.csv
- Separate short correctness table: /home/ubuntu/test/MiniMax/results/scoring/short_leaderboard_2.csv
- Immutable copy for this report: /home/ubuntu/test/MiniMax/results/book/20261009-short-study-v2/leaderboard_snapshot
- This report: /home/ubuntu/test/MiniMax/.worktrees/book-book-short-study/research/book/short_study/RESULTS.md

## New models and weak-market results

These are after-cost historical cash-start cases selected using only conditions at their start. The main horizon is 228 hours, with 216/240-hour sensitivities. Both frozen profiles and cash/fixed-e20 comparisons enter the conservative score. Higher selection score is better; it is a simultaneous lower advantage bound, not expected profit. Original gates test engineering/activity; passing them does not prove superior returns.

The snapshot has 53 model rows. Ranks and joint bounds can change when teammates publish more models; this copy pins the evidence read here.

| Model | Rank | Selection score | Mean 228h | Median | P10 | Worst | CS |
|---|---:|---:|---:|---:|---:|---:|---:|
| book_short_trend | 52 | -10.59% | -0.24% | -0.42% | -3.90% | -4.17% | 0.021 |
| book_short_rebound | 53 | -10.72% | -0.31% | -0.14% | -4.12% | -5.38% | 0.022 |
| book_short_breakdown | 48 | -9.32% | +0.37% | -0.00% | -0.24% | -0.84% | 0.044 |

The strongest originally eligible existing model remains baitoey_ovl_brk_dual in this snapshot: score -2.79%, archived mean +2.94%. It also has no positive stronger replacement evidence. None of the three new models improves that ranking.
Breakdown is the least weak of the new three, with lower exposure/tail losses. Its small positive average and mainly flat median do not establish an edge over cash or the fixed incumbent. Rebound exits did not improve the weak-profile average versus ordinary trend.

## How the three rules work

1. Trend measures each coin's completed 24/72/168-hour moves, scales by recent volatility, and averages/clips conviction. It can be long or short. It makes daily 01 UTC decisions, with a 25% per-coin cap,100% gross cap and conservative 1.25% daily volatility budget.
2. Rebound uses the same entries, with additional 01/07/13/19 UTC checks. A short is covered above the previous 24-hour close-high. Exit has priority and short re-entry waits until a later daily decision.
3. Breakdown shorts a fresh 72-hour close-low with a 1.5x volume confirmation and weak five-major breadth. It checks every 6 hours, closes above the previous 24-hour close-high, and retains cash when no qualifying signal exists.
Exact numerical settings are engineering priors, fixed before outcomes. They were not selected because they looked good on the supplied five dates. See PROTOCOL.md and config.yaml.

Primary research motivates these mechanisms but does not validate these hourly settings: [time-series momentum](https://www.aqr.com/Insights/Research/Journal-Article/Time-Series-Momentum), [volatility management](https://conference.nber.org/confer/2016/LTAMs16/Moreira_Muir.pdf), and [momentum rebound risk](https://www.nber.org/papers/w20439). Full citations, contrary evidence and failure modes are in research/book/short_research/RESEARCH.md.

## Did their shorts fire correctly?

The following uses the archived weak profile. It labels a fixed 6-hour unit short after declared fees/spread; it is not whole-position profit or a verified minute/second scalp. Onsets exclude resizing an already open short. Many onsets share the same historical window; do not treat them as independent.

| Model | Short onsets | Windows with onsets | Net-positive 6h / valid | Minimum30 onsets |
|---|---:|---:|---:|---|
| book_short_trend | 208 | 25/25 | 62/208 (29.8%) | True |
| book_short_rebound | 265 | 25/25 | 89/265 (33.6%) | True |
| book_short_breakdown | 29 | 12/25 | 16/29 (55.2%) | False |

Breakdown's 29 archived onsets fail the minimum 30 rule; its fresh profile has 32 onsets but only 27 valid 6-hour labels and 12 correct. No threshold was loosened. Inspect censored labels, confidence intervals and wrong-direction/cost failures in the separate CSV. A percentage alone is insufficient.

## Same recorded competition period

Common start 4 October 20:00 HKT; cutoff 9 October 09:15 HKT.100,000 USD seed. Fine-price replay reuses the shared planner/paper broker, with minute proxy before recorded quotes and as-of bid/ask thereafter. New models retain 1-hour lag; original clone retains its frozen 5-minute lag.

| Model | After full closing costs | Sampled MDD | Mean gross |
|---|---:|---:|---:|
| book_short_trend | +1.03% | 2.00% | 33.60% |
| book_short_rebound | +1.03% | 2.00% | 33.60% |
| book_short_breakdown | +0.70% | 0.57% | 6.44% |
| original_frozen_clone | +4.65% | 2.91% | 71.88% |
| observed_literal_ledger | +5.18% | 2.87% | 72.03% |

None beats the observed ledger. Trend/rebound produced identical fills because no rebound exit activated on this path. Lower risk partly reflects less exposure. All organic short cycles remain censored at cutoff; no completed-cycle hit rate is claimed.
Full trade/equity/fee evidence and 40-check independent valuation audit: /home/ubuntu/test/MiniMax/results/book/20261009-short-competition/README.md.

## Broader chronology and actual cost stress

An independent cache-only analysis verifies publication hashes and full original liquidation returns, then summarizes 97 nonoverlapping 228-hour paths across 2022H2→2026H1. Parameters are fixed throughout; these are retrospective chronological blocks, not nested out-of-sample model selection. Trend/rebound pooled means are +0.48%/+0.49%, breakdown+0.04%. The fixed incumbent averages+1.35% with much worse tails. Both return and risk matter; these broad means do not replace the conditional weak ranking.
See /home/ubuntu/test/MiniMax/results/book/20261009-short-validation-final/REPORT.md, fold_summary.csv and paired_summary.csv.

A separate 160-case 14-day-spaced replay doubles fees and halfspread. It reconstructs each original hourly equity path to 1e-12 before accepting stress results, then actually replays the changed costs and terminal close. It does not multiply final returns. These cases start in 2020 and differ from the 97-case chronology and the weak cohort.

| Model | Original-cost mean | Doubled-cost mean | Doubled-cost P10 |
|---|---:|---:|---:|
| book_short_trend | -0.20% | -0.49% | -3.89% |
| book_short_rebound | -0.19% | -0.49% | -3.90% |
| book_short_breakdown | -0.04% | -0.07% | -1.02% |

All 160-case averages are negative at original costs and worse at doubled costs. This is additional evidence against claiming an established trading edge. Cost-stress artifacts remain separate from the frozen primary metric: /home/ubuntu/test/MiniMax/results/book/20261009-short-cost-stress.

## What the cloning research established

Capped forecasts plus risk sizing naturally explain equal-dollar clusters; pure risk parity and a more complicated covariance optimizer do not explain the whole sequence. Several forecast caps produce identical fitting allocations but different later allocations, demonstrating why five daily sessions cannot identify a unique rule.
All 4,932 directed target candidates,64 shared scales each and 480 brokerage variants are retained. No later successful-looking setting replaces the training-frozen candidate. The largest full strict count among the tested shortlist remains 13/33. This does not prove every conceivable hidden rule is impossible.
Details: /home/ubuntu/test/MiniMax/.worktrees/book-book-allocation-mechanisms/research/book/allocation_mechanisms/REPORT.md. Corrected original: /home/ubuntu/test/MiniMax/.worktrees/book-book-observed-baseline/research/book/observed_baseline/CORRECTION.md.

## Reliability and limits

- Final model worktree: 472 tests passed; independent model audit 38 checks passed.
- Fine-execution worktree: 271 tests passed; independent signed-cash/wrapper/causality audit 40 checks passed; zero execution or valuation failures.
- Independent chronological helper: 466 tests passed. Directed clone 6 tests and separate cost replay 3 tests passed.
- Source/model/config/historical close/volume/universe/spread hashes are saved. Before/after study hashes match.
- Cache wrapper identity was repaired before first publication.72 synthetic cases retain identical targets. The earlier partial run is preserved and excluded; old key8b1089e686062d36 is not a final model revision.
- Fresh broad-universe failure remains29/30 because BCH has no competition ticker data. The old adaptive activation failure stays failed.
- Primary horizon preserves the documented October18 12UTC endpoint from dated public API evidence; fresh unsigned verification returned HTTP 451. Older AGENTS prose conflicts.
- Historical spreads are modern proxies; hourly minimum-order execution is approximate; current-list survivor constraints remain.
- No actual-account switch, minute-scalp edge, prospective validation or guaranteed profit is established.

## Testing another model and updating the board

Add a pure registered MODEL and its config.yaml parameter block in your own Book worktree based on compatible scoring code. From that worktree run:

```bash
scripts/lock harness-book-weak-score -- nice -n10 .venv/bin/python -B -m backtest.run --model YOUR_REGISTERED_MODEL --score2
```

This appends immutable secondary evidence and automatically regenerates leaderboard_2.md/CSV and short_leaderboard_2.csv against the same frozen profile. It does not refresh the market checkpoint. Do not change global scoring settings or rerun prepare to make a model pass.
To repeat these fixed candidates, research/book/short_study/run.py runs the suite and all three --score2 calls. Changed model/data inputs need a new experiment identity; existing snapshots are preserved.

## Frozen final model identities

- book_short_trend: e758f48cfbbba861
- book_short_rebound: 41ce2438da8f9330
- book_short_breakdown: 8b75f0d5cd989604

Implementation:317a600; wrapper identity repair02b06ff. Branchfeature/book-short-study; Book15011 commits. Model source: src/models/book/_short_study.py plus individual wrappers. Main and live bot were not changed.
