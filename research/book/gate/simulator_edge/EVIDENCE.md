# Evidence and limitations — 2026-10-15

This finite research screen is verified and reported. It has not achieved a safe recovery method, a verified top-20 probability or the earlier 85% target.

## Scope and provenance

- Host: metallurgy-server. Book branch: feature/simulator-edge. Parent: feature/gate at 92da2831e99878bee3089bbee0f8a29d1a58c2f4.
- Main at inspection: 320984ee97ae162d0856d4ae926dae9796f0c7a5. No merge or live edit.
- Read committed measured-fill research 6357531, 670b9be and 7e76e3b, plus wallet fixes c1b521a / 4518fe0 / 197661d. These are committed observations; raw authenticated probe/wallet outputs were not independently available.
- Only three public metadata/quote calls were made. No secrets, signed calls, account client, orders or restarts.
- Eight complete quote days, October 7–14, were hashed. October 7 is warmup; October 14 is a 24-hour check, not a fresh 72-hour holdout.
- Quote cleaning removed 3,251 exact duplicates and quarantined 2,786 conflicting rows. No invalid numeric rows. Coverage is 86 recorded / 88 currently supported pairs, not proof of historical listings.
- The earlier BCH coverage failure and adaptive-scoring decision are not changed.

## Checks

- Core plus then-current research suite: 290 passed in 187.57 seconds.
- Expanded research suite including metric boundary cases: 18 passed in 0.58 seconds. These overlap the preceding suite; do not add the two counts.
- Independent verification reconstructed all 255 quote scenarios, with zero return and drawdown discrepancy. Maximum cash/fee ledger discrepancy is below USD 1e-7.
- Phase1 raw hourly reconstruction: 20,760 outcome rows; maximum return/drawdown discrepancy zero.
- Final publication reconstructs 31,140 hourly outcome rows from nine models; maximum return/drawdown discrepancy zero.
- All 411 pre-CS comparison rows and columns remain numerically unchanged after adding diagnostics.
- Independent closed-form reconstruction of 142 CS groups: maximum error 4.440892098500626e-16. All 108 hourly gross-exposure groups verified.
- Existing primary/recovery scoreboards are preserved. No model is production eligible; actual_top20_probability stays unavailable.

## Corrections preserved

Early red test logs remain in the results folder. An inherited hourly grid contained 86 off-hour timestamps in 2018, outside the scored 2022+ period. Correcting the clock grid reproduced all five already-completed hourly models exactly. No parameters were chosen on that repair.

Optional saved quote traces were added after the first run solely for verification; they reproduced the earlier numeric results. The original source hash and outputs remain preserved.

The first CS publisher attempt shadowed the hourly result list with a quote array and aborted while building the ranking. The variable was renamed. The independent publication check subsequently proved all original 411 comparison rows unchanged. This was a reporting failure, not a successful trial or a reason to select different outcomes.

The original protocol described 40 legacy gate settings. The source script and CSV contain 38. This documentation correction changed no model parameter or outcome.

## Material unresolved limits

The inherited parent proxy breaches 100% marked gross in 110/634 historical-check windows (maximum 107.46%). Its results cannot be described as a certified compliant live baseline. The new long benchmarks stay below 100%; the slower shorts stay below 53%.

Short execution, queues, large-order capacity, current EC2 wallet/holdings, pending orders, funded transition, moving cutoff and exact official endpoint remain UNVERIFIED. The 20% latency penalty is accepted from the user's WhatsApp report; its denominator/formula is unknown.

The old PaperExchange still permits optimistic buy/sell matching. This screen bypasses it. Do not use its attractive profits as deployment evidence.

CS over three daily returns is only a short-horizon diagnostic. Its floored ratios and outliers can produce a positive average even when the median portfolio return is negative. It is not the official judge score or a 14-day score.

## Artifacts

Code, frozen configuration, derived CSV and reports are committed here. Raw quotes, cash/fee ledgers, arrays, logs, failed attempts and JSON audits remain untracked at:

/home/ubuntu/test/MiniMax/results/book/20261015-simulator-edge-v1

Start with final_recommendation.md, then README.md and edge_results.csv. The separate convenient board is:

/home/ubuntu/test/MiniMax/results/scoring/leaderboard_simulator_edge.md

See evidence_manifest.json in the results folder for the final commit, artifact hashes and preservation checks.
