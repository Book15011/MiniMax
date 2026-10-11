# Recovery stress audit: no qualified replacement

**Decision: do not recommend a live switch from this evidence. Neither new guard passed the original
historical requirements. This extra audit cannot overturn those failures. Live was not changed.**

Book's branch: feature/book-recovery-stress. Numeric audit source b61c13d.
Exact frozen parent: book_e20combo_brk_cash at committed live-source ef1b0dd.
Models being checked: book_recovery_allshort24 (remove parent shorts rebounding over 24h),
book_recovery_rebound (remove parent shorts on broad BTC/coin 48h rebound), each with inherited risk matching.
No rule, parameter, case selection, score weight or live setting changed.

## How to read the evidence

A mean is the average result from cash over a fixed horizon, after modeled trading costs and the
configured terminal liquidation charge. It is not a prediction of the return left in this competition.
Median is the middle result. Bad10 is the 10th percentile, not the average loss of the worst 10%.
Worst is the minimum return. Drawdown is the largest peak-to-trough loss inside each path; it is shown as a loss size, so smaller is better.
CS is the existing FLOORED.V1 composite, not a new short-accuracy score. Higher is better but does not
override a failed return/downside gate. Delta is candidate minus baseline on identical windows;
pp means percentage points. Positive average delta alone is insufficient.

Each scenario tests all 2,298 original cash-start windows. These windows overlap heavily, so they are
not 2,298 independent experiments. Every past observation is spent historical evidence.
The added 5/6-day cuts supplement the existing 7/8/9/9.5/10/14-day cuts and do not replace original gates.

Scenarios: base =0.10% per executed side and 1h lag; double_cost =0.20% per executed side,
twice the spread, twice the configured terminal charge; extra_lag =2h lag with original costs;
combined = both adverse changes. The saved shared target decisions are identical across all four scenarios.
The stress replay simulates all original cash-start paths again; it does not subtract a flat fee estimate.

## Full-history 14-day outcomes

| Scenario | Model | Mean | Median | Bad10 | Worst | Mean drawdown | Mean CS | Mean delta |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| base | book_e20combo_brk_cash | +3.7316% | +0.2833% | -11.5222% | -26.0494% | 10.7700% | 0.152300 | +0.0000 pp |
| base | book_recovery_allshort24 | +3.6702% | -0.0066% | -11.0302% | -26.0494% | 10.4829% | 0.139817 | -0.0614 pp |
| base | book_recovery_rebound | +3.6267% | -0.0188% | -11.4583% | -26.0494% | 10.6767% | 0.144757 | -0.1049 pp |
| double_cost | book_e20combo_brk_cash | +3.0342% | -0.4472% | -12.2679% | -26.4247% | 10.9762% | 0.129750 | +0.0000 pp |
| double_cost | book_recovery_allshort24 | +2.9633% | -0.6717% | -11.8382% | -26.4247% | 10.7023% | 0.115305 | -0.0708 pp |
| double_cost | book_recovery_rebound | +2.9345% | -0.6620% | -12.1671% | -26.4247% | 10.8832% | 0.121873 | -0.0997 pp |
| extra_lag | book_e20combo_brk_cash | +3.6353% | +0.2735% | -11.7135% | -27.2542% | 10.8292% | 0.149190 | +0.0000 pp |
| extra_lag | book_recovery_allshort24 | +3.6496% | +0.2712% | -11.2471% | -27.2542% | 10.5199% | 0.140156 | +0.0143 pp |
| extra_lag | book_recovery_rebound | +3.5227% | -0.0867% | -11.6423% | -27.2542% | 10.7508% | 0.141765 | -0.1126 pp |
| combined | book_e20combo_brk_cash | +2.9114% | -0.4026% | -12.5406% | -27.6397% | 11.0387% | 0.125906 | +0.0000 pp |
| combined | book_recovery_allshort24 | +2.9154% | -0.4182% | -11.9218% | -27.6397% | 10.7385% | 0.114884 | +0.0040 pp |
| combined | book_recovery_rebound | +2.8040% | -0.7537% | -12.3978% | -27.6397% | 10.9620% | 0.118187 | -0.1074 pp |

## 2024-onward 14-day outcomes

