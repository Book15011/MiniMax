# Pre-registration: inverse-volatility weights instead of equal weights? (Baitoey, 2026-10-03)

Written and committed before any run. Not edited after results exist; results go to
`results/baitoey/20261003-inverse-vol/` and a report committed under `research/baitoey/results/`.

## Question

`baitoey_vt_mom` (and the momentum sleeve of `pol_switch_vt_tl_e20v45`) holds its six coins in equal weights, so a
wild coin (PUMP fell 9% in one night on the test account) gets as much money as a calm one. The rotation code already
supports `weighting: inverse_vol` (weights proportional to 1 / the coin's recent hourly volatility, as in the team
baseline `team_rot_iv`). The only earlier evidence is confounded: `team_rot_iv` also has a lower volatility target
(2% vs 3%) and scored far below `team_rot_ew` under scoring v1. Does inverse-volatility weighting alone help?

## Runs

One setting changed: `weighting: inverse_vol`. Everything else (coins picked, volatility cap, exits) unchanged.

| Run | Model | Change |
|---|---|---|
| V0 / E0 | `baitoey_vt_mom` / `pol_switch_vt_tl_e20v45` | none (registered runs, read from the registry) |
| VIV | `baitoey_vt_mom` | `weighting: inverse_vol` |
| EIV | `pol_switch_vt_tl_e20v45` | `weighting: inverse_vol` in the momentum sleeve (its 4.5% cap kept) |

Scored with `score_model` like `--score`, not registered (the leaderboard is untouched). Script:
`research/baitoey/inverse_vol.py`.

## Verdict (fixed now)

- A run is **better** if it passes the hard gates, HEADLINE_RET >= base - 0.01, and either the worst 14-day R_liq
  improves by at least 2 points or CS_HIT rises by at least 0.02.
- A run is **worse** if it fails a hard gate or HEADLINE_RET < base - 0.03 (the team margin).
- Otherwise **no clear difference**.
- **Propose to the team** (for e20v45, the launch model) only if EIV is better and VIV is not worse.
- Report-only: HEADLINE_RET without the post-holdout windows, CS_HIT, hit rates by market type and in volatile
  windows, weighted median and mean R_liq, worst R_liq, the two real-round replays, fees, mean money invested.

## Known limits, stated before running

- With the same volatility cap, calmer weights lower the estimated book volatility, so the book may hold more money
  in total; the report shows the mean invested so this is visible.
- The post-holdout windows (Jul-Sep 2026) are in the pool and were already seen.
- The round starts 2026-10-04 12:00 UTC; nothing here changes the launch. A positive result would go through the
  team rule for upgrades (pre-written rule plus three days of paper).
