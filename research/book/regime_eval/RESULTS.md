# Completed Book evaluation

The implementation and evidence review are complete for the frozen October 8 12:00 UTC checkpoint. **306 tests passed; adaptive scoring remains disabled.** The matcher did not establish direction nondegradation and the current query failed breadth coverage and archive confirmation. No production replacement ranking or validated fast-short score is available.

Research judgment at the frozen checkpoint: **DOWN for the broad competition altcoin universe, with limited confidence**. Average forecast-distribution skill improved mainly for volatility and drawdown; this does not validate the directional narrative or minute/second entries.

All 38 compatible registered models were compared. No replacement candidate has a positive pointwise or family-adjusted lower delta versus e20. The e20 paper replay lost 8.0646% in its first 96 hours, worse than 24/25 legacy cases. Actual competition account equity and execution remain UNVERIFIED.

Remote implementation: /home/ubuntu/test/MiniMax/.worktrees/book-book-regime-eval
Branch: feature/book-regime-eval; based on main 320984e
Raw artifacts: /home/ubuntu/test/MiniMax/results/book/20261008-regime-eval/
Evidence/protocol: RESEARCH.md; reproduction: README.md

Only research code, tests, a separate configuration block and review documents are committed. Large data, caches and logs remain outside Git. Main and the live bot were not changed.

## Generated comparison

Snapshot: 2026-10-08 12:00:00+00:00. Prefix: 96h; remaining: 240h.

**Weight mode: UNIFORM_BASELINE_FALLBACK. Adaptive pass: False.**

Artifact hashes, alignment and numerical integrity passed. Current market coverage and forecast usefulness are separate gates.

Chosen alpha on SCREEN: 0.5. Active alpha: 0.0.

Confirmation CRPS improvement CI: {"mean": 0.009633616181761565, "lower": 0.002176824111347887, "upper": 0.01682388107773103}.

Confirmation Brier degradation CI: {"mean": -0.002326433575864049, "lower": -0.01577703893059434, "upper": 0.010861603708594217}.

Statistical gates: {"query_coverage": true, "adaptive_selected": true, "confirm_crps_improvement": true, "direction_not_degraded": false, "prior_only": true}.

Current complete archive data: False.

Current feature coverage: False. Missing: breadth48, alt_minus_btc48.

Case-study matcher: LEGACY_CORE_DIAGNOSTIC. Legacy daily CORE may use older within-day asset closes; it does not remedy missing precise48h endpoints.

All 38 registered models are included. Another 56 unregistered research cache names are inventoried separately.

These are each model's own historical continuation, not switching from identical incumbent holdings. The original leaderboard is unchanged. Strategy models were developed on observed history; no pristine holdout claim.

## First 96 hours versus the e20 paper replay

| Model | Paper prefix | Legacy case prefix median | p10 | p90 | Paper percentile | Path band coverage |
|---|---:|---:|---:|---:|---:|---:|
| baitoey_vt_mom | -5.71% | -0.27% | -6.43% | 11.21% | 12.0% | 88.7% |
| book_orch | -5.71% | -0.27% | -6.43% | 10.29% | 12.0% | 87.6% |
| book_vt_top4 | -4.89% | 0.71% | -6.30% | 13.04% | 20.0% | 95.9% |
| pol_abl_shock | -5.71% | -0.27% | -6.43% | 11.21% | 12.0% | 88.7% |
| pol_switch_vt_tl | -5.71% | 0.16% | -6.43% | 7.50% | 12.0% | 88.7% |
| pol_switch_vt_tl_e20v45 | -8.06% | -0.31% | -7.07% | 9.95% | 4.0% | 62.9% |

Legacy CORE case statistics never affect baseline weights. Prefix statistics are descriptive, not independent prediction tests: matching uses market observations from the already observed prefix. Paper is not the actual competition account.

## All registered models: historical continuation diagnostics

