# Selection and sizing recovery study — pre-registered finite extension

Book, 2026-10-11 HKT; research only. Baseline unchanged: book_e20combo_brk_cash, deployment source ef1b0dd.
The earlier vol/short-confirm study has three failures. They remain failures, with no threshold relaxation.
This study asks a different question: is relative coin selection or equal sizing holding back recovery?
All prior history remains spent, no fresh holdout. Actual EC2 holdings/deployment remain UNVERIFIED.

Three additional fixed candidates (six new total across this research task):
- book_recovery_abs: in e20 up mode, a chosen long with non-positive mean 7/14-day risk-adjusted momentum
  is left as cash. No replacement coin, no enlargement of any existing short. Down mode unchanged.
- book_recovery_iv: in up mode, allocate the parent's positive gross proportionally to inverse 30-day hourly
  volatility, at most 25% per coin. Downward scale if estimated long-book risk exceeds the parent's.
  Existing shorts unchanged. No leverage, no extra short budget from this adjustment.
- book_recovery_abs_iv: apply both; inverse-vol sizing distributes only the surviving positive gross.
All horizons and numbers come from existing model concepts, not an optimizer. No coin/date exceptions.

Use identical paired evaluator to prior study: 2298 cash-start 14-day cases; fixed weak archive/fresh profiles;
168/192h current remaining-time interpretations; 216/228/240h old-board diagnostics.
Keep primary gates unchanged. Increase new bounds' family count to SIX, never decrease it.
All-historical mean/median/p10 must not decline; mean/worst drawdown must not worsen; recent mean and weak
profile means must not decline; purged quarter-cluster one-sided lower bound must exceed 0; 2x costs and
+1h lag must confirm any pass. No recommendation from weak windows alone.
No model switches, broker, live configuration, signing APIs or services are changed.

The first study tests model core only, without the live runner's endgame lock-in. Every promotion also requires
a separate endgame-aware and same-holdings replay before any live recommendation. This is a stronger condition,
not an approval to switch. No true prospective evidence yet. Forward evaluation is still frozen from
2026-10-11 00:00 UTC to 2026-10-14 00:00 UTC; do not retune on it.
