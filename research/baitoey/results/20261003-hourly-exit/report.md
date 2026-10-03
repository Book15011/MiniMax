# Volume exit every hour, and a 5% cut-and-rebuy, on a 5% band (scoring v2)

Pre-registration: `research/baitoey/prereg/20261003-hourly-exit.md`. Scored like `--score`, not registered.
Type columns: hit rate (mean of the three bars) by BTC's 14-day move (<= -5% / -5..0% / 0..+5% / >= +5%)
and in the most volatile windows.

| Run | Change | HEADLINE_RET | vs base | without post-holdout | CS_HIT | Strong fall | Mild fall | Mild rise | Strong rise | Volatile | Median / mean R | Worst R | Round 1 · Final | Fees | Hard gates | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E0 | none (daily, base) | **0.568** | +0.000 | 0.501 | 0.384 | 36% | 44% | 61% | 80% | 35% | +1.7% / +4.8% | -26.2% | +3.4% #2/47 · +0.2% #9/16 | +0.53% | pass | — |
| EC | hourly wrapper, no rule | **0.567** | -0.001 | 0.500 | 0.381 | 37% | 43% | 60% | 80% | 34% | +1.5% / +4.8% | -25.8% | +3.4% #2/47 · +0.6% #8/16 | +0.53% | pass | — |
| EX | volume exit every hour | **0.517** | -0.052 | 0.449 | 0.385 | 27% | 39% | 56% | 77% | 33% | +0.8% / +4.1% | -26.6% | +3.4% #2/47 · -0.3% #9/16 | +0.54% | pass | worse |
| ES5 | cut at -5%, rebuy at 16:00 | **0.541** | -0.027 | 0.462 | 0.376 | 32% | 48% | 52% | 77% | 37% | +1.0% / +4.5% | -25.4% | +2.9% #3/47 · -2.7% #13/16 | +0.76% | pass | no clear difference |
| V0 | none (daily, base) | **0.609** | +0.000 | 0.556 | 0.368 | 20% | 47% | 72% | 90% | 37% | +2.6% / +4.9% | -30.9% | -3.0% #31/47 · +9.6% #2/16 | +0.36% | pass | — |
| VC | hourly wrapper, no rule | **0.609** | -0.000 | 0.556 | 0.369 | 20% | 47% | 72% | 90% | 37% | +2.6% / +4.9% | -30.9% | -3.0% #31/47 · +11.3% #2/16 | +0.36% | pass | — |
| VX | volume exit every hour | **0.570** | -0.039 | 0.526 | 0.359 | 19% | 40% | 68% | 88% | 35% | +1.9% / +4.2% | -28.9% | -2.9% #30/47 · +10.7% #2/16 | +0.36% | pass | worse |

- Control on the 5% band vs the daily model: -0.001 (within 0.01).
- EX against EC: changed 75% of rounds (helped 24%, hurt 51%), mean change there -1.04%.
- ES5 against EC: changed 96% of rounds (helped 42%, hurt 54%), mean change there -1.12%.
- VX against VC: changed 87% of rounds (helped 31%, hurt 56%), mean change there -0.71%.
- Hourly volume exit: EX worse, VX worse -> **DO NOT PROPOSE**.
- 5% cut-and-rebuy: ES5 no clear difference -> **DO NOT PROPOSE**.

Tool version(s): 3036a0d8bfdaa6a0.