| Scenario | Model | Mean | Median | Bad10 | Mean drawdown | Mean CS | Mean delta |
|---|---|---:|---:|---:|---:|---:|---:|
| base | book_e20combo_brk_cash | +2.3785% | -0.5727% | -13.1801% | 11.2913% | 0.095878 | +0.0000 pp |
| base | book_recovery_allshort24 | +2.5842% | -0.2380% | -12.3042% | 10.8899% | 0.092952 | +0.2056 pp |
| base | book_recovery_rebound | +2.2587% | -0.7999% | -12.9162% | 11.0969% | 0.085145 | -0.1198 pp |
| double_cost | book_e20combo_brk_cash | +1.6197% | -1.4185% | -14.0292% | 11.5357% | 0.072935 | +0.0000 pp |
| double_cost | book_recovery_allshort24 | +1.8193% | -0.9943% | -12.9787% | 11.1357% | 0.068036 | +0.1996 pp |
| double_cost | book_recovery_rebound | +1.5166% | -1.5630% | -13.7531% | 11.3408% | 0.061959 | -0.1030 pp |
| extra_lag | book_e20combo_brk_cash | +2.2219% | -0.5420% | -13.8279% | 11.4191% | 0.088101 | +0.0000 pp |
| extra_lag | book_recovery_allshort24 | +2.4774% | -0.0700% | -12.8424% | 11.0003% | 0.087825 | +0.2555 pp |
| extra_lag | book_recovery_rebound | +2.0445% | -0.8331% | -13.1973% | 11.2545% | 0.074835 | -0.1774 pp |
| combined | book_e20combo_brk_cash | +1.4377% | -1.2099% | -14.5995% | 11.6643% | 0.064850 | +0.0000 pp |
| combined | book_recovery_allshort24 | +1.6864% | -0.8717% | -13.6722% | 11.2443% | 0.062493 | +0.2487 pp |
| combined | book_recovery_rebound | +1.2774% | -1.5708% | -14.0087% | 11.4998% | 0.051524 | -0.1603 pp |

## Shorter weak-market paths

All fixed archived and fresh-BTC-selected weak cases are retained, including unfavourable results.
Fresh in the case-set label means the later October query, not an untouched out-of-sample outcome.
This table shows the mean and Bad10 differences against the same-scenario baseline.
The complete CSV includes each absolute return, median, worst result, drawdown and CS.
No negative-bias subset was reselected to make a candidate win.

