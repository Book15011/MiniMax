# Short models against e20v45 over the rest of this round: independent test

Pre-registration: `research/baitoey/prereg/20261012-short-models-rest-of-round.md` (3c5bdd8). Start: round hour 186 (2026-10-12 06:00 UTC), e20v45 at -2.84% on Book's live-price replay (EC2 account UNVERIFIED), BTC -1.53% since the round start, 150 hours left.

- Similar past rounds: **357** of 2298, in 72 calendar months.
- Primary sample (rest of round does not overlap Book's 50 weak-market cases): **260** rounds in 61 months.
- Models tested against e20v45: **102**; Bonferroni threshold p <= 0.0010. Excluded (reference log, AGENTS rule 7 question): 18.
- Switching cost 0.20% for every model except e20v45. Final account = (1 -2.84%)(1 + R) - 1.

## Verdict (primary sample)

- Better than e20v45: **none**.
- Promising, not proven: none.

## A. Book's 13 ranked short models

| Model | Group | Rest of round: mean / median / p10 | vs e20v45: mean d (90% low) | p (one-sided) | Finish >= 0% | Median finish | BTC falls / flat / rises (median R) | HEADLINE | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| pol_switch_vt_tl_e20v45 | reference | +1.11% / -0.06% / -6.19% | +0.00% (+0.00%) | 1.000 | 27% | -2.90% | -0.55% / -0.74% / +0.87% | 0.568 | current |
| book_short_shock_fade | A ranked short | -0.20% / -0.20% / -0.21% | -1.31% (-2.40%) | 0.957 | 0% | -3.04% | -0.20% / -0.20% / -0.20% | 0.297 | no |
| book_short_volume_fade | A ranked short | -0.21% / -0.20% / -0.28% | -1.32% (-2.40%) | 0.958 | 0% | -3.04% | -0.20% / -0.20% / -0.20% | 0.303 | no |
| book_short_range_fail | A ranked short | -0.21% / -0.20% / -0.30% | -1.32% (-2.40%) | 0.958 | 0% | -3.04% | -0.20% / -0.20% / -0.20% | 0.364 | no |
| book_short_ridge6 | A ranked short | -0.22% / -0.20% / -0.32% | -1.33% (-2.41%) | 0.959 | 0% | -3.04% | -0.20% / -0.20% / -0.20% | 0.204 | no |
| book_bear_pullback | A ranked short | -0.25% / -0.23% / -0.50% | -1.36% (-2.43%) | 0.963 | 0% | -3.06% | -0.29% / -0.25% / -0.21% | 0.214 | no |
| book_short_analogue12 | A ranked short | -0.33% / -0.25% / -0.70% | -1.43% (-2.52%) | 0.970 | 0% | -3.09% | -0.21% / -0.25% / -0.33% | 0.265 | no |
| book_bear_breakdown | A ranked short | -0.26% / -0.28% / -0.68% | -1.37% (-2.44%) | 0.964 | 0% | -3.11% | -0.21% / -0.37% / -0.26% | 0.242 | no |
| book_short_analogue6 | A ranked short | -0.25% / -0.21% / -0.45% | -1.36% (-2.44%) | 0.963 | 0% | -3.04% | -0.21% / -0.21% / -0.21% | 0.270 | no |
| book_bear_cost_guard | A ranked short | -0.25% / -0.26% / -0.69% | -1.36% (-2.43%) | 0.963 | 0% | -3.10% | -0.17% / -0.34% / -0.28% | 0.246 | no |
| book_bear_guard | A ranked short | -0.27% / -0.30% / -0.71% | -1.38% (-2.46%) | 0.965 | 0% | -3.13% | -0.15% / -0.36% / -0.31% | 0.227 | no |
| book_bear_trend_control | A ranked short | -0.20% / -0.40% / -0.81% | -1.31% (-2.41%) | 0.954 | 1% | -3.23% | +0.12% / -0.42% / -0.48% | 0.261 | no |
| book_bear_trail_exit | A ranked short | -0.27% / -0.30% / -0.65% | -1.38% (-2.45%) | 0.964 | 0% | -3.13% | -0.24% / -0.37% / -0.28% | 0.225 | no |
| book_bear_fast_exit | A ranked short | -0.36% / -0.38% / -0.71% | -1.47% (-2.54%) | 0.973 | 0% | -3.21% | -0.44% / -0.42% / -0.29% | 0.183 | no |

## C e20v45 + add-on (top 10 of 23 by mean d)

| Model | Group | Rest of round: mean / median / p10 | vs e20v45: mean d (90% low) | p (one-sided) | Finish >= 0% | Median finish | BTC falls / flat / rises (median R) | HEADLINE | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| pol_switch_vt_tl_e20v45 | reference | +1.11% / -0.06% / -6.19% | +0.00% (+0.00%) | 1.000 | 27% | -2.90% | -0.55% / -0.74% / +0.87% | 0.568 | current |
| baitoey_e20_shortc_alts | C e20v45 + add-on | +1.13% / -0.21% / -7.00% | +0.02% (-0.20%) | 0.458 | 31% | -3.04% | +0.86% / -1.15% / +0.53% | 0.559 | no |
| baitoey_e20_btcs_c | C e20v45 + add-on | +1.02% / -0.26% / -6.84% | -0.08% (-0.30%) | 0.700 | 30% | -3.09% | +0.22% / -1.24% / +0.46% | 0.548 | no |
| baitoey_e20_btcs_a | C e20v45 + add-on | +1.00% / -0.54% / -6.78% | -0.11% (-0.32%) | 0.751 | 28% | -3.36% | +0.06% / -1.26% / +0.46% | 0.544 | no |
| baitoey_e20_btcs_d | C e20v45 + add-on | +0.97% / -0.54% / -6.78% | -0.13% (-0.34%) | 0.788 | 28% | -3.36% | +0.06% / -1.26% / +0.46% | 0.544 | no |
| baitoey_e20_shortc_sol | C e20v45 + add-on | +0.93% / -0.24% / -7.41% | -0.17% (-0.39%) | 0.848 | 30% | -3.07% | +0.14% / -0.90% / -0.24% | 0.533 | no |
| baitoey_ovl_brk_e20 | C e20v45 + add-on | +0.92% / -0.31% / -6.33% | -0.19% (-0.25%) | 1.000 | 26% | -3.14% | -0.75% / -0.94% / +1.22% | 0.571 | no |
| book_e20combo_brk_cash | C e20v45 + add-on | +0.91% / -0.31% / -6.33% | -0.19% (-0.26%) | 1.000 | 26% | -3.14% | -0.75% / -0.94% / +1.22% | 0.570 | no |
| baitoey_ovl_evtctl_e20 | C e20v45 + add-on | +0.89% / -0.38% / -6.49% | -0.22% (-0.24%) | 1.000 | 27% | -3.21% | -0.75% / -0.92% / +0.67% | 0.547 | no |
| baitoey_e20_btcs_a2 | C e20v45 + add-on | +0.89% / -0.45% / -6.88% | -0.22% (-0.47%) | 0.860 | 28% | -3.27% | +0.19% / -1.10% / +0.66% | 0.537 | no |
| book_e20guard_pullback | C e20v45 + add-on | +0.88% / -0.38% / -6.38% | -0.23% (-0.26%) | 1.000 | 26% | -3.21% | -0.75% / -0.94% / +0.67% | 0.547 | no |

## B short or long/short (top 10 of 36 by mean d)

| Model | Group | Rest of round: mean / median / p10 | vs e20v45: mean d (90% low) | p (one-sided) | Finish >= 0% | Median finish | BTC falls / flat / rises (median R) | HEADLINE | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| pol_switch_vt_tl_e20v45 | reference | +1.11% / -0.06% / -6.19% | +0.00% (+0.00%) | 1.000 | 27% | -2.90% | -0.55% / -0.74% / +0.87% | 0.568 | current |
| pol_switch_rmax_tl | B short or long/short | +0.56% / -0.39% / -7.44% | -0.55% (-1.10%) | 0.886 | 25% | -3.22% | -0.66% / -0.25% / -0.50% | 0.491 | no |
| book_cashshort_pullback | B short or long/short | +0.49% / -1.08% / -6.39% | -0.62% (-1.40%) | 0.858 | 25% | -3.89% | -5.02% / -1.34% / +4.12% | 0.567 | no |
| book_cashshort_confirm | B short or long/short | +0.48% / -1.07% / -6.64% | -0.63% (-1.43%) | 0.855 | 25% | -3.88% | -4.48% / -1.28% / +4.47% | 0.577 | no |
| baitoey_mjt_24_96_d | B short or long/short | +0.44% / -0.32% / -5.63% | -0.67% (-1.58%) | 0.830 | 23% | -3.15% | -0.27% / -0.98% / +0.33% | 0.351 | no |
| baitoey_mjt_24_96_6h | B short or long/short | +0.39% / -0.73% / -5.63% | -0.72% (-1.59%) | 0.858 | 21% | -3.55% | -0.16% / -1.65% / +0.91% | 0.341 | no |
| baitoey_mjt_12_48_d | B short or long/short | +0.33% / -0.80% / -6.94% | -0.78% (-1.83%) | 0.832 | 25% | -3.62% | -0.04% / -1.40% / +0.13% | 0.341 | no |
| book_price_slow_signed | B short or long/short | +0.31% / -0.33% / -3.74% | -0.80% (-1.76%) | 0.861 | 20% | -3.16% | +0.58% / -1.41% / -0.20% | 0.299 | no |
| book_transition_short | B short or long/short | +0.31% / -1.23% / -7.07% | -0.80% (-1.60%) | 0.906 | 24% | -4.04% | -4.32% / -1.54% / +3.53% | 0.500 | no |
| baitoey_tg_mom | B short or long/short | +0.23% / -0.32% / -1.91% | -0.88% (-1.74%) | 0.919 | 8% | -3.15% | -0.21% / -0.58% / +0.29% | 0.374 | no |
| baitoey_mjt_12_48_6h | B short or long/short | +0.23% / -0.78% / -5.80% | -0.88% (-1.85%) | 0.879 | 26% | -3.60% | -0.80% / -1.24% / +0.46% | 0.314 | no |

## D other (top 10 of 28 by mean d)

| Model | Group | Rest of round: mean / median / p10 | vs e20v45: mean d (90% low) | p (one-sided) | Finish >= 0% | Median finish | BTC falls / flat / rises (median R) | HEADLINE | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| pol_switch_vt_tl_e20v45 | reference | +1.11% / -0.06% / -6.19% | +0.00% (+0.00%) | 1.000 | 27% | -2.90% | -0.55% / -0.74% / +0.87% | 0.568 | current |
| book_vt_top4 | D other | +1.15% / +0.06% / -7.37% | +0.04% (-0.85%) | 0.487 | 32% | -2.78% | -6.10% / -0.30% / +5.71% | 0.572 | no |
| book_vt_breadth | D other | +0.81% / -0.65% / -3.81% | -0.30% (-1.04%) | 0.716 | 22% | -3.47% | -2.70% / -0.76% / +3.26% | 0.516 | no |
| book_orch | D other | +0.80% / -0.29% / -7.46% | -0.30% (-1.18%) | 0.682 | 29% | -3.12% | -5.93% / -0.57% / +5.96% | 0.617 | no |
| baitoey_rot_max | D other | +0.76% / +0.19% / -11.72% | -0.35% (-1.55%) | 0.653 | 39% | -2.65% | -9.20% / -1.51% / +6.81% | 0.546 | no |
| baitoey_vt_mom | D other | +0.73% / -0.34% / -7.81% | -0.37% (-1.26%) | 0.715 | 30% | -3.17% | -6.31% / -0.54% / +5.80% | 0.609 | no |
| pol_vt_mvr | D other | +0.73% / -0.37% / -5.47% | -0.38% (-1.25%) | 0.729 | 28% | -3.20% | -3.83% / -0.52% / +3.89% | 0.528 | no |
| baitoey_ovl_evtctl_dual | D other | +0.70% / -0.83% / -6.65% | -0.41% (-1.30%) | 0.739 | 29% | -3.65% | -5.15% / -1.04% / +4.68% | 0.588 | no |
| baitoey_vt_dual | D other | +0.66% / -0.91% / -6.65% | -0.45% (-1.33%) | 0.757 | 29% | -3.72% | -5.14% / -1.18% / +4.68% | 0.587 | no |
| book_vt_dual | D other | +0.66% / -0.85% / -4.48% | -0.45% (-1.16%) | 0.807 | 24% | -3.67% | -3.22% / -0.94% / +3.21% | 0.532 | no |
| pol_abl_shock | D other | +0.62% / -0.39% / -8.19% | -0.48% (-1.40%) | 0.760 | 30% | -3.22% | -6.31% / -0.54% / +5.79% | 0.607 | no |

## References

| Model | Group | Rest of round: mean / median / p10 | vs e20v45: mean d (90% low) | p (one-sided) | Finish >= 0% | Median finish | BTC falls / flat / rises (median R) | HEADLINE | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| pol_switch_vt_tl_e20v45 | reference | +1.11% / -0.06% / -6.19% | +0.00% (+0.00%) | 1.000 | 27% | -2.90% | -0.55% / -0.74% / +0.87% | 0.568 | current |
| team_cash | reference | -0.20% / -0.20% / -0.21% | -1.31% (-2.39%) | 0.957 | 0% | -3.04% | -0.21% / -0.20% / -0.19% | 0.372 | no |
| team_btc_hold | reference | +0.79% / +0.18% / -6.99% | -0.31% (-1.35%) | 0.655 | 29% | -2.66% | -5.18% / -0.16% / +6.09% | 0.478 | no |

## Top 10 overall by mean d

| Model | Group | Rest of round: mean / median / p10 | vs e20v45: mean d (90% low) | p (one-sided) | Finish >= 0% | Median finish | BTC falls / flat / rises (median R) | HEADLINE | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| pol_switch_vt_tl_e20v45 | reference | +1.11% / -0.06% / -6.19% | +0.00% (+0.00%) | 1.000 | 27% | -2.90% | -0.55% / -0.74% / +0.87% | 0.568 | current |
| book_vt_top4 | D other | +1.15% / +0.06% / -7.37% | +0.04% (-0.85%) | 0.487 | 32% | -2.78% | -6.10% / -0.30% / +5.71% | 0.572 | no |
| baitoey_e20_shortc_alts | C e20v45 + add-on | +1.13% / -0.21% / -7.00% | +0.02% (-0.20%) | 0.458 | 31% | -3.04% | +0.86% / -1.15% / +0.53% | 0.559 | no |
| baitoey_e20_btcs_c | C e20v45 + add-on | +1.02% / -0.26% / -6.84% | -0.08% (-0.30%) | 0.700 | 30% | -3.09% | +0.22% / -1.24% / +0.46% | 0.548 | no |
| baitoey_e20_btcs_a | C e20v45 + add-on | +1.00% / -0.54% / -6.78% | -0.11% (-0.32%) | 0.751 | 28% | -3.36% | +0.06% / -1.26% / +0.46% | 0.544 | no |
| baitoey_e20_btcs_d | C e20v45 + add-on | +0.97% / -0.54% / -6.78% | -0.13% (-0.34%) | 0.788 | 28% | -3.36% | +0.06% / -1.26% / +0.46% | 0.544 | no |
| baitoey_e20_shortc_sol | C e20v45 + add-on | +0.93% / -0.24% / -7.41% | -0.17% (-0.39%) | 0.848 | 30% | -3.07% | +0.14% / -0.90% / -0.24% | 0.533 | no |
| baitoey_ovl_brk_e20 | C e20v45 + add-on | +0.92% / -0.31% / -6.33% | -0.19% (-0.25%) | 1.000 | 26% | -3.14% | -0.75% / -0.94% / +1.22% | 0.571 | no |
| book_e20combo_brk_cash | C e20v45 + add-on | +0.91% / -0.31% / -6.33% | -0.19% (-0.26%) | 1.000 | 26% | -3.14% | -0.75% / -0.94% / +1.22% | 0.570 | no |
| baitoey_ovl_evtctl_e20 | C e20v45 + add-on | +0.89% / -0.38% / -6.49% | -0.22% (-0.24%) | 1.000 | 27% | -3.21% | -0.75% / -0.92% / +0.67% | 0.547 | no |
| baitoey_e20_btcs_a2 | C e20v45 + add-on | +0.89% / -0.45% / -6.88% | -0.22% (-0.47%) | 0.860 | 28% | -3.27% | +0.19% / -1.10% / +0.66% | 0.537 | no |

## Context: all similar rounds (secondary sample)

Better: none. Promising: none.

| Model | Group | Rest of round: mean / median / p10 | vs e20v45: mean d (90% low) | p (one-sided) | Finish >= 0% | Median finish | BTC falls / flat / rises (median R) | HEADLINE | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| pol_switch_vt_tl_e20v45 | reference | +1.12% / -0.04% / -7.04% | +0.00% (+0.00%) | 1.000 | 28% | -2.88% | -0.92% / -0.49% / +2.60% | 0.568 | current |
| book_short_shock_fade | A ranked short | -0.20% / -0.20% / -0.22% | -1.32% (-2.22%) | 0.979 | 0% | -3.04% | -0.20% / -0.20% / -0.20% | 0.297 | no |
| book_short_volume_fade | A ranked short | -0.21% / -0.20% / -0.27% | -1.33% (-2.23%) | 0.980 | 0% | -3.04% | -0.20% / -0.20% / -0.20% | 0.303 | no |
| book_short_range_fail | A ranked short | -0.21% / -0.20% / -0.30% | -1.33% (-2.23%) | 0.980 | 0% | -3.04% | -0.20% / -0.20% / -0.20% | 0.364 | no |
| book_short_ridge6 | A ranked short | -0.22% / -0.20% / -0.29% | -1.34% (-2.24%) | 0.980 | 0% | -3.04% | -0.20% / -0.20% / -0.20% | 0.204 | no |
| book_bear_pullback | A ranked short | -0.24% / -0.24% / -0.46% | -1.36% (-2.25%) | 0.982 | 0% | -3.07% | -0.28% / -0.27% / -0.21% | 0.214 | no |
| book_short_analogue12 | A ranked short | -0.31% / -0.24% / -0.64% | -1.43% (-2.32%) | 0.986 | 0% | -3.07% | -0.22% / -0.23% / -0.29% | 0.265 | no |
| book_bear_breakdown | A ranked short | -0.25% / -0.28% / -0.65% | -1.37% (-2.26%) | 0.983 | 0% | -3.11% | -0.16% / -0.37% / -0.27% | 0.242 | no |
| book_short_analogue6 | A ranked short | -0.24% / -0.20% / -0.42% | -1.36% (-2.26%) | 0.983 | 0% | -3.04% | -0.20% / -0.20% / -0.21% | 0.270 | no |
| book_bear_cost_guard | A ranked short | -0.25% / -0.27% / -0.61% | -1.37% (-2.26%) | 0.982 | 0% | -3.11% | -0.13% / -0.37% / -0.28% | 0.246 | no |
| book_bear_guard | A ranked short | -0.27% / -0.31% / -0.62% | -1.39% (-2.28%) | 0.984 | 0% | -3.14% | -0.15% / -0.37% / -0.31% | 0.227 | no |
| book_bear_trend_control | A ranked short | -0.19% / -0.40% / -0.80% | -1.31% (-2.21%) | 0.975 | 1% | -3.23% | +0.17% / -0.45% / -0.47% | 0.261 | no |
| book_bear_trail_exit | A ranked short | -0.27% / -0.30% / -0.62% | -1.39% (-2.29%) | 0.984 | 0% | -3.13% | -0.22% / -0.37% / -0.29% | 0.225 | no |
| book_bear_fast_exit | A ranked short | -0.37% / -0.39% / -0.71% | -1.50% (-2.39%) | 0.991 | 0% | -3.22% | -0.45% / -0.43% / -0.30% | 0.183 | no |
| book_vt_top4 | D other | +1.25% / +0.36% / -7.60% | +0.13% (-0.55%) | 0.406 | 34% | -2.49% | -6.38% / +0.15% / +5.39% | 0.572 | no |
| baitoey_e20_shortc_alts | C e20v45 + add-on | +1.10% / -0.24% / -7.82% | -0.02% (-0.19%) | 0.563 | 31% | -3.07% | -0.39% / -0.84% / +1.79% | 0.559 | no |
| book_vt_dual | D other | +1.05% / -0.25% / -4.53% | -0.07% (-0.61%) | 0.567 | 27% | -3.09% | -3.26% / -0.78% / +3.54% | 0.532 | no |
| baitoey_vt_dual | D other | +1.04% / -0.30% / -6.57% | -0.08% (-0.76%) | 0.567 | 31% | -3.13% | -4.91% / -0.90% / +4.58% | 0.587 | no |
| baitoey_ovl_evtctl_dual | D other | +1.04% / -0.30% / -6.60% | -0.08% (-0.76%) | 0.571 | 32% | -3.13% | -5.08% / -0.77% / +4.62% | 0.588 | no |

## Notes

- Skipped: none.
- Rounds that start on consecutive days overlap, so the effective sample is far smaller than the round count; the bootstrap resamples whole calendar months for that reason.
- Full tables: `primary.csv`, `all_similar.csv` in this folder.
