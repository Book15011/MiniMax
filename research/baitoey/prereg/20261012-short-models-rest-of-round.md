# Pre-registration: does any short model beat e20v45 over the rest of this round? (independent test)

Written 2026-10-12 06:00 UTC, before any result of this test was computed. Author: baitoey. Research only; no live change.

**Question.** The team asked for an independent check of the new short models (`results/scoring/leaderboard_short_ranked.md`) against the live model, e20v45 (`pol_switch_vt_tl_e20v45`). The main objective is the time left in this round, not the full history.

## Starting state (measured before the test)

- Round hour 186: 2026-10-12 06:00 UTC. 150 hours remain until 2026-10-18 12:00 UTC.
- e20v45 on Book's live-price replay (`results/book/paper-live/paper_live.py`): **-2.84%**. The EC2 account itself is UNVERIFIED.
- BTC since the round start: **-1.53%**.
- e20v45 holds AAVE, FET, FIL, NEAR, PUMP and WLD, about 16% each.

## Models

Every model in `results/scoring/leaderboard_2.csv` (121), using its cached 2,298-window run (tool version `3036a0d8bfdaa6a0`).

**Excluded (18):** models calibrated on, or built from, the reference log, pending the AGENTS rule 7 question:
- `book_pooled_trend`, `book_pooled_offsets` and `book_pooled_offsets_v2`;
- `book_daily_channel` and `book_clone_ourcoins`;
- `book_cloneall_*` (11 models);
- `book_e20clone_cash` and `book_e20clone_flip`.

That leaves 103 models, reported in four groups:
- **A:** Book's 13 ranked short models.
- **B:** other short or long/short models.
- **C:** e20v45 with a short or protection add-on.
- **D:** everything else.

References: e20v45, cash and BTC hold.

## Past rounds like ours

Use the 14-day windows starting 12:00 UTC where, at hour 186, both of these hold:
- e20v45's return is within 3 points of -2.84%;
- BTC's return is within 3 points of -1.53%.

**Primary sample (independent of Book's selection data).** Drop every round whose remaining period (hours 186-336) overlaps any of the 50 weak-market cases Book used to build and rank the models. These are the archived and fresh-BTC cases in `results/book/20261009-weak-eval-v2/cases.parquet`, each covering its checkpoint plus 228 hours. If fewer than 40 rounds remain, the primary sample becomes all similar rounds.

**Secondary sample.** All similar rounds.

## Outcome

- **Model return R:** the model's own return over hours 186-336, after the end-of-round selling cost. Subtract 0.20% switching cost for every model except e20v45.
- **Final account:** (1 - 2.84%)(1 + R) - 1.
- **Comparison with e20v45:** for each round, d = R(model) - R(e20v45). Take the mean of d and bootstrap it by calendar month of the window start (10,000 resamples, seed 20261012).

## "Better than e20v45": all four, on the primary sample

1. The one-sided bootstrap p-value for mean d <= 0 is at most 0.10 / k, where k is the number of models tested (Bonferroni, family-wise 10%).
2. Median d >= 0.
3. The p10 of R is no more than 1.0 point below e20v45's.
4. No hard-gate failure in the full-history score (`failed_hard_gates` is empty in `leaderboard_2.csv`).

Models that meet 2-4 with an unadjusted p of 0.10 or less are reported as "promising, not proven". Nothing else is called better.

## Context only (not part of the decision)

- the secondary sample;
- mean d with no switching cost;
- median R split by BTC's move over the remaining period (falls 2% or more, within 2%, rises 2% or more);
- each model's full-history HEADLINE.

A live forward check since Book froze the ranking (2026-10-10) would cover only about 42 hours, or two daily decisions. It is too short to tell anything and is not run.
