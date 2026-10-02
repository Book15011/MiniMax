# Return-first score (scoring v2): recheck, rescore and leaderboard (2026-10-02, Book)

| | |
|---|---|
| Branch | `feature/return-first` (`.worktrees/book-return-first`), on `feature/realtest` `f9bbc15` |
| Pre-registration | `reports/review/20261002-prereg-return-first.md`, commit `0e9280b`, committed alone before any run |
| Commits | `55e9091` live-like v2 wrapper · `56ad298` live-like v2 files · `b47e309` scoring v2 code, tests, config, docs · this note and the score reports |
| Tool version | `3036a0d8bfdaa6a0` (scoring v2). Previous: `56cb5a2e85d45862` |
| Runtime | timing run 427 s (pol_switch_vt_tl); batch of 25 models, 6 workers, 17:59–18:31 UTC (33 min wall; 3.2 hours summed over the 25 runs) |
| Review | not merged and not pushed. Pol or Baitoey reviews through `scripts/wt merge`. Nothing in the live runner, its config or any model was changed |

## 1. Lookalike weights v2 (preliminary)

- **Method:** PART 0's code, unchanged (`python -m src.validation.prelim_v2`), with these inputs:
  - 12:00 UTC starts;
  - T* = 2026-10-04 12:00 UTC;
  - as-of 2026-09-30 00:00 UTC, the panel's last bar;
  - pool end = the as-of, so 2,298 windows.
- **What the walk-forward chose:**
  - ensemble MIX (25 lookalikes + REC_60) with bandwidth 0.05. v1 had REC_60 with 0.10;
  - the direction test failed again, so no direction factor and no STOP.
- **Weight moved vs v1:**
  - total variation 0.49;
  - 11% of the v2 weight is on the 52 post-holdout windows, which v1 did not have;
  - on the common windows, each renormalized: total variation 0.46, correlation 0.46;
  - effective n 601 (v1: 991).
- **pi_up = 0.5431** on the full pool (1,248 of 2,298 windows UP) and 0.5392 in-sample. The validation reported 0.54.

**Top 10 lookalike windows (v2):**

| # | Start (12:00 UTC) | Weight ‰ | BTC 14-day log return | v1 rank of the same day |
|---|---|---|---|---|
| 1 | 2026-07-23 | 4.50 | −0.014 | 43 |
| 2 | 2023-07-20 | 4.37 | −0.038 | 190 |
| 3 | 2025-09-15 | 4.03 | −0.026 | 138 |
| 4 | 2023-05-14 | 3.87 | +0.013 | 351 |
| 5 | 2023-09-14 | 3.69 | +0.001 | 90 |
| 6 | 2022-12-17 | 3.68 | −0.008 | 148 |
| 7 | 2026-09-15 | 3.64 | +0.092 | (post-holdout) |
| 8 | 2026-05-11 | 3.43 | −0.048 | 296 |
| 9 | 2025-07-14 | 3.41 | −0.022 | 216 |
| 10 | 2026-08-29 | 3.17 | −0.003 | (post-holdout) |

These are calm, small-move fortnights.

## 2. Recheck

| Check | Result | Evidence |
|---|---|---|
| 6.1 Unit tests | **PASS** | `tests/test_return_first.py`, 11 tests: weights by hand and sum to 1 with UP share = pi_up; bars on 5 hand-built windows; HIT and HEADLINE_RET by hand for 2 toy models; bootstrap deterministic with its seed; LENIENT constant = mean of the two #20 cuts (also read from the file); 15 HKT + 15 UTC buckets for a 12:00 start; first decision at the window start with empty previous targets |
| 6.2 Independent recomputation | **PASS** | `tests/return_first_reference.py` imports nothing from `backtest/` or `src/`. On baitoey_vt_mom (top eligible), team_cash and team_btc_hold, both pools: largest difference 2.2e-16 (limit 1e-12) |
| 6.3 Sanity | **PASS** | See below |
| 6.4 Engine consistency | **FLAG** as pre-registered (> 1 pp), explained below | |
| 6.5 Full test suite | **PASS** | 220 passed |

**6.3, actual vs expected:**

