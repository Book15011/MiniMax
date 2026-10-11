# Book: predeclared continuous-trend recovery experiment

Freeze written 2026-10-11 13:15 UTC, before any new candidate outcomes are read.
Remote only, isolated Book branch; research only. No live change, signed API, main merge, or secrets.
Parent commit 7b239c66fb60e2945a4b8f834b0df579ea4a1737; numeric baseline live-source ef1b0dd.
Twelve previous recovery hypotheses remain failed. This pair increases the task family to FOURTEEN.
Historical data are spent calibration, never fresh validation; conditional bounds are not project-wide guarantees.

## Question and fixed hypotheses
Do steady daily paths within strong momentum coins avoid jump-and-reversal losses better than the parent?
Only refine the UP regime's positive long budget; DOWN mode, all parent shorts, cash-short rules and budgets stay parent.
At decision t use complete positive hourly closes through t over 7/14 days.
For each lookback d, form d nonoverlapping 24-hour endpoint returns ending at t.
Keep only coins with strictly positive total return at BOTH 7 and 14 days and finite parent volatility-adjusted momentum.
Quality Q = average across 7/14 days of (positive daily count minus negative daily count)/d.
Zero-return days stay in the denominator. Daily blocks end at decision time, not partial calendar days.
First restrict to the top12 parent-momentum coins (stable alphabetical ties). This conditions quality on momentum.
A: book_recovery_quality ranks these coins by Q.
B: book_recovery_quality_blend ranks them by 0.5*percentile(parent momentum)+0.5*percentile(Q) within this same pool.
No parameter search. The 7/14, pool12, select6/retain12, daily16UTC decisions and3% band come from parent conventions.
Keep parent volume/breakdown filters and never select a parent short as a long.
No eligible features or incomplete covariance => exact parent fallback.
Use the inherited high-recovery allocation checks: equal positive budget, scale down if30d long covariance risk increases;
exact parent fallback if full signed portfolio variance would increase. Never increase gross or any parent short target.
This can lose hedging value and fall back often. Estimated covariance is not a loss guarantee.
Absolute-positive conditioning is part of these two joint hypotheses; the earlier absolute-only failure stays recorded.

## Evidence and rejection rules
Same2298 cash-start14d windows, panels ending before competition, same fees/spread/1h lag and proportional terminal charge.
Horizons168/192/216/228/240/336 hours. Original mean/median/p10/drawdown/recent/weak-window gates unchanged.
Purged quarter bootstrap20000 draws seed20261011, lower tail0.05/14 for new paired hypotheses.
No historical pass => no cost/delay extension for these candidates. Historical pass => original double-cost and+1h-lag tests.
Independently reconstruct every stored return, drawdown, CS; verify source/data/cache hashes, risk targets and parent config.
Require all tests and publication audit before adding both trials to the135-model BTC-only diagnostic leaderboard.
Retain the SAME25 BTC-only cases, jointly widen its bound for135*2 comparisons; do not reselect lookalikes.
BCH missing, original broad-universe29/30 remains FAILED; adaptive remains OFF.
Scores/ranks are diagnostic and cannot override original historical vetoes.
Original full competition gates, actual EC2 holdings/endgame/deadline remain UNVERIFIED.
Inherited marked gross drift and omitted separate terminal spread are retained simulator limitations, not live compliance proof.

## Fresh evidence
Previous three future worktrees/cohorts are immutable. These two trials have no fresh evidence now.
If a new future replay is prepared, freeze separately before its start and never add models to the old frozen cohort.
No partial scores, no automatic schedule, and one3-day path cannot prove a future profit advantage.

## Primary basis and limits
Da/Gurun/Warachka2014 author PDF https://academicweb.nd.edu/~zda/Frog.pdf read in full-tool text.
Their information-discreteness formula conditions on formation momentum; this study uses its sign-count intuition.
Their stock horizons are12-month formation/6-month holding, not7/14-day crypto. Our application is an unverified inference.
Count signs do not measure jump magnitude perfectly; all-positive paths may still contain one dominant jump.
Grobys/Shahzad publisher abstract https://onlinelibrary.wiley.com/doi/10.1002/ijfe.70036 read abstract only.
It warns of heavy tails in crypto momentum variance; it does not prove our mean undefined or validate this rule.
Keep realized returns, calendar concentration, downside and CS; do not select on a variance statistic alone.
