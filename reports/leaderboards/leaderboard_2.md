# Leaderboard 2: weak-market model selection

**Highest ranked originally eligible candidate: baitoey_ovl_brk_dual.** Its conservative selection score is -3.20%; its archive-profile mean 228-hour return is +2.94%.

**No candidate currently clears the stronger replacement-evidence checks.** The numeric ranks remain useful for choosing the next experiment. A rank alone does not establish that switching improves the live account.

## Read this first

The question answered here is: **which tested model performs most defensibly across historical weak-market checkpoints resembling this competition state, over the remaining 228 hours?** The main table now has explicit experimental ranks and comparisons against cash and the fixed e20 revision.

Market checkpoint: **2026-10-09 00:00:00+00:00**. Competition endpoint: **2026-10-18 12:00:00+00:00**. Main horizon: **228 h = 9.50 days**; robustness horizons: **216/228/240 h**. Historical tests start from cash at each selected checkpoint. They do not recreate the live account's holdings, pending orders, accrued activity or earlier loss.

1. Start with **Rank** and **Selection score**. Higher is better. The score is the smallest simultaneous lower return bound across both data profiles, all three horizons, and both cash/e20 comparisons (12 contrasts per model). It is a conservative evidence statistic; it is not expected profit.
2. Check **Original gates**. A model can have a high experimental rank while failing the team's original engineering/activity/compatibility gates. References and failed-gate models are visible for comparison.
3. Read **Mean 228h**, **Median**, **P10**, **Tail 10%**, **Worst**, **Cash wins** and **vs e20** together. A large average with severe bad tails is weaker evidence. Fresh BTC mean is a separate current-data sensitivity, not a substituted breadth observation.
4. Read the risk table. **CS** keeps the existing daily competition composite formula. **CS UTC** changes the day clock; **CS on positive windows** conditions on a positive after-cost return. That positive-window definition differs from the original leaderboard's return-bar CS_HIT.
5. Use the separate short table to inspect how many short onsets fired correctly at 1/3/6 hours, how often direction/costs defeated them, and how often a sampled profit was surrendered to a rebound. Its labels do not enter the main selection score.
6. A new model tested with **--score2** is automatically appended to this protocol's separate registry and the Markdown/CSV boards are regenerated. The market checkpoint and selection rules remain frozen.

A value of 0.02 in a CSV means +2%; the Markdown displays percentages. CS is a ratio composite, not a percentage. Missing/censored short labels appear explicitly and are excluded from valid-label precision, so inspect their counts alongside any accuracy percentage.

## Windows and data coverage

Weak historical eligibility is fixed before model comparisons: BTC's trailing 48-hour return lies between -10.00% and 0.00%, its 24-hour log return is at most 1.00%, and historical positive 48-hour breadth is at most 40.00%. Matching uses only information available at the historical checkpoint, never the following return.

The primary cohort requests 25 similar checkpoints, with at least 14 days between selected starts and at most 3 starts in any 90-day span. Only matured historical paths with the 24-hour embargo qualify. The saved cohort contains the actual admitted windows.

**Archive-full profile** uses a confirmed full-feature query at 2026-10-08 00:00:00+00:00, 24 hours before the current checkpoint. **Fresh-BTC profile** uses complete BTC features from ticker-assisted observations at the current checkpoint and deliberately declares its narrower feature set. It does not claim fresh full market breadth. The exact fresh broad-universe query remains **29/30 endpoints** because BCH is absent from competition ticker data; that failed coverage is preserved.

The previous October 8 adaptive forecast method did not pass all its evidence gates. Its failed activation record remains unchanged. This report ranks a separately declared conditional experiment; it does not silently enable that failed forecasting method or establish a validated downward forecast.

## Main ranked table

Mean/risk distribution columns use the archive-full cohort at 228 hours. The selection score uses the joint evidence across both profiles and all three horizons.

| Rank | Model | Original gates | Selection score | Mean 228h | Fresh BTC mean | Median | P10 | Tail 10% mean | Worst | Cash wins | Mean vs e20 | CS |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | baitoey_ovl_brk_dual | PASS | -3.20% | +2.94% | +2.40% | +3.63% | -8.35% | -11.35% | -15.67% | 64.0% | +2.20% | 0.23 |
| 2 | baitoey_vt_dual | PASS | -3.26% | +2.95% | +2.29% | +3.63% | -8.52% | -11.46% | -15.67% | 64.0% | +2.21% | 0.23 |
| 3 | book_cashshort_pullback | PASS | -3.38% | +2.76% | +2.19% | +3.18% | -8.35% | -11.38% | -15.67% | 64.0% | +2.02% | 0.23 |
| 4 | book_cashshort_confirm | PASS | -3.56% | +2.57% | +2.26% | +2.88% | -8.35% | -11.65% | -15.67% | 64.0% | +1.83% | 0.22 |
| 5 | book_vt_dual | PASS | -3.60% | +2.86% | +2.17% | +2.12% | -7.98% | -9.49% | -10.38% | 60.0% | +2.12% | 0.21 |
| 6 | baitoey_ovl_evtctl_dual | PASS | -3.66% | +2.63% | +2.08% | +2.93% | -8.49% | -11.48% | -15.40% | 60.0% | +1.89% | 0.20 |
| 7 | baitoey_ovl_evt_dual | PASS | -3.81% | +2.35% | +2.08% | +2.93% | -8.49% | -11.50% | -15.46% | 56.0% | +1.61% | 0.18 |
| 8 | book_vt_breadth | PASS | -3.90% | +2.22% | +1.21% | +1.08% | -7.32% | -7.64% | -7.99% | 56.0% | +1.48% | 0.14 |
| 9 | book_orch | PASS | -4.96% | +2.26% | +1.57% | +2.12% | -12.61% | -13.67% | -14.86% | 60.0% | +1.52% | 0.23 |
| 10 | pol_vt_mvr | PASS | -5.13% | +1.46% | +0.53% | +1.64% | -8.51% | -11.81% | -16.16% | 60.0% | +0.72% | 0.20 |
| 12 | book_transition_short | PASS | -5.30% | +1.32% | +0.93% | +1.61% | -8.50% | -12.00% | -15.01% | 56.0% | +0.58% | 0.12 |
| 13 | pol_combo_rt | PASS | -5.39% | +0.33% | +0.75% | -0.42% | -8.12% | -10.82% | -13.61% | 44.0% | -0.42% | 0.10 |
| 14 | pol_combo_rb | PASS | -5.57% | +1.30% | +0.92% | +1.39% | -9.43% | -13.49% | -19.02% | 64.0% | +0.56% | 0.18 |
| 15 | team_rot_iv | PASS | -5.59% | +0.72% | +0.98% | +1.23% | -9.18% | -10.75% | -12.88% | 56.0% | -0.02% | 0.13 |
| 16 | baitoey_vt_mom | PASS | -5.59% | +2.00% | +1.28% | +2.12% | -13.22% | -15.01% | -17.48% | 60.0% | +1.26% | 0.21 |
| 17 | pol_combo_rtt | PASS | -5.61% | +0.40% | +0.75% | +0.23% | -7.67% | -11.77% | -16.49% | 56.0% | -0.34% | 0.12 |
| 18 | baitoey_ovl_altbtc_a_dual | PASS | -5.77% | +1.70% | +1.53% | +0.95% | -7.45% | -11.01% | -15.47% | 60.0% | +0.96% | 0.21 |
| 19 | baitoey_e20_out10 | PASS | -5.80% | +0.43% | +0.88% | -2.16% | -8.35% | -10.76% | -11.75% | 36.0% | -0.31% | 0.08 |
| 20 | pol_combo_all | PASS | -5.80% | +0.58% | +0.41% | +1.15% | -7.88% | -11.40% | -16.33% | 60.0% | -0.16% | 0.14 |
| 21 | baitoey_e20_out15 | PASS | -5.83% | +0.27% | +0.77% | -2.23% | -8.35% | -10.76% | -11.75% | 36.0% | -0.47% | 0.07 |
| 22 | baitoey_ovl_altbtc_b_e20 | PASS | -5.91% | +0.66% | +0.94% | -0.89% | -10.38% | -11.29% | -12.14% | 44.0% | -0.08% | 0.12 |
| 23 | baitoey_ovl_altbtc_b_dual | PASS | -6.15% | +1.49% | +1.15% | +0.04% | -6.85% | -10.37% | -15.58% | 52.0% | +0.75% | 0.29 |
| 24 | book_vt_top4 | PASS | -6.16% | +2.12% | +1.74% | +0.70% | -13.57% | -14.55% | -15.80% | 60.0% | +1.38% | 0.21 |
| 25 | pol_abl_shock | PASS | -6.16% | +1.44% | +0.95% | +2.12% | -13.22% | -15.10% | -17.71% | 60.0% | +0.70% | 0.20 |
| 26 | book_e20combo_alt_cash_pb | PASS | -6.19% | +0.60% | +0.98% | -0.89% | -10.38% | -11.29% | -12.14% | 44.0% | -0.14% | 0.12 |
| 27 | book_e20combo_alt_trim | PASS | -6.20% | +0.50% | +0.89% | -1.04% | -10.38% | -11.29% | -12.14% | 44.0% | -0.24% | 0.10 |
| 28 | pol_switch_vtm_tl | PASS | -6.20% | +0.51% | -0.05% | +0.97% | -9.54% | -13.41% | -15.10% | 52.0% | -0.23% | 0.14 |
| 29 | team_btc_hold | PASS | -6.23% | +1.42% | +0.67% | +2.65% | -6.71% | -13.01% | -19.90% | 60.0% | +0.68% | 0.22 |
| 30 | book_e20combo_alt_half_cash | PASS | -6.24% | +0.50% | +0.89% | -2.57% | -9.62% | -11.82% | -13.62% | 36.0% | -0.24% | 0.07 |
| 31 | book_e20combo_alt_cash | PASS | -6.25% | +0.58% | +1.09% | -1.09% | -10.38% | -11.29% | -12.14% | 44.0% | -0.16% | 0.11 |
| 32 | pol_switch_rc | PASS | -6.29% | +0.77% | +0.42% | +0.00% | -12.39% | -15.16% | -16.78% | 52.0% | +0.03% | 0.08 |
| 33 | book_coin_trend | PASS | -6.33% | +0.61% | +0.26% | +0.21% | -4.81% | -7.72% | -11.34% | 52.0% | -0.13% | 0.09 |
| 34 | team_trend_2 | PASS | -6.46% | +0.51% | +0.49% | +0.64% | -8.91% | -12.19% | -14.43% | 52.0% | -0.23% | 0.15 |
| 35 | baitoey_e20_btcs_b2 | PASS | -6.60% | +0.16% | -0.19% | -2.03% | -10.62% | -12.97% | -14.08% | 44.0% | -0.58% | 0.11 |
| 36 | baitoey_e20_shortc_sol | PASS | -6.74% | +1.43% | +1.09% | -2.23% | -10.46% | -14.27% | -15.25% | 48.0% | +0.69% | 0.14 |
| 37 | team_rot_ew | PASS | -6.80% | +1.20% | +1.33% | +1.34% | -14.15% | -16.22% | -19.14% | 56.0% | +0.46% | 0.12 |
| 38 | baitoey_ovl_altbtc_a_e20 | PASS | -6.85% | +0.68% | +1.57% | -2.65% | -9.56% | -11.91% | -12.66% | 40.0% | -0.06% | 0.09 |
| 39 | pol_switch_vt_tl | PASS | -6.91% | +0.77% | +0.36% | +0.40% | -13.42% | -14.19% | -15.10% | 52.0% | +0.03% | 0.14 |
| 40 | baitoey_ovl_brk_e20 | PASS | -6.93% | +1.06% | +0.78% | -2.88% | -11.23% | -12.30% | -13.38% | 44.0% | +0.32% | 0.13 |
| 41 | book_e20combo_brk_cash | PASS | -6.98% | +1.05% | +0.89% | -2.88% | -11.75% | -12.48% | -13.38% | 44.0% | +0.30% | 0.13 |
| 42 | pol_switch3_cap | PASS | -6.98% | +0.86% | -0.39% | +0.04% | -8.15% | -12.31% | -17.48% | 56.0% | +0.12% | 0.37 |
| 43 | baitoey_e20_btcs_a2 | PASS | -7.05% | +0.33% | +0.24% | -2.23% | -10.19% | -12.54% | -16.05% | 40.0% | -0.41% | 0.08 |
| 44 | pol_switch_rt | PASS | -7.07% | +0.13% | +0.05% | -0.96% | -14.31% | -14.74% | -14.91% | 48.0% | -0.61% | 0.06 |
| 45 | baitoey_e20_shortc_alts | PASS | -7.13% | +0.85% | +0.79% | -2.35% | -10.21% | -14.12% | -15.20% | 44.0% | +0.11% | 0.12 |
| 46 | baitoey_e20_btcs_c | PASS | -7.19% | +0.84% | +0.59% | -2.23% | -10.05% | -13.74% | -15.20% | 44.0% | +0.10% | 0.13 |
| 47 | book_e20guard_confirm | PASS | -7.21% | +0.49% | +0.64% | -2.88% | -11.75% | -14.43% | -15.11% | 44.0% | -0.25% | 0.11 |
| 48 | book_e20guard_pullback | PASS | -7.31% | +0.56% | +0.65% | -2.88% | -11.75% | -14.36% | -15.11% | 44.0% | -0.18% | 0.11 |
| 49 | pol_switch_vt_tl_e20v45 | PASS | -7.42% | +0.74% | +0.58% | -2.88% | -11.75% | -14.48% | -15.20% | 44.0% | +0.00% | 0.12 |
| 50 | pol_switch3 | PASS | -7.42% | +1.11% | -0.56% | +0.07% | -8.15% | -12.00% | -16.69% | 52.0% | +0.36% | 0.28 |
| 51 | baitoey_ovl_evt_e20 | PASS | -7.44% | +0.79% | +0.56% | -2.88% | -12.17% | -14.42% | -15.20% | 40.0% | +0.05% | 0.12 |
| 52 | baitoey_e20_shortc_eth | PASS | -7.44% | +0.77% | +0.46% | -2.61% | -10.96% | -15.20% | -17.31% | 44.0% | +0.03% | 0.13 |
| 54 | baitoey_ovl_evtctl_e20 | PASS | -7.48% | +0.70% | +0.42% | -2.88% | -11.71% | -14.52% | -15.25% | 44.0% | -0.04% | 0.13 |
| 55 | pol_mom_ss | PASS | -7.50% | +0.58% | +0.10% | -0.39% | -5.94% | -6.28% | -6.55% | 48.0% | -0.16% | 0.16 |
| 56 | team_mom_ss25 | PASS | -7.50% | +0.58% | +0.10% | -0.39% | -5.94% | -6.28% | -6.55% | 48.0% | -0.16% | 0.16 |
| 57 | pol_combo_ms_tl | PASS | -7.55% | -0.17% | +0.12% | -1.31% | -5.44% | -6.13% | -6.94% | 44.0% | -0.91% | 0.10 |
| 58 | pol_switch_rot_mr | PASS | -7.65% | +0.56% | +0.57% | -0.23% | -13.48% | -14.00% | -14.55% | 48.0% | -0.18% | 0.08 |
| 59 | baitoey_e20_btcs_a | PASS | -7.71% | +0.54% | +0.37% | -2.88% | -13.90% | -14.51% | -15.20% | 44.0% | -0.20% | 0.12 |
| 60 | baitoey_e20_btcs_d | PASS | -7.71% | +0.54% | +0.37% | -2.88% | -13.90% | -14.51% | -15.20% | 44.0% | -0.20% | 0.12 |
| 61 | baitoey_rot_max | PASS | -7.92% | +2.84% | +2.68% | +0.39% | -16.76% | -18.93% | -22.13% | 52.0% | +2.10% | 0.16 |
| 62 | baitoey_e20_btcs_b | PASS | -8.02% | +0.31% | +0.51% | -2.23% | -14.12% | -14.58% | -15.20% | 44.0% | -0.43% | 0.12 |
| 63 | pol_trend_ls | PASS | -8.02% | -0.76% | +0.14% | -1.66% | -7.81% | -9.60% | -11.70% | 40.0% | -1.50% | 0.07 |
| 64 | baitoey_mr_4h | PASS | -8.51% | -0.27% | -0.91% | +0.07% | -7.54% | -11.16% | -16.04% | 52.0% | -1.01% | 0.11 |
| 65 | pol_switch_rmax_mr | PASS | -8.94% | +1.32% | +0.81% | -1.81% | -16.21% | -16.38% | -16.47% | 48.0% | +0.57% | 0.06 |
| 66 | pol_switch_rmax_tl | PASS | -9.25% | +1.75% | +1.88% | -1.55% | -16.76% | -18.12% | -20.11% | 44.0% | +1.01% | 0.09 |
| 67 | team_ew_daily | PASS | -9.28% | +0.51% | -0.83% | +1.09% | -15.01% | -20.06% | -25.17% | 56.0% | -0.24% | 0.14 |
| 68 | baitoey_tg_mom | PASS | -9.45% | +0.24% | +0.15% | -0.04% | -1.96% | -2.88% | -3.86% | 48.0% | -0.50% | 0.05 |
| 69 | pol_mr_cap | PASS | -9.91% | -0.99% | -1.29% | +0.02% | -8.09% | -13.66% | -19.47% | 52.0% | -1.73% | 0.13 |
| 70 | team_cash | PASS | -10.02% | -0.00% | -0.00% | +0.00% | -0.01% | -0.02% | -0.02% | 52.0% | -0.74% | -0.00 |
| 71 | book_short_breakdown | PASS | -10.02% | +0.37% | +0.62% | -0.00% | -0.24% | -0.61% | -0.84% | 24.0% | -0.37% | 0.04 |
| 72 | book_short_shock_fade | PASS | -10.02% | +0.02% | +0.01% | -0.00% | -0.06% | -0.11% | -0.15% | 28.0% | -0.72% | 0.01 |
| 73 | book_short_ridge6 | PASS | -10.03% | -0.01% | -0.03% | -0.00% | -0.02% | -0.15% | -0.29% | 12.0% | -0.76% | -0.01 |
| 74 | book_short_volume_fade | PASS | -10.03% | +0.00% | +0.01% | -0.00% | -0.13% | -0.19% | -0.23% | 32.0% | -0.74% | 0.00 |
| 75 | book_short_range_fail | PASS | -10.04% | +0.00% | +0.00% | -0.00% | -0.17% | -0.20% | -0.22% | 36.0% | -0.74% | -0.00 |
| 76 | book_short_analogue6 | PASS | -10.04% | -0.07% | -0.07% | -0.01% | -0.21% | -0.59% | -1.15% | 28.0% | -0.81% | -0.03 |
| 77 | book_short_analogue12 | PASS | -10.09% | -0.08% | -0.09% | -0.05% | -0.27% | -0.47% | -0.59% | 24.0% | -0.82% | -0.05 |
| 78 | baitoey_btc_short_a | PASS | -10.15% | -0.14% | +0.12% | -0.00% | -0.01% | -1.61% | -2.13% | 12.0% | -0.88% | -0.02 |
| 79 | baitoey_btc_short_d | PASS | -10.15% | -0.14% | +0.12% | -0.00% | -0.01% | -1.61% | -2.13% | 12.0% | -0.88% | -0.02 |
| 80 | book_bear_pullback | PASS | -10.23% | -0.11% | -0.04% | -0.10% | -0.36% | -0.52% | -0.60% | 8.0% | -0.85% | -0.09 |
| 81 | baitoey_mr_bbrsi | PASS | -10.25% | -0.26% | -0.87% | +0.00% | -3.32% | -5.71% | -8.92% | 52.0% | -1.00% | 0.08 |
| 82 | book_bear_breakdown | PASS | -10.30% | -0.09% | -0.00% | -0.13% | -0.56% | -0.66% | -0.78% | 28.0% | -0.83% | -0.08 |
| 83 | book_bear_cost_guard | PASS | -10.34% | -0.20% | -0.09% | -0.24% | -0.48% | -0.62% | -0.76% | 20.0% | -0.94% | -0.13 |
| 85 | book_bear_trail_exit | PASS | -10.37% | -0.31% | -0.17% | -0.26% | -0.67% | -1.15% | -1.80% | 12.0% | -1.05% | -0.17 |
| 86 | book_bear_guard | PASS | -10.38% | -0.26% | -0.13% | -0.30% | -0.64% | -0.73% | -0.86% | 12.0% | -1.00% | -0.17 |
| 87 | baitoey_btc_short_c | PASS | -10.45% | -0.19% | -0.20% | -0.00% | -1.96% | -2.94% | -4.26% | 28.0% | -0.93% | -0.01 |
| 88 | baitoey_btc_short_b | PASS | -10.46% | -0.53% | +0.08% | -0.01% | -2.07% | -2.24% | -2.45% | 16.0% | -1.27% | -0.07 |
| 89 | book_bear_fast_exit | PASS | -10.47% | -0.50% | -0.41% | -0.41% | -0.95% | -1.34% | -1.92% | 0.0% | -1.24% | -0.26 |
| 90 | book_bear_trend_control | PASS | -10.54% | -0.17% | +0.03% | -0.17% | -0.88% | -1.03% | -1.19% | 36.0% | -0.91% | -0.13 |
| 91 | baitoey_btc_short_a2 | PASS | -10.64% | -0.12% | +0.09% | -0.01% | -2.07% | -2.38% | -2.75% | 24.0% | -0.86% | -0.01 |
| 92 | baitoey_mjt_12_48_d | PASS | -10.66% | +1.00% | +0.32% | -0.31% | -4.25% | -6.63% | -7.99% | 40.0% | +0.26% | 0.06 |
| 93 | baitoey_btc_short_b2 | PASS | -10.68% | -0.08% | +0.02% | -0.00% | -2.45% | -2.76% | -2.97% | 40.0% | -0.82% | 0.02 |
| 94 | baitoey_mjt_24_96_d | PASS | -10.70% | +0.62% | +0.56% | -0.38% | -7.17% | -8.88% | -10.44% | 48.0% | -0.12% | 0.03 |
| 95 | baitoey_mjt_06_24_d | PASS | -10.73% | +0.54% | +1.08% | -0.08% | -5.11% | -7.17% | -7.82% | 48.0% | -0.20% | 0.05 |
| 98 | book_price_fast_signed | PASS | -10.95% | -0.02% | +0.08% | -0.80% | -3.42% | -4.18% | -5.02% | 40.0% | -0.76% | 0.03 |
| 100 | book_daily_channel | PASS | -10.96% | -0.04% | +0.27% | -0.01% | -5.05% | -7.51% | -9.97% | 44.0% | -0.78% | 0.02 |
| 103 | book_short_trend | PASS | -11.35% | -0.24% | +0.05% | -0.42% | -3.90% | -4.06% | -4.17% | 44.0% | -0.98% | 0.02 |
| 104 | book_price_channel_signed | PASS | -11.40% | -0.72% | -0.42% | -1.25% | -3.83% | -4.96% | -5.56% | 44.0% | -1.46% | -0.05 |
| 106 | book_short_rebound | PASS | -11.49% | -0.31% | +0.07% | -0.14% | -4.12% | -4.69% | -5.38% | 44.0% | -1.05% | 0.02 |
| 107 | book_price_slow_signed | PASS | -11.55% | -0.35% | -0.22% | -1.66% | -5.19% | -5.85% | -6.28% | 40.0% | -1.09% | 0.00 |
| 109 | book_price_fast_short | PASS | -11.81% | -0.42% | +0.18% | -1.06% | -3.19% | -3.36% | -3.59% | 40.0% | -1.16% | -0.09 |
| 113 | baitoey_mjt_24_96_6h | PASS | -11.90% | +0.89% | +0.73% | -0.41% | -6.58% | -9.18% | -10.25% | 48.0% | +0.15% | 0.06 |
| 115 | book_price_channel_short | PASS | -12.23% | -0.75% | +0.02% | -0.72% | -3.78% | -4.01% | -4.32% | 36.0% | -1.49% | -0.14 |
| 117 | book_price_slow_short | PASS | -12.31% | -0.79% | -0.46% | -1.09% | -3.17% | -4.22% | -5.35% | 24.0% | -1.53% | -0.13 |
| 118 | baitoey_mjt_12_48_6h | PASS | -12.47% | -0.10% | +0.45% | -1.46% | -6.18% | -9.49% | -11.12% | 44.0% | -0.84% | -0.01 |
| 119 | baitoey_mjt_06_24_6h | PASS | -12.49% | -0.21% | +0.15% | -1.05% | -6.38% | -9.35% | -11.42% | 40.0% | -0.95% | 0.02 |

