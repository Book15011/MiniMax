# Current strategy recovery research — Book, 2026-10-11

**Decision: no new strategy is recommended. Six fixed candidates and 127 compatible frozen runs produced no verified improvement under the saved checks. The live bot was not changed.**

## Current strategy and account evidence

The selected live configuration is book_e20combo_brk_cash at ef1b0dd: 7/14-day volume-timed momentum, BTC regime switching, 20-day breakdown exits and conditional cash-funded shorts. Decisions are daily at 16 UTC. The short leg is capped at 25% gross, three coins and 10% per coin, and does not trim the long book.
The committed runner also has a +3% cash lock from round day 10. Core backtests below do not include that runner overlay; they cannot validate an account switch.
Actual EC2 deployment, current holdings and equity are **UNVERIFIED**. Every holdings file found here is paper. A user question requesting a timestamped actual account snapshot is pending. No secrets or signed competition endpoints were accessed.

The latest saved supported-universe diagnostic is 2026-10-11 01:00:00+08:00: 28/29 coins rose over 48 h, while BTC remained down about 2.2% over 7 d. The added cash-short regime is OFF; e20 switch is UP. This is an observed rebound, not a forecast for the remaining week.
A fresh empty-memory decision would target AAVE, ADA, FIL, NEAR, PUMP and WLD at about 16.18% each. These are **hypothetical target weights, not verified actual positions**. An existing model-memory chain can hold different coins.

## What was tested and why

Six simple rules were committed before reading their results: faster volatility scaling, recent downside confirmation of cash shorts, their combination; positive absolute momentum for longs, inverse-volatility sizing with risk no higher than the parent, and their combination. No fitted clone coefficients were used. No parameter grid or coin/date exceptions were searched.
Every model shares the baseline costs, lag, daily clock, activity guard and gross limit. The two protocols specify the rejection rules in advance. No threshold was lowered after failure.
The first study has 252 passing regression/control tests; after all six models, 257 passed. Eight additional workflow tests verify current-review uncertainty and completed-bar/data-gap guards.
Both study audits verify 55,152 model/horizon outcomes each against raw arrays: return and drawdown errors are zero; summary rounding error is below 1e-16. The baseline configuration and inherited runtime match the selected committed revision.

## Current-market comparison and how to read it

New diagnostic: /home/ubuntu/test/MiniMax/results/book/20261011-recovery-current-context-v1/leaderboard_current_diagnostic.md. Published shortcut: /home/ubuntu/test/MiniMax/results/scoring/leaderboard_recovery.md.
This compares all 121 saved-board runs plus six new candidates on 25 spaced BTC-only historical matches, at 7/8-day horizons. It ranks by the lower of those two average returns. A high point-estimate rank is not a reliable winner.
Uncertainty resamples 23 purged cases across 14 quarters jointly over 127 models × 2 horizons. No model has positive uniform lower differences at both horizons while passing the remaining checks. All 381 source-cache artifacts were independently rehashed. Query features were independently reconstructed with zero error, and adding future rows did not change them.
BTC-only matching omits alt breadth. The original broad query still fails at BCH: 29/30 endpoints. The live-supported 29-coin universe is a different universe; its complete endpoints do not repair the original failure. Adaptive scoring stays OFF. The old Oct 9 weak table is retained unchanged.
Historical periods and clone-fitting periods are spent research evidence. Coefficients fitted on October observations are not retrospectively out of sample on older dates. Neither this diagnostic nor a raw old-board rank authorizes a live switch.
The new CSV includes mean, median, bad 10%, worst, drawdown and CS for each model. CS means daily-HKT floored 0.4 Sortino + 0.3 Sharpe + 0.3 Calmar, not HEADLINE_RET. These study p10 values use linear quantiles; old weak-board headline p10 uses an empirical quantile. Do not mix their numeric conventions.

## Verified research context

Crypto time-series momentum is documented by [Liu & Tsyvinski](https://www.nber.org/papers/w24877); it does not establish an edge for our exact coins, clocks or parameters.
[Moreira & Muir](https://www.nber.org/papers/w22208) motivate volatility-managed exposure, while [Cederburg et al.](https://www.sciencedirect.com/science/article/pii/S0304405X2030132X) show that volatility management need not improve real-time performance. Our failed volatility variants are retained rather than justified away.
[Daniel & Moskowitz](https://www.aqr.com/insights/research/journal-article/momentum-crashes) explain rebound risk for momentum shorts. This motivates testing both falling and rebound scenarios; it is not a bearish forecast.
The [BLS release calendar](https://www.bls.gov/schedule/2026/home.htm) schedules CPI on Oct 14 and PPI on Oct 15, both 20:30 HKT. The [Fed calendar](https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm) schedules the next FOMC meeting for Oct 27–28, beyond either documented competition end. Events are risk context, not directional trade signals.

## What remains before any recommendation

A timestamped real portfolio and model state are required for meaningful same-holdings switch costs. A full runner replay must retain the endgame policy and distinguish staying with the model from switching and resetting memory.
The forward cohort and parameters are frozen for Oct 11 08:00 HKT → Oct 14 08:00 HKT. The runner requires completed metadata, all hourly rows and available held-coin prices, and fixes costs and spreads. These data-integrity guards were amended after the period began without reading or producing results; strategy parameters and dates stayed fixed. This is not wholly untouched evaluator preregistration. The runner refuses to score until the full period exists; preflight correctly returned WAITING with no results. No automation was created or started. One 3-day future path alone cannot establish a robust new winner.
Run from this Book worktree after the full period is recorded: .venv/bin/python -B -m research.book.recovery_study.forward. It performs no network call or order.
Further work should address genuinely new causal mechanisms or independent forward evidence. Do not rerun the six rejected controls with tuned thresholds, expand clone capacity, or erase failures to manufacture a pass.

## Remote locations

- Worktree: /home/ubuntu/test/MiniMax/.worktrees/book-book-recovery-study (feature/book-recovery-study).
- Current comparison: /home/ubuntu/test/MiniMax/results/scoring/leaderboard_recovery.md and .csv.
- All six trial contexts: /home/ubuntu/test/MiniMax/results/scoring/recovery_trials.csv.
- Vol/short-confirm study: /home/ubuntu/test/MiniMax/results/book/20261011-recovery-study-v1.
- Selection/sizing study: /home/ubuntu/test/MiniMax/results/book/20261011-recovery-selection-v1.
- All-model current diagnostic: /home/ubuntu/test/MiniMax/results/book/20261011-recovery-current-context-v1.
Source, protocols, tests and continuation instructions are in this research folder. Large results and data are gitignored and not committed.
