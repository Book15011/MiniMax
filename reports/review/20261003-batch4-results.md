# Batch 4 results: four return-first candidates (2026-10-03, Book)

| | |
|---|---|
| Pre-registration | `reports/review/20261003-prereg-batch4.md`, committed alone as `93e13eb` before any scoring. Rebased as `f736cdc`, content unchanged (`git range-diff`: equal) |
| Code | `4dbd7db`, rebased as `e614c01` |
| Base | `feature/return-first` at `4371453`: the PART 8 rescore (`e1f7bd8`) and its leaderboard |
| Rebase or merge | **rebase.** AGENTS.md states no preference. Its only rule on history is never to rewrite someone else's branch; this branch is mine, unpushed, and the two commits only add files plus one appended config block. The rebase was clean |
| Tool version | `3036a0d8bfdaa6a0`: this worktree, and the registry rows of baitoey_vt_mom, pol_switch_vt_tl and team_cash |
| Registered runs | 4, one per model, each with `scripts/lock harness-book -- nice -n 10 .venv/bin/python -m backtest.run --model <name> --score`, at commit `e614c01` (clean). Reports in `reports/<model>/20261003-*` |
| Scratch runs | 3.2b (`book_coin_trend_ls`) and top-3 (`book_vt_top3`): `backtest.scoring.score.score_model` called directly, as `results/pol/20261001-final/volume.py` did. Never registered. `results/book/20261003-batch4/scratch/` |
| Analysis | `results/book/20261003-batch4/phase_b.py`, which uses the tool's own weight, HIT and bootstrap functions. Self-checks: the sub-pool weight rule reproduces the tool's full-pool and in-sample weights, and every model's HEADLINE_RET on both pools, with error 0.0 |

**Deviation recorded in the pre-registration:** book_vt_dual gives vt_mom only the coins it kept as previous holdings. No other deviation.

## 1. Score table

Full pool unless marked; 2,298 windows; pi_up 0.543.

- HIT UP and DOWN are each group's HEADLINE_RET (the mean of the three bars).
- SCREEN and CONFIRM are HEADLINE_RET on each period by the pre-registered sub-pool rule; the tool's REL period check is in brackets.
- Bootstrap: the tool's paired calendar-month bootstrap, 2,000 draws, seed 20261002, 90% interval of HEADLINE_RET(row) − HEADLINE_RET(baseline).

| Model | HEADLINE_RET | without post-holdout | HIT LENIENT / MIDDLE / STRICT | HIT UP / DOWN | CS_HIT | SCREEN | CONFIRM |
|---|---|---|---|---|---|---|---|
| book_vt_dual | 0.532 | 0.474 | 0.598 / 0.560 / 0.439 | 0.683 / 0.353 | 0.365 | 0.372 (0.95) | 0.527 (2.10) |
| book_coin_trend | 0.353 | 0.300 | 0.504 / 0.423 / 0.131 | 0.516 / 0.159 | 0.287 | 0.342 (0.01) | 0.283 (0.00) |
| book_vt_breadth | 0.516 | 0.456 | 0.610 / 0.547 / 0.390 | 0.685 / 0.314 | 0.329 | 0.376 (0.75) | 0.495 (1.09) |
| book_vt_top4 | 0.572 | 0.519 | 0.636 / 0.595 / 0.484 | 0.744 / 0.367 | 0.363 | 0.425 (0.96) | 0.564 (2.39) |
| *3.2b coin_trend with shorts (scratch)* | *0.341* | *0.281* | *0.481 / 0.399 / 0.143* | *0.467 / 0.192* | *0.289* | *0.328 (0.05)* | *0.268 (0.07)* |
| *top-3 (scratch)* | *0.586* | *0.503* | *0.629 / 0.612 / 0.517* | *0.721 / 0.426* | *0.379* | *0.444 (0.50)* | *0.539 (2.85)* |
| VT baitoey_vt_mom | 0.609 | 0.556 | 0.652 / 0.623 / 0.551 | 0.805 / 0.376 | 0.368 | 0.459 (1.03) | 0.602 (2.56) |
| SW pol_switch_vt_tl | 0.548 | 0.456 | 0.601 / 0.564 / 0.478 | 0.635 / 0.444 | 0.366 | 0.469 (0.99) | 0.456 (2.00) |
| CASH team_cash | 0.372 | 0.326 | 0.747 / 0.315 / 0.054 | 0.380 / 0.361 | −0.002 | 0.320 (0.00) | 0.322 (0.00) |

