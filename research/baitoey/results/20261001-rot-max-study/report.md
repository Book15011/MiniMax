# Return-max rotation: full results (CONFIRM opened once)

| Run | Gate passed SCREEN / CONFIRM | Median R S / C | 75th pct R S / C | 90th pct R S / C | Worst 10% R S / C | REL | Gates G1-G6 | Fees + spread per window | vs team_rot_ew: REL diff [90%] |
|---|---|---|---|---|---|---|---|---|---|
| ref: team_rot_ew | 39% / 40% | +0.55% / -1.12% | +6.64% / +5.76% | +16.62% / +15.17% | -11.71% / -12.48% | 1.324 | 1✓ 2✓ 3✓ 4✓ 5✓ 6✓ | 0.28% + 0.04% | — |
| A **preferred** | 42% / 40% | +0.25% / -1.90% | +8.70% / +7.16% | +21.08% / +20.61% | -14.46% / -17.64% | 1.365 | 1✓ 2✗ 3✗ 4✓ 5✓ 6✗ | 0.37% + 0.06% | +0.040 [-0.008, +0.091] |
| B | 39% / 42% | +0.29% / -1.34% | +8.28% / +8.34% | +21.05% / +19.70% | -16.42% / -18.60% | 1.313 | 1✓ 2✗ 3✗ 4✓ 5✓ 6✗ | 0.36% + 0.05% | -0.012 [-0.346, +0.194] |
| C | 39% / 38% | +0.18% / -1.59% | +8.43% / +8.30% | +20.75% / +18.93% | -17.56% / -18.36% | 1.303 | 1✓ 2✗ 3✗ 4✓ 5✓ 6✗ | 0.35% + 0.05% | -0.021 [-0.511, +0.397] |
| D | 27% / 29% | -0.79% / -1.32% | +4.63% / +3.91% | +16.90% / +17.16% | -15.28% / -14.16% | 0.937 | 1✓ 2✓ 3✓ 4✓ 5✓ 6✓ | 0.30% + 0.04% | -0.388 [-0.639, -0.021] |

Gate failures:
- A: G2 worst 14-day R -54.75% vs BTC_HOLD -42.20% (must be higher)
- A: G3 cells below -10%: down/midvol -12.2%, down/highvol -13.6%
- A: G6 STRESS (n=20): worst -54.75% vs BTC_HOLD -42.20%, median +15.40% vs -0.66% (both must be >=)
- B: G2 worst 14-day R -48.58% vs BTC_HOLD -42.20% (must be higher)
- B: G3 cells below -10%: down/midvol -12.1%, down/highvol -14.3%
- B: G6 STRESS (n=20): worst -48.58% vs BTC_HOLD -42.20%, median +16.00% vs -0.66% (both must be >=)
- C: G2 worst 14-day R -48.19% vs BTC_HOLD -42.20% (must be higher)
- C: G3 cells below -10%: down/midvol -11.2%, down/highvol -13.0%
- C: G6 STRESS (n=20): worst -48.19% vs BTC_HOLD -42.20%, median +14.99% vs -0.66% (both must be >=)

Report-only robustness (REL FLOORED by layer):

| Run | Live-like | Recency | Flat (all windows) |
|---|---|---|---|
| ref: team_rot_ew | 1.268 | 1.454 | 2.631 |
| A **preferred** | 1.300 | 1.515 | 2.870 |
| B | 1.325 | 1.284 | 2.501 |
| C | 1.370 | 1.148 | 2.354 |
| D | 0.981 | 0.834 | 2.501 |
