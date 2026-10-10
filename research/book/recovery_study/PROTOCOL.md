# Current-strategy recovery study: frozen finite protocol

Book, 2026-10-11 HKT. Research only. No live file, API, order, or service is changed.

## Baseline and scope
Baseline: book_e20combo_brk_cash, exact deployment-source ef1b0dd23fde620db407f13ecabadc1447c39669.
A deployment configuration exists; actual EC2 deployment and current actual holdings are UNVERIFIED.
The server's holdings are paper. An e20 paper book or simulated brk switch is never called the actual account.

## Motivation
The existing 7/14-day rotation can remain long while volatility rises. Thirty-day risk estimates react slowly.
Momentum shorts may lose during rebounds. Primary literature motivates these hypotheses, not a crypto forecast:
- Moreira & Muir, Volatility Managed Portfolios, https://www.nber.org/papers/w22208
- Daniel & Moskowitz, Momentum Crashes, https://www.aqr.com/insights/research/journal-article/momentum-crashes
Neither paper validates these exact rules, this market, or a next-week prediction.

## Exactly three new candidates; no parameter search or refitting
1. book_recovery_vol: same current model, multiply the entire signed book by
   min(1, 30-day / 7-day standard deviation of fixed-weight hourly portfolio returns).
   At least 90% complete rows are required in each estimate, otherwise keep the parent.
   No upscaling, no changed signs or coin ranks. Both lookbacks are borrowed from existing strategy horizons.
2. book_recovery_short: same parent, but a cash-funded short requires its own 24-hour return <= 0;
   positive or missing endpoint means cash for that short. Existing e20 down-mode book is unchanged.
3. book_recovery_both: apply the two above, volatility scaling after short confirmation.
Same daily clock (16 UTC), band 3%, gross cap, fees, spreads, execution lag, activity guard and liquidation.
An equality control with vol off and short filter off must reproduce the baseline.
No parameter/value/coin-specific exceptions based on trial returns.

## Evidence and selection
All historical data through Oct 10 and the reference log are spent exploratory data: no fresh holdout claim.
Use all standard 14-day cash-start windows and paired differences to the exact current baseline, recent
calendar subsets and fixed Oct9 weak profiles at 216/228/240 h. Weak profiles were selected before this study;
future falling/rebounding outcomes are diagnostics ONLY and never admission or signal features.
Archive/fresh profiles overlap and are never called 50 independent cases.

Primary historical improvement gate: all of full-history mean, median and p10 return >= baseline; max drawdown
distribution no worse (mean and worst); positive calendar-quarter-cluster paired mean lower bound after Bonferroni
for 3 candidates; pooled recent 2024-on mean difference >=0; weak-profile 6-context mean differences >=0.
Repeat at 2x fees/spreads and +1h lag; improvement must survive both to be a research promotion.
Also report risk score (0.4 Sortino +0.3 Sharpe +0.3 Calmar), closed short PnL accuracy/F1 if valid ledgers exist.
Proxy short onsets are never called executed win rate.
3 new comparisons are conditional study multiplicity ONLY. Prior project-wide selection is spent, so passing
this gate does not establish global false-positive control or authorize live use.

Freeze eligible candidates for prospective data from 2026-10-11 00:00 UTC, ending 2026-10-14 00:00 UTC.
No prospective result exists before those bars arrive. No repeated peeking to choose or retune the winner.
Actual account-switch testing requires timestamped real holdings, the current live model state and prices;
until then hypothetical switches remain explicitly hypothetical and production_eligible=false.
All failures and data hashes are saved. User-facing candidate recommendations include only verified
improvements; absence of a pass must never be concealed by renaming a point estimate a winner.

## Current remaining-time addendum (before any candidate outcome is read)
The old 9-10-day board remains a diagnostic reference, not today's horizon.
Also report paired returns at 168 and 192 hours (7 and 8 days) because main rules end Oct17 whereas the committed
live schedule says Oct18 12 UTC. Keep both end-date interpretations; do not assert a verified competition end.
A research promotion additionally needs nonnegative mean differences and no worse p10 at both horizons, for each
weak profile. Quarter bounds purge windows crossing calendar-quarter boundaries before resampling.
