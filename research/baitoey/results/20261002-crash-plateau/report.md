# Robustness check of the crash rule pol_abl_shock (scoring v2)

Pre-registration: `research/baitoey/prereg/20261002-crash-rule-plateau.md`. One setting changed per run;
neighbours scored like `--score`, not registered. Type columns: hit rate (mean of the three bars) by BTC's
14-day move (<= -5% / -5..0% / 0..+5% / >= +5%) and in the most volatile windows.

| Run | Change | HEADLINE_RET | vs S0 | without post-holdout | Strong fall | Mild fall | Mild rise | Strong rise | Volatile | Median / mean R | Worst R | Round 1 · Final | Guard share | Fees | Hard gates |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S0 | none (base) | **0.607** | +0.000 | 0.555 | 24% | 47% | 70% | 89% | 32% | +2.5% / +4.7% | -26.8% | -3.0% #31/47 · +11.3% #2/16 | 47% | +0.38% | pass |
| vt_mom | reference | **0.609** | +0.001 | 0.556 | 20% | 47% | 72% | 90% | 37% | +2.6% / +4.9% | -30.9% | -3.0% #31/47 · +9.6% #2/16 | 48% | +0.36% | pass |
| S1 | drop threshold 4% | **0.597** | -0.010 | 0.543 | 24% | 45% | 69% | 88% | 25% | +2.3% / +4.6% | -26.8% | -3.0% #31/47 · +11.3% #2/16 | 45% | +0.41% | pass |
| S2 | drop threshold 6% | **0.604** | -0.003 | 0.551 | 20% | 47% | 71% | 89% | 33% | +2.6% / +4.7% | -27.2% | -3.0% #31/47 · +11.3% #2/16 | 48% | +0.37% | pass |
| S3 | drop window 2 h | **0.608** | +0.000 | 0.555 | 20% | 47% | 72% | 89% | 37% | +2.6% / +4.7% | -26.6% | -3.0% #31/47 · +11.3% #2/16 | 48% | +0.38% | pass |
| S4 | drop window 8 h | **0.607** | -0.001 | 0.556 | 25% | 46% | 70% | 89% | 31% | +2.6% / +4.7% | -26.6% | -3.0% #31/47 · +11.3% #2/16 | 46% | +0.40% | pass |
| S5 | cash pause 12 h | **0.612** | +0.005 | 0.563 | 23% | 48% | 71% | 89% | 35% | +2.6% / +4.8% | -28.5% | -3.0% #31/47 · +11.3% #2/16 | 48% | +0.40% | pass |
| S6 | cash pause 48 h | **0.615** | +0.007 | 0.567 | 28% | 46% | 71% | 89% | 30% | +2.9% / +4.9% | -26.8% | -3.0% #31/47 · +11.3% #2/16 | 46% | +0.37% | pass |

- Score holds (hard gates and HEADLINE_RET >= 0.577): yes; below: none.
- Insurance holds (worst R above vt_mom's -30.9%): yes; failing: none.

**Verdict: ROBUST.**
Tool version(s): 3036a0d8bfdaa6a0.
