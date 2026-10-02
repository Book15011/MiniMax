# Dual-momentum study (scoring v2)

Pre-registration: `research/baitoey/prereg/20261002-dual-momentum.md`. D0 is on the leaderboard; Dm and Dp
are scored like `--score` but not registered. Type columns: hit rate (mean of the three bars) in windows where
BTC moved <= -5% / -5..0% / 0..+5% / >= +5% over the 14 days.

| Run | Change | HEADLINE_RET | without post-holdout | Strong fall | Mild fall | Mild rise | Strong rise | Median / mean R | Worst R | Round 1 · Final | Mean gross | Guard share | Fees | Hard gates |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| D0 | min_score 0 (registered) | **0.587** | 0.541 | 24% | 48% | 64% | 86% | +1.8% / +4.4% | -23.5% | -2.4% #24/47 · +9.3% #2/16 | 57% | 31% | +0.41% | pass |
| vt_mom | reference | **0.609** | 0.556 | 20% | 47% | 72% | 90% | +2.6% / +4.9% | -30.9% | -3.0% #31/47 · +9.6% #2/16 | 72% | 48% | +0.36% | pass |
| vt_mom + crash rule | reference | **0.607** | 0.555 | 24% | 47% | 70% | 89% | +2.5% / +4.7% | -26.8% | -3.0% #31/47 · +11.3% #2/16 | 70% | 47% | +0.38% | pass |
| Dm | min_score -0.25 | **0.604** | 0.560 | 23% | 50% | 67% | 89% | +2.4% / +4.9% | -22.9% | -1.4% #20/47 · +9.6% #2/16 | 63% | 36% | +0.41% | pass |
| Dp | min_score +0.25 | **0.559** | 0.510 | 25% | 45% | 61% | 82% | +1.2% / +4.0% | -21.0% | +1.0% #4/47 · +7.1% #3/16 | 50% | 26% | +0.40% | pass |

D0 on the leaderboard: rank 1 of the candidates; tie group vs the top: **yes** [-0.048, +0.006].

- Keeps the score (hard gates pass and HEADLINE_RET >= 0.579): D0 yes, Dm yes, Dp NO.
- Improves falls (strong-fall hit >= 25.4% and worst R above -30.9%): NO (D0: 23.7%, -23.5%).

**Verdict: NOT A CANDIDATE.**
Tool version(s): 3036a0d8bfdaa6a0.
