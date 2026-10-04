# Addendum to 20261004-fast-switch: v2 checks the flip on the decision grid (Baitoey, 2026-10-04)

Written after the v1 results and before any v2 run.

**Why.** v1 (`grid: hourly`) checked BTC's state every hour. btc_state samples every 6 hours from the hour it is
called, so at each hour it read a different set of points and the state flickered: 932 triggers in 2020-2026 against
112 real flips on the 16:00 UTC grid (5.3 per 14-day round instead of about 0.6). v1 therefore tested acting on
flicker, not on flips; its verdict (keep 16:00) stands and is recorded as is.

**v2** (`grid: decision`): checks only at 22:00, 04:00 and 10:00 UTC, the 6-hour points of the 16:00 decision, where
the state is read on the same points as the daily decision; it decides at once when the state differs from the last
16:00 and from 6 hours earlier (a real new flip), and otherwise holds.

| Run | Acts at once on | Switch EMA days | Compared with |
|---|---|---|---|
| G20 | real flips up and down | 20 | E0 and C20 (v1 control, 0.567) |
| GD20 | real flips to down only | 20 | report-only |
| G15 / G25 | real flips up and down | 15 / 25 | E1 / E2 (0.565 / 0.577) |

**Verdict:** the same rule as in 20261004-fast-switch, with G20 in place of F20 and G15 / G25 in place of F15 / F25.
Script: `research/baitoey/fast_switch_v2.py`.