Fixed incumbent: **pol_switch_vt_tl_e20v45**. Cash is the zero-return comparator. The incumbent's cached revision stays fixed even if a new run reuses its model name. All model returns include the existing cached trading fees, spread assumptions and execution lag; an endpoint liquidation fee is applied once. Results begin from cash and measure an experimental replacement strategy, not a transaction from incumbent holdings.

## Risk and original-gate detail

| Model | Role | Mean MDD | Worst MDD | CS | CS UTC | CS on positive windows | Stronger evidence | Failed original hard gates |
|---|---|---|---|---|---|---|---|---|
| baitoey_ovl_brk_dual | candidate | 7.75% | 17.65% | 0.23 | 0.18 | 0.48 | NO | — |
| baitoey_vt_dual | candidate | 7.74% | 17.65% | 0.23 | 0.18 | 0.48 | NO | — |
| book_cashshort_pullback | candidate | 7.80% | 17.65% | 0.23 | 0.17 | 0.47 | NO | — |
| book_cashshort_confirm | candidate | 7.85% | 17.65% | 0.22 | 0.17 | 0.47 | NO | — |
| book_vt_dual | candidate | 7.86% | 16.14% | 0.21 | 0.16 | 0.49 | NO | — |
| baitoey_ovl_evtctl_dual | candidate | 8.02% | 17.51% | 0.20 | 0.15 | 0.47 | NO | — |
| baitoey_ovl_evt_dual | candidate | 7.77% | 17.50% | 0.18 | 0.14 | 0.48 | NO | — |
| book_vt_breadth | candidate | 7.24% | 15.63% | 0.14 | 0.12 | 0.43 | NO | — |
| book_orch | candidate | 9.54% | 19.64% | 0.23 | 0.17 | 0.51 | NO | — |
| pol_vt_mvr | candidate | 8.72% | 22.89% | 0.20 | 0.15 | 0.48 | NO | — |
| book_transition_short | candidate | 7.61% | 17.01% | 0.12 | 0.08 | 0.42 | NO | — |
| pol_combo_rt | candidate | 6.98% | 20.01% | 0.10 | 0.17 | 0.47 | NO | — |
| pol_combo_rb | candidate | 8.22% | 24.87% | 0.18 | 0.18 | 0.41 | NO | — |
| team_rot_iv | reference | 7.39% | 18.72% | 0.13 | 0.16 | 0.38 | NO | — |
| baitoey_vt_mom | candidate | 9.81% | 22.89% | 0.21 | 0.17 | 0.49 | NO | — |
| pol_combo_rtt | candidate | 6.67% | 21.03% | 0.12 | 0.15 | 0.39 | NO | — |
| baitoey_ovl_altbtc_a_dual | candidate | 6.75% | 17.50% | 0.21 | 0.17 | 0.49 | NO | — |
| baitoey_e20_out10 | candidate | 9.39% | 18.48% | 0.08 | 0.05 | 0.55 | NO | — |
| pol_combo_all | candidate | 6.82% | 20.91% | 0.14 | 0.17 | 0.38 | NO | — |
| baitoey_e20_out15 | candidate | 9.42% | 18.48% | 0.07 | 0.04 | 0.55 | NO | — |
| baitoey_ovl_altbtc_b_e20 | candidate | 7.47% | 18.29% | 0.12 | 0.05 | 0.60 | NO | — |
| baitoey_ovl_altbtc_b_dual | candidate | 5.39% | 17.49% | 0.29 | 0.20 | 0.74 | NO | — |
| book_vt_top4 | candidate | 9.95% | 22.55% | 0.21 | 0.19 | 0.49 | NO | — |
| pol_abl_shock | candidate | 10.04% | 21.74% | 0.20 | 0.15 | 0.48 | NO | — |
| book_e20combo_alt_cash_pb | candidate | 7.54% | 18.29% | 0.12 | 0.04 | 0.60 | NO | — |
| book_e20combo_alt_trim | candidate | 7.40% | 18.29% | 0.10 | 0.04 | 0.60 | NO | — |
| pol_switch_vtm_tl | candidate | 8.54% | 20.98% | 0.14 | 0.08 | 0.51 | NO | — |
| team_btc_hold | reference | 6.73% | 24.44% | 0.22 | 0.22 | 0.49 | NO | — |
| book_e20combo_alt_half_cash | candidate | 8.63% | 17.94% | 0.07 | 0.01 | 0.67 | NO | — |
| book_e20combo_alt_cash | candidate | 7.58% | 18.29% | 0.11 | 0.04 | 0.61 | NO | — |
| pol_switch_rc | candidate | 9.44% | 18.65% | 0.08 | 0.09 | 0.35 | NO | — |
| book_coin_trend | candidate | 5.41% | 13.40% | 0.09 | 0.17 | 0.38 | NO | — |
| team_trend_2 | reference | 6.45% | 15.65% | 0.15 | 0.16 | 0.45 | NO | — |
| baitoey_e20_btcs_b2 | candidate | 9.54% | 18.18% | 0.11 | 0.03 | 0.58 | NO | — |
| baitoey_e20_shortc_sol | candidate | 10.54% | 20.35% | 0.14 | 0.07 | 0.60 | NO | — |
| team_rot_ew | reference | 10.62% | 26.80% | 0.12 | 0.15 | 0.39 | NO | — |
| baitoey_ovl_altbtc_a_e20 | candidate | 8.72% | 17.53% | 0.09 | 0.05 | 0.62 | NO | — |
| pol_switch_vt_tl | candidate | 9.61% | 20.98% | 0.14 | 0.09 | 0.50 | NO | — |
| baitoey_ovl_brk_e20 | candidate | 10.14% | 18.48% | 0.13 | 0.05 | 0.62 | NO | — |
| book_e20combo_brk_cash | candidate | 10.16% | 18.48% | 0.13 | 0.05 | 0.62 | NO | — |
| pol_switch3_cap | candidate | 5.94% | 29.59% | 0.37 | 0.28 | 0.80 | NO | — |
| baitoey_e20_btcs_a2 | candidate | 9.99% | 19.49% | 0.08 | 0.02 | 0.59 | NO | — |
| pol_switch_rt | candidate | 10.16% | 20.77% | 0.06 | 0.07 | 0.37 | NO | — |
| baitoey_e20_shortc_alts | candidate | 10.38% | 19.75% | 0.12 | 0.06 | 0.63 | NO | — |
| baitoey_e20_btcs_c | candidate | 10.30% | 18.48% | 0.13 | 0.05 | 0.63 | NO | — |
| book_e20guard_confirm | candidate | 10.23% | 18.48% | 0.11 | 0.04 | 0.59 | NO | — |
| book_e20guard_pullback | candidate | 10.44% | 18.48% | 0.11 | 0.05 | 0.59 | NO | — |
| pol_switch_vt_tl_e20v45 | candidate | 10.50% | 18.48% | 0.12 | 0.05 | 0.62 | NO | — |
| pol_switch3 | candidate | 6.80% | 30.64% | 0.28 | 0.21 | 0.70 | NO | — |
| baitoey_ovl_evt_e20 | candidate | 10.13% | 18.09% | 0.12 | 0.05 | 0.67 | NO | — |
| baitoey_e20_shortc_eth | candidate | 10.31% | 19.17% | 0.13 | 0.05 | 0.63 | NO | — |
| baitoey_ovl_evtctl_e20 | candidate | 10.51% | 18.48% | 0.13 | 0.05 | 0.63 | NO | — |
| pol_mom_ss | candidate | 4.35% | 11.33% | 0.16 | 0.13 | 0.52 | NO | — |
| team_mom_ss25 | reference | 4.35% | 11.33% | 0.16 | 0.13 | 0.52 | NO | — |
| pol_combo_ms_tl | candidate | 4.69% | 11.11% | 0.10 | 0.12 | 0.49 | NO | — |
| pol_switch_rot_mr | candidate | 10.06% | 25.46% | 0.08 | 0.11 | 0.42 | NO | — |
| baitoey_e20_btcs_a | candidate | 10.56% | 18.48% | 0.12 | 0.04 | 0.63 | NO | — |
| baitoey_e20_btcs_d | candidate | 10.56% | 18.48% | 0.12 | 0.04 | 0.63 | NO | — |
| baitoey_rot_max | candidate | 12.77% | 31.80% | 0.16 | 0.18 | 0.46 | NO | — |
| baitoey_e20_btcs_b | candidate | 10.72% | 19.49% | 0.12 | 0.04 | 0.63 | NO | — |
| pol_trend_ls | candidate | 6.14% | 17.06% | 0.07 | 0.11 | 0.52 | NO | — |
| baitoey_mr_4h | candidate | 6.18% | 30.06% | 0.11 | 0.17 | 0.37 | NO | — |
| pol_switch_rmax_mr | candidate | 11.87% | 27.99% | 0.06 | 0.08 | 0.39 | NO | — |
| pol_switch_rmax_tl | candidate | 12.00% | 26.22% | 0.09 | 0.10 | 0.50 | NO | — |
| team_ew_daily | reference | 11.48% | 31.65% | 0.14 | 0.21 | 0.40 | NO | — |
| baitoey_tg_mom | candidate | 2.52% | 4.60% | 0.05 | 0.09 | 0.33 | NO | — |
| pol_mr_cap | candidate | 5.28% | 29.31% | 0.13 | 0.21 | 0.42 | NO | — |
| team_cash | reference | 0.01% | 0.02% | -0.00 | -0.00 | 0.00 | NO | — |
| book_short_breakdown | candidate | 0.59% | 3.46% | 0.04 | 0.01 | 0.34 | NO | — |
| book_short_shock_fade | candidate | 0.04% | 0.18% | 0.01 | 0.01 | 0.10 | NO | — |
| book_short_ridge6 | candidate | 0.05% | 0.87% | -0.01 | -0.01 | 0.03 | NO | — |
| book_short_volume_fade | candidate | 0.07% | 0.28% | 0.00 | 0.00 | 0.08 | NO | — |
| book_short_range_fail | candidate | 0.08% | 0.38% | -0.00 | 0.00 | 0.07 | NO | — |
| book_short_analogue6 | candidate | 0.11% | 1.29% | -0.03 | -0.03 | 0.05 | NO | — |
| book_short_analogue12 | candidate | 0.16% | 0.81% | -0.05 | -0.06 | 0.06 | NO | — |
| baitoey_btc_short_a | candidate | 0.46% | 5.60% | -0.02 | -0.02 | 0.05 | NO | — |
| baitoey_btc_short_d | candidate | 0.46% | 5.60% | -0.02 | -0.02 | 0.05 | NO | — |
| book_bear_pullback | candidate | 0.34% | 1.00% | -0.09 | -0.11 | 0.38 | NO | — |
| baitoey_mr_bbrsi | candidate | 2.89% | 14.59% | 0.08 | 0.08 | 0.21 | NO | — |
| book_bear_breakdown | candidate | 0.46% | 1.26% | -0.08 | -0.10 | 0.20 | NO | — |
| book_bear_cost_guard | candidate | 0.54% | 1.70% | -0.13 | -0.14 | 0.11 | NO | — |
| book_bear_trail_exit | candidate | 0.58% | 2.16% | -0.17 | -0.18 | 0.15 | NO | — |
| book_bear_guard | candidate | 0.59% | 1.68% | -0.17 | -0.17 | 0.11 | NO | — |
| baitoey_btc_short_c | candidate | 1.30% | 5.48% | -0.01 | -0.05 | 0.25 | NO | — |
| baitoey_btc_short_b | candidate | 1.10% | 5.60% | -0.07 | -0.08 | 0.08 | NO | — |
| book_bear_fast_exit | candidate | 0.64% | 2.35% | -0.26 | -0.28 | — | NO | — |
| book_bear_trend_control | candidate | 0.81% | 1.97% | -0.13 | -0.15 | 0.17 | NO | — |
| baitoey_btc_short_a2 | candidate | 1.47% | 5.48% | -0.01 | -0.05 | 0.41 | NO | — |
| baitoey_mjt_12_48_d | candidate | 6.77% | 14.42% | 0.06 | 0.06 | 0.34 | NO | — |
| baitoey_btc_short_b2 | candidate | 1.45% | 5.48% | 0.02 | -0.01 | 0.22 | NO | — |
| baitoey_mjt_24_96_d | candidate | 6.93% | 14.42% | 0.03 | 0.12 | 0.33 | NO | — |
| baitoey_mjt_06_24_d | candidate | 7.23% | 18.87% | 0.05 | 0.04 | 0.31 | NO | — |
| book_price_fast_signed | candidate | 4.05% | 7.41% | 0.03 | -0.00 | 0.38 | NO | — |
| book_daily_channel | candidate | 5.16% | 11.56% | 0.02 | 0.01 | 0.22 | NO | — |
| book_short_trend | candidate | 2.98% | 4.59% | 0.02 | 0.06 | 0.42 | NO | — |
| book_price_channel_signed | candidate | 4.70% | 9.23% | -0.05 | -0.05 | 0.19 | NO | — |
| book_short_rebound | candidate | 2.98% | 6.18% | 0.02 | 0.05 | 0.41 | NO | — |
| book_price_slow_signed | candidate | 4.82% | 7.99% | 0.00 | 0.04 | 0.41 | NO | — |
| book_price_fast_short | candidate | 2.97% | 4.99% | -0.09 | -0.10 | 0.23 | NO | — |
| baitoey_mjt_24_96_6h | candidate | 7.08% | 13.83% | 0.06 | 0.09 | 0.36 | NO | — |
| book_price_channel_short | candidate | 3.49% | 5.77% | -0.14 | -0.15 | 0.18 | NO | — |
| book_price_slow_short | candidate | 3.66% | 5.71% | -0.13 | -0.13 | 0.22 | NO | — |
| baitoey_mjt_12_48_6h | candidate | 6.83% | 15.98% | -0.01 | -0.02 | 0.24 | NO | — |
| baitoey_mjt_06_24_6h | candidate | 6.83% | 19.19% | 0.02 | 0.00 | 0.36 | NO | — |

MDD is a positive loss fraction from a prior equity peak and includes terminal liquidation. CS = 0.4 Sortino + 0.3 Sharpe + 0.3 Calmar using the configured FLOORED.V1 daily-raw formulas, with the same handling of partial first/last days as the original scorer. A favourable CS cannot replace the return and downside checks.

## Separate stress/control tables

The following-down and following-rebound subsets are **ex-post scenarios**. They classify the following 240-hour BTC outcome using the frozen down/rebound thresholds, then report the model's 228-hour return. Their different horizons are intentional and must not be read as exact same-horizon market attribution. Their future labels are never used to admit the main lookalikes.

Down stress: BTC's following 240-hour return <= -2.00%. Rebound stress: >= 2.00%. Positive control checkpoints are selected from the separately predeclared positive pre-window state, so they test the cost of a short/defensive model when market conditions improve.

