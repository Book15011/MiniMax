# BTC-adjusted coin selection: frozen finite study

Book, 2026-10-11 HKT. Research only in feature/book-residual-recovery.
Baseline is book_e20combo_brk_cash at ef1b0dd; actual EC2 holdings/deployment UNVERIFIED.
Six earlier recovery controls remain failures. No thresholds or parameters are retuned.

## Economic question and sources

Common crypto market exposure can make a coin look strong because it responds more strongly to BTC.
Test whether separating that response from coin-specific strength improves the long selection.
Liu, Tsyvinski & Wu, Common Risk Factors in Cryptocurrency: https://www.nber.org/papers/w25882.
This primary source documents market and momentum factors; it does NOT validate our BTC proxy, estimator,
lookbacks or a remaining-week prediction. One BTC factor is an incomplete description of crypto risk.
The regression is a rolling feature estimate, not a fit to strategy returns or the observed trading log.
No hedge or pair trade is created; positions remain directional and gross <=100%.

## Exactly two candidates

book_recovery_resid: in parent up mode only, select longs using BTC-adjusted momentum.
For each coin estimate beta=cov(coin hourly log return,BTC hourly log return)/var(BTC)
from 30 days ending 14 days before the decision. Thus none of the 7/14-day score period trains beta.
Score = mean of 7/14-day sums of (coin log return-beta*BTC log return), divided by
the corresponding residual standard deviation times sqrt(hours). A truly zero residual gets score zero.
Require >=90% of the training hours and every scoring hour. Missing or degenerate BTC means exact parent fallback.
book_recovery_resid_blend: equal average of cross-sectional percentile ranks of this score and the parent's
ordinary 7/14-day risk-adjusted score. No optimized blend weight.

Both retain top6/keep12, equal weights and existing daily16UTC clock/band3%.
Use the parent's existing volume breakdown and daily20-day breakdown filters without changing them.
A candidate may allocate only the positive gross of its parent decision given the same previous book.
Parent shorts remain exact, never overlap selected longs. No extra shorts or leverage.
Match estimated long-book risk downward to the parent using complete 30-day covariance.
If full signed-book risk then exceeds the parent, or covariance lacks90% complete rows, use the exact parent.
Down mode, zero long budget, unavailable features or fewer than one eligible coin: exact parent.

## Evaluation and stopping

All existing history is spent research evidence. No fresh holdout or private-rule recovery claim.
Use same2298 standard14-day cash-start windows and costs/lag/guard/liquidation as the earlier study.
Report mean/median/p10/worst return, drawdown, CS and paired differences, recent2024on,
fixed old weak profiles216/228/240h and current horizon interpretations168/192h.
Keep ALL historical improvement gates from recovery_study/PROTOCOL.md.
Raise conditional family multiplicity from6 to8; never decrease it.
Any historical pass must survive2x fees/spreads and+1h lag before even a research promotion.
Project-wide historical selection is not fully controlled. Current BTC-only matching remains exploratory.
Do not modify the prior seven-model forward cohort, its worktree, dates, sources or freeze.
These two new hypotheses have no pre-start forward evidence.
Actual same-holdings switch and runner endgame must be validated before a live recommendation.
Preserve every failure. No post-result adjustment, new blend weight or coin/date exception.
