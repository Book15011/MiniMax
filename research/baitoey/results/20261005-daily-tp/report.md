# A daily take-profit on e20v45 (scoring v2)

Pre-registration: `research/baitoey/prereg/20261005-daily-tp.md`. e20v45's cached paths, method of Pol's endgame2.py.
Check: e20v45 without the lock gives HEADLINE_RET 0.5682 (registered 0.5682).

| Run | Rule | HEADLINE_RET | vs L0 | CS_HIT | Top-20 proxy | Mean R | Worst R | Take-profit exits per round |
|---|---|---|---|---|---|---|---|---|
| L0 | e20v45 + lock-in (as launched) | **0.608** | +0.000 | 0.470 | 0.390 | +3.99% | -26.15% | — |
| TP05 | daily take-profit +0.5%, plus lock-in | **0.367** | -0.241 | 0.386 | 0.163 | -1.15% | -24.87% | 8.6 |
| TP10 | daily take-profit +1%, plus lock-in | **0.502** | -0.105 | 0.403 | 0.228 | +0.59% | -25.91% | 6.3 |
| TP20 | daily take-profit +2%, plus lock-in | **0.548** | -0.060 | 0.387 | 0.290 | +1.42% | -26.92% | 3.5 |

- TP05 not better, TP10 not better -> **KEEP THE STRATEGY AS LAUNCHED**.

Tool version: 3036a0d8bfdaa6a0.