| Model | Down N | Down mean | Rebound N | Rebound mean | Positive-control N | Positive-control mean |
|---|---|---|---|---|---|---|
| baitoey_ovl_brk_dual | 7 | -3.27% | 13 | +6.73% | 25 | +2.70% |
| baitoey_vt_dual | 7 | -3.28% | 13 | +6.73% | 25 | +2.70% |
| book_cashshort_pullback | 7 | -3.50% | 13 | +6.56% | 25 | +2.68% |
| book_cashshort_confirm | 7 | -3.83% | 13 | +6.38% | 25 | +2.70% |
| book_vt_dual | 7 | -3.48% | 13 | +6.89% | 25 | +2.75% |
| baitoey_ovl_evtctl_dual | 7 | -4.38% | 13 | +6.69% | 25 | +2.48% |
| baitoey_ovl_evt_dual | 7 | -4.76% | 13 | +6.36% | 25 | +2.56% |
| book_vt_breadth | 7 | -3.10% | 13 | +5.98% | 25 | +2.55% |
| book_orch | 7 | -7.04% | 13 | +7.34% | 25 | +2.97% |
| pol_vt_mvr | 7 | -5.99% | 13 | +5.97% | 25 | +2.87% |
| book_transition_short | 7 | -5.59% | 13 | +5.21% | 25 | +1.94% |
| pol_combo_rt | 7 | -5.68% | 13 | +3.68% | 25 | +1.91% |
| pol_combo_rb | 7 | -8.28% | 13 | +6.75% | 25 | +3.03% |
| team_rot_iv | 7 | -6.67% | 13 | +4.83% | 25 | +1.80% |
| baitoey_vt_mom | 7 | -7.89% | 13 | +7.41% | 25 | +2.98% |
| pol_combo_rtt | 7 | -6.66% | 13 | +4.40% | 25 | +2.20% |
| baitoey_ovl_altbtc_a_dual | 7 | -4.75% | 13 | +6.06% | 25 | +2.19% |
| baitoey_e20_out10 | 7 | -6.43% | 13 | +4.62% | 25 | +2.93% |
| pol_combo_all | 7 | -6.87% | 13 | +4.67% | 25 | +2.00% |
| baitoey_e20_out15 | 7 | -6.65% | 13 | +4.44% | 25 | +2.78% |
| baitoey_ovl_altbtc_b_e20 | 7 | -4.34% | 13 | +4.13% | 25 | +0.45% |
| baitoey_ovl_altbtc_b_dual | 7 | -3.06% | 13 | +4.48% | 25 | +0.68% |
| book_vt_top4 | 7 | -8.35% | 13 | +8.13% | 25 | +2.67% |
| pol_abl_shock | 7 | -8.79% | 13 | +7.07% | 25 | +2.34% |
| book_e20combo_alt_cash_pb | 7 | -4.25% | 13 | +4.06% | 25 | +0.48% |
| book_e20combo_alt_trim | 7 | -4.20% | 13 | +3.80% | 25 | +0.48% |
| pol_switch_vtm_tl | 7 | -7.65% | 13 | +5.43% | 25 | +2.62% |
| team_btc_hold | 7 | -7.77% | 13 | +6.96% | 25 | +3.69% |
| book_e20combo_alt_half_cash | 7 | -7.27% | 13 | +5.27% | 25 | +1.60% |
| book_e20combo_alt_cash | 7 | -4.31% | 13 | +4.08% | 25 | +0.47% |
| pol_switch_rc | 7 | -8.86% | 13 | +6.02% | 25 | +2.37% |
| book_coin_trend | 7 | -4.78% | 13 | +3.77% | 25 | +1.18% |
| team_trend_2 | 7 | -7.76% | 13 | +5.31% | 25 | +2.76% |
| baitoey_e20_btcs_b2 | 7 | -8.92% | 13 | +4.88% | 25 | +1.89% |
| baitoey_e20_shortc_sol | 7 | -6.82% | 13 | +6.11% | 25 | +2.56% |
| team_rot_ew | 7 | -9.23% | 13 | +6.98% | 25 | +1.68% |
| baitoey_ovl_altbtc_a_e20 | 7 | -7.65% | 13 | +5.87% | 25 | +2.58% |
| pol_switch_vt_tl | 7 | -9.60% | 13 | +6.35% | 25 | +2.50% |
| baitoey_ovl_brk_e20 | 7 | -9.14% | 13 | +6.49% | 25 | +2.58% |
| book_e20combo_brk_cash | 7 | -9.18% | 13 | +6.49% | 25 | +2.59% |
| pol_switch3_cap | 7 | -4.18% | 13 | +4.16% | 25 | +0.39% |
| baitoey_e20_btcs_a2 | 7 | -8.63% | 13 | +5.06% | 25 | +2.30% |
| pol_switch_rt | 7 | -10.10% | 13 | +5.58% | 25 | +2.38% |
| baitoey_e20_shortc_alts | 7 | -8.96% | 13 | +6.08% | 25 | +2.52% |
| baitoey_e20_btcs_c | 7 | -9.34% | 13 | +6.25% | 25 | +2.61% |
| book_e20guard_confirm | 7 | -9.92% | 13 | +6.01% | 25 | +2.71% |
| book_e20guard_pullback | 7 | -10.07% | 13 | +6.24% | 25 | +2.66% |
| pol_switch_vt_tl_e20v45 | 7 | -10.26% | 13 | +6.52% | 25 | +2.68% |
| pol_switch3 | 7 | -5.78% | 13 | +5.06% | 25 | +0.21% |
| baitoey_ovl_evt_e20 | 7 | -10.11% | 13 | +6.55% | 25 | +2.84% |
| baitoey_e20_shortc_eth | 7 | -9.34% | 13 | +6.15% | 25 | +2.54% |
| baitoey_ovl_evtctl_e20 | 7 | -10.26% | 13 | +6.44% | 25 | +2.66% |
| pol_mom_ss | 7 | -1.18% | 13 | +1.89% | 25 | +0.44% |
| team_mom_ss25 | 7 | -1.18% | 13 | +1.89% | 25 | +0.44% |
| pol_combo_ms_tl | 7 | -2.15% | 13 | +1.21% | 25 | +0.91% |
| pol_switch_rot_mr | 7 | -9.64% | 13 | +6.45% | 25 | +1.29% |
| baitoey_e20_btcs_a | 7 | -10.54% | 13 | +6.28% | 25 | +2.70% |
| baitoey_e20_btcs_d | 7 | -10.54% | 13 | +6.28% | 25 | +2.70% |
| baitoey_rot_max | 7 | -9.62% | 13 | +10.32% | 25 | +3.26% |
| baitoey_e20_btcs_b | 7 | -10.91% | 13 | +6.09% | 25 | +2.60% |
| pol_trend_ls | 7 | -3.07% | 13 | +0.85% | 25 | +1.42% |
| baitoey_mr_4h | 7 | -5.30% | 13 | +2.18% | 25 | -0.34% |
| pol_switch_rmax_mr | 7 | -9.83% | 13 | +7.90% | 25 | +1.33% |
| pol_switch_rmax_tl | 7 | -11.15% | 13 | +9.46% | 25 | +3.37% |
| team_ew_daily | 7 | -13.03% | 13 | +7.43% | 25 | +0.94% |
| baitoey_tg_mom | 7 | +0.54% | 13 | +0.40% | 25 | +1.17% |
| pol_mr_cap | 7 | -4.50% | 13 | +0.78% | 25 | -0.42% |
| team_cash | 7 | -0.01% | 13 | +0.00% | 25 | +0.00% |
| book_short_breakdown | 7 | +1.16% | 13 | +0.11% | 25 | +0.41% |
| book_short_shock_fade | 7 | +0.06% | 13 | +0.02% | 25 | +0.00% |
| book_short_ridge6 | 7 | -0.05% | 13 | -0.01% | 25 | -0.04% |
| book_short_volume_fade | 7 | +0.03% | 13 | -0.00% | 25 | +0.00% |
| book_short_range_fail | 7 | +0.04% | 13 | -0.03% | 25 | -0.00% |
| book_short_analogue6 | 7 | -0.21% | 13 | -0.01% | 25 | -0.03% |
| book_short_analogue12 | 7 | -0.19% | 13 | -0.02% | 25 | -0.10% |
| baitoey_btc_short_a | 7 | -0.21% | 13 | -0.15% | 25 | +0.06% |
| baitoey_btc_short_d | 7 | -0.21% | 13 | -0.15% | 25 | +0.06% |
| book_bear_pullback | 7 | +0.07% | 13 | -0.15% | 25 | -0.05% |
| baitoey_mr_bbrsi | 7 | -2.36% | 13 | +0.78% | 25 | +0.03% |
| book_bear_breakdown | 7 | +0.25% | 13 | -0.18% | 25 | -0.07% |
| book_bear_cost_guard | 7 | -0.02% | 13 | -0.26% | 25 | -0.13% |
| book_bear_trail_exit | 7 | -0.28% | 13 | -0.33% | 25 | -0.21% |
| book_bear_guard | 7 | -0.10% | 13 | -0.31% | 25 | -0.19% |
| baitoey_btc_short_c | 7 | +1.05% | 13 | -0.71% | 25 | -0.32% |
| baitoey_btc_short_b | 7 | -0.57% | 13 | -0.51% | 25 | -0.09% |
| book_bear_fast_exit | 7 | -0.76% | 13 | -0.44% | 25 | -0.28% |
| book_bear_trend_control | 7 | +0.50% | 13 | -0.38% | 25 | -0.15% |
| baitoey_btc_short_a2 | 7 | +1.47% | 13 | -0.67% | 25 | -0.16% |
| baitoey_mjt_12_48_d | 7 | +2.98% | 13 | +0.80% | 25 | +2.07% |
| baitoey_btc_short_b2 | 7 | +1.10% | 13 | -0.45% | 25 | -0.34% |
| baitoey_mjt_24_96_d | 7 | +1.40% | 13 | +0.34% | 25 | +1.98% |
| baitoey_mjt_06_24_d | 7 | +0.92% | 13 | +0.83% | 25 | +0.26% |
| book_price_fast_signed | 7 | -0.05% | 13 | +1.05% | 25 | +0.62% |
| book_daily_channel | 7 | -0.07% | 13 | +0.35% | 25 | +0.06% |
| book_short_trend | 7 | +1.71% | 13 | -0.71% | 25 | +0.88% |
| book_price_channel_signed | 7 | -0.39% | 13 | +0.17% | 25 | +0.26% |
| book_short_rebound | 7 | +1.40% | 13 | -0.59% | 25 | +0.81% |
| book_price_slow_signed | 7 | +0.70% | 13 | +0.36% | 25 | +0.98% |
| book_price_fast_short | 7 | +1.70% | 13 | -1.02% | 25 | -0.59% |
| baitoey_mjt_24_96_6h | 7 | +2.94% | 13 | +0.34% | 25 | +2.39% |
| book_price_channel_short | 7 | +2.00% | 13 | -1.61% | 25 | -0.63% |
| book_price_slow_short | 7 | +2.41% | 13 | -1.93% | 25 | -0.20% |
| baitoey_mjt_12_48_6h | 7 | +1.78% | 13 | +0.22% | 25 | +1.89% |
| baitoey_mjt_06_24_6h | 7 | +1.16% | 13 | +0.99% | 25 | +0.77% |

Small scenario counts have weak precision. Scenario means remain diagnostic and do not override the main conservative ranking.

## Separate short-trigger table

**Hourly directional proxies only.** An onset is a cached entry/decision fill crossing from zero/long to a negative asset weight. Adds and partial covers do not create extra triggers; activity-guard onsets remain separately recorded. The cache already includes the engine's one-hour execution lag.

For a unit short, the entry proxy is hourly close x (1 - 0.050%); the cover proxy is hourly close x (1 + 0.050%). Both entry and cover pay 0.100% of their respective notionals. The spread is a declared constant stress assumption, not measured historical bid/ask. Correct means a positive after-cost unit-short proxy at the stated fixed horizon.

Fixed-horizon labels continue probing market direction even if the model already covered. Episode-cover behaviour is exported separately and is not quantity-weighted through adds or partial covers. **Actual account short PnL, minute/second timing, and intrahour TP/SL order are unverified.** Every hourly sampled barrier keeps that ambiguity; sampled take-profit counts must not be presented as executable before-rebound accuracy.

Each precision cell is **correct/valid (percentage)**. Six-hour intervals cluster by historical windows; 30 triggers in one window do not provide 30 independent market episodes.