| Model | Mean remainder | p10 | Delta vs e20 | Family-adjusted lower delta | Original hard eligibility |
|---|---:|---:|---:|---:|---:|
| baitoey_mr_4h | -0.29% | -6.88% | -2.91% | -5.45% | True |
| baitoey_mr_bbrsi | -0.07% | -2.62% | -2.69% | -5.39% | True |
| baitoey_rot_max | 2.55% | -15.62% | -0.07% | -2.04% | True |
| baitoey_tg_mom | 0.53% | -2.96% | -2.09% | -4.54% | True |
| baitoey_vt_dual | 2.19% | -8.08% | -0.44% | -1.79% | True |
| baitoey_vt_mom | 2.09% | -9.52% | -0.54% | -2.05% | True |
| book_coin_trend | 1.53% | -5.61% | -1.09% | -2.84% | True |
| book_orch | 2.13% | -9.46% | -0.49% | -1.98% | True |
| book_vt_breadth | 2.16% | -6.00% | -0.47% | -1.78% | True |
| book_vt_dual | 2.21% | -6.91% | -0.42% | -1.71% | True |
| book_vt_top4 | 1.86% | -9.67% | -0.76% | -2.44% | True |
| pol_abl_shock | 1.56% | -10.17% | -1.07% | -2.80% | True |
| pol_combo_all | 1.14% | -6.83% | -1.49% | -3.32% | True |
| pol_combo_ms_tl | 0.58% | -4.42% | -2.04% | -4.38% | True |
| pol_combo_rb | 1.40% | -9.38% | -1.22% | -2.82% | True |
| pol_combo_rt | 1.14% | -6.35% | -1.49% | -3.33% | True |
| pol_combo_rtt | 1.12% | -5.64% | -1.51% | -3.28% | True |
| pol_mom_ss | 0.35% | -5.04% | -2.28% | -4.53% | True |
| pol_mr_cap | -0.12% | -5.26% | -2.74% | -5.33% | True |
| pol_switch3 | -0.00% | -8.38% | -2.63% | -4.17% | True |
| pol_switch3_cap | 0.12% | -7.71% | -2.50% | -4.14% | True |
| pol_switch_rc | 1.62% | -8.06% | -1.01% | -2.47% | True |
| pol_switch_rmax_mr | 2.63% | -11.73% | 0.00% | -1.51% | True |
| pol_switch_rmax_tl | 2.65% | -11.84% | 0.02% | -1.31% | True |
| pol_switch_rot_mr | 1.37% | -9.22% | -1.25% | -2.73% | True |
| pol_switch_rt | 1.43% | -9.35% | -1.20% | -2.55% | True |
| pol_switch_vt_tl | 1.81% | -8.81% | -0.82% | -1.90% | True |
| pol_switch_vt_tl_e20v45 | 2.63% | -10.36% | 0.00% | 0.00% | True |
| pol_switch_vtm_tl | 1.79% | -7.31% | -0.84% | -1.99% | True |
| pol_trend_ls | 0.75% | -5.87% | -1.87% | -4.28% | True |
| pol_vt_mvr | 2.04% | -7.85% | -0.58% | -2.10% | True |
| team_btc_hold | 1.33% | -9.81% | -1.30% | -3.23% | True |
| team_cash | -0.00% | -0.02% | -2.63% | -5.41% | True |
| team_ew_daily | 1.64% | -14.34% | -0.98% | -3.07% | True |
| team_mom_ss25 | 0.35% | -5.04% | -2.28% | -4.53% | True |
| team_rot_ew | 1.64% | -10.23% | -0.98% | -2.52% | True |
| team_rot_iv | 1.16% | -7.12% | -1.47% | -3.29% | True |
| team_trend_2 | 1.07% | -5.91% | -1.55% | -3.25% | True |

Full data: all_registered_models.csv; selected historical cases: incumbent_case_windows.csv; chronological forecast audit: walkforward.csv.

## Separate short timing table