| Model | Hard gates G1 / G4 / G5 | Report-only gates failed | Worst R | Median MDD | Turnover / window | Average exposure | Guard-only share | vs VT [90%] | vs SW [90%] |
|---|---|---|---|---|---|---|---|---|---|
| book_vt_dual | pass | none | −19.9% | 7.8% | 3.32 | 0.52 | 31% | −0.077 [−0.110, −0.041] | −0.015 [−0.088, +0.059] |
| book_coin_trend | pass | none | −24.1% | 6.1% | 2.09 | 0.50 | 55% | −0.256 [−0.352, −0.159] | −0.195 [−0.254, −0.119] |
| book_vt_breadth | pass | none | −16.8% | 7.3% | 3.04 | 0.49 | 47% | −0.093 [−0.123, −0.063] | −0.032 [−0.084, +0.024] |
| book_vt_top4 | pass | none | −30.7% | 10.2% | 3.20 | 0.69 | 62% | −0.037 [−0.065, −0.010] | +0.024 [−0.053, +0.108] |
| *3.2b (scratch)* | *pass* | *none* | *−27.6%* | *6.9%* | *2.79* | *0.57* | *55%* | *−0.268 [−0.366, −0.166]* | *−0.207 [−0.269, −0.126]* |
| *top-3 (scratch)* | *pass* | *none* | *−30.0%* | *10.1%* | *2.98* | *0.67* | *69%* | *−0.023 [−0.063, +0.018]* | *+0.038 [−0.038, +0.118]* |
| VT | pass | none | −30.8% | 10.1% | 3.59 | 0.72 | 48% | — | +0.061 [−0.005, +0.136] |
| SW | pass | none | −27.0% | 8.6% | 4.72 | 0.69 | 37% | −0.061 [−0.136, +0.005] | — |
| CASH | pass | G6 median | −0.07% | 0.02% | 0.06 | 0.00 | 0% | −0.237 [−0.304, −0.150] | −0.176 [−0.247, −0.095] |

## 2. Selection rule (pre-registered, section 5.3)