| Model | Profile | Onsets | Windows firing/total | Correct 1h | Correct 3h | Correct 6h | 6h precision 90% interval | Open at endpoint |
|---|---|---|---|---|---|---|---|---|
| baitoey_btc_short_a | weak_archived | 4 | 4/25 | 2/4 (50.0%) | 2/4 (50.0%) | 2/4 (50.0%) | [0.0%, 100.0%] | 1 |
| baitoey_btc_short_a | weak_fresh_btc | 9 | 9/25 | 2/9 (22.2%) | 5/9 (55.6%) | 3/9 (33.3%) | [10.0%, 60.0%] | 4 |
| baitoey_btc_short_a2 | weak_archived | 20 | 17/25 | 3/20 (15.0%) | 8/20 (40.0%) | 6/20 (30.0%) | [12.5%, 50.0%] | 5 |
| baitoey_btc_short_a2 | weak_fresh_btc | 21 | 19/25 | 6/21 (28.6%) | 10/21 (47.6%) | 10/21 (47.6%) | [29.4%, 68.0%] | 3 |
| baitoey_btc_short_b | weak_archived | 15 | 12/25 | 3/15 (20.0%) | 4/15 (26.7%) | 5/15 (33.3%) | [16.7%, 47.4%] | 6 |
| baitoey_btc_short_b | weak_fresh_btc | 16 | 13/25 | 5/16 (31.2%) | 7/16 (43.8%) | 6/16 (37.5%) | [21.1%, 55.6%] | 6 |
| baitoey_btc_short_b2 | weak_archived | 22 | 18/25 | 6/22 (27.3%) | 7/22 (31.8%) | 7/22 (31.8%) | [14.3%, 50.0%] | 6 |
| baitoey_btc_short_b2 | weak_fresh_btc | 27 | 23/25 | 8/27 (29.6%) | 9/27 (33.3%) | 8/27 (29.6%) | [14.3%, 46.4%] | 7 |
| baitoey_btc_short_c | weak_archived | 19 | 15/25 | 4/19 (21.1%) | 6/19 (31.6%) | 2/19 (10.5%) | [0.0%, 23.8%] | 5 |
| baitoey_btc_short_c | weak_fresh_btc | 21 | 18/25 | 7/21 (33.3%) | 7/21 (33.3%) | 5/21 (23.8%) | [9.5%, 42.1%] | 5 |
| baitoey_btc_short_d | weak_archived | 4 | 4/25 | 2/4 (50.0%) | 2/4 (50.0%) | 2/4 (50.0%) | [0.0%, 100.0%] | 1 |
| baitoey_btc_short_d | weak_fresh_btc | 9 | 9/25 | 2/9 (22.2%) | 5/9 (55.6%) | 3/9 (33.3%) | [10.0%, 60.0%] | 4 |
| baitoey_e20_btcs_a | weak_archived | 104 | 13/25 | 35/104 (33.7%) | 29/104 (27.9%) | 29/104 (27.9%) | [14.9%, 39.5%] | 45 |
| baitoey_e20_btcs_a | weak_fresh_btc | 165 | 17/25 | 63/165 (38.2%) | 65/165 (39.4%) | 66/165 (40.0%) | [27.3%, 51.3%] | 89 |
| baitoey_e20_btcs_a2 | weak_archived | 110 | 17/25 | 34/110 (30.9%) | 34/110 (30.9%) | 32/110 (29.1%) | [17.9%, 38.9%] | 46 |
| baitoey_e20_btcs_a2 | weak_fresh_btc | 177 | 20/25 | 64/177 (36.2%) | 71/177 (40.1%) | 74/177 (41.8%) | [31.0%, 52.0%] | 95 |
| baitoey_e20_btcs_b | weak_archived | 102 | 13/25 | 35/102 (34.3%) | 28/102 (27.5%) | 28/102 (27.5%) | [14.0%, 38.9%] | 44 |
| baitoey_e20_btcs_b | weak_fresh_btc | 163 | 17/25 | 64/163 (39.3%) | 64/163 (39.3%) | 65/163 (39.9%) | [27.6%, 50.7%] | 88 |
| baitoey_e20_btcs_b2 | weak_archived | 112 | 19/25 | 37/112 (33.0%) | 34/112 (30.4%) | 33/112 (29.5%) | [18.3%, 39.7%] | 46 |
| baitoey_e20_btcs_b2 | weak_fresh_btc | 180 | 23/25 | 65/180 (36.1%) | 69/180 (38.3%) | 70/180 (38.9%) | [27.8%, 49.0%] | 95 |
| baitoey_e20_btcs_c | weak_archived | 102 | 13/25 | 33/102 (32.4%) | 28/102 (27.5%) | 27/102 (26.5%) | [14.1%, 36.9%] | 44 |
| baitoey_e20_btcs_c | weak_fresh_btc | 171 | 17/25 | 61/171 (35.7%) | 64/171 (37.4%) | 67/171 (39.2%) | [28.4%, 49.3%] | 96 |
| baitoey_e20_btcs_d | weak_archived | 104 | 13/25 | 35/104 (33.7%) | 29/104 (27.9%) | 29/104 (27.9%) | [14.9%, 39.5%] | 45 |
| baitoey_e20_btcs_d | weak_fresh_btc | 165 | 17/25 | 63/165 (38.2%) | 65/165 (39.4%) | 66/165 (40.0%) | [27.3%, 51.3%] | 89 |
| baitoey_e20_out10 | weak_archived | 152 | 18/25 | 46/152 (30.3%) | 54/152 (35.5%) | 53/152 (34.9%) | [26.5%, 41.8%] | 52 |
| baitoey_e20_out10 | weak_fresh_btc | 231 | 21/25 | 70/231 (30.3%) | 90/231 (39.0%) | 109/231 (47.2%) | [37.9%, 55.8%] | 102 |
| baitoey_e20_out15 | weak_archived | 151 | 18/25 | 46/151 (30.5%) | 53/151 (35.1%) | 52/151 (34.4%) | [26.0%, 41.5%] | 52 |
| baitoey_e20_out15 | weak_fresh_btc | 231 | 21/25 | 70/231 (30.3%) | 90/231 (39.0%) | 109/231 (47.2%) | [37.9%, 55.8%] | 102 |
| baitoey_e20_shortc_alts | weak_archived | 134 | 13/25 | 43/134 (32.1%) | 40/134 (29.9%) | 41/134 (30.6%) | [19.7%, 40.0%] | 59 |
| baitoey_e20_shortc_alts | weak_fresh_btc | 209 | 17/25 | 77/209 (36.8%) | 79/209 (37.8%) | 77/209 (36.8%) | [26.9%, 46.0%] | 112 |
| baitoey_e20_shortc_eth | weak_archived | 103 | 13/25 | 35/103 (34.0%) | 29/103 (28.2%) | 26/103 (25.2%) | [15.6%, 34.0%] | 45 |
| baitoey_e20_shortc_eth | weak_fresh_btc | 176 | 17/25 | 63/176 (35.8%) | 66/176 (37.5%) | 64/176 (36.4%) | [26.3%, 46.3%] | 97 |
| baitoey_e20_shortc_sol | weak_archived | 109 | 13/25 | 38/109 (34.9%) | 34/109 (31.2%) | 34/109 (31.2%) | [19.0%, 41.7%] | 48 |
| baitoey_e20_shortc_sol | weak_fresh_btc | 181 | 17/25 | 67/181 (37.0%) | 71/181 (39.2%) | 72/181 (39.8%) | [29.9%, 49.5%] | 99 |
| baitoey_mjt_06_24_6h | weak_archived | 491 | 25/25 | 93/491 (18.9%) | 145/477 (30.4%) | 164/477 (34.4%) | [28.6%, 41.0%] | 42 |
| baitoey_mjt_06_24_6h | weak_fresh_btc | 510 | 25/25 | 108/510 (21.2%) | 178/498 (35.7%) | 196/498 (39.4%) | [34.5%, 44.3%] | 52 |
| baitoey_mjt_06_24_d | weak_archived | 292 | 25/25 | 72/292 (24.7%) | 97/292 (33.2%) | 100/292 (34.2%) | [26.4%, 41.4%] | 39 |
| baitoey_mjt_06_24_d | weak_fresh_btc | 311 | 25/25 | 73/311 (23.5%) | 123/311 (39.5%) | 125/311 (40.2%) | [32.2%, 47.8%] | 55 |
| baitoey_mjt_12_48_6h | weak_archived | 351 | 25/25 | 63/351 (17.9%) | 102/345 (29.6%) | 115/345 (33.3%) | [28.0%, 39.1%] | 39 |
| baitoey_mjt_12_48_6h | weak_fresh_btc | 360 | 25/25 | 76/360 (21.1%) | 132/351 (37.6%) | 143/351 (40.7%) | [35.9%, 46.2%] | 54 |
| baitoey_mjt_12_48_d | weak_archived | 253 | 25/25 | 66/253 (26.1%) | 82/253 (32.4%) | 92/253 (36.4%) | [26.7%, 45.4%] | 43 |
| baitoey_mjt_12_48_d | weak_fresh_btc | 256 | 25/25 | 60/256 (23.4%) | 104/256 (40.6%) | 111/256 (43.4%) | [32.8%, 53.8%] | 56 |
| baitoey_mjt_24_96_6h | weak_archived | 217 | 25/25 | 45/217 (20.7%) | 71/215 (33.0%) | 73/215 (34.0%) | [27.7%, 40.8%] | 39 |
| baitoey_mjt_24_96_6h | weak_fresh_btc | 233 | 25/25 | 50/233 (21.5%) | 95/228 (41.7%) | 95/228 (41.7%) | [35.5%, 49.4%] | 59 |
| baitoey_mjt_24_96_d | weak_archived | 193 | 25/25 | 56/193 (29.0%) | 64/193 (33.2%) | 65/193 (33.7%) | [25.0%, 41.6%] | 45 |
| baitoey_mjt_24_96_d | weak_fresh_btc | 204 | 25/25 | 50/204 (24.5%) | 80/204 (39.2%) | 82/204 (40.2%) | [31.6%, 49.7%] | 58 |
| baitoey_mr_4h | weak_archived | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| baitoey_mr_4h | weak_fresh_btc | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| baitoey_mr_bbrsi | weak_archived | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| baitoey_mr_bbrsi | weak_fresh_btc | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| baitoey_ovl_altbtc_a_dual | weak_archived | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| baitoey_ovl_altbtc_a_dual | weak_fresh_btc | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| baitoey_ovl_altbtc_a_e20 | weak_archived | 103 | 13/25 | 34/103 (33.0%) | 28/103 (27.2%) | 27/103 (26.2%) | [14.6%, 36.4%] | 42 |
| baitoey_ovl_altbtc_a_e20 | weak_fresh_btc | 174 | 17/25 | 62/174 (35.6%) | 64/174 (36.8%) | 65/174 (37.4%) | [27.5%, 47.0%] | 94 |
| baitoey_ovl_altbtc_b_dual | weak_archived | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| baitoey_ovl_altbtc_b_dual | weak_fresh_btc | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| baitoey_ovl_altbtc_b_e20 | weak_archived | 103 | 13/25 | 34/103 (33.0%) | 28/103 (27.2%) | 28/103 (27.2%) | [15.1%, 37.9%] | 44 |
| baitoey_ovl_altbtc_b_e20 | weak_fresh_btc | 174 | 17/25 | 62/174 (35.6%) | 64/174 (36.8%) | 66/174 (37.9%) | [27.7%, 48.1%] | 97 |
| baitoey_ovl_brk_dual | weak_archived | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| baitoey_ovl_brk_dual | weak_fresh_btc | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| baitoey_ovl_brk_e20 | weak_archived | 103 | 13/25 | 34/103 (33.0%) | 28/103 (27.2%) | 28/103 (27.2%) | [15.1%, 37.9%] | 44 |
| baitoey_ovl_brk_e20 | weak_fresh_btc | 174 | 17/25 | 62/174 (35.6%) | 64/174 (36.8%) | 66/174 (37.9%) | [27.7%, 48.1%] | 97 |
| baitoey_ovl_evt_dual | weak_archived | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| baitoey_ovl_evt_dual | weak_fresh_btc | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| baitoey_ovl_evt_e20 | weak_archived | 106 | 13/25 | 37/106 (34.9%) | 31/106 (29.2%) | 29/106 (27.4%) | [15.4%, 37.7%] | 47 |
| baitoey_ovl_evt_e20 | weak_fresh_btc | 178 | 17/25 | 66/178 (37.1%) | 68/178 (38.2%) | 68/178 (38.2%) | [27.9%, 48.3%] | 100 |
| baitoey_ovl_evtctl_dual | weak_archived | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| baitoey_ovl_evtctl_dual | weak_fresh_btc | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| baitoey_ovl_evtctl_e20 | weak_archived | 103 | 13/25 | 34/103 (33.0%) | 28/103 (27.2%) | 28/103 (27.2%) | [15.1%, 37.9%] | 44 |
| baitoey_ovl_evtctl_e20 | weak_fresh_btc | 175 | 17/25 | 63/175 (36.0%) | 65/175 (37.1%) | 67/175 (38.3%) | [27.8%, 48.6%] | 97 |
| baitoey_rot_max | weak_archived | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| baitoey_rot_max | weak_fresh_btc | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| baitoey_tg_mom | weak_archived | 363 | 25/25 | 102/363 (28.1%) | 140/363 (38.6%) | 145/363 (39.9%) | [36.2%, 44.0%] | 36 |
| baitoey_tg_mom | weak_fresh_btc | 395 | 25/25 | 110/395 (27.8%) | 164/395 (41.5%) | 167/395 (42.3%) | [37.5%, 47.7%] | 52 |
| baitoey_vt_dual | weak_archived | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| baitoey_vt_dual | weak_fresh_btc | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| baitoey_vt_mom | weak_archived | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| baitoey_vt_mom | weak_fresh_btc | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| book_bear_breakdown | weak_archived | 472 | 25/25 | 115/472 (24.4%) | 144/472 (30.5%) | 172/464 (37.1%) | [32.2%, 41.7%] | 15 |
| book_bear_breakdown | weak_fresh_btc | 445 | 25/25 | 113/444 (25.5%) | 150/444 (33.8%) | 158/441 (35.8%) | [30.1%, 41.1%] | 21 |
| book_bear_cost_guard | weak_archived | 611 | 25/25 | 138/610 (22.6%) | 185/610 (30.3%) | 213/596 (35.7%) | [31.2%, 40.3%] | 21 |
| book_bear_cost_guard | weak_fresh_btc | 582 | 25/25 | 132/581 (22.7%) | 179/580 (30.9%) | 213/572 (37.2%) | [32.2%, 41.7%] | 25 |
| book_bear_fast_exit | weak_archived | 976 | 25/25 | 234/975 (24.0%) | 297/970 (30.6%) | 330/957 (34.5%) | [29.8%, 39.4%] | 5 |
| book_bear_fast_exit | weak_fresh_btc | 943 | 25/25 | 220/941 (23.4%) | 313/938 (33.4%) | 352/923 (38.1%) | [32.9%, 42.8%] | 4 |
| book_bear_guard | weak_archived | 802 | 25/25 | 180/799 (22.5%) | 223/799 (27.9%) | 255/786 (32.4%) | [28.2%, 36.8%] | 23 |
| book_bear_guard | weak_fresh_btc | 735 | 25/25 | 164/732 (22.4%) | 218/731 (29.8%) | 255/723 (35.3%) | [29.9%, 40.0%] | 27 |
| book_bear_pullback | weak_archived | 239 | 24/25 | 53/237 (22.4%) | 78/237 (32.9%) | 76/236 (32.2%) | [26.1%, 38.3%] | 4 |
| book_bear_pullback | weak_fresh_btc | 215 | 24/25 | 52/213 (24.4%) | 72/211 (34.1%) | 77/210 (36.7%) | [27.4%, 44.0%] | 9 |
| book_bear_trail_exit | weak_archived | 674 | 25/25 | 155/673 (23.0%) | 206/672 (30.7%) | 236/658 (35.9%) | [30.8%, 41.0%] | 19 |
| book_bear_trail_exit | weak_fresh_btc | 655 | 25/25 | 152/654 (23.2%) | 214/652 (32.8%) | 249/644 (38.7%) | [33.8%, 42.9%] | 17 |
| book_bear_trend_control | weak_archived | 553 | 25/25 | 111/553 (20.1%) | 156/551 (28.3%) | 176/545 (32.3%) | [27.2%, 38.1%] | 36 |
| book_bear_trend_control | weak_fresh_btc | 539 | 25/25 | 107/537 (19.9%) | 160/535 (29.9%) | 188/530 (35.5%) | [31.9%, 39.7%] | 44 |
| book_cashshort_confirm | weak_archived | 62 | 12/25 | 15/62 (24.2%) | 16/62 (25.8%) | 19/62 (30.6%) | [8.6%, 46.5%] | 13 |
| book_cashshort_confirm | weak_fresh_btc | 93 | 15/25 | 34/93 (36.6%) | 45/93 (48.4%) | 38/93 (40.9%) | [30.1%, 51.4%] | 15 |
| book_cashshort_pullback | weak_archived | 38 | 8/25 | 9/38 (23.7%) | 18/38 (47.4%) | 11/38 (28.9%) | [16.7%, 45.0%] | 10 |
| book_cashshort_pullback | weak_fresh_btc | 68 | 11/25 | 13/68 (19.1%) | 29/68 (42.6%) | 29/68 (42.6%) | [28.6%, 57.1%] | 12 |
| book_coin_trend | weak_archived | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| book_coin_trend | weak_fresh_btc | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| book_daily_channel | weak_archived | 232 | 18/25 | 44/232 (19.0%) | 61/232 (26.3%) | 79/232 (34.1%) | [24.8%, 42.0%] | 37 |
| book_daily_channel | weak_fresh_btc | 262 | 21/25 | 62/262 (23.7%) | 89/262 (34.0%) | 97/262 (37.0%) | [28.6%, 45.2%] | 60 |
| book_e20combo_alt_cash | weak_archived | 142 | 17/25 | 50/142 (35.2%) | 40/142 (28.2%) | 44/142 (31.0%) | [21.0%, 39.0%] | 47 |
| book_e20combo_alt_cash | weak_fresh_btc | 203 | 19/25 | 78/203 (38.4%) | 81/203 (39.9%) | 85/203 (41.9%) | [34.2%, 49.5%] | 97 |
| book_e20combo_alt_cash_pb | weak_archived | 125 | 16/25 | 43/125 (34.4%) | 39/125 (31.2%) | 40/125 (32.0%) | [23.3%, 40.1%] | 47 |
| book_e20combo_alt_cash_pb | weak_fresh_btc | 186 | 18/25 | 66/186 (35.5%) | 71/186 (38.2%) | 77/186 (41.4%) | [33.3%, 50.0%] | 97 |
| book_e20combo_alt_half_cash | weak_archived | 141 | 17/25 | 49/141 (34.8%) | 38/141 (27.0%) | 43/141 (30.5%) | [20.3%, 38.6%] | 47 |
| book_e20combo_alt_half_cash | weak_fresh_btc | 203 | 19/25 | 78/203 (38.4%) | 80/203 (39.4%) | 85/203 (41.9%) | [34.0%, 49.6%] | 97 |
| book_e20combo_alt_trim | weak_archived | 156 | 19/25 | 55/156 (35.3%) | 43/156 (27.6%) | 51/156 (32.7%) | [23.5%, 40.2%] | 47 |
| book_e20combo_alt_trim | weak_fresh_btc | 218 | 21/25 | 81/218 (37.2%) | 83/218 (38.1%) | 87/218 (39.9%) | [31.9%, 48.0%] | 97 |
| book_e20combo_brk_cash | weak_archived | 118 | 15/25 | 38/118 (32.2%) | 29/118 (24.6%) | 30/118 (25.4%) | [15.2%, 34.3%] | 47 |
| book_e20combo_brk_cash | weak_fresh_btc | 192 | 19/25 | 71/192 (37.0%) | 72/192 (37.5%) | 73/192 (38.0%) | [29.6%, 46.2%] | 97 |
| book_e20guard_confirm | weak_archived | 155 | 19/25 | 54/155 (34.8%) | 41/155 (26.5%) | 50/155 (32.3%) | [22.9%, 39.9%] | 47 |
| book_e20guard_confirm | weak_fresh_btc | 215 | 21/25 | 80/215 (37.2%) | 79/215 (36.7%) | 84/215 (39.1%) | [31.3%, 47.0%] | 95 |
| book_e20guard_pullback | weak_archived | 128 | 17/25 | 43/128 (33.6%) | 39/128 (30.5%) | 40/128 (31.2%) | [22.0%, 40.0%] | 46 |
| book_e20guard_pullback | weak_fresh_btc | 189 | 19/25 | 66/189 (34.9%) | 71/189 (37.6%) | 76/189 (40.2%) | [31.2%, 49.7%] | 97 |
| book_orch | weak_archived | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| book_orch | weak_fresh_btc | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| book_price_channel_short | weak_archived | 390 | 25/25 | 65/390 (16.7%) | 109/390 (27.9%) | 126/384 (32.8%) | [27.4%, 38.4%] | 36 |
| book_price_channel_short | weak_fresh_btc | 385 | 25/25 | 62/385 (16.1%) | 127/385 (33.0%) | 144/378 (38.1%) | [33.6%, 42.9%] | 53 |
| book_price_channel_signed | weak_archived | 449 | 25/25 | 73/449 (16.3%) | 116/449 (25.8%) | 133/446 (29.8%) | [25.3%, 34.4%] | 43 |
| book_price_channel_signed | weak_fresh_btc | 447 | 25/25 | 73/447 (16.3%) | 138/447 (30.9%) | 161/441 (36.5%) | [32.7%, 40.6%] | 56 |
| book_price_fast_short | weak_archived | 431 | 25/25 | 82/431 (19.0%) | 133/431 (30.9%) | 149/424 (35.1%) | [29.3%, 41.3%] | 35 |
| book_price_fast_short | weak_fresh_btc | 421 | 25/25 | 93/421 (22.1%) | 152/421 (36.1%) | 175/415 (42.2%) | [37.2%, 47.1%] | 41 |
| book_price_fast_signed | weak_archived | 453 | 25/25 | 89/453 (19.6%) | 137/453 (30.2%) | 156/446 (35.0%) | [29.0%, 41.3%] | 35 |
| book_price_fast_signed | weak_fresh_btc | 446 | 25/25 | 94/446 (21.1%) | 152/446 (34.1%) | 180/441 (40.8%) | [35.0%, 46.6%] | 42 |
| book_price_slow_short | weak_archived | 164 | 25/25 | 32/164 (19.5%) | 47/164 (28.7%) | 59/163 (36.2%) | [28.6%, 44.6%] | 36 |
| book_price_slow_short | weak_fresh_btc | 176 | 25/25 | 36/176 (20.5%) | 67/176 (38.1%) | 74/173 (42.8%) | [35.6%, 51.2%] | 50 |
| book_price_slow_signed | weak_archived | 166 | 25/25 | 35/166 (21.1%) | 45/166 (27.1%) | 57/165 (34.5%) | [26.8%, 42.8%] | 36 |
| book_price_slow_signed | weak_fresh_btc | 179 | 25/25 | 39/179 (21.8%) | 70/179 (39.1%) | 76/175 (43.4%) | [35.7%, 52.8%] | 51 |
| book_short_analogue12 | weak_archived | 354 | 23/25 | 82/353 (23.2%) | 127/347 (36.6%) | 138/346 (39.9%) | [34.4%, 46.3%] | 9 |
| book_short_analogue12 | weak_fresh_btc | 367 | 23/25 | 84/366 (23.0%) | 132/357 (37.0%) | 160/355 (45.1%) | [41.1%, 49.2%] | 14 |
| book_short_analogue6 | weak_archived | 114 | 20/25 | 29/114 (25.4%) | 46/114 (40.4%) | 38/113 (33.6%) | [28.2%, 40.0%] | 0 |
| book_short_analogue6 | weak_fresh_btc | 128 | 22/25 | 35/128 (27.3%) | 52/128 (40.6%) | 46/127 (36.2%) | [29.8%, 43.4%] | 4 |
| book_short_breakdown | weak_archived | 29 | 12/25 | 11/29 (37.9%) | 11/29 (37.9%) | 16/29 (55.2%) | [34.3%, 75.0%] | 6 |
| book_short_breakdown | weak_fresh_btc | 32 | 10/25 | 11/32 (34.4%) | 11/32 (34.4%) | 12/27 (44.4%) | [25.0%, 64.0%] | 16 |
| book_short_range_fail | weak_archived | 54 | 16/25 | 20/54 (37.0%) | 26/53 (49.1%) | 24/52 (46.2%) | [32.1%, 57.1%] | 2 |
| book_short_range_fail | weak_fresh_btc | 67 | 19/25 | 28/67 (41.8%) | 32/67 (47.8%) | 30/66 (45.5%) | [34.0%, 56.1%] | 1 |
| book_short_rebound | weak_archived | 265 | 25/25 | 57/265 (21.5%) | 71/265 (26.8%) | 89/265 (33.6%) | [27.0%, 41.7%] | 37 |
| book_short_rebound | weak_fresh_btc | 274 | 25/25 | 46/274 (16.8%) | 65/274 (23.7%) | 79/274 (28.8%) | [22.6%, 35.6%] | 44 |
| book_short_ridge6 | weak_archived | 31 | 8/25 | 10/31 (32.3%) | 11/31 (35.5%) | 14/31 (45.2%) | [27.6%, 61.9%] | 0 |
| book_short_ridge6 | weak_fresh_btc | 53 | 8/25 | 14/53 (26.4%) | 17/53 (32.1%) | 23/53 (43.4%) | [23.3%, 61.5%] | 4 |
| book_short_shock_fade | weak_archived | 22 | 11/25 | 7/22 (31.8%) | 10/19 (52.6%) | 9/19 (47.4%) | [26.7%, 71.4%] | 3 |
| book_short_shock_fade | weak_fresh_btc | 24 | 10/25 | 11/24 (45.8%) | 12/21 (57.1%) | 11/21 (52.4%) | [30.0%, 75.0%] | 4 |
| book_short_trend | weak_archived | 208 | 25/25 | 48/208 (23.1%) | 55/208 (26.4%) | 62/208 (29.8%) | [23.0%, 38.4%] | 50 |
| book_short_trend | weak_fresh_btc | 220 | 25/25 | 40/220 (18.2%) | 54/220 (24.5%) | 60/220 (27.3%) | [20.8%, 35.4%] | 59 |
| book_short_volume_fade | weak_archived | 42 | 16/25 | 9/42 (21.4%) | 17/41 (41.5%) | 17/39 (43.6%) | [32.0%, 55.8%] | 3 |
| book_short_volume_fade | weak_fresh_btc | 48 | 17/25 | 17/48 (35.4%) | 20/47 (42.6%) | 23/47 (48.9%) | [32.3%, 63.8%] | 2 |
| book_transition_short | weak_archived | 264 | 16/25 | 65/264 (24.6%) | 102/264 (38.6%) | 95/262 (36.3%) | [28.8%, 43.8%] | 6 |
| book_transition_short | weak_fresh_btc | 294 | 19/25 | 99/294 (33.7%) | 127/294 (43.2%) | 115/289 (39.8%) | [31.1%, 46.3%] | 15 |
| book_vt_breadth | weak_archived | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| book_vt_breadth | weak_fresh_btc | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| book_vt_dual | weak_archived | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| book_vt_dual | weak_fresh_btc | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| book_vt_top4 | weak_archived | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| book_vt_top4 | weak_fresh_btc | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| pol_abl_shock | weak_archived | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| pol_abl_shock | weak_fresh_btc | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| pol_combo_all | weak_archived | 123 | 25/25 | 33/123 (26.8%) | 58/123 (47.2%) | 55/123 (44.7%) | [32.4%, 56.3%] | 23 |
| pol_combo_all | weak_fresh_btc | 142 | 25/25 | 39/142 (27.5%) | 61/142 (43.0%) | 69/142 (48.6%) | [36.9%, 61.3%] | 29 |
| pol_combo_ms_tl | weak_archived | 297 | 25/25 | 79/297 (26.6%) | 107/297 (36.0%) | 121/297 (40.7%) | [33.1%, 48.6%] | 79 |
| pol_combo_ms_tl | weak_fresh_btc | 336 | 25/25 | 93/336 (27.7%) | 126/336 (37.5%) | 149/336 (44.3%) | [35.9%, 53.8%] | 124 |
| pol_combo_rb | weak_archived | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| pol_combo_rb | weak_fresh_btc | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| pol_combo_rt | weak_archived | 193 | 23/25 | 47/193 (24.4%) | 72/193 (37.3%) | 73/193 (37.8%) | [31.0%, 43.6%] | 53 |
| pol_combo_rt | weak_fresh_btc | 244 | 23/25 | 72/244 (29.5%) | 96/244 (39.3%) | 110/244 (45.1%) | [36.6%, 53.6%] | 86 |
| pol_combo_rtt | weak_archived | 159 | 23/25 | 45/159 (28.3%) | 64/159 (40.3%) | 64/159 (40.3%) | [31.8%, 47.7%] | 46 |
| pol_combo_rtt | weak_fresh_btc | 189 | 23/25 | 59/189 (31.2%) | 76/189 (40.2%) | 92/189 (48.7%) | [39.6%, 57.3%] | 66 |
| pol_mom_ss | weak_archived | 339 | 25/25 | 90/339 (26.5%) | 134/339 (39.5%) | 132/339 (38.9%) | [33.2%, 44.9%] | 76 |
| pol_mom_ss | weak_fresh_btc | 361 | 25/25 | 91/361 (25.2%) | 136/361 (37.7%) | 151/361 (41.8%) | [36.2%, 48.1%] | 90 |
| pol_mr_cap | weak_archived | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| pol_mr_cap | weak_fresh_btc | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| pol_switch3 | weak_archived | 17 | 2/25 | 4/17 (23.5%) | 7/17 (41.2%) | 8/16 (50.0%) | [50.0%, 50.0%] | 10 |
| pol_switch3 | weak_fresh_btc | 42 | 4/25 | 8/42 (19.0%) | 12/42 (28.6%) | 20/41 (48.8%) | [35.0%, 69.2%] | 27 |
| pol_switch3_cap | weak_archived | 17 | 2/25 | 4/17 (23.5%) | 7/17 (41.2%) | 8/16 (50.0%) | [50.0%, 50.0%] | 10 |
| pol_switch3_cap | weak_fresh_btc | 42 | 4/25 | 8/42 (19.0%) | 12/42 (28.6%) | 20/41 (48.8%) | [35.0%, 69.2%] | 27 |
| pol_switch_rc | weak_archived | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| pol_switch_rc | weak_fresh_btc | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| pol_switch_rmax_mr | weak_archived | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| pol_switch_rmax_mr | weak_fresh_btc | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| pol_switch_rmax_tl | weak_archived | 67 | 8/25 | 30/67 (44.8%) | 24/67 (35.8%) | 21/67 (31.3%) | [17.7%, 42.0%] | 28 |
| pol_switch_rmax_tl | weak_fresh_btc | 138 | 12/25 | 48/138 (34.8%) | 45/138 (32.6%) | 34/138 (24.6%) | [15.7%, 33.0%] | 78 |
| pol_switch_rot_mr | weak_archived | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| pol_switch_rot_mr | weak_fresh_btc | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| pol_switch_rt | weak_archived | 67 | 8/25 | 30/67 (44.8%) | 24/67 (35.8%) | 21/67 (31.3%) | [17.7%, 42.0%] | 28 |
| pol_switch_rt | weak_fresh_btc | 138 | 12/25 | 48/138 (34.8%) | 45/138 (32.6%) | 34/138 (24.6%) | [15.7%, 33.0%] | 78 |
| pol_switch_vt_tl | weak_archived | 69 | 8/25 | 31/69 (44.9%) | 25/69 (36.2%) | 23/69 (33.3%) | [20.8%, 43.6%] | 28 |
| pol_switch_vt_tl | weak_fresh_btc | 141 | 12/25 | 50/141 (35.5%) | 46/141 (32.6%) | 36/141 (25.5%) | [16.8%, 33.9%] | 79 |
| pol_switch_vt_tl_e20v45 | weak_archived | 103 | 13/25 | 34/103 (33.0%) | 28/103 (27.2%) | 28/103 (27.2%) | [15.1%, 37.9%] | 44 |
| pol_switch_vt_tl_e20v45 | weak_fresh_btc | 175 | 17/25 | 63/175 (36.0%) | 65/175 (37.1%) | 67/175 (38.3%) | [27.8%, 48.6%] | 97 |
| pol_switch_vtm_tl | weak_archived | 69 | 8/25 | 31/69 (44.9%) | 25/69 (36.2%) | 23/69 (33.3%) | [20.8%, 43.6%] | 28 |
| pol_switch_vtm_tl | weak_fresh_btc | 141 | 12/25 | 50/141 (35.5%) | 46/141 (32.6%) | 36/141 (25.5%) | [16.8%, 33.9%] | 79 |
| pol_trend_ls | weak_archived | 211 | 23/25 | 53/211 (25.1%) | 75/211 (35.5%) | 83/211 (39.3%) | [32.6%, 44.8%] | 68 |
| pol_trend_ls | weak_fresh_btc | 273 | 23/25 | 82/273 (30.0%) | 109/273 (39.9%) | 125/273 (45.8%) | [37.7%, 54.3%] | 118 |
| pol_vt_mvr | weak_archived | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| pol_vt_mvr | weak_fresh_btc | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| team_btc_hold | weak_archived | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| team_btc_hold | weak_fresh_btc | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| team_cash | weak_archived | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| team_cash | weak_fresh_btc | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| team_ew_daily | weak_archived | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| team_ew_daily | weak_fresh_btc | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| team_mom_ss25 | weak_archived | 339 | 25/25 | 90/339 (26.5%) | 134/339 (39.5%) | 132/339 (38.9%) | [33.2%, 44.9%] | 76 |
| team_mom_ss25 | weak_fresh_btc | 361 | 25/25 | 91/361 (25.2%) | 136/361 (37.7%) | 151/361 (41.8%) | [36.2%, 48.1%] | 90 |
| team_rot_ew | weak_archived | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| team_rot_ew | weak_fresh_btc | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| team_rot_iv | weak_archived | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| team_rot_iv | weak_fresh_btc | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| team_trend_2 | weak_archived | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |
| team_trend_2 | weak_fresh_btc | 0 | 0/25 | 0/0 (—) | 0/0 (—) | 0/0 (—) | [—, —] | 0 |

