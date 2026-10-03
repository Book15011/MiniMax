# Final book_orch steps: macro risk check, "hold longer", logging fixes, batch 4 table (2026-10-03, Book)

| | |
|---|---|
| Pre-registration | `reports/review/20261003-prereg-final-steps.md` (`b49ecb0`), committed before anything in parts 1 and 2 was computed |
| Logging fixes | `4852fb1` (code and tests) |
| Research write-up | `docs/research/book_orch.md` (tests and results only; no model is recommended there) |
| Tool | `3036a0d8bfdaa6a0`. Two scratch scoring runs, nothing registered |
| Scripts and outputs | `results/book/20261003-final-steps/` (not committed): `macro.py`, `macro.json`, `macro_state.parquet`, `run_hold.py`, `score.sh`, `hold.py`, `hold.json`, `versions/H15`, `versions/H18` |
| Not done | writes to `data/` (including `data/harness/`), Roostoo calls, downloads, registration |

This report gives tests and results. Choosing the launch model waits for batch 4's results and the combined test.

| Part | Result |
|---|---|
| 1. Macro risk check | **Rule fails on all three conditions: no macro brake.** Windows starting under macro stress were not worse for vt_mom. They cleared the bars *more* often (HIT 0.746 vs 0.580), and the approximate brake lowers HEADLINE_RET (0.6086 to 0.5996) |
| 2. Hold longer (keep_rank 15) | **Keep rule fails (K1): not registered.** Turnover, fees and quick round trips all fall, but HEADLINE_RET drops from 0.609 to 0.540 (bootstrap: behind). keep_rank 18 (report only) behaves the same way |
| 3. Logging fixes | Done. Universe exits are now logged, and E's stage reasons state the real completion time. 2 tests added; full suite 297 passed |
| 5. Batch 4 Phase B | The committed report exists (`feature/book-batch4`, `551451c`). Its table is in section 5: no batch 4 model passes its selection rule |

## 1. Macro risk check (read-only; vt_mom's windows)

**Inputs.**
- **Windows:** the 2,298 stored windows of version A, which is vt_mom at band 0.05 (equal to the registered vt_mom run within 0.00015 HEADLINE_RET).
- **Macro data:** the pinned FRED snapshot (sha256 checked), with a 1-day lag. DTWEXBGS also gets the team's existing 7-day lag, since it is published weekly.
- **Crypto data:** BTC funding prints from `binance_futures_ext`.
- **Coverage:** all six score components exist at every window start. BTC open interest (report only) covers 2,165 windows, from 2020-09-08 to 2026-08-12. 473 zero rows in the OI files are treated as missing.

**Score.** The macro risk score is the mean of six 365-day percentile ranks, oriented so that high means stress:
- VIX level and VIX 5-day change;
- minus the S&P 20-day return, and the S&P drawdown depth;
- the dollar 20-day change;
- BTC funding (7-day average).

Its range is 0.15 to 0.89, with median 0.46. The top fifth (score ≥ 0.618) has 460 windows: 2020 14, 2021 58, 2022 144, 2023 29, 2024 70, 2025 77, 2026 68.

