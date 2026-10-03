# Pre-registration: batch 4, four candidates for the return-first score (2026-10-03, Book, before any scoring)

| | |
|---|---|
| Branch | `feature/book-batch4` (`.worktrees/book-book-batch4`), on `feature/realtest` at `f9bbc15` |
| Committed | alone, before the models are committed and before any run that produces a return |
| Changes after this commit | none to any default below. A rule that proves impossible is built as closely as possible and reported as a **DEVIATION**, with the reason |
| Scoring | PHASE B only: after the return-first rescore is done (its PART 8 report committed on `feature/return-first`, `scripts/lock` free), on that branch's tool |
| Not changed | any existing model, the engine, the scoring code, the live runner; the launch choice (a team decision) |

## 1. The four models and their levers

| Model | Lever | Expected, written before any run |
|---|---|---|
| `book_vt_dual` | lose less in falling markets | HIT DOWN above baitoey_vt_mom's, HIT UP somewhat below |
| `book_coin_trend` | lose less in falling markets | HIT DOWN above baitoey_vt_mom's, HIT UP below |
| `book_vt_breadth` | lose less in falling markets, faster than a 40-day switch | HIT DOWN above baitoey_vt_mom's, HIT UP slightly below |
| `book_vt_top4` | more upside in rallies | HIT UP above baitoey_vt_mom's, HIT DOWN and worst R below |

All four decide daily at 16:00 UTC (`rebalance_hours` 24, the contract maximum). Shared code lives in `src/models/book/_trend.py`; like `src/models/pol/_combo.py`, it is not a registered model (the registry skips modules starting with `_`). Every number is in `config.yaml` under `models:`, in a book section after the baitoey blocks, because the models use the `*baitoey_vt_mom` YAML anchor.

## 2. The shared trend signal (`trend:` block, one anchor for all three models that use it)

For coin i at decision time t, from hourly closes up to t only, looked up by timestamp, never by bar count:

| Item | Definition | Default |
|---|---|---|
| close(x) | the coin's last close at or before x, if it is at most `max_stale_hours` old; otherwise missing | `max_stale_hours: 24` |
| ret_L | close(t) / close(t − L days) − 1 | `lookback_days: [5, 10, 20, 30, 60]` |
| s_i | the share of the **available** lookbacks with ret_L > 0. L is available when close(t − L days) exists. A coin with less than 60 days of history uses only the lookbacks it has; with less than 5 days, or no close(t), s_i = 0. With all five, s_i is one of 0, 0.2, …, 1 | |
| up-trend | s_i ≥ `up_threshold` | `0.6` |
| liquid universe | the `liquid_n` coins of `view.universe` with the highest quote volume over (t − `volume_days`, t]; missing hours count as 0; ties by name | `liquid_n: 20`, `volume_days: 30` |
| breadth_t | share of the liquid universe in an up-trend (0 if it is empty) | |

