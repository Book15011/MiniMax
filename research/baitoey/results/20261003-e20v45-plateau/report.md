# Robustness check of pol_switch_vt_tl_e20v45 (scoring v2)

Pre-registration: `research/baitoey/prereg/20261003-e20v45-plateau.md`. One setting changed per run;
neighbours scored like `--score`, not registered. Type columns: hit rate (mean of the three bars) by BTC's
14-day move (<= -5% / -5..0% / 0..+5% / >= +5%) and in the most volatile windows.

| Run | Change | HEADLINE_RET | vs E0 | without post-holdout | Strong fall | Mild fall | Mild rise | Strong rise | Volatile | Median / mean R | Worst R | Round 1 · Final | Guard share | Fees | Hard gates |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E0 | none (base) | **0.568** | +0.000 | 0.501 | 36% | 44% | 61% | 80% | 35% | +1.7% / +4.8% | -26.2% | +3.4% #2/47 · +0.2% #9/16 | 36% | +0.53% | pass |
| vt_mom | reference | **0.609** | +0.041 | 0.556 | 20% | 47% | 72% | 90% | 37% | +2.6% / +4.9% | -30.9% | -3.0% #31/47 · +9.6% #2/16 | 48% | +0.36% | pass |
| E1 | switch EMA 15 days | **0.565** | -0.003 | 0.497 | 36% | 44% | 60% | 79% | 35% | +1.7% / +4.8% | -26.2% | +3.4% #2/47 · +0.2% #9/16 | 36% | +0.54% | pass |
| E2 | switch EMA 25 days | **0.577** | +0.009 | 0.499 | 43% | 49% | 56% | 78% | 34% | +1.8% / +5.1% | -26.6% | +3.4% #2/47 · +0.2% #9/16 | 36% | +0.53% | pass |
| E3 | switch band 2% | **0.539** | -0.030 | 0.490 | 35% | 47% | 53% | 74% | 32% | +1.2% / +2.6% | -26.2% | -1.3% #20/47 · +7.0% #3/16 | 35% | +0.56% | pass |
| E4 | switch band 4% | **0.565** | -0.003 | 0.482 | 43% | 45% | 56% | 78% | 37% | +1.5% / +5.1% | -27.7% | -0.2% #16/47 · +0.2% #9/16 | 36% | +0.53% | pass |
| E5 | momentum cap 3.5%/day | **0.570** | +0.001 | 0.500 | 37% | 45% | 61% | 79% | 34% | +1.7% / +4.5% | -25.7% | +3.4% #2/47 · +0.2% #9/16 | 36% | +0.50% | pass |
| E6 | momentum cap 5.5%/day | **0.567** | -0.001 | 0.499 | 36% | 44% | 60% | 80% | 35% | +1.5% / +4.8% | -30.4% | +3.4% #2/47 · +0.2% #9/16 | 36% | +0.54% | pass |

- Score holds (hard gates and HEADLINE_RET >= 0.538): yes; below: none.
- Falls edge holds (strong-fall hit >= 30.4%, vt_mom + 10 points): yes; failing: none.

**Verdict: ROBUST.**
Tool version(s): 3036a0d8bfdaa6a0.
