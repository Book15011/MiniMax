# BTC-adjusted selection: results and reading guide

**Decision: no upgrade recommended. Both fixed variants failed the saved improvement rule. The six earlier failures remain failed.**

This study changes which coins the long book selects. It does not add a new short-timing signal or fit the reference log.
Source c1143d4 on feature/book-residual-recovery. Baseline is the selected committed brk-cash model from ef1b0dd.
Actual EC2 deployment, account holdings and equity remain UNVERIFIED; server states are paper. No live changes or signed APIs.

## The idea in plain language

A coin can appear strong because it tends to move more than Bitcoin. This test asks whether its extra strength is more useful.
Rough example before volatility normalization: BTC rises 2%; a coin that usually moves3 times BTC rises 6%, adding little beyond its usual response.
A second coin that usually moves with BTC rises 3%, adding about 1 percentage point beyond that response.
The first variant ranks this additional strength. The second averages that rank 50/50 with the existing momentum rank.
The 50/50 weight was fixed before results; no grid, refitting to strategy returns, coin exceptions or date exceptions were used.

Beta estimates use30 days ending14 days before the decision, then measure the following 7/14 days. Scoring observations do not train beta.
Daily16UTC decisions, existing price/volume exits, top 6 / keep 12, gross limits and parent short targets are retained.
Long allocation may use only its parent decision positive gross. Estimated long risk is scaled down to its parent; if total signed-book risk is larger, the exact parent is used.
The independent control fixture confirms a real selection change with shorts preserved; the rule is not an always-fallback placeholder.

## Historical comparison

All 2,298 standard14-day cash-start windows use identical fees, spread, one-hour execution lag, guard and endpoint liquidation.
An audit independently reconstructed41,364 model/horizon outcomes: zero return, drawdown and CS error; summary rounding error below1e-16.
All 117 inherited runtime files and exact live/harness/scoring/validation configuration match the selected baseline.
The prior seven-model forward worktree is unchanged. Full regression checks: 271 PASS in 194.23 seconds. The publication-only index-label failure is preserved; restoring the label changed no numeric result.

| Model | Mean14d | Median | Bad10 | Worst | Mean drawdown | CS | Improvement pass |
|---|---:|---:|---:|---:|---:|---:|---|
| book_e20combo_brk_cash | +3.732% | +0.283% | -11.522% | -26.049% | 10.770% | 0.15230 | baseline |
| book_recovery_resid | +3.407% | -0.308% | -11.509% | -24.013% | 10.860% | 0.13889 | NO |
| book_recovery_resid_blend | +3.640% | -0.304% | -11.496% | -24.480% | 10.861% | 0.15017 | NO |

Both variants lost average and median return and slightly worsened average drawdown. The blend reduces part of the loss but does not establish an edge.
The eight-hypothesis purged-quarter mean-difference lower bounds are negative: about -1.05 percentage points for pure adjustment and -0.72 points for the blend.
They also failed the fixed recent/weak/horizon checks. No rejected parameter was changed and no stress-pass claim is made; stress execution is reserved for historical passes.

## How to read the updated model table

Remote shortcut: /home/ubuntu/test/MiniMax/results/scoring/leaderboard_recovery.md and .csv.
The table adds these two models to the earlier127, retaining the same25 spaced BTC-only historical matches and Oct 11 01:00 HKT query.
Rank is the lower of the7/8-day mean returns. It is a point estimate, not confidence or a live selection.
CSV includes rank, model, horizon, mean, median, bad10, worst, drawdown, CS, confidence differences and diagnostic pass.
CS is the daily-HKT floored 0.4 Sortino + 0.3 Sharpe + 0.3 Calmar convention. A high CS alone cannot pass the improvement rule.
Study bad10 uses linear quantiles; old leaderboard_2 headline bad10 uses the empirical convention. Read each table own definition.
The joint confidence review covers 129 models and 2 horizons, using23 purged cases in 14 quarters. Project-wide historical selection remains spent.
All eight new models have model-core diagnostics; full original competition gate eligibility is UNVERIFIED.
Short-imitation precision/recall/F1 measures resemblance to observed actions, not profitable-short accuracy. Existing short tables are unchanged.

## Updated market evidence and limits

AtOct 11 18:00 HKT,20/29 live-supported coins rose48h; BTC was downabout 2.57% over7 days. The added cash-short trigger was OFF and e20 switch UP.
This price observation is not a remaining-week forecast and did not reselect the frozen table cases.
The research store has 10 ticker-only hours after Oct 11 00:00 UTC; their hourly quote volumes are reconstructed from rolling 24-hour totals.
A first diagnostic used 65 configured harness symbols and mislabeled them supported; that attempt is preserved and corrected to the point-in-time 29-coin universe.
Original strict competition coverage still fails at BCH: 29/30. Completeness of another universe does not repair it. Adaptive activation remainsOFF.
Actual EC2 feed health is UNVERIFIED; research-store limitations do not prove a live-feed defect.
Actual same-holdings switch costs and runner endgame are not validated. No future evidence for these two candidates is claimed.

## Research sources

[Liu, Tsyvinski and Wu](https://economics.yale.edu/sites/default/files/2022-10/LiuTsyvinskiWu2019%20COMMON%20RISK%20FACTORS.pdf) document market and momentum components in crypto returns.
[Li and Zhu (2026)](https://www.sciencedirect.com/science/article/pii/S0275531926000255) discuss residual momentum and changing anomaly behavior out of sample.
The latter abstract was reviewed after protocol freeze; no strategy rule changed. Its paid full text was not obtained and its Lasso factor model was not implemented.
These sources motivate a hypothesis; they do not validate this BTC proxy, estimator, trading clock, net profit or forecast.

Evidence: /home/ubuntu/test/MiniMax/results/book/20261011-residual-recovery-v1.
Combined129model diagnostic: /home/ubuntu/test/MiniMax/results/book/20261011-residual-current-context-v1.
Reproduce from this remote worktree: .venv/bin/python -B -m research.book.residual_recovery.run.
After tests/audit PASS, refresh this fixed cohort using .venv/bin/python -B -m research.book.residual_recovery.publish_review.
The standard --score command updates the original primary board; it does not automatically refresh this separate diagnostic.

The tested strategy source, protocol and tests are committed. Large results/data/logs remain outside Git.
