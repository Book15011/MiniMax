# A mid-frequency volume-spike strategy against e20v45

Pre-registration: `research/baitoey/prereg/20261005-mft.md`. 379 rounds (2025-09-02 12:00 to 2026-09-15 12:00 starts), 56 coins.

| Strategy | Clears the bars | Top-20 proxy | Mean R | Median R | Worst R | Rounds > 0 | Trades per round | Fees + spread per round | Whole year |
|---|---|---|---|---|---|---|---|---|---|
| e20v45 (live, same rounds) | 71% | 0.499 | +7.87% | +0.65% | -18.48% | 73% | — | — | — |
| M4: 3x spike, hold 4 h, market | 15% | 0.029 | -8.35% | -12.73% | -33.78% | 21% | 467 | +10.36% | -96.13% |
| M1: 3x spike, hold 1 h, market | 4% | 0.000 | -15.18% | -16.86% | -28.51% | 6% | 834 | +17.96% | -99.34% |
| M4K5: 5x spike, hold 4 h, market | 17% | 0.031 | -4.29% | -5.47% | -22.37% | 21% | 233 | +5.36% | -78.80% |
| M4L: 3x spike, hold 4 h, limit-first entry | 18% | 0.032 | -6.85% | -11.49% | -32.70% | 25% | 467 | +9.55% | -93.98% |

- M4 vs e20v45 on the same rounds; neighbours M1 and M4K5 -> **NO CANDIDATE**.
