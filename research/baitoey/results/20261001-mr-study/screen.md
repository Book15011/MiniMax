# Mean-reversion study: SCREEN (2022-07 to 2024-06) only

| Run | Return gate passed | Median R | 75th pct R | 90th pct R | Worst 10% R | Turnover/day | Fees + spread per window | Min active days |
|---|---|---|---|---|---|---|---|---|
| ref: team_rot_ew (core @24h) | 39% | +0.55% | +6.64% | +16.62% | -11.71% | 0.21 | 0.30% + 0.05% | 14 |
| MR_4h **chosen** | 29% | +0.79% | +3.75% | +7.37% | -8.04% | 0.28 | 0.39% + 0.06% | 14 |
| MR_24h | 26% | +0.00% | +0.94% | +2.92% | -4.07% | 0.06 | 0.08% + 0.01% | 14 |
| DIP_4h **chosen** | 43% | +0.93% | +8.17% | +19.17% | -11.44% | 0.20 | 0.28% + 0.04% | 14 |
| DIP_24h | 38% | +0.99% | +7.28% | +15.69% | -11.96% | 0.15 | 0.21% + 0.03% | 14 |
| CORE_4h | 43% | +0.87% | +7.55% | +15.74% | -12.01% | 0.28 | 0.40% + 0.06% | 14 |

Rule: per family, lowest mean rank over return-gate pass share, median R, 75th pct R and worst-10% R (ties: lower turnover). MR: {'MR_4h': 1.25, 'MR_24h': 1.75}; DIP: {'DIP_4h': 1.25, 'DIP_24h': 1.75}
