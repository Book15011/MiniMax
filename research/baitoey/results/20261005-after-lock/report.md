# After the lock-in fires: cash or another strategy? (scoring v2)

Pre-registration: `research/baitoey/prereg/20261005-after-lock.md`. e20v45's cached paths, method of Pol's endgame2.py.
Check: e20v45 without the lock gives HEADLINE_RET 0.5682 (registered 0.5682).

| Run | After the lock fires | HEADLINE_RET | vs L0 | CS_HIT | Top-20 proxy | Mean R | Worst R |
|---|---|---|---|---|---|---|---|
| L0 | cash (as launched) | **0.608** | +0.000 | 0.470 | 0.390 | +3.99% | -26.15% |
| AMR | mean reversion (pol_mr_cap) | **0.586** | -0.022 | 0.484 | 0.355 | +4.04% | -26.15% |
| ATR | BTC/ETH trend (team_trend_2) | **0.584** | -0.024 | 0.446 | 0.342 | +4.17% | -26.15% |
| AHALF | keep half in e20v45 | **0.600** | -0.008 | 0.465 | 0.372 | +4.42% | -26.15% |

- Better than cash: none -> **KEEP CASH AFTER THE LOCK**.

Tool version: 3036a0d8bfdaa6a0.
