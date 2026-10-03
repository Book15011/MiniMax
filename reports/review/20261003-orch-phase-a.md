# book_orch Phase A: ML gate, tests, and the parity STOP (2026-10-03, Book)

Pre-registration `reports/review/20261003-prereg-orch.md` (`9f8640d`). Tool `3036a0d8bfdaa6a0`. Scratch outputs, not committed: `results/book/20261003-book-orch/` (`ml_gate.json`, `parity_A.json`, `diag.py`, `versions/A/`, and the trained models in `ml/`).

**Status: Phase B is STOPPED** at the pre-registered parity check (section 3.1). Only version A was scored.

## 1. Pol's `pol_abl_shock`, inspected

| Item | Finding |
|---|---|
| Source | Pol, commits `cc47e09` and `1df1dd7`, on `feature/v2check` (merged here as `d9aa8a8`) |
| Layers implemented | A, base `baitoey_vt_mom`; F, shock. C is a separate model, `pol_abl_partial`. B, D, E and G are not implemented |
| Trigger | BTC's 4-hour return is −5% or worse at any hour of the last 24 h, checked every hour |
| Response | Cash, longs and shorts. Afterwards the base decides from an empty book |
| Score (tool `3036a0d8`) | HEADLINE_RET 0.607, 0.555 without the post-holdout windows; worst R −26.8%; vt_mom: 0.609, 0.556, −30.8% |
| Pure? | Yes; G5 passes |
| Reused here | The trigger only, by import (`ShockOverride.shocked`) |

**For Pol (not fixed here):**
- The cached run of `pol_abl_shock` contains 333 trades away from any shock. The engine trades an hourly model back to its stale daily targets whenever a weight drifts past the band, and those trades slightly penalize its score.
- Its 16:00 UTC decision hour is hard-coded (`GRID_HOUR`), not read from config.

## 2. What the base reads from its previous targets

Only which coins are held long (`team_rot_ew.rotation_targets`: w > 0 and still in the top 12), never the weights. Verified by test: with the sleeve on, the base's calls and outputs are identical.

## 3. ML gate: FAIL (pre-registered rule: T is dropped and X uses its no-ML candidates)

| Check | Value | Needed | Result |
|---|---|---|---|
| Pooled out-of-sample Spearman IC, mu3 | **+0.052** (held coins +0.056) | ≥ 0.02 | pass |
| Years with positive IC, mu3 | **5 of 6** | ≥ 4 | pass |
| Shuffled-label control, IC of mu3 | **+0.023** | \|IC\| < 0.01 | **FAIL** |

**IC by year:**

| Year | IC mu1 | IC mu3 | IC mu3, held coins |
|---|---|---|---|
| 2021 (from July) | −0.040 | +0.066 | +0.067 |
| 2022 | +0.066 | +0.036 | +0.054 |
| 2023 | +0.000 | +0.079 | +0.035 |
| 2024 | +0.056 | +0.057 | +0.059 |
| 2025 | −0.006 | +0.049 | +0.044 |
| 2026 | −0.073 | −0.016 | +0.054 |

- **Pooled IC of mu1:** +0.011.
- **Filter pass rate:** |mu3| ≥ 2 round trips on 75.6% of held coin-decisions (74.2% of all rows).
- **Why the control fails:** shuffling labels within each month keeps every month's average return, so the market-wide features (BTC returns, breadth, dispersion) can still learn the market's direction. A shuffled model reaching IC 0.023 means about half of the pooled IC is market timing, not coin selection.
- **Not run:** T, T-shuffled, ST and X-shuffled.

## 4. Phase A tests

| Test | Result |
|---|---|
| `tests/test_book_orch.py` (11 tests) | pass; without scikit-learn, 10 pass and the training test skips |
| Determinism of the full training, run twice | **identical sha256 for all 126 model files**, and identical q |
| Full suite, scikit-learn on the path | 291 passed |
| Full suite, shared venv | 290 passed, 1 skipped |

## 5. Parity of version A with `baitoey_vt_mom`: FAIL, so STOP

| | A (every layer off) | baitoey_vt_mom (registered) | Tolerance |
|---|---|---|---|
| HEADLINE_RET | 0.5810 | 0.6087 | \|diff\| ≤ 0.003: **0.0277, FAIL** |
| without post-holdout | 0.5560 | 0.5564 | — |
| Median \|per-window R diff\| | | | ≤ 0.02 pp: **0.110 pp, FAIL** (in-sample 0.108, post-holdout 0.227) |
| Windows within 0.02 pp | 12.8% | | |
| Extra drift-band trades | 325, in 220 windows | 0 | reported |
| Turnover; fees / E_0 | 3.56; 0.359% | 3.59; 0.362% | |
| Worst R | −30.80% | −30.84% | |

**Causes, from `diag.py`:**
1. **The guard.** On every UTC day the base run's guard (04:00 UTC) rebalances vt_mom exactly back to its 16:00 targets. With the drift-hold rule, book_orch's guard trades to its drifted weights instead, so its weights keep drifting until the next 16:00 decision. This systematic difference in the daily rebalance accounts for the median gap.
2. **The drift-band trades.** In extreme hours the one-hour lag of the drift estimate exceeds the band. Example: the 2021-01-28 window, R +43.2% against +61.6%.
3. **The headline.** 19–35 window bar results flip, and the 52 post-holdout windows carry 21.6% of w′. Together they move HEADLINE_RET by −0.028. Without the post-holdout windows the two agree within 0.0005.

## 6. DEVIATIONS so far

1. **D1, the adjustment's rescale.** The pre-registered "scale every adjusted coin by one factor" could push a down-tilted coin below 0.5 b, breaking the pre-registered bounds (caught by the bounds test). Implemented as the closest version that keeps both rules: only the upward tilts are shrunk, by one factor. T is not used (gate failed), so this has no effect on any result.
2. **The first model is retrained on 2021-07-01, not 2021-06-01 as the pre-registration's parenthesis said.** The rule ("the first month start ≥ the first row + 365 days") is followed: the first row is 2020-06-01 16:00, plus 365 days is 2021-06-01 16:00, so the first month start after it is 2021-07-01. The parenthesis was a miscalculation.
3. **The sleeve's candidates are `trend`,** by the pre-registered rule for a failed gate.
