# Momentum long-short at 60/40 and 50/50 (scoring v2)

Pre-registration: `research/baitoey/prereg/20261005-long-short-split.md`. Scored like `--score`, not registered.

| Model | HEADLINE_RET | Top-20 proxy | Strong fall | Mild fall | Mild rise | Strong rise | Median / mean R | Worst R | Round 1 · Final | With lock-in: HEADLINE_RET / CS_HIT / top-20 |
|---|---|---|---|---|---|---|---|---|---|---|
| e20v45 (live) | **0.568** | 0.365 | 36% | 44% | 61% | 80% | +1.7% / +4.8% | -26.2% | +3.4% #2/47 · +0.2% #9/16 | 0.608 / 0.470 / 0.390 |
| L75 (pol_mom_ss, registered) | **0.458** | 0.195 | 35% | 49% | 41% | 53% | +0.2% / +0.8% | -16.3% | +0.8% #4/47 · +3.2% #6/16 | 0.464 / 0.366 / 0.197 |
| L60 (60/40) | **0.442** | 0.226 | 55% | 55% | 34% | 37% | -0.0% / -0.1% | -25.5% | +1.5% #4/47 · +3.4% #6/16 | 0.444 / 0.326 / 0.236 |
| L50 (50/50) research only | **0.458** | 0.261 | 75% | 62% | 30% | 27% | -0.0% / -0.6% | -32.5% | +2.0% #4/47 · +3.6% #6/16 | 0.476 / 0.304 / 0.293 |

- L60 with the lock-in: HEADLINE_RET 0.444 vs e20v45 0.608, top-20 proxy 0.236 vs 0.390 -> **no candidate**.

Tool version: 3036a0d8bfdaa6a0.
