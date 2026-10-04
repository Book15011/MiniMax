# Act at once when the BTC state flips (scoring v2)

Pre-registration: `research/baitoey/prereg/20261004-fast-switch.md`. Scored like `--score`, not registered. Type
columns: hit rate (mean of the three bars) by BTC's 14-day move (<= -5% / -5..0% / 0..+5% / >= +5%) and in the
most volatile windows.

| Run | Rule | HEADLINE_RET | vs E0 | without post-holdout | CS_HIT | Strong fall | Mild fall | Mild rise | Strong rise | Volatile | Median / mean R | Worst R | Round 1 · Final | Fees | Hard gates |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E0 | daily at 16:00, EMA 20 (base) | **0.568** | +0.000 | 0.501 | 0.384 | 36% | 44% | 61% | 80% | 35% | +1.7% / +4.8% | -26.2% | +3.4% #2/47 · +0.2% #9/16 | +0.53% | pass |
| C20 | hourly wrapper, never at once, EMA 20 | **0.567** | -0.001 | 0.500 | 0.381 | 37% | 43% | 60% | 80% | 34% | +1.5% / +4.8% | -25.8% | +3.4% #2/47 · +0.6% #8/16 | +0.53% | pass |
| F20 | hourly, at once on up_and_down flips, EMA 20 | **0.531** | -0.037 | 0.440 | 0.395 | 40% | 46% | 50% | 74% | 33% | +1.0% / +4.2% | -27.6% | -5.8% #40/47 · -0.9% #11/16 | +0.80% | pass |
| FD20 | hourly, at once on down flips, EMA 20 | **0.525** | -0.043 | 0.435 | 0.387 | 36% | 43% | 52% | 74% | 33% | +0.9% / +4.0% | -29.7% | -1.1% #19/47 · +0.6% #8/16 | +0.71% | pass |
| E1 | daily at 16:00, EMA 15 | **0.565** | -0.003 | 0.497 | 0.385 | 36% | 44% | 60% | 79% | 35% | +1.7% / +4.8% | -26.2% | +3.4% #2/47 · +0.2% #9/16 | +0.54% | pass |
| F15 | hourly, at once on up_and_down flips, EMA 15 | **0.533** | -0.035 | 0.451 | 0.380 | 37% | 43% | 55% | 74% | 32% | +1.0% / +4.0% | -27.0% | -1.5% #21/47 · -0.9% #11/16 | +0.78% | pass |
| E2 | daily at 16:00, EMA 25 | **0.577** | +0.009 | 0.499 | 0.373 | 43% | 49% | 56% | 78% | 34% | +1.8% / +5.1% | -26.6% | +3.4% #2/47 · +0.2% #9/16 | +0.53% | pass |
| F25 | hourly, at once on up_and_down flips, EMA 25 | **0.520** | -0.048 | 0.422 | 0.388 | 39% | 40% | 50% | 75% | 32% | +0.8% / +4.1% | -34.2% | -5.8% #40/47 · -0.9% #11/16 | +0.79% | pass |

- F20 not better; neighbours do not hold -> **KEEP DECIDING AT 16:00 UTC**.

Tool version(s): 3036a0d8bfdaa6a0.

Note: v1 checked the state every hour, where its 6-hour sampling shifts with the hour; it triggered 932 times in 2020-2026 against 112 real flips, so it tested acting on flicker. See the addendum 20261004-fast-switch-v2.md.
