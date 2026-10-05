# A one-step scalper on large-step coins against e20v45 (research only)

Pre-registration: `research/baitoey/prereg/20261005-scalp.md`. 379 rounds (2025-09-02 12:00 to 2026-09-15 12:00 starts); coins BONK, PEPE, STO, 1000CHEEMS, SHIB, WLFI, HEMI.

| Strategy | Clears the bars | Top-20 proxy | Mean R | Median R | Worst R | Rounds > 0 | Eligible coins | Round trips per round | Win rate | Fees per round | Calls/min peak / mean |
|---|---|---|---|---|---|---|---|---|---|---|---|
| e20v45 (live, same rounds) | 71% | 0.499 | +7.87% | +0.65% | -18.48% | 73% | — | — | — | — | — / — |
| P0: buy 1 step below, +1 / -3 steps, THROUGH | 4% | 0.000 | -82.09% | -87.69% | -99.62% | 0% | 3.5 | 3308 | 61% | +2.43% | 14 / 1.8 |
| P0T: P0 with TOUCH fills | 99% | 0.948 | +5204.04% | +983.33% | -85.16% | 95% | 3.5 | 9615 | 90% | +1971.36% | 14 / 3.0 |
| V1: buy at the last-price level | 4% | 0.000 | -91.68% | -97.07% | -100.00% | 0% | 3.5 | 4382 | 52% | +0.00% | 14 / 2.0 |
| V2: stop -2 steps | 4% | 0.000 | -89.20% | -94.76% | -99.92% | 0% | 3.5 | 4150 | 50% | +0.35% | 14 / 2.1 |
| V3: target +2 steps | 4% | 0.000 | -76.96% | -82.64% | -99.06% | 0% | 3.5 | 2452 | 48% | +4.19% | 14 / 1.5 |

- P0 against e20v45 on the same rounds (and P0T positive) -> **NO CANDIDATE**.
- Steps (Roostoo snapshot 2026-09-28): BONK 1e-08, PEPE 1e-08, STO 0.0001, 1000CHEEMS 1e-06, SHIB 1e-08, WLFI 0.0001, HEMI 1e-05.

Note (read with the verdict): the outcome is decided by the fill model, not the strategy. With a one-step spread, the
price trades at our buy level almost every minute, so TOUCH fills a buy and then a sell nearly every two minutes
(9,615 round trips per round, 90% won), compounding to returns that are not credible (median +983% per round). THROUGH
needs the price to fall one more level before the buy fills, so each trade starts a step behind (61% won, mostly
stopped out) and loses nearly everything. Roostoo's real rule (does a resting limit fill when the price only touches
it, and with what delay) is UNVERIFIED and is the whole question; minute bars cannot answer it. The next evidence has to
be a measured fill test on the test account, not another backtest.