| Scenario | Candidate | Cases | Days | Mean delta | Bad10 delta |
|---|---|---|---:|---:|---:|
| base | book_recovery_allshort24 | weak_archived | 5 | -0.1593 pp | -0.0736 pp |
| base | book_recovery_allshort24 | weak_archived | 6 | -0.0739 pp | -0.3348 pp |
| base | book_recovery_allshort24 | weak_archived | 7 | +0.0172 pp | -0.8022 pp |
| base | book_recovery_allshort24 | weak_archived | 8 | +0.2422 pp | -0.8471 pp |
| base | book_recovery_allshort24 | weak_fresh_btc | 5 | +0.1084 pp | +0.3766 pp |
| base | book_recovery_allshort24 | weak_fresh_btc | 6 | +0.0640 pp | -0.1354 pp |
| base | book_recovery_allshort24 | weak_fresh_btc | 7 | +0.3008 pp | -0.8159 pp |
| base | book_recovery_allshort24 | weak_fresh_btc | 8 | +0.2791 pp | +0.1238 pp |
| base | book_recovery_rebound | weak_archived | 5 | -0.0505 pp | +0.0000 pp |
| base | book_recovery_rebound | weak_archived | 6 | -0.0493 pp | +0.0000 pp |
| base | book_recovery_rebound | weak_archived | 7 | -0.0074 pp | +0.0000 pp |
| base | book_recovery_rebound | weak_archived | 8 | +0.1374 pp | +0.0000 pp |
| base | book_recovery_rebound | weak_fresh_btc | 5 | -0.3591 pp | +0.0000 pp |
| base | book_recovery_rebound | weak_fresh_btc | 6 | -0.3021 pp | +0.0000 pp |
| base | book_recovery_rebound | weak_fresh_btc | 7 | -0.1754 pp | +0.0000 pp |
| base | book_recovery_rebound | weak_fresh_btc | 8 | -0.2283 pp | +0.0000 pp |
| double_cost | book_recovery_allshort24 | weak_archived | 5 | -0.1543 pp | -0.0763 pp |
| double_cost | book_recovery_allshort24 | weak_archived | 6 | -0.0696 pp | -0.3407 pp |
| double_cost | book_recovery_allshort24 | weak_archived | 7 | +0.0263 pp | -0.7020 pp |
| double_cost | book_recovery_allshort24 | weak_archived | 8 | +0.2459 pp | -0.7455 pp |
| double_cost | book_recovery_allshort24 | weak_fresh_btc | 5 | +0.1018 pp | +0.3917 pp |
| double_cost | book_recovery_allshort24 | weak_fresh_btc | 6 | +0.0566 pp | -0.0957 pp |
| double_cost | book_recovery_allshort24 | weak_fresh_btc | 7 | +0.2985 pp | -0.9212 pp |
| double_cost | book_recovery_allshort24 | weak_fresh_btc | 8 | +0.2695 pp | +0.1236 pp |
| double_cost | book_recovery_rebound | weak_archived | 5 | -0.0531 pp | +0.0000 pp |
| double_cost | book_recovery_rebound | weak_archived | 6 | -0.0519 pp | +0.0000 pp |
| double_cost | book_recovery_rebound | weak_archived | 7 | -0.0089 pp | +0.0000 pp |
| double_cost | book_recovery_rebound | weak_archived | 8 | +0.1404 pp | +0.0000 pp |
| double_cost | book_recovery_rebound | weak_fresh_btc | 5 | -0.3699 pp | +0.0000 pp |
| double_cost | book_recovery_rebound | weak_fresh_btc | 6 | -0.3125 pp | +0.0000 pp |
| double_cost | book_recovery_rebound | weak_fresh_btc | 7 | -0.1891 pp | -0.0081 pp |
| double_cost | book_recovery_rebound | weak_fresh_btc | 8 | -0.2367 pp | +0.0000 pp |
| extra_lag | book_recovery_allshort24 | weak_archived | 5 | -0.0974 pp | -0.2217 pp |
| extra_lag | book_recovery_allshort24 | weak_archived | 6 | -0.0337 pp | +0.4963 pp |
| extra_lag | book_recovery_allshort24 | weak_archived | 7 | +0.0746 pp | -0.1379 pp |
| extra_lag | book_recovery_allshort24 | weak_archived | 8 | +0.2940 pp | -0.2448 pp |
| extra_lag | book_recovery_allshort24 | weak_fresh_btc | 5 | +0.0779 pp | -0.0249 pp |
| extra_lag | book_recovery_allshort24 | weak_fresh_btc | 6 | +0.0623 pp | -0.8106 pp |
| extra_lag | book_recovery_allshort24 | weak_fresh_btc | 7 | +0.3133 pp | -0.5102 pp |
| extra_lag | book_recovery_allshort24 | weak_fresh_btc | 8 | +0.3753 pp | +0.3508 pp |
| extra_lag | book_recovery_rebound | weak_archived | 5 | -0.0419 pp | -0.3577 pp |
| extra_lag | book_recovery_rebound | weak_archived | 6 | -0.0410 pp | -0.3148 pp |
| extra_lag | book_recovery_rebound | weak_archived | 7 | -0.0078 pp | +0.0727 pp |
| extra_lag | book_recovery_rebound | weak_archived | 8 | +0.1328 pp | +0.2740 pp |
| extra_lag | book_recovery_rebound | weak_fresh_btc | 5 | -0.3190 pp | +0.0000 pp |
| extra_lag | book_recovery_rebound | weak_fresh_btc | 6 | -0.2896 pp | +0.0000 pp |
| extra_lag | book_recovery_rebound | weak_fresh_btc | 7 | -0.1922 pp | +0.0000 pp |
| extra_lag | book_recovery_rebound | weak_fresh_btc | 8 | -0.2351 pp | +0.0000 pp |
| combined | book_recovery_allshort24 | weak_archived | 5 | -0.0927 pp | -0.2177 pp |
| combined | book_recovery_allshort24 | weak_archived | 6 | -0.0296 pp | +0.5802 pp |
| combined | book_recovery_allshort24 | weak_archived | 7 | +0.0834 pp | -0.1433 pp |
| combined | book_recovery_allshort24 | weak_archived | 8 | +0.2974 pp | -0.3463 pp |
| combined | book_recovery_allshort24 | weak_fresh_btc | 5 | +0.0713 pp | +0.0446 pp |
| combined | book_recovery_allshort24 | weak_fresh_btc | 6 | +0.0548 pp | -0.8332 pp |
| combined | book_recovery_allshort24 | weak_fresh_btc | 7 | +0.3109 pp | -0.6406 pp |
| combined | book_recovery_allshort24 | weak_fresh_btc | 8 | +0.3647 pp | +0.3279 pp |
| combined | book_recovery_rebound | weak_archived | 5 | -0.0445 pp | -0.4212 pp |
| combined | book_recovery_rebound | weak_archived | 6 | -0.0435 pp | -0.2874 pp |
| combined | book_recovery_rebound | weak_archived | 7 | -0.0092 pp | +0.0054 pp |
| combined | book_recovery_rebound | weak_archived | 8 | +0.1358 pp | +0.3118 pp |
| combined | book_recovery_rebound | weak_fresh_btc | 5 | -0.3298 pp | +0.0000 pp |
| combined | book_recovery_rebound | weak_fresh_btc | 6 | -0.3000 pp | +0.0000 pp |
| combined | book_recovery_rebound | weak_fresh_btc | 7 | -0.2058 pp | +0.0000 pp |
| combined | book_recovery_rebound | weak_fresh_btc | 8 | -0.2436 pp | +0.0000 pp |