| Check | Expected | Actual |
|---|---|---|
| CASH HIT_LENIENT | ≥ 1 − pi_up = 0.457 | 0.747 |
| CASH HIT_DOWN, LENIENT | 100% | 100% |
| CASH HIT_UP, LENIENT | not predicted | 53% (its keep-alive BTC gains beat the fees) |
| CASH MIDDLE / STRICT HIT_DOWN | ≤ 25% | 5.4% / 2.9% |
| CASH HIT_STRICT ≤ HIT_MIDDLE | yes | yes |
| BTC_HOLD HIT_UP, LENIENT and MIDDLE | ≥ 90% | 96% |
| BTC_HOLD HIT_DOWN, LENIENT | ≤ 30% | 22% |
| Candidates below CASH | listed | none, on either pool |

**6.4 detail.** Median |ΔR| between the 12:00 and 16:00 UTC windows of the same day:

| Model | Median abs ΔR | p90 | Median ΔR | Correlation |
|---|---|---|---|---|
| pol_switch_vt_tl | **1.02 pp (flag)** | 3.26 pp | −0.02 pp | 0.984 |
| team_rot_ew | **1.42 pp (flag)** | 4.24 pp | +0.07 pp | 0.976 |
| baitoey_mr_4h | 0.15 pp | 1.59 pp | 0.00 pp | 0.982 |
| *team_btc_hold (calibrator, no decisions)* | *1.01 pp* | *3.31 pp* | *−0.01 pp* | *0.985* |
| *team_cash (calibrator)* | *0.00 pp* | *0.01 pp* | *0.00 pp* | — |

- **The 1 pp expectation was set below the pure shift.** Holding BTC already gives 1.01 pp: both ends of the window move by 4 h, and BTC's median 4-hour move is 0.63 pp.
- **pol_switch_vt_tl is at the calibrator's level.**
- **team_rot_ew is about 0.4 pp above it.** Its keep-while-in-the-top-12 rule carries a different first decision for days: its windows needed about 9 decisions on average before they rejoined the shared history.
- **No systematic bias:** median ΔR is about 0 for every model.

**DEVIATIONS**

1. **Four models registered from `feature/volume` were not rescored:** pol_vt_mvr, pol_mr_cap, pol_switch_vtm_tl and pol_switch3_cap. A fifth, pol_switch_vt_tl_e20v45, was registered after the pre-registration. None of their code is on this branch. They stay on the leaderboard as previous-version rows.
2. **One build test failed inside the v2 rebuild (208 of 209 passed).** `test_e5` compares the 12:00-grid universe written by that run with the real config's 16:00 grid. That table is not used by the score; the harness keeps its 16:00 universe, as live. The repo suite itself passes, 220 of 220.

## 3. The new leaderboard

Tool `3036a0d8bfdaa6a0`. HEADLINE_RET on the full pool and without the 52 post-holdout windows. Tie = 90% month-bootstrap interval of the difference to the top contains 0.

