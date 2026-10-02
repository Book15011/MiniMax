# Stress test of MR @4h

## 1. Leave one month out

All windows: MR @4h 2.088, team_rot_ew 1.324 (diff +0.764)
July 2026 dropped (39 windows): MR 1.464, ROT 1.370, diff +0.094
MR above ROT in 100% of 74 one-month exclusions; smallest diff +0.094 (2026-07), largest +1.325 (2026-04)
Most influential months (dropping them lowers the diff most):

| Month dropped | Windows dropped | MR | ROT | Diff |
|---|---|---|---|---|
| 2026-07 | 39.0 | 1.464 | 1.370 | +0.094 |
| 2022-12 | 45.0 | 1.936 | 1.316 | +0.620 |
| 2022-11 | 44.0 | 1.946 | 1.321 | +0.625 |
| 2023-11 | 44.0 | 2.000 | 1.352 | +0.648 |
| 2024-05 | 45.0 | 1.991 | 1.335 | +0.656 |
| 2024-06 | 44.0 | 1.990 | 1.331 | +0.659 |

**Check 1 PASSES** (needs diff > 0 without July 2026 and in >= 90% of exclusions)

## 2. Plateau (SCREEN only for the check; REL reported)

| Run | SCREEN gate passed | SCREEN median R | SCREEN worst 10% | REL | vs team_rot_ew [90%] |
|---|---|---|---|---|---|
| MR @4h (base) | 29% | +0.79% | -8.04% | 2.088 | (study) |
| bb_k_1.5 | 28% | +0.50% | -8.72% | 1.511 | +0.187 [-0.712, +0.719] |
| bb_k_2.5 | 28% | +0.82% | -5.75% | 2.577 | +1.253 [-0.502, +1.500] |
| rsi_25 | 26% | +0.47% | -7.42% | 2.030 | +0.706 [-0.583, +1.231] |
| rsi_35 | 31% | +0.93% | -9.05% | 1.777 | +0.453 [-0.797, +0.891] |

**Check 2 PASSES** (each neighbour within 0.5 pt of median R and 5 pt of gate pass on SCREEN)
