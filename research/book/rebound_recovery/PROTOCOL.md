# Main short sleeve rebound protection: frozen finite study

Book,2026-10-11 HKT. Remote-only research; exact parent book_e20combo_brk_cash at ef1b0dd.
Ten recovery hypotheses have failed. Keep them as failures; no retuning of their rules.
Near-high selection reduced downside but lost average return. A separate mechanism is needed.

## Economic distinction
The previous book_recovery_short applied24h confirmation only to the additional cash-funded shorts.
It explicitly left the main e20 DOWN-mode pol_trend_ls shorts unchanged.
That main sleeve holds both signs based on a longer-horizon per-coin trend. Baseline matched7-day paths had
13.48%average short exposure; individual shorts can remain negative-momentum assets through a fast rebound.
Daniel and Moskowitz2016, Momentum Crashes:
https://www.sciencedirect.com/science/article/pii/S0304405X16301490
Author summary: https://www.aqr.com/Insights/Research/Journal-Article/Momentum-Crashes
Motivation: past losers can rebound sharply after downturns. This does not establish the efficacy of our guards
or a crypto direction forecast. The source's dynamic strategy is NOT replicated.

## Exactly two new candidates, no outcome-based tuning
book_recovery_allshort24: compute the exact parent decision; remove ANY short whose own completed24h
endpoint return is strictly positive, including the main trend sleeve. Missing/invalid endpoint means retain that
short; no inferred exit. Other parent positions unchanged before risk matching.
book_recovery_rebound: remove ALL parent shorts only when BTC48h return is strictly positive AND more than
half of the parent's point-in-time liquid universe is up48h. Use parent's existing breadth logic:30most-liquid,
minimum20, complete168h nonnegative quote volume,12h bounded volume forward fill before that check.
Selected missing price endpoints invalidate breadth, never get dropped to manufacture a signal.
No new long entry, sign flip, leverage, grid, blend weight or coin/date exception.

For both, risk matching is mandatory before a changed proposal is returned.30-day complete hourly covariance,
minimum90%complete rows for ALL parent positions. Missing covariance means exact parent fallback.
If removing shorts increases full signed variance (by removing a hedge), scale the remaining signed book DOWN
by sqrt(parent variance / proposal variance). No exposure upscaling; zero-parent-risk scales proposal to cash.
No short or gross exposure can expand; shorts not removed may shrink under this whole-book risk constraint.
This is conditional on the supplied previous book; standalone parent trajectories can differ.

## Evaluation and stopping
Same2298 cash-start14-day windows, all original costs/lag/guard/liquidation and six horizons168/192/216/228/240/336.
Keep every historical gate, raise conditional family count10 to12, never lower thresholds.
Historical passes receive2x costs and+1h lag stresses, must pass both for a research promotion.
Add both to the unchanged25-case BTC-only diagnostic:133models, joint131-to133 recalculation, no case reselection.
The strict original broad query still FAILED:BCH29/30; adaptiveOFF.
All history spent; no project-wide post-selection claim. All failed candidates and operational errors preserved.
Both earlier future worktrees, cohorts, sources/configs/endpoints remain untouched.
These two new guards are outside those cohorts and have no pre-start forward evidence.
Actual EC2 account/deployment/endgame and full original competition hard gates remain UNVERIFIED.
Never recommend a live change from a larger point estimate or passing software tests.
