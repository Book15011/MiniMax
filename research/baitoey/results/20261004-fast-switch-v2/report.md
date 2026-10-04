# Act at once on real BTC state flips, v2 on the decision grid (scoring v2)

Pre-registration: `research/baitoey/prereg/20261004-fast-switch.md` and its addendum `20261004-fast-switch-v2.md`.
Scored like `--score`, not registered.

| Run | Rule | HEADLINE_RET | vs E0 | without post-holdout | CS_HIT | Strong fall | Mild fall | Mild rise | Strong rise | Median / mean R | Worst R | Round 1 · Final | Fees | Hard gates |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E0 | daily at 16:00, EMA 20 (base) | **0.568** | +0.000 | 0.501 | 0.384 | 36% | 44% | 61% | 80% | +1.7% / +4.8% | -26.2% | +3.4% #2/47 · +0.2% #9/16 | +0.53% | pass |
| C20 | hourly wrapper, never at once, EMA 20 (v1 control) | **0.567** | -0.001 | 0.500 | 0.381 | 37% | 43% | 60% | 80% | +1.5% / +4.8% | -25.8% | +3.4% #2/47 · +0.6% #8/16 | +0.53% | pass |
| G20 | at once on real up_and_down flips (decision grid), EMA 20 | **0.548** | -0.020 | 0.470 | 0.393 | 36% | 43% | 57% | 77% | +1.3% / +4.7% | -30.0% | -0.7% #18/47 · +0.2% #9/16 | +0.54% | pass |
| GD20 | at once on real down flips (decision grid), EMA 20 | **0.563** | -0.005 | 0.494 | 0.383 | 36% | 43% | 60% | 79% | +1.4% / +4.7% | -29.8% | -0.7% #18/47 · +0.6% #8/16 | +0.54% | pass |
| E1 | daily at 16:00, EMA 15 | **0.565** | -0.003 | 0.497 | 0.385 | 36% | 44% | 60% | 79% | +1.7% / +4.8% | -26.2% | +3.4% #2/47 · +0.2% #9/16 | +0.54% | pass |
| G15 | at once on real up_and_down flips (decision grid), EMA 15 | **0.552** | -0.016 | 0.475 | 0.389 | 39% | 44% | 57% | 77% | +1.2% / +4.7% | -30.3% | -0.7% #18/47 · +0.2% #9/16 | +0.55% | pass |
| E2 | daily at 16:00, EMA 25 | **0.577** | +0.009 | 0.499 | 0.373 | 43% | 49% | 56% | 78% | +1.8% / +5.1% | -26.6% | +3.4% #2/47 · +0.2% #9/16 | +0.53% | pass |
| G25 | at once on real up_and_down flips (decision grid), EMA 25 | **0.565** | -0.003 | 0.484 | 0.370 | 41% | 46% | 56% | 78% | +1.4% / +4.8% | -28.2% | -0.7% #18/47 · +0.2% #9/16 | +0.54% | pass |

- G20 not better; neighbours hold -> **KEEP DECIDING AT 16:00 UTC**.

Tool version(s): 3036a0d8bfdaa6a0.
