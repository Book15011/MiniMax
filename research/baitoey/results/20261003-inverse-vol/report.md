# Inverse-volatility weights instead of equal weights? (scoring v2)

Pre-registration: `research/baitoey/prereg/20261003-inverse-vol.md`. Scored like `--score`, not registered.
Type columns: hit rate (mean of the three bars) by BTC's 14-day move (<= -5% / -5..0% / 0..+5% / >= +5%)
and in the most volatile windows.

| Run | Weights | HEADLINE_RET | vs base | without post-holdout | CS_HIT | Strong fall | Mild fall | Mild rise | Strong rise | Volatile | Median / mean R | Worst R | Round 1 · Final | Fees | Mean invested | Hard gates | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| V0 | equal (base) | **0.609** | +0.000 | 0.556 | 0.368 | 20% | 47% | 72% | 90% | 37% | +2.6% / +4.9% | -30.9% | -3.0% #31/47 · +9.6% #2/16 | +0.36% | 72% | pass | base |
| E0 | equal (base) | **0.568** | +0.000 | 0.501 | 0.384 | 36% | 44% | 61% | 80% | 35% | +1.7% / +4.8% | -26.2% | +3.4% #2/47 · +0.2% #9/16 | +0.53% | 79% | pass | base |
| VIV | inverse vol | **0.559** | -0.050 | 0.540 | 0.360 | 20% | 42% | 60% | 89% | 39% | +1.5% / +3.5% | -30.2% | -1.9% #21/47 · +10.2% #2/16 | +0.39% | 79% | pass | worse |
| EIV | inverse vol | **0.522** | -0.046 | 0.475 | 0.385 | 39% | 40% | 50% | 77% | 34% | +0.6% / +3.4% | -24.9% | +2.9% #3/47 · -0.4% #9/16 | +0.54% | 80% | pass | worse |

- VIV worse, EIV worse -> **DO NOT PROPOSE**.

Tool version(s): 3036a0d8bfdaa6a0.
