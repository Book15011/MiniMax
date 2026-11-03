# Scoring leaderboard (tool version `3036a0d8bfdaa6a0`, scoring v2)

Primary: **HEADLINE_RET**, the mean over three return bars (LENIENT, MIDDLE, STRICT) of the share of live-like, direction-balanced windows whose 14-day R_liq clears the bar. Windows start at 12:00 UTC like the round. Candidates are in the pre-registered pick order (hard gates, HEADLINE_RET, CS_HIT inside the top model's tie group, then min(SCREEN, CONFIRM)); benchmarks are reference rows. Definitions: docs/EVALUATION.md; pre-registration: reports/review/20261002-prereg-return-first.md. Latest full run of each model, regenerated after every registered run. pi_up (full / without the post-holdout windows): 0.543 / 0.539.

Tie rule ordering this table: **margin 0.03 (Pol's proposal)**; the legacy (pre-registered) pick is shown under each pick (top-level `selection:` in config.yaml, backtest/scoring/selection.py).

## Candidates (full pool)

| # | Model | HEADLINE_RET | without post-holdout | HIT L / M / S | HIT UP / DOWN | Tie group (90% interval vs top) | CS_HIT (V1 HKT) | V1 UTC days | old REL (rank) | Hard gates | Report-only gates failed | Worst R | Median MDD | Guard-only days | Turnover · fees / window | Replay R1 HK/SG · Final |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | book_orch | **0.617** | 0.561 | 0.66 / 0.63 / 0.56 | 0.80 / 0.40 | **yes** [+0.000, +0.000] | 0.371 | 0.332 | — | pass | none | -30.0% | 9.8% | 45% | 3.46 · 0.35% | -2.3% #24/#26 · +7.6% #3 |
| 2 | pol_abl_shock | **0.607** | 0.555 | 0.65 / 0.62 / 0.54 | 0.79 / 0.39 | **yes** [-0.022, +0.004] | 0.360 | 0.327 | — | pass | none | -26.8% | 10.0% | 47% | 3.82 · 0.38% | -3.0% #31/#30 · +11.3% #2 |
| 3 | baitoey_vt_mom | **0.609** | 0.556 | 0.65 / 0.62 / 0.55 | 0.80 / 0.38 | no [-0.015, -0.001] | 0.368 | 0.330 | 2.10 (#8) | pass | none | -30.8% | 10.1% | 48% | 3.59 · 0.36% | -3.0% #31/#30 · +9.6% #2 |
| 4 | baitoey_vt_dual | **0.587** | 0.541 | 0.64 / 0.61 / 0.52 | 0.74 / 0.40 | no [-0.060, +0.001] | 0.351 | 0.320 | — | pass | none | -23.5% | 8.5% | 31% | 4.08 · 0.41% | -2.4% #24/#26 · +9.3% #2 |
| 5 | book_vt_top4 | **0.572** | 0.519 | 0.64 / 0.59 / 0.48 | 0.74 / 0.37 | no [-0.073, -0.018] | 0.363 | 0.317 | — | pass | none | -30.7% | 10.2% | 62% | 3.20 · 0.32% | +3.2% #2/#5 · +7.3% #3 |
| 6 | pol_switch_vt_tl_e20v45 | **0.568** | 0.501 | 0.62 / 0.59 / 0.50 | 0.70 / 0.41 | no [-0.088, -0.013] | 0.384 | 0.334 | 3.07 (#2) | pass | none | -26.1% | 9.8% | 36% | 5.31 · 0.53% | +3.4% #2/#5 · +0.2% #9 |
| 7 | pol_switch_vt_tl | **0.548** | 0.456 | 0.60 / 0.56 / 0.48 | 0.63 / 0.44 | no [-0.144, -0.004] | 0.366 | 0.318 | 2.29 (#5) | pass | none | -27.0% | 8.6% | 37% | 4.72 · 0.47% | +0.1% #10/#7 · -1.3% #12 |
| 8 | baitoey_rot_max | **0.546** | 0.509 | 0.58 / 0.56 / 0.49 | 0.69 / 0.37 | no [-0.132, -0.006] | 0.296 | 0.276 | 2.06 (#9) | pass | G2, G3, G6_median, G6_worst | -48.4% | 14.5% | 69% | 3.46 · 0.35% | +2.0% #4/#5 · +18.6% #2 |
| 9 | book_vt_dual | **0.532** | 0.474 | 0.60 / 0.56 / 0.44 | 0.68 / 0.35 | no [-0.122, -0.045] | 0.365 | 0.328 | — | pass | none | -19.9% | 7.8% | 31% | 3.32 · 0.34% | -0.4% #17/#11 · +9.2% #2 |
| 10 | pol_vt_mvr | **0.528** | 0.479 | 0.60 / 0.55 / 0.44 | 0.70 / 0.33 | no [-0.144, -0.039] | 0.382 | 0.349 | 1.08 (#21) | pass | none | -27.8% | 8.0% | 38% | 4.13 · 0.42% | -2.3% #24/#25 · +6.7% #3 |
| 11 | book_vt_breadth | **0.516** | 0.456 | 0.61 / 0.55 / 0.39 | 0.68 / 0.31 | no [-0.132, -0.067] | 0.329 | 0.302 | — | pass | none | -16.8% | 7.3% | 47% | 3.04 · 0.31% | -4.9% #39/#38 · +8.7% #2 |
| 12 | pol_switch_rot_mr | **0.514** | 0.461 | 0.57 / 0.54 / 0.43 | 0.69 / 0.30 | no [-0.168, -0.029] | 0.342 | 0.340 | 1.62 (#13) | pass | none | -32.7% | 9.2% | 30% | 5.14 · 0.51% | -3.5% #34/#31 · +4.8% #5 |
| 13 | pol_mr_cap | **0.509** | 0.497 | 0.67 / 0.57 / 0.29 | 0.54 / 0.47 | no [-0.201, -0.008] | 0.414 | 0.475 | 4.14 (#1) | pass | G6_median | -25.5% | 4.1% | 10% | 2.39 · 0.24% | -1.9% #21/#23 · -0.7% #10 |
| 14 | baitoey_mr_bbrsi | **0.499** | 0.467 | 0.75 / 0.54 / 0.21 | 0.53 / 0.46 | no [-0.208, +0.002] | 0.150 | 0.144 | 1.37 (#17) | pass | G6_median | -25.3% | 1.0% | 14% | 0.77 · 0.08% | +0.7% #6/#6 · +0.4% #8 |
| 15 | pol_switch_rmax_tl | **0.491** | 0.421 | 0.54 / 0.51 / 0.43 | 0.55 / 0.42 | no [-0.243, -0.019] | 0.312 | 0.289 | 2.31 (#4) | pass | none | -30.4% | 11.0% | 48% | 4.62 · 0.46% | +0.6% #6/#6 · -2.8% #13 |
| 16 | pol_switch_vtm_tl | **0.488** | 0.416 | 0.55 / 0.51 / 0.41 | 0.56 / 0.40 | no [-0.239, -0.034] | 0.393 | 0.352 | 2.02 (#10) | pass | none | -20.4% | 7.9% | 30% | 5.05 · 0.51% | +0.0% #10/#7 · -2.1% #13 |
| 17 | pol_combo_rb | **0.481** | 0.457 | 0.57 / 0.52 / 0.35 | 0.73 / 0.19 | no [-0.226, -0.045] | 0.297 | 0.291 | — | pass | none | -30.0% | 9.3% | 12% | 3.57 · 0.36% | -3.7% #34/#32 · +13.5% #2 |
| 18 | pol_switch_rmax_mr | **0.475** | 0.449 | 0.53 / 0.50 / 0.39 | 0.64 / 0.28 | no [-0.234, -0.044] | 0.395 | 0.373 | 2.13 (#7) | pass | G6_median | -36.1% | 12.1% | 37% | 5.73 · 0.57% | -3.2% #31/#31 · +6.5% #3 |
| 19 | pol_switch_rt | **0.472** | 0.408 | 0.53 / 0.50 / 0.39 | 0.54 / 0.39 | no [-0.279, -0.021] | 0.299 | 0.282 | 1.78 (#11) | pass | none | -26.0% | 8.9% | 16% | 6.15 · 0.62% | +0.1% #10/#7 · +1.4% #6 |
| 20 | baitoey_mr_4h | **0.472** | 0.475 | 0.59 / 0.54 / 0.29 | 0.60 / 0.32 | no [-0.253, -0.033] | 0.461 | 0.544 | 3.03 (#3) | pass | G6_median | -28.6% | 5.3% | 12% | 3.49 · 0.35% | -2.5% #28/#27 · +1.6% #6 |
| 21 | pol_combo_all | **0.458** | 0.421 | 0.59 / 0.53 / 0.25 | 0.65 / 0.23 | no [-0.257, -0.060] | 0.284 | 0.297 | — | pass | none | -20.0% | 6.9% | 19% | 3.30 · 0.33% | -2.3% #24/#25 · +7.1% #3 |
| 22 | pol_mom_ss | **0.458** | 0.430 | 0.57 / 0.52 / 0.28 | 0.47 / 0.45 | no [-0.295, -0.015] | 0.321 | 0.306 | 1.08 (#20) | pass | none | -16.3% | 4.8% | 15% | 5.28 · 0.53% | +0.8% #4/#6 · +3.2% #6 |
| 23 | pol_switch3_cap | **0.456** | 0.385 | 0.59 / 0.49 / 0.29 | 0.49 / 0.42 | no [-0.258, -0.045] | 0.690 | 0.402 | 1.49 (#15) | pass | G6_median | -31.2% | 6.4% | 18% | 5.81 · 0.57% | +1.6% #4/#5 · -2.5% #13 |
| 24 | pol_combo_rt | **0.456** | 0.397 | 0.55 / 0.50 / 0.32 | 0.57 / 0.33 | no [-0.257, -0.063] | 0.286 | 0.287 | — | pass | none | -16.1% | 6.4% | 4% | 5.58 · 0.56% | -0.8% #18/#14 · +5.0% #5 |
| 25 | pol_switch_rc | **0.443** | 0.373 | 0.58 / 0.45 / 0.31 | 0.53 / 0.33 | no [-0.278, -0.075] | 0.247 | 0.233 | — | pass | none | -21.8% | 7.7% | 6% | 3.68 · 0.37% | -0.0% #13/#10 · +5.2% #4 |
| 26 | pol_switch3 | **0.438** | 0.380 | 0.52 / 0.48 / 0.31 | 0.53 / 0.33 | no [-0.267, -0.063] | 0.841 | 0.535 | 1.35 (#18) | pass | G6_median | -31.2% | 7.2% | 19% | 6.44 · 0.63% | +1.6% #4/#5 · -2.5% #13 |
| 27 | pol_combo_rtt | **0.434** | 0.372 | 0.55 / 0.49 / 0.26 | 0.57 / 0.27 | no [-0.269, -0.095] | 0.295 | 0.299 | — | pass | none | -18.8% | 5.8% | 7% | 4.00 · 0.40% | -1.5% #21/#20 · +5.1% #4 |
| 28 | pol_trend_ls | **0.418** | 0.395 | 0.51 / 0.46 / 0.29 | 0.37 / 0.48 | no [-0.317, -0.062] | 0.288 | 0.282 | 2.18 (#6) | pass | none | -18.7% | 6.5% | 20% | 5.83 · 0.58% | -0.0% #13/#10 · -5.4% #14 |
| 29 | pol_combo_ms_tl | **0.415** | 0.393 | 0.52 / 0.47 / 0.25 | 0.38 / 0.45 | no [-0.338, -0.042] | 0.295 | 0.296 | — | pass | none | -12.4% | 5.0% | 6% | 5.41 · 0.54% | +0.4% #8/#6 · -0.3% #9 |
| 30 | baitoey_tg_mom | **0.374** | 0.351 | 0.55 / 0.43 / 0.14 | 0.36 / 0.40 | no [-0.373, -0.091] | 0.269 | 0.257 | 0.91 (#22) | pass | none | -9.7% | 3.4% | 7% | 3.83 · 0.38% | -0.5% #17/#12 · -1.2% #12 |
| 31 | book_coin_trend ⚠ worse than doing nothing for the top-20 gate | **0.353** | 0.300 | 0.50 / 0.42 / 0.13 | 0.52 / 0.16 | no [-0.362, -0.165] | 0.287 | 0.304 | — | pass | none | -24.1% | 6.1% | 54% | 2.09 · 0.21% | -2.8% #30/#30 · +3.2% #6 |

## Reference rows (benchmarks, CASH included)

| | Model | HEADLINE_RET | without post-holdout | HIT L / M / S | HIT UP / DOWN | Tie group (90% interval vs top) | CS_HIT (V1 HKT) | V1 UTC days | old REL (rank) | Hard gates | Report-only gates failed | Worst R | Median MDD | Guard-only days | Turnover · fees / window | Replay R1 HK/SG · Final |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|  | ROT_EW | **0.547** | 0.507 | 0.59 / 0.56 / 0.49 | 0.71 / 0.36 | no [-0.141, +0.001] | 0.306 | 0.294 | 1.67 (#12) | pass | none | -33.5% | 10.4% | 56% | 2.94 · 0.30% | +0.4% #7/#6 · +13.5% #2 |
|  | ROT_IV | **0.511** | 0.456 | 0.60 / 0.55 / 0.38 | 0.65 / 0.35 | no [-0.202, -0.023] | 0.334 | 0.332 | 0.06 (#24) | pass | none | -24.0% | 7.0% | 55% | 2.35 · 0.24% | -0.4% #17/#11 · +9.4% #2 |
|  | BTC_HOLD | **0.478** | 0.491 | 0.62 / 0.53 / 0.29 | 0.81 / 0.08 | no [-0.212, -0.048] | 0.317 | 0.304 | 1.55 (#14) | pass | G2, G3 | -37.3% | 8.6% | 7% | 1.05 · 0.11% | -5.8% #40/#39 · +10.7% #2 |
|  | EW_DAILY | **0.468** | 0.444 | 0.53 / 0.49 / 0.39 | 0.73 / 0.15 | no [-0.231, -0.045] | 0.321 | 0.330 | 1.42 (#16) | pass | G2, G3, G6_median, G6_worst | -47.3% | 13.8% | 0% | 1.66 · 0.17% | -5.8% #40/#39 · +5.8% #3 |
|  | MOM_SS25 | **0.458** | 0.430 | 0.57 / 0.52 / 0.28 | 0.47 / 0.45 | no [-0.295, -0.015] | 0.321 | 0.306 | 1.08 (#19) | pass | none | -16.3% | 4.8% | 15% | 5.28 · 0.53% | +0.8% #4/#6 · +3.2% #6 |
|  | TREND_2 | **0.449** | 0.423 | 0.62 / 0.51 / 0.22 | 0.69 / 0.17 | no [-0.240, -0.085] | 0.312 | 0.308 | 0.22 (#23) | pass | G6_median | -16.9% | 5.2% | 87% | 1.04 · 0.10% | -2.2% #24/#25 · +5.5% #4 |
|  | CASH | **0.372** | 0.326 | 0.75 / 0.31 / 0.05 | 0.38 / 0.36 | no [-0.313, -0.157] | -0.002 | -0.002 | 0.00 (#25) | pass | G6_median | -0.1% | 0.0% | 0% | 0.06 · 0.01% | -0.0% #12/#10 · +0.0% #9 |

**Pick (full pool), rule margin 0.03 (Pol's proposal): `book_orch`.** Tie group: `book_orch`, `pol_abl_shock`.

Under the legacy (pre-registered) rule the pick would be `baitoey_vt_dual`. Rule: top-level `selection:` in config.yaml; evidence in reports/review/20261002-selection-rule.md.

## Without the post-holdout windows (in-sample pool, its own weights, pi_up and tie group)

| # | Model | HEADLINE_RET | HIT L / M / S | HIT UP / DOWN | Tie group (90% interval vs top) | CS_HIT | Full-pool rank |
|---|---|---|---|---|---|---|---|
| 1 | baitoey_vt_dual | 0.541 | 0.60 / 0.56 / 0.47 | 0.69 / 0.36 | **yes** [-0.052, +0.007] | 0.301 | 4 |
| 2 | book_orch | 0.561 | 0.61 / 0.57 / 0.51 | 0.75 / 0.34 | **yes** [+0.000, +0.000] | 0.319 | 1 |
| 3 | baitoey_vt_mom | 0.556 | 0.60 / 0.57 / 0.50 | 0.75 / 0.32 | **yes** [-0.011, +0.002] | 0.316 | 3 |
| 4 | pol_abl_shock | 0.555 | 0.60 / 0.57 / 0.50 | 0.73 / 0.35 | **yes** [-0.022, +0.012] | 0.304 | 2 |
| 5 | book_vt_top4 | 0.519 | 0.58 / 0.54 / 0.43 | 0.69 / 0.33 | no [-0.084, +0.001] | 0.292 | 5 |
| 6 | baitoey_rot_max | 0.509 | 0.55 / 0.52 / 0.46 | 0.66 / 0.34 | no [-0.109, +0.006] | 0.257 | 8 |
| 7 | pol_switch_vt_tl_e20v45 | 0.501 | 0.55 / 0.52 / 0.43 | 0.60 / 0.39 | no [-0.110, -0.010] | 0.320 | 6 |
| 8 | pol_mr_cap | 0.497 | 0.63 / 0.53 / 0.33 | 0.55 / 0.43 | no [-0.184, +0.049] | 0.419 | 13 |
| 9 | pol_vt_mvr | 0.479 | 0.55 / 0.51 / 0.38 | 0.65 / 0.28 | no [-0.131, -0.037] | 0.305 | 10 |
| 10 | baitoey_mr_4h | 0.475 | 0.57 / 0.53 / 0.33 | 0.61 / 0.32 | no [-0.197, +0.021] | 0.391 | 20 |
| 11 | book_vt_dual | 0.474 | 0.54 / 0.50 / 0.38 | 0.62 / 0.30 | no [-0.133, -0.040] | 0.300 | 9 |
| 12 | baitoey_mr_bbrsi | 0.467 | 0.70 / 0.48 / 0.23 | 0.50 / 0.43 | no [-0.202, +0.029] | 0.139 | 14 |
| 13 | pol_switch_rot_mr | 0.461 | 0.53 / 0.48 / 0.37 | 0.65 / 0.24 | no [-0.174, -0.015] | 0.325 | 12 |
| 14 | pol_combo_rb | 0.457 | 0.53 / 0.48 / 0.36 | 0.73 / 0.14 | no [-0.190, -0.018] | 0.267 | 17 |
| 15 | book_vt_breadth | 0.456 | 0.55 / 0.49 / 0.32 | 0.62 / 0.26 | no [-0.138, -0.071] | 0.287 | 11 |
| 16 | pol_switch_vt_tl | 0.456 | 0.51 / 0.47 / 0.38 | 0.49 / 0.41 | no [-0.215, +0.000] | 0.307 | 7 |
| 17 | pol_switch_rmax_mr | 0.449 | 0.51 / 0.47 / 0.37 | 0.65 / 0.21 | no [-0.195, -0.020] | 0.353 | 18 |
| 18 | pol_mom_ss | 0.430 | 0.55 / 0.49 / 0.25 | 0.45 / 0.41 | no [-0.282, +0.007] | 0.274 | 22 |
| 19 | pol_switch_rmax_tl | 0.421 | 0.47 / 0.44 / 0.36 | 0.45 / 0.39 | no [-0.282, -0.005] | 0.278 | 15 |
| 20 | pol_combo_all | 0.421 | 0.55 / 0.48 / 0.23 | 0.62 / 0.18 | no [-0.241, -0.042] | 0.248 | 21 |
| 21 | pol_switch_vtm_tl | 0.416 | 0.47 / 0.44 / 0.34 | 0.44 / 0.38 | no [-0.281, -0.020] | 0.314 | 16 |
| 22 | pol_switch_rt | 0.408 | 0.46 / 0.43 / 0.34 | 0.45 / 0.36 | no [-0.311, -0.007] | 0.291 | 19 |
| 23 | pol_combo_rt | 0.397 | 0.49 / 0.44 / 0.26 | 0.50 / 0.28 | no [-0.264, -0.064] | 0.279 | 24 |
| 24 | pol_trend_ls | 0.395 | 0.47 / 0.43 / 0.28 | 0.34 / 0.46 | no [-0.300, -0.028] | 0.268 | 28 |
| 25 | pol_combo_ms_tl | 0.393 | 0.50 / 0.44 / 0.23 | 0.38 / 0.41 | no [-0.317, -0.016] | 0.254 | 29 |
| 26 | pol_switch3_cap | 0.385 | 0.51 / 0.41 / 0.24 | 0.40 / 0.37 | no [-0.307, -0.034] | 0.286 | 23 |
| 27 | pol_switch3 | 0.380 | 0.46 / 0.42 / 0.26 | 0.43 / 0.32 | no [-0.303, -0.038] | 0.347 | 26 |
| 28 | pol_switch_rc | 0.373 | 0.53 / 0.36 / 0.23 | 0.45 / 0.28 | no [-0.295, -0.085] | 0.218 | 25 |
| 29 | pol_combo_rtt | 0.372 | 0.49 / 0.43 / 0.20 | 0.49 / 0.23 | no [-0.281, -0.092] | 0.274 | 27 |
| 30 | baitoey_tg_mom | 0.351 | 0.51 / 0.38 / 0.17 | 0.30 / 0.41 | no [-0.368, -0.057] | 0.261 | 30 |
| 31 | book_coin_trend ⚠ worse than doing nothing | 0.300 | 0.43 / 0.35 / 0.12 | 0.45 / 0.12 | no [-0.368, -0.155] | 0.250 | 31 |
| | ROT_EW | 0.507 | 0.55 / 0.52 / 0.45 | 0.67 / 0.31 | — | 0.264 | — |
| | ROT_IV | 0.456 | 0.56 / 0.50 / 0.30 | 0.59 / 0.30 | — | 0.259 | — |
| | BTC_HOLD | 0.491 | 0.60 / 0.52 / 0.35 | 0.85 / 0.07 | — | 0.267 | — |
| | EW_DAILY | 0.444 | 0.50 / 0.46 / 0.37 | 0.71 / 0.14 | — | 0.278 | — |
| | MOM_SS25 | 0.430 | 0.55 / 0.49 / 0.25 | 0.45 / 0.41 | — | 0.274 | — |
| | TREND_2 | 0.423 | 0.57 / 0.47 / 0.23 | 0.67 / 0.13 | — | 0.246 | — |
| | CASH | 0.326 | 0.68 / 0.24 / 0.06 | 0.30 / 0.36 | — | -0.004 | — |

**Pick without the post-holdout windows, rule margin 0.03 (Pol's proposal): `baitoey_vt_dual`.** Under the legacy (pre-registered) rule: `baitoey_mr_4h`.

Columns: HIT L / M / S = the share of weight clearing LENIENT (−1.4965% in DOWN windows, 0% in UP windows, an assumption), MIDDLE (0%) and STRICT (max(0, the 6 gate benchmarks' median)); HIT UP / DOWN = the mean of the three HITs on UP and on DOWN windows, each group's weights renormalized. CS_HIT = mean composite (V1 FLOORED) over the windows clearing LENIENT, on HKT days and on UTC days. Old REL = the primary of tool version `56cb5a2e85d45862` (report only). Hard gates: G1 (≥ 10 active HKT days in every window), G4 (long-only run completes), G5 (leakage). Report-only gates: G2, G3, G6_median, G6_worst. Replay: the previous edition's two real windows from cash, R and rank among its teams (numbers only).

## Return view (report-only): ranked by the size of the 14-day return

The main ranking above is by HEADLINE_RET: how often the return clears the cut. This view ranks the same runs by how large the return is: the mean 14-day R_liq weighted with the same final weights w' (live-like, recency, direction-balanced). It is shown so both can be read side by side; it does not change the pick or the order above.

| Return rank | Model | Mean R_liq (w') | without post-holdout (rank) | Median R_liq (w') | 10th pct | 90th pct | Share > 0 | Plain median | Worst | Best | Main rank (HEADLINE_RET) | Eligible |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | book_orch | **+5.03%** | +2.71% (#1) | +3.21% | -9.0% | +23.6% | 63% | +1.22% | -30.1% | +68.4% | #1 | yes |
| 2 | baitoey_vt_mom | **+4.86%** | +2.54% (#2) | +2.60% | -9.1% | +23.6% | 62% | +1.17% | -30.9% | +71.3% | #3 | yes |
| 3 | pol_switch_vt_tl_e20v45 | **+4.84%** | +1.77% (#7) | +1.65% | -10.0% | +27.7% | 59% | +0.30% | -26.2% | +98.6% | #6 | yes |
| 4 | pol_abl_shock | **+4.75%** | +2.47% (#3) | +2.53% | -9.3% | +23.6% | 62% | +0.70% | -26.8% | +59.1% | #2 | yes |
| 5 | book_vt_top4 | **+4.49%** | +1.93% (#6) | +2.02% | -8.6% | +24.6% | 59% | +0.84% | -30.7% | +75.9% | #5 | yes |
| 6 | book_vt_dual | **+4.44%** | +2.08% (#5) | +1.60% | -7.5% | +22.5% | 56% | -0.25% | -19.9% | +71.3% | #9 | yes |
| 7 | baitoey_vt_dual | **+4.41%** | +2.31% (#4) | +1.82% | -8.3% | +23.6% | 61% | +0.48% | -23.5% | +71.3% | #4 | yes |
| 8 | pol_vt_mvr | **+4.03%** | +1.53% (#10) | +1.23% | -7.5% | +22.0% | 55% | +0.85% | -27.9% | +70.7% | #10 | yes |
| 9 | pol_switch_vt_tl | **+3.88%** | +1.04% (#11) | +1.20% | -8.1% | +21.6% | 56% | +0.17% | -27.0% | +66.5% | #7 | yes |
| 10 | baitoey_rot_max | **+3.85%** | +1.66% (#9) | +1.68% | -13.7% | +23.9% | 56% | +0.68% | -48.4% | +287.9% | #8 | yes |
| 11 | book_vt_breadth | **+3.53%** | +1.69% (#8) | +0.64% | -6.4% | +18.3% | 55% | -0.25% | -16.8% | +71.3% | #11 | yes |
| 12 | pol_switch_vtm_tl | **+3.42%** | +0.72% (#12) | +0.28% | -7.5% | +21.2% | 51% | -0.01% | -20.4% | +65.9% | #16 | yes |
| 13 | pol_switch_rmax_mr | **+3.17%** | +0.58% (#13) | -0.07% | -13.3% | +25.4% | 50% | -0.17% | -36.1% | +152.0% | #18 | yes |
| 14 | pol_switch_rmax_tl | **+3.09%** | +0.49% (#15) | +0.45% | -11.9% | +22.4% | 51% | -0.41% | -30.5% | +281.6% | #15 | yes |
| 15 | pol_switch_rot_mr | **+2.44%** | +0.29% (#19) | +0.59% | -10.7% | +17.6% | 54% | +0.05% | -32.7% | +61.3% | #12 | yes |
| 16 | pol_switch_rc | **+1.90%** | +0.38% (#18) | -0.01% | -9.6% | +16.5% | 45% | -0.01% | -21.8% | +57.6% | #25 | yes |
| 17 | pol_combo_rb | **+1.82%** | +0.54% (#14) | +0.59% | -8.6% | +14.7% | 52% | +0.65% | -30.1% | +55.3% | #17 | yes |
| 18 | pol_switch_rt | **+1.76%** | +0.15% (#22) | +0.06% | -10.4% | +16.7% | 50% | -0.24% | -26.0% | +57.6% | #19 | yes |
| 19 | pol_combo_all | **+1.61%** | +0.39% (#17) | +0.28% | -6.3% | +12.6% | 53% | +0.15% | -20.0% | +38.8% | #21 | yes |
| 20 | pol_combo_rtt | **+1.42%** | +0.26% (#20) | -0.10% | -5.6% | +11.4% | 49% | -0.16% | -18.8% | +40.7% | #27 | yes |
| 21 | pol_combo_rt | **+1.36%** | +0.39% (#16) | -0.03% | -7.1% | +12.0% | 50% | -0.24% | -16.1% | +40.1% | #24 | yes |
| 22 | book_coin_trend | **+1.28%** | +0.09% (#23) | -0.69% | -5.3% | +13.4% | 42% | -0.74% | -24.1% | +92.2% | #31 | yes |
| 23 | pol_mom_ss | **+0.76%** | +0.25% (#21) | +0.24% | -6.3% | +9.1% | 52% | +0.09% | -16.3% | +25.3% | #22 | yes |
| 24 | pol_switch3_cap | **+0.74%** | -1.09% (#30) | -0.03% | -6.3% | +7.8% | 49% | -0.01% | -31.2% | +61.4% | #23 | yes |
| 25 | pol_switch3 | **+0.60%** | -1.30% (#31) | -0.17% | -7.8% | +9.3% | 48% | -0.17% | -31.2% | +61.4% | #26 | yes |
| 26 | pol_combo_ms_tl | **+0.49%** | +0.03% (#24) | -0.22% | -4.8% | +8.4% | 47% | -0.07% | -12.5% | +25.2% | #29 | yes |
| 27 | pol_trend_ls | **+0.29%** | -0.30% (#27) | -0.47% | -6.4% | +9.1% | 46% | -0.05% | -18.7% | +33.0% | #28 | yes |
| 28 | baitoey_tg_mom | **+0.22%** | -0.11% (#25) | -0.44% | -3.5% | +5.5% | 43% | -0.02% | -9.7% | +25.3% | #30 | yes |
| 29 | pol_mr_cap | **+0.19%** | -0.28% (#26) | +0.58% | -4.9% | +4.9% | 57% | +0.52% | -25.6% | +16.2% | #13 | yes |
| 30 | baitoey_mr_4h | **+0.08%** | -0.43% (#29) | +0.63% | -6.6% | +6.2% | 54% | +0.63% | -28.7% | +21.0% | #20 | yes |
| 31 | baitoey_mr_bbrsi | **-0.17%** | -0.42% (#28) | +0.00% | -1.9% | +2.2% | 54% | +0.00% | -25.3% | +22.1% | #14 | yes |
| ref | ROT_EW | **+3.14%** | +1.27% | +1.31% | -10.6% | +20.3% | 56% | +0.66% | -33.6% | +76.8% | ref | yes |
| ref | ROT_IV | **+2.54%** | +0.85% | +0.96% | -6.4% | +13.0% | 55% | +0.61% | -24.0% | +41.3% | ref | yes |
| ref | EW_DAILY | **+2.15%** | +0.27% | -0.49% | -12.7% | +23.9% | 49% | -0.15% | -47.3% | +133.7% | ref | yes |
| ref | TREND_2 | **+1.60%** | +0.15% | +0.04% | -6.3% | +10.0% | 51% | -0.13% | -16.9% | +45.6% | ref | yes |
| ref | BTC_HOLD | **+1.39%** | +0.28% | +0.26% | -7.2% | +10.8% | 53% | +0.60% | -37.4% | +69.2% | ref | yes |
| ref | MOM_SS25 | **+0.76%** | +0.25% | +0.24% | -6.3% | +9.1% | 52% | +0.09% | -16.3% | +25.3% | ref | yes |
| ref | CASH | **-0.00%** | -0.01% | -0.01% | -0.0% | +0.0% | 31% | -0.01% | -0.1% | +0.1% | ref | yes |

## Why: results by market type (report-only)

Hit rate (mean of the three bars) per type of 14-day window, with the model's average net exposure in brackets; weights w'. Types from BTC: strong fall <= -5%, mild fall, mild rise, strong rise >= +5% over 14 days; turning point = first and second week move >= 2% in opposite directions; calm / volatile = low / high volatility tercile. The sentence names the types at least 10 points above or below the model's own average and what it held there (backtest/scoring/explain.py).

| Model | All | strong fall | mild fall | mild rise | strong rise | turning point | calm | volatile | Why (measured) |
|---|---|---|---|---|---|---|---|---|---|
| *share of weight* | 100% | 16% | 30% | 29% | 26% | 25% | 64% | 8% | |
| book_orch | 62% | 21% (+74%) | 49% (+84%) | 72% (+83%) | 90% (+83%) | 59% (+78%) | 70% (+86%) | 36% (+68%) | Strong in strong rise windows (90% vs 62% overall; 83% net long); weak in strong fall windows (21%; it stays 74% net long while prices drop). |
| pol_abl_shock | 61% | 24% (+73%) | 47% (+85%) | 70% (+84%) | 89% (+83%) | 56% (+78%) | 69% (+88%) | 32% (+65%) | Strong in strong rise windows (89% vs 61% overall; 83% net long); weak in strong fall windows (24%; it stays 73% net long while prices drop). |
| baitoey_vt_mom | 61% | 20% (+76%) | 47% (+85%) | 72% (+84%) | 90% (+83%) | 56% (+79%) | 69% (+88%) | 37% (+70%) | Strong in strong rise windows (90% vs 61% overall; 83% net long); weak in strong fall windows (20%; it stays 76% net long while prices drop). |
| baitoey_vt_dual | 59% | 24% (+56%) | 48% (+72%) | 64% (+74%) | 86% (+80%) | 54% (+70%) | 66% (+78%) | 34% (+48%) | Strong in strong rise windows (86% vs 59% overall; 80% net long); weak in strong fall windows (24%; it stays 56% net long while prices drop). |
| book_vt_top4 | 57% | 21% (+74%) | 45% (+81%) | 66% (+80%) | 84% (+78%) | 55% (+74%) | 63% (+83%) | 37% (+68%) | Strong in strong rise windows (84% vs 57% overall; 78% net long); weak in strong fall windows (21%; it stays 74% net long while prices drop). |
| pol_switch_vt_tl_e20v45 | 57% | 36% (+21%) | 44% (+64%) | 61% (+61%) | 80% (+85%) | 57% (+62%) | 59% (+71%) | 35% (+32%) | Strong in strong rise windows (80% vs 57% overall; 85% net long); weak in volatile windows (35%; 32% net long). |
| pol_switch_vt_tl | 55% | 42% (+25%) | 46% (+62%) | 54% (+47%) | 75% (+68%) | 56% (+55%) | 57% (+62%) | 31% (+34%) | Strong in strong rise windows (75% vs 55% overall; 68% net long); weak in volatile windows (31%; 34% net long). |
| baitoey_rot_max | 55% | 24% (+100%) | 44% (+100%) | 59% (+100%) | 80% (+100%) | 47% (+100%) | 60% (+100%) | 34% (+100%) | Strong in strong rise windows (80% vs 55% overall; 100% net long); weak in strong fall windows (24%; it stays 100% net long while prices drop). |
| book_vt_dual | 53% | 25% (+53%) | 41% (+68%) | 56% (+67%) | 82% (+77%) | 49% (+66%) | 60% (+74%) | 31% (+47%) | Strong in strong rise windows (82% vs 53% overall; 77% net long); weak in strong fall windows (25%; it stays 53% net long while prices drop). |
| pol_vt_mvr | 53% | 19% (+61%) | 40% (+66%) | 54% (+65%) | 87% (+71%) | 49% (+63%) | 57% (+70%) | 37% (+56%) | Strong in strong rise windows (87% vs 53% overall; 71% net long); weak in strong fall windows (19%; it stays 61% net long while prices drop). |
| book_vt_breadth | 52% | 21% (+44%) | 37% (+61%) | 56% (+60%) | 83% (+72%) | 49% (+59%) | 59% (+66%) | 29% (+43%) | Strong in strong rise windows (83% vs 52% overall; 72% net long); weak in strong fall windows (21%; it stays 44% net long while prices drop). |
| pol_switch_rot_mr | 51% | 12% (+59%) | 39% (+73%) | 60% (+62%) | 79% (+73%) | 52% (+66%) | 58% (+73%) | 38% (+55%) | Strong in strong rise windows (79% vs 51% overall; 73% net long); weak in strong fall windows (12%; it stays 59% net long while prices drop). |
| pol_mr_cap | 51% | 26% (+33%) | 58% (+27%) | 52% (+22%) | 56% (+14%) | 50% (+23%) | 54% (+24%) | 46% (+18%) | Weak in strong fall windows (26%; it stays 33% net long while prices drop). |
| baitoey_mr_bbrsi | 50% | 38% (+21%) | 50% (+12%) | 47% (+10%) | 60% (+5%) | 50% (+10%) | 50% (+10%) | 63% (+11%) | Strong in volatile windows (63% vs 50% overall; mostly in cash (11% invested)); weak in strong fall windows (38%; mostly in cash (21% invested)). |
| pol_switch_rmax_tl | 49% | 42% (+34%) | 41% (+71%) | 45% (+55%) | 67% (+80%) | 47% (+67%) | 50% (+71%) | 31% (+48%) | Strong in strong rise windows (67% vs 49% overall; 80% net long); weak in volatile windows (31%; 48% net long). |
| pol_switch_vtm_tl | 49% | 42% (+20%) | 38% (+50%) | 41% (+38%) | 73% (+60%) | 51% (+46%) | 47% (+51%) | 30% (+28%) | Strong in strong rise windows (73% vs 49% overall; 60% net long); weak in volatile windows (30%; close to flat (+28% net)). |
| pol_combo_rb | 48% | 10% (+88%) | 23% (+92%) | 57% (+92%) | 91% (+92%) | 41% (+89%) | 51% (+93%) | 34% (+85%) | Strong in strong rise windows (91% vs 48% overall; 92% net long); weak in strong fall windows (10%; it stays 88% net long while prices drop). |
| pol_switch_rmax_mr | 47% | 14% (+67%) | 35% (+82%) | 57% (+70%) | 72% (+85%) | 48% (+79%) | 54% (+82%) | 37% (+68%) | Strong in strong rise windows (72% vs 47% overall; 85% net long); weak in strong fall windows (14%; it stays 67% net long while prices drop). |
| pol_switch_rt | 47% | 44% (+26%) | 37% (+61%) | 42% (+47%) | 67% (+67%) | 47% (+54%) | 47% (+61%) | 30% (+35%) | Strong in strong rise windows (67% vs 47% overall; 67% net long); weak in volatile windows (30%; 35% net long). |
| baitoey_mr_4h | 47% | 12% (+41%) | 43% (+36%) | 58% (+32%) | 61% (+23%) | 43% (+32%) | 50% (+34%) | 42% (+25%) | Strong in strong rise windows (61% vs 47% overall; mostly in cash (23% invested)); weak in strong fall windows (12%; it stays 41% net long while prices drop). |
| pol_combo_all | 46% | 12% (+57%) | 28% (+67%) | 51% (+65%) | 80% (+70%) | 39% (+64%) | 50% (+69%) | 27% (+56%) | Strong in strong rise windows (80% vs 46% overall; 70% net long); weak in strong fall windows (12%; it stays 57% net long while prices drop). |
| pol_mom_ss | 46% | 35% (+12%) | 49% (+23%) | 41% (+25%) | 53% (+27%) | 46% (+19%) | 52% (+26%) | 32% (+13%) | Weak in volatile windows (32%; close to flat (+13% net)). |
| pol_switch3_cap | 46% | 31% (+26%) | 48% (+26%) | 40% (+23%) | 58% (+24%) | 49% (+25%) | 46% (+28%) | 37% (+16%) | Strong in strong rise windows (58% vs 46% overall; close to flat (+24% net)); weak in strong fall windows (31%; close to flat (+26% net)). |
| pol_combo_rt | 46% | 30% (+39%) | 34% (+48%) | 46% (+47%) | 68% (+54%) | 41% (+46%) | 50% (+50%) | 31% (+36%) | Strong in strong rise windows (68% vs 46% overall; 54% net long); weak in strong fall windows (30%; it stays 39% net long while prices drop). |
| pol_switch_rc | 44% | 33% (+32%) | 34% (+64%) | 37% (+50%) | 72% (+68%) | 43% (+56%) | 47% (+64%) | 36% (+41%) | Strong in strong rise windows (72% vs 44% overall; 68% net long); weak in strong fall windows (33%; it stays 32% net long while prices drop). |
| pol_switch3 | 44% | 20% (+32%) | 40% (+34%) | 46% (+29%) | 61% (+30%) | 44% (+31%) | 44% (+35%) | 35% (+21%) | Strong in strong rise windows (61% vs 44% overall; 30% net long); weak in strong fall windows (20%; it stays 32% net long while prices drop). |
| pol_combo_rtt | 43% | 22% (+41%) | 30% (+57%) | 42% (+53%) | 73% (+63%) | 41% (+54%) | 47% (+59%) | 27% (+41%) | Strong in strong rise windows (73% vs 43% overall; 63% net long); weak in strong fall windows (22%; it stays 41% net long while prices drop). |
| pol_trend_ls | 42% | 51% (+2%) | 46% (+11%) | 36% (+9%) | 38% (+25%) | 45% (+15%) | 44% (+13%) | 33% (+1%) | About the same in every market type. |
| pol_combo_ms_tl | 41% | 40% (+7%) | 48% (+17%) | 37% (+17%) | 40% (+26%) | 39% (+17%) | 48% (+20%) | 31% (+7%) | Weak in volatile windows (31%; close to flat (+7% net)). |
| baitoey_tg_mom | 37% | 56% (-7%) | 31% (+3%) | 25% (+10%) | 48% (+20%) | 40% (+6%) | 34% (+9%) | 30% (+1%) | Strong in strong fall windows (56% vs 37% overall; net short (-7%)); weak in mild rise windows (25%; it is under-invested (+10% net) while prices rise). |
| book_coin_trend | 35% | 6% (+40%) | 21% (+52%) | 33% (+51%) | 72% (+67%) | 34% (+55%) | 37% (+56%) | 26% (+46%) | Strong in strong rise windows (72% vs 35% overall; 67% net long); weak in strong fall windows (6%; it stays 40% net long while prices drop). |
| team_btc_hold | 48% | 0% (+100%) | 12% (+100%) | 81% (+100%) | 82% (+100%) | 45% (+100%) | 49% (+100%) | 43% (+100%) | Strong in strong rise windows (82% vs 48% overall; 100% net long); weak in strong fall windows (0%; it stays 100% net long while prices drop). |

## Runs per person (this tool version)

| Person | Full runs | Best eligible candidate HEADLINE_RET |
|---|---|---|
| baitoey | 6 | 0.609 (baitoey_vt_mom) |
| book | 5 | 0.617 (book_orch) |
| pol | 20 | 0.607 (pol_abl_shock) |
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
