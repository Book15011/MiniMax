# Pre-registration: book_orch v2, a per-coin forecaster (2/4/8 h) with sizing, staging, forecast longs and forecast shorts (2026-10-03, Book)

| | |
|---|---|
| Branch | `feature/book-orch` (`.worktrees/book-book-orch`) at `183827f`. v1: pre-registration `9f8640d`, reports `71cfb2a` and `183827f` |
| Scoring tool | return-first, tool version `3036a0d8bfdaa6a0` (unchanged) |
| Committed | alone, before any v2 code, feature computation, training or scoring |
| After this commit | **no default changes.** Any change is reported as a DEVIATION. The layer switches of the one registered run are set by the keep rule (section 4), never by hand |
| Not changed | any teammate's file, the engine, the live runner and its config, `data/` |

## 1. Reasons and team decisions

| # | Item |
|---|---|
| a | **Weekly retraining.** Published studies find that retraining frequency barely changes forecast accuracy, so the models are retrained weekly, not hourly or daily |
| b | **A long model and a short model, averaged.** Under drift, recent training windows keep errors stable but add noise; an expanding, age-weighted model (L) and a 180-day model (S) are averaged 50/50 |
| c | **A stricter gate for ML shorts.** v1's no-ML short sleeve failed (46.4% of its shorts won after costs; −3.0 pp in the rebound windows). ML shorts are used only if the confident-FALL class itself clears a cost bar (G-d-short) |
| d | **Coin-relative features** (team request, added before any training). The gate tests ranking coins against each other; these give the model relative strength directly |
| e | **Funding rates: skipped.** A point-in-time archive exists (`data/external/binance_futures_ext/fundingRate`: 54 of the 58 coins ever in the universe, monthly files), but it has no October file, and Binance's live API is blocked on this server, so live and shadow forecasts could not compute the feature. Training on a feature that is missing or stale live would make the backtest unrepresentative. A possible v3 feature, only if EC2 can fetch it live (UNVERIFIED) |
| f | **Band 0.015 for every v2 version** (team decision, 2026-10-03). The engine and the live planner trade a coin only when \|target − current\| > `spec.band`. At vt_mom's 0.05, FS's 2% and 5% shorts could never open, F's resizes would rarely trade, and E's half entries would trade only for coins above 10% (vt_mom often holds 7% per coin). 0.015 is below the smallest designed trade (2%). Version A is re-scored at 0.015 as **A′**, the reference of every keep rule; v1's A (band 0.05, equal to `baitoey_vt_mom` within tolerance) is reported alongside |
| g | **The model stays pure.** A model has no memory: its state between hours is only the view and its own previous targets (`src/contracts.py`). Every layer below is therefore written as a rule on those two; section 3.0 states the consequences |
| h | **Not tuned, now or later in this task:** the +0.15 / +0.25 confidence margins, the 50/50 L/S average and the classifier (no regression model, no neural network, no per-coin models, no hyperparameter search). The diagnostics B1–B4 are report-only; nothing is tuned on them |
| i | **v1's layers are removed from `book_orch`** (T, S, X, P). They are recorded at `183827f` and in its reports. The base handling (option 2) and the hold between decisions (option 1) are kept |

## 2. Forecaster (Phase 1)

### 2.1 Universe
At each hour t: `_trend.liquid_universe` on the view at t (the `book_trend` block: the 20 coins of the point-in-time universe with the most quote volume over (t − 30 d, t], ties by name). Forecasts exist only for these coins at that hour. A base coin outside them has no forecast (section 3).