Wrong direction means the underlying price did not fall. Cost-only loss means it fell but the move did not cover the declared spread and both fees. A rebound loss means sampled profit existed within the horizon but the final proxy was nonpositive.

| Model | Profile | Wrong direction 1/3/6h | Cost-only loss 1/3/6h | Unresolved 1/3/6h | Rebound losses 1/3/6h |
|---|---|---|---|---|---|
| baitoey_btc_short_a | weak_archived | 2/1/2 | 0/1/0 | 0/0/0 | 0/0/0 |
| baitoey_btc_short_a | weak_fresh_btc | 4/2/6 | 3/2/0 | 0/0/0 | 0/0/2 |
| baitoey_btc_short_a2 | weak_archived | 10/12/9 | 7/0/5 | 0/0/0 | 0/0/3 |
| baitoey_btc_short_a2 | weak_fresh_btc | 7/7/7 | 8/4/4 | 0/0/0 | 0/2/6 |
| baitoey_btc_short_b | weak_archived | 11/10/9 | 1/1/1 | 0/0/0 | 0/0/2 |
| baitoey_btc_short_b | weak_fresh_btc | 9/8/9 | 2/1/1 | 0/0/0 | 0/0/3 |
| baitoey_btc_short_b2 | weak_archived | 12/13/11 | 4/2/4 | 0/0/0 | 0/1/2 |
| baitoey_btc_short_b2 | weak_fresh_btc | 11/15/14 | 8/3/5 | 0/0/0 | 0/2/7 |
| baitoey_btc_short_c | weak_archived | 12/12/12 | 3/1/5 | 0/0/0 | 0/0/4 |
| baitoey_btc_short_c | weak_fresh_btc | 12/11/10 | 2/3/6 | 0/0/0 | 0/1/5 |
| baitoey_btc_short_d | weak_archived | 2/1/2 | 0/1/0 | 0/0/0 | 0/0/0 |
| baitoey_btc_short_d | weak_fresh_btc | 4/2/6 | 3/2/0 | 0/0/0 | 0/0/2 |
| baitoey_e20_btcs_a | weak_archived | 55/64/65 | 14/11/10 | 0/0/0 | 0/20/26 |
| baitoey_e20_btcs_a | weak_fresh_btc | 85/80/84 | 17/20/15 | 0/0/0 | 0/32/41 |
| baitoey_e20_btcs_a2 | weak_archived | 58/66/64 | 18/10/14 | 0/0/0 | 0/18/27 |
| baitoey_e20_btcs_a2 | weak_fresh_btc | 92/83/85 | 21/23/18 | 0/0/0 | 0/31/42 |
| baitoey_e20_btcs_b | weak_archived | 55/63/63 | 12/11/11 | 0/0/0 | 0/19/26 |
| baitoey_e20_btcs_b | weak_fresh_btc | 84/79/83 | 15/20/15 | 0/0/0 | 0/31/40 |
| baitoey_e20_btcs_b2 | weak_archived | 59/66/65 | 16/12/14 | 0/0/0 | 0/19/27 |
| baitoey_e20_btcs_b2 | weak_fresh_btc | 94/89/90 | 21/22/20 | 0/0/0 | 0/31/43 |
| baitoey_e20_btcs_c | weak_archived | 54/64/64 | 15/10/11 | 0/0/0 | 0/18/25 |
| baitoey_e20_btcs_c | weak_fresh_btc | 93/85/88 | 17/22/16 | 0/0/0 | 0/29/39 |
| baitoey_e20_btcs_d | weak_archived | 55/64/65 | 14/11/10 | 0/0/0 | 0/20/26 |
| baitoey_e20_btcs_d | weak_fresh_btc | 85/80/84 | 17/20/15 | 0/0/0 | 0/32/41 |
| baitoey_e20_out10 | weak_archived | 74/80/81 | 32/18/18 | 0/0/0 | 0/24/38 |
| baitoey_e20_out10 | weak_fresh_btc | 123/116/103 | 38/25/19 | 0/0/0 | 0/25/36 |
| baitoey_e20_out15 | weak_archived | 73/80/81 | 32/18/18 | 0/0/0 | 0/25/39 |
| baitoey_e20_out15 | weak_fresh_btc | 123/116/103 | 38/25/19 | 0/0/0 | 0/26/37 |
| baitoey_e20_shortc_alts | weak_archived | 78/80/82 | 13/14/11 | 0/0/0 | 0/25/35 |
| baitoey_e20_shortc_alts | weak_fresh_btc | 114/107/116 | 18/23/16 | 0/0/0 | 0/41/53 |
| baitoey_e20_shortc_eth | weak_archived | 55/63/65 | 13/11/12 | 0/0/0 | 0/21/32 |
| baitoey_e20_shortc_eth | weak_fresh_btc | 96/89/94 | 17/21/18 | 0/0/0 | 0/33/46 |
| baitoey_e20_shortc_sol | weak_archived | 58/66/65 | 13/9/10 | 0/0/0 | 0/20/27 |
| baitoey_e20_shortc_sol | weak_fresh_btc | 97/90/94 | 17/20/15 | 0/0/0 | 0/32/42 |
| baitoey_mjt_06_24_6h | weak_archived | 278/265/262 | 120/67/51 | 0/14/14 | 0/53/108 |
| baitoey_mjt_06_24_6h | weak_fresh_btc | 277/247/248 | 125/73/54 | 0/12/12 | 0/57/103 |
| baitoey_mjt_06_24_d | weak_archived | 176/155/159 | 44/40/33 | 0/0/0 | 0/40/72 |
| baitoey_mjt_06_24_d | weak_fresh_btc | 179/145/152 | 59/43/34 | 0/0/0 | 0/38/74 |
| baitoey_mjt_12_48_6h | weak_archived | 214/194/181 | 74/49/49 | 0/6/6 | 0/40/74 |
| baitoey_mjt_12_48_6h | weak_fresh_btc | 199/168/168 | 85/51/40 | 0/9/9 | 0/42/77 |
| baitoey_mjt_12_48_d | weak_archived | 142/134/126 | 45/37/35 | 0/0/0 | 0/38/57 |
| baitoey_mjt_12_48_d | weak_fresh_btc | 139/121/118 | 57/31/27 | 0/0/0 | 0/28/51 |
| baitoey_mjt_24_96_6h | weak_archived | 121/107/111 | 51/37/31 | 0/2/2 | 0/26/53 |
| baitoey_mjt_24_96_6h | weak_fresh_btc | 119/96/108 | 64/37/25 | 0/5/5 | 0/21/50 |
| baitoey_mjt_24_96_d | weak_archived | 103/97/100 | 34/32/28 | 0/0/0 | 0/34/53 |
| baitoey_mjt_24_96_d | weak_fresh_btc | 106/97/98 | 48/27/24 | 0/0/0 | 0/27/47 |
| baitoey_mr_4h | weak_archived | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| baitoey_mr_4h | weak_fresh_btc | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| baitoey_mr_bbrsi | weak_archived | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| baitoey_mr_bbrsi | weak_fresh_btc | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| baitoey_ovl_altbtc_a_dual | weak_archived | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| baitoey_ovl_altbtc_a_dual | weak_fresh_btc | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| baitoey_ovl_altbtc_a_e20 | weak_archived | 56/65/65 | 13/10/11 | 0/0/0 | 0/21/28 |
| baitoey_ovl_altbtc_a_e20 | weak_fresh_btc | 96/90/93 | 16/20/16 | 0/0/0 | 0/33/43 |
| baitoey_ovl_altbtc_b_dual | weak_archived | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| baitoey_ovl_altbtc_b_dual | weak_fresh_btc | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| baitoey_ovl_altbtc_b_e20 | weak_archived | 55/65/65 | 14/10/10 | 0/0/0 | 0/20/26 |
| baitoey_ovl_altbtc_b_e20 | weak_fresh_btc | 95/90/93 | 17/20/15 | 0/0/0 | 0/32/41 |
| baitoey_ovl_brk_dual | weak_archived | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| baitoey_ovl_brk_dual | weak_fresh_btc | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| baitoey_ovl_brk_e20 | weak_archived | 55/65/65 | 14/10/10 | 0/0/0 | 0/20/26 |
| baitoey_ovl_brk_e20 | weak_fresh_btc | 95/90/93 | 17/20/15 | 0/0/0 | 0/32/41 |
| baitoey_ovl_evt_dual | weak_archived | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| baitoey_ovl_evt_dual | weak_fresh_btc | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| baitoey_ovl_evt_e20 | weak_archived | 55/65/67 | 14/10/10 | 0/0/0 | 0/20/28 |
| baitoey_ovl_evt_e20 | weak_fresh_btc | 95/90/95 | 17/20/15 | 0/0/0 | 0/32/43 |
| baitoey_ovl_evtctl_dual | weak_archived | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| baitoey_ovl_evtctl_dual | weak_fresh_btc | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| baitoey_ovl_evtctl_e20 | weak_archived | 55/65/65 | 14/10/10 | 0/0/0 | 0/20/26 |
| baitoey_ovl_evtctl_e20 | weak_fresh_btc | 95/90/93 | 17/20/15 | 0/0/0 | 0/32/41 |
| baitoey_rot_max | weak_archived | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| baitoey_rot_max | weak_fresh_btc | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| baitoey_tg_mom | weak_archived | 207/175/185 | 54/48/33 | 0/0/0 | 0/48/92 |
| baitoey_tg_mom | weak_fresh_btc | 220/190/190 | 65/41/38 | 0/0/0 | 0/50/87 |
| baitoey_vt_dual | weak_archived | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| baitoey_vt_dual | weak_fresh_btc | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| baitoey_vt_mom | weak_archived | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| baitoey_vt_mom | weak_fresh_btc | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| book_bear_breakdown | weak_archived | 262/264/238 | 95/64/54 | 0/0/8 | 0/61/93 |
| book_bear_breakdown | weak_fresh_btc | 247/234/230 | 84/60/53 | 1/1/4 | 0/56/99 |
| book_bear_cost_guard | weak_archived | 329/338/304 | 143/87/79 | 1/1/15 | 0/74/124 |
| book_bear_cost_guard | weak_fresh_btc | 321/316/289 | 128/85/70 | 1/2/10 | 0/69/115 |
| book_bear_fast_exit | weak_archived | 545/540/515 | 196/133/112 | 1/6/19 | 0/111/184 |
| book_bear_fast_exit | weak_fresh_btc | 525/497/479 | 196/128/92 | 2/5/20 | 0/97/174 |
| book_bear_guard | weak_archived | 436/450/424 | 183/126/107 | 3/3/16 | 0/99/170 |
| book_bear_guard | weak_fresh_btc | 397/396/381 | 171/117/87 | 3/4/12 | 0/95/159 |
| book_bear_pullback | weak_archived | 135/126/132 | 49/33/28 | 2/2/3 | 0/26/59 |
| book_bear_pullback | weak_fresh_btc | 119/111/109 | 42/28/24 | 2/4/5 | 0/21/45 |
| book_bear_trail_exit | weak_archived | 366/375/342 | 152/91/80 | 1/2/16 | 0/81/133 |
| book_bear_trail_exit | weak_fresh_btc | 355/348/323 | 147/90/72 | 1/3/11 | 0/75/130 |
| book_bear_trend_control | weak_archived | 307/303/297 | 135/92/72 | 0/2/8 | 0/64/115 |
| book_bear_trend_control | weak_fresh_btc | 298/283/282 | 132/92/60 | 2/4/9 | 0/68/111 |
| book_cashshort_confirm | weak_archived | 41/43/39 | 6/3/4 | 0/0/0 | 0/11/14 |
| book_cashshort_confirm | weak_fresh_btc | 45/40/41 | 14/8/14 | 0/0/0 | 0/16/30 |
| book_cashshort_pullback | weak_archived | 19/14/23 | 10/6/4 | 0/0/0 | 0/3/12 |
| book_cashshort_pullback | weak_fresh_btc | 44/30/31 | 11/9/8 | 0/0/0 | 0/10/15 |
| book_coin_trend | weak_archived | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| book_coin_trend | weak_fresh_btc | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| book_daily_channel | weak_archived | 148/140/128 | 40/31/25 | 0/0/0 | 0/31/50 |
| book_daily_channel | weak_fresh_btc | 144/133/140 | 56/40/25 | 0/0/0 | 0/33/58 |
| book_e20combo_alt_cash | weak_archived | 73/88/88 | 19/14/10 | 0/0/0 | 0/29/33 |
| book_e20combo_alt_cash | weak_fresh_btc | 103/99/102 | 22/23/16 | 0/0/0 | 0/35/44 |
| book_e20combo_alt_cash_pb | weak_archived | 63/72/74 | 19/14/11 | 0/0/0 | 0/20/28 |
| book_e20combo_alt_cash_pb | weak_fresh_btc | 100/92/93 | 20/23/16 | 0/0/0 | 0/30/38 |
| book_e20combo_alt_half_cash | weak_archived | 73/89/88 | 19/14/10 | 0/0/0 | 0/30/33 |
| book_e20combo_alt_half_cash | weak_fresh_btc | 103/100/102 | 22/23/16 | 0/0/0 | 0/36/44 |
| book_e20combo_alt_trim | weak_archived | 80/97/93 | 21/16/12 | 0/0/0 | 0/32/34 |
| book_e20combo_alt_trim | weak_fresh_btc | 113/109/111 | 24/26/20 | 0/0/0 | 0/38/47 |
| book_e20combo_brk_cash | weak_archived | 65/77/78 | 15/12/10 | 0/0/0 | 0/24/29 |
| book_e20combo_brk_cash | weak_fresh_btc | 99/100/103 | 22/20/16 | 0/0/0 | 0/35/46 |
| book_e20guard_confirm | weak_archived | 80/98/93 | 21/16/12 | 0/0/0 | 0/33/34 |
| book_e20guard_confirm | weak_fresh_btc | 111/110/111 | 24/26/20 | 0/0/0 | 0/39/47 |
| book_e20guard_pullback | weak_archived | 63/74/74 | 22/15/14 | 0/0/0 | 0/21/29 |
| book_e20guard_pullback | weak_fresh_btc | 100/95/94 | 23/23/19 | 0/0/0 | 0/30/39 |
| book_orch | weak_archived | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| book_orch | weak_fresh_btc | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| book_price_channel_short | weak_archived | 222/217/202 | 103/64/56 | 0/0/6 | 0/45/85 |
| book_price_channel_short | weak_fresh_btc | 214/204/190 | 109/54/44 | 0/0/7 | 0/41/75 |
| book_price_channel_signed | weak_archived | 262/256/248 | 114/77/65 | 0/0/3 | 0/53/98 |
| book_price_channel_signed | weak_fresh_btc | 252/234/228 | 122/75/52 | 0/0/6 | 0/48/85 |
| book_price_fast_short | weak_archived | 243/234/218 | 106/64/57 | 0/0/7 | 0/42/85 |
| book_price_fast_short | weak_fresh_btc | 217/200/191 | 111/69/49 | 0/0/6 | 0/47/82 |
| book_price_fast_signed | weak_archived | 255/246/233 | 109/70/57 | 0/0/7 | 0/49/90 |
| book_price_fast_signed | weak_fresh_btc | 234/216/209 | 118/78/52 | 0/0/5 | 0/52/86 |
| book_price_slow_short | weak_archived | 84/86/79 | 48/31/25 | 0/0/1 | 0/19/36 |
| book_price_slow_short | weak_fresh_btc | 83/79/80 | 57/30/19 | 0/0/3 | 0/19/36 |
| book_price_slow_signed | weak_archived | 86/91/83 | 45/30/25 | 0/0/1 | 0/21/38 |
| book_price_slow_signed | weak_fresh_btc | 86/81/81 | 54/28/18 | 0/0/4 | 0/19/35 |
| book_short_analogue12 | weak_archived | 161/165/166 | 110/55/42 | 1/7/8 | 0/33/67 |
| book_short_analogue12 | weak_fresh_btc | 179/170/152 | 103/55/43 | 1/10/12 | 0/34/61 |
| book_short_analogue6 | weak_archived | 65/57/60 | 20/11/15 | 0/0/1 | 0/10/28 |
| book_short_analogue6 | weak_fresh_btc | 74/62/67 | 19/14/14 | 0/0/1 | 0/13/34 |
| book_short_breakdown | weak_archived | 13/17/10 | 5/1/3 | 0/0/0 | 0/6/3 |
| book_short_breakdown | weak_fresh_btc | 19/21/13 | 2/0/2 | 0/0/5 | 0/4/4 |
| book_short_range_fail | weak_archived | 17/23/24 | 17/4/4 | 0/1/2 | 0/7/14 |
| book_short_range_fail | weak_fresh_btc | 24/27/30 | 15/8/6 | 0/0/1 | 0/10/16 |
| book_short_rebound | weak_archived | 140/143/136 | 68/51/40 | 0/0/0 | 0/32/53 |
| book_short_rebound | weak_fresh_btc | 147/151/147 | 81/58/48 | 0/0/0 | 0/23/56 |
| book_short_ridge6 | weak_archived | 14/12/9 | 7/8/8 | 0/0/0 | 0/5/6 |
| book_short_ridge6 | weak_fresh_btc | 33/26/24 | 6/10/6 | 0/0/0 | 0/9/8 |
| book_short_shock_fade | weak_archived | 11/7/8 | 4/2/2 | 0/3/3 | 0/2/6 |
| book_short_shock_fade | weak_fresh_btc | 9/6/7 | 4/3/3 | 0/3/3 | 0/2/6 |
| book_short_trend | weak_archived | 113/120/115 | 47/33/31 | 0/0/0 | 0/27/44 |
| book_short_trend | weak_fresh_btc | 125/125/126 | 55/41/34 | 0/0/0 | 0/17/43 |
| book_short_volume_fade | weak_archived | 21/16/16 | 12/8/6 | 0/1/3 | 0/3/7 |
| book_short_volume_fade | weak_fresh_btc | 19/14/17 | 12/13/7 | 0/1/1 | 0/6/10 |
| book_transition_short | weak_archived | 161/127/138 | 38/35/29 | 0/0/2 | 0/32/76 |
| book_transition_short | weak_fresh_btc | 162/134/150 | 33/33/24 | 0/0/5 | 0/42/79 |
| book_vt_breadth | weak_archived | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| book_vt_breadth | weak_fresh_btc | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| book_vt_dual | weak_archived | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| book_vt_dual | weak_fresh_btc | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| book_vt_top4 | weak_archived | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| book_vt_top4 | weak_fresh_btc | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| pol_abl_shock | weak_archived | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| pol_abl_shock | weak_fresh_btc | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| pol_combo_all | weak_archived | 71/54/57 | 19/11/11 | 0/0/0 | 0/16/32 |
| pol_combo_all | weak_fresh_btc | 76/66/66 | 27/15/7 | 0/0/0 | 0/13/22 |
| pol_combo_ms_tl | weak_archived | 165/149/139 | 53/41/37 | 0/0/0 | 0/47/77 |
| pol_combo_ms_tl | weak_fresh_btc | 173/171/157 | 70/39/30 | 0/0/0 | 0/47/69 |
| pol_combo_rb | weak_archived | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| pol_combo_rb | weak_fresh_btc | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| pol_combo_rt | weak_archived | 111/98/98 | 35/23/22 | 0/0/0 | 0/25/41 |
| pol_combo_rt | weak_fresh_btc | 128/123/118 | 44/25/16 | 0/0/0 | 0/28/41 |
| pol_combo_rtt | weak_archived | 88/75/76 | 26/20/19 | 0/0/0 | 0/21/37 |
| pol_combo_rtt | weak_fresh_btc | 97/91/85 | 33/22/12 | 0/0/0 | 0/24/34 |
| pol_mom_ss | weak_archived | 184/166/165 | 65/39/42 | 0/0/0 | 0/44/94 |
| pol_mom_ss | weak_fresh_btc | 200/186/176 | 70/39/34 | 0/0/0 | 0/43/74 |
| pol_mr_cap | weak_archived | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| pol_mr_cap | weak_fresh_btc | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| pol_switch3 | weak_archived | 6/8/5 | 7/2/3 | 0/0/1 | 0/2/4 |
| pol_switch3 | weak_fresh_btc | 26/24/17 | 8/6/4 | 0/0/1 | 0/3/7 |
| pol_switch3_cap | weak_archived | 6/8/5 | 7/2/3 | 0/0/1 | 0/2/4 |
| pol_switch3_cap | weak_fresh_btc | 26/24/17 | 8/6/4 | 0/0/1 | 0/3/7 |
| pol_switch_rc | weak_archived | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| pol_switch_rc | weak_fresh_btc | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| pol_switch_rmax_mr | weak_archived | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| pol_switch_rmax_mr | weak_fresh_btc | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| pol_switch_rmax_tl | weak_archived | 32/35/38 | 5/8/8 | 0/0/0 | 0/13/17 |
| pol_switch_rmax_tl | weak_fresh_btc | 77/81/97 | 13/12/7 | 0/0/0 | 0/25/43 |
| pol_switch_rot_mr | weak_archived | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| pol_switch_rot_mr | weak_fresh_btc | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| pol_switch_rt | weak_archived | 32/35/38 | 5/8/8 | 0/0/0 | 0/13/17 |
| pol_switch_rt | weak_fresh_btc | 77/81/97 | 13/12/7 | 0/0/0 | 0/25/43 |
| pol_switch_vt_tl | weak_archived | 33/36/38 | 5/8/8 | 0/0/0 | 0/13/17 |
| pol_switch_vt_tl | weak_fresh_btc | 78/83/98 | 13/12/7 | 0/0/0 | 0/26/44 |
| pol_switch_vt_tl_e20v45 | weak_archived | 55/65/65 | 14/10/10 | 0/0/0 | 0/20/26 |
| pol_switch_vt_tl_e20v45 | weak_fresh_btc | 95/90/93 | 17/20/15 | 0/0/0 | 0/32/41 |
| pol_switch_vtm_tl | weak_archived | 33/36/38 | 5/8/8 | 0/0/0 | 0/13/17 |
| pol_switch_vtm_tl | weak_fresh_btc | 78/83/98 | 13/12/7 | 0/0/0 | 0/26/44 |
| pol_trend_ls | weak_archived | 119/111/103 | 39/25/25 | 0/0/0 | 0/29/44 |
| pol_trend_ls | weak_fresh_btc | 144/137/125 | 47/27/23 | 0/0/0 | 0/28/44 |
| pol_vt_mvr | weak_archived | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| pol_vt_mvr | weak_fresh_btc | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| team_btc_hold | weak_archived | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| team_btc_hold | weak_fresh_btc | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| team_cash | weak_archived | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| team_cash | weak_fresh_btc | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| team_ew_daily | weak_archived | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| team_ew_daily | weak_fresh_btc | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| team_mom_ss25 | weak_archived | 184/166/165 | 65/39/42 | 0/0/0 | 0/44/94 |
| team_mom_ss25 | weak_fresh_btc | 200/186/176 | 70/39/34 | 0/0/0 | 0/43/74 |
| team_rot_ew | weak_archived | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| team_rot_ew | weak_fresh_btc | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| team_rot_iv | weak_archived | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| team_rot_iv | weak_fresh_btc | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| team_trend_2 | weak_archived | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |
| team_trend_2 | weak_fresh_btc | 0/0/0 | 0/0/0 | 0/0/0 | 0/0/0 |

