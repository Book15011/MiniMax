# Take-profit overlay on baitoey_vt_mom: CONFIRM

Pre-registration: `research/baitoey/prereg/20261006-tp-overlay.md`. 755 windows starting 2024-07-01 to 2026-07-25; 52 coins traded, 5 without hourly highs (close used): ASTERUSDT, AVNTUSDT, PUMPUSDT, WLFIUSDT, XPLUSDT.
Check: A's REL 2.5616 against the registered period_check 2.5616; A's fortnight returns differ from the engine's by at most 0.00e+00. Hourly highs: Binance 1-hour klines (every window ends by 2026-08-08, so the 1-minute data is not needed). Between a fill and the next decision the overlay skips that coin's guard trades (addendum, written before the run).

| Variant | tp_pct / fraction | Median fortnight R | 75th pct | 90th pct | TP fill rate (per coin-decision) | Fills per round | Bought back higher / lower | Fees per round | REL | REL vs A |
|---|---|---|---|---|---|---|---|---|---|---|
| A | none | +0.10% | +6.87% | +17.22% | — | — | — | +0.49% | 2.562 | +0.000 |
| B | 8% / 1 | -0.97% | +5.17% | +11.67% | 12.3% | 11.04 | 3609 / 3581 (649 dropped) | +0.68% | 1.178 | -1.384 |
| C | 12% / 1 | -0.34% | +6.16% | +14.09% | 6.1% | 5.50 | 1934 / 1665 (316 dropped) | +0.58% | 1.117 | -1.444 |
| D | 8% / 0.5 | -0.53% | +6.03% | +14.32% | 12.3% | 11.04 | 3609 / 3581 (649 dropped) | +0.58% | 1.294 | -1.267 |

- Better than A in CONFIRM (REL at least +0.05, median not lower): none.
