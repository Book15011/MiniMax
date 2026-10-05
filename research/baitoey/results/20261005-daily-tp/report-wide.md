# A daily take-profit on e20v45 (scoring v2)

Pre-registration: `research/baitoey/prereg/20261005-daily-tp.md`. e20v45's cached paths, method of Pol's endgame2.py.
Check: e20v45 without the lock gives HEADLINE_RET 0.5682 (registered 0.5682).

| Run | Rule | HEADLINE_RET | vs L0 | CS_HIT | Top-20 proxy | Mean R | Worst R | Take-profit exits per round |
|---|---|---|---|---|---|---|---|---|
| L0 | e20v45 + lock-in (as launched) | **0.608** | +0.000 | 0.470 | 0.390 | +3.99% | -26.15% | — |
| TP30 | daily take-profit +3%, plus lock-in | **0.541** | -0.067 | 0.457 | 0.289 | +2.01% | -27.94% | 2.2 |
| TP40 | daily take-profit +4%, plus lock-in | **0.574** | -0.034 | 0.453 | 0.324 | +2.79% | -27.60% | 1.2 |
| TP50 | daily take-profit +5%, plus lock-in | **0.597** | -0.011 | 0.446 | 0.338 | +3.18% | -27.31% | 0.9 |

- TP30 not better, TP40 not better, TP50 not better -> **KEEP THE STRATEGY AS LAUNCHED**.

Tool version: 3036a0d8bfdaa6a0.