## Ranked short accuracy and returns

Two descriptive ranks within each profile: accuracy rank sorts the six-hour precision lower90% bound; return rank sorts the equal-firing-window mean six-hour after-cost unit proxy. A rank is not a reliability pass. MINIMUM_COUNT_ONLY means the existing onset-count rule passed; independent evidence can still be weak. INSUFFICIENT means the count rule failed. Zero valid labels receive no rank.


| Model | Profile | Accuracy rank | Return proxy rank | Onsets | Firing windows | 6h correct/valid | 6h accuracy lower90% | 6h unit proxy return | Full portfolio mean | CS | Sample flag |
|---|---|---|---|---|---|---|---|---|---|---|---|
| pol_switch3 | weak_archived | 1 | 3 | 17 | 2/25 | 8/16 (50.0%) | 50.00% | +0.96% | +1.11% | 0.28 | INSUFFICIENT |
| pol_switch3_cap | weak_archived | 2 | 4 | 17 | 2/25 | 8/16 (50.0%) | 50.00% | +0.96% | +0.86% | 0.37 | INSUFFICIENT |
| baitoey_tg_mom | weak_archived | 10 | 46 | 363 | 25/25 | 145/363 (39.9%) | 36.19% | -0.30% | +0.24% | 0.05 | MINIMUM_COUNT_ONLY |
| book_short_analogue12 | weak_archived | 15 | 9 | 354 | 23/25 | 138/346 (39.9%) | 34.44% | +0.01% | -0.08% | -0.05 | MINIMUM_COUNT_ONLY |
| book_short_breakdown | weak_archived | 17 | 5 | 29 | 12/25 | 16/29 (55.2%) | 34.29% | +0.50% | +0.37% | 0.04 | INSUFFICIENT |
| pol_mom_ss | weak_archived | 18 | 15 | 339 | 25/25 | 132/339 (38.9%) | 33.16% | -0.16% | +0.58% | 0.16 | MINIMUM_COUNT_ONLY |
| team_mom_ss25 | weak_archived | 19 | 16 | 339 | 25/25 | 132/339 (38.9%) | 33.16% | -0.16% | +0.58% | 0.16 | MINIMUM_COUNT_ONLY |
| pol_combo_ms_tl | weak_archived | 20 | 18 | 297 | 25/25 | 121/297 (40.7%) | 33.10% | -0.17% | -0.17% | 0.10 | MINIMUM_COUNT_ONLY |
| pol_trend_ls | weak_archived | 21 | 56 | 211 | 23/25 | 83/211 (39.3%) | 32.58% | -0.35% | -0.76% | 0.07 | MINIMUM_COUNT_ONLY |
| pol_combo_all | weak_archived | 22 | 23 | 123 | 25/25 | 55/123 (44.7%) | 32.38% | -0.19% | +0.58% | 0.14 | MINIMUM_COUNT_ONLY |
| book_bear_breakdown | weak_archived | 23 | 68 | 472 | 25/25 | 172/464 (37.1%) | 32.16% | -0.43% | -0.09% | -0.08 | MINIMUM_COUNT_ONLY |
| book_short_range_fail | weak_archived | 24 | 22 | 54 | 16/25 | 24/52 (46.2%) | 32.14% | -0.18% | +0.00% | -0.00 | MINIMUM_COUNT_ONLY |
| book_short_volume_fade | weak_archived | 26 | 10 | 42 | 16/25 | 17/39 (43.6%) | 32.00% | -0.09% | +0.00% | 0.00 | MINIMUM_COUNT_ONLY |
| pol_combo_rtt | weak_archived | 27 | 63 | 159 | 23/25 | 64/159 (40.3%) | 31.79% | -0.40% | +0.40% | 0.12 | MINIMUM_COUNT_ONLY |
| book_bear_cost_guard | weak_archived | 28 | 71 | 611 | 25/25 | 213/596 (35.7%) | 31.18% | -0.48% | -0.20% | -0.13 | MINIMUM_COUNT_ONLY |
| pol_combo_rt | weak_archived | 29 | 67 | 193 | 23/25 | 73/193 (37.8%) | 31.03% | -0.42% | +0.33% | 0.10 | MINIMUM_COUNT_ONLY |
| book_bear_trail_exit | weak_archived | 30 | 77 | 674 | 25/25 | 236/658 (35.9%) | 30.80% | -0.49% | -0.31% | -0.17 | MINIMUM_COUNT_ONLY |
| book_bear_fast_exit | weak_archived | 31 | 81 | 976 | 25/25 | 330/957 (34.5%) | 29.82% | -0.54% | -0.50% | -0.26 | MINIMUM_COUNT_ONLY |
| book_price_fast_short | weak_archived | 32 | 21 | 431 | 25/25 | 149/424 (35.1%) | 29.32% | -0.17% | -0.42% | -0.09 | MINIMUM_COUNT_ONLY |
| book_price_fast_signed | weak_archived | 33 | 20 | 453 | 25/25 | 156/446 (35.0%) | 28.95% | -0.17% | -0.02% | 0.03 | MINIMUM_COUNT_ONLY |
| book_transition_short | weak_archived | 34 | 58 | 264 | 16/25 | 95/262 (36.3%) | 28.79% | -0.35% | +1.32% | 0.12 | MINIMUM_COUNT_ONLY |
| baitoey_mjt_06_24_6h | weak_archived | 36 | 60 | 491 | 25/25 | 164/477 (34.4%) | 28.59% | -0.38% | -0.21% | 0.02 | MINIMUM_COUNT_ONLY |
| book_price_slow_short | weak_archived | 37 | 57 | 164 | 25/25 | 59/163 (36.2%) | 28.57% | -0.35% | -0.79% | -0.13 | MINIMUM_COUNT_ONLY |
| book_bear_guard | weak_archived | 39 | 83 | 802 | 25/25 | 255/786 (32.4%) | 28.16% | -0.54% | -0.26% | -0.17 | MINIMUM_COUNT_ONLY |
| book_short_analogue6 | weak_archived | 40 | 6 | 114 | 20/25 | 38/113 (33.6%) | 28.16% | +0.23% | -0.07% | -0.03 | MINIMUM_COUNT_ONLY |
| baitoey_mjt_12_48_6h | weak_archived | 41 | 55 | 351 | 25/25 | 115/345 (33.3%) | 27.99% | -0.34% | -0.10% | -0.01 | MINIMUM_COUNT_ONLY |
| baitoey_mjt_24_96_6h | weak_archived | 42 | 13 | 217 | 25/25 | 73/215 (34.0%) | 27.72% | -0.13% | +0.89% | 0.06 | MINIMUM_COUNT_ONLY |
| book_short_ridge6 | weak_archived | 43 | 12 | 31 | 8/25 | 14/31 (45.2%) | 27.59% | -0.13% | -0.01% | -0.01 | MINIMUM_COUNT_ONLY |
| book_price_channel_short | weak_archived | 44 | 44 | 390 | 25/25 | 126/384 (32.8%) | 27.42% | -0.30% | -0.75% | -0.14 | MINIMUM_COUNT_ONLY |
| book_bear_trend_control | weak_archived | 45 | 45 | 553 | 25/25 | 176/545 (32.3%) | 27.20% | -0.30% | -0.17% | -0.13 | MINIMUM_COUNT_ONLY |
| book_short_rebound | weak_archived | 46 | 17 | 265 | 25/25 | 89/265 (33.6%) | 26.99% | -0.16% | -0.31% | 0.02 | MINIMUM_COUNT_ONLY |
| book_price_slow_signed | weak_archived | 47 | 47 | 166 | 25/25 | 57/165 (34.5%) | 26.79% | -0.31% | -0.35% | 0.00 | MINIMUM_COUNT_ONLY |
| baitoey_mjt_12_48_d | weak_archived | 48 | 50 | 253 | 25/25 | 92/253 (36.4%) | 26.70% | -0.32% | +1.00% | 0.06 | MINIMUM_COUNT_ONLY |
| book_short_shock_fade | weak_archived | 49 | 7 | 22 | 11/25 | 9/19 (47.4%) | 26.67% | +0.18% | +0.02% | 0.01 | INSUFFICIENT |
| baitoey_e20_out10 | weak_archived | 51 | 43 | 152 | 18/25 | 53/152 (34.9%) | 26.50% | -0.29% | +0.43% | 0.08 | MINIMUM_COUNT_ONLY |
| baitoey_mjt_06_24_d | weak_archived | 52 | 53 | 292 | 25/25 | 100/292 (34.2%) | 26.41% | -0.33% | +0.54% | 0.05 | MINIMUM_COUNT_ONLY |
| book_bear_pullback | weak_archived | 53 | 52 | 239 | 24/25 | 76/236 (32.2%) | 26.09% | -0.33% | -0.11% | -0.09 | MINIMUM_COUNT_ONLY |
| baitoey_e20_out15 | weak_archived | 54 | 41 | 151 | 18/25 | 52/151 (34.4%) | 26.04% | -0.29% | +0.27% | 0.07 | MINIMUM_COUNT_ONLY |
| book_price_channel_signed | weak_archived | 55 | 59 | 449 | 25/25 | 133/446 (29.8%) | 25.32% | -0.38% | -0.72% | -0.05 | MINIMUM_COUNT_ONLY |
| baitoey_mjt_24_96_d | weak_archived | 56 | 25 | 193 | 25/25 | 65/193 (33.7%) | 25.00% | -0.19% | +0.62% | 0.03 | MINIMUM_COUNT_ONLY |
| book_daily_channel | weak_archived | 57 | 51 | 232 | 18/25 | 79/232 (34.1%) | 24.77% | -0.32% | -0.04% | 0.02 | MINIMUM_COUNT_ONLY |
| book_e20combo_alt_trim | weak_archived | 58 | 88 | 156 | 19/25 | 51/156 (32.7%) | 23.53% | -0.70% | +0.50% | 0.10 | MINIMUM_COUNT_ONLY |
| book_e20combo_alt_cash_pb | weak_archived | 59 | 40 | 125 | 16/25 | 40/125 (32.0%) | 23.33% | -0.29% | +0.60% | 0.12 | MINIMUM_COUNT_ONLY |
| book_short_trend | weak_archived | 60 | 11 | 208 | 25/25 | 62/208 (29.8%) | 23.05% | -0.12% | -0.24% | 0.02 | MINIMUM_COUNT_ONLY |
| book_e20guard_confirm | weak_archived | 61 | 90 | 155 | 19/25 | 50/155 (32.3%) | 22.94% | -0.72% | +0.49% | 0.11 | MINIMUM_COUNT_ONLY |
| book_e20guard_pullback | weak_archived | 62 | 42 | 128 | 17/25 | 40/128 (31.2%) | 21.97% | -0.29% | +0.56% | 0.11 | MINIMUM_COUNT_ONLY |
| book_e20combo_alt_cash | weak_archived | 63 | 89 | 142 | 17/25 | 44/142 (31.0%) | 20.99% | -0.72% | +0.58% | 0.11 | MINIMUM_COUNT_ONLY |
| pol_switch_vt_tl | weak_archived | 64 | 65 | 69 | 8/25 | 23/69 (33.3%) | 20.78% | -0.41% | +0.77% | 0.14 | MINIMUM_COUNT_ONLY |
| pol_switch_vtm_tl | weak_archived | 65 | 66 | 69 | 8/25 | 23/69 (33.3%) | 20.78% | -0.41% | +0.51% | 0.14 | MINIMUM_COUNT_ONLY |
| book_e20combo_alt_half_cash | weak_archived | 66 | 91 | 141 | 17/25 | 43/141 (30.5%) | 20.32% | -0.75% | +0.50% | 0.07 | MINIMUM_COUNT_ONLY |
| baitoey_e20_shortc_alts | weak_archived | 67 | 62 | 134 | 13/25 | 41/134 (30.6%) | 19.70% | -0.39% | +0.85% | 0.12 | MINIMUM_COUNT_ONLY |
| baitoey_e20_shortc_sol | weak_archived | 68 | 54 | 109 | 13/25 | 34/109 (31.2%) | 19.05% | -0.34% | +1.43% | 0.14 | MINIMUM_COUNT_ONLY |
| baitoey_e20_btcs_b2 | weak_archived | 69 | 87 | 112 | 19/25 | 33/112 (29.5%) | 18.27% | -0.56% | +0.16% | 0.11 | MINIMUM_COUNT_ONLY |
| baitoey_e20_btcs_a2 | weak_archived | 70 | 64 | 110 | 17/25 | 32/110 (29.1%) | 17.91% | -0.41% | +0.33% | 0.08 | MINIMUM_COUNT_ONLY |
| pol_switch_rmax_tl | weak_archived | 71 | 84 | 67 | 8/25 | 21/67 (31.3%) | 17.72% | -0.55% | +1.75% | 0.09 | MINIMUM_COUNT_ONLY |
| pol_switch_rt | weak_archived | 72 | 85 | 67 | 8/25 | 21/67 (31.3%) | 17.72% | -0.55% | +0.13% | 0.06 | MINIMUM_COUNT_ONLY |
| baitoey_btc_short_b | weak_archived | 73 | 29 | 15 | 12/25 | 5/15 (33.3%) | 16.67% | -0.22% | -0.53% | -0.07 | INSUFFICIENT |
| book_cashshort_pullback | weak_archived | 74 | 49 | 38 | 8/25 | 11/38 (28.9%) | 16.67% | -0.32% | +2.76% | 0.23 | MINIMUM_COUNT_ONLY |
| baitoey_e20_shortc_eth | weak_archived | 75 | 76 | 103 | 13/25 | 26/103 (25.2%) | 15.58% | -0.49% | +0.77% | 0.13 | MINIMUM_COUNT_ONLY |
| baitoey_ovl_evt_e20 | weak_archived | 76 | 82 | 106 | 13/25 | 29/106 (27.4%) | 15.38% | -0.54% | +0.79% | 0.12 | MINIMUM_COUNT_ONLY |
| book_e20combo_brk_cash | weak_archived | 77 | 92 | 118 | 15/25 | 30/118 (25.4%) | 15.15% | -0.78% | +1.05% | 0.13 | MINIMUM_COUNT_ONLY |
| baitoey_ovl_altbtc_b_e20 | weak_archived | 78 | 72 | 103 | 13/25 | 28/103 (27.2%) | 15.12% | -0.49% | +0.66% | 0.12 | MINIMUM_COUNT_ONLY |
| baitoey_ovl_brk_e20 | weak_archived | 79 | 73 | 103 | 13/25 | 28/103 (27.2%) | 15.12% | -0.49% | +1.06% | 0.13 | MINIMUM_COUNT_ONLY |
| baitoey_ovl_evtctl_e20 | weak_archived | 80 | 74 | 103 | 13/25 | 28/103 (27.2%) | 15.12% | -0.49% | +0.70% | 0.13 | MINIMUM_COUNT_ONLY |
| pol_switch_vt_tl_e20v45 | weak_archived | 81 | 75 | 103 | 13/25 | 28/103 (27.2%) | 15.12% | -0.49% | +0.74% | 0.12 | MINIMUM_COUNT_ONLY |
| baitoey_e20_btcs_a | weak_archived | 82 | 69 | 104 | 13/25 | 29/104 (27.9%) | 14.89% | -0.46% | +0.54% | 0.12 | MINIMUM_COUNT_ONLY |
| baitoey_e20_btcs_d | weak_archived | 83 | 70 | 104 | 13/25 | 29/104 (27.9%) | 14.89% | -0.46% | +0.54% | 0.12 | MINIMUM_COUNT_ONLY |
| baitoey_ovl_altbtc_a_e20 | weak_archived | 85 | 80 | 103 | 13/25 | 27/103 (26.2%) | 14.61% | -0.53% | +0.68% | 0.09 | MINIMUM_COUNT_ONLY |
| baitoey_btc_short_b2 | weak_archived | 86 | 61 | 22 | 18/25 | 7/22 (31.8%) | 14.29% | -0.38% | -0.08% | 0.02 | INSUFFICIENT |
| baitoey_e20_btcs_c | weak_archived | 87 | 86 | 102 | 13/25 | 27/102 (26.5%) | 14.06% | -0.56% | +0.84% | 0.13 | MINIMUM_COUNT_ONLY |
| baitoey_e20_btcs_b | weak_archived | 88 | 78 | 102 | 13/25 | 28/102 (27.5%) | 14.00% | -0.49% | +0.31% | 0.12 | MINIMUM_COUNT_ONLY |
| baitoey_btc_short_a2 | weak_archived | 89 | 8 | 20 | 17/25 | 6/20 (30.0%) | 12.50% | +0.15% | -0.12% | -0.01 | INSUFFICIENT |
| book_cashshort_confirm | weak_archived | 90 | 93 | 62 | 12/25 | 19/62 (30.6%) | 8.57% | -1.21% | +2.57% | 0.22 | MINIMUM_COUNT_ONLY |
| baitoey_btc_short_a | weak_archived | 91 | 1 | 4 | 4/25 | 2/4 (50.0%) | 0.00% | +1.43% | -0.14% | -0.02 | INSUFFICIENT |
| baitoey_btc_short_c | weak_archived | 92 | 33 | 19 | 15/25 | 2/19 (10.5%) | 0.00% | -0.23% | -0.19% | -0.01 | INSUFFICIENT |
| baitoey_btc_short_d | weak_archived | 93 | 2 | 4 | 4/25 | 2/4 (50.0%) | 0.00% | +1.43% | -0.14% | -0.02 | INSUFFICIENT |
| baitoey_mr_4h | weak_archived | — | — | 0 | 0/25 | 0/0 (—) | — | — | -0.27% | 0.11 | INSUFFICIENT |
| baitoey_mr_bbrsi | weak_archived | — | — | 0 | 0/25 | 0/0 (—) | — | — | -0.26% | 0.08 | INSUFFICIENT |
| baitoey_ovl_altbtc_a_dual | weak_archived | — | — | 0 | 0/25 | 0/0 (—) | — | — | +1.70% | 0.21 | INSUFFICIENT |
| baitoey_ovl_altbtc_b_dual | weak_archived | — | — | 0 | 0/25 | 0/0 (—) | — | — | +1.49% | 0.29 | INSUFFICIENT |
| baitoey_ovl_brk_dual | weak_archived | — | — | 0 | 0/25 | 0/0 (—) | — | — | +2.94% | 0.23 | INSUFFICIENT |
| baitoey_ovl_evt_dual | weak_archived | — | — | 0 | 0/25 | 0/0 (—) | — | — | +2.35% | 0.18 | INSUFFICIENT |
| baitoey_ovl_evtctl_dual | weak_archived | — | — | 0 | 0/25 | 0/0 (—) | — | — | +2.63% | 0.20 | INSUFFICIENT |
| baitoey_rot_max | weak_archived | — | — | 0 | 0/25 | 0/0 (—) | — | — | +2.84% | 0.16 | INSUFFICIENT |
| baitoey_vt_dual | weak_archived | — | — | 0 | 0/25 | 0/0 (—) | — | — | +2.95% | 0.23 | INSUFFICIENT |
| baitoey_vt_mom | weak_archived | — | — | 0 | 0/25 | 0/0 (—) | — | — | +2.00% | 0.21 | INSUFFICIENT |
| book_coin_trend | weak_archived | — | — | 0 | 0/25 | 0/0 (—) | — | — | +0.61% | 0.09 | INSUFFICIENT |
| book_orch | weak_archived | — | — | 0 | 0/25 | 0/0 (—) | — | — | +2.26% | 0.23 | INSUFFICIENT |
| book_vt_breadth | weak_archived | — | — | 0 | 0/25 | 0/0 (—) | — | — | +2.22% | 0.14 | INSUFFICIENT |
| book_vt_dual | weak_archived | — | — | 0 | 0/25 | 0/0 (—) | — | — | +2.86% | 0.21 | INSUFFICIENT |
| book_vt_top4 | weak_archived | — | — | 0 | 0/25 | 0/0 (—) | — | — | +2.12% | 0.21 | INSUFFICIENT |
| pol_abl_shock | weak_archived | — | — | 0 | 0/25 | 0/0 (—) | — | — | +1.44% | 0.20 | INSUFFICIENT |
| pol_combo_rb | weak_archived | — | — | 0 | 0/25 | 0/0 (—) | — | — | +1.30% | 0.18 | INSUFFICIENT |
| pol_mr_cap | weak_archived | — | — | 0 | 0/25 | 0/0 (—) | — | — | -0.99% | 0.13 | INSUFFICIENT |
| pol_switch_rc | weak_archived | — | — | 0 | 0/25 | 0/0 (—) | — | — | +0.77% | 0.08 | INSUFFICIENT |
| pol_switch_rmax_mr | weak_archived | — | — | 0 | 0/25 | 0/0 (—) | — | — | +1.32% | 0.06 | INSUFFICIENT |
| pol_switch_rot_mr | weak_archived | — | — | 0 | 0/25 | 0/0 (—) | — | — | +0.56% | 0.08 | INSUFFICIENT |
| pol_vt_mvr | weak_archived | — | — | 0 | 0/25 | 0/0 (—) | — | — | +1.46% | 0.20 | INSUFFICIENT |
| team_btc_hold | weak_archived | — | — | 0 | 0/25 | 0/0 (—) | — | — | +1.42% | 0.22 | INSUFFICIENT |
| team_cash | weak_archived | — | — | 0 | 0/25 | 0/0 (—) | — | — | -0.00% | -0.00 | INSUFFICIENT |
| team_ew_daily | weak_archived | — | — | 0 | 0/25 | 0/0 (—) | — | — | +0.51% | 0.14 | INSUFFICIENT |
| team_rot_ew | weak_archived | — | — | 0 | 0/25 | 0/0 (—) | — | — | +1.20% | 0.12 | INSUFFICIENT |
| team_rot_iv | weak_archived | — | — | 0 | 0/25 | 0/0 (—) | — | — | +0.72% | 0.13 | INSUFFICIENT |
| team_trend_2 | weak_archived | — | — | 0 | 0/25 | 0/0 (—) | — | — | +0.51% | 0.15 | INSUFFICIENT |
| book_short_analogue12 | weak_fresh_btc | 2 | 20 | 367 | 23/25 | 160/355 (45.1%) | 41.10% | +0.02% | -0.09% | -0.05 | MINIMUM_COUNT_ONLY |
| pol_combo_rtt | weak_fresh_btc | 4 | 6 | 189 | 23/25 | 92/189 (48.7%) | 39.60% | +0.20% | +0.75% | 0.12 | MINIMUM_COUNT_ONLY |
| baitoey_e20_out10 | weak_fresh_btc | 9 | 11 | 231 | 21/25 | 109/231 (47.2%) | 37.86% | +0.14% | +0.88% | 0.08 | MINIMUM_COUNT_ONLY |
| baitoey_e20_out15 | weak_fresh_btc | 10 | 12 | 231 | 21/25 | 109/231 (47.2%) | 37.86% | +0.10% | +0.77% | 0.07 | MINIMUM_COUNT_ONLY |
| pol_trend_ls | weak_fresh_btc | 12 | 7 | 273 | 23/25 | 125/273 (45.8%) | 37.70% | +0.18% | +0.14% | 0.07 | MINIMUM_COUNT_ONLY |
| baitoey_tg_mom | weak_fresh_btc | 13 | 47 | 395 | 25/25 | 167/395 (42.3%) | 37.53% | -0.20% | +0.15% | 0.05 | MINIMUM_COUNT_ONLY |
| book_price_fast_short | weak_fresh_btc | 15 | 30 | 421 | 25/25 | 175/415 (42.2%) | 37.22% | -0.12% | +0.18% | -0.09 | MINIMUM_COUNT_ONLY |
| pol_combo_all | weak_fresh_btc | 16 | 9 | 142 | 25/25 | 69/142 (48.6%) | 36.94% | +0.16% | +0.41% | 0.14 | MINIMUM_COUNT_ONLY |
| pol_combo_rt | weak_fresh_btc | 18 | 13 | 244 | 23/25 | 110/244 (45.1%) | 36.61% | +0.08% | +0.75% | 0.10 | MINIMUM_COUNT_ONLY |
| pol_mom_ss | weak_fresh_btc | 19 | 15 | 361 | 25/25 | 151/361 (41.8%) | 36.21% | +0.04% | +0.10% | 0.16 | MINIMUM_COUNT_ONLY |
| team_mom_ss25 | weak_fresh_btc | 20 | 16 | 361 | 25/25 | 151/361 (41.8%) | 36.21% | +0.04% | +0.10% | 0.16 | MINIMUM_COUNT_ONLY |
| baitoey_mjt_12_48_6h | weak_fresh_btc | 21 | 40 | 360 | 25/25 | 143/351 (40.7%) | 35.89% | -0.16% | +0.45% | -0.01 | MINIMUM_COUNT_ONLY |
| pol_combo_ms_tl | weak_fresh_btc | 22 | 10 | 336 | 25/25 | 149/336 (44.3%) | 35.88% | +0.15% | +0.12% | 0.10 | MINIMUM_COUNT_ONLY |
| book_price_slow_signed | weak_fresh_btc | 24 | 25 | 179 | 25/25 | 76/175 (43.4%) | 35.68% | -0.09% | -0.22% | 0.00 | MINIMUM_COUNT_ONLY |
| book_price_slow_short | weak_fresh_btc | 25 | 44 | 176 | 25/25 | 74/173 (42.8%) | 35.59% | -0.18% | -0.46% | -0.13 | MINIMUM_COUNT_ONLY |
| baitoey_mjt_24_96_6h | weak_fresh_btc | 26 | 18 | 233 | 25/25 | 95/228 (41.7%) | 35.52% | +0.03% | +0.73% | 0.06 | MINIMUM_COUNT_ONLY |
| book_price_fast_signed | weak_fresh_btc | 27 | 32 | 446 | 25/25 | 180/441 (40.8%) | 35.02% | -0.13% | +0.08% | 0.03 | MINIMUM_COUNT_ONLY |
| pol_switch3 | weak_fresh_btc | 28 | 87 | 42 | 4/25 | 20/41 (48.8%) | 35.00% | -0.85% | -0.56% | 0.28 | MINIMUM_COUNT_ONLY |
| pol_switch3_cap | weak_fresh_btc | 29 | 88 | 42 | 4/25 | 20/41 (48.8%) | 35.00% | -0.85% | -0.39% | 0.37 | MINIMUM_COUNT_ONLY |
| baitoey_mjt_06_24_6h | weak_fresh_btc | 31 | 50 | 510 | 25/25 | 196/498 (39.4%) | 34.52% | -0.22% | +0.15% | 0.02 | MINIMUM_COUNT_ONLY |
| book_e20combo_alt_cash | weak_fresh_btc | 32 | 39 | 203 | 19/25 | 85/203 (41.9%) | 34.25% | -0.16% | +1.09% | 0.11 | MINIMUM_COUNT_ONLY |
| book_e20combo_alt_half_cash | weak_fresh_btc | 33 | 42 | 203 | 19/25 | 85/203 (41.9%) | 33.98% | -0.17% | +0.89% | 0.07 | MINIMUM_COUNT_ONLY |
| book_short_range_fail | weak_fresh_btc | 34 | 19 | 67 | 19/25 | 30/66 (45.5%) | 33.96% | +0.02% | +0.00% | -0.00 | MINIMUM_COUNT_ONLY |
| book_bear_trail_exit | weak_fresh_btc | 35 | 73 | 655 | 25/25 | 249/644 (38.7%) | 33.79% | -0.42% | -0.17% | -0.17 | MINIMUM_COUNT_ONLY |
| book_price_channel_short | weak_fresh_btc | 36 | 49 | 385 | 25/25 | 144/378 (38.1%) | 33.60% | -0.22% | +0.02% | -0.14 | MINIMUM_COUNT_ONLY |
| book_e20combo_alt_cash_pb | weak_fresh_btc | 38 | 24 | 186 | 18/25 | 77/186 (41.4%) | 33.33% | -0.08% | +0.98% | 0.12 | MINIMUM_COUNT_ONLY |
| book_bear_fast_exit | weak_fresh_btc | 40 | 84 | 943 | 25/25 | 352/923 (38.1%) | 32.93% | -0.52% | -0.41% | -0.26 | MINIMUM_COUNT_ONLY |
| baitoey_mjt_12_48_d | weak_fresh_btc | 41 | 33 | 256 | 25/25 | 111/256 (43.4%) | 32.80% | -0.13% | +0.32% | 0.06 | MINIMUM_COUNT_ONLY |
| book_price_channel_signed | weak_fresh_btc | 42 | 59 | 447 | 25/25 | 161/441 (36.5%) | 32.68% | -0.31% | -0.42% | -0.05 | MINIMUM_COUNT_ONLY |
| book_short_volume_fade | weak_fresh_btc | 43 | 17 | 48 | 17/25 | 23/47 (48.9%) | 32.26% | +0.03% | +0.01% | 0.00 | MINIMUM_COUNT_ONLY |
| book_bear_cost_guard | weak_fresh_btc | 44 | 79 | 582 | 25/25 | 213/572 (37.2%) | 32.23% | -0.47% | -0.09% | -0.13 | MINIMUM_COUNT_ONLY |
| baitoey_mjt_06_24_d | weak_fresh_btc | 45 | 46 | 311 | 25/25 | 125/311 (40.2%) | 32.17% | -0.19% | +1.08% | 0.05 | MINIMUM_COUNT_ONLY |
| book_bear_trend_control | weak_fresh_btc | 46 | 54 | 539 | 25/25 | 188/530 (35.5%) | 31.89% | -0.29% | +0.03% | -0.13 | MINIMUM_COUNT_ONLY |
| book_e20combo_alt_trim | weak_fresh_btc | 47 | 55 | 218 | 21/25 | 87/218 (39.9%) | 31.87% | -0.29% | +0.89% | 0.10 | MINIMUM_COUNT_ONLY |
| baitoey_mjt_24_96_d | weak_fresh_btc | 48 | 26 | 204 | 25/25 | 82/204 (40.2%) | 31.56% | -0.09% | +0.56% | 0.03 | MINIMUM_COUNT_ONLY |
| book_e20guard_confirm | weak_fresh_btc | 49 | 63 | 215 | 21/25 | 84/215 (39.1%) | 31.31% | -0.34% | +0.64% | 0.11 | MINIMUM_COUNT_ONLY |
| book_e20guard_pullback | weak_fresh_btc | 50 | 36 | 189 | 19/25 | 76/189 (40.2%) | 31.25% | -0.15% | +0.65% | 0.11 | MINIMUM_COUNT_ONLY |
| book_transition_short | weak_fresh_btc | 51 | 86 | 294 | 19/25 | 115/289 (39.8%) | 31.06% | -0.55% | +0.93% | 0.12 | MINIMUM_COUNT_ONLY |
| baitoey_e20_btcs_a2 | weak_fresh_btc | 52 | 57 | 177 | 20/25 | 74/177 (41.8%) | 30.99% | -0.31% | +0.24% | 0.08 | MINIMUM_COUNT_ONLY |
| book_cashshort_confirm | weak_fresh_btc | 53 | 35 | 93 | 15/25 | 38/93 (40.9%) | 30.11% | -0.15% | +2.26% | 0.22 | MINIMUM_COUNT_ONLY |
| book_bear_breakdown | weak_fresh_btc | 54 | 71 | 445 | 25/25 | 158/441 (35.8%) | 30.08% | -0.41% | -0.00% | -0.08 | MINIMUM_COUNT_ONLY |
| book_short_shock_fade | weak_fresh_btc | 55 | 5 | 24 | 10/25 | 11/21 (52.4%) | 30.00% | +0.31% | +0.01% | 0.01 | INSUFFICIENT |
| baitoey_e20_shortc_sol | weak_fresh_btc | 56 | 61 | 181 | 17/25 | 72/181 (39.8%) | 29.94% | -0.31% | +1.09% | 0.14 | MINIMUM_COUNT_ONLY |
| book_bear_guard | weak_fresh_btc | 57 | 85 | 735 | 25/25 | 255/723 (35.3%) | 29.86% | -0.54% | -0.13% | -0.17 | MINIMUM_COUNT_ONLY |
| book_short_analogue6 | weak_fresh_btc | 58 | 48 | 128 | 22/25 | 46/127 (36.2%) | 29.75% | -0.22% | -0.07% | -0.03 | MINIMUM_COUNT_ONLY |
| book_e20combo_brk_cash | weak_fresh_btc | 59 | 66 | 192 | 19/25 | 73/192 (38.0%) | 29.65% | -0.39% | +0.89% | 0.13 | MINIMUM_COUNT_ONLY |
| baitoey_btc_short_a2 | weak_fresh_btc | 60 | 2 | 21 | 19/25 | 10/21 (47.6%) | 29.41% | +0.49% | +0.09% | -0.01 | INSUFFICIENT |
| book_cashshort_pullback | weak_fresh_btc | 64 | 89 | 68 | 11/25 | 29/68 (42.6%) | 28.57% | -0.86% | +2.19% | 0.23 | MINIMUM_COUNT_ONLY |
| book_daily_channel | weak_fresh_btc | 65 | 62 | 262 | 21/25 | 97/262 (37.0%) | 28.57% | -0.33% | +0.27% | 0.02 | MINIMUM_COUNT_ONLY |
| baitoey_e20_btcs_c | weak_fresh_btc | 66 | 78 | 171 | 17/25 | 67/171 (39.2%) | 28.39% | -0.46% | +0.59% | 0.13 | MINIMUM_COUNT_ONLY |
| baitoey_ovl_evt_e20 | weak_fresh_btc | 67 | 77 | 178 | 17/25 | 68/178 (38.2%) | 27.88% | -0.44% | +0.56% | 0.12 | MINIMUM_COUNT_ONLY |
| baitoey_ovl_evtctl_e20 | weak_fresh_btc | 68 | 68 | 175 | 17/25 | 67/175 (38.3%) | 27.83% | -0.40% | +0.42% | 0.13 | MINIMUM_COUNT_ONLY |
| pol_switch_vt_tl_e20v45 | weak_fresh_btc | 69 | 69 | 175 | 17/25 | 67/175 (38.3%) | 27.83% | -0.40% | +0.58% | 0.12 | MINIMUM_COUNT_ONLY |
| baitoey_e20_btcs_b2 | weak_fresh_btc | 70 | 81 | 180 | 23/25 | 70/180 (38.9%) | 27.78% | -0.47% | -0.19% | 0.11 | MINIMUM_COUNT_ONLY |
| baitoey_ovl_altbtc_b_e20 | weak_fresh_btc | 71 | 74 | 174 | 17/25 | 66/174 (37.9%) | 27.70% | -0.42% | +0.94% | 0.12 | MINIMUM_COUNT_ONLY |
| baitoey_ovl_brk_e20 | weak_fresh_btc | 72 | 75 | 174 | 17/25 | 66/174 (37.9%) | 27.70% | -0.42% | +0.78% | 0.13 | MINIMUM_COUNT_ONLY |
| baitoey_e20_btcs_b | weak_fresh_btc | 73 | 70 | 163 | 17/25 | 65/163 (39.9%) | 27.57% | -0.40% | +0.51% | 0.12 | MINIMUM_COUNT_ONLY |
| baitoey_ovl_altbtc_a_e20 | weak_fresh_btc | 74 | 82 | 174 | 17/25 | 65/174 (37.4%) | 27.46% | -0.48% | +1.57% | 0.09 | MINIMUM_COUNT_ONLY |
| book_bear_pullback | weak_fresh_btc | 75 | 83 | 215 | 24/25 | 77/210 (36.7%) | 27.43% | -0.49% | -0.04% | -0.09 | MINIMUM_COUNT_ONLY |
| baitoey_e20_btcs_a | weak_fresh_btc | 77 | 64 | 165 | 17/25 | 66/165 (40.0%) | 27.33% | -0.38% | +0.37% | 0.12 | MINIMUM_COUNT_ONLY |
| baitoey_e20_btcs_d | weak_fresh_btc | 78 | 65 | 165 | 17/25 | 66/165 (40.0%) | 27.33% | -0.38% | +0.37% | 0.12 | MINIMUM_COUNT_ONLY |
| baitoey_e20_shortc_alts | weak_fresh_btc | 79 | 80 | 209 | 17/25 | 77/209 (36.8%) | 26.86% | -0.47% | +0.79% | 0.12 | MINIMUM_COUNT_ONLY |
| baitoey_e20_shortc_eth | weak_fresh_btc | 80 | 72 | 176 | 17/25 | 64/176 (36.4%) | 26.32% | -0.42% | +0.46% | 0.13 | MINIMUM_COUNT_ONLY |
| book_short_breakdown | weak_fresh_btc | 81 | 1 | 32 | 10/25 | 12/27 (44.4%) | 25.00% | +1.00% | +0.62% | 0.04 | MINIMUM_COUNT_ONLY |
| book_short_ridge6 | weak_fresh_btc | 82 | 67 | 53 | 8/25 | 23/53 (43.4%) | 23.26% | -0.39% | -0.03% | -0.01 | MINIMUM_COUNT_ONLY |
| book_short_rebound | weak_fresh_btc | 83 | 53 | 274 | 25/25 | 79/274 (28.8%) | 22.63% | -0.28% | +0.07% | 0.02 | MINIMUM_COUNT_ONLY |
| baitoey_btc_short_b | weak_fresh_btc | 84 | 14 | 16 | 13/25 | 6/16 (37.5%) | 21.05% | +0.06% | +0.08% | -0.07 | INSUFFICIENT |
| book_short_trend | weak_fresh_btc | 85 | 51 | 220 | 25/25 | 60/220 (27.3%) | 20.82% | -0.23% | +0.05% | 0.02 | MINIMUM_COUNT_ONLY |
| pol_switch_vt_tl | weak_fresh_btc | 86 | 90 | 141 | 12/25 | 36/141 (25.5%) | 16.84% | -1.21% | +0.36% | 0.14 | MINIMUM_COUNT_ONLY |
| pol_switch_vtm_tl | weak_fresh_btc | 87 | 91 | 141 | 12/25 | 36/141 (25.5%) | 16.84% | -1.21% | -0.05% | 0.14 | MINIMUM_COUNT_ONLY |
| pol_switch_rmax_tl | weak_fresh_btc | 88 | 92 | 138 | 12/25 | 34/138 (24.6%) | 15.66% | -1.30% | +1.88% | 0.09 | MINIMUM_COUNT_ONLY |
| pol_switch_rt | weak_fresh_btc | 89 | 93 | 138 | 12/25 | 34/138 (24.6%) | 15.66% | -1.30% | +0.05% | 0.06 | MINIMUM_COUNT_ONLY |
| baitoey_btc_short_b2 | weak_fresh_btc | 90 | 52 | 27 | 23/25 | 8/27 (29.6%) | 14.29% | -0.23% | +0.02% | 0.02 | INSUFFICIENT |
| baitoey_btc_short_a | weak_fresh_btc | 91 | 3 | 9 | 9/25 | 3/9 (33.3%) | 10.00% | +0.37% | +0.12% | -0.02 | INSUFFICIENT |
| baitoey_btc_short_d | weak_fresh_btc | 92 | 4 | 9 | 9/25 | 3/9 (33.3%) | 10.00% | +0.37% | +0.12% | -0.02 | INSUFFICIENT |
| baitoey_btc_short_c | weak_fresh_btc | 93 | 8 | 21 | 18/25 | 5/21 (23.8%) | 9.52% | +0.16% | -0.20% | -0.01 | INSUFFICIENT |
| baitoey_mr_4h | weak_fresh_btc | — | — | 0 | 0/25 | 0/0 (—) | — | — | -0.91% | 0.11 | INSUFFICIENT |
| baitoey_mr_bbrsi | weak_fresh_btc | — | — | 0 | 0/25 | 0/0 (—) | — | — | -0.87% | 0.08 | INSUFFICIENT |
| baitoey_ovl_altbtc_a_dual | weak_fresh_btc | — | — | 0 | 0/25 | 0/0 (—) | — | — | +1.53% | 0.21 | INSUFFICIENT |
| baitoey_ovl_altbtc_b_dual | weak_fresh_btc | — | — | 0 | 0/25 | 0/0 (—) | — | — | +1.15% | 0.29 | INSUFFICIENT |
| baitoey_ovl_brk_dual | weak_fresh_btc | — | — | 0 | 0/25 | 0/0 (—) | — | — | +2.40% | 0.23 | INSUFFICIENT |
| baitoey_ovl_evt_dual | weak_fresh_btc | — | — | 0 | 0/25 | 0/0 (—) | — | — | +2.08% | 0.18 | INSUFFICIENT |
| baitoey_ovl_evtctl_dual | weak_fresh_btc | — | — | 0 | 0/25 | 0/0 (—) | — | — | +2.08% | 0.20 | INSUFFICIENT |
| baitoey_rot_max | weak_fresh_btc | — | — | 0 | 0/25 | 0/0 (—) | — | — | +2.68% | 0.16 | INSUFFICIENT |
| baitoey_vt_dual | weak_fresh_btc | — | — | 0 | 0/25 | 0/0 (—) | — | — | +2.29% | 0.23 | INSUFFICIENT |
| baitoey_vt_mom | weak_fresh_btc | — | — | 0 | 0/25 | 0/0 (—) | — | — | +1.28% | 0.21 | INSUFFICIENT |
| book_coin_trend | weak_fresh_btc | — | — | 0 | 0/25 | 0/0 (—) | — | — | +0.26% | 0.09 | INSUFFICIENT |
| book_orch | weak_fresh_btc | — | — | 0 | 0/25 | 0/0 (—) | — | — | +1.57% | 0.23 | INSUFFICIENT |
| book_vt_breadth | weak_fresh_btc | — | — | 0 | 0/25 | 0/0 (—) | — | — | +1.21% | 0.14 | INSUFFICIENT |
| book_vt_dual | weak_fresh_btc | — | — | 0 | 0/25 | 0/0 (—) | — | — | +2.17% | 0.21 | INSUFFICIENT |
| book_vt_top4 | weak_fresh_btc | — | — | 0 | 0/25 | 0/0 (—) | — | — | +1.74% | 0.21 | INSUFFICIENT |
| pol_abl_shock | weak_fresh_btc | — | — | 0 | 0/25 | 0/0 (—) | — | — | +0.95% | 0.20 | INSUFFICIENT |
| pol_combo_rb | weak_fresh_btc | — | — | 0 | 0/25 | 0/0 (—) | — | — | +0.92% | 0.18 | INSUFFICIENT |
| pol_mr_cap | weak_fresh_btc | — | — | 0 | 0/25 | 0/0 (—) | — | — | -1.29% | 0.13 | INSUFFICIENT |
| pol_switch_rc | weak_fresh_btc | — | — | 0 | 0/25 | 0/0 (—) | — | — | +0.42% | 0.08 | INSUFFICIENT |
| pol_switch_rmax_mr | weak_fresh_btc | — | — | 0 | 0/25 | 0/0 (—) | — | — | +0.81% | 0.06 | INSUFFICIENT |
| pol_switch_rot_mr | weak_fresh_btc | — | — | 0 | 0/25 | 0/0 (—) | — | — | +0.57% | 0.08 | INSUFFICIENT |
| pol_vt_mvr | weak_fresh_btc | — | — | 0 | 0/25 | 0/0 (—) | — | — | +0.53% | 0.20 | INSUFFICIENT |
| team_btc_hold | weak_fresh_btc | — | — | 0 | 0/25 | 0/0 (—) | — | — | +0.67% | 0.22 | INSUFFICIENT |
| team_cash | weak_fresh_btc | — | — | 0 | 0/25 | 0/0 (—) | — | — | -0.00% | -0.00 | INSUFFICIENT |
| team_ew_daily | weak_fresh_btc | — | — | 0 | 0/25 | 0/0 (—) | — | — | -0.83% | 0.14 | INSUFFICIENT |
| team_rot_ew | weak_fresh_btc | — | — | 0 | 0/25 | 0/0 (—) | — | — | +1.33% | 0.12 | INSUFFICIENT |
| team_rot_iv | weak_fresh_btc | — | — | 0 | 0/25 | 0/0 (—) | — | — | +0.98% | 0.13 | INSUFFICIENT |
| team_trend_2 | weak_fresh_btc | — | — | 0 | 0/25 | 0/0 (—) | — | — | +0.49% | 0.15 | INSUFFICIENT |

