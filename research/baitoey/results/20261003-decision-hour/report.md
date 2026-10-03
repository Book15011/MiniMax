# Which hour should e20v45 decide at? (scoring v2)

Pre-registration: `research/baitoey/prereg/20261003-decision-hour.md`. All runs use the same hourly wrapper;
H16 (today's hour) is the control. Scored like `--score`, not registered. Type columns: hit rate (mean of the
three bars) by BTC's 14-day move (<= -5% / -5..0% / 0..+5% / >= +5%) and in the most volatile windows.

| Run | Decision hour | HEADLINE_RET | vs H16 | without post-holdout | CS_HIT | Strong fall | Mild fall | Mild rise | Strong rise | Volatile | Median / mean R | Worst R | Round 1 · Final | Fees | Hard gates |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| H00 | 00:00 UTC (08:00 HKT) | **0.510** | -0.037 | 0.482 | 0.331 | 34% | 37% | 51% | 77% | 32% | +0.4% / +3.4% | -32.9% | -2.3% #24/47 · +3.1% #6/16 | +0.52% | pass |
| H04 | 04:00 UTC (12:00 HKT) | **0.525** | -0.022 | 0.528 | 0.388 | 42% | 32% | 55% | 80% | 39% | +0.8% / +4.3% | -33.5% | -3.4% #34/47 · +0.2% #9/16 | +0.55% | pass |
| H08 | 08:00 UTC (16:00 HKT) | **0.502** | -0.045 | 0.478 | 0.374 | 39% | 31% | 54% | 76% | 32% | +0.2% / +4.0% | -26.6% | +0.5% #7/47 · -1.4% #12/16 | +0.56% | pass |
| H12 | 12:00 UTC (20:00 HKT) | **0.530** | -0.017 | 0.493 | 0.357 | 39% | 39% | 54% | 76% | 30% | +1.3% / +4.3% | -26.1% | -1.3% #20/47 · -1.7% #12/16 | +0.53% | pass |
| H16 | 16:00 UTC (00:00 HKT) | **0.547** | +0.000 | 0.497 | 0.400 | 36% | 41% | 56% | 80% | 34% | +1.6% / +4.8% | -26.2% | +3.4% #2/47 · +0.2% #9/16 | +0.53% | pass |
| H20 | 20:00 UTC (04:00 HKT) | **0.570** | +0.023 | 0.533 | 0.375 | 47% | 42% | 59% | 79% | 38% | +1.5% / +5.1% | -38.7% | -0.7% #18/47 · +2.9% #6/16 | +0.55% | pass |

- Spread of HEADLINE_RET across the six hours: 0.068. No hour beats 16:00 UTC by the margin on a plateau -> **KEEP 16:00 UTC**.

Tool version(s): 3036a0d8bfdaa6a0.
