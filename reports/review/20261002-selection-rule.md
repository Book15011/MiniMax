# The leaderboard's pick rule: legacy vs a tie margin and three other rules (2026-10-02, Pol)

Branch `feature/v2check` (Book's scoring v2 + feature/volume, local). Code: `backtest/scoring/selection.py`
(0f2336b), the market-type view `backtest/scoring/explain.py` (2d296dd). Study: `results/pol/20261002-v2check/
selection_study.py` (output `selection_study.out`, `selection_walkforward.csv`). Nothing here changes a score: the
pick rule and the views are report-layer code, not tool-version files, so the tool version stays `3036a0d8bfdaa6a0`.

## The problem

v2 picks the best CS_HIT inside the top model's tie group, and a model is tied when the 90% month-bootstrap interval
of its HEADLINE_RET difference to the top contains 0. That interval is wide for a model that moves differently from
the top and narrow for one that moves with it, so the group is set by correlation, not by closeness. Today the
shared leaderboard picks `pol_mr_cap` (HEADLINE_RET 0.509) over `baitoey_vt_mom` (0.609): that changed when the five
feature/volume models were registered (2026-10-02 14:45 HKT), without any change to the rule or the scores.

## Rules compared (candidates only; benchmarks and research rows never)

| Rule | Definition |
|---|---|
| legacy | pre-registered v2 rule, as above |
| margin d | legacy, but tied also needs the point difference within d of the top (d = 0.02, 0.03, 0.05) |
| max_score | the highest HEADLINE_RET |
| p_best | the model with the highest HEADLINE_RET in the most bootstrap draws |
| lcb | the highest 5th percentile of HEADLINE_RET across the draws |

## 1. Stability on today's data (4 bar settings x 2 pools = 8 cells)

| Rule | Distinct picks over the 8 cells | Pick (Book's bars, full pool) |
|---|---|---|
| legacy | **3** (pol_mr_cap, baitoey_mr_4h, baitoey_vt_mom) | pol_mr_cap (0.509) |
| margin 0.02 / 0.03 / 0.05, max_score, p_best, lcb | **1** | baitoey_vt_mom (0.609) |

Dropping any one non-picked candidate changes no rule's pick (0 of 22).

## 2. Walk-forward: pick from the past, score the next quarter

At each quarter start from 2022-07 to 2026-07 (17 quarters), every rule picks from the windows that ended before
it (weights 0.7 uniform + 0.3 recency, direction-balanced; min(SCREEN, CONFIRM) replaced by the worse half of the
training windows, so nothing from the future enters), and its pick is scored on the windows starting in the next
three months.

| Rule | Mean next-quarter hit rate | Median rank of the pick (of 24) | Quarters beating the average candidate |
|---|---|---|---|
| legacy | 0.417 | 16 | 35% |
| **margin 0.03** | **0.470** | **7.5** | **65%** |
| margin 0.02 | 0.470 | 7.5 | 65% |
| margin 0.05 | 0.444 | 11 | 53% |
| max_score | 0.450 | 12 | 59% |
| p_best | 0.450 | 7.5 | 59% |
| lcb | 0.450 | 12 | 59% |
| average candidate | 0.434 | | |
| best in hindsight | 0.633 | | |

Margin 0.03 minus legacy, per quarter: +0.053 on average, better in 8, worse in 2, the same in 7. Legacy's picks did
worse than the average candidate. Margin also beats max_score: using the risk score to choose between models whose
return scores are really close adds value; legacy's problem is only the width of its tie group.

Limits: 17 quarters; all candidates were designed with hindsight (the comparison between rules is fair, the levels
are optimistic); one bar setting (Book's) in the walk-forward.

## 3. What is implemented

- Top-level `selection:` in config.yaml: `rule: legacy | margin`, `tie_margin: 0.03`. **The active rule stays legacy
  (pre-registered) until the team decides**; changing it is one line and rescores nothing.
- The leaderboard always prints both picks ("Under the margin 0.03 rule the pick would be ...").
- New section "Why: results by market type": hit rate and average net exposure per type of 14-day window (strong /
  mild fall, mild / strong rise, turning point, calm, volatile) with a measured reason per model, e.g.
  baitoey_vt_mom: strong rises 90%, strong falls 20% (it stays 76% net long while prices drop);
  pol_switch_vt_tl_e20v45: strong rises 80%, strong falls 36% (it cuts to 21% net long).
- Copies with each rule ordering the table: `results/pol/20261002-v2check/leaderboard_{legacy,margin}.md`.

## Recommendation

Switch the active rule to margin 0.03 (Book's call: it changes his pre-registered step 3). Under it, every bar
setting and both pools pick `baitoey_vt_mom`.