```json
{
  "status": "NOT_VALIDATED",
  "scoring_table": "separate from main continuation table",
  "executable_event_ledger": "UNAVAILABLE; no minute/second strategy edge claimed",
  "minimum_independent_episodes": 30,
  "account_shorts": "UNVERIFIED",
  "prior_research": {
    "variants": 72,
    "positive_all_three_periods": 0,
    "positive_april_august_2026": 0
  },
  "metrics": [
    "continuation precision",
    "rebound-first rate",
    "remaining favorable excursion",
    "causal cover delay",
    "net expectancy after entry and cover",
    "tail losses",
    "independent episodes"
  ],
  "reasons": [
    "Existing minute timestamps/exit-lag assumptions require repair",
    "Three days of second quotes insufficient",
    "No shared-incumbent transition execution",
    "HFT remains forbidden"
  ]
}
```

No executable short-event ledger is available, so timing scores are not fabricated. At least 30 episodes is only a minimum evidence guard, not proof of independence or profitability.

Reproduction: run the commands in the research README from Book's dedicated worktree. Hashes, frozen settings, and model provenance are stored in the accompanying JSON files.

## Coverage, sampling and audit details

Broad top-30 coverage is 29/30: BCHUSDT has no competition ticker row at the frozen checkpoint. Both breadth features stay null under the unchanged 98% coverage threshold. The archive is confirmed only through October 8 00:00 UTC; later hours are ticker-assisted. K sensitivity cannot be evaluated on this incomplete query, so the false stability flag is an unevaluated guard, not measured instability.

There are 21 SCREEN and 27 CONFIRM queries. Six early SCREEN dates remain skipped because the fixed rules could not supply 25 cases; the threshold was not reduced. The confirmation interval uses four-query circular blocks and 2,000 bootstrap draws at 90%. Average CRPS improvement is a rank-space aggregate; return CRPS alone slightly worsened (0.147263 to 0.147724), while volatility and drawdown improved.

Brier degradation has a slightly favorable point estimate but an interval spanning harm. Failure to establish nondegradation does not prove deterioration.

Five historical windows (starts April 11-15, 2021 at 12:00 UTC) fail BTC forward endpoint/hour coverage and are excluded uniformly. The remaining 2,293 daily starts overlap. Their algebraic effective count is not an independent sample count; uncertainty uses 76 calendar-month clusters, and dependence across months remains possible. Nominal family intervals use a Bonferroni level across 31 candidate labels and only 2,000 bootstrap draws, so extreme-tail estimates are approximate. These estimates do not correct the prior strategy-development search or provide calibrated ten-day probabilities.

The source and configured parameters for pol_switch_vt_tl_e20v45 reproduce saved cache key 0ec3cf0ca1185b36 with the pinned scoring tool and starts. This verifies compatibility of current model code with the saved trajectory; it does not authenticate the EC2 deployment or the paper CSV's historical execution identity. See incumbent_identity.json.

registered_snapshot.json pins all selected registry entries. Registered score SHA-256 checks, exact window/grid alignment and original terminal liquidation arithmetic passed for every model. cache_inputs.json pins the trajectory arrays, window files and metadata and rejects later input changes. input_manifest.json preserves raw-source and frozen-snapshot hashes.

## All 25 legacy CORE cases

Selection uses historical market features at the stated state time. The early prefix is the model's first 96 hours; the remainder is its own subsequent 240 hours, including terminal liquidation fee. Distances below belong to legacy CORE, not the failed new FAST/TREND/BREADTH/VOL query. These case outcomes are disclosed after selection and never alter uniform baseline weights.

