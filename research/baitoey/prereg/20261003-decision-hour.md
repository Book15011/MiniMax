# Pre-registration: which hour of the day should e20v45 decide at? (Baitoey, 2026-10-03)

Written and committed before any run. Not edited after results exist; results go to
`results/baitoey/20261003-decision-hour/` and a report committed under `research/baitoey/results/`.

## Question

The daily models decide at 16:00 UTC (00:00 HKT), chosen to match the competition's HKT day, not by testing. Does
the hour matter, and is another hour clearly better?

## Runs

`src/models/baitoey/_decision_hour.py` wraps `pol_switch_vt_tl_e20v45` (unchanged) and runs its daily decision at
`decision_hour` UTC; every other hour holds the book. The guard, day boundaries and the round start (12:00 UTC) stay
as they are. All six runs use the same hourly wrapper, so H16 is the control (the hourly wrapper alone scored 0.022
below the daily model in the stop-loss check; comparing within the wrapper removes that).

| Run | Decision hour (UTC) | HKT |
|---|---|---|
| H00 | 00:00 | 08:00 |
| H04 | 04:00 | 12:00 |
| H08 | 08:00 | 16:00 |
| H12 | 12:00 | 20:00 |
| H16 | 16:00 (today's hour, control) | 00:00 |
| H20 | 20:00 | 04:00 |

Scored with `score_model` like `--score`, not registered (the leaderboard is untouched). Script:
`research/baitoey/decision_hour.py`.

## Verdict (fixed now)

- **Move** to hour H only if H passes the hard gates, scores HEADLINE_RET >= H16 + 0.03 (the team margin), and both
  neighbouring hours (H - 4 and H + 4) also score at least H16 (a plateau, not one lucky hour). If several qualify,
  report them all and do not pick among them here.
- Otherwise **keep 16:00 UTC**.
- Report-only: the spread of HEADLINE_RET across the six hours (how much the result depends on the clock), CS_HIT,
  hit rates by market type, median / mean and worst R_liq, the two real-round replays, fees.

## Known limits, stated before running

- Six hours are six comparisons; one hour can beat 16:00 by chance, hence the plateau condition.
- The post-holdout windows (Jul-Sep 2026) are in the pool and were already seen.
- A decision at a different hour also trades at a different hour than the guard (04:00 UTC); the guard is unchanged.
- The round starts 2026-10-04 12:00 UTC; nothing here changes the launch. A positive result would go through the
  team rule for upgrades (pre-written rule plus three days of paper).