### 1.1 Rank correlation of the score with each window's result
Values are Spearman correlations, with 90% month-block bootstrap intervals in brackets (2,000 draws, the tool's seed).

| Pool | With R | With LENIENT pass | With MIDDLE pass | With STRICT pass |
|---|---|---|---|---|
| All (2,298) | −0.017 [−0.110, +0.078] | +0.022 [−0.058, +0.100] | +0.016 [−0.066, +0.099] | +0.026 [−0.051, +0.105] |
| 2020 | −0.020 [−0.214, +0.234] | +0.042 [−0.123, +0.239] | +0.066 [−0.112, +0.265] | −0.057 [−0.182, +0.132] |
| 2021 | +0.088 [−0.073, +0.233] | +0.105 [−0.073, +0.275] | +0.107 [−0.066, +0.271] | +0.055 [−0.101, +0.191] |
| 2022 | **+0.217 [+0.027, +0.401]** | +0.165 [+0.001, +0.357] | +0.149 [−0.019, +0.334] | +0.113 [−0.028, +0.262] |
| 2023 | +0.075 [−0.256, +0.363] | +0.072 [−0.191, +0.309] | +0.070 [−0.189, +0.303] | +0.106 [−0.153, +0.329] |
| 2024 | +0.030 [−0.229, +0.290] | +0.004 [−0.172, +0.187] | −0.009 [−0.193, +0.185] | +0.104 [−0.104, +0.305] |
| 2025 | −0.132 [−0.374, +0.121] | −0.021 [−0.248, +0.191] | −0.031 [−0.274, +0.194] | −0.030 [−0.264, +0.181] |
| 2026 | −0.085 [−0.362, +0.239] | +0.016 [−0.182, +0.251] | +0.039 [−0.185, +0.295] | +0.080 [−0.128, +0.322] |

Every pooled interval contains 0. The only interval clear of 0 is 2022's, and there the sign is *positive*: more stress came with better windows.

### 1.2 Top fifth vs the rest
- **HIT** is the tool's definition: the w′-weighted share of windows clearing each bar, with w′ renormalized within the group.
- **t** is the mean-R difference divided by its month-block bootstrap standard deviation.

| Pool | n (top / rest) | Mean R | Median R | Worst R | HIT, mean of three bars | t |
|---|---|---|---|---|---|---|
| **All** | 460 / 1,838 | +2.80% / +3.02% | +2.04% / +1.08% | −26.2% / −30.8% | **0.746 / 0.580** | **−0.13** |
| 2020 | 14 / 200 | +2.14% / +10.31% | +4.63% / +6.09% | −9.9% / −14.4% | 0.521 / 0.528 | −2.02 |
| 2021 | 58 / 307 | +6.92% / +5.40% | +9.04% / +4.48% | −17.6% / −18.9% | 0.535 / 0.512 | +0.63 |
| 2022 | 144 / 221 | −0.42% / −4.07% | −0.37% / −4.81% | −26.2% / −23.8% | 0.717 / 0.302 | +1.96 |
| 2023 | 29 / 336 | +7.74% / +2.50% | +9.45% / +1.17% | −11.6% / −20.9% | 0.742 / 0.466 | +1.11 |
| 2024 | 70 / 296 | +7.06% / +3.33% | +1.20% / +0.90% | −24.7% / −30.8% | 0.506 / 0.463 | +0.54 |
| 2025 | 77 / 288 | −0.05% / +0.54% | +0.20% / −1.34% | −17.2% / −18.1% | 0.516 / 0.455 | −0.19 |
| 2026 | 68 / 190 | +3.01% / +3.95% | +2.87% / +1.99% | −15.3% / −22.4% | 0.814 / 0.747 | −0.29 |

- **Pooled HIT per bar, top / rest:** LENIENT 0.767 / 0.628; MIDDLE 0.755 / 0.596; STRICT 0.716 / 0.516.
- **Unweighted shares** (report only) point the same way: 0.620 / 0.562, 0.585 / 0.529, 0.504 / 0.428.

### 1.3 Approximate brake (R_liq × 0.5 in top-fifth windows)
**APPROXIMATE:** path effects, the brake's own trades and fees, and the guard are ignored. The recomputation with no scaling reproduces A's stored HEADLINE_RET exactly (0.60859).

| | LENIENT | MIDDLE | STRICT | HEADLINE_RET |
|---|---|---|---|---|
| vt_mom (A), stored | 0.652 | 0.623 | 0.550 | **0.6086** |
| With the brake | 0.657 | 0.623 | 0.519 | **0.5996** (−0.009) |

Halving a stress window lifts a few small losses above the LENIENT DOWN bar (−1.5%), but it costs more STRICT passes.

### 1.4 Decision
| Condition | Needed | Result |
|---|---|---|
| D1: pooled mean R lower in the top fifth, t ≤ −2 | t ≤ −2 | −0.22 pp, t −0.13: **fail** |
| D2: lower mean R **and** lower HIT in ≥ 4 of 2020–2026 | 4 years | 1 year (2020): **fail** |
| D3: the approximate brake raises HEADLINE_RET | > 0.6086 | 0.5996: **fail** |

**No macro brake is worth pre-registering. The macro line stops.**

**Report only:** pooled Spearman correlation of each component with R (point estimates, no intervals):

| Component | Spearman with R |
|---|---|
| VIX level | −0.051 |
| VIX 5-day change | −0.084 |
| Minus S&P 20-day return | −0.019 |
| S&P drawdown depth | −0.064 |
| Dollar 20-day change | +0.059 |
| BTC funding | **+0.118** |
| 10-year yield 20-day change | +0.031 |
| BTC OI 7-day change | −0.029 |

**UNVERIFIED:** the top-fifth cutoff is the 80th percentile of the whole sample, which a live rule could not know in advance. It does not matter here because the rule fails anyway.

## 2. "Hold longer": vt_mom keeping coins while in the top 15 (and 18)

**Runs.**
- vt_mom's own `keep_rank` parameter, set by config override: no code change and no subclass.
- Both versions were scored under `scripts/lock book-final-steps-score` with `nice -n 10`, on the scratch registry: H15 in 4.7 minutes, H18 in 5.2.
- The baseline is the registered vt_mom run (`ac38d1af5cdc2e2d`).
- All three share tool version `3036a0d8bfdaa6a0`. The recomputed HEADLINE_RETs match the stored ones.

| | vt_mom (keep 12) | **H15** (keep 15) | H18 (keep 18, report only) |
|---|---|---|---|
| HEADLINE_RET, full | **0.6087** | 0.5396 | 0.5521 |
| without post-holdout | 0.5564 | 0.5433 | 0.5355 |
| SCREEN / CONFIRM | 0.4465 / 0.5844 | 0.4712 / 0.5513 | 0.4763 / 0.5443 |
| HIT UP / DOWN | 0.805 / 0.376 | 0.742 / 0.299 | 0.747 / 0.320 |
| Mean / median / worst R | +2.97% / +1.24% / −30.8% | +2.77% / +1.05% / −30.9% | +2.66% / +1.09% / −29.6% |
| Turnover per window | 3.59 | 3.05 | 2.74 |
| Fees per window (% of E₀); with spread | 0.362%; 0.417% | 0.307%; 0.353% | 0.276%; 0.317% |
| Round trips within 24 h, per window | 1.64 | 1.08 | 0.88 |
| Trades per window | 109.5 | 105.3 | 102.8 |
| CS_HIT | 0.368 | 0.411 | 0.398 |
| Bootstrap vs vt_mom [90%] | — | **behind**: −0.069 [−0.135, −0.000] | behind: −0.057 [−0.104, −0.003] |
| Eligible (hard gates) | yes | yes | yes |
| Run key | `ac38d1af5cdc2e2d` | `da09d8bf369b4e22` | `37096007b00118ee` |

**Keep rule for H15:**
- **K1: FAIL.**
  - Full pool: 0.540 vs 0.609.
  - SCREEN: higher, 0.471 vs 0.447.
  - CONFIRM: lower, 0.551 vs 0.584.
- **K2 (turnover lower): pass.** 3.05 vs 3.59.
- **K3 (worst R no more than 2 pp worse): pass.** −30.87% vs −30.84%.
- **Not kept and not registered.**

**What it shows:**
- Holding longer trades less (−15% turnover, a third fewer quick round trips) but clears the bars less often, in both UP and DOWN windows (HIT UP 0.742 vs 0.805, HIT DOWN 0.299 vs 0.376).
- Most of the gap is in recent windows: without the post-holdout windows, the difference is −0.013; on the full pool it is −0.069.

**Notes.**
- **SCREEN and CONFIRM** here use the v2 keep rule's sub-pool weights (w′ renormalized within the period), as pre-registered. Batch 4's report uses its own sub-pool rule, which gives vt_mom 0.459 / 0.602 (section 5). The decision does not depend on this: K1 already fails on the full pool.
- **The H18 run's code is flagged "dirty".** At that moment the only uncommitted change was part 3's edit to `book_orch.py`, which is not part of vt_mom's code (the run key hashes vt_mom's sources and parameters). H15 ran clean at `b49ecb0`.

