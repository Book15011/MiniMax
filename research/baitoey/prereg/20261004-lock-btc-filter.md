# Pre-registration: skip the lock-in while BTC is in a strong rally? (Baitoey, 2026-10-04)

Written and committed before any run. Not edited after results exist; results go to
`results/baitoey/20261004-lock-btc-filter/` and a report committed under `research/baitoey/results/`.

## Question

The live lock-in (`live.endgame`: from day 10, once equity is +3% above the round start, sell everything and hold
cash) was chosen on Pol's grid (`results/pol/20261002-v2check/endgame2.py`, +0.040 HEADLINE_RET for e20v45). An
exploratory replay (`research/baitoey/results/20261004-lock-scenarios`, after looking) suggested that the lock lowers
the chance of clearing a top-20 proxy when BTC is already up 10% or more when it fires (18% vs 29%), because the
cut keeps rising in strong rallies. Does a BTC filter on the lock help, on the team's own measures?

## Rule tested

Lock as live, except at hours when BTC's return since the round's first hour is at least X: then no lock at that
hour (the check repeats every hour; if BTC falls back below X while equity is still +3% up, the lock fires then).
The exit is Pol's: at the next hour's close, 0.1% fee + 0.03% half-spread on the gross held, cash to the end.

| Run | Rule |
|---|---|
| N | no lock-in (the registered model) |
| L0 | lock +3% from day 10 (the live rule) |
| B8 / B10 / B12 | L0, but not while BTC is up at least 8% / 10% / 12% since the round start |

Model: `pol_switch_vt_tl_e20v45` (the launch model). `baitoey_vt_mom` is scored the same way, report-only.
Method: Pol's endgame2.py, unchanged in substance: the cached v2 equity paths of the 2,298 windows (the unmodified
paths must reproduce the score file), v2 weights and bars, the V1 FLOORED composite on HKT days for CS_HIT, and his
"~150-team cut" (best of the six benchmarks in up windows, +0.6% in down windows) as the top-20 proxy. Script:
`research/baitoey/lock_btc_filter.py`.

## Verdict (fixed now), for e20v45 against L0

- **Propose the filter** only if all three of B8, B10 and B12 (no picking a threshold) have: the share of weighted
  rounds clearing the ~150-team cut at least 0.005 above L0, HEADLINE_RET at least L0 - 0.01, and CS_HIT at least
  L0 - 0.02.
- Otherwise **keep the lock-in as it is**.
- Report-only: the 90% month-bootstrap interval of each difference (Pol's tie_test for HEADLINE_RET, the same
  resampling for the cut share), the best-of-six cut, mean and worst R_liq, how often each rule exits, and the same
  numbers on the rounds where BTC is up at least 10% at day 10.

## Known limits, stated before running

- The 10% line came from an exploratory look at the same data; the three thresholds and the fixed verdict are there
  to limit that, not remove it.
- The cut is a proxy built from six benchmarks, not the real field; last season's falling round had a real top-20
  cut near -1.5%.
- The post-holdout windows (Jul-Sep 2026) are in the pool and were already seen.
- The lock cannot fire before 2026-10-14; a positive result would still need the team rule for upgrades (pre-written
  rule plus three days of paper) before the 2026-10-10 freeze, and a change to the live runner, which is Pol's code.
