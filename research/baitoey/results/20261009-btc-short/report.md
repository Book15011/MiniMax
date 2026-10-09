# BTC-only short sleeve and e20v45 add-ons: results

Pre-registration: `research/baitoey/prereg/20261009-btc-short.md` (bc348ed).

## Standalone (BTC short 40% or cash)

| Variant | Weak 228 h median / p10 / p90 | All windows median / p10 / p90 | HEADLINE / REL SCREEN / CONFIRM | Gates | Fees per round | Board rank |
|---|---|---|---|---|---|---|
| A trend | -0.00% / -0.01% / +0.00% | -0.01% / -1.94% / +1.07% | 0.225 / 1.105 / 1.756 | FAIL G6_median | +0.05% | 57 (-9.67%) |
| B breakdown | -0.01% / -2.01% / +0.02% | -0.01% / -2.23% / +0.82% | 0.235 / 1.308 / 1.174 | FAIL G6_median | +0.06% | 61 (-9.98%) |
| C failed rally | -0.00% / -1.90% / +0.64% | -0.01% / -2.12% / +1.62% | 0.306 / 1.154 / 1.157 | FAIL G6_median | +0.06% | 60 (-9.96%) |
| D trend + funding | -0.00% / -0.01% / +0.00% | -0.01% / -1.90% / +0.84% | 0.218 / 1.105 / 1.703 | FAIL G6_median | +0.04% | 58 (-9.67%) |

Trades 2020-06 to 2026-09 (model's own replay; after 0.3% round-trip costs):

| Variant | Trades | Hit rate | Average | Worst trade | Squeeze rate (BTC +5% within 72 h) | Average hours held | Exits (stop / time / cover) |
|---|---|---|---|---|---|---|---|
| A trend | 65 | 38% | -0.42% | -7.50% | 18% | 127 | 29 / 36 / 0 |
| B breakdown | 85 | 36% | -0.72% | -8.62% | 26% | 118 | 35 / 44 / 6 |
| C failed rally | 98 | 44% | -0.17% | -10.06% | 21% | 119 | 43 / 55 / 0 |
| D trend + funding | 63 | 37% | -0.51% | -7.63% | 17% | 128 | 29 / 34 / 0 |

## Add-on to e20v45 (short only while its switch reads down)

| Model | Weak 228 h median / p10 / p90 | All windows median / p10 / p90 | HEADLINE / REL SCREEN / CONFIRM | Gates | Fees per round | Board rank |
|---|---|---|---|---|---|---|
| e20v45 (base) | -2.88% / -11.44% / +19.75% | +0.30% / -12.09% / +23.62% | 0.568 / 2.244 / 3.002 | all pass | +0.61% | 36 (-6.99%) |
| e20v45 decided hourly (context: the hourly-wrapper effect) | -2.88% / -11.42% / +19.03% | +0.17% / -12.09% / +23.49% | 0.547 / 2.290 / 3.008 | all pass | +0.61% | 38 (-7.05%) |
| e20v45 + A trend | -2.88% / -12.73% / +19.03% | +0.33% / -12.51% / +23.61% | 0.544 / 2.225 / 3.200 | all pass | +0.63% | 44 (-7.26%) |
| e20v45 + B breakdown | -2.23% / -12.86% / +19.03% | -0.08% / -12.72% / +23.61% | 0.540 / 2.146 / 3.258 | all pass | +0.63% | 47 (-7.56%) |
| e20v45 + C failed rally | -2.23% / -9.78% / +19.03% | +0.44% / -12.31% / +23.31% | 0.548 / 2.205 / 3.169 | all pass | +0.63% | 35 (-6.76%) |
| e20v45 + D trend + funding | -2.88% / -12.73% / +19.03% | +0.37% / -12.44% / +23.61% | 0.544 / 2.225 / 3.215 | all pass | +0.63% | 45 (-7.26%) |

Add-on trades (2020-06 to 2026-09):

| Add-on | Trades | Hit rate | Worst trade | Squeeze rate |
|---|---|---|---|---|
| e20v45 + A trend | 64 | 39% | -7.50% | 20% |
| e20v45 + B breakdown | 81 | 37% | -8.62% | 28% |
| e20v45 + C failed rally | 87 | 45% | -10.06% | 23% |
| e20v45 + D trend + funding | 61 | 39% | -7.63% | 20% |

Reading rule (pre-registered): an add-on is better if its weak 228 h median and p10 are both at least e20v45's, REL SCREEN and CONFIRM each at least e20v45's minus 0.05, and no hard gate fails.

- e20v45 + A trend: not better than e20v45.
- e20v45 + B breakdown: not better than e20v45.
- e20v45 + C failed rally: **better** than e20v45.
- e20v45 + D trend + funding: not better than e20v45.

## From our situation (125 rounds: e20v45 down 5.4-11.4% on day 5, BTC 0 to -6%; the add-on's last 9 days of the same round; our -8.4% applied)

| Last 9 days with | Bad (p10) | Median | Good (p90) | Finish >= +1% | Finish <= -15% |
|---|---|---|---|---|---|
| e20v45 | -16.62% | -9.10% | +4.56% | 18% | 14% |
| e20v45 + A trend | -16.94% | -9.48% | +5.33% | 18% | 16% |
| e20v45 + B breakdown | -17.66% | -9.32% | +5.11% | 18% | 18% |
| e20v45 + C failed rally | -17.66% | -8.26% | +4.48% | 18% | 15% |
| e20v45 + D trend + funding | -16.94% | -9.48% | +5.33% | 18% | 16% |