Thresholds:
- R2: HEADLINE_RET above both VT (0.609) and SW (0.548).
- R3: above VT in SCREEN (0.459) and in CONFIRM (0.602).
- R4: worst R at least −35.8% (VT's −30.8% minus 5 points).

| Model | R1 hard gates | R2 | R3 | R4 | Result |
|---|---|---|---|---|---|
| book_vt_dual | PASS | FAIL (0.532) | FAIL (0.372 / 0.527) | PASS (−19.9%) | not a candidate |
| book_coin_trend | PASS | FAIL (0.353) | FAIL (0.342 / 0.283) | PASS (−24.1%) | not a candidate |
| book_vt_breadth | PASS | FAIL (0.516) | FAIL (0.376 / 0.495) | PASS (−16.8%) | not a candidate |
| book_vt_top4 | PASS | FAIL (0.572: above SW, below VT) | FAIL (0.425 / 0.564) | PASS (−30.7%) | not a candidate |

**Candidates: none.** No batch-4 model beats baitoey_vt_mom on HEADLINE_RET, overall or in either period. The scratch variants are never candidates; the top-3 version would also fail R2 and R3.

## 3. Levers (section 1 of the pre-registration)

| Model | Lever | HIT on its lever side vs VT | Other side vs VT | Pulled? |
|---|---|---|---|---|
| book_vt_dual | DOWN | 0.353 vs 0.376 (−0.023) | UP 0.683 vs 0.805 (−0.122) | no. It cut worst R to −19.9% (VT −30.8%) and median MDD to 7.8% (10.1%) |
| book_coin_trend | DOWN | 0.159 vs 0.376 (−0.217) | UP 0.516 vs 0.805 (−0.289) | no |
| book_vt_breadth | DOWN | 0.314 vs 0.376 (−0.062) | UP 0.685 vs 0.805 (−0.120) | no. Best worst R of the batch (−16.8%) |
| book_vt_top4 | UP | 0.744 vs 0.805 (−0.061) | DOWN 0.367 vs 0.376 (−0.009) | no |

The three models that cut exposure lost less in the worst windows but cleared the bars less often, including in DOWN windows. VT already clears the DOWN bars more often than CASH (0.376 vs 0.361), so there is little to gain by stepping aside. A likely reason (**UNVERIFIED**, not tested): when BTC falls, the coins vt_mom holds often still make money, and going to cash gives that up.

## 4. REPORT-ONLY, NOT PRE-REGISTERED: the 150-team scenario

Not used for selection. These are the larger-field cuts from `reports/review/20261002-hit-metric-review.md` (Pol), the top 13% of the previous edition's leaderboards:
- UP windows: +8.08% (round 469, the final; only 16 teams);
- DOWN windows: −0.00% (round 456; used as 0.00%) or +0.60% (round 455).

R_liq on the full pool, w′ weights. The average is pi_up × HIT UP + (1 − pi_up) × HIT DOWN, with pi_up = 0.543 (the same weighting as HEADLINE_RET).

| Model | HEADLINE_RET (normal) | HIT UP at +8.08% | HIT DOWN at 0.00% | Average | HIT DOWN at +0.60% | Average |
|---|---|---|---|---|---|---|
| book_vt_dual | 0.532 | 0.414 | 0.330 | 0.376 | 0.304 | 0.364 |
| book_coin_trend | 0.353 | 0.301 | 0.123 | 0.220 | 0.103 | 0.210 |
| book_vt_breadth | 0.516 | 0.406 | 0.277 | 0.347 | 0.245 | 0.332 |
| book_vt_top4 | 0.572 | 0.458 | 0.354 | 0.411 | 0.315 | 0.392 |
| *3.2b (scratch)* | *0.341* | *0.299* | *0.154* | *0.233* | *0.122* | *0.218* |
| *top-3 (scratch)* | *0.586* | *0.436* | *0.421* | *0.429* | *0.391* | *0.416* |
| VT | 0.609 | 0.468 | 0.357 | 0.418 | 0.334 | 0.407 |
| SW | 0.548 | 0.398 | 0.420 | 0.408 | 0.384 | 0.392 |
| CASH | 0.372 | 0.000 | 0.054 | 0.025 | 0.000 | 0.000 |

At these cuts VT, SW, book_vt_top4 and the top-3 variant all sit around 0.39–0.43. Only the top-3 scratch variant edges VT, by about 0.01, which is not tested for significance. CASH drops to almost 0.

## 5. Notes and UNVERIFIED items

- **UNVERIFIED: the 150-team cuts.** They come from one previous edition, and the UP cut from a 16-team final. The 150-team field size is a team estimate.
- **UNVERIFIED: the live-like weights are v2 preliminary** (as of 2026-09-30). The Oct 4 rerun changes them and the tool version, so these numbers will move.
- **UNVERIFIED: why replay agreement for book_vt_dual levels off at about 90%** (see the pre-registration).
- **The shared leaderboard changed format.** Before these runs, `results/scoring/leaderboard.md` showed a "margin 0.03" tie-rule view and rows from other branches' models, written by newer code on another branch. Registering from `feature/return-first` rewrote it in this branch's format, as docs/EVALUATION.md warns. It returns to the other format when someone scores from that code again.
- **The 20-window sanity run in PHASE A** showed worst R near −8% for 3.1–3.3. The full pool's worst is −17% to −24%. The 20 windows simply missed the worst fortnights.
