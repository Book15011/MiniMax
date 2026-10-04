# Pre-registration: act at once when the BTC up/down state flips, instead of at the next 16:00 UTC (Baitoey, 2026-10-04)

Written and committed before any run. Not edited after results exist; results go to
`results/baitoey/20261004-fast-switch/` and a report committed under `research/baitoey/results/`.

## Question

e20v45 reads BTC's up/down state only at its daily decision (16:00 UTC), so a flip waits up to about 21 hours. Flips
are rare (103 in 2,279 days, Pol's trend_mode_history), unlike the daily noise that made hourly decisions, hourly
exits and stop-losses lose. Does deciding at once on a new flip help?

## Rule tested

`src/models/baitoey/_fast_switch.py`: checked every hour; at 16:00 UTC the model decides as usual; at any other hour,
if BTC's state differs from the state at the last 16:00 UTC bar and did not an hour earlier, the model decides at
once; otherwise the book is held. Band 5% (as the control in `20261003-hourly-exit`, which matched the daily model).

| Run | Acts at once on | Switch EMA days | Compared with |
|---|---|---|---|
| C20 | never (control: same hourly wrapper) | 20 | — |
| F20 | flips up and down | 20 | E0 (registered e20v45) and C20 |
| FD20 | flips to down only | 20 | report-only |
| F15 / F25 | flips up and down | 15 / 25 | E1 / E2 of `20261003-e20v45-plateau` (0.565 / 0.577) |

Scored with `score_model` like `--score`, not registered (the leaderboard is untouched). Script:
`research/baitoey/fast_switch.py`.

## Verdict (fixed now)

- F20 is **better** if it passes the hard gates, HEADLINE_RET >= C20 - 0.01, and either HEADLINE_RET >= E0 + 0.03 or
  HEADLINE_RET >= E0 - 0.01 with the worst 14-day R_liq at least 2 points better or CS_HIT at least 0.02 higher.
- F15 and F25 **hold** if each passes the hard gates and scores at least its same-EMA reference - 0.03.
- **Propose** only if F20 is better and both hold. Otherwise **keep deciding at 16:00 UTC**.
- Report-only: FD20, hit rates by market type, median / mean and worst R_liq, the two real rounds, fees.

## Known limits, stated before running

- With about one flip every three weeks, the effect is expected to be small; the 90% intervals of earlier checks were
  about +-0.03, so a real gain may not be detectable.
- The post-holdout windows (Jul-Sep 2026) are in the pool and were already seen.
- The round starts 2026-10-04 12:00 UTC; nothing here changes the launch. A positive result would need an hourly
  live model (with the guard fix 149d564) and the team rule for upgrades before the 2026-10-10 freeze.
