# Pre-registration: mean reversion with Bollinger Bands + RSI (Baitoey, 2026-10-01)

Written and committed before any run. Not edited after results exist; results go to
`results/baitoey/20261001-mr-study/`.

## Question

Book’s forecast for Oct 4–17 is a calm, low-dispersion fortnight, the one market where mean reversion may earn.
(1) Does a standalone Bollinger + RSI mean-reversion bot score well? (2) Does using RSI as an entry timer (buy the
momentum leaders on a dip, not after a run-up) improve the ROT_EW rotation? Prior evidence says no for liquid
coins (they show short-term momentum, not reversal), and fees punish frequent trading; this test checks it once.

## Variants

| Run | Model | Rule | Rebalance and indicator bars |
|---|---|---|---|
| MR @4h, MR @24h | `baitoey_mr_bbrsi` | Buy when close < lower band (20-bar mean − 2 sd) AND 14-bar RSI < 30; sell at close ≥ 20-bar mean, or when no buy signal for 72 h (time stop); 1/6 slots, most oversold first; book ≤ 3%/day volatility | 4 h / 24 h |
| DIP @4h, DIP @24h | `baitoey_rot_dip` | ROT_EW rotation (3/7/14-day score, top 6, keep while top 12, equal weights, ≤ 3%/day); a coin not held may be bought only if its 14-bar RSI < 50; the slot goes to the next-ranked coin that qualifies | 4 h / 24 h |
| CORE @4h (control) | `baitoey_rot_dip`, filter off | ROT_EW rotation at 4 h, to separate the filter from the interval | 4 h |
| team_rot_ew (reference) | — | the same core at 24 h | 24 h |

Definitions: bars are the hourly close every 4 or 24 hours ending at the decision; Bollinger sd is the population
sd; RSI uses simple averages of the last 14 bar changes. Missing data makes a condition false (no buy; a held MR
coin without a recent signal is sold by the time stop). In DIP, removing unheld coins before ranking can lift the
rank of held coins (slightly stickier holding). Long only; band 5 points; harness costs, guard and keep-alive
(tool version `ce40153`). `baitoey_mr_bbrsi` is filed under method `trend` (it judges each coin against its own
past, as STRATEGY_GUIDE §3 defines `trend`); a separate mean-reversion method would need team agreement.

## The only choice made on SCREEN

SCREEN = windows starting 2022-07-01 … 2024-06-30 (16:00 UTC). For MR and for DIP separately, 4 h and 24 h are ranked
on four SCREEN scores (higher is better): share of windows passing the return gate, median 14-day return R, 75th
percentile R, worst-10% R. The lower mean rank wins; a tie goes to the lower turnover. No parameter is varied.
Phase 1 (`python -m research.baitoey.mr_study screen`) prints only SCREEN numbers and writes `choice.json`.

## The one CONFIRM look

Phase 2 (`... mr_study confirm`) runs once, after `choice.json`. For every run and team_rot_ew: return-gate pass
share, median, 75th and 90th percentile and worst-10% R on SCREEN and CONFIRM, REL (HEADLINE REL FLOORED), gates
G1–G6, turnover per day, fees and spread per window, max orders per decision, and `compare` against team_rot_ew
(paired REL CS difference, 90% block bootstrap, blocks of 56). REL leans on 2025–26 windows, so it belongs to
this look and is not used for any choice. Nothing changes afterwards; the holdout stays sealed.

## Stated before running

- This is the third study today (after volume timing and return-max rotation): with this many runs, one cell
  looking significant by luck is likely. Only the SCREEN-chosen runs count.
- Expected: MR rarely passes the return gate (small, capped wins) and may fail G2/G6 (buying into crashes).
