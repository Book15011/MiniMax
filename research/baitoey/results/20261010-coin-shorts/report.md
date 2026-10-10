# e20v45 plus failed-rally shorts on other coins: results

Pre-registration: `research/baitoey/prereg/20261010-e20-coin-shorts.md` (9dc8849).

| Model | Weak 228 h median / p10 / p90 | All rounds median / p10 / p90 | HEADLINE / REL SCREEN / CONFIRM | Gates | Fees per round | Board rank (conservative) |
|---|---|---|---|---|---|---|
| e20v45 (live) | -2.88% / -11.44% / +19.75% | +0.30% / -12.09% / +23.62% | 0.568 / 2.244 / 3.002 | all pass | +0.61% | 41 (-7.29%) |
| e20v45 + BTC short (C) | -2.23% / -9.78% / +19.03% | +0.44% / -12.31% / +23.31% | 0.548 / 2.205 / 3.169 | all pass | +0.63% | 40 (-7.06%) |
| e20v45 + ETH short (C) | -2.61% / -10.57% / +19.03% | +0.24% / -12.57% / +23.61% | 0.543 / 2.108 / 3.168 | all pass | +0.63% | 43 (-7.31%) |
| e20v45 + SOL short (C) | -2.23% / -10.30% / +19.03% | +0.44% / -13.06% / +23.44% | 0.533 / 2.201 / 3.036 | all pass | +0.64% | 31 (-6.62%) |
| e20v45 + 6-altcoin basket shorts (C) | -2.35% / -10.01% / +19.03% | +0.55% / -12.56% / +23.45% | 0.559 / 2.124 / 3.129 | all pass | +0.65% | 39 (-7.01%) |

Better than e20v45 (pre-registered rule): weak median and p10 at least e20v45's, REL SCREEN and CONFIRM each >= e20v45's - 0.05, no hard gate fails.

- e20v45 + ETH short (C): not better.
- e20v45 + SOL short (C): **better**.
- e20v45 + 6-altcoin basket shorts (C): not better.

Short trades while the switch reads down (2020-06 to 2026-09, after 0.3% round-trip costs):

| Coin | Trades | Hit rate | Average | Worst | Squeeze +5% / +10% within 72 h |
|---|---|---|---|---|---|
| BTC | 87 | 45% | -0.03% | -10.06% | 23% / 7% |
| ETH | 85 | 33% | -0.58% | -10.37% | 36% / 12% |
| SOL | 68 | 24% | +0.08% | -8.41% | 46% / 21% |

## This round on live prices (Book's replay engine, from cash at 4 Oct 12:00 UTC)

| Model | This round | Shorts now |
|---|---|---|
| e20v45 (live) | -6.72% (as of 10-10 21:00 HKT) | none |
| e20v45 + BTC short (C) | -6.72% (as of 10-10 21:00 HKT) | none |
| e20v45 + ETH short (C) | -6.72% (as of 10-10 21:00 HKT) | none |
| e20v45 + SOL short (C) | -6.72% (as of 10-10 21:00 HKT) | none |
| e20v45 + 6-altcoin basket shorts (C) | -6.72% (as of 10-10 21:00 HKT) | none |

## Recovery from -6.6% on day 6 (180 rounds like ours; the model's own last 8 days)

| Last 8 days with | Bad (p10) | Median | Good (p90) | Finish >= 0% | Finish >= +1% | Finish <= -10% |
|---|---|---|---|---|---|---|
| e20v45 (live) | -15.01% | -6.87% | +6.97% | 23% | 18% | 25% |
| e20v45 + BTC short (C) | -13.79% | -6.32% | +7.35% | 23% | 21% | 24% |
| e20v45 + ETH short (C) | -14.35% | -6.49% | +8.42% | 24% | 21% | 24% |
| e20v45 + SOL short (C) | -15.01% | -6.53% | +8.24% | 26% | 20% | 26% |
| e20v45 + 6-altcoin basket shorts (C) | -15.02% | -6.40% | +9.37% | 23% | 21% | 25% |

## Recovery from -8.4% on day 6 (139 rounds like ours; the model's own last 8 days)

| Last 8 days with | Bad (p10) | Median | Good (p90) | Finish >= 0% | Finish >= +1% | Finish <= -10% |
|---|---|---|---|---|---|---|
| e20v45 (live) | -16.66% | -9.04% | +3.21% | 15% | 13% | 42% |
| e20v45 + BTC short (C) | -16.76% | -8.21% | +5.56% | 16% | 14% | 38% |
| e20v45 + ETH short (C) | -17.76% | -8.21% | +6.43% | 17% | 14% | 38% |
| e20v45 + SOL short (C) | -17.08% | -9.05% | +3.24% | 16% | 13% | 42% |
| e20v45 + 6-altcoin basket shorts (C) | -16.81% | -8.74% | +6.10% | 18% | 15% | 41% |
