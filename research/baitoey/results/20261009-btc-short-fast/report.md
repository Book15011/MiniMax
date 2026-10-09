# Lower BTC-short triggers (A2 / B2): results

Pre-registration: `research/baitoey/prereg/20261009-btc-short-fast.md` (e922af9).

## Standalone

| Model | Weak 228 h median / p10 / p90 | All windows median / p10 / p90 | HEADLINE / REL SCREEN / CONFIRM | Gates | Fees per round | Board rank |
|---|---|---|---|---|---|---|
| A2 fast trend (20-day EMA -1%) | -0.01% / -1.97% / +1.29% | -0.01% / -2.20% / +1.67% | 0.285 / 0.706 / 2.161 | FAIL G6_median | +0.07% | 65 (-10.19%) |
| B2 fast breakdown (10-day low) | -0.00% / -2.42% / +1.29% | -0.01% / -2.43% / +2.16% | 0.332 / 1.493 / 1.448 | FAIL G6_median | +0.08% | 66 (-10.22%) |

| Variant | Trades | Hit rate | Average | Worst trade | Squeeze rate (BTC +5% within 72 h) | Exits (stop / time / cover) |
|---|---|---|---|---|---|---|
| A2 fast trend (20-day EMA -1%) | 112 | 43% | -0.18% | -9.07% | 21% | 35 / 61 / 16 |
| B2 fast breakdown (10-day low) | 125 | 36% | -0.38% | -9.07% | 29% | 42 / 50 / 33 |

## Add-on to e20v45 (not gated by its switch)

| Model | Weak 228 h median / p10 / p90 | All windows median / p10 / p90 | HEADLINE / REL SCREEN / CONFIRM | Gates | Fees per round | Board rank |
|---|---|---|---|---|---|---|
| e20v45 (base) | -2.88% / -11.44% / +19.75% | +0.30% / -12.09% / +23.62% | 0.568 / 2.244 / 3.002 | all pass | +0.61% | 39 (-7.03%) |
| e20v45 decided hourly (context) | -2.88% / -11.42% / +19.03% | +0.17% / -12.09% / +23.49% | 0.547 / 2.290 / 3.008 | all pass | +0.61% | 41 (-7.09%) |
| e20v45 + C failed rally (switch-gated, earlier run) | -2.23% / -9.78% / +19.03% | +0.44% / -12.31% / +23.31% | 0.548 / 2.205 / 3.169 | all pass | +0.63% | 38 (-6.80%) |
| e20v45 + A2 fast trend (20-day EMA -1%) | -2.23% / -9.96% / +12.43% | +0.23% / -12.30% / +23.17% | 0.537 / 2.169 / 2.902 | all pass | +0.64% | 37 (-6.70%) |
| e20v45 + B2 fast breakdown (10-day low) | -2.03% / -10.40% / +12.68% | -0.12% / -12.28% / +22.51% | 0.524 / 1.916 / 3.189 | all pass | +0.65% | 30 (-6.28%) |

Reading rule (pre-registered, as before): better if weak 228 h median and p10 both at least e20v45's, REL SCREEN and CONFIRM each at least e20v45's minus 0.05, no hard gate fails.

- e20v45 + A2 fast trend (20-day EMA -1%): not better than e20v45.
- e20v45 + B2 fast breakdown (10-day low): not better than e20v45.

## From our situation (125 rounds like ours; the model's last 9 days of the same round; our -8.4% applied)

| Last 9 days with | Bad (p10) | Median | Good (p90) | Finish >= +1% | Finish <= -15% |
|---|---|---|---|---|---|
| e20v45 | -16.62% | -9.10% | +4.56% | 18% | 14% |
| e20v45 + C (gated) | -17.66% | -8.26% | +4.48% | 18% | 15% |
| e20v45 + A2 fast trend (20-day EMA -1%) | -16.36% | -9.13% | +4.22% | 17% | 18% |
| e20v45 + B2 fast breakdown (10-day low) | -16.55% | -9.13% | +3.43% | 16% | 15% |

```
This round on live prices (Book's replay engine, from cash at 2026-10-04 12:00 UTC)
  pol_switch_vt_tl_e20v45    -11.60% as of 10-10 03:00 HKT | BTC short moves: [] | now {'AAVE': 16, 'WLD': 16, 'SUI': 16, 'FIL': 16, 'FET': 16, 'PUMP': 15}
  baitoey_btc_short_a2        -0.78% as of 10-10 03:00 HKT | BTC short moves: [('10-09 01:00', -40)] | now {'BTC': -40}
  baitoey_btc_short_b2        -0.78% as of 10-10 03:00 HKT | BTC short moves: [('10-09 01:00', -40)] | now {'BTC': -40}
  baitoey_e20_btcs_a2        -13.13% as of 10-10 03:00 HKT | BTC short moves: [('10-09 01:00', -40)] | now {'BTC': -40, 'AAVE': 10, 'WLD': 10, 'SUI': 10, 'FIL': 10, 'FET': 10, 'PUMP': 9}
  baitoey_e20_btcs_b2        -13.13% as of 10-10 03:00 HKT | BTC short moves: [('10-09 01:00', -40)] | now {'BTC': -40, 'AAVE': 10, 'WLD': 10, 'SUI': 10, 'FIL': 10, 'FET': 10, 'PUMP': 9}
```
