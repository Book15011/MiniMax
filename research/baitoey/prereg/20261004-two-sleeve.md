# Pre-registration: baitoey_two_sleeve, variants A-D, against the leaderboard (Baitoey, 2026-10-04)

Written and committed before any run. Not edited after results exist; results go to
`results/baitoey/20261004-two-sleeve/` and a report committed under `research/baitoey/results/`.

## The model

`src/models/baitoey/baitoey_two_sleeve.py`, written from Baitoey's spec of 2026-10-04 (no external code fetched or
copied); every number in `config.yaml` (`models: baitoey_two_sleeve:`); unit tests written first
(`tests/test_baitoey_two_sleeve.py`, 8 tests).
- Universe: the view's universe cut to coins with 800 h of history, ranked by 7-day quote volume.
- Trend sleeve (top 15 by liquidity): t-statistics over 7, 14, 30 days (log return / (hourly vol x sqrt(L))), clipped
  to +-2, averaged; positive scores held, weights proportional to score / vol, sleeve volatility target 25% a year.
- Momentum sleeve (top 25 by liquidity): 14-day return relative to their mean; long the top 5, inverse-vol weights.
- Each coin capped at +-25%, gross at most 95%, 2% band, daily at 16:00 UTC.

| Variant | Definition | Class |
|---|---|---|
| A | trend sleeve only | `baitoey_two_sleeve`, momentum long_gross 0 |
| B | A + momentum long top 5 and short bottom 5, 30% / 30% (research only, never live: the momentum sleeve is market-neutral) | `_two_sleeve_variants.TwoSleeveLS` |
| C | A + momentum long-only top 5 at 30% (the config defaults) | `baitoey_two_sleeve` |
| D | C in three tranches rebalanced at 00:00, 08:00 and 16:00 UTC | `_two_sleeve_variants.TwoSleeveStaggered` |

## Comparison

Each variant scored with `score_model` like `--score`, not registered (the team leaderboard and its pick are
untouched), next to the registered runs of pol_switch_vt_tl_e20v45 (live), baitoey_vt_mom, pol_abl_shock and
book_orch (H1): HEADLINE_RET, CS_HIT, Pol's ~150-team cut (top-20 proxy), hit rates by market type, worst R, the two
real-round replays; and HEADLINE_RET, CS_HIT and the top-20 proxy with the live lock-in (method of Pol's endgame2.py).
Script: `research/baitoey/two_sleeve.py`.

## Verdict (fixed now)

- A variant (A, C or D; never B) is a **CANDIDATE for team discussion** only if it passes the hard gates and, with the
  lock-in, beats e20v45 + lock-in by at least 0.03 on HEADLINE_RET and is not lower on the top-20 proxy.
- Otherwise **no candidate**. A candidate would still need its own pre-registered robustness check (one setting at a
  time) before any proposal, and the team rule for upgrades.
- Report-only: B; D against C (whether tranches help); everything in the comparison list.

## Known limits, stated before running

- The numbers are the spec's, not tuned; one run per variant.
- The post-holdout windows (Jul-Sep 2026) are in the pool and were already seen.
- The round is live (started 2026-10-04 12:00 UTC); nothing here changes the live bot. The 2026-10-10 freeze applies.
