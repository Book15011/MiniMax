# Pre-registration: book_orch, a daily base with an ML weight adjustment, a shock rule and a short sleeve (2026-10-03, Book)

| | |
|---|---|
| Branch | `feature/book-orch` (`.worktrees/book-book-orch`), on `feature/realtest` `f9bbc15`, plus two recorded local merges (approved): `d9aa8a8` = `feature/v2check` at `9c3bbf3` (Pol's `pol_abl_shock`; it stacks on `feature/return-first` and `feature/volume`), and `4dc473d` = `feature/book-batch4` at `4dbd7db` (`src/models/book/_trend.py`) |
| Scoring tool | return-first, tool version `3036a0d8bfdaa6a0` (unchanged by the merges; checked) |
| Committed | alone, before any code, training or scoring of book_orch |
| After this commit | **no default changes.** Any change is reported as a DEVIATION. The layer switches of the one registered run are set by the keep rule in section 5, never by hand |
| Not changed | any teammate's file, the engine, the live runner and its config |

## 1. Why: refinements to the team's orchestrator plan

| # | Refinement |
|---|---|
| a | **Partial movement (layer C) is dropped from the main design.** Partial trading is optimal when costs grow with trade size (market impact). Our costs are a flat percentage on small orders, for which the optimal policy is a no-trade band; the cost filter provides one. Partial moves also add lag at market turns. Kept only as the report-only version P |
| b | **The cost filter gates only the ML adjustment,** never the base's own rebalances. Realistic forecasts are small, so gating the base would freeze it |
| c | **ML acts only at the base's daily decision (16:00 UTC),** with 1-day and 3-day forecasts. Hourly ML is deferred: at 10 bps fees, simple hourly trading fails after costs in recent evidence, and hourly adjustments would break the base's exact view of its holdings. The shock rule runs hourly |
| d | **Layers are tested side by side against the base,** then combined, so each effect can be attributed |
| e | **Activity (layer G) is reporting only.** One trade per day counts (organizers, `docs/EVALUATION.md`), and the engine's daily guard exists. Guard-only days are reported; there is no new code |
| f | **Limit-order execution (layer E) cannot be validated** until the test wallet is funded. It is the report-only cost scenario C-maker, labelled UNVERIFIED |
| g | **The holdout is spent.** Overfitting protection comes from walk-forward training, this pre-registration, and the shadow parity check (Phase C) |

**Context, recorded on the team's request:**
- `pol_abl_partial` (half-way moves on vt_mom) scored HEADLINE_RET 0.567 against 0.609 for its base. That supports dropping partial movement.
- The maker-fee upper bound (every trade filled as a maker at the touch) is **+0.016** HEADLINE_RET on vt_mom (Pol, `results/pol/20261002-v2check/e_maker.py`).
- Pol's simple hourly regression (ridge, walk-forward) reached a pooled IC of **+0.0195 at 72 h**, below the gate. Our ML gate stays at 0.02 as written.

**The base: `baitoey_vt_mom` (default, configurable).**
- It is the strongest daily model on the return-first score so far: 0.609, #1 in the PART 8 report, `reports/review/20261002-return-first.md`.
- It is the same base as `pol_abl_shock`, so the comparison is like for like.
- It reads only which coins are held (ROT_EW's keep-while-ranked rule: coins with a positive previous weight), so the held-coin rule keeps it exact.

## 2. What was reused, and the DEVIATIONS decided before building

| Item | Decision |
|---|---|
| Shock trigger | **Imported, not copied:** `ShockOverride.shocked` from `src/models/pol/pol_abl_shock.py`. It fires while BTC's 4-hour return has been −5% or worse at any hour of the last 24 h (`shock_4h` 0.05, `cooldown_hours` 24), checked every hour. **DEVIATION from 3.3 of the task** (−3σ trigger, held until the next 16:00 decision) |
| Shock response | While the trigger is active, long weights are scaled to 50%; shorts are unchanged; held coins never change. **DEVIATION from Pol's response** (cash). Pol's cash response is scored as the report-only version S-cash |
| Hold between decisions | The model returns its held weights drifted by the last hour's returns, with the engine's own drift formula: w_i ← w_i (1 + r_i) / (1 + Σ_j w_j r_j), where r is the last hourly close-to-close return from the view (0 if a close is missing). The engine and the live runner are not changed |
| Dispersion | Computed in book_orch's own feature code: `_trend.py` has breadth but no dispersion function |
| scikit-learn | Not in the shared venv. Installed **without touching it**: pinned wheels (scikit-learn 1.6.1, scipy 1.15.3, joblib 1.5.1, threadpoolctl 3.6.0, `--no-deps`) in `results/book/20261003-book-orch/pylib`, used through `PYTHONPATH`. numpy 2.2.6 and pandas 2.3.3 stay the shared ones. book_orch imports scikit-learn only when it loads its ML models, so the registry and the shared test suite work without it (the ML tests skip there) |

## 3. Design: model `book_orch`

### 3.1 Base handling
- **Hourly model.** `rebalance_hours` 1, band = the base's (0.05), `uses_shorts` True (only the sleeve, layer X, can short).
- **When the base is called.**
  - At its own decision times only: 16:00 UTC (`decision_hour_utc`).
  - Also at any hour where book_orch holds nothing: the window's first hour, as the live bot's first decision, or after the base itself chose cash.
- **What the base sees.** book_orch's current holdings, as its previous holdings (the "option 2" rule). vt_mom reads only which coins have a positive weight.
- **No layer changes which coins are held long.**
  - The ML adjustment and the shock only scale the weights of coins the base holds: never to zero, never adding a coin.
  - The sleeve (X) holds only negative weights, in coins the base does not hold.
- **Between decisions:** hold, as in section 2.
- **Parity tolerance for "every layer off = the base"** (version A against the registered `baitoey_vt_mom` run, same tool):
  - |HEADLINE_RET difference| ≤ 0.003, **and** median absolute per-window R difference ≤ 0.02 percentage points.
  - The number of extra drift-band trades is reported.
  - **If the tolerance is exceeded: STOP and report** before any other version is scored.

### 3.2 ML adjustment, layer T (at 16:00 UTC decisions only; not at a window's first hour)

**Forecasts**
- One model pooled across coins, walk-forward, for each horizon: `HistGradientBoostingRegressor(max_depth=3, learning_rate=0.05, max_iter=200, min_samples_leaf=200, l2_regularization=1.0, random_state=0, early_stopping=False)`. `early_stopping=False` makes it run all 200 iterations, as specified, and keeps it deterministic. Trained single-threaded (`OMP_NUM_THREADS=1`).
- **Targets:** each coin's forward return over 1 day (mu1) and over 3 days (mu3), with entry at t + 1 h (the engine's lag). y_H = close(t + 1 h + H) / close(t + 1 h) − 1, taking the last close at or before each time.
- **Rows:** every coin of the day's universe (point-in-time top 30, cut to Roostoo) at every 16:00 UTC decision from 2020-06-01. A row is dropped if its label or a feature is missing.
- **Walk-forward:**
  - retrained monthly, at 00:00 UTC on the 1st of each month;
  - expanding window;
  - purged: a training row needs t + 1 h + H ≤ the retrain time;
  - the first model at the first month start ≥ the first row + 365 days (2021-06-01). Before that there is no adjustment;
  - a decision at t uses the latest model retrained at or before t.
- **Features**, from the view's hourly close and quote volume only, looked up by timestamp (the last close at or before each time, at most 24 h old):
  - the coin's returns over 1, 3, 7, 14 and 30 days;
  - realized volatility over 1, 7 and 30 days (`_trend.hourly_vol`), and the ratio 7d / 30d;
  - distance from the 30-day high (close / max close over 30 days − 1);
  - volume ratio: quote volume of the last 24 h / (30-day quote volume / 30);
  - BTC's returns over 1, 7 and 30 days;
  - BTC's 7-day volatility percentile: the mid-rank percentile of today's value among its values at t − 24h·k, k = 0..364;
  - breadth (`_trend.breadth` with the `book_trend` parameters);
  - dispersion: the cross-sectional standard deviation of the 7-day returns of `_trend.liquid_universe`;
  - the base's weight in the coin: 0 if not held; in training, the base's own history of decisions.
- **Artifacts:**
  - every fitted model is pickled under `results/book/20261003-book-orch/ml/` (not committed: too large);
  - a manifest (`validation/book_orch_ml_v1.json`, committed) holds each file's sha256, each model's retrain time, rows and q, the feature list, the hyperparameters, the library versions and the engine's half-spreads;
  - the manifest's sha256 is in book_orch's parameters, so the run key changes when the artifacts change;
  - a shuffled-label set (labels shuffled within each calendar month of t, seed 0, the same permutation for y1 and y3) is trained the same way, with its own manifest.

**Adjustment**, for each coin the base holds long with weight b_i > 0:
- z_i = mu3_i / q, where q = the 90th percentile of |mu3| among that model's in-sample predictions on its training rows.
- adj_i = clip(0.5 z_i, −0.5, +0.5), and adj_i = 0 if sign(mu1_i) ≠ sign(mu3_i).
- aim_i = b_i (1 + adj_i), between 0.5 b_i and 1.5 b_i.
- **Cost filter (no-trade band):** coin i moves to aim_i only if |mu3_i| ≥ 2 × round_trip_cost_i, where round_trip_cost_i = 2 × (0.10% + the engine's half-spread for the coin). Otherwise aim_i = b_i.
- **No added exposure:** if Σ aim > Σ b, only the adjusted coins are scaled down, by one factor, so that Σ aim = Σ b. Filtered coins stay exactly at b_i.
- The base's own rebalances are never filtered.

### 3.3 Shock rule, layer S (hourly): section 2
- At a 16:00 decision while active: the new longs × 0.5.
- At any other hour:
  - the trigger turns on (active now, not active one hour earlier, both read from the view): longs × 0.5;
  - it turns off: longs × 2, and if the gross would exceed 1, the longs are scaled down to fit.
- The state comes from the view, never from memory, so the model stays pure. The activation log (episodes, hours, days) is produced from the same rule offline, since a pure model cannot write.
- **S-cash (report-only):** Pol's response. While active the book is cash; afterwards the base decides at the first hour (the book is empty), as `pol_abl_shock` does.

### 3.4 Short sleeve, layer X (16:00 UTC decisions only)
- **Gate:** breadth_t < 0.3 (`_trend.breadth`, `book_trend` parameters).
- **Candidates (ML gate passed):** coins of `_trend.liquid_universe` that the base does not hold long, with mu3_i ≤ −2 × short_round_trip_cost_i, where short_round_trip_cost_i = 0.10% to open + 0.10% to close + 2 × the engine's half-spread. Ranked by mu3, most negative first.
- **Candidates (ML gate failed):** coins with s_i = 0 (`_trend.trend_scores`), ranked by the most negative 30-day return, ties by name.
- **Size:**
  - up to 5 candidates;
  - weights ∝ −1/σ_i (σ_i = `_trend.hourly_vol` over 30 days), scaled so the sleeve totals min(25%, 1 − the long gross after layer T);
  - the base's longs are never reduced to make room.
- **Recomputed every decision.** A short is closed at the next decision where the gate is off or the coin no longer qualifies; closing trades are never filtered. Between decisions it is held (drifted), like the longs.
- **The shock leaves shorts unchanged.**
- **G4 (shorts disabled):** the long-only run clips the sleeve to 0 and must still pass.

### 3.5 Activity
The engine guard is unchanged. Guard-only days are reported.

### 3.6 Order of the layers at a 16:00 decision
base → P (if on) → T → X → S. P is report-only and never combined.

### 3.7 Partial movement, version P (report-only)
- At 16:00 decisions: coins the base keeps or adds move half-way from the held weight to the base's (a new coin enters at 0.5 b_i); coins the base drops exit fully, so the held set stays the base's.
- At a window's first hour, straight to target.

## 4. ML gate and tests (Phase A)

### 4.1 ML GATE
Checked on the walk-forward out-of-sample predictions, all universe rows from 2021-06-01, **before any forecast is used in trading.**
1. Pooled out-of-sample Spearman IC of mu3 ≥ 0.02.
2. IC of mu3 positive in at least 4 of the out-of-sample calendar years (2021 from June, 2022, 2023, 2024, 2025, 2026 to September).
3. Shuffled-label control: the shuffled models' pooled out-of-sample IC of mu3 against the real labels has |IC| < 0.01.

**If any fails:** T is dropped. X uses its no-ML candidates. Phase B continues with S and X.

**Also reported:**
- IC of mu1 and mu3 per year, and on held coins only;
- the filter pass rate: the share of (16:00 decision, held coin) pairs with |mu3| ≥ 2 × round_trip_cost, and the same on all rows.

### 4.2 Tests
1. Every layer off gives the base's targets at every base decision, on synthetic data.
2. The set of coins held long always equals the base's, with T, S and X on.
3. With X on, the base's decisions are identical to those with X off.
4. Adjustment bounds hold (0.5 b to 1.5 b), and gross never exceeds the base's.
5. Cost-filter math is correct on hand-built cases.
6. The shock trigger and response are correct on a hand-built price series.
7. Sleeve sizing (top 5, ∝ −1/σ, min(25%, 1 − long gross)), the gate, and the closing rule.
8. No look-ahead: decisions at t are unchanged when later bars are altered or deleted.
9. Purge: no training row's label ends after its retrain time.
10. Deterministic training: two runs give identical artifact hashes, and the manifest hash in the parameters changes the run key.
11. The full suite passes: with scikit-learn on the path, and without it, where the ML tests skip.

## 5. Phase B: scoring (scratch registry and leaderboard for every version except the one registered run)

All on tool `3036a0d8bfdaa6a0`, with the same windows (2,298 starts at 12:00 UTC; post-holdout included, and every headline also without).

| Version | What | Status |
|---|---|---|
| A | book_orch, every layer off | reference; parity check, section 3.1 |
| S | A + shock (half longs) | layer test |
| S-cash | A + Pol's cash response | report-only |
| T | A + ML adjustment with the cost filter | layer test; only if the ML gate passed |
| T-shuffled | T with the shuffled-label models | control |
| P | A + partial movement | report-only |
| X | A + short sleeve | layer test |
| X-shuffled | X with the shuffled-label models | control; only if the ML gate passed |
| ST | S + T | report-only combination |
| **C** | **every layer whose own version passed its keep rule** (any of S, T, X) | **the ONE registered run**, via `backtest.run --model book_orch --score`, with those layers set in config. If no layer passes, nothing is registered, and the report says so |
| C-maker | C with every long-side fee at the maker rate 0.05% | report-only, UNVERIFIED; if C is empty, ST |

**C-maker is a simplification, decided now:** the engine has one fee per side and cannot tell urgent trades from others without an engine change. So every long-side trade pays 0.05% (shorts keep 0.10%, the spread is still paid), and the run's R_liq is scored against the unchanged taker-fee bars and weights. The share of fees from shock trades is reported, so the urgent part can be bounded.

**Keep rule** (each line PASS / FAIL against A; computed from the per-window outputs):
- **K1:** HEADLINE_RET higher than A's in the full pool, in SCREEN and in CONFIRM.
  - SCREEN: starts 2022-07-01 … 2024-06-30. CONFIRM: 2024-07-01 … 2026-07-25.
  - A period's HEADLINE_RET uses w′ restricted to its windows and renormalized, with no new direction rebalance.
- **K2:** HIT DOWN not lower than A's; HIT UP not lower than A's by more than 0.02. Each is the mean of the three bars' HIT on DOWN or UP windows.
- **K3:** worst 14-day R no more than 2 pp worse than A's.
- **K4:** mean turnover per window at most 1.25 × A's.
- **K5:** the shuffled-label version does not beat A (its HEADLINE_RET ≤ A's). It applies to ML layers only (T, and X with ML candidates); otherwise it is n/a and counts as a pass.
- **K6** (for C): after dropping the 10% of windows (230) where C beats A by the most (R_liq difference), C's HEADLINE_RET on the remaining windows (w′ renormalized) is ≥ A's on the same windows.
- **K7** (for X, and for C if it includes X): median R over the 10 rebound STRESS windows no more than 1 pp worse than A's (squeeze risk).

**Keeping:**
- A layer (S, T, X) is kept only if its own version passes K1–K5, plus K7 for X.
- C is called a **candidate** only if it passes K1–K6, plus K7 if it contains X. It is registered either way, as the record of the combination.

**Report, for each version:**
- HEADLINE_RET (full pool, without post-holdout, SCREEN, CONFIRM); HIT UP / DOWN;
- ALL_PERIOD_RET: HEADLINE_RET with the natural weights w, before the direction rebalance; diagnostic only;
- mean, median and worst R; CS_HIT;
- turnover and fees per window; tactical uplift (w′-weighted mean R_liq − A's) and extra fees vs A;
- filter pass rate; shock activations; guard-only days;
- extra drift-band trades.

**For X, also:**
- sleeve activation days and average sleeve size;
- hit rate of the shorts (a short held from one decision to the next gained, after costs);
- fees paid by the sleeve;
- rebound-window R for A vs X.

## 6. Phase C
Not started until the team says go. It will need Pol's guard fix for hourly models (`149d564`, on `an earlier branch`), which is not merged here.

## 7. The top daily models in the PART 8 report, checked before Phase B

| # | Model | HEADLINE_RET |
|---|---|---|
| 1 | baitoey_vt_mom | 0.609 |
| 2 | pol_switch_vt_tl | 0.548 |
| 3 | baitoey_rot_max | 0.546 |
| 4 | baitoey_mr_bbrsi | 0.499 |
| 5 | pol_switch_rmax_tl | 0.491 |

No eligible daily model is ahead of `baitoey_vt_mom`, so scoring proceeds.
