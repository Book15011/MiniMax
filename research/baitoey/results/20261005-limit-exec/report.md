# Limit orders with a 2-5 minute wait, then market; shorts at market

Pre-registration: `research/baitoey/prereg/20261005-limit-exec.md`. Costs are notional-weighted, in % of the notional,
relative to the mid at the trade hour; a lower cost is better. 27413 spot trades of e20v45's backtest, windows 2025-09-01 to 2026-09-15.

| Policy | Fill rate | Cost (all) | Saving vs market now | Buys / sells saving | decision / entry / guard saving | Quarters saving | Saving per 14-day round |
|---|---|---|---|---|---|---|---|
| Market now (base) | — | +0.113% | — | — | — | — | — |
| Limit at the bid/ask, wait 2 min | 84% | +0.080% | **+0.032%** | +0.035% / +0.029% | +0.032% / +0.036% / +0.025% | 5 of 5 | +0.124% |
| Limit at the mid, wait 2 min | 84% | +0.088% | **+0.025%** | +0.027% / +0.022% | +0.024% / +0.029% / +0.017% | 5 of 5 | +0.094% |
| Limit at the bid/ask, wait 5 min | 89% | +0.081% | **+0.032%** | +0.035% / +0.028% | +0.031% / +0.039% / +0.026% | 5 of 5 | +0.123% |
| Limit at the mid, wait 5 min | 89% | +0.089% | **+0.023%** | +0.026% / +0.019% | +0.023% / +0.031% / +0.017% | 5 of 5 | +0.090% |

- Passive limit: W=2 passes, W=5 passes -> **WORTH PROPOSING TO THE TEAM**.
- Median half-spread of the coins traded: +0.016%.