### 2.2 Labels
For coin i, hour t and horizon h ∈ {2, 4, 8} hours:
- entry e = t + 1 h (the engine's one-bar lag); r_h = close(e + h) / close(e) − 1, from the bars stamped exactly e and e + h. A row whose entry or exit bar is missing (a data gap) is dropped.
- c_i = 2 × (0.10% + hs_i): the round-trip taker cost. hs_i = the engine's half-spread (`Market.half_spread`: the Roostoo snapshot `ticker_20260928T174533Z.json`; 5 bps for coins missing from it).
- class = RISE if r_h > c_i, FALL if r_h < −c_i, else FLAT.
- The label is known at e + h (used by the purge).

### 2.3 Features
As of t, from the view's hourly close and quote volume only, on the clock-hour grid. close(x) = the last close at or before x, at most 24 h old (`book_trend.max_stale_hours`), else missing. Hourly returns across a missing hour are missing. Missing values stay missing (the classifier handles them).

| Group | Features |
|---|---|
| Coin returns | close(t) / close(t − L) − 1 for L = 1, 2, 4, 8, 24 h and 3, 7, 14 d |
| Coin volatility | sample std of hourly returns over (t − L, t] for L = 24 h, 7 d, 30 d (`_trend.hourly_vol`, at least 2 returns); ratio 24 h / 30 d |
| Distance | close(t) / max of the closes in (t − 24 h, t] − 1; close(t) / min of the same − 1; close(t) / max of the closes in (t − 7 d, t] − 1 |
| Volume | qv(t) / mean qv over (t − 24 h, t]; qv over (t − 24 h, t] / (qv over (t − 30 d, t] / 30). Missing volume counts as 0 |
| Calendar | hour of day (UTC), day of week (0 = Monday) |
| Beta | 30-day beta to BTC: cov / var of hourly returns over (t − 30 d, t], pairwise complete, at least 48 pairs |
| **Coin-relative (1.d)** | coin return − BTC return over 1 h, 4 h, 24 h, 7 d; coin return − the liquid universe's mean return (coins with that return) over 1 h, 4 h, 24 h, 7 d; coin 7-day volatility / BTC 7-day volatility; coin 24-hour quote volume / the cross-sectional median of the same over the liquid universe |
| Market | BTC returns over 1 h, 4 h, 24 h, 7 d; BTC 7-day volatility percentile (mid-rank of its value at t among its values at t − 24 h × k, k = 0…364, as in v1); breadth (`_trend.breadth`); dispersion (cross-sectional std, ddof 1, of the 7-day returns of the liquid universe, as in v1) |

37 features. No funding (1.e), no other external data.

### 2.4 Models
- **Classifier**, one per horizon, pooled across coins: `HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, max_iter=200, min_samples_leaf=500, l2_regularization=1.0, random_state=0, early_stopping=False)`, classes FALL / FLAT / RISE. `early_stopping=False` makes every fit run the specified 200 iterations without a random validation split. Each fit is single-threaded (`OMP_NUM_THREADS=1`); up to 8 fits run in parallel processes under `nice -n 10` and `scripts/lock`.
- **Training rows:** hours with t.hour ∈ {0, 4, 8, 12, 16, 20} UTC (every 4th hour, on the 16:00 grid), the liquid coins at t, with a label.
- **Retrain times T:** every Monday 16:00 UTC (the first 16:00 UTC decision of each ISO week). The first is the first Monday 16:00 with at least 365 days of rows: rows start with the universe on 2020-06-01 16:00, so **T₁ = 2021-06-07 16:00**; the last is 2026-09-28 16:00. 278 retrains.
- **Purge:** a row trains a model only if its label is known before the retrain time: e + h < T.
- **L:** all purged rows, sample weight 0.5^(age / 365 d), age = T − t.
- **S:** purged rows with t > T − 180 d, unweighted.
- **Forecast:** P = ½ (P_L + P_S) for each class.
- **Predictions:** every hour t in [T, next T), each liquid coin at t, from the models of T. Out of sample by construction. From 2021-06-07 16:00 to the panel's last hour, 2026-09-30 00:00.
- **Base rates:** p̄_k,h(T) = ½ (L's weighted share of class k + S's share), per horizon. p̄_RISE and p̄_FALL = their means over the three horizons.
- **Expected 8-hour return** (for F's cost filter and FS): E8 = ½ (E_L + E_S), with E_M = σ8_i × Σ_k P_M,k × μ̃_M,k. σ8_i = the coin's 30-day hourly volatility × √8; μ̃_M,k = the mean of r_8 / σ8 over model M's training rows of class k (weighted for L). A missing σ makes E8 missing, and then no discretionary trade is made on the coin.
- **Compute budget:** one fit (the largest L) is timed first and the total is estimated for all three label sets below. **If it exceeds 8 hours of wall-clock time, retraining becomes every 2 weeks (a DEVIATION).**
- **Label sets:**
  - `real`;
  - `shuffled`: labels (r and class of all three horizons together, by row) permuted across all training rows of the whole period, numpy `default_rng(0)`; the purge uses each row's own times;
  - `shuffled_hour`: labels permuted across coins within each hour, `default_rng(0)`.
- **Artifacts:** `results/book/20261003-book-orch-v2/ml/<label set>/` (not committed): forecasts as parquet, and the pickled models of `real`. The manifest `validation/book_orch_v2_forecasts.json` (committed) holds the sha256 of every file, the retrain times, row counts, base rates, μ̃, the feature list, the hyperparameters, the library versions and the half-spreads. Its sha256 is in book_orch's parameters, so the run key changes when the forecasts change. scikit-learn comes from v1's `--no-deps` install in `results/book/20261003-book-orch/pylib` (1.6.1); the shared venv is not touched.

### 2.5 Combined signal
- q = mean over the three horizons of P_h(RISE) − P_h(FALL).
- P̄(RISE), P̄(FALL) = means over the three horizons.
- **Confident RISE:** P̄(RISE) ≥ p̄_RISE + 0.15. **Confident FALL:** P̄(FALL) ≥ p̄_FALL + 0.15. **Strong FALL** (FS's 5% size): P̄(FALL) ≥ p̄_FALL + 0.25.

### 2.6 Skill gate
All on the out-of-sample forecast rows with a label, from 2021-06-07 16:00. Each statistic is reported per horizon and for q.

| | Rule |
|---|---|
| **G-a** | For each h, the mean multi-class log loss (natural log, probabilities clipped at 1e-15) of P_h is lower than that of the base-rate predictor p̄_h(T) on the same rows. **Pass if lower at all three horizons** |
| **G-b** | IC_t = Spearman correlation across coins at hour t of q with r_8, for hours with at least 10 coins. **Pass if the mean over hours is ≥ 0.02 AND the yearly mean is > 0 in at least 3 of 2023, 2024, 2025, 2026** (2026 to September) |
| **G-c** | The `shuffled` models' G-b statistic has **\|IC\| < 0.005**. The `shuffled_hour` models' IC is reported (it keeps market timing and removes coin picking) |
| **G-d-long** | Over confident-RISE rows: mean r_8 ≥ 2 × mean c (round-trip taker cost) |
| **G-d-short** | Over confident-FALL rows: mean r_8 ≤ −2 × mean short round-trip cost (0.10% to open + 0.10% to close + 2 × hs, which equals c) |

- **Long gate** = G-a, G-b, G-c and G-d-long. **Short gate** = G-a, G-b, G-c and G-d-short. With no confident rows, G-d fails.
- Forecasts are used for longs (F) only if the long gate passes, and for shorts (FS) only if the short gate passes.

**Reported, never gates:**
- every statistic for L alone and S alone;
- per coin: IC (Spearman of q with r_8 over the coin's own rows) and the precision of its confident RISE and FALL calls (the share whose 8-hour class was right);
- **B1, q buckets:** every hour with at least 10 coins, the liquid coins are split into 5 equal-count buckets by q. Reported: each bucket's mean r_8 (pooled and per year); the top-minus-bottom spread with a t-stat from daily means; and monotonicity (Spearman between bucket number and bucket mean);
- **B2, calibration:** for RISE, FLAT and FALL, each horizon, and L, S and the combined model: a 10-bin table (predicted probability in steps of 0.1) of count, mean prediction and actual frequency; the multi-class Brier score; the expected calibration error (Σ over bins of the bin share × \|mean prediction − frequency\|);
- **B3, return size by probability:** for P̄(RISE) and P̄(FALL), mean r_8 in each 0.1 bin, and for the +0.15 and +0.25 groups: how many predictions qualify, how often they are right (8-hour class), and their mean r_8;
- **B4, per coin:** B1 (each coin's mean r_8 by the bucket it fell in) and B3, split by coin.

## 3. Decision layers (Phase 2)

### 3.0 Common rules
- **Spec:** `book_orch`, `rebalance_hours` 1, **band 0.015** (1.f), `uses_shorts` True. When FS is off, the scratch runs set `uses_shorts` False, as in v1.
- Every hour the model returns full targets, with gross ≤ 1.
- **Base decisions:** at 16:00 UTC, and at any hour with no long target (a window's first hour, or after the base or the layers left no long position). Then the base runs on the current view, with our current long targets as its previous holdings (option 2; vt_mom reads only which coins have a positive weight).
- **Between base decisions** every coin keeps its previous target exactly, except for the events of the layers below.
- **B′, the base's target between decisions** (needed only by E's top-up and F's entries): the base re-run on the view truncated at the latest 16:00 decision t_d ≤ t (bars up to t_d, padded as the harness pads), with our current long targets as its previous holdings.
  - While the long set is unchanged, B′ equals the 16:00 decision.
  - If F has removed a coin the base kept only by its keep rule (rank 7 to 12), B′ fills that slot from its 16:00 ranking. This follows from option 2.
  - Before a window's first 16:00 decision, B′ uses the previous day's 16:00 data.
- **Layer order:** base → R → E → F → FS.
- **Cost filter:** F's size tilts and FS's openings trade only if the expected 8-hour gain is at least 2 × the round-trip cost (sections 3.3 and 3.4). Risk exits (F's confident-FALL exits, FS's closes) and the base's own trades, which R resizes and E re-times without a forecast, are never filtered.
- **No forecast** for a coin (outside the liquid 20, or before T₁): F and FS do nothing to it.
- **A′** = every layer off, at band 0.015.

### 3.1 R, equal-risk sizing (no ML)
At each base decision, within the base's coins: w_i = G × (1/σ_i) / Σ_j (1/σ_j), where σ = 30-day hourly volatility (`_trend.hourly_vol`) and G = the base's gross. A coin with missing σ keeps its base weight, and the others share the rest. Held between decisions.

### 3.2 E, confidence-staged entries (no ML)
With L = the targets after the base (and R):
- At a base decision:
  - a coin held long before: L_i;
  - a new coin with s_i = 1 (`_trend.trend_scores`, `book_trend`) and 30-day volatility below the median of L's coins: L_i;
  - any other new coin: 0.5 L_i;
  - coins not in L: 0 (exits are immediate).
- **Top-up** at 00:00 UTC (8 hours after the 16:00 decision): a held coin whose target is half its full target as of t_d (recomputed through B′ and the layers; \|target − 0.5 full\| ≤ 1e-9 × full) moves to its full target if it is in B′ and not broken down. Broken down = vt_mom's early-exit signal (`breakdown_blocked` from baitoey's volume signals, vt_mom's parameters, on the view at t). Otherwise it stays at half until the next decision.
- Coins staged at a decision other than 16:00 (a window's first hour) are completed at the next 16:00 decision, where they are held coins.

### 3.3 F, forecast longs (only if the long gate passed)
- **At a base decision**, for each coin of L:
  - confident FALL: 0 (a held coin exits; a new coin waits);
  - otherwise multiplier m_i = clip(1 + q_i, 0.5, 1.5), applied only if (m_i > 1 and E8_i ≥ 2 c_i) or (m_i < 1 and E8_i ≤ −2 c_i); else m_i = 1. Target = L_i × m_i (× 0.5 for a coin E stages);
  - if the sum exceeds the base's gross, the coins with m_i > 1 are scaled down by one common factor so that it equals the base's gross. Coins with m_i ≤ 1 keep their targets.
- **At every other hour:**
  - a held long coin with a confident FALL exits (risk exit, never filtered);
  - a coin of B′ that we do not hold long, with q_i ≥ 0 and no confident FALL, enters at its full target (R-sized if R is on, × m_i by the same rule), cut so that the long gross stays ≤ B′'s gross. This covers coins F exited, new coins that waited, and slots B′ refilled.
- The difference from the task text, forced by 1.g: at a 16:00 decision, a coin F exited earlier counts as new, so it re-enters unless it has a confident FALL, even if q_i < 0. Between decisions the stricter rule (q_i ≥ 0) applies.

### 3.4 FS, forecast shorts (only if the short gate passed)
Every hour, after the longs:
- **Close** a short (risk exit, never filtered) when P̄(FALL) < p̄_FALL, or the coin has no forecast, leaves the universe, or is in the long target.
- **Open** on liquid coins not in the long target and not already short, with a confident FALL and E8 ≤ −2 × the short round-trip cost:
  - ranked by P̄(FALL) − p̄_FALL, highest first, ties by name;
  - size 5% if P̄(FALL) ≥ p̄_FALL + 0.25, else 2%;
  - at most 4 shorts, and total shorts ≤ min(20%, 1 − long gross): only cash the long book isn't using;
  - a short that does not fit is cut to the remaining room if that is above 0.015 (the band), else skipped.
- Existing shorts keep their size; they are never resized up.
- If the long book grows so that the shorts exceed min(20%, 1 − long gross), the weakest shorts (smallest P̄(FALL) − p̄_FALL) are closed first until they fit.

### 3.5 Controls and combination
- **F-shuffled, FS-shuffled:** F and FS with the `shuffled` forecasts.
- **Combined candidate C:** every layer whose own version passes its keep rule.

## 4. Scoring (Phase 2)
- Tool `3036a0d8bfdaa6a0`, the same windows (2,298 starts at 12:00 UTC; post-holdout included, and the headline also without). Every version runs on the scratch registry and leaderboard except the one registered run.
- **Smoke test first:** 20 windows (stride 115), for correctness only: it runs, the gates compute, the trades look sane. Never used for any decision.
- **Versions:** A′, R, E, F, FS, F-shuffled, FS-shuffled, C. F and F-shuffled only if the long gate passed; FS and FS-shuffled only if the short gate passed. Windows before T₁ have no forecasts, so F and FS act as A′ there.
- **ONE registered run:** C, through `backtest.run --model book_orch --score` with its layers switched on in `config.yaml`, if any layer passed. If none passed, nothing is registered, and the report says so.

**Keep rule against A′** (each line PASS / FAIL, from the per-window outputs):

| | Rule |
|---|---|
| K1 | HEADLINE_RET higher than A′'s in the full pool, in SCREEN and in CONFIRM (periods and weights as in v1). Reported with the month-bootstrap label against A′ (the tool's tie test: 90% interval of the difference; above 0 = ahead, containing 0 = tied, below 0 = behind). The label is reported; it is not required for PASS |
| K2 | HIT DOWN not lower than A′'s; HIT UP not lower than A′'s by more than 0.02 |
| K3 | Worst 14-day R no more than 2 pp worse than A′'s |
| K4 | Mean turnover per window at most 1.25 × A′'s |
| K5 | The shuffled control's HEADLINE_RET ≤ A′'s (F and FS; n/a and a pass for R and E) |
| K6 | After dropping the 10% of windows (230) where the version beats A′ by the most (R_liq difference), its HEADLINE_RET on the rest (w′ renormalized) is ≥ A′'s on the same windows |
| K7 | FS, and C if it contains FS: the median R over the 10 rebound STRESS windows is no more than 1 pp worse than A′'s |
| K8 | The share of windows in which a single coin causes more than 40% of the loss is not higher than A′'s |

- **K8 in detail:** each coin's contribution to a window = Σ over hours of equity × weight × the coin's hourly return, minus the fees and spread of its trades, as a fraction of E₀ (reconstructed from the trade log and hourly closes; it must add up to the window's R). A window counts when R < 0 and its worst coin's loss exceeds 40% of the sum of the losses of all coins that lost. The share is over all scored windows, unweighted.
- **A layer is kept** if its version passes K1–K6 and K8, plus K7 for FS. **C is a candidate** if it passes K1–K8 (K7 if it contains FS); it is registered either way.

**Reported for every version:** HEADLINE_RET (full, without post-holdout, SCREEN, CONFIRM); HIT UP / DOWN; mean, median and worst R; turnover; fees; the shorts' win rate (a short from its open to its close gained after costs); median R over the rebound windows; the K8 share; guard-only days; trades between decisions. Also v1's A (band 0.05) as a second reference.

## 5. Per-coin analysis (Phase 3)
1. **Attribution, for A′ and C** (if C is empty, for A′ and the scored layer version with the highest HEADLINE_RET):
   - per coin, and per volatility tercile (coins split into three groups by their median 30-day volatility over the scored period): P&L share, entries, win rate (positions closed with a gain after costs), average holding hours, and the contribution in UP and in DOWN windows;
   - how often one coin caused more than 40% of a window's loss (K8).
2. **Forecast skill per coin:** IC and the precision of confident RISE and FALL calls (section 2.6). A coin is called predictable if its IC is > 0 with t ≥ 2 (from daily means); this is descriptive only.
3. **Launch-time coin cards** for the liquid universe at the latest complete hour in the panel (2026-09-30 00:00 UTC; `data/` is read-only, so it is not refreshed, and the cards are UNVERIFIED as a launch-hour view):
   - P(RISE / FLAT / FALL) per horizon, q, the confidence flags, 30-day volatility, the breakdown flag;
   - the size each coin gets under A′, R, E, F and FS from an empty book (the live start);
   - the order in which E and F would buy them: now in full, now at half (then +8 h), waiting.
4. **Shadow log format** (implemented and tested, not started): one record per coin per hour, with coin, hour, signals, probabilities, decision, reason and size, built by a pure function. The runner that would write it is not touched.

## 6. Tests, git and report
**Tests:**
1. Every layer off: the base's targets at its decisions, held unchanged between them (synthetic data).
2. No look-ahead: features at t are unchanged when bars after t are altered or deleted; the stored forecast at sampled hours equals a recomputation from a view truncated at t with that week's models.
3. Purge: no training row's label is known at or after its retrain time; S's window; L's weights.
4. Determinism: two trainings on synthetic data give identical forecasts and model hashes; the manifest hash changes the run key.
5. Labels by hand: costs, classes, gaps dropped.
6. Layers on hand-built cases: R's weights; E's staging, top-up and breakdown block; F's multiplier, filter, exit, re-entry and rescale; FS's sizes, limits, ranking and closing; gross ≤ 1; the base sees our long targets.
7. The full suite passes with scikit-learn on the path and without it (the ML tests skip).

**Git:** this file first, alone; then code, tests, the forecast manifest and the reports. No push, no merge.

**Report:** the gate per horizon and for q with the controls; the table of all versions; K1–K8 for each version; the per-coin tables and launch cards; the compute time; a one-line recommendation, with anything uncertain marked UNVERIFIED. Stop before shadow mode.
