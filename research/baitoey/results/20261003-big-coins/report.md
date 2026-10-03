# Trade only the biggest coins? (scoring v2)

Pre-registration: `research/baitoey/prereg/20261003-big-coins.md`. Variants keep the top N of the usual
Roostoo universe by trailing 30-day traded value; scored like `--score`, not registered. Type columns: hit
rate (mean of the three bars) by BTC's 14-day move (<= -5% / -5..0% / 0..+5% / >= +5%) and in the most
volatile windows.

| Run | Coins | HEADLINE_RET | vs base | without post-holdout | CS_HIT | Strong fall | Mild fall | Mild rise | Strong rise | Volatile | Median / mean R | Worst R | Round 1 · Final | Fees | Hard gates | Same bars | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| V0 | all | **0.609** | +0.000 | 0.556 | 0.368 | 20% | 47% | 72% | 90% | 37% | +2.6% / +4.9% | -30.9% | -3.0% #31/47 · +9.6% #2/16 | +0.36% | pass | — | base |
| E0 | all | **0.568** | +0.000 | 0.501 | 0.384 | 36% | 44% | 61% | 80% | 35% | +1.7% / +4.8% | -26.2% | +3.4% #2/47 · +0.2% #9/16 | +0.53% | pass | — | base |
| V10 | top 10 | **0.500** | -0.109 | 0.447 | 0.335 | 9% | 32% | 58% | 88% | 36% | +0.7% / +2.5% | -29.9% | -3.8% #34/47 · +12.6% #2/16 | +0.26% | pass | yes | worse |
| E10 | top 10 | **0.467** | -0.101 | 0.377 | 0.345 | 31% | 36% | 43% | 74% | 34% | -0.1% / +2.6% | -24.5% | -3.2% #32/47 · -1.5% #12/16 | +0.44% | pass | yes | worse |
| V15 | top 15 | **0.514** | -0.095 | 0.480 | 0.320 | 9% | 33% | 66% | 84% | 36% | +0.9% / +2.5% | -30.3% | +0.8% #5/47 · +6.6% #3/16 | +0.31% | pass | yes | worse |
| E15 | top 15 | **0.474** | -0.094 | 0.420 | 0.344 | 37% | 32% | 49% | 70% | 33% | +0.1% / +2.6% | -28.8% | +3.4% #2/47 · -2.6% #13/16 | +0.49% | pass | yes | worse |

- `baitoey_vt_mom`: V10 worse, V15 worse -> **DO NOT PROPOSE**.
- `pol_switch_vt_tl_e20v45`: E10 worse, E15 worse -> **DO NOT PROPOSE**.

Tool version(s): 258275c1ce3ad397, 3036a0d8bfdaa6a0, d592fb2e30e99d6e.

Note: the variants show tool versions 258275c1ce3ad397 (top 10) and d592fb2e30e99d6e (top 15) only because the tool
version hashes the market notes, where each variant records `universe_top_n`. Code files and scoring settings are those
of 3036a0d8bfdaa6a0, and the benchmark runs that set the bars are the cached ones ("Same bars: yes").