| Window start UTC | State time UTC | Legacy distance | e20 first 96h | e20 remaining 240h |
|---|---|---:|---:|---:|
| 2020-06-17 12:00 | 2020-06-21 12:00 | 0.1742 | -2.20% | -0.96% |
| 2020-07-08 12:00 | 2020-07-12 12:00 | 0.2160 | 0.35% | 2.05% |
| 2020-08-25 12:00 | 2020-08-29 12:00 | 0.2031 | -0.31% | -7.56% |
| 2020-10-03 12:00 | 2020-10-07 12:00 | 0.2220 | 0.62% | -5.64% |
| 2023-01-09 12:00 | 2023-01-13 12:00 | 0.2049 | 9.95% | 25.31% |
| 2023-02-10 12:00 | 2023-02-14 12:00 | 0.1459 | -1.17% | 6.83% |
| 2023-02-25 12:00 | 2023-03-01 12:00 | 0.2066 | 1.57% | -4.92% |
| 2023-04-16 12:00 | 2023-04-20 12:00 | 0.1470 | -7.07% | -5.70% |
| 2023-05-29 12:00 | 2023-06-02 12:00 | 0.2101 | -0.55% | -1.48% |
| 2023-07-14 12:00 | 2023-07-18 12:00 | 0.2308 | -6.55% | -0.76% |
| 2023-07-29 12:00 | 2023-08-02 12:00 | 0.2283 | -1.55% | 1.87% |
| 2023-12-14 12:00 | 2023-12-18 12:00 | 0.2214 | -7.38% | 30.14% |
| 2024-01-15 12:00 | 2024-01-19 12:00 | 0.1877 | -1.24% | 4.08% |
| 2024-02-01 12:00 | 2024-02-05 12:00 | 0.2141 | 4.02% | 10.71% |
| 2024-05-13 12:00 | 2024-05-17 12:00 | 0.2023 | 4.73% | 5.80% |
| 2024-07-17 12:00 | 2024-07-21 12:00 | 0.1958 | -0.05% | -2.86% |
| 2024-09-28 12:00 | 2024-10-02 12:00 | 0.1813 | -6.90% | -0.50% |
| 2024-10-13 12:00 | 2024-10-17 12:00 | 0.2110 | -6.54% | -2.11% |
| 2025-07-29 12:00 | 2025-08-02 12:00 | 0.2013 | -12.93% | -4.12% |
| 2026-04-10 12:00 | 2026-04-14 12:00 | 0.2305 | 2.07% | -0.07% |
| 2026-05-06 12:00 | 2026-05-10 12:00 | 0.1909 | -2.24% | -11.89% |
| 2026-05-20 12:00 | 2026-05-24 12:00 | 0.1340 | 4.66% | 7.40% |
| 2026-08-16 12:00 | 2026-08-20 12:00 | 0.1863 | 13.83% | 13.74% |
| 2026-09-01 12:00 | 2026-09-05 12:00 | 0.1985 | 3.23% | -1.89% |
| 2026-09-15 12:00 | 2026-09-19 12:00 | 0.1548 | 25.89% | 8.28% |


Twenty percent means five of these 25 prefixes lie within two percentage points of the paper loss. The empirical percentile is one of 25, not a p-value. The pointwise path band is not a simultaneous confidence band. Market matching uses already observed prefix information, so the comparison is descriptive rather than an independent predictive test.

## Verification and remaining limits

The final full suite passed 306 tests in 193.32 seconds; the focused evaluator suite passed 68 tests in 0.80 seconds. The final comparison completed successfully in 7.975 seconds. Tests and source hashes are saved with verification.json and code_inputs.json.

Checked behavior includes continuation fees, gross exposure drift, CRPS and quantiles, causal clipping, feature allowlisting, mature prior pools, embargo, breadth coverage, peak-to-trough drawdown, bootstrap guards, failed activation and registry snapshot preservation. New code does not write the official registry, invoke a signed competition API or call the live execution path.

The executable short ledger is unavailable. Its separate table records missing evidence instead of a made-up performance score. Cash/short transition execution, seconds ordering, entry/cover latency, current account short support and whole-round activity remain unvalidated.

Team review is pending. A future production switch requires account-aware simulation from common holdings and verified execution state; historical own-state results cannot authorize that switch. A new universe or adaptive protocol requires a separately declared version and validation, preserving this failed checkpoint.