## 3. Logging fixes (`4852fb1`)

| Fix | Before | After |
|---|---|---|
| A held coin leaves the point-in-time universe (PUMP 2026-04-11, FIL 2026-04-17) | dropped with no record in `explain()` | `exit` (a short: `close_short`), reason "left the point-in-time universe" |
| E's stage reason, coin staged at the 16:00 decision | "new coin: half now, the rest at 00:00 UTC" | "new coin: half now, the rest at 00:00 UTC (at the next 16:00 UTC decision if it has broken down by then)" |
| E's stage reason, coin staged at any other hour (a window's first hour) | the same 00:00 text (wrong) | "new coin: half now, the rest at the next 16:00 UTC decision" |

**Why two texts.** The read-only checks (A8, 70 staged coins) found that coins staged at 16:00 complete at 00:00 (35), while window-start stages complete at the 16:00 decision (31); 4 exited first. So the fix states the actual time for each case, rather than one time for both. The times are read from config (`decision_hour_utc`, `stage.topup_hours`).

**Tests.**
- `test_E_stage_reason_states_when_the_half_is_completed`: both texts; a window-start stage stays at half until 16:00, then reaches the base's full weight.
- `test_a_held_coin_that_leaves_the_universe_is_logged_as_an_exit`: a long and a short, at the decision and between decisions. The targets equal `targets()`, so the change is logging only, and the shadow log shows `in_universe: false` with size 0.