## Evidence strength and limits

Stronger historical replacement evidence requires the original hard gates, a positive joint conservative selection score, and at least **12 merged overlap clusters and 12 calendar quarters in every comparison context**. This requirement is not relaxed to manufacture a winner.

Uncertainty uses 20000 paired bootstrap draws across 121 model revisions. The standardized centred maximum statistic controls the simultaneous family of cash/e20 comparisons over two profiles and three horizons. It uses shared resampling so correlated models and comparisons remain paired.

Nonoverlapping selected windows can still share market regimes; nearby context windows are merged for dependence and the quarter check guards narrow calendar coverage. Bootstrap bounds remain finite-sample estimates. They do not erase prior strategy-development search, prove future profitability or provide a 90% probability of winning the remaining competition.

Evidence method: centered standardized maximum; fixed bootstrap SE. Joint family quantile: 3.2490.

Saved clusters summary:

~~~json
17
~~~

Saved contexts summary:

~~~json
6
~~~

## Test a new model and update this board

Run on the server in the feature worktree containing this implementation. Register the pure model through the project's existing model interface and place its tunable parameters in config.yaml. Check scripts/status before a heavy job and use an owned mm-book-* tmux session for a long run.

~~~bash
ssh metallurgy-server
cd /home/ubuntu/test/MiniMax/.worktrees/book-book-bear-eval
scripts/status
scripts/lock harness-book-weak-score -- nice -n 10 .venv/bin/python -B -m backtest.run --model book_NAME --score2
~~~

