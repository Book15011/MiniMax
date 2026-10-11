# Continuous-trend recovery research

**No live switch recommended.** These are two fixed research candidates, with every failed check retained.
Historical requirements passed: [].
Passing code tests or a point-estimate leaderboard rank cannot establish future profits.

Book branch feature/book-quality-recovery; frozen numeric implementation1aaa397, protocol79f963f.
Parent reference book_e20combo_brk_cash from committed live-source ef1b0dd; actual EC2 deployment remains UNVERIFIED.

## What changed and why

The existing momentum score already divides trend return by volatility. This pair instead refines long selection:
require positive 7/14-day returns, keep top 12 parent-momentum coins, then prefer more positive daily steps.
book_recovery_quality ranks by daily sign consistency; book_recovery_quality_blend uses an equal rank blend with momentum.
Select 6/retain 12, volume and breakdown rules, daily decisions, costs and risk matching stay fixed.
Short targets remain exactly the parent output given the same decision view. Later paths can differ through carried portfolio memory.
The UP-regime long overlay does not introduce a new short entry/cover strategy; DOWN mode is the exact parent.
Q averages (positive days minus negative days)/days over 7/14-day formation. Zero days count in the denominator.
Q measures historical path consistency, not future win probability, short accuracy, F1 or clone agreement.
No eligible candidates or missing risk evidence => exact parent fallback. New long covariance risk and full signed variance cannot increase.
This estimate does not guarantee lower realized losses; equal allocation can concentrate when few coins qualify.

## Research basis

