# Short models against book_e20combo_brk_cash over the rest of this round: independent test

Pre-registration: `research/baitoey/prereg/20261012-short-models-rest-of-round.md` (3c5bdd8) + amendment 1 (b52de31). Baseline: `book_e20combo_brk_cash`. Start: round hour 186 (2026-10-12 06:00 UTC), account at -3.80%, BTC -1.53% since the round start, 150 hours left.

- Similar past rounds: **324** of 2298, in 69 calendar months.
- Primary sample (rest of round does not overlap Book's 50 weak-market cases): **230** rounds in 58 months.
- Models tested against the baseline: **102**; Bonferroni threshold p <= 0.0010. Excluded (reference log, AGENTS rule 7 question): 18.
- Switching cost 0.20% for every model except the baseline. Final account = (1 -3.80%)(1 + R) - 1.

## Verdict (primary sample)

- Better than book_e20combo_brk_cash: **none**.
- Promising, not proven: none.

## A. Book's 13 ranked short models

| Model | Group | Rest of round: mean / median / p10 | vs baseline: mean d (90% low) | p (one-sided) | Finish >= 0% | Median finish | BTC falls / flat / rises (median R) | HEADLINE | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| book_e20combo_brk_cash | reference | +1.28% / +0.05% / -5.88% | +0.00% (+0.00%) | 1.000 | 24% | -3.75% | +0.18% / -0.30% / +1.90% | 0.570 | baseline |
| book_short_shock_fade | A ranked short | -0.20% / -0.20% / -0.21% | -1.48% (-2.53%) | 0.978 | 0% | -3.99% | -0.20% / -0.20% / -0.20% | 0.297 | no |
| book_short_volume_fade | A ranked short | -0.21% / -0.20% / -0.28% | -1.49% (-2.55%) | 0.978 | 0% | -3.99% | -0.20% / -0.20% / -0.20% | 0.303 | no |
| book_short_range_fail | A ranked short | -0.21% / -0.20% / -0.30% | -1.49% (-2.54%) | 0.979 | 0% | -3.99% | -0.20% / -0.20% / -0.20% | 0.364 | no |
| book_short_ridge6 | A ranked short | -0.23% / -0.20% / -0.33% | -1.51% (-2.56%) | 0.980 | 0% | -4.00% | -0.20% / -0.20% / -0.20% | 0.204 | no |
| book_bear_pullback | A ranked short | -0.26% / -0.22% / -0.51% | -1.54% (-2.59%) | 0.982 | 0% | -4.01% | -0.22% / -0.24% / -0.21% | 0.214 | no |
| book_short_analogue12 | A ranked short | -0.33% / -0.25% / -0.70% | -1.62% (-2.66%) | 0.985 | 0% | -4.04% | -0.22% / -0.25% / -0.30% | 0.265 | no |
| book_bear_breakdown | A ranked short | -0.26% / -0.27% / -0.65% | -1.54% (-2.59%) | 0.982 | 0% | -4.06% | -0.22% / -0.37% / -0.25% | 0.242 | no |
| book_short_analogue6 | A ranked short | -0.27% / -0.21% / -0.48% | -1.56% (-2.61%) | 0.982 | 0% | -4.00% | -0.21% / -0.20% / -0.21% | 0.270 | no |
| book_bear_cost_guard | A ranked short | -0.25% / -0.26% / -0.60% | -1.53% (-2.58%) | 0.981 | 0% | -4.05% | -0.17% / -0.34% / -0.26% | 0.246 | no |
| book_bear_guard | A ranked short | -0.27% / -0.28% / -0.64% | -1.55% (-2.60%) | 0.982 | 0% | -4.07% | -0.12% / -0.36% / -0.28% | 0.227 | no |
| book_bear_trend_control | A ranked short | -0.20% / -0.39% / -0.75% | -1.48% (-2.54%) | 0.976 | 0% | -4.17% | +0.12% / -0.43% / -0.48% | 0.261 | no |
| book_bear_trail_exit | A ranked short | -0.27% / -0.30% / -0.61% | -1.55% (-2.60%) | 0.983 | 0% | -4.09% | -0.29% / -0.37% / -0.28% | 0.225 | no |
| book_bear_fast_exit | A ranked short | -0.35% / -0.37% / -0.71% | -1.63% (-2.68%) | 0.987 | 0% | -4.16% | -0.44% / -0.40% / -0.29% | 0.183 | no |

## C e20v45 + add-on (top 10 of 22 by mean d)

| Model | Group | Rest of round: mean / median / p10 | vs baseline: mean d (90% low) | p (one-sided) | Finish >= 0% | Median finish | BTC falls / flat / rises (median R) | HEADLINE | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| book_e20combo_brk_cash | reference | +1.28% / +0.05% / -5.88% | +0.00% (+0.00%) | 1.000 | 24% | -3.75% | +0.18% / -0.30% / +1.90% | 0.570 | baseline |
| baitoey_e20_shortc_alts | C e20v45 + add-on | +1.36% / +0.04% / -6.51% | +0.08% (-0.18%) | 0.367 | 27% | -3.76% | +0.94% / -0.56% / +0.67% | 0.559 | no |
| baitoey_e20_shortc_sol | C e20v45 + add-on | +1.29% / -0.04% / -7.02% | +0.00% (-0.20%) | 0.509 | 27% | -3.84% | +0.32% / -0.42% / +0.67% | 0.533 | no |
| baitoey_e20_btcs_c | C e20v45 + add-on | +1.27% / -0.03% / -6.72% | -0.02% (-0.26%) | 0.556 | 26% | -3.83% | +0.79% / -0.56% / +0.77% | 0.548 | no |
| baitoey_e20_btcs_a | C e20v45 + add-on | +1.23% / -0.26% / -6.52% | -0.05% (-0.29%) | 0.629 | 23% | -4.05% | +0.32% / -0.83% / +0.77% | 0.544 | no |
| baitoey_e20_btcs_d | C e20v45 + add-on | +1.18% / -0.26% / -6.52% | -0.10% (-0.35%) | 0.711 | 23% | -4.05% | +0.32% / -0.86% / +0.77% | 0.544 | no |
| baitoey_e20_shortc_eth | C e20v45 + add-on | +1.12% / -0.21% / -7.38% | -0.17% (-0.45%) | 0.778 | 27% | -4.00% | +0.22% / -0.40% / +0.69% | 0.543 | no |
| baitoey_ovl_evtctl_e20 | C e20v45 + add-on | +1.11% / -0.23% / -6.19% | -0.18% (-0.23%) | 0.999 | 23% | -4.02% | -0.05% / -0.55% / +1.69% | 0.547 | no |
| baitoey_e20_btcs_a2 | C e20v45 + add-on | +1.10% / +0.00% / -6.73% | -0.18% (-0.47%) | 0.793 | 24% | -3.80% | +0.43% / -0.94% / +0.67% | 0.537 | no |
| baitoey_ovl_brk_e20 | C e20v45 + add-on | +1.08% / -0.15% / -6.07% | -0.20% (-0.21%) | 1.000 | 23% | -3.95% | -0.02% / -0.50% / +1.69% | 0.571 | no |
| book_e20guard_pullback | C e20v45 + add-on | +1.07% / -0.22% / -6.33% | -0.21% (-0.27%) | 1.000 | 22% | -4.01% | -0.53% / -0.38% / +1.26% | 0.547 | no |

## B short or long/short (top 10 of 36 by mean d)

| Model | Group | Rest of round: mean / median / p10 | vs baseline: mean d (90% low) | p (one-sided) | Finish >= 0% | Median finish | BTC falls / flat / rises (median R) | HEADLINE | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| book_e20combo_brk_cash | reference | +1.28% / +0.05% / -5.88% | +0.00% (+0.00%) | 1.000 | 24% | -3.75% | +0.18% / -0.30% / +1.90% | 0.570 | baseline |
| pol_switch_rmax_tl | B short or long/short | +0.67% / -0.38% / -7.02% | -0.61% (-1.19%) | 0.914 | 20% | -4.16% | -0.39% / -0.40% / +0.10% | 0.491 | no |
| baitoey_mjt_12_48_d | B short or long/short | +0.54% / -0.91% / -6.25% | -0.74% (-1.85%) | 0.818 | 23% | -4.68% | -0.05% / -1.45% / +0.80% | 0.341 | no |
| baitoey_mjt_24_96_d | B short or long/short | +0.45% / -0.30% / -5.81% | -0.84% (-1.80%) | 0.872 | 19% | -4.09% | +0.07% / -1.52% / +0.95% | 0.351 | no |
| baitoey_mjt_12_48_6h | B short or long/short | +0.35% / -0.73% / -5.76% | -0.93% (-1.87%) | 0.906 | 23% | -4.50% | -0.91% / -1.41% / +1.26% | 0.314 | no |
| book_cashshort_confirm | B short or long/short | +0.35% / -0.87% / -6.26% | -0.94% (-1.78%) | 0.924 | 20% | -4.64% | -4.01% / -0.97% / +3.45% | 0.577 | no |
| book_cashshort_pullback | B short or long/short | +0.33% / -0.95% / -6.31% | -0.95% (-1.78%) | 0.932 | 20% | -4.71% | -4.01% / -1.07% / +3.45% | 0.567 | no |
| baitoey_mjt_24_96_6h | B short or long/short | +0.33% / -0.68% / -6.15% | -0.95% (-1.87%) | 0.916 | 20% | -4.46% | -0.43% / -1.77% / +1.58% | 0.341 | no |
| pol_switch_vt_tl | B short or long/short | +0.31% / -0.36% / -6.40% | -0.97% (-1.51%) | 0.993 | 17% | -4.14% | -0.37% / -0.40% / +0.39% | 0.548 | no |
| book_short_trend | B short or long/short | +0.26% / -0.15% / -2.77% | -1.02% (-1.95%) | 0.932 | 8% | -3.94% | -0.18% / -0.44% / +0.65% | 0.335 | no |
| book_transition_short | B short or long/short | +0.26% / -1.02% / -6.76% | -1.02% (-1.84%) | 0.945 | 18% | -4.78% | -4.14% / -1.11% / +3.20% | 0.500 | no |

## D other (top 10 of 28 by mean d)

| Model | Group | Rest of round: mean / median / p10 | vs baseline: mean d (90% low) | p (one-sided) | Finish >= 0% | Median finish | BTC falls / flat / rises (median R) | HEADLINE | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| book_e20combo_brk_cash | reference | +1.28% / +0.05% / -5.88% | +0.00% (+0.00%) | 1.000 | 24% | -3.75% | +0.18% / -0.30% / +1.90% | 0.570 | baseline |
| book_vt_top4 | D other | +0.99% / +0.42% / -7.33% | -0.30% (-1.21%) | 0.668 | 25% | -3.40% | -5.97% / -0.10% / +5.26% | 0.572 | no |
| book_vt_breadth | D other | +0.76% / -0.59% / -3.63% | -0.52% (-1.26%) | 0.819 | 18% | -4.36% | -2.69% / -0.67% / +3.26% | 0.516 | no |
| book_orch | D other | +0.75% / -0.07% / -7.86% | -0.53% (-1.45%) | 0.779 | 24% | -3.87% | -5.31% / -0.17% / +4.72% | 0.617 | no |
| pol_vt_mvr | D other | +0.73% / -0.27% / -5.13% | -0.55% (-1.46%) | 0.788 | 21% | -4.06% | -3.64% / -0.46% / +3.58% | 0.528 | no |
| baitoey_rot_max | D other | +0.71% / +0.42% / -11.93% | -0.58% (-1.81%) | 0.719 | 33% | -3.40% | -8.73% / -0.18% / +6.81% | 0.546 | no |
| baitoey_vt_mom | D other | +0.70% / -0.20% / -7.77% | -0.58% (-1.54%) | 0.795 | 25% | -4.00% | -5.93% / -0.29% / +4.72% | 0.609 | no |
| book_vt_dual | D other | +0.69% / -0.80% / -4.36% | -0.59% (-1.33%) | 0.858 | 19% | -4.57% | -3.18% / -0.84% / +3.21% | 0.532 | no |
| pol_abl_shock | D other | +0.68% / -0.22% / -7.77% | -0.60% (-1.53%) | 0.808 | 26% | -4.01% | -5.74% / -0.35% / +4.68% | 0.607 | no |
| team_trend_2 | D other | +0.66% / -0.27% / -3.87% | -0.62% (-1.31%) | 0.874 | 13% | -4.06% | -1.38% / -0.21% / +1.90% | 0.449 | no |
| pol_combo_rb | D other | +0.60% / +0.20% / -7.13% | -0.69% (-1.69%) | 0.806 | 24% | -3.61% | -5.56% / -0.35% / +5.85% | 0.481 | no |

## References

| Model | Group | Rest of round: mean / median / p10 | vs baseline: mean d (90% low) | p (one-sided) | Finish >= 0% | Median finish | BTC falls / flat / rises (median R) | HEADLINE | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| book_e20combo_brk_cash | reference | +1.28% / +0.05% / -5.88% | +0.00% (+0.00%) | 1.000 | 24% | -3.75% | +0.18% / -0.30% / +1.90% | 0.570 | baseline |
| pol_switch_vt_tl_e20v45 | reference | +1.11% / -0.17% / -6.33% | -0.17% (-0.22%) | 1.000 | 23% | -3.96% | -0.02% / -0.38% / +1.69% | 0.568 | no |
| team_cash | reference | -0.20% / -0.20% / -0.21% | -1.48% (-2.53%) | 0.978 | 0% | -3.99% | -0.21% / -0.20% / -0.19% | 0.372 | no |
| team_btc_hold | reference | +0.94% / +0.19% / -7.11% | -0.34% (-1.48%) | 0.645 | 24% | -3.62% | -4.79% / -0.26% / +6.55% | 0.478 | no |

## Top 10 overall by mean d

| Model | Group | Rest of round: mean / median / p10 | vs baseline: mean d (90% low) | p (one-sided) | Finish >= 0% | Median finish | BTC falls / flat / rises (median R) | HEADLINE | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| book_e20combo_brk_cash | reference | +1.28% / +0.05% / -5.88% | +0.00% (+0.00%) | 1.000 | 24% | -3.75% | +0.18% / -0.30% / +1.90% | 0.570 | baseline |
| baitoey_e20_shortc_alts | C e20v45 + add-on | +1.36% / +0.04% / -6.51% | +0.08% (-0.18%) | 0.367 | 27% | -3.76% | +0.94% / -0.56% / +0.67% | 0.559 | no |
| baitoey_e20_shortc_sol | C e20v45 + add-on | +1.29% / -0.04% / -7.02% | +0.00% (-0.20%) | 0.509 | 27% | -3.84% | +0.32% / -0.42% / +0.67% | 0.533 | no |
| baitoey_e20_btcs_c | C e20v45 + add-on | +1.27% / -0.03% / -6.72% | -0.02% (-0.26%) | 0.556 | 26% | -3.83% | +0.79% / -0.56% / +0.77% | 0.548 | no |
| baitoey_e20_btcs_a | C e20v45 + add-on | +1.23% / -0.26% / -6.52% | -0.05% (-0.29%) | 0.629 | 23% | -4.05% | +0.32% / -0.83% / +0.77% | 0.544 | no |
| baitoey_e20_btcs_d | C e20v45 + add-on | +1.18% / -0.26% / -6.52% | -0.10% (-0.35%) | 0.711 | 23% | -4.05% | +0.32% / -0.86% / +0.77% | 0.544 | no |
| baitoey_e20_shortc_eth | C e20v45 + add-on | +1.12% / -0.21% / -7.38% | -0.17% (-0.45%) | 0.778 | 27% | -4.00% | +0.22% / -0.40% / +0.69% | 0.543 | no |
| pol_switch_vt_tl_e20v45 | reference | +1.11% / -0.17% / -6.33% | -0.17% (-0.22%) | 1.000 | 23% | -3.96% | -0.02% / -0.38% / +1.69% | 0.568 | no |
| baitoey_ovl_evtctl_e20 | C e20v45 + add-on | +1.11% / -0.23% / -6.19% | -0.18% (-0.23%) | 0.999 | 23% | -4.02% | -0.05% / -0.55% / +1.69% | 0.547 | no |
| baitoey_e20_btcs_a2 | C e20v45 + add-on | +1.10% / +0.00% / -6.73% | -0.18% (-0.47%) | 0.793 | 24% | -3.80% | +0.43% / -0.94% / +0.67% | 0.537 | no |
| baitoey_ovl_brk_e20 | C e20v45 + add-on | +1.08% / -0.15% / -6.07% | -0.20% (-0.21%) | 1.000 | 23% | -3.95% | -0.02% / -0.50% / +1.69% | 0.571 | no |

## Context: all similar rounds (secondary sample)

Better: none. Promising: none.

| Model | Group | Rest of round: mean / median / p10 | vs baseline: mean d (90% low) | p (one-sided) | Finish >= 0% | Median finish | BTC falls / flat / rises (median R) | HEADLINE | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| book_e20combo_brk_cash | reference | +1.24% / -0.02% / -6.55% | +0.00% (+0.00%) | 1.000 | 24% | -3.82% | -0.57% / -0.49% / +2.66% | 0.570 | baseline |
| book_short_shock_fade | A ranked short | -0.20% / -0.20% / -0.23% | -1.44% (-2.32%) | 0.989 | 0% | -3.99% | -0.20% / -0.20% / -0.20% | 0.297 | no |
| book_short_volume_fade | A ranked short | -0.21% / -0.20% / -0.27% | -1.45% (-2.33%) | 0.989 | 0% | -3.99% | -0.20% / -0.20% / -0.20% | 0.303 | no |
| book_short_range_fail | A ranked short | -0.21% / -0.20% / -0.29% | -1.45% (-2.33%) | 0.989 | 0% | -3.99% | -0.20% / -0.20% / -0.20% | 0.364 | no |
| book_short_ridge6 | A ranked short | -0.23% / -0.20% / -0.30% | -1.47% (-2.34%) | 0.990 | 0% | -3.99% | -0.20% / -0.20% / -0.20% | 0.204 | no |
| book_bear_pullback | A ranked short | -0.24% / -0.23% / -0.46% | -1.48% (-2.36%) | 0.991 | 0% | -4.02% | -0.23% / -0.27% / -0.21% | 0.214 | no |
| book_short_analogue12 | A ranked short | -0.31% / -0.23% / -0.62% | -1.55% (-2.43%) | 0.993 | 0% | -4.02% | -0.23% / -0.23% / -0.27% | 0.265 | no |
| book_bear_breakdown | A ranked short | -0.25% / -0.27% / -0.63% | -1.49% (-2.37%) | 0.991 | 0% | -4.06% | -0.16% / -0.37% / -0.26% | 0.242 | no |
| book_short_analogue6 | A ranked short | -0.26% / -0.20% / -0.44% | -1.50% (-2.38%) | 0.992 | 0% | -4.00% | -0.20% / -0.20% / -0.21% | 0.270 | no |
| book_bear_cost_guard | A ranked short | -0.25% / -0.27% / -0.58% | -1.49% (-2.37%) | 0.991 | 0% | -4.06% | -0.13% / -0.37% / -0.28% | 0.246 | no |
| book_bear_guard | A ranked short | -0.27% / -0.31% / -0.61% | -1.51% (-2.39%) | 0.993 | 0% | -4.09% | -0.17% / -0.36% / -0.30% | 0.227 | no |
| book_bear_trend_control | A ranked short | -0.20% / -0.39% / -0.75% | -1.44% (-2.33%) | 0.987 | 0% | -4.17% | +0.12% / -0.45% / -0.44% | 0.261 | no |
| book_bear_trail_exit | A ranked short | -0.27% / -0.30% / -0.60% | -1.51% (-2.39%) | 0.993 | 0% | -4.09% | -0.23% / -0.38% / -0.28% | 0.225 | no |
| book_bear_fast_exit | A ranked short | -0.37% / -0.39% / -0.71% | -1.61% (-2.49%) | 0.995 | 0% | -4.17% | -0.45% / -0.43% / -0.29% | 0.183 | no |
| book_vt_top4 | D other | +1.28% / +0.64% / -7.52% | +0.04% (-0.66%) | 0.476 | 27% | -3.19% | -5.76% / -0.03% / +5.09% | 0.572 | no |
| book_vt_dual | D other | +1.22% / -0.23% / -4.51% | -0.02% (-0.59%) | 0.520 | 22% | -4.02% | -3.00% / -0.64% / +3.61% | 0.532 | no |
| baitoey_e20_shortc_alts | C e20v45 + add-on | +1.19% / -0.16% / -7.81% | -0.05% (-0.26%) | 0.642 | 26% | -3.95% | -0.40% / -0.67% / +2.23% | 0.559 | no |
| baitoey_e20_shortc_sol | C e20v45 + add-on | +1.16% / -0.12% / -7.69% | -0.08% (-0.26%) | 0.725 | 26% | -3.91% | -0.58% / -0.64% / +2.51% | 0.533 | no |
| baitoey_rot_max | D other | +1.14% / +0.80% / -11.83% | -0.10% (-1.05%) | 0.552 | 34% | -3.03% | -8.37% / -0.08% / +6.07% | 0.546 | no |

## Notes

- Skipped: none.
- Rounds that start on consecutive days overlap, so the effective sample is far smaller than the round count; the bootstrap resamples whole calendar months for that reason.
- Full tables: `primary.csv`, `all_similar.csv` in this folder.
