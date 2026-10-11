# Additional rejection-only audit of frozen recovery models

Book, frozen 2026-10-11 12:29:00 UTC (trusted client clock; remote clock offset known).
User requested stronger evidence before any change. No new model, parameter search or live action.
Parent branch feature/book-rebound-recovery at 3a11857; numeric model source ea93ce2.
Earlier twelve model failures and their finite stopping rule remain unchanged.
This is a separately disclosed audit extension, decided after reading historical results.
Any favourable result here cannot promote an earlier failure, establish fresh evidence, or prove future returns.

## Fixed models and scenarios

book_e20combo_brk_cash, book_recovery_allshort24, book_recovery_rebound.
Recompute base summaries from the exact saved runs; independently replay three adverse scenarios for all three:
(1) every executed-side fee, spread and terminal liquidation charge doubled;
(2) execution lag increased from one completed hour to two, other costs unchanged;
(3) both adverse changes together.
No costs are removed. Shared original caches are read only; new runs use an owned cache.
All 2298 identical cash-start windows and the exact original data, liquidity and model rules remain.
Report 120/144/168/192/216/228/240/336-hour outcomes. Added 5/6-day cuts are timing sensitivity,
not retrospective changes to the original 7/8-day or 14-day gates.
Conditional purged-quarter bootstrap bound uses 36 = 12 tried recovery hypotheses times 3 adverse scenarios.
This is conservative within this stated family only, not control of the project's accumulated searches.
Original full-history and recent/weak gates remain reported; original failure veto applies irrespective of stress results.

## Stability and independent arithmetic

Verify each model/scenario return, max drawdown and existing FLOORED.V1 composite directly from saved hourly arrays.
No replacement score and no re-ranking on a favourable scenario.
Calendar-year paired differences purge windows crossing the year boundary.
Report all leave-one-calendar-year-out mean differences, separately for full history and 2024 onward.
Report each of 14 fixed disjoint fortnight offsets; all offsets shown, never selected.
These groups and offsets are descriptive sensitivity, not independent holdouts or confidence certificates.
Quantify gross exposure above one in the simulator; target caps do not cure marked exposure drift.
Check inherited model, live, backtest and config sources and every input content hash before/after.
Preserve both earlier frozen cohorts and the all-13 common prospective cohort without edits.

## Decision limits

No production promotion if original historical gates fail, fresh prospective evidence is incomplete,
actual EC2 holdings/deployment/endgame are unverified, or competition hard gates remain unverified.
The live runner's endgame and memory are not reproduced by cash-start research paths.
No actual-account switch claim, no signed API, secrets, orders, live edits or main merge.
Original broad-universe query failure BCH 29/30 stays failed; adaptive scoring stays OFF.
Update the research leaderboard with a clearly separated audit link/status, without changing its frozen ranking.
