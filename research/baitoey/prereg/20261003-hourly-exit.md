# Pre-registration: check the volume exit every hour, and a 5% cut-and-rebuy, on a 5% band (Baitoey, 2026-10-03)

Written and committed before any run. Not edited after results exist; results go to
`results/baitoey/20261003-hourly-exit/` and a report committed under `research/baitoey/results/`.

## Questions

1. The volume-confirmed exit (a new 24-hour low on 1.5 times normal volume) is the one per-coin rule that helped
   (+0.040 for vt_mom), but it is only checked at the 16:00 UTC decision. Does checking it every hour help?
2. Cut a coin once it is 5% down since the 16:00 UTC decision and let the next decision buy again (the stop-loss
   check `20261003-stop-loss`, S5). That check ran the hourly wrapper on e20v45's 3% band, and its control scored
   0.022 below the daily model; Pol's crash brake on e20v45 used a 5% band and matched the daily model. Rerun S5 on
   a 5% band, with a control on the same band.

## Runs

Wrappers: `src/models/baitoey/_hourly_exit.py` (5% band; `hourly_exit: false` is the control) and the stop-loss
wrapper `src/models/baitoey/_stop_loss.py` with its band set to 5% in the script. The daily models are unchanged.

| Run | Model | Hourly rule | Role |
|---|---|---|---|
| E0 / V0 | `pol_switch_vt_tl_e20v45` / `baitoey_vt_mom` | none, daily | base (registered runs) |
| EC / VC | same, hourly wrapper, 5% band | none | control |
| EX / VX | same, hourly wrapper, 5% band | volume exit every hour (vt_mom exit settings) | candidate 1 |
| ES5 | e20v45, stop-loss wrapper, 5% band | cut at -5% since 16:00 UTC, rebuy at the next decision | candidate 2 |

Scored with `score_model` like `--score`, not registered (the leaderboard is untouched). Script:
`research/baitoey/hourly_exit.py`.

## Verdict (fixed now)

- A candidate X (base B, control C) is **better** if it passes the hard gates, HEADLINE_RET >= B - 0.01 and >= C -
  0.01, and either the worst 14-day R_liq improves on B by at least 2 points, CS_HIT rises by at least 0.02 over B,
  or HEADLINE_RET >= B + 0.03.
- **Worse** if it fails a hard gate or HEADLINE_RET < B - 0.03. Otherwise **no clear difference**.
- Hourly volume exit: **propose** only if EX is better and VX is not worse.
- 5% cut-and-rebuy: **propose** only if ES5 is better.
- Report-only: whether EC is within 0.01 of E0 (the band explains the earlier control gap), hit rates by market type,
  median / mean and worst R_liq, the real-round replays, fees, and against the control the share of rounds the rule
  changed, helped and hurt.

## Known limits, stated before running

- The hourly exit applies to every long held between decisions; in e20v45's down mode the trend sleeve's longs are
  checked too. Shorts are untouched.
- The post-holdout windows (Jul-Sep 2026) are in the pool and were already seen.
- S5 was already rejected on the 3% band; this rerun can change that only through the band.
- The round starts 2026-10-04 12:00 UTC; nothing here changes the launch. A positive result would go through the
  team rule for upgrades (pre-written rule plus three days of paper), and an hourly rule needs the live guard fix for
  hourly models (149d564).
