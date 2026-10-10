# Fast large-cap trend long/short: results

Pre-registration: `research/baitoey/prereg/20261010-majors-trend.md` (df48129). Public reference: Pol's EMA 8/24 version scored 0.304 (reports/review/20261003-ext-baselines.md). Board: 94 models.

| Model | Weak 228 h median / p10 / p90 | All rounds median / p10 / p90 | HEADLINE / REL SCREEN / CONFIRM | Gates | Turnover / fees per round | Board rank (conservative) |
|---|---|---|---|---|---|---|
| e20v45 (live) | -2.88% / -11.44% / +19.75% | +0.30% / -12.09% / +23.62% | 0.568 / 2.244 / 3.002 | all pass | 5.31 / +0.61% | 39 (-7.24%) |
| EMA 6/24 daily | -0.08% / -5.09% / +7.32% | -1.40% / -11.61% / +9.18% | 0.321 / 1.177 / 1.822 | all pass | 13.64 / +1.37% | 82 (-10.50%) |
| EMA 6/24 6-hourly | -1.05% / -6.37% / +8.06% | -2.54% / -11.59% / +9.36% | 0.300 / 1.145 / 2.238 | all pass | 29.04 / +2.90% | 94 (-12.24%) |
| EMA 12/48 daily | -0.31% / -4.09% / +7.77% | -0.36% / -10.66% / +12.18% | 0.341 / 0.736 / 1.534 | all pass | 11.11 / +1.12% | 78 (-10.42%) |
| EMA 12/48 6-hourly | -1.46% / -5.91% / +6.60% | -1.01% / -10.74% / +11.23% | 0.314 / 0.710 / 1.654 | all pass | 18.80 / +1.88% | 93 (-12.21%) |
| EMA 24/96 daily | -0.38% / -6.84% / +10.88% | -0.13% / -9.77% / +13.34% | 0.351 / 0.971 / 1.416 | all pass | 8.05 / +0.81% | 81 (-10.47%) |
| EMA 24/96 6-hourly | -0.41% / -6.32% / +10.94% | -0.73% / -10.43% / +12.80% | 0.341 / 1.089 / 1.219 | all pass | 11.33 / +1.13% | 90 (-11.64%) |

Worth a forward paper test (pre-registered): conservative score above e20v45's, REL SCREEN and CONFIRM >= 1.0, no hard gate fails.

- EMA 6/24 daily: no.
- EMA 6/24 6-hourly: no.
- EMA 12/48 daily: no.
- EMA 12/48 6-hourly: no.
- EMA 24/96 daily: no.
- EMA 24/96 6-hourly: no.

## This round on live prices (Book's replay engine, from cash at 4 Oct 12:00 UTC)

| Model | This round | Holdings now |
|---|---|---|
| e20v45 (live) | -6.58% (as of 10-10 16:00 HKT) | WLD +17%, FET +16%, PUMP +16%, SUI +16%, AAVE +16%, FIL +15% |
| EMA 6/24 daily | +1.42% (as of 10-10 16:00 HKT) | BNB -30%, BTC +30%, SOL -20%, XRP -17% |
| EMA 6/24 6-hourly | +1.43% (as of 10-10 16:00 HKT) | SOL -30%, XRP +30% |
| EMA 12/48 daily | +0.77% (as of 10-10 16:00 HKT) | BNB -30%, ETH -27%, SOL -22%, XRP -18% |
| EMA 12/48 6-hourly | +3.07% (as of 10-10 16:00 HKT) | BNB -30%, ETH -27%, SOL -22% |
| EMA 24/96 daily | +1.32% (as of 10-10 16:00 HKT) | BTC -26%, BNB -25%, ETH -20%, SOL -16%, XRP -13% |
| EMA 24/96 6-hourly | +2.46% (as of 10-10 16:00 HKT) | BTC -26%, BNB -25%, ETH -20%, SOL -16%, XRP -13% |

## Recovery for the rest of the round, starting at -8.4% on day 6 (139 past rounds within 3 points, BTC 0 to -6%; last 8 days)