## Calendar stability

Year rows omit windows whose14-day outcome crosses into the next calendar year.
2020 and2026 are partial available years. These are descriptive historical slices, not new holdouts.
The14 fortnight offsets each contain non-overlapping windows internally. They overlap each other;
they are not 14 independent replications. Every offset is kept, never the best one.

| Candidate | Year | Windows | Mean return delta |
|---|---:|---:|---:|
| book_recovery_allshort24 | 2020 | 200 | +0.1613 pp |
| book_recovery_allshort24 | 2021 | 351 | -0.4050 pp |
| book_recovery_allshort24 | 2022 | 351 | -0.5186 pp |
| book_recovery_allshort24 | 2023 | 351 | -0.1312 pp |
| book_recovery_allshort24 | 2024 | 352 | +0.2037 pp |
| book_recovery_allshort24 | 2025 | 351 | +0.5442 pp |
| book_recovery_allshort24 | 2026 | 258 | -0.4528 pp |

book_recovery_allshort24: improves the mean in 0/14 full-history disjoint offsets.
Paired windows: improves 29.46%, trails 33.94%, ties 36.60%.
These are whole-window outcome comparisons, not executed-short accuracy or F1.
Recent-period leave-one-year-out mean deltas:
- Omit 2024: +0.1218 pp across 609 retained windows.
- Omit 2025: -0.0740 pp across 610 retained windows.
- Omit 2026: +0.3737 pp across 703 retained windows.

| book_recovery_rebound | 2020 | 200 | +0.0000 pp |
| book_recovery_rebound | 2021 | 351 | +0.0000 pp |
| book_recovery_rebound | 2022 | 351 | +0.0000 pp |
| book_recovery_rebound | 2023 | 351 | -0.3494 pp |
| book_recovery_rebound | 2024 | 352 | +0.2861 pp |
| book_recovery_rebound | 2025 | 351 | -0.3311 pp |
| book_recovery_rebound | 2026 | 258 | -0.5668 pp |

book_recovery_rebound: improves the mean in 0/14 full-history disjoint offsets.
Paired windows: improves 12.10%, trails 18.06%, ties 69.84%.
These are whole-window outcome comparisons, not executed-short accuracy or F1.
Recent-period leave-one-year-out mean deltas:
- Omit 2024: -0.4310 pp across 609 retained windows.
- Omit 2025: -0.0746 pp across 610 retained windows.
- Omit 2026: -0.0221 pp across 703 retained windows.

## Original failure veto and additional stressed gates

The original12-hypothesis paired lower bounds were negative; full mean/median gates failed.
allshort24 also failed the original 7/8-day downside checks; rebound failed recent and weak means.
These decisions remain unchanged. Extra bounds use a conservative .05/36 tail sensitivity for
12 tried hypotheses times 3 adverse scenarios; the displayed base bound is also conservatively widened.
They do not control all accumulated project research, every displayed metric, or all future risks.

