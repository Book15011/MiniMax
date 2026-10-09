# Three overlays on e20v45 and vt_dual: results

Pre-registration: `research/baitoey/prereg/20261009-overlays.md` (c35047e). Book's weak-market board, protocol 603da2948b68ee0f5c8a; tool version 3036a0d8bfdaa6a0 for every row. Rank = the board's experimental rank among 50 models (lower is better); conservative = the board's joint lower bound.

## Base: pol_switch_vt_tl_e20v45

| Model | Archived 228 h median / p10 / p90 | Fresh 228 h median / p10 / p90 | HEADLINE_RET | REL SCREEN / CONFIRM | Gates G1-G6 | Turnover / fees per round | Board rank (conservative) |
|---|---|---|---|---|---|---|---|
| base (`pol_switch_vt_tl_e20v45`) | -2.88% / -11.44% / +19.75% | -2.39% / -10.13% / +13.36% | 0.568 | 2.244 / 3.002 | all pass | 5.31 / +0.61% | 32 (-6.73%) |
| 1a alts to BTC (`baitoey_ovl_altbtc_a_e20`) | -2.65% / -9.15% / +15.38% | -1.19% / -6.61% / +14.88% | 0.429 | 1.517 / 0.753 | all pass | 6.02 / +0.67% | 26 (-6.18%) |
| 1b alts to cash (`baitoey_ovl_altbtc_b_e20`) | -0.89% / -9.85% / +11.50% | +0.45% / -7.45% / +8.32% | 0.375 | 1.461 / 0.640 | all pass | 4.52 / +0.52% | 16 (-5.38%) |
| 2 breakdown exit (`baitoey_ovl_brk_e20`) | -2.88% / -11.13% / +19.75% | -2.23% / -9.89% / +12.57% | 0.571 | 2.360 / 2.866 | all pass | 5.26 / +0.60% | 28 (-6.26%) |
| 3 event de-risk (`baitoey_ovl_evt_e20`) | -2.88% / -11.69% / +18.66% | -2.23% / -10.13% / +13.95% | 0.539 | 2.232 / 3.055 | all pass | 5.71 / +0.65% | 31 (-6.72%) |
| 3 control (hourly, factor 1) (`baitoey_ovl_evtctl_e20`) | -2.88% / -11.42% / +19.03% | -2.39% / -10.13% / +13.42% | 0.547 | 2.290 / 3.008 | all pass | 5.32 / +0.61% | 33 (-6.78%) |

9- and 10-day horizons (archived profile, median / p10 / p90):

| Model | 216 h | 240 h |
|---|---|---|
| base | -2.05% / -11.40% / +13.59% | -2.83% / -11.18% / +23.58% |
| 1a alts to BTC | -3.25% / -10.24% / +12.28% | -2.51% / -8.99% / +17.33% |
| 1b alts to cash | -1.18% / -9.90% / +11.15% | -0.62% / -9.65% / +14.67% |
| 2 breakdown exit | -2.05% / -11.17% / +13.59% | -2.83% / -11.01% / +23.58% |
| 3 event de-risk | -1.98% / -11.43% / +13.08% | -2.84% / -11.43% / +22.62% |
| 3 control (hourly, factor 1) | -2.05% / -11.38% / +13.46% | -2.84% / -11.16% / +23.21% |

Reading rule (pre-registered): better than the base if archived 228 h median and p10 are both at least the base's, REL SCREEN and CONFIRM each at least the base's minus 0.05, and no hard gate fails that the base passes.

- 1a alts to BTC: not better than the base.
- 1b alts to cash: not better than the base.
- 2 breakdown exit: not better than the base.
- 3 event de-risk: not better than the base; not better than its control.
- 3 control (hourly, factor 1): not better than the base.

## Base: baitoey_vt_dual

| Model | Archived 228 h median / p10 / p90 | Fresh 228 h median / p10 / p90 | HEADLINE_RET | REL SCREEN / CONFIRM | Gates G1-G6 | Turnover / fees per round | Board rank (conservative) |
|---|---|---|---|---|---|---|---|
| base (`baitoey_vt_dual`) | +3.63% / -7.96% / +13.36% | +1.78% / -3.75% / +10.02% | 0.587 | 1.328 / 2.534 | all pass | 4.08 / +0.47% | 2 (-2.79%) |
| 1a alts to BTC (`baitoey_ovl_altbtc_a_dual`) | +0.95% / -6.75% / +10.28% | +2.00% / -6.23% / +8.39% | 0.402 | 0.967 / 0.135 | all pass | 4.81 / +0.53% | 14 (-5.19%) |
| 1b alts to cash (`baitoey_ovl_altbtc_b_dual`) | +0.04% / -6.55% / +6.34% | +0.61% / -4.10% / +6.17% | 0.375 | 1.096 / 0.306 | FAIL G6_median | 3.00 / +0.35% | 19 (-5.56%) |
| 2 breakdown exit (`baitoey_ovl_brk_dual`) | +3.63% / -7.86% / +13.36% | +1.78% / -3.84% / +10.02% | 0.581 | 1.110 / 2.467 | all pass | 3.81 / +0.44% | 1 (-2.73%) |
| 3 event de-risk (`baitoey_ovl_evt_dual`) | +2.93% / -8.01% / +13.59% | +0.96% / -4.20% / +10.43% | 0.567 | 1.305 / 2.364 | all pass | 4.45 / +0.51% | 5 (-3.34%) |
| 3 control (hourly, factor 1) (`baitoey_ovl_evtctl_dual`) | +2.93% / -8.01% / +13.36% | +0.96% / -4.20% / +10.09% | 0.588 | 1.307 / 2.559 | all pass | 4.18 / +0.48% | 4 (-3.19%) |

9- and 10-day horizons (archived profile, median / p10 / p90):

| Model | 216 h | 240 h |
|---|---|---|
| base | +2.19% / -7.95% / +12.58% | +3.86% / -7.98% / +14.57% |
| 1a alts to BTC | +1.04% / -7.25% / +8.16% | +1.04% / -6.46% / +10.32% |
| 1b alts to cash | +0.04% / -6.89% / +7.21% | +0.04% / -6.34% / +7.31% |
| 2 breakdown exit | +2.19% / -7.95% / +12.58% | +3.86% / -7.73% / +14.57% |
| 3 event de-risk | +2.17% / -8.05% / +12.10% | +3.67% / -8.13% / +14.35% |
| 3 control (hourly, factor 1) | +2.19% / -8.05% / +12.58% | +3.67% / -8.13% / +14.57% |

Reading rule (pre-registered): better than the base if archived 228 h median and p10 are both at least the base's, REL SCREEN and CONFIRM each at least the base's minus 0.05, and no hard gate fails that the base passes.

- 1a alts to BTC: not better than the base.
- 1b alts to cash: not better than the base.
- 2 breakdown exit: not better than the base.
- 3 event de-risk: not better than the base; not better than its control.
- 3 control (hourly, factor 1): not better than the base.

