# e20v45 with cash in down mode (scoring v2)

Pre-registration: `research/baitoey/prereg/20261004-down-cash.md`. Scored like `--score`, not registered. Type
columns: hit rate (mean of the three bars) by BTC's 14-day move (<= -5% / -5..0% / 0..+5% / >= +5%) and in the
most volatile windows.

| Run | Down mode | HEADLINE_RET | vs E0 | without post-holdout | CS_HIT | Strong fall | Mild fall | Mild rise | Strong rise | Volatile | Median / mean R | Worst R | Round 1 · Final | Fees | Hard gates |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E0 | long/short trend, EMA 20 (base) | **0.568** | +0.000 | 0.501 | 0.384 | 36% | 44% | 61% | 80% | 35% | +1.7% / +4.8% | -26.2% | +3.4% #2/47 · +0.2% #9/16 | +0.53% | pass |
| DC20 | cash, EMA 20 | **0.505** | -0.063 | 0.411 | 0.356 | 22% | 41% | 49% | 80% | 36% | -0.0% / +4.8% | -25.6% | -0.2% #16/47 · +3.8% #6/16 | +0.29% | pass |
| E1 | long/short trend, EMA 15 | **0.565** | -0.003 | 0.497 | 0.385 | 36% | 44% | 60% | 79% | 35% | +1.7% / +4.8% | -26.2% | +3.4% #2/47 · +0.2% #9/16 | +0.54% | pass |
| DC15 | cash, EMA 15 | **0.502** | -0.067 | 0.408 | 0.362 | 20% | 41% | 50% | 79% | 36% | -0.0% / +4.8% | -28.2% | -0.2% #16/47 · +3.8% #6/16 | +0.30% | pass |
| E2 | long/short trend, EMA 25 | **0.577** | +0.009 | 0.499 | 0.373 | 43% | 49% | 56% | 78% | 34% | +1.8% / +5.1% | -26.6% | +3.4% #2/47 · +0.2% #9/16 | +0.53% | pass |
| DC25 | cash, EMA 25 | **0.526** | -0.042 | 0.434 | 0.362 | 30% | 45% | 47% | 82% | 32% | +0.0% / +5.1% | -25.4% | -0.2% #16/47 · +3.8% #6/16 | +0.28% | pass |

- DC20 not better than E0; neighbours do not hold -> **KEEP THE TREND SLEEVE IN DOWN MODE**.
- With the live lock-in (report-only): E0 HEADLINE_RET 0.608, CS_HIT 0.470, worst -26.2%; DC20 0.538, CS_HIT 0.440, worst -25.6%.

Tool version(s): 3036a0d8bfdaa6a0.
