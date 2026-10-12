# Short models against book_e20combo_alt_half_cash over the rest of this round: independent test

Pre-registration: `research/baitoey/prereg/20261012-short-models-rest-of-round.md` (3c5bdd8) + amendment 1 (b52de31). Baseline: `book_e20combo_alt_half_cash`. Start: round hour 186 (2026-10-12 06:00 UTC), account at -3.80%, BTC -1.53% since the round start, 150 hours left.

- Similar past rounds: **346** of 2298, in 70 calendar months.
- Primary sample (rest of round does not overlap Book's 50 weak-market cases): **231** rounds in 59 months.
- Models tested against the baseline: **102**; Bonferroni threshold p <= 0.0010. Excluded (reference log, AGENTS rule 7 question): 18.
- Switching cost 0.20% for every model except the baseline. Final account = (1 -3.80%)(1 + R) - 1.

## Verdict (primary sample)

- Better than book_e20combo_alt_half_cash: **none**.
- Promising, not proven: none.

## A. Book's 13 ranked short models

| Model | Group | Rest of round: mean / median / p10 | vs baseline: mean d (90% low) | p (one-sided) | Finish >= 0% | Median finish | BTC falls / flat / rises (median R) | HEADLINE | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| book_e20combo_alt_half_cash | reference | +0.96% / +0.04% / -4.70% | +0.00% (+0.00%) | 1.000 | 22% | -3.76% | +1.18% / -0.71% / +1.90% | 0.443 | baseline |
| book_short_shock_fade | A ranked short | -0.20% / -0.20% / -0.21% | -1.16% (-1.95%) | 0.976 | 0% | -3.99% | -0.20% / -0.20% / -0.20% | 0.297 | no |
| book_short_volume_fade | A ranked short | -0.21% / -0.20% / -0.28% | -1.17% (-1.95%) | 0.976 | 0% | -3.99% | -0.20% / -0.20% / -0.20% | 0.303 | no |
| book_short_range_fail | A ranked short | -0.21% / -0.20% / -0.30% | -1.17% (-1.95%) | 0.976 | 0% | -3.99% | -0.20% / -0.20% / -0.20% | 0.364 | no |
| book_short_ridge6 | A ranked short | -0.23% / -0.20% / -0.33% | -1.19% (-1.97%) | 0.978 | 0% | -4.00% | -0.20% / -0.20% / -0.20% | 0.204 | no |
| book_bear_pullback | A ranked short | -0.24% / -0.22% / -0.54% | -1.21% (-1.98%) | 0.980 | 0% | -4.01% | -0.22% / -0.26% / -0.21% | 0.214 | no |
| book_short_analogue12 | A ranked short | -0.33% / -0.26% / -0.68% | -1.29% (-2.08%) | 0.985 | 0% | -4.05% | -0.21% / -0.27% / -0.29% | 0.265 | no |
| book_bear_breakdown | A ranked short | -0.23% / -0.27% / -0.66% | -1.19% (-1.96%) | 0.980 | 0% | -4.06% | -0.18% / -0.38% / -0.25% | 0.242 | no |
| book_short_analogue6 | A ranked short | -0.27% / -0.21% / -0.47% | -1.23% (-2.01%) | 0.981 | 0% | -4.00% | -0.20% / -0.21% / -0.21% | 0.270 | no |
| book_bear_cost_guard | A ranked short | -0.23% / -0.28% / -0.69% | -1.19% (-1.96%) | 0.979 | 0% | -4.07% | -0.13% / -0.39% / -0.28% | 0.246 | no |
| book_bear_guard | A ranked short | -0.24% / -0.29% / -0.71% | -1.21% (-1.98%) | 0.980 | 0% | -4.08% | -0.09% / -0.39% / -0.28% | 0.227 | no |
| book_bear_trend_control | A ranked short | -0.15% / -0.39% / -0.86% | -1.12% (-1.89%) | 0.971 | 0% | -4.17% | +0.16% / -0.45% / -0.48% | 0.261 | no |
| book_bear_trail_exit | A ranked short | -0.24% / -0.30% / -0.67% | -1.20% (-1.97%) | 0.981 | 0% | -4.09% | -0.21% / -0.38% / -0.28% | 0.225 | no |
| book_bear_fast_exit | A ranked short | -0.32% / -0.37% / -0.73% | -1.29% (-2.06%) | 0.986 | 0% | -4.16% | -0.42% / -0.42% / -0.29% | 0.183 | no |

## C e20v45 + add-on (top 10 of 22 by mean d)

| Model | Group | Rest of round: mean / median / p10 | vs baseline: mean d (90% low) | p (one-sided) | Finish >= 0% | Median finish | BTC falls / flat / rises (median R) | HEADLINE | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| book_e20combo_alt_half_cash | reference | +0.96% / +0.04% / -4.70% | +0.00% (+0.00%) | 1.000 | 22% | -3.76% | +1.18% / -0.71% / +1.90% | 0.443 | baseline |
| baitoey_e20_shortc_alts | C e20v45 + add-on | +1.30% / +0.13% / -7.84% | +0.34% (-0.09%) | 0.162 | 28% | -3.67% | +1.07% / -1.26% / +0.81% | 0.559 | no |
| baitoey_e20_btcs_c | C e20v45 + add-on | +1.22% / +0.10% / -7.71% | +0.26% (-0.14%) | 0.200 | 27% | -3.71% | +1.20% / -1.26% / +1.78% | 0.548 | no |
| baitoey_e20_btcs_a | C e20v45 + add-on | +1.15% / -0.24% / -6.93% | +0.19% (-0.18%) | 0.260 | 25% | -4.03% | +1.12% / -1.26% / +1.78% | 0.544 | no |
| baitoey_e20_shortc_sol | C e20v45 + add-on | +1.11% / +0.09% / -7.50% | +0.15% (-0.24%) | 0.318 | 27% | -3.72% | +0.58% / -1.26% / +2.40% | 0.533 | no |
| baitoey_e20_btcs_d | C e20v45 + add-on | +1.11% / -0.24% / -6.93% | +0.15% (-0.25%) | 0.322 | 25% | -4.03% | +1.12% / -1.26% / +1.78% | 0.544 | no |
| baitoey_e20_shortc_eth | C e20v45 + add-on | +1.06% / -0.10% / -7.50% | +0.10% (-0.36%) | 0.396 | 28% | -3.90% | +0.37% / -1.25% / +1.10% | 0.543 | no |
| baitoey_e20_btcs_a2 | C e20v45 + add-on | +1.01% / -0.08% / -7.50% | +0.04% (-0.34%) | 0.450 | 25% | -3.88% | +0.88% / -1.21% / +1.22% | 0.537 | no |
| baitoey_ovl_brk_e20 | C e20v45 + add-on | +0.96% / -0.09% / -6.89% | +0.00% (-0.34%) | 0.500 | 23% | -3.89% | -0.02% / -0.53% / +2.40% | 0.571 | no |
| book_e20combo_brk_cash | C e20v45 + add-on | +0.96% / -0.09% / -6.89% | -0.00% (-0.34%) | 0.504 | 23% | -3.89% | -0.02% / -0.53% / +2.40% | 0.570 | no |
| baitoey_e20_btcs_b | C e20v45 + add-on | +0.95% / -0.28% / -7.21% | -0.01% (-0.40%) | 0.518 | 25% | -4.06% | +0.51% / -1.26% / +1.82% | 0.540 | no |

## B short or long/short (top 10 of 36 by mean d)

| Model | Group | Rest of round: mean / median / p10 | vs baseline: mean d (90% low) | p (one-sided) | Finish >= 0% | Median finish | BTC falls / flat / rises (median R) | HEADLINE | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| book_e20combo_alt_half_cash | reference | +0.96% / +0.04% / -4.70% | +0.00% (+0.00%) | 1.000 | 22% | -3.76% | +1.18% / -0.71% / +1.90% | 0.443 | baseline |
| pol_switch_rmax_tl | B short or long/short | +0.64% / -0.16% / -7.38% | -0.32% (-0.95%) | 0.728 | 19% | -3.95% | -0.39% / -0.25% / +0.68% | 0.491 | no |
| baitoey_mjt_24_96_d | B short or long/short | +0.60% / -0.06% / -6.03% | -0.36% (-1.17%) | 0.713 | 19% | -3.86% | +0.64% / -1.69% / +0.84% | 0.351 | no |
| baitoey_mjt_12_48_d | B short or long/short | +0.58% / -0.41% / -6.70% | -0.38% (-1.29%) | 0.706 | 23% | -4.20% | +0.44% / -1.61% / +0.80% | 0.341 | no |
| baitoey_mjt_24_96_6h | B short or long/short | +0.49% / -0.56% / -6.15% | -0.47% (-1.22%) | 0.784 | 20% | -4.34% | +0.05% / -1.98% / +1.67% | 0.341 | no |
| book_price_slow_signed | B short or long/short | +0.43% / -0.21% / -3.65% | -0.54% (-1.26%) | 0.833 | 16% | -4.00% | +0.68% / -1.43% / -0.20% | 0.299 | no |
| baitoey_mjt_12_48_6h | B short or long/short | +0.38% / -0.78% / -6.00% | -0.59% (-1.35%) | 0.839 | 24% | -4.55% | -0.83% / -1.47% / +1.26% | 0.314 | no |
| book_short_trend | B short or long/short | +0.34% / -0.14% / -2.84% | -0.62% (-1.27%) | 0.893 | 10% | -3.93% | -0.10% / -0.52% / +0.76% | 0.335 | no |
| pol_switch_vt_tl | B short or long/short | +0.34% / -0.22% / -6.77% | -0.62% (-1.20%) | 0.909 | 17% | -4.01% | -0.37% / -0.37% / +0.49% | 0.548 | no |
| book_short_rebound | B short or long/short | +0.32% / -0.24% / -2.58% | -0.64% (-1.26%) | 0.903 | 11% | -4.03% | -0.21% / -0.53% / +0.70% | 0.339 | no |
| book_price_slow_short | B short or long/short | +0.29% / -0.51% / -2.82% | -0.68% (-1.54%) | 0.854 | 11% | -4.29% | +1.95% / -0.80% / -1.06% | 0.264 | no |

## D other (top 10 of 28 by mean d)

| Model | Group | Rest of round: mean / median / p10 | vs baseline: mean d (90% low) | p (one-sided) | Finish >= 0% | Median finish | BTC falls / flat / rises (median R) | HEADLINE | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| book_e20combo_alt_half_cash | reference | +0.96% / +0.04% / -4.70% | +0.00% (+0.00%) | 1.000 | 22% | -3.76% | +1.18% / -0.71% / +1.90% | 0.443 | baseline |
| book_vt_breadth | D other | +0.48% / -0.78% / -3.84% | -0.48% (-1.19%) | 0.809 | 18% | -4.55% | -2.85% / -0.76% / +3.48% | 0.516 | no |
| team_trend_2 | D other | +0.43% / -0.34% / -4.06% | -0.53% (-1.20%) | 0.845 | 12% | -4.12% | -1.76% / -0.18% / +1.90% | 0.449 | no |
| book_vt_dual | D other | +0.38% / -1.05% / -4.85% | -0.58% (-1.32%) | 0.847 | 18% | -4.81% | -3.18% / -1.17% / +3.50% | 0.532 | no |
| book_vt_top4 | D other | +0.30% / -0.15% / -8.56% | -0.66% (-1.69%) | 0.800 | 24% | -3.94% | -6.27% / -0.55% / +5.60% | 0.572 | no |
| pol_switch_rc | D other | +0.27% / -0.20% / -3.99% | -0.69% (-1.27%) | 0.939 | 11% | -4.00% | -0.21% / -0.20% / +0.04% | 0.443 | no |
| pol_vt_mvr | D other | +0.24% / -0.63% / -6.01% | -0.72% (-1.62%) | 0.850 | 19% | -4.41% | -3.88% / -0.87% / +3.51% | 0.528 | no |
| book_orch | D other | +0.12% / -0.50% / -8.30% | -0.84% (-1.86%) | 0.861 | 23% | -4.28% | -6.89% / -0.62% / +4.68% | 0.617 | no |
| baitoey_ovl_evtctl_dual | D other | +0.10% / -0.82% / -7.38% | -0.86% (-1.85%) | 0.876 | 22% | -4.59% | -5.53% / -0.94% / +4.21% | 0.588 | no |
| baitoey_vt_dual | D other | +0.08% / -0.94% / -7.38% | -0.88% (-1.86%) | 0.884 | 22% | -4.70% | -5.53% / -1.04% / +4.21% | 0.587 | no |
| baitoey_vt_mom | D other | +0.07% / -0.54% / -8.48% | -0.89% (-1.94%) | 0.868 | 23% | -4.32% | -6.58% / -0.64% / +4.68% | 0.609 | no |

## References

| Model | Group | Rest of round: mean / median / p10 | vs baseline: mean d (90% low) | p (one-sided) | Finish >= 0% | Median finish | BTC falls / flat / rises (median R) | HEADLINE | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| book_e20combo_alt_half_cash | reference | +0.96% / +0.04% / -4.70% | +0.00% (+0.00%) | 1.000 | 22% | -3.76% | +1.18% / -0.71% / +1.90% | 0.443 | baseline |
| pol_switch_vt_tl_e20v45 | reference | +0.93% / -0.22% / -7.02% | -0.03% (-0.38%) | 0.550 | 23% | -4.01% | -0.02% / -1.16% / +2.40% | 0.568 | no |
| team_cash | reference | -0.20% / -0.20% / -0.21% | -1.16% (-1.94%) | 0.976 | 0% | -3.99% | -0.21% / -0.20% / -0.19% | 0.372 | no |
| team_btc_hold | reference | +0.25% / +0.17% / -9.59% | -0.71% (-2.05%) | 0.745 | 23% | -3.64% | -5.46% / +0.01% / +6.71% | 0.478 | no |

## Top 10 overall by mean d

| Model | Group | Rest of round: mean / median / p10 | vs baseline: mean d (90% low) | p (one-sided) | Finish >= 0% | Median finish | BTC falls / flat / rises (median R) | HEADLINE | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| book_e20combo_alt_half_cash | reference | +0.96% / +0.04% / -4.70% | +0.00% (+0.00%) | 1.000 | 22% | -3.76% | +1.18% / -0.71% / +1.90% | 0.443 | baseline |
| baitoey_e20_shortc_alts | C e20v45 + add-on | +1.30% / +0.13% / -7.84% | +0.34% (-0.09%) | 0.162 | 28% | -3.67% | +1.07% / -1.26% / +0.81% | 0.559 | no |
| baitoey_e20_btcs_c | C e20v45 + add-on | +1.22% / +0.10% / -7.71% | +0.26% (-0.14%) | 0.200 | 27% | -3.71% | +1.20% / -1.26% / +1.78% | 0.548 | no |
| baitoey_e20_btcs_a | C e20v45 + add-on | +1.15% / -0.24% / -6.93% | +0.19% (-0.18%) | 0.260 | 25% | -4.03% | +1.12% / -1.26% / +1.78% | 0.544 | no |
| baitoey_e20_shortc_sol | C e20v45 + add-on | +1.11% / +0.09% / -7.50% | +0.15% (-0.24%) | 0.318 | 27% | -3.72% | +0.58% / -1.26% / +2.40% | 0.533 | no |
| baitoey_e20_btcs_d | C e20v45 + add-on | +1.11% / -0.24% / -6.93% | +0.15% (-0.25%) | 0.322 | 25% | -4.03% | +1.12% / -1.26% / +1.78% | 0.544 | no |
| baitoey_e20_shortc_eth | C e20v45 + add-on | +1.06% / -0.10% / -7.50% | +0.10% (-0.36%) | 0.396 | 28% | -3.90% | +0.37% / -1.25% / +1.10% | 0.543 | no |
| baitoey_e20_btcs_a2 | C e20v45 + add-on | +1.01% / -0.08% / -7.50% | +0.04% (-0.34%) | 0.450 | 25% | -3.88% | +0.88% / -1.21% / +1.22% | 0.537 | no |
| baitoey_ovl_brk_e20 | C e20v45 + add-on | +0.96% / -0.09% / -6.89% | +0.00% (-0.34%) | 0.500 | 23% | -3.89% | -0.02% / -0.53% / +2.40% | 0.571 | no |
| book_e20combo_brk_cash | C e20v45 + add-on | +0.96% / -0.09% / -6.89% | -0.00% (-0.34%) | 0.504 | 23% | -3.89% | -0.02% / -0.53% / +2.40% | 0.570 | no |
| baitoey_e20_btcs_b | C e20v45 + add-on | +0.95% / -0.28% / -7.21% | -0.01% (-0.40%) | 0.518 | 25% | -4.06% | +0.51% / -1.26% / +1.82% | 0.540 | no |

## Context: all similar rounds (secondary sample)

Better: none. Promising: none.

| Model | Group | Rest of round: mean / median / p10 | vs baseline: mean d (90% low) | p (one-sided) | Finish >= 0% | Median finish | BTC falls / flat / rises (median R) | HEADLINE | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| book_e20combo_alt_half_cash | reference | +0.93% / +0.01% / -5.49% | +0.00% (+0.00%) | 1.000 | 22% | -3.79% | +0.24% / -0.60% / +1.94% | 0.443 | baseline |
| book_short_shock_fade | A ranked short | -0.20% / -0.20% / -0.23% | -1.13% (-1.77%) | 0.991 | 0% | -3.99% | -0.20% / -0.20% / -0.20% | 0.297 | no |
| book_short_volume_fade | A ranked short | -0.20% / -0.20% / -0.28% | -1.13% (-1.77%) | 0.992 | 0% | -3.99% | -0.20% / -0.20% / -0.20% | 0.303 | no |
| book_short_range_fail | A ranked short | -0.20% / -0.20% / -0.29% | -1.13% (-1.77%) | 0.992 | 0% | -3.99% | -0.20% / -0.20% / -0.20% | 0.364 | no |
| book_short_ridge6 | A ranked short | -0.22% / -0.20% / -0.30% | -1.15% (-1.79%) | 0.992 | 0% | -3.99% | -0.20% / -0.20% / -0.20% | 0.204 | no |
| book_bear_pullback | A ranked short | -0.21% / -0.24% / -0.47% | -1.14% (-1.78%) | 0.992 | 0% | -4.03% | -0.22% / -0.28% / -0.21% | 0.214 | no |
| book_short_analogue12 | A ranked short | -0.31% / -0.24% / -0.58% | -1.24% (-1.88%) | 0.996 | 0% | -4.03% | -0.22% / -0.25% / -0.24% | 0.265 | no |
| book_bear_breakdown | A ranked short | -0.22% / -0.27% / -0.65% | -1.14% (-1.78%) | 0.992 | 0% | -4.06% | -0.14% / -0.38% / -0.26% | 0.242 | no |
| book_short_analogue6 | A ranked short | -0.26% / -0.20% / -0.42% | -1.18% (-1.82%) | 0.994 | 0% | -4.00% | -0.20% / -0.20% / -0.21% | 0.270 | no |
| book_bear_cost_guard | A ranked short | -0.22% / -0.28% / -0.63% | -1.15% (-1.78%) | 0.993 | 0% | -4.06% | -0.10% / -0.39% / -0.27% | 0.246 | no |
| book_bear_guard | A ranked short | -0.25% / -0.30% / -0.64% | -1.18% (-1.80%) | 0.994 | 0% | -4.09% | -0.09% / -0.39% / -0.29% | 0.227 | no |
| book_bear_trend_control | A ranked short | -0.13% / -0.38% / -0.81% | -1.06% (-1.71%) | 0.985 | 0% | -4.17% | +0.17% / -0.45% / -0.45% | 0.261 | no |
| book_bear_trail_exit | A ranked short | -0.24% / -0.30% / -0.63% | -1.17% (-1.80%) | 0.994 | 0% | -4.09% | -0.19% / -0.39% / -0.27% | 0.225 | no |
| book_bear_fast_exit | A ranked short | -0.35% / -0.39% / -0.73% | -1.28% (-1.91%) | 0.997 | 0% | -4.17% | -0.44% / -0.45% / -0.29% | 0.183 | no |
| baitoey_e20_shortc_alts | C e20v45 + add-on | +1.21% / -0.04% / -8.45% | +0.28% (-0.13%) | 0.186 | 27% | -3.84% | -0.27% / -0.87% / +2.53% | 0.559 | no |
| baitoey_e20_btcs_c | C e20v45 + add-on | +1.15% / +0.02% / -8.06% | +0.23% (-0.16%) | 0.225 | 27% | -3.78% | +0.01% / -0.83% / +2.63% | 0.548 | no |
| baitoey_e20_shortc_eth | C e20v45 + add-on | +1.09% / -0.10% / -7.98% | +0.17% (-0.27%) | 0.315 | 28% | -3.89% | -0.28% / -0.84% / +2.53% | 0.543 | no |
| baitoey_e20_btcs_a | C e20v45 + add-on | +1.08% / -0.24% / -7.86% | +0.15% (-0.23%) | 0.305 | 26% | -4.03% | -0.24% / -1.26% / +2.53% | 0.544 | no |
| baitoey_e20_shortc_sol | C e20v45 + add-on | +1.06% / -0.02% / -8.32% | +0.13% (-0.28%) | 0.347 | 27% | -3.82% | -0.33% / -1.25% / +2.65% | 0.533 | no |

## Notes

- Skipped: none.
- Rounds that start on consecutive days overlap, so the effective sample is far smaller than the round count; the bootstrap resamples whole calendar months for that reason.
- Full tables: `primary.csv`, `all_similar.csv` in this folder.
