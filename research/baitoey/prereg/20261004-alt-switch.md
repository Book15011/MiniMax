# Pre-registration: read e20v45's up/down switch from altcoins or from the momentum basket instead of BTC (Baitoey, 2026-10-04)

Written and committed before any run. Not edited after results exist; results go to
`results/baitoey/20261004-alt-switch/` and a report committed under `research/baitoey/results/`.

## Question

e20v45 holds momentum altcoins in up mode and the long/short trend sleeve in down mode, and decides the mode from BTC
alone. Our 14-day results move with altcoins more than with BTC (correlation 0.71 vs 0.54 for e20v45, 2,298 rounds).
Would the switch work better on (a) an equal-weight altcoin index, or (b) the momentum basket (the coins the model
would hold)?

## Rule tested

`src/models/baitoey/_alt_switch.py`: team_trend_2's state rule exactly as e20v45 applies it to BTC (EMA of hourly
closes, +-3% band, replayed every 6 hours over `state_days`, out of trend when undecided), applied to:
- **alts**: the equal-weight index of the universe's coins other than BTC and ETH;
- **momentum**: the basket of the universe's top 6 by the 7/14-day momentum score, picked daily at 16:00 UTC from data
  up to that hour, held equally for the next 24 hours (a raw basket: no volatility cap, no exits);
- **both** (report-only): up only when BTC and the altcoin index are both up.
Everything else is e20v45 unchanged. Both indices use the universe at the decision time for their whole history.

| Run | Switch read from | EMA days |
|---|---|---|
| E0 | BTC (the registered e20v45) | 20 |
| A15 / A20 / A25 | altcoin index | 15 / 20 / 25 |
| M15 / M20 / M25 | momentum basket | 15 / 20 / 25 |
| AB | BTC and altcoin index both up | 20 |

Scored with `score_model` like `--score`, not registered (the leaderboard is untouched). Script:
`research/baitoey/alt_switch.py`.

## Verdict (fixed now), per family (alts; momentum)

- The 20-day run is **better** than E0 if it passes the hard gates and either HEADLINE_RET >= E0 + 0.03, or
  HEADLINE_RET >= E0 - 0.01 with the worst 14-day R_liq at least 2 points better or CS_HIT at least 0.02 higher.
- Its neighbours (15 and 25 days) **hold** if they pass the hard gates and HEADLINE_RET >= E0 - 0.03.
- **Propose the family** only if the 20-day run is better and both neighbours hold. If both families pass, report
  both for the team to choose; nothing is picked here. Otherwise **keep the BTC switch**.
- Report-only: AB, CS_HIT, hit rates by market type and in volatile windows, median / mean and worst R_liq, the two
  real-round replays, fees.

## Known limits, stated before running

- The idea came from looking at correlations on the same data.
- The momentum basket is a simplified version of what the model holds (no cap, no exits, today's universe).
- The post-holdout windows (Jul-Sep 2026) are in the pool and were already seen.
- The round starts 2026-10-04 12:00 UTC; nothing here changes the launch. A positive result would need the team rule
  for upgrades (pre-written rule plus three days of paper) before the 2026-10-10 freeze and a change to Pol's model.