| # | Model | HEADLINE_RET | without post-holdout (rank there) | HIT L / M / S | HIT UP / DOWN | Tie group | CS_HIT | min(SCREEN, CONFIRM) | old REL (rank among these) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **baitoey_vt_mom** | **0.609** | 0.556 (#3) | 0.65 / 0.62 / 0.55 | 0.81 / 0.38 | top | 0.368 | 1.03 | 2.10 (#6) |
| 2 | pol_switch_vt_tl | 0.548 | 0.456 (#4) | 0.60 / 0.56 / 0.48 | 0.64 / 0.44 | yes [−0.136, +0.005] | 0.366 | 0.99 | 2.29 (#3) |
| 3 | baitoey_rot_max | 0.546 | 0.509 (#5) | 0.58 / 0.56 / 0.49 | 0.69 / 0.37 | yes [−0.125, +0.001] | 0.296 | 2.14 | 2.06 (#7) |
| 4 | baitoey_mr_bbrsi | 0.499 | 0.467 (#7) | 0.75 / 0.54 / 0.21 | 0.53 / 0.46 | yes [−0.199, +0.009] | 0.150 | 0.58 | 1.37 (#10) |
| 5 | pol_switch_rot_mr | 0.514 | 0.461 (#8) | 0.58 / 0.54 / 0.43 | 0.69 / 0.30 | no | 0.342 | 1.12 | 1.62 (#9) |
| 6 | pol_switch_rmax_tl | 0.491 | 0.421 (#2) | 0.54 / 0.51 / 0.43 | 0.55 / 0.42 | no | 0.312 | 1.54 | 2.31 (#2) |
| 7 | pol_combo_rb | 0.481 | 0.457 (#9) | 0.58 / 0.52 / 0.35 | 0.73 / 0.19 | no | 0.297 | 0.11 | — |
| 8 | pol_switch_rmax_mr | 0.475 | 0.449 (#10) | 0.53 / 0.50 / 0.39 | 0.64 / 0.28 | no | 0.395 | 1.71 | 2.13 (#5) |
| 9 | pol_switch_rt | 0.472 | 0.408 (#12) | 0.53 / 0.50 / 0.39 | 0.54 / 0.39 | no | 0.299 | 1.16 | 1.78 (#8) |
| 10 | baitoey_mr_4h | 0.472 | 0.475 (**#1**, by CS_HIT in a 7-model tie group) | 0.59 / 0.54 / 0.29 | 0.60 / 0.32 | no | 0.461 | 1.48 | 3.03 (#1) |
| 11 | pol_combo_all | 0.458 | 0.421 (#11) | 0.59 / 0.53 / 0.25 | 0.65 / 0.23 | no | 0.284 | 0.00 | — |
| 12 | pol_mom_ss | 0.458 | 0.430 (#6) | 0.57 / 0.52 / 0.28 | 0.47 / 0.45 | no | 0.321 | 0.90 | 1.08 (#12) |
| 13 | pol_combo_rt | 0.456 | 0.397 (#13) | 0.55 / 0.50 / 0.32 | 0.57 / 0.33 | no | 0.286 | 0.19 | — |
| 14 | pol_switch_rc | 0.443 | 0.373 (#17) | 0.58 / 0.45 / 0.31 | 0.54 / 0.34 | no | 0.247 | 0.50 | — |
| 15 | pol_switch3 | 0.438 | 0.380 (#16) | 0.52 / 0.48 / 0.31 | 0.53 / 0.33 | no | 0.841 | 0.89 | 1.35 (#11) |
| 16 | pol_combo_rtt | 0.434 | 0.372 (#18) | 0.55 / 0.49 / 0.26 | 0.57 / 0.27 | no | 0.295 | 0.07 | — |
| 17 | pol_trend_ls | 0.418 | 0.395 (#14) | 0.51 / 0.46 / 0.29 | 0.37 / 0.48 | no | 0.288 | 0.97 | 2.18 (#4) |
| 18 | pol_combo_ms_tl | 0.415 | 0.393 (#15) | 0.52 / 0.47 / 0.25 | 0.38 / 0.45 | no | 0.295 | 0.46 | — |
| 19 | baitoey_tg_mom | 0.374 | 0.351 (#19) | 0.55 / 0.43 / 0.14 | 0.36 / 0.40 | no | 0.269 | 0.57 | 0.91 (#13) |

**Reference rows:**

| Benchmark | HEADLINE_RET | without post-holdout | HIT L / M / S | CS_HIT |
|---|---|---|---|---|
| ROT_EW | 0.547 | 0.507 | 0.59 / 0.56 / 0.49 | 0.306 |
| ROT_IV | 0.511 | 0.456 | 0.61 / 0.55 / 0.38 | 0.334 |
| BTC_HOLD | 0.478 | 0.491 | 0.62 / 0.53 / 0.29 | 0.317 |
| EW_DAILY | 0.468 | 0.444 | 0.53 / 0.49 / 0.39 | 0.321 |
| MOM_SS25 | 0.458 | 0.430 | 0.57 / 0.52 / 0.28 | 0.321 |
| TREND_2 | 0.449 | 0.423 | 0.62 / 0.51 / 0.22 | 0.312 |
| CASH | 0.372 | 0.326 | 0.75 / 0.31 / 0.05 | −0.002 |

- **Eligibility.** Every candidate passes the hard gates (G1, G4, G5).
- **Report-only gate failures:**
  - baitoey_rot_max: G2, G3, both G6 forms (worst R −48%);
  - G6_median only: mr_bbrsi, mr_4h, switch_rmax_mr, switch3.
- **Guard reliance.** Guard-only days exceed 25% of active days (the G1 flag) for vt_mom (48%), switch_vt_tl (37%), rot_max (69%), switch_rot_mr (30%), switch_rmax_tl (48%) and switch_rmax_mr (37%).
- Full columns are in `results/scoring/leaderboard.md`: tail, turnover, fees, replay.

## 4. Moves of 3 or more places vs the old REL ranking (among the 13 candidates scored in both versions)

| Model | Old → new rank | Why |
|---|---|---|
| baitoey_vt_mom | #6 → #1 | It clears the cut most often: 0.65 / 0.62 / 0.55, the highest STRICT HIT of all. REL weighted a few high-ratio windows more |
| baitoey_rot_max | #7 → #3 | It was not eligible on G2, G3 and G6, which are now report-only. Fully invested rotation clears the bars in up markets (UP 0.69) |
| baitoey_mr_bbrsi | #10 → #4 | Low exposure clears LENIENT in falling markets (0.75 overall, DOWN 0.46). It is in the tie group, but has the lowest CS_HIT there (0.150) |
| pol_switch_rot_mr | #9 → #5 | Steady HITs (0.58 / 0.54 / 0.43) |
| pol_switch_rmax_tl | #2 → #6 | Fewer windows clear the bars (0.54 / 0.51 / 0.43); its REL came from high composites in the windows it did clear |
| baitoey_mr_4h | #1 → #9 | Its REL came from very high ratios in calm windows; it clears STRICT in only 29% of the weight. Without the post-holdout windows it is tied with the top and wins on CS_HIT (0.391) |
| pol_trend_ls | #4 → #12 | It misses in rising markets (UP 0.37), where it is often flat or short, and up windows carry 54% of the weight |

## 5. The pick, and the pre-registered launch pick

- **Full pool:**
  - Top = baitoey_vt_mom. Its tie group is vt_mom, pol_switch_vt_tl, rot_max and mr_bbrsi.
  - CS_HIT: vt_mom 0.368, switch_vt_tl 0.366. These are within 0.05, so step 4 decides: min(SCREEN, CONFIRM) **1.03 vs 0.99 → `baitoey_vt_mom`**.
  - pol_switch_vt_tl (the pre-registered launch pick) is second. The pick differs from it by a thin margin: a 0.04 gap on Pol's period measure, after a 0.002 gap on CS_HIT.
- **Without the post-holdout windows:**
  - Top by HEADLINE_RET = baitoey_vt_mom (0.556). Its tie group is wide, 7 models: vt_mom, rot_max (0.509), mr_4h (0.475), mr_bbrsi, switch_vt_tl, mom_ss and switch_rmax_tl.
  - CS_HIT: mr_4h 0.391 is more than 0.05 ahead of vt_mom (0.316), so the pick is **`baitoey_mr_4h`**.
- **The two pools disagree.** The 52 post-holdout windows (a rising market) move HEADLINE_RET by up to 0.09 (pol_switch_vt_tl 0.456 → 0.548).
- **No live setting was changed.** `live.model` is untouched; the launch choice stays with the team.

## 6. UNVERIFIED and limits

- **LENIENT in UP windows (0%) is an assumption.** No field data exists for rising markets.
- **The replay ranks differ from Pol's table.** Example: pol_switch_vt_tl +0.1% (#10 / #7) in Round 1 here, against −2.64% (#29 / #27) in Pol's. The engine now makes the first decision at the window start, as live, where Pol's run chained decisions from 3 days earlier. Which matches the real bot better is UNVERIFIED until the live bot's first hours are seen.
- **The guard carries a large share of active days for several top models (37–69%).** They pass G1 because of the daily guard trade. If the organizers do not count the 0.2% keep-alive trade as a strategy trade, that matters. Book confirmed that one trade per day counts; that is not verified with the organizers in writing.
- **The lookalike weights are preliminary.** The Oct 4 rerun changes them, and so the tool version and possibly the pick.
- **The tie test samples calendar months (about 76 in the pool).** The groups are wide; read them as "not separable", not as equal.
- **Older-branch scoring.** A run from a branch without this code registers an older tool version and rewrites `results/scoring/leaderboard.md` in the old format. Teammates should score from this branch until it merges.