| Scenario | Candidate | New stress gate pass |14-day paired lower | Original failure veto | Live eligible |
|---|---|---|---:|---|---|
| base | book_recovery_allshort24 | NO | -0.6391 pp | YES | NO |
| base | book_recovery_rebound | NO | -0.4776 pp | YES | NO |
| double_cost | book_recovery_allshort24 | NO | -0.6510 pp | YES | NO |
| double_cost | book_recovery_rebound | NO | -0.4880 pp | YES | NO |
| extra_lag | book_recovery_allshort24 | NO | -0.5482 pp | YES | NO |
| extra_lag | book_recovery_rebound | NO | -0.4542 pp | YES | NO |
| combined | book_recovery_allshort24 | NO | -0.5709 pp | YES | NO |
| combined | book_recovery_rebound | NO | -0.4682 pp | YES | NO |

## Verification and remaining limits

Regular suite: 249 passed. Separately discovered research tests: 40 passed. Total 289, including 4 new arithmetic tests.
Raw-cache reconstruction: 220,608 model/horizon/window rows;
return error 0.0, drawdown error 0.0, CS reconstruction error 0.0.
Trade-level fee/spread arithmetic and per-window cost sums checked. Saved shared target decisions
match their base model exactly. Initial cash-start target vectors are recomputed by unchanged pure code
and are not separately serialized. Original raw cache hashes, model sources, shared main and all
three frozen prospective worktrees remained unchanged during computation.
A prior independent uncached baseline replay also matched exactly; its evidence is retained in
/home/ubuntu/test/MiniMax/results/book/20261011-high-recovery-v1/fresh_baseline_audit.json.

A capped target can drift above 100% marked gross between rebalances in the inherited simulator.
That is a disclosed engine limitation, not evidence of actual EC2 leverage. Original hard-gate
eligibility remains UNVERIFIED. Historical spreads come from one fixed snapshot; terminal cost is
a configured proportional charge and does not separately add a terminal bid/ask spread.
Actual account fills, pending orders, endgame, funded-round return and model memory were not replayed.
The live runner resets prior model targets on a model-name change, so an actual transition can differ
materially from these cash-start results. Actual EC2 deployment and holdings remain UNVERIFIED.
The deadline differs between main rules and committed runner; the shorter cuts do not resolve it.

Original broad coverage failure BCH 29/30 remains. Adaptive scoring OFF. No production promotion.
Fresh common all 13-model cohort remains frozen for Oct 12 08HKT to Oct 15 08HKT and is incomplete.
It has no automatic job in this audit. Even that one 3-day future path cannot certify future returns.

## Files and reproduction

Raw metrics, all outcomes and manifests: /home/ubuntu/test/MiniMax/results/book/20261011-recovery-stress-v1
comparison.{base,double_cost,extra_lag,combined}.csv: all 384 model/scenario/context/horizon summaries.
calendar_stability.json: every year, leave-one-year-out slice and fortnight offset.
execution_costs.csv: fee, spread, turnover and exposure diagnostics.
decision.*.json: each unchanged gate and permanent original-failure veto.
independent_audit.json: raw cache identities, hashes and maximum errors.
METHOD_NOTES.md: inspected runner lines, cost limitations and primary research sources.
The public recovery leaderboard receives an audit note; its 133-model ranks and CSV stay unchanged.

Run remotely from Book's stress worktree using the environment and lock described in PROTOCOL.md.
python -B -m research.book.recovery_stress.run reproduces the fixed four-scenario audit.
python -B -m research.book.recovery_stress.audit reconstructs the raw evidence.
python -B -m research.book.recovery_stress.report rebuilds this guide.
pytest -q covers regular tests; also explicitly test research/book/recovery_study,
research/book/recovery_selection, research/book/residual_recovery, research/book/high_recovery
and research/book/rebound_recovery to include the 40 research tests.

## Research support

Retaining failed trials and refusing to call reused history fresh follow the selection-bias concern in
[Novy-Marx 2015, Backtesting Strategies Based on Multiple Signals](https://www.nber.org/papers/w21329).
Cost stresses are consistent with the implementation concern in
[Novy-Marx and Velikov, A Taxonomy of Anomalies and their Trading Costs](https://www.nber.org/papers/w20721).
These primary studies motivate checks; neither validates these crypto models or their score.
