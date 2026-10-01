# Pre-registration: calm/trend switch (Baitoey, 2026-10-01)

Written and committed before any run. Not edited after results exist; results go to
`results/baitoey/20261001-switch-study/`.

## Question

MR @4h (Bollinger + RSI mean reversion) scores well in calm stretches but misses rallies; the ROT_EW rotation
catches rallies but gives back in chop. Does switching between them by market calm beat each one alone?

## Model

`src/models/baitoey/baitoey_switch_mr.py`, method `selector`. At every 4 h decision: calm = BTC’s 30-day realized
volatility (hourly returns) below the `calm_quantile` of its values at the decision hour over the past 365 days
(too little history or a missing value: not calm). Calm → the book follows `baitoey_mr_bbrsi` with 4 h bars (the
MR @4h settings); otherwise → `team_rot_ew`’s rotation (both through YAML anchors in `config.yaml`, so the sleeves
cannot drift). Long only, band 5 points, harness costs, guard and keep-alive (tool version `ce40153`). As a
`selector`, it may go live only after passing the selection ladder (STRATEGY_GUIDE §6).

## Runs

| Run | calm_quantile | Role |
|---|---|---|
| S50 | 0.5 | the switch |
| S40, S60 | 0.4, 0.6 | plateau neighbours |

References (already scored, same tool version): MR_4h and CORE_4h from the mean-reversion study (the two sleeves
alone at 4 h), team_rot_ew, and pol_switch_rt (the current leader).

## Verdict on SCREEN (the only judgement)

SCREEN = windows starting 2022-07-01 … 2024-06-30. S50, MR_4h and CORE_4h are ranked on four SCREEN scores
(higher is better): return-gate pass share, median 14-day R, 75th percentile R, worst-10% R. **The switch adds
value** if S50’s mean rank is better (lower) than both sleeves’. **Robust** if S40 and S60, each ranked the same
way against the two sleeves, also beat both. Phase 1 (`python -m research.baitoey.switch_study screen`) prints
only SCREEN numbers and the verdict, and records them in `verdict.json`.

## The one CONFIRM look

Phase 2 (`... switch_study confirm`) runs once, after `verdict.json`. For S50, S40, S60, the sleeves, team_rot_ew
and pol_switch_rt: return-gate pass share, median, 75th and 90th percentile and worst-10% R on SCREEN and CONFIRM,
REL (HEADLINE REL FLOORED) and its live-like, recency and flat layers, gates G1–G6, turnover per day, fees and
spread per window, max orders per decision, and `compare` (90% block bootstrap, blocks of 56) of S50 against
team_rot_ew, MR_4h and pol_switch_rt. Also the share of decision days that were calm, per period. Nothing changes
afterwards; the holdout stays sealed.

## Stated before running

- The calm sleeve inherits MR @4h’s dependence on one calm stretch (July 2026).
- Fourth study today: treat a lone good cell with suspicion; only S50 counts.