[Da/Gurun/Warachka2014 author paper](https://academicweb.nd.edu/~zda/Frog.pdf) studies continuous-information momentum in stocks.
Its formation/holding horizons are far longer than ours. Applying sign counts to 7/14-day crypto is an unverified adaptation.
The paper conditions on momentum first; a smooth flat coin is not a momentum signal. Sign counts do not measure jump magnitude.
[Grobys/Shahzad publisher abstract](https://onlinelibrary.wiley.com/doi/10.1002/ijfe.70036) discusses heavy-tailed crypto momentum risk.
Only its abstract was read. It supports caution about variance-based metrics; it does not establish a trading rule or prove our return mean undefined.

## How to read the results

Mean = average after modeled trading costs and terminal charge. Median = middle outcome. Bad10 =10th percentile, not worst-decile average.
Worst = minimum return. Drawdown is peak-to-trough loss; smaller is better. CS is the existing FLOORED.V1 composite.
Delta = candidate minus baseline on exactly the same starts; pp means percentage points.
There are 2,298 heavily overlapping cash-start14-day windows, NOT2298 independent tests. Historical data are spent calibration.
A conditional purged-quarter bootstrap uses 20,000 draws and tail 0.05/14 to retain all fourteen recovery hypotheses.
This is not project-wide post-selection control, a joint bound on every metric, or fresh evidence.

## Full-history and recent 14-day results

| Context | Model | Mean | Median | Bad10 | Worst | Mean drawdown | CS | Mean delta |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| all | book_e20combo_brk_cash | +3.7316% | +0.2833% | -11.5222% | -26.0494% | +10.7700% | 0.152300 | +0.0000 pp |
| all | book_recovery_quality | +3.0161% | -0.4791% | -11.4490% | -27.1681% | +10.7270% | 0.133786 | -0.7156 pp |
| all | book_recovery_quality_blend | +3.2723% | -0.2943% | -11.2996% | -26.7833% | +10.7828% | 0.136037 | -0.4594 pp |
| recent_2024on | book_e20combo_brk_cash | +2.3785% | -0.5727% | -13.1801% | -26.0494% | +11.2913% | 0.095878 | +0.0000 pp |
| recent_2024on | book_recovery_quality | +1.6772% | -1.1939% | -13.1941% | -27.1681% | +11.1095% | 0.070948 | -0.7013 pp |
| recent_2024on | book_recovery_quality_blend | +1.6987% | -1.2236% | -12.9816% | -26.7833% | +11.2593% | 0.067096 | -0.6799 pp |

## Unchanged historical gates

- book_recovery_quality: historical pass=False; failures=['full_mean', 'full_median', 'quarter_lower_positive', 'recent_mean', 'weak_six_means', 'current_horizon_means_p10']; paired lower difference=-1.6314 pp.
- book_recovery_quality_blend: historical pass=False; failures=['full_mean', 'full_median', 'mean_mdd', 'worst_mdd', 'quarter_lower_positive', 'recent_mean', 'weak_six_means', 'current_horizon_means_p10']; paired lower difference=-1.1979 pp.

No failed trial is promoted by a newer diagnostic rank. Cost/delay extensions run only for original historical passes.
Earlier guard stress audit remains available: /home/ubuntu/test/MiniMax/results/book/20261011-recovery-stress-v1/README.md

## Fixed weak-market windows

Archived and later BTC-selected weak cases are reused without reselecting. 'Fresh' in that legacy label does not mean untouched outcomes.
Full absolute returns, drawdowns and CS for every horizon are in comparison.base.csv.

| Candidate | Case set | Days | Mean delta | Bad10 delta |
|---|---|---:|---:|---:|
| book_recovery_quality | weak_archived | 7 | -0.8866 pp | +1.2042 pp |
| book_recovery_quality | weak_archived | 8 | -1.2214 pp | +0.7063 pp |
| book_recovery_quality | weak_archived | 9 | -1.5358 pp | +0.3223 pp |
| book_recovery_quality | weak_archived | 9.5 | -1.4309 pp | +1.5964 pp |
| book_recovery_quality | weak_archived | 10 | -1.5138 pp | +1.2114 pp |
| book_recovery_quality | weak_fresh_btc | 7 | -0.3640 pp | +0.2134 pp |
| book_recovery_quality | weak_fresh_btc | 8 | -0.2806 pp | +1.3704 pp |
| book_recovery_quality | weak_fresh_btc | 9 | -0.4453 pp | +0.1742 pp |
| book_recovery_quality | weak_fresh_btc | 9.5 | -0.5905 pp | +0.0885 pp |
| book_recovery_quality | weak_fresh_btc | 10 | -0.5693 pp | +0.0796 pp |
| book_recovery_quality_blend | weak_archived | 7 | -0.4519 pp | +1.2630 pp |
| book_recovery_quality_blend | weak_archived | 8 | -0.7282 pp | +0.7792 pp |
| book_recovery_quality_blend | weak_archived | 9 | -0.9912 pp | +0.6708 pp |
| book_recovery_quality_blend | weak_archived | 9.5 | -0.9674 pp | +1.7066 pp |
| book_recovery_quality_blend | weak_archived | 10 | -1.0871 pp | +1.3675 pp |
| book_recovery_quality_blend | weak_fresh_btc | 7 | -0.1069 pp | -0.3244 pp |
| book_recovery_quality_blend | weak_fresh_btc | 8 | +0.0048 pp | +1.3704 pp |
| book_recovery_quality_blend | weak_fresh_btc | 9 | -0.1426 pp | +0.2823 pp |
| book_recovery_quality_blend | weak_fresh_btc | 9.5 | -0.3039 pp | +0.2503 pp |
| book_recovery_quality_blend | weak_fresh_btc | 10 | -0.3184 pp | +0.1877 pp |

## Calendar and concentration checks

Year rows remove paths crossing the calendar year;2020/2026 are partial.
All 14 disjoint-fortnight offsets are saved; offsets overlap one another and are not 14 independent replications.

| Candidate | Year | Windows | Mean delta |
|---|---:|---:|---:|
| book_recovery_quality | 2020 | 200 | -0.3079 pp |
| book_recovery_quality | 2021 | 351 | -1.3157 pp |
| book_recovery_quality | 2022 | 351 | -0.0720 pp |
| book_recovery_quality | 2023 | 351 | -0.5896 pp |
| book_recovery_quality | 2024 | 352 | -0.4121 pp |
| book_recovery_quality | 2025 | 351 | -0.8410 pp |
| book_recovery_quality | 2026 | 258 | -1.0265 pp |

book_recovery_quality: improves 34.16% of complete paths, trails 40.34%, ties 25.50%. These are paired portfolio outcomes, not short-trade accuracy.
Positive full-history disjoint offsets: 0/14.

| Candidate | Year | Windows | Mean delta |
|---|---:|---:|---:|
| book_recovery_quality_blend | 2020 | 200 | -0.4491 pp |
| book_recovery_quality_blend | 2021 | 351 | -0.6559 pp |
| book_recovery_quality_blend | 2022 | 351 | +0.0423 pp |
| book_recovery_quality_blend | 2023 | 351 | +0.0732 pp |
| book_recovery_quality_blend | 2024 | 352 | +0.0082 pp |
| book_recovery_quality_blend | 2025 | 351 | -0.8410 pp |
| book_recovery_quality_blend | 2026 | 258 | -1.4389 pp |

book_recovery_quality_blend: improves 34.86% of complete paths, trails 39.16%, ties 25.98%. These are paired portfolio outcomes, not short-trade accuracy.
Positive full-history disjoint offsets: 0/14.

## Independent verification

All 298 regular/research tests passed. Raw reconstruction checked 41364 return/drawdown/CS rows and 1011903 trade cost rows.
Maximum return/drawdown/CS discrepancy=0; maximum summary discrepancy=9.91e-17.
Maximum fee/spread discrepancyUSD=2.84e-14.
24 real historical decisions passed extreme-future append, short-target, gross and covariance checks.
Baseline raw hashes, inherited live-source files, old frozen future worktrees and fixed historical inputs were preserved.
An initial manifest attempt failed because two nonnumeric reporting files were added mid-run; its outputs/logs are preserved in attempt1_integrity_failure.
The repair reran identical cache keys after freezing reporting files. No strategy, parameter, gate, case or numeric input was changed.
Per-window first decisions are recomputed by the shared pure code but are not separately serialized in the cache.

## Leaderboard and future evidence

Shared recovery guide: /home/ubuntu/test/MiniMax/results/scoring/leaderboard_recovery.md
CSV includes CS and drawdown; rank compares the worse of 7/8-day means on the SAME 25 BTC-only matched cases.
Exact ties are alphabetical by model name; tied means do not show that one model is better.
Both new trials are added to 135-model joint diagnostics, including failures. Ranked means are not promotion scores.
The uniform lower differences cover 135 models * 2 horizons with 23 purged cases in 14 quarters; broad BCH coverage still fails29/30.
Adaptive stays OFF. --score does not refresh this separate diagnostic automatically.
Reproduce from this worktree: python -B -m research.book.quality_recovery.run; then audit, publish_review and report modules.
These commands are offline research and write results; avoid duplicate runs while an owned job is active.

Separate frozen future cohort: baseline plus these two models, Oct12 00UTC toOct15 00UTC (Oct12 08HKT toOct15 08HKT).
Original three future cohorts are unchanged. No future scores exist yet; no automatic future job was created.
After all required bars validate, run forward only from /home/ubuntu/test/MiniMax/.worktrees/book-book-quality-recovery.
One3-day path is insufficient to certify an edge and cannot erase historical failures.

## Practical limits

Actual EC2 holdings, deployment, endgame memory, pending orders, fills, refusal/fallback/precision and official endpoint remain UNVERIFIED.
The inherited cash-start simulator uses one historical spread snapshot and a proportional terminal charge, without a separately added terminal bid/ask spread.
Marked gross can drift above100% between capped targets. This is not proof of live rule compliance or an actual EC2 violation.
Original full competition eligibility for these research models remains UNVERIFIED; no model is production eligible here.
Clone imitation85% remains unmet; this study makes no new clone or short-accuracy claim.
The intended reliable better-model goal remains incomplete.