- `view.universe` is the validation build's point-in-time top-30 by 30-day volume, cut to the Roostoo list. It already leaves out stablecoins (`validation.universe.stablecoins`), PAXG and every tokenized stock (they are not in the pair list). A test checks that no stablecoin or excluded coin ever appears in the saved universe.
- Two choices the task leaves open, fixed here: the share is taken over the available lookbacks (so a young coin can still reach 0.6), and `max_stale_hours` (a 24 h search back keeps the panel's 1–4 h gaps harmless and turns a coin without recent closes off).

## 3. The models

**3.1 `book_vt_dual`: dual momentum.** Method `momentum`, band 0.05 (vt_mom's).
- `baitoey_vt_mom` (from the registry, unchanged, its own config block via the anchor) chooses the coins and weights. A coin is held only while s_i ≥ 0.6, at vt_mom's weight.
- vt_mom does not expose its ranking or scores (`team_rot_ew.rotation_targets` returns only the final weights), so the model cannot refill a slot "with the next-ranked coin at the removed coin's weight".
- **Rule:** book_vt_dual passes vt_mom only the coins it kept as vt_mom's previous holdings.
  - Dropped coins are forgotten, so vt_mom may refill their slots with its next choices.
  - Every choice is then filtered by the up-trend rule (s_i ≥ 0.6). Any slot without an up-trending coin stays in cash.
  - A window start and "everything was dropped" both give vt_mom an empty previous book, and it starts fresh in both cases.
- **DEVIATION** from the task's "give vt_mom its own unscaled previous targets". Why:
  - Under STRATEGY_GUIDE §2 a model is a pure function of its view and its own previous decision. This model's previous decision no longer holds the coins its filter dropped, so vt_mom's own previous holdings cannot be rebuilt exactly.
  - The rule above is exact and pure, cheap, and behaves identically in backtests and live.
  - The only alternative, replaying vt_mom from an empty book over past decisions (as `src/models/pol/_combo.py` does for its sleeves), levels off at about 90% agreement. The reasons were not tested.
- **Evidence (measured before this commit, decisions only, no returns):**
  - Every daily 16:00 UTC decision from 2020-06-01 to 2026-09-29 (2,312) was compared with an IDEAL: vt_mom's true standalone chain, then the filter.
  - The comparison ran on a replay version of this model at several depths. Depth 0 is the rule above.
  - Script and output: `results/book/20261002-batch4/replay_fidelity.py`, `replay_fidelity.out`, `replay_fidelity_deep.out`.

  | Replay depth (decisions) | Decisions equal to IDEAL | …after a decision that dropped a coin (1,246) | vt_mom's previous holdings exactly right |
  |---|---|---|---|
  | 0 (this rule) | 56% | 34% | 35% |
  | 1 | 62% | 42% | 45% |
  | 2 | 67% | 51% | 52% |
  | 4 | 75% | 61% | 62% |
  | 8 | 84% | 76% | 75% |
  | 16 | 88% | 82% | 82% |
  | 32 | 90% | 85% | 85% |

- **Tests:**
  - With every s_i forced to 1 nothing is dropped, so the model equals vt_mom decision for decision.
  - After a day that drops a coin, the next decision equals vt_mom(view, previous = the kept coins only) followed by the filter.

**3.2 `book_coin_trend`: per-coin trend bots plus a manager.** Method `trend`, band 0.05, `uses_shorts: False`.
- Universe: the liquid universe of section 2.
- raw_i = s_i / sigma_i, sigma_i = the sample standard deviation (ddof 1) of the coin's hourly returns over (t − `vol_days`, t] on the clock-hour grid (a return across a missing hour is missing). `vol_days: 30`.
- w_i = raw_i / Σ_j (1 / sigma_j), sum over the liquid universe. Fully invested (inverse-volatility weights) only when every coin has s_i = 1.
- Cap each coin at `max_weight: 0.25`; the excess stays in cash. Gross ≤ 1 by construction.
- A coin without a usable sigma (fewer than 2 hourly returns, or 0) gets no weight and is left out of the sum.
- **Variant 3.2b (scratch only, never registered):** `shorts: true` with `uses_shorts` set for that run. While breadth < `short_breadth: 0.3`, a coin with s_i = 0 gets w_i = −`short_scale` / sigma_i / Σ_j (1 / sigma_j), `short_scale: 0.5`, capped at −0.25. Gross ≤ 1.

**3.3 `book_vt_breadth`: breadth-scaled exposure.** Method `momentum`, band 0.05.
- vt_mom's weights times e_t = clip(breadth_t / `full_breadth`, `min_exposure`, 1), rounded half up to the nearest `exposure_step`. `full_breadth: 0.6`, `min_exposure: 0.25`, `exposure_step: 0.25`.
- **vt_mom's previous targets:** this model's own previous targets are passed as they are. They hold exactly vt_mom's previous coins (scaling by e ≥ 0.25 never changes that set), and vt_mom reads only that set. This replaces the literal "unscaled weights": dividing back by the previous e would need the previous decision's time, and the return-first engine adds a 12:00 UTC decision at each window start. A test checks that vt_mom's decision is the same for any positive scaling of its previous weights, and that with e forced to 1 the model equals vt_mom decision for decision.

**3.4 `book_vt_top4`: concentration.** Method `momentum`, band 0.05.
- **Version built:** vt_mom's own parameter `k`. The config block is vt_mom's block (YAML merge of the anchor) with `k: 4`. The model class calls `baitoey_vt_mom`'s `targets()` from the registry under that block: no subclass, no copied code. A test checks that with `k: 6` it equals vt_mom decision for decision.
- **Variant (scratch only, never registered):** `k: 3`.

## 4. Tests (PHASE A, `tests/test_book_batch4.py`)

- **Signal:**
  - hand-checked s_i for 3 coins on 3 dates;
  - fewer than 5 days of history, and no recent close, give 0;
  - lookups by timestamp: deleting whole bars elsewhere changes nothing; a gap at a lookback point uses the last close before it, or makes it unavailable beyond 24 h;
  - s, breadth, the liquid universe and sigma are unchanged when bars after t are altered or deleted;
  - the exposure rounding table.
- **Identities:**
  - book_vt_dual with every s = 1, book_vt_breadth with e = 1 and book_vt_top4 with k = 6 each equal vt_mom;
  - book_vt_dual after a day that drops a coin: the next decision equals vt_mom with only the kept coins as its previous holdings, then the filter;
  - vt_mom ignores the scale of its previous weights.
- **book_coin_trend:**
  - weights ≥ 0, sum ≤ 1, each ≤ 0.25;
  - all zero when every s = 0;
  - inverse-volatility proportions when every s = 1;
  - the variant shorts only when the market is broken.
- **Every model:**
  - the contract on a decision sequence;
  - decisions reproduce;
  - the leakage gate passes (future noise, no I/O).
- **Settings:** they come from `config.yaml` and equal the defaults above.
- **Suite:** the full suite passes.

PHASE A also reports a sanity run of each model on 20 windows (a light scratch job, nothing registered).

## 5. PHASE B: scoring and the selection rule

**5.1 Runs**
- The PHASE A commits move onto the tip of `feature/return-first`. They only add files, apart from the book block appended to `config.yaml`.
- Each of the four models gets one registered full run, inside `scripts/lock`, with the scoring command documented on that branch.
- The variants (3.2b, top-3) go through the verified scratch path only, never registered. They are reported, never candidates.

**5.2 Baselines,** from the new leaderboard: `baitoey_vt_mom` (VT), `pol_switch_vt_tl` (SW), `team_cash`.

**5.3 Selection rule.** Every line is reported as PASS/FAIL per model.
- **R1:** eligible under the new score's hard gates G1, G4 and G5.
- **R2:** HEADLINE_RET higher than both VT's and SW's.
- **R3:** HEADLINE_RET higher than VT's in both SCREEN (window starts 2022-07-01 … 2024-06-30) and CONFIRM (2024-07-01 … 2026-07-25).
- **R4:** worst 14-day R (plain R) no more than 5 percentage points below VT's.

Definitions:
- R2 and R4 use the new score's primary pool: `scoring.include_spent_holdout` as committed by the rescore, which the return-first pre-registration sets to true. The numbers without the post-holdout windows are reported alongside.
- In R3, HEADLINE_RET on a period follows return-first's rule for a sub-pool: weights renormalized over the period's windows, recency age from the period's latest start, pi_up = the period's own unweighted UP share. If the tool reports period numbers under another rule, both are shown, and R3 uses this one.

Outcome:
- A model that passes R1–R4 is a **CANDIDATE**.
  - It is **clear** if the paired bootstrap 90% interval of HEADLINE_RET(model) − HEADLINE_RET(VT) excludes 0. This is the new tool's calendar-month block bootstrap: 2,000 draws, seed 20261002, the same draws for every model. Otherwise it is a **tie**.
- Candidates are ranked by HEADLINE_RET, then by CS_HIT. No model is declared a winner any other way. The launch choice stays a team decision.
- STRATEGY_GUIDE §5 (the per-method comparison) admitted models registered by Oct 1, 20:00 HKT. These four come later, so they are outside that comparison. This rule is separate from it.

**5.4 Reported** for the 4 models, the 2 variants (marked scratch), VT, SW and CASH:
- HEADLINE_RET with and without the post-holdout windows;
- HIT LENIENT / MIDDLE / STRICT, HIT UP / DOWN, and CS_HIT;
- SCREEN and CONFIRM;
- the hard gates, worst R and median max drawdown;
- turnover, average exposure and the guard-only share of active days;
- the bootstrap interval against VT and against SW;
- whether each model pulled its lever (section 1), and at what cost on the other side.
