# Recovery model comparison — frozen BTC-only diagnostic

**No live recommendation. Adaptive scoring remains OFF.**

Prior guard cost/delay/calendar audit: /home/ubuntu/test/MiniMax/results/book/20261011-recovery-stress-v1/README.md
Its failed reliability checks remain a veto; new rank positions do not override them.

Query remains Oct11 01:00 HKT; 25 spaced BTC-only historical matches. This refresh adds two fixed research models
without reselecting windows. Newer price-only context is saved separately; it does not change these cases.
Rank = lower of 7/8-day average after-cost cash-start returns; exact ties are alphabetical by model name.
Rank is a point estimate, not proof of an edge. Equal-return rows do not establish superiority over one another.
The uniform 95% lower differences account jointly for 135 models and 2 horizons with 23 purged cases in 14 quarters.
All history is spent. Strict broad coverage still fails at BCH: 29/30. Actual holdings and endgame replay are unverified.
The fourteen new recovery models have model-core results here; full original competition gate eligibility is UNVERIFIED.
CS and drawdown are in the CSV. Short-imitation F1 is distinct from profitable-short accuracy; neither is inferred here.

| Rank | Model | 7-day mean | 8-day mean | 7-day bad10 | 8-day bad10 | Lower difference (7/8 days) | Diagnostic pass |
|---|---|---:|---:|---:|---:|---|---|
| 1 | baitoey_rot_max | +4.93% | +5.64% | -7.70% | -8.72% | -4.75% / -4.38% | NO |
| 2 | pol_switch_rmax_tl | +4.21% | +4.45% | -7.00% | -8.89% | -5.37% / -5.36% | NO |
| 3 | baitoey_ovl_brk_dual | +4.11% | +4.50% | -4.43% | -4.35% | -5.41% / -5.28% | NO |
| 4 | baitoey_vt_dual | +4.02% | +4.59% | -5.28% | -4.35% | -5.42% / -5.30% | NO |
| 5 | book_cashshort_pullback | +3.93% | +4.32% | -4.46% | -4.35% | -5.54% / -5.41% | NO |
| 6 | book_vt_dual | +3.92% | +4.30% | -4.71% | -5.56% | -5.61% / -5.58% | NO |
| 7 | baitoey_ovl_evt_dual | +3.91% | +4.37% | -5.51% | -4.66% | -5.55% / -5.50% | NO |
| 8 | book_cashshort_confirm | +3.89% | +4.31% | -4.61% | -4.35% | -5.56% / -5.41% | NO |
| 9 | pol_switch_rmax_mr | +3.76% | +4.10% | -7.49% | -9.27% | -6.10% / -6.02% | NO |
| 10 | baitoey_ovl_evtctl_dual | +3.72% | +4.28% | -5.63% | -5.15% | -5.75% / -5.64% | NO |
| 11 | book_vt_top4 | +3.36% | +3.71% | -6.65% | -7.13% | -6.32% / -6.31% | NO |
| 12 | book_recovery_abs | +3.31% | +3.63% | -5.92% | -7.73% | -6.26% / -6.12% | NO |
| 13 | pol_switch_rc | +3.36% | +3.25% | -4.78% | -6.78% | -6.56% / -6.99% | NO |
| 14 | book_orch | +3.25% | +3.78% | -5.59% | -8.43% | -6.45% / -6.31% | NO |
| 15 | baitoey_vt_mom | +3.22% | +3.75% | -5.79% | -8.47% | -6.43% / -6.29% | NO |
| 16 | baitoey_ovl_evt_e20 | +3.17% | +3.26% | -6.74% | -10.26% | -6.50% / -6.64% | NO |
| 17 | team_rot_ew | +3.16% | +3.56% | -6.82% | -7.89% | -6.57% / -6.56% | NO |
| 18 | baitoey_e20_btcs_b | +3.00% | +3.20% | -7.28% | -10.37% | -6.79% / -6.87% | NO |
| 19 | book_transition_short | +2.99% | +3.46% | -5.57% | -5.39% | -6.70% / -6.53% | NO |
| 20 | book_recovery_allshort24 | +2.96% | +3.21% | -8.42% | -9.70% | -6.50% / -6.50% | NO |
| 21 | baitoey_e20_btcs_a | +2.96% | +3.16% | -7.28% | -10.41% | -6.80% / -6.88% | NO |
| 22 | baitoey_e20_btcs_d | +2.96% | +3.16% | -7.28% | -10.41% | -6.80% / -6.88% | NO |
| 23 | pol_abl_shock | +2.84% | +3.34% | -5.94% | -8.51% | -6.84% / -6.74% | NO |
| 24 | book_recovery_rebound | +2.84% | +3.01% | -7.32% | -9.28% | -6.70% / -6.74% | NO |
| 25 | baitoey_e20_shortc_sol | +2.84% | +2.94% | -7.06% | -10.41% | -6.88% / -7.00% | NO |
| 26 | pol_switch_vt_tl_e20v45 | +2.84% | +3.05% | -7.44% | -10.41% | -6.85% / -6.90% | NO |
| 27 | baitoey_e20_shortc_alts | +2.84% | +2.99% | -7.36% | -10.38% | -6.88% / -6.98% | NO |
| 28 | baitoey_e20_shortc_eth | +2.80% | +2.91% | -6.89% | -10.49% | -6.90% / -7.01% | NO |
| 29 | baitoey_ovl_evtctl_e20 | +2.79% | +2.99% | -7.44% | -10.41% | -6.91% / -6.98% | NO |
| 30 | baitoey_ovl_brk_e20 | +2.79% | +2.99% | -7.32% | -10.07% | -6.82% / -6.82% | NO |
| 31 | book_e20combo_brk_cash | +2.79% | +2.99% | -7.32% | -10.07% | -6.82% / -6.82% | NO |
| 32 | book_recovery_short | +2.79% | +2.99% | -7.32% | -10.07% | -6.82% / -6.82% | NO |
| 33 | baitoey_e20_btcs_c | +2.79% | +2.92% | -6.89% | -10.47% | -6.90% / -7.04% | NO |
| 34 | pol_vt_mvr | +2.77% | +3.27% | -4.89% | -5.53% | -6.97% / -6.81% | NO |
| 35 | pol_switch_vt_tl | +2.85% | +2.76% | -5.79% | -9.77% | -6.84% / -7.22% | NO |
| 36 | baitoey_e20_out10 | +2.75% | +3.26% | -6.07% | -6.39% | -6.95% / -6.68% | NO |
| 37 | book_vt_breadth | +2.75% | +3.28% | -5.41% | -5.16% | -7.02% / -6.77% | NO |
| 38 | pol_switch_rt | +2.76% | +2.56% | -5.07% | -7.48% | -7.11% / -7.59% | NO |
| 39 | book_recovery_quality_blend | +2.55% | +2.78% | -5.22% | -6.23% | -7.15% / -7.11% | NO |
| 40 | book_e20guard_pullback | +2.50% | +2.72% | -7.44% | -10.41% | -7.22% / -7.27% | NO |
| 41 | baitoey_e20_out15 | +2.49% | +3.01% | -7.21% | -7.43% | -7.23% / -6.95% | NO |
| 42 | book_e20guard_confirm | +2.48% | +2.72% | -7.44% | -10.65% | -7.24% / -7.26% | NO |
| 43 | pol_switch_rot_mr | +2.62% | +2.48% | -6.87% | -8.86% | -7.46% / -7.93% | NO |
| 44 | pol_switch_vtm_tl | +2.43% | +2.49% | -4.78% | -6.18% | -7.30% / -7.51% | NO |
| 45 | baitoey_e20_btcs_b2 | +2.43% | +2.66% | -6.84% | -8.53% | -7.42% / -7.45% | NO |
| 46 | book_recovery_quality | +2.38% | +2.77% | -6.34% | -7.35% | -7.34% / -7.12% | NO |
| 47 | book_recovery_resid | +2.36% | +2.90% | -7.28% | -9.09% | -7.32% / -7.02% | NO |
| 48 | pol_combo_rt | +2.29% | +2.40% | -3.38% | -3.44% | -7.51% / -7.87% | NO |
| 49 | book_recovery_both | +2.30% | +2.29% | -7.24% | -9.34% | -7.31% / -7.58% | NO |
| 50 | book_recovery_vol | +2.30% | +2.29% | -7.24% | -9.34% | -7.31% / -7.58% | NO |
| 51 | baitoey_e20_btcs_a2 | +2.24% | +2.46% | -6.66% | -8.34% | -7.51% / -7.56% | NO |
| 52 | pol_combo_rb | +2.17% | +2.61% | -4.46% | -5.77% | -7.74% / -7.67% | NO |
| 53 | team_rot_iv | +2.16% | +2.37% | -4.43% | -6.07% | -7.80% / -7.98% | NO |
| 54 | baitoey_ovl_altbtc_a_dual | +2.13% | +3.00% | -3.07% | -3.52% | -7.44% / -6.91% | NO |
| 55 | book_recovery_high_blend | +1.93% | +2.05% | -5.93% | -8.64% | -7.73% / -7.85% | NO |
| 56 | pol_combo_rtt | +1.91% | +2.16% | -3.79% | -4.08% | -7.91% / -8.06% | NO |
| 57 | book_recovery_abs_iv | +1.85% | +1.92% | -5.67% | -6.71% | -7.90% / -8.06% | NO |
| 59 | book_recovery_resid_blend | +1.67% | +2.18% | -7.40% | -9.25% | -8.04% / -7.71% | NO |
| 60 | pol_combo_all | +1.65% | +1.92% | -3.70% | -5.20% | -8.19% / -8.31% | NO |
| 61 | baitoey_ovl_altbtc_b_dual | +1.63% | +2.10% | -2.95% | -3.23% | -7.78% / -7.70% | NO |
| 62 | book_e20combo_alt_half_cash | +1.53% | +1.79% | -6.87% | -7.95% | -8.12% / -8.13% | NO |
| 63 | book_recovery_iv | +1.44% | +1.38% | -6.05% | -8.11% | -8.35% / -8.65% | NO |
| 64 | pol_combo_ms_tl | +1.28% | +1.27% | -2.34% | -2.57% | -8.25% / -8.74% | NO |
| 65 | pol_trend_ls | +1.34% | +1.27% | -2.76% | -2.48% | -8.26% / -8.84% | NO |
| 66 | team_ew_daily | +1.27% | +1.64% | -10.06% | -10.85% | -8.72% / -8.64% | NO |
| 67 | pol_switch3_cap | +1.26% | +1.74% | -3.34% | -4.04% | -8.48% / -8.25% | NO |
| 68 | pol_mom_ss | +1.25% | +1.27% | -3.11% | -3.49% | -8.21% / -8.63% | NO |
| 69 | team_mom_ss25 | +1.25% | +1.27% | -3.11% | -3.49% | -8.21% / -8.63% | NO |
| 70 | book_recovery_high | +1.63% | +1.24% | -5.96% | -8.17% | -7.98% / -8.63% | NO |
| 71 | pol_switch3 | +1.18% | +1.78% | -5.13% | -5.35% | -8.70% / -8.36% | NO |
| 72 | team_btc_hold | +1.08% | +1.78% | -5.73% | -6.40% | -8.73% / -8.37% | NO |
| 73 | team_trend_2 | +1.06% | +1.55% | -4.19% | -5.44% | -8.81% / -8.56% | NO |
| 75 | baitoey_tg_mom | +0.94% | +1.08% | -1.30% | -1.66% | -8.86% / -9.05% | NO |
| 76 | book_coin_trend | +0.78% | +1.00% | -4.22% | -4.88% | -8.93% / -8.97% | NO |
| 77 | baitoey_ovl_altbtc_a_e20 | +0.77% | +1.52% | -8.39% | -7.82% | -8.98% / -8.38% | NO |
| 78 | baitoey_mjt_12_48_d | +0.66% | +1.02% | -3.60% | -3.49% | -9.35% / -9.28% | NO |
| 81 | book_daily_channel | +0.52% | +1.00% | -2.75% | -1.97% | -9.07% / -8.83% | NO |
| 83 | book_price_slow_signed | +0.44% | +0.86% | -2.95% | -3.88% | -9.71% / -9.51% | NO |
| 86 | baitoey_mjt_24_96_6h | +0.39% | +0.72% | -4.56% | -5.37% | -9.75% / -9.60% | NO |
| 87 | baitoey_ovl_altbtc_b_e20 | +0.37% | +0.74% | -7.74% | -7.52% | -9.15% / -8.97% | NO |
| 89 | book_e20combo_alt_cash | +0.31% | +0.68% | -7.74% | -7.52% | -9.21% / -9.03% | NO |
| 90 | baitoey_mjt_06_24_d | +0.32% | +0.30% | -4.13% | -3.76% | -9.23% / -9.56% | NO |
| 91 | book_e20combo_alt_cash_pb | +0.30% | +0.67% | -7.74% | -7.52% | -9.22% / -9.04% | NO |
| 93 | book_e20combo_alt_trim | +0.24% | +0.61% | -7.74% | -7.52% | -9.29% / -9.10% | NO |
| 94 | baitoey_mjt_12_48_6h | +0.23% | +0.53% | -4.41% | -4.95% | -9.56% / -9.59% | NO |
| 95 | baitoey_btc_short_a | +0.22% | +0.21% | -0.00% | -0.00% | -9.52% / -9.90% | NO |
| 96 | baitoey_btc_short_d | +0.22% | +0.21% | -0.00% | -0.00% | -9.52% / -9.90% | NO |
| 99 | baitoey_mr_4h | +0.18% | +0.29% | -5.14% | -5.36% | -9.80% / -10.02% | NO |
| 101 | baitoey_btc_short_b2 | +0.21% | +0.18% | -0.79% | -0.96% | -9.56% / -9.97% | NO |
| 102 | baitoey_btc_short_b | +0.19% | +0.17% | -0.60% | -0.60% | -9.58% / -9.98% | NO |
| 104 | book_short_breakdown | +0.10% | +0.08% | -0.27% | -0.22% | -9.57% / -9.96% | NO |
| 107 | book_short_volume_fade | +0.01% | +0.01% | -0.01% | -0.03% | -9.66% / -10.04% | NO |
| 108 | baitoey_mjt_24_96_d | +0.01% | +0.48% | -5.05% | -5.82% | -10.32% / -10.05% | NO |
| 109 | book_short_shock_fade | +0.00% | +0.00% | -0.01% | -0.01% | -9.67% / -10.05% | NO |
| 110 | team_cash | -0.00% | -0.00% | -0.01% | -0.01% | -9.67% / -10.05% | NO |
| 112 | pol_mr_cap | +0.04% | -0.00% | -3.34% | -4.04% | -9.81% / -10.14% | NO |
| 113 | book_short_range_fail | -0.01% | -0.01% | -0.08% | -0.08% | -9.67% / -10.05% | NO |
| 114 | book_short_analogue6 | -0.02% | -0.03% | -0.04% | -0.05% | -9.69% / -10.08% | NO |
| 115 | book_short_ridge6 | -0.02% | -0.04% | -0.05% | -0.05% | -9.69% / -10.09% | NO |
| 116 | baitoey_btc_short_a2 | -0.04% | -0.04% | -1.07% | -1.08% | -9.71% / -10.10% | NO |
| 118 | book_bear_pullback | -0.08% | -0.07% | -0.29% | -0.29% | -9.77% / -10.14% | NO |
| 119 | book_short_analogue12 | -0.07% | -0.08% | -0.21% | -0.23% | -9.75% / -10.13% | NO |
| 120 | book_short_trend | -0.10% | -0.04% | -2.77% | -2.93% | -9.93% / -10.15% | NO |
| 121 | book_bear_breakdown | -0.12% | -0.09% | -0.47% | -0.50% | -9.80% / -10.15% | NO |
| 122 | book_short_rebound | -0.12% | -0.07% | -2.05% | -2.22% | -9.96% / -10.20% | NO |
| 123 | book_price_fast_signed | -0.14% | +0.35% | -3.62% | -3.69% | -10.01% / -9.85% | NO |
| 124 | book_bear_cost_guard | -0.14% | -0.12% | -0.46% | -0.47% | -9.83% / -10.19% | NO |
| 125 | book_bear_guard | -0.16% | -0.15% | -0.42% | -0.42% | -9.85% / -10.22% | NO |
| 126 | book_bear_trend_control | -0.16% | -0.12% | -0.63% | -0.74% | -9.84% / -10.17% | NO |
| 127 | baitoey_btc_short_c | -0.11% | -0.16% | -1.27% | -1.27% | -9.73% / -10.17% | NO |
| 128 | baitoey_mjt_06_24_6h | -0.16% | +0.35% | -5.04% | -5.65% | -9.98% / -9.83% | NO |
| 129 | book_bear_trail_exit | -0.20% | -0.18% | -0.56% | -0.62% | -9.90% / -10.26% | NO |
| 130 | book_bear_fast_exit | -0.25% | -0.25% | -0.53% | -0.59% | -9.94% / -10.32% | NO |
| 131 | baitoey_mr_bbrsi | -0.29% | -0.25% | -1.81% | -2.42% | -9.99% / -10.33% | NO |
| 132 | book_price_slow_short | -0.31% | -0.19% | -2.31% | -2.31% | -10.05% / -10.28% | NO |
| 133 | book_price_channel_signed | -0.38% | -0.01% | -3.49% | -3.43% | -10.18% / -10.13% | NO |
| 134 | book_price_fast_short | -0.51% | -0.34% | -2.20% | -2.38% | -10.20% / -10.39% | NO |
| 135 | book_price_channel_short | -0.64% | -0.54% | -2.54% | -2.99% | -10.26% / -10.53% | NO |

Research protocols and reading guide: /home/ubuntu/test/MiniMax/.worktrees/book-book-quality-recovery/research/book/quality_recovery/README.md
Original live bot and existing leaderboard_2 have not been changed.