**Results:**
- `tests/test_book_orch.py`: 17 passed with scikit-learn; 15 passed and 2 skipped without it.
- **Full suite: 297 passed.**

## 4. Research write-up
`docs/research/book_orch.md`. Per the change to this task, it describes the tests and results only: no final conclusion and no model recommendation.

## 5. Batch 4 Phase B results (from `feature/book-batch4`, `551451c`)

The branch has a committed Phase B report: `reports/review/20261003-batch4-results.md` (analysis `results/book/20261003-batch4/phase_b.py`). Its numbers are copied here unchanged.
- **Pool:** the full pool, 2,298 windows.
- **HIT UP and DOWN:** each the mean of the three bars on UP or DOWN windows.
- **SCREEN and CONFIRM:** batch 4's sub-pool rule.
- **Bootstrap:** 90% interval of the HEADLINE_RET difference against VT.
- **Italics:** scratch variants, never candidates.

| Model | HEADLINE_RET | without post-holdout | SCREEN | CONFIRM | HIT UP | **HIT DOWN** | **Worst R** | Turnover | vs VT [90%] | Selection |
|---|---|---|---|---|---|---|---|---|---|---|
| book_vt_dual | 0.532 | 0.474 | 0.372 | 0.527 | 0.683 | 0.353 | −19.9% | 3.32 | −0.077 [−0.110, −0.041] | not a candidate |
| book_coin_trend | 0.353 | 0.300 | 0.342 | 0.283 | 0.516 | 0.159 | −24.1% | 2.09 | −0.256 [−0.352, −0.159] | not a candidate |
| book_vt_breadth | 0.516 | 0.456 | 0.376 | 0.495 | 0.685 | 0.314 | −16.8% | 3.04 | −0.093 [−0.123, −0.063] | not a candidate |
| book_vt_top4 | 0.572 | 0.519 | 0.425 | 0.564 | 0.744 | 0.367 | −30.7% | 3.20 | −0.037 [−0.065, −0.010] | not a candidate |
| *coin_trend with shorts (3.2b)* | *0.341* | *0.281* | *0.328* | *0.268* | *0.467* | *0.192* | *−27.6%* | *2.79* | *−0.268 [−0.366, −0.166]* | *scratch* |
| *top-3* | *0.586* | *0.503* | *0.444* | *0.539* | *0.721* | *0.426* | *−30.0%* | *2.98* | *−0.023 [−0.063, +0.018]* | *scratch* |
| VT, baitoey_vt_mom | 0.609 | 0.556 | 0.459 | 0.602 | 0.805 | 0.376 | −30.8% | 3.59 | — | reference |
| SW, pol_switch_vt_tl | 0.548 | 0.456 | 0.469 | 0.456 | 0.635 | 0.444 | −27.0% | 4.72 | −0.061 [−0.136, +0.005] | reference |

**The batch 4 report's own result:** "Candidates: none. No batch-4 model beats baitoey_vt_mom on HEADLINE_RET, overall or in either period."
- The three exposure-cutting models had better worst windows (−16.8% to −24.1%) but lower HIT DOWN than VT.
- Among all rows, only the top-3 scratch variant (0.426) and SW (0.444) clear the DOWN bars more often than VT.

## 6. Unverified and open
- **UNVERIFIED:** the macro brake numbers are approximate (path ignored), and the top-fifth cutoff uses the whole sample.
- **UNVERIFIED:** DTWEXBGS revisions; the snapshot is the pinned one, not a real-time vintage.
- **Open: the combined test and the launch choice.** They wait for batch 4's results and the combined test, as instructed. Nothing here was registered or merged.
