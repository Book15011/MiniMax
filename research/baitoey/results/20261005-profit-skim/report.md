# Skim profits to cash and keep trading only the original money (scoring v2)

Pre-registration: `research/baitoey/prereg/20261005-profit-skim.md`. e20v45's cached paths, method of Pol's endgame2.py.
Check: the unmodified path gives HEADLINE_RET 0.5682 (score file 0.5682).

| Run | Rule | HEADLINE_RET | vs L0 | CS_HIT | Top-20 proxy | Mean R | Worst R | Skim fired in |
|---|---|---|---|---|---|---|---|---|
| L0 | e20v45 + lock-in (as launched) | **0.608** | +0.000 | 0.470 | 0.390 | +3.99% | -26.15% | — |
| S2 | skim at +2%, plus lock-in | **0.608** | +0.001 | 0.475 | 0.373 | +3.63% | -26.15% | 79% of rounds |
| S3 | skim at +3%, plus lock-in | **0.608** | +0.000 | 0.477 | 0.374 | +3.63% | -26.15% | 70% of rounds |
| S5 | skim at +5%, plus lock-in | **0.610** | +0.002 | 0.471 | 0.378 | +3.66% | -26.15% | 56% of rounds |
| N3 | skim at +3%, no lock-in | **0.576** | -0.032 | 0.407 | 0.349 | +4.34% | -26.15% | 70% of rounds |
| N0 | e20v45, no lock-in, no skim | **0.568** | -0.040 | 0.384 | 0.365 | +4.84% | -26.15% | — |

- S2 / S3 / S5 against L0 -> **KEEP THE STRATEGY AS LAUNCHED**.

Tool version: 3036a0d8bfdaa6a0.
