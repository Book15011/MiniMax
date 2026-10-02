# Pre-registration: dual momentum on top of baitoey_vt_mom (Baitoey, 2026-10-02)

Written and committed before any run. Not edited after results exist; results go to
`results/baitoey/20261002-vt-dual/` and a report committed under `research/baitoey/results/`.

## Question

`baitoey_vt_mom` clears the bars in only 20% of strong-fall windows: it always fills six slots, so it stays about
76% invested while prices drop. Does an absolute-momentum filter (a coin holds a slot only while its own trend is
positive) cut those losses without giving up the rally performance, under scoring v2 (tool `3036a0d8bfdaa6a0`)?

## Model

`src/models/baitoey/baitoey_vt_dual.py`, registered as `baitoey_vt_dual`. Exactly `baitoey_vt_mom` (7/14-day
risk-adjusted rotation, top 6 kept while in the top 12, the volume-confirmed early exit, 24 h rebalance, band 5
points), except:
- a coin may hold a slot only while its own momentum score (the same ROT_EW score vt_mom ranks by) is above
  `min_score`; a held coin whose score falls to or below it is sold;
- each slot is 1/k of the book, and a slot with no eligible coin stays in cash (vt_mom spreads the book over the
  coins it holds); the book is then scaled to at most 3%/day estimated volatility, as in vt_mom.
With every coin eligible and at least k of them, the targets equal vt_mom's exactly (tested). No code shared with
other models changes.

## Runs

| Run | min_score | Role |
|---|---|---|
| D0 | 0 | the variant; scored with `--score`, so it is on the leaderboard |
| Dm | -0.25 | neighbour (report-only, not registered) |
| Dp | +0.25 | neighbour (report-only, not registered) |

References (already scored, same tool version): `baitoey_vt_mom` and `pol_abl_shock` (vt_mom + crash rule).
Script: `research/baitoey/vt_dual.py` (one run at a time; the harness uses up to 8 workers).

## Verdict (fixed now), D0 against baitoey_vt_mom

- **Keeps the score:** D0 passes the hard gates and HEADLINE_RET >= 0.609 - 0.03 = 0.579.
- **Improves falls:** strong-fall hit rate at least 5 points above vt_mom's (>= 25%) AND worst 14-day R_liq above
  vt_mom's (-30.9%).
- **Candidate for the team** only if D0 keeps the score AND improves falls AND both neighbours keep the score.
  Otherwise **not a candidate**, and the report says which test failed.
- Report-only: HEADLINE_RET without the post-holdout windows, hits on the three bars, hit rates in strong / mild
  falls and rises, weighted median and mean 14-day R_liq, worst R_liq, the two real-round replays, guard share,
  fees, and D0's tie interval against the leaderboard's top.

## Known limits, stated before running

- The idea was chosen after seeing vt_mom's weakness by market type: it is a lead found after looking, not a
  pre-registered pick, even if it passes.
- The post-holdout windows (Jul-Sep 2026) are in the pool and were already seen.
- No paper-trading time before the Oct 4 launch: adopting it would be a team decision.
- Fixed 1/k slots also mean it holds less than vt_mom whenever fewer than k coins are eligible for other reasons.
