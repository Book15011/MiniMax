# Pre-registration: stress test of MR @4h (Baitoey, 2026-10-01)

Follows `20261001-mean-reversion.md`, where MR @4h (`baitoey_mr_bbrsi`, 4 h bars and rebalance) scored REL 2.088
against 1.324 for team_rot_ew, with a wide interval (−0.587, +1.240) and 76% of its score from the top 5% of
windows, mostly one calm stretch in July 2026. Written and committed before these checks run. No parameter of
MR @4h changes because of them; they decide only whether it is presented to the team as a candidate.

## 1. Leave one month out

For each calendar month from 2020-06 to 2026-07, drop every scored window that overlaps that month and recompute
HEADLINE REL FLOORED for MR @4h, team_rot_ew and the six field members (the REL unit is recomputed on the kept
windows; live-like and recency weights renormalized). **Survives if** MR @4h stays above team_rot_ew with July
2026 dropped AND in at least 90% of the one-month exclusions.

## 2. Plateau (SCREEN only)

One change at a time at 4 h: `bb_k` 1.5 and 2.5, `rsi_entry` 25 and 35. **Survives if** each neighbour’s SCREEN
median R is no more than 0.5 points below MR @4h’s and its SCREEN return-gate pass share no more than 5 points
below. Their REL and `compare` against team_rot_ew are reported, not used for any choice.

Output: `results/baitoey/20261001-mr-stress/`. Script: `research/baitoey/mr_stress.py`.