| Last 8 days with | Bad (p10) | Median | Good (p90) | Finish >= +1% | Finish <= -15% |
|---|---|---|---|---|---|
| stay with e20v45 | -16.66% | -9.04% | +3.21% | 13% | 14% |
| switch to EMA 6/24 daily | -14.60% | -8.91% | +0.13% | 9% | 9% |
| 70% e20v45 + 30% EMA 6/24 daily | -14.79% | -8.64% | -0.20% | 10% | 9% |
| switch to EMA 6/24 6-hourly | -14.46% | -9.11% | -1.79% | 7% | 6% |
| 70% e20v45 + 30% EMA 6/24 6-hourly | -14.74% | -8.94% | +0.22% | 9% | 9% |
| switch to EMA 12/48 daily | -13.90% | -8.45% | -0.96% | 8% | 6% |
| 70% e20v45 + 30% EMA 12/48 daily | -14.02% | -8.70% | +0.16% | 10% | 6% |
| switch to EMA 12/48 6-hourly | -14.83% | -8.50% | -0.26% | 8% | 9% |
| 70% e20v45 + 30% EMA 12/48 6-hourly | -13.97% | -8.46% | +0.06% | 10% | 9% |
| switch to EMA 24/96 daily | -15.31% | -8.57% | -1.78% | 6% | 12% |
| 70% e20v45 + 30% EMA 24/96 daily | -13.91% | -9.04% | +1.10% | 10% | 9% |
| switch to EMA 24/96 6-hourly | -14.14% | -8.01% | -0.55% | 8% | 6% |
| 70% e20v45 + 30% EMA 24/96 6-hourly | -13.62% | -9.13% | +1.93% | 11% | 8% |

## Recovery for the rest of the round, starting at -11.6% on day 6 (71 past rounds within 3 points, BTC 0 to -6%; last 8 days)

| Last 8 days with | Bad (p10) | Median | Good (p90) | Finish >= +1% | Finish <= -15% |
|---|---|---|---|---|---|
| stay with e20v45 | -19.07% | -12.98% | -3.81% | 4% | 27% |
| switch to EMA 6/24 daily | -16.82% | -12.83% | -7.34% | 0% | 25% |
| 70% e20v45 + 30% EMA 6/24 daily | -17.09% | -12.45% | -5.77% | 1% | 23% |
| switch to EMA 6/24 6-hourly | -18.77% | -13.02% | -6.11% | 1% | 34% |
| 70% e20v45 + 30% EMA 6/24 6-hourly | -17.71% | -12.89% | -6.70% | 1% | 27% |
| switch to EMA 12/48 daily | -17.05% | -13.27% | -7.01% | 0% | 25% |
| 70% e20v45 + 30% EMA 12/48 daily | -16.94% | -12.96% | -5.63% | 3% | 25% |
| switch to EMA 12/48 6-hourly | -18.08% | -13.24% | -7.11% | 0% | 34% |
| 70% e20v45 + 30% EMA 12/48 6-hourly | -16.74% | -13.02% | -5.71% | 3% | 27% |
| switch to EMA 24/96 daily | -16.68% | -11.94% | -6.56% | 0% | 30% |
| 70% e20v45 + 30% EMA 24/96 daily | -16.98% | -12.44% | -6.48% | 1% | 23% |
| switch to EMA 24/96 6-hourly | -16.81% | -11.98% | -5.28% | 0% | 20% |
| 70% e20v45 + 30% EMA 24/96 6-hourly | -16.64% | -12.88% | -6.25% | 3% | 25% |

## Recovery starting at -6.6% on day 6 (the replay at 10 Oct 16:00 HKT; 180 past rounds within 3 points; last 8 days)

| Last 8 days with | Bad (p10) | Median | Good (p90) | Finish >= +1% | Finish >= 0% | Finish <= -15% |
|---|---|---|---|---|---|---|
| stay with e20v45 | -15.01% | -6.87% | +6.97% | 18% | 23% | 10% |
| switch to EMA 6/24 daily | -13.22% | -7.37% | +1.63% | 11% | 11% | 7% |
| 70% e20v45 + 30% EMA 6/24 daily | -12.74% | -6.63% | +3.10% | 13% | 14% | 3% |
| switch to EMA 6/24 6-hourly | -13.23% | -7.82% | +0.13% | 9% | 11% | 7% |
| 70% e20v45 + 30% EMA 6/24 6-hourly | -13.29% | -6.93% | +2.55% | 13% | 14% | 4% |
| switch to EMA 12/48 daily | -11.34% | -6.27% | +2.29% | 13% | 16% | 4% |
| 70% e20v45 + 30% EMA 12/48 daily | -12.19% | -6.30% | +3.43% | 13% | 16% | 3% |
| switch to EMA 12/48 6-hourly | -12.30% | -6.59% | +2.11% | 13% | 15% | 4% |
| 70% e20v45 + 30% EMA 12/48 6-hourly | -12.48% | -6.32% | +3.94% | 13% | 16% | 4% |
| switch to EMA 24/96 daily | -12.70% | -6.35% | +0.41% | 8% | 11% | 3% |
| 70% e20v45 + 30% EMA 24/96 daily | -12.17% | -7.07% | +4.75% | 14% | 17% | 4% |
| switch to EMA 24/96 6-hourly | -12.21% | -5.86% | +2.52% | 13% | 17% | 3% |
| 70% e20v45 + 30% EMA 24/96 6-hourly | -11.78% | -7.04% | +5.03% | 15% | 18% | 3% |