After a successful run, this secondary leaderboard updates automatically. It contains the latest compatible run for each model under the frozen protocol; the separate registry retains previous attempts and immutable artifacts. Repeating the same run is idempotent.

To update both the team's original scoring board and this board from one scoring run:

~~~bash
scripts/lock harness-book-weak-score -- nice -n 10 .venv/bin/python -B -m backtest.run --model book_NAME --score --score2
~~~

To rebuild this board from already published results, or import the frozen registered models:

~~~bash
scripts/lock harness-book-weak-score -- nice -n 10 .venv/bin/python -B -m backtest.scoring leaderboard2
scripts/lock harness-book-weak-score -- nice -n 10 .venv/bin/python -B -m backtest.scoring import-score2
~~~

--score keeps the original scoring rules. --score2 alone publishes this separate evaluation; it does not update the original leaderboard. Neither command deploys a model, changes the live bot, merges main or opens the holdout. A new market checkpoint requires a new frozen protocol; ordinary model scoring cannot alter the selected windows or thresholds.

## Files and provenance

| Remote path | Purpose |
|---|---|
| /home/ubuntu/test/MiniMax/results/scoring/leaderboard_2.md | This guide, ranked table and separate short diagnostics |
| /home/ubuntu/test/MiniMax/results/scoring/leaderboard_2.csv | Full numeric model-selection rows |
| /home/ubuntu/test/MiniMax/results/scoring/registry_2.jsonl | Append-only publication history |
| /home/ubuntu/test/MiniMax/results/book/20261009-weak-eval-v2/ | Frozen protocol, selected windows, data/coverage manifests, detailed diagnostics and reliability evidence |
| /home/ubuntu/test/MiniMax/results/book/20261008-regime-eval/ | Preserved earlier failed adaptive activation and original evidence |
| /home/ubuntu/test/MiniMax/results/scoring/leaderboard.md | Original team full-round leaderboard |
| /home/ubuntu/test/MiniMax/.worktrees/book-book-bear-eval/backtest/scoring/ | Book feature implementation: weak evaluation, risk, short diagnostics and publisher |

Protocol identity: 603da2948b68ee0f5c8a. Original incumbent source identity is pinned. Input manifests, cached-path compatibility and hashes are checked before publication; outputs from different checkpoints or metric definitions cannot silently share a ranking.

This is historical selection evidence for the next experiment. The actual live-account transition and future realised competition result remain unverified.
