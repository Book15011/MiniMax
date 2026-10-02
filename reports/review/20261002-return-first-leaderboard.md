# Scoring leaderboard (tool version `3036a0d8bfdaa6a0`, scoring v2)

Primary: **HEADLINE_RET**, the mean over three return bars (LENIENT, MIDDLE, STRICT) of the share of live-like, direction-balanced windows whose 14-day R_liq clears the bar. Windows start at 12:00 UTC like the round. Candidates are in the pre-registered pick order (hard gates, HEADLINE_RET, CS_HIT inside the top model's tie group, then min(SCREEN, CONFIRM)); benchmarks are reference rows. Definitions: docs/EVALUATION.md; pre-registration: reports/review/20261002-prereg-return-first.md. Latest full run of each model, regenerated after every registered run. pi_up (full / without the post-holdout windows): 0.543 / 0.539.

## Candidates (full pool)

| # | Model | HEADLINE_RET | without post-holdout | HIT L / M / S | HIT UP / DOWN | Tie group (90% interval vs top) | CS_HIT (V1 HKT) | V1 UTC days | old REL (rank) | Hard gates | Report-only gates failed | Worst R | Median MDD | Guard-only days | Turnover · fees / window | Replay R1 HK/SG · Final |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | baitoey_vt_mom | **0.609** | 0.556 | 0.65 / 0.62 / 0.55 | 0.80 / 0.38 | **yes** [+0.000, +0.000] | 0.368 | 0.330 | 2.10 (#8) | pass | none | -30.8% | 10.1% | 48% | 3.59 · 0.36% | -3.0% #31/#30 · +9.6% #2 |
| 2 | pol_switch_vt_tl | **0.548** | 0.456 | 0.60 / 0.56 / 0.48 | 0.63 / 0.44 | **yes** [-0.136, +0.005] | 0.366 | 0.318 | 2.29 (#5) | pass | none | -27.0% | 8.6% | 37% | 4.72 · 0.47% | +0.1% #10/#7 · -1.3% #12 |
| 3 | baitoey_rot_max | **0.546** | 0.509 | 0.58 / 0.56 / 0.49 | 0.69 / 0.37 | **yes** [-0.125, +0.001] | 0.296 | 0.276 | 2.06 (#9) | pass | G2, G3, G6_median, G6_worst | -48.4% | 14.5% | 69% | 3.46 · 0.35% | +2.0% #4/#5 · +18.6% #2 |
| 4 | baitoey_mr_bbrsi | **0.499** | 0.467 | 0.75 / 0.54 / 0.21 | 0.53 / 0.46 | **yes** [-0.199, +0.009] | 0.150 | 0.144 | 1.37 (#17) | pass | G6_median | -25.3% | 1.0% | 14% | 0.77 · 0.08% | +0.7% #6/#6 · +0.4% #8 |
| 5 | pol_switch_rot_mr | **0.514** | 0.461 | 0.57 / 0.54 / 0.43 | 0.69 / 0.30 | no [-0.160, -0.021] | 0.342 | 0.340 | 1.62 (#13) | pass | none | -32.7% | 9.2% | 30% | 5.14 · 0.51% | -3.5% #34/#31 · +4.8% #5 |
| 6 | pol_switch_rmax_tl | **0.491** | 0.421 | 0.54 / 0.51 / 0.43 | 0.55 / 0.42 | no [-0.236, -0.012] | 0.312 | 0.289 | 2.31 (#4) | pass | none | -30.4% | 11.0% | 48% | 4.62 · 0.46% | +0.6% #6/#6 · -2.8% #13 |
| 7 | pol_combo_rb | **0.481** | 0.457 | 0.57 / 0.52 / 0.35 | 0.73 / 0.19 | no [-0.216, -0.039] | 0.297 | 0.291 | — | pass | none | -30.0% | 9.3% | 12% | 3.57 · 0.36% | -3.7% #34/#32 · +13.5% #2 |
| 8 | pol_switch_rmax_mr | **0.475** | 0.449 | 0.53 / 0.50 / 0.39 | 0.64 / 0.28 | no [-0.226, -0.036] | 0.395 | 0.373 | 2.13 (#7) | pass | G6_median | -36.1% | 12.1% | 37% | 5.73 · 0.57% | -3.2% #31/#31 · +6.5% #3 |
| 9 | pol_switch_rt | **0.472** | 0.408 | 0.53 / 0.50 / 0.39 | 0.54 / 0.39 | no [-0.271, -0.015] | 0.299 | 0.282 | 1.78 (#11) | pass | none | -26.0% | 8.9% | 16% | 6.15 · 0.62% | +0.1% #10/#7 · +1.4% #6 |
| 10 | baitoey_mr_4h | **0.472** | 0.475 | 0.59 / 0.54 / 0.29 | 0.60 / 0.32 | no [-0.245, -0.025] | 0.461 | 0.544 | 3.03 (#3) | pass | G6_median | -28.6% | 5.3% | 12% | 3.49 · 0.35% | -2.5% #28/#27 · +1.6% #6 |
| 11 | pol_combo_all | **0.458** | 0.421 | 0.59 / 0.53 / 0.25 | 0.65 / 0.23 | no [-0.248, -0.053] | 0.284 | 0.297 | — | pass | none | -20.0% | 6.9% | 19% | 3.30 · 0.33% | -2.3% #24/#25 · +7.1% #3 |
| 12 | pol_mom_ss | **0.458** | 0.430 | 0.57 / 0.52 / 0.28 | 0.47 / 0.45 | no [-0.284, -0.010] | 0.321 | 0.306 | 1.08 (#20) | pass | none | -16.3% | 4.8% | 15% | 5.28 · 0.53% | +0.8% #4/#6 · +3.2% #6 |
| 13 | pol_combo_rt | **0.456** | 0.397 | 0.55 / 0.50 / 0.32 | 0.57 / 0.33 | no [-0.247, -0.057] | 0.286 | 0.287 | — | pass | none | -16.1% | 6.4% | 4% | 5.58 · 0.56% | -0.8% #18/#14 · +5.0% #5 |
| 14 | pol_switch_rc | **0.443** | 0.373 | 0.58 / 0.45 / 0.31 | 0.53 / 0.33 | no [-0.270, -0.070] | 0.247 | 0.233 | — | pass | none | -21.8% | 7.7% | 6% | 3.68 · 0.37% | -0.0% #13/#10 · +5.2% #4 |
| 15 | pol_switch3 | **0.438** | 0.380 | 0.52 / 0.48 / 0.31 | 0.53 / 0.33 | no [-0.257, -0.057] | 0.841 | 0.535 | 1.35 (#18) | pass | G6_median | -31.2% | 7.2% | 19% | 6.44 · 0.63% | +1.6% #4/#5 · -2.5% #13 |
| 16 | pol_combo_rtt | **0.434** | 0.372 | 0.55 / 0.49 / 0.26 | 0.57 / 0.27 | no [-0.262, -0.089] | 0.295 | 0.299 | — | pass | none | -18.8% | 5.8% | 7% | 4.00 · 0.40% | -1.5% #21/#20 · +5.1% #4 |
| 17 | pol_trend_ls | **0.418** | 0.395 | 0.51 / 0.46 / 0.29 | 0.37 / 0.48 | no [-0.307, -0.057] | 0.288 | 0.282 | 2.18 (#6) | pass | none | -18.7% | 6.5% | 20% | 5.83 · 0.58% | -0.0% #13/#10 · -5.4% #14 |
| 18 | pol_combo_ms_tl | **0.415** | 0.393 | 0.52 / 0.47 / 0.25 | 0.38 / 0.45 | no [-0.328, -0.034] | 0.295 | 0.296 | — | pass | none | -12.4% | 5.0% | 6% | 5.41 · 0.54% | +0.4% #8/#6 · -0.3% #9 |
| 19 | baitoey_tg_mom | **0.374** | 0.351 | 0.55 / 0.43 / 0.14 | 0.36 / 0.40 | no [-0.364, -0.086] | 0.269 | 0.257 | 0.91 (#22) | pass | none | -9.7% | 3.4% | 7% | 3.83 · 0.38% | -0.5% #17/#12 · -1.2% #12 |

## Reference rows (benchmarks, CASH included)

| | Model | HEADLINE_RET | without post-holdout | HIT L / M / S | HIT UP / DOWN | Tie group (90% interval vs top) | CS_HIT (V1 HKT) | V1 UTC days | old REL (rank) | Hard gates | Report-only gates failed | Worst R | Median MDD | Guard-only days | Turnover · fees / window | Replay R1 HK/SG · Final |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|  | ROT_EW | **0.547** | 0.507 | 0.59 / 0.56 / 0.49 | 0.71 / 0.36 | **yes** [-0.133, +0.008] | 0.306 | 0.294 | 1.67 (#12) | pass | none | -33.5% | 10.4% | 56% | 2.94 · 0.30% | +0.4% #7/#6 · +13.5% #2 |
|  | ROT_IV | **0.511** | 0.456 | 0.60 / 0.55 / 0.38 | 0.65 / 0.35 | no [-0.193, -0.015] | 0.334 | 0.332 | 0.06 (#24) | pass | none | -24.0% | 7.0% | 55% | 2.35 · 0.24% | -0.4% #17/#11 · +9.4% #2 |
|  | BTC_HOLD | **0.478** | 0.491 | 0.62 / 0.53 / 0.29 | 0.81 / 0.08 | no [-0.204, -0.038] | 0.317 | 0.304 | 1.55 (#14) | pass | G2, G3 | -37.3% | 8.6% | 7% | 1.05 · 0.11% | -5.8% #40/#39 · +10.7% #2 |
|  | EW_DAILY | **0.468** | 0.444 | 0.53 / 0.49 / 0.39 | 0.73 / 0.15 | no [-0.222, -0.041] | 0.321 | 0.330 | 1.42 (#16) | pass | G2, G3, G6_median, G6_worst | -47.3% | 13.8% | 0% | 1.66 · 0.17% | -5.8% #40/#39 · +5.8% #3 |
|  | MOM_SS25 | **0.458** | 0.430 | 0.57 / 0.52 / 0.28 | 0.47 / 0.45 | no [-0.284, -0.010] | 0.321 | 0.306 | 1.08 (#19) | pass | none | -16.3% | 4.8% | 15% | 5.28 · 0.53% | +0.8% #4/#6 · +3.2% #6 |
|  | TREND_2 | **0.449** | 0.423 | 0.62 / 0.51 / 0.22 | 0.69 / 0.17 | no [-0.234, -0.076] | 0.312 | 0.308 | 0.22 (#23) | pass | G6_median | -16.9% | 5.2% | 87% | 1.04 · 0.10% | -2.2% #24/#25 · +5.5% #4 |
|  | CASH | **0.372** | 0.326 | 0.75 / 0.31 / 0.05 | 0.38 / 0.36 | no [-0.303, -0.150] | -0.002 | -0.002 | 0.00 (#25) | pass | G6_median | -0.1% | 0.0% | 0% | 0.06 · 0.01% | -0.0% #12/#10 · +0.0% #9 |

**Pick (full pool): `baitoey_vt_mom`.** Tie group: `baitoey_vt_mom`, `pol_switch_vt_tl`, `baitoey_rot_max`, `baitoey_mr_bbrsi`.

## Without the post-holdout windows (in-sample pool, its own weights, pi_up and tie group)

| # | Model | HEADLINE_RET | HIT L / M / S | HIT UP / DOWN | Tie group (90% interval vs top) | CS_HIT | Full-pool rank |
|---|---|---|---|---|---|---|---|
| 1 | baitoey_mr_4h | 0.475 | 0.57 / 0.53 / 0.33 | 0.61 / 0.32 | **yes** [-0.194, +0.027] | 0.391 | 10 |
| 2 | pol_switch_rmax_tl | 0.421 | 0.47 / 0.44 / 0.36 | 0.45 / 0.39 | **yes** [-0.278, +0.001] | 0.278 | 6 |
| 3 | baitoey_vt_mom | 0.556 | 0.60 / 0.57 / 0.50 | 0.75 / 0.32 | **yes** [+0.000, +0.000] | 0.316 | 1 |
| 4 | pol_switch_vt_tl | 0.456 | 0.51 / 0.47 / 0.38 | 0.49 / 0.41 | **yes** [-0.213, +0.007] | 0.307 | 2 |
| 5 | baitoey_rot_max | 0.509 | 0.55 / 0.52 / 0.46 | 0.66 / 0.34 | **yes** [-0.106, +0.012] | 0.257 | 3 |
| 6 | pol_mom_ss | 0.430 | 0.55 / 0.49 / 0.25 | 0.45 / 0.41 | **yes** [-0.280, +0.012] | 0.274 | 12 |
| 7 | baitoey_mr_bbrsi | 0.467 | 0.70 / 0.48 / 0.23 | 0.50 / 0.43 | **yes** [-0.198, +0.035] | 0.139 | 4 |
| 8 | pol_switch_rot_mr | 0.461 | 0.53 / 0.48 / 0.37 | 0.65 / 0.24 | no [-0.173, -0.009] | 0.325 | 5 |
| 9 | pol_combo_rb | 0.457 | 0.53 / 0.48 / 0.36 | 0.73 / 0.14 | no [-0.186, -0.013] | 0.267 | 7 |
| 10 | pol_switch_rmax_mr | 0.449 | 0.51 / 0.47 / 0.37 | 0.65 / 0.21 | no [-0.193, -0.014] | 0.353 | 8 |
| 11 | pol_combo_all | 0.421 | 0.55 / 0.48 / 0.23 | 0.62 / 0.18 | no [-0.238, -0.036] | 0.248 | 11 |
| 12 | pol_switch_rt | 0.408 | 0.46 / 0.43 / 0.34 | 0.45 / 0.36 | no [-0.309, -0.000] | 0.291 | 9 |
| 13 | pol_combo_rt | 0.397 | 0.49 / 0.44 / 0.26 | 0.50 / 0.28 | no [-0.261, -0.058] | 0.279 | 13 |
| 14 | pol_trend_ls | 0.395 | 0.47 / 0.43 / 0.28 | 0.34 / 0.46 | no [-0.297, -0.022] | 0.268 | 17 |
| 15 | pol_combo_ms_tl | 0.393 | 0.50 / 0.44 / 0.23 | 0.38 / 0.41 | no [-0.314, -0.009] | 0.254 | 18 |
| 16 | pol_switch3 | 0.380 | 0.46 / 0.42 / 0.26 | 0.43 / 0.32 | no [-0.300, -0.030] | 0.347 | 15 |
| 17 | pol_switch_rc | 0.373 | 0.53 / 0.36 / 0.23 | 0.45 / 0.28 | no [-0.292, -0.081] | 0.218 | 14 |
| 18 | pol_combo_rtt | 0.372 | 0.49 / 0.43 / 0.20 | 0.49 / 0.23 | no [-0.279, -0.085] | 0.274 | 16 |
| 19 | baitoey_tg_mom | 0.351 | 0.51 / 0.38 / 0.17 | 0.30 / 0.41 | no [-0.365, -0.053] | 0.261 | 19 |
| | ROT_EW | 0.507 | 0.55 / 0.52 / 0.45 | 0.67 / 0.31 | — | 0.264 | — |
| | ROT_IV | 0.456 | 0.56 / 0.50 / 0.30 | 0.59 / 0.30 | — | 0.259 | — |
| | BTC_HOLD | 0.491 | 0.60 / 0.52 / 0.35 | 0.85 / 0.07 | — | 0.267 | — |
| | EW_DAILY | 0.444 | 0.50 / 0.46 / 0.37 | 0.71 / 0.14 | — | 0.278 | — |
| | MOM_SS25 | 0.430 | 0.55 / 0.49 / 0.25 | 0.45 / 0.41 | — | 0.274 | — |
| | TREND_2 | 0.423 | 0.57 / 0.47 / 0.23 | 0.67 / 0.13 | — | 0.246 | — |
| | CASH | 0.326 | 0.68 / 0.24 / 0.06 | 0.30 / 0.36 | — | -0.004 | — |

**Pick without the post-holdout windows: `baitoey_mr_4h`.**

Columns: HIT L / M / S = the share of weight clearing LENIENT (−1.4965% in DOWN windows, 0% in UP windows, an assumption), MIDDLE (0%) and STRICT (max(0, the 6 gate benchmarks' median)); HIT UP / DOWN = the mean of the three HITs on UP and on DOWN windows, each group's weights renormalized. CS_HIT = mean composite (V1 FLOORED) over the windows clearing LENIENT, on HKT days and on UTC days. Old REL = the primary of tool version `56cb5a2e85d45862` (report only). Hard gates: G1 (≥ 10 active HKT days in every window), G4 (long-only run completes), G5 (leakage). Report-only gates: G2, G3, G6_median, G6_worst. Replay: the previous edition's two real windows from cash, R and rank among its teams (numbers only).

## Return view (report-only): ranked by the size of the 14-day return

The main ranking above is by HEADLINE_RET: how often the return clears the cut. This view ranks the same runs by how large the return is: the mean 14-day R_liq weighted with the same final weights w' (live-like, recency, direction-balanced). It is shown so both can be read side by side; it does not change the pick or the order above.

| Return rank | Model | Mean R_liq (w') | without post-holdout (rank) | Median R_liq (w') | 10th pct | 90th pct | Share > 0 | Plain median | Worst | Best | Main rank (HEADLINE_RET) | Eligible |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | baitoey_vt_mom | **+4.86%** | +2.54% (#1) | +2.60% | -9.1% | +23.6% | 62% | +1.17% | -30.9% | +71.3% | #1 | yes |
| 2 | pol_switch_vt_tl | **+3.88%** | +1.04% (#3) | +1.20% | -8.1% | +21.6% | 56% | +0.17% | -27.0% | +66.5% | #2 | yes |
| 3 | baitoey_rot_max | **+3.85%** | +1.66% (#2) | +1.68% | -13.7% | +23.9% | 56% | +0.68% | -48.4% | +287.9% | #3 | yes |
| 4 | pol_switch_rmax_mr | **+3.17%** | +0.58% (#4) | -0.07% | -13.3% | +25.4% | 50% | -0.17% | -36.1% | +152.0% | #8 | yes |
| 5 | pol_switch_rmax_tl | **+3.09%** | +0.49% (#6) | +0.45% | -11.9% | +22.4% | 51% | -0.41% | -30.5% | +281.6% | #6 | yes |
| 6 | pol_switch_rot_mr | **+2.44%** | +0.29% (#10) | +0.59% | -10.7% | +17.6% | 54% | +0.05% | -32.7% | +61.3% | #5 | yes |
| 7 | pol_switch_rc | **+1.90%** | +0.38% (#9) | -0.01% | -9.6% | +16.5% | 45% | -0.01% | -21.8% | +57.6% | #14 | yes |
| 8 | pol_combo_rb | **+1.82%** | +0.54% (#5) | +0.59% | -8.6% | +14.7% | 52% | +0.65% | -30.1% | +55.3% | #7 | yes |
| 9 | pol_switch_rt | **+1.76%** | +0.15% (#13) | +0.06% | -10.4% | +16.7% | 50% | -0.24% | -26.0% | +57.6% | #9 | yes |
| 10 | pol_combo_all | **+1.61%** | +0.39% (#8) | +0.28% | -6.3% | +12.6% | 53% | +0.15% | -20.0% | +38.8% | #11 | yes |
| 11 | pol_combo_rtt | **+1.42%** | +0.26% (#11) | -0.10% | -5.6% | +11.4% | 49% | -0.16% | -18.8% | +40.7% | #16 | yes |
| 12 | pol_combo_rt | **+1.36%** | +0.39% (#7) | -0.03% | -7.1% | +12.0% | 50% | -0.24% | -16.1% | +40.1% | #13 | yes |
| 13 | pol_mom_ss | **+0.76%** | +0.25% (#12) | +0.24% | -6.3% | +9.1% | 52% | +0.09% | -16.3% | +25.3% | #12 | yes |
| 14 | pol_switch3 | **+0.60%** | -1.30% (#19) | -0.17% | -7.8% | +9.3% | 48% | -0.17% | -31.2% | +61.4% | #15 | yes |
| 15 | pol_combo_ms_tl | **+0.49%** | +0.03% (#14) | -0.22% | -4.8% | +8.4% | 47% | -0.07% | -12.5% | +25.2% | #18 | yes |
| 16 | pol_trend_ls | **+0.29%** | -0.30% (#16) | -0.47% | -6.4% | +9.1% | 46% | -0.05% | -18.7% | +33.0% | #17 | yes |
| 17 | baitoey_tg_mom | **+0.22%** | -0.11% (#15) | -0.44% | -3.5% | +5.5% | 43% | -0.02% | -9.7% | +25.3% | #19 | yes |
| 18 | baitoey_mr_4h | **+0.08%** | -0.43% (#18) | +0.63% | -6.6% | +6.2% | 54% | +0.63% | -28.7% | +21.0% | #10 | yes |
| 19 | baitoey_mr_bbrsi | **-0.17%** | -0.42% (#17) | +0.00% | -1.9% | +2.2% | 54% | +0.00% | -25.3% | +22.1% | #4 | yes |
| ref | ROT_EW | **+3.14%** | +1.27% | +1.31% | -10.6% | +20.3% | 56% | +0.66% | -33.6% | +76.8% | ref | yes |
| ref | ROT_IV | **+2.54%** | +0.85% | +0.96% | -6.4% | +13.0% | 55% | +0.61% | -24.0% | +41.3% | ref | yes |
| ref | EW_DAILY | **+2.15%** | +0.27% | -0.49% | -12.7% | +23.9% | 49% | -0.15% | -47.3% | +133.7% | ref | yes |
| ref | TREND_2 | **+1.60%** | +0.15% | +0.04% | -6.3% | +10.0% | 51% | -0.13% | -16.9% | +45.6% | ref | yes |
| ref | BTC_HOLD | **+1.39%** | +0.28% | +0.26% | -7.2% | +10.8% | 53% | +0.60% | -37.4% | +69.2% | ref | yes |
| ref | MOM_SS25 | **+0.76%** | +0.25% | +0.24% | -6.3% | +9.1% | 52% | +0.09% | -16.3% | +25.3% | ref | yes |
| ref | CASH | **-0.00%** | -0.01% | -0.01% | -0.0% | +0.0% | 31% | -0.01% | -0.1% | +0.1% | ref | yes |

## Runs per person (this tool version)

| Person | Full runs | Best eligible candidate HEADLINE_RET |
|---|---|---|
| baitoey | 5 | 0.609 (baitoey_vt_mom) |
| pol | 14 | 0.548 (pol_switch_vt_tl) |
| team | 7 | — |

## Previous tool versions (not comparable with the rows above)

| Tool version | Scoring version | Latest run | Model | Primary of that version | Eligible then |
|---|---|---|---|---|---|
| `f7887e401efa92a0` (previous version) | v1 | 2026-10-01T15:02 | pol_switch_vt_tl | +2.288 | yes |
| `f7887e401efa92a0` (previous version) | v1 | 2026-10-01T15:00 | pol_switch3 | +1.346 | no |
| `56cb5a2e85d45862` (previous version) | v1 | 2026-10-01T16:27 | pol_mr_cap | +4.139 | yes |
| `56cb5a2e85d45862` (previous version) | v1 | 2026-10-01T17:32 | pol_switch_vt_tl_e20v45 | +3.072 | yes |
| `56cb5a2e85d45862` (previous version) | v1 | 2026-10-01T13:38 | baitoey_mr_4h | +3.026 | no |
| `56cb5a2e85d45862` (previous version) | v1 | 2026-10-01T13:48 | pol_switch_rmax_tl | +2.306 | yes |
| `56cb5a2e85d45862` (previous version) | v1 | 2026-10-01T15:12 | pol_switch_vt_tl | +2.289 | yes |
| `56cb5a2e85d45862` (previous version) | v1 | 2026-10-01T13:55 | pol_trend_ls | +2.181 | yes |
| `56cb5a2e85d45862` (previous version) | v1 | 2026-10-01T13:47 | pol_switch_rmax_mr | +2.128 | yes |
| `56cb5a2e85d45862` (previous version) | v1 | 2026-10-01T13:42 | baitoey_vt_mom | +2.101 | yes |
| `56cb5a2e85d45862` (previous version) | v1 | 2026-10-01T13:39 | baitoey_rot_max | +2.061 | no |
| `56cb5a2e85d45862` (previous version) | v1 | 2026-10-01T16:29 | pol_switch_vtm_tl | +2.020 | yes |
| `56cb5a2e85d45862` (previous version) | v1 | 2026-10-01T13:54 | pol_switch_rt | +1.784 | yes |
| `56cb5a2e85d45862` (previous version) | v1 | 2026-10-01T13:34 | team_rot_ew | +1.666 | yes |
| `56cb5a2e85d45862` (previous version) | v1 | 2026-10-01T13:51 | pol_switch_rot_mr | +1.624 | yes |
| `56cb5a2e85d45862` (previous version) | v1 | 2026-10-01T13:33 | team_btc_hold | +1.553 | no |
| `56cb5a2e85d45862` (previous version) | v1 | 2026-10-01T16:39 | pol_switch3_cap | +1.493 | no |
| `56cb5a2e85d45862` (previous version) | v1 | 2026-10-01T13:34 | team_ew_daily | +1.416 | no |
| `56cb5a2e85d45862` (previous version) | v1 | 2026-10-01T13:39 | baitoey_mr_bbrsi | +1.371 | yes |
| `56cb5a2e85d45862` (previous version) | v1 | 2026-10-01T15:21 | pol_switch3 | +1.346 | no |
| `56cb5a2e85d45862` (previous version) | v1 | 2026-10-01T13:35 | team_mom_ss25 | +1.082 | yes |
| `56cb5a2e85d45862` (previous version) | v1 | 2026-10-01T13:44 | pol_mom_ss | +1.082 | yes |
| `56cb5a2e85d45862` (previous version) | v1 | 2026-10-01T16:21 | pol_vt_mvr | +1.076 | yes |
| `56cb5a2e85d45862` (previous version) | v1 | 2026-10-01T13:41 | baitoey_tg_mom | +0.909 | yes |
| `56cb5a2e85d45862` (previous version) | v1 | 2026-10-01T13:34 | team_trend_2 | +0.223 | yes |
| `56cb5a2e85d45862` (previous version) | v1 | 2026-10-01T13:34 | team_rot_iv | +0.061 | yes |
| `56cb5a2e85d45862` (previous version) | v1 | 2026-10-01T13:33 | team_cash | +0.001 | yes |
| `b8c34f35cb5e30ba` (previous version) | v1 | 2026-10-01T10:05 | baitoey_mr_4h | +3.062 | yes |
| `b8c34f35cb5e30ba` (previous version) | v1 | 2026-10-01T10:07 | pol_switch_rmax_tl | +2.216 | yes |
| `b8c34f35cb5e30ba` (previous version) | v1 | 2026-10-01T10:08 | pol_trend_ls | +2.122 | yes |
| `b8c34f35cb5e30ba` (previous version) | v1 | 2026-10-01T10:09 | baitoey_vt_mom | +2.050 | yes |
| `b8c34f35cb5e30ba` (previous version) | v1 | 2026-10-01T10:14 | pol_switch_rmax_mr | +2.029 | yes |
| `b8c34f35cb5e30ba` (previous version) | v1 | 2026-10-01T10:20 | baitoey_rot_max | +1.985 | no |
| `b8c34f35cb5e30ba` (previous version) | v1 | 2026-10-01T10:17 | pol_switch_rt | +1.907 | yes |
| `b8c34f35cb5e30ba` (previous version) | v1 | 2026-10-01T10:26 | pol_switch_rot_mr | +1.632 | yes |
| `b8c34f35cb5e30ba` (previous version) | v1 | 2026-10-01T09:59 | team_rot_ew | +1.593 | yes |
| `b8c34f35cb5e30ba` (previous version) | v1 | 2026-10-01T09:58 | team_btc_hold | +1.537 | no |
| `b8c34f35cb5e30ba` (previous version) | v1 | 2026-10-01T09:59 | team_ew_daily | +1.394 | no |
| `b8c34f35cb5e30ba` (previous version) | v1 | 2026-10-01T10:27 | baitoey_mr_bbrsi | +1.356 | yes |
| `b8c34f35cb5e30ba` (previous version) | v1 | 2026-10-01T10:00 | team_mom_ss25 | +1.123 | yes |
| `b8c34f35cb5e30ba` (previous version) | v1 | 2026-10-01T10:18 | pol_mom_ss | +1.123 | yes |
| `b8c34f35cb5e30ba` (previous version) | v1 | 2026-10-01T10:19 | baitoey_tg_mom | +0.879 | yes |
| `b8c34f35cb5e30ba` (previous version) | v1 | 2026-10-01T09:59 | team_trend_2 | +0.237 | yes |
| `b8c34f35cb5e30ba` (previous version) | v1 | 2026-10-01T09:59 | team_rot_iv | +0.116 | yes |
| `b8c34f35cb5e30ba` (previous version) | v1 | 2026-10-01T09:58 | team_cash | +0.007 | yes |
| `ce40153bf480e315` (previous version) | v1 | 2026-10-01T04:44 | pol_switch_rt | +1.373 | yes |
| `ce40153bf480e315` (previous version) | v1 | 2026-10-01T04:11 | team_rot_ew | +1.324 | yes |
| `ce40153bf480e315` (previous version) | v1 | 2026-10-01T04:15 | pol_trend_ls | +1.314 | yes |
| `ce40153bf480e315` (previous version) | v1 | 2026-10-01T04:20 | pol_combo_rb | +1.152 | yes |
| `ce40153bf480e315` (previous version) | v1 | 2026-10-01T06:29 | team_btc_hold | +1.148 | no |
| `ce40153bf480e315` (previous version) | v1 | 2026-10-01T06:29 | team_ew_daily | +1.085 | no |
| `ce40153bf480e315` (previous version) | v1 | 2026-10-01T04:18 | pol_combo_rt | +0.995 | yes |
| `ce40153bf480e315` (previous version) | v1 | 2026-10-01T04:29 | pol_combo_ms_tl | +0.923 | yes |
| `ce40153bf480e315` (previous version) | v1 | 2026-10-01T04:12 | team_mom_ss25 | +0.897 | yes |
| `ce40153bf480e315` (previous version) | v1 | 2026-10-01T04:13 | pol_mom_ss | +0.897 | yes |
| `ce40153bf480e315` (previous version) | v1 | 2026-10-01T04:11 | team_rot_iv | +0.874 | yes |
| `ce40153bf480e315` (previous version) | v1 | 2026-10-01T04:45 | pol_switch_rc | +0.794 | yes |
| `ce40153bf480e315` (previous version) | v1 | 2026-10-01T04:11 | team_trend_2 | +0.671 | yes |
| `ce40153bf480e315` (previous version) | v1 | 2026-10-01T04:37 | pol_combo_all | +0.630 | yes |
| `ce40153bf480e315` (previous version) | v1 | 2026-10-01T07:00 | baitoey_tg_mom | +0.620 | yes |
| `ce40153bf480e315` (previous version) | v1 | 2026-10-01T04:25 | pol_combo_rtt | +0.597 | yes |
| `ce40153bf480e315` (previous version) | v1 | 2026-10-01T06:29 | team_cash | +0.007 | yes |
| `0e226336340813e9` (previous version) | v1 | 2026-10-01T03:56 | team_rot_ew | +1.324 | yes |
| `0e226336340813e9` (previous version) | v1 | 2026-10-01T04:00 | pol_trend_ls | +1.314 | no |
| `0e226336340813e9` (previous version) | v1 | 2026-10-01T03:56 | team_btc_hold | +1.149 | no |
| `0e226336340813e9` (previous version) | v1 | 2026-10-01T03:56 | team_ew_daily | +1.085 | no |
| `0e226336340813e9` (previous version) | v1 | 2026-10-01T03:57 | team_mom_ss25 | +0.897 | no |
| `0e226336340813e9` (previous version) | v1 | 2026-10-01T03:59 | pol_mom_ss | +0.897 | no |
| `0e226336340813e9` (previous version) | v1 | 2026-10-01T03:56 | team_rot_iv | +0.874 | yes |
| `0e226336340813e9` (previous version) | v1 | 2026-10-01T03:57 | team_trend_2 | +0.671 | yes |
| `0e226336340813e9` (previous version) | v1 | 2026-10-01T03:55 | team_cash | +0.000 | no |
| `c0f83aa56ae994e9` (previous version) | v1 | 2026-10-01T02:23 | team_rot_ew | +0.090 | yes |
| `c0f83aa56ae994e9` (previous version) | v1 | 2026-10-01T02:22 | team_btc_hold | +0.076 | no |
| `c0f83aa56ae994e9` (previous version) | v1 | 2026-10-01T02:22 | team_ew_daily | +0.074 | no |
| `c0f83aa56ae994e9` (previous version) | v1 | 2026-10-01T02:24 | team_mom_ss25 | +0.064 | yes |
| `c0f83aa56ae994e9` (previous version) | v1 | 2026-10-01T02:23 | team_rot_iv | +0.059 | yes |
| `c0f83aa56ae994e9` (previous version) | v1 | 2026-10-01T02:23 | team_trend_2 | +0.046 | yes |
| `c0f83aa56ae994e9` (previous version) | v1 | 2026-10-01T02:22 | team_cash | +0.000 | no |
