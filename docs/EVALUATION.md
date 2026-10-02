# Evaluation: the competition-style score

How the team scores every model the same way, as close as we can get to the competition's own scoring. The code is `backtest/scoring/`, on top of the harness in `backtest/` (`docs/STRATEGY_GUIDE.md`). Every constant lives under `scoring:` in `config.yaml`. **Every setting is pending team review** until the checklist at the end is signed off.

- **Status: scoring v2, return first (2026-10-02, `feature/return-first`, pending review).** The primary score is now HEADLINE_RET: how often a model's 14-day return clears the cut, over live-like, direction-balanced windows that start at 12:00 UTC like the round. The definition is the next section. Sections 1–3 describe v1; where v2 changed something, the v2 section says so, and the rest of sections 1–3 still holds. Pre-registration: `reports/review/20261002-prereg-return-first.md`.
- **Score from `feature/return-first` until it merges.** Scoring from an older branch registers an older tool version. The leaderboard keeps those rows only as "previous version", and a run from older code regenerates `results/scoring/leaderboard.md` in the old format until someone scores from this branch again.
- v1 history: tool built, formulas tested, and reviewed by Pol on 2026-10-01 (section 7). Book's and Baitoey's sign-off are still pending.
- **The official formula is unpublished** (organizers: "formulas published on Finale Day"). We know only the outline: top 20 by return per region, then 0.4·Sortino + 0.3·Sharpe + 0.3·Calmar. So the score reports four readings of that formula (V1–V4) under two denominator conventions, and picks one as primary.
- **What it does not change:** the per-method pre-registered rule (`docs/STRATEGY_GUIDE.md` §5) and the launch rule (`docs/TEAM_PLAN.md` §4.3). If the team wants this score to pick the live bot, that rule must be amended by a reviewed merge.

## 0. Run it

```bash
cd .worktrees/<member>-<task>
scripts/lock harness-<member> -- nice -n 10 .venv/bin/python -m backtest.run --model <name> --score
.venv/bin/python -m backtest.scoring compare <model_a> <model_b>   # HEADLINE_RET difference with a 90% month-bootstrap interval
.venv/bin/python -m backtest.scoring leaderboard                   # regenerate results/scoring/leaderboard.md
.venv/bin/python -m backtest.scoring field                         # re-score CASH and the six benchmarks
```

`--score` adds `reports/<name>/<YYYYMMDD-HHMM>-score.md` and its charts next to the harness's report. The first run of a tool version also scores the six benchmarks (a few minutes); after that they come from the cache.

## Scoring v2: return first (2026-10-02)

Every constant is under `scoring:` in `config.yaml`; the code is `backtest/scoring/returnfirst.py` on top of the modules below. The rules were committed before any run (`reports/review/20261002-prereg-return-first.md`, commit `0e9280b`).

### Why

| # | Reason |
|---|---|
| a | The competition keeps the top 20 **by return** first, then ranks by Sortino, Sharpe and Calmar. Return must be the primary number. v1's primary multiplied a return gate by a risk composite and averaged it, so a few high-ratio windows could outweigh how often a model makes the cut |
| b | Real teams move much less than the market. The previous edition's falling round (BTC about −7%): #20 at −1.4% (HK) and −1.6% (SG), median team −2.4% / −2.8%; cash would have ranked about #12 of 47. In the rising final, cash ranked #9 of 16. Benchmark-only bars are stricter than reality (`results/pol/20261001-final/past_leaderboards_numeric.csv`, numbers only) |
| c | The 14-day direction cannot be predicted (the validation's up-probability test failed), while volatility and dispersion can (the 60-day ensemble won the CRPS test). So lookalike weights decide which kinds of markets count, but not the mix of up and down outcomes: that mix is the pool's own share of up windows |
| d | v1's G6 median-of-20 compared two meaningless points: the 20 STRESS windows are 10 crashes and 10 rebounds, and the median falls between them. A worst-only G6 repeats G2. Crash windows are already scored as misses by a return-first score |

### Windows and weights

| Item | Rule (v2) |
|---|---|
| Pool | A start every day at **12:00 UTC** (`window_hour_utc`; the round runs 2026-10-04 12:00 → 2026-10-18 12:00 UTC), from 2020-06-01, 336 h from $100,000 cash, up to the last start whose window and 1 h lag end by the panel's last bar: 2,298 windows to 2026-09-15 with the panel to 2026-09-30 00:00 UTC |
| Spent holdout | `include_spent_holdout: true`: the 52 windows ending after 2026-08-08 16:00 UTC (opened once on 2026-10-01, now spent) are in the pool. **Every headline is also reported without them**, applying the same rules to the in-sample pool alone (its own weights, pi_up, recency age and tie group) |
| First decision | As the live bot does, each window's first decision is at its start with no previous targets. The next decisions on the model's grid (16:00 UTC + k × `rebalance_hours`) chain from it until one equals the shared history's decision at that time; from there the shared decisions apply. That is exact: a model is a deterministic function of its view and its previous targets. A 12:00 decision uses the latest 16:00 UTC universe, as live |
| Days | Clock days, as the live bot dates a fill: HKT days with boundaries at 16:00 UTC and UTC days with boundaries at 00:00 UTC; the window's start and end close the first and last. A 12:00 UTC start has 15 HKT days (4 h, 13 × 24 h, 20 h) and 15 UTC days (12 h, 13 × 24 h, 12 h). A fill at time t belongs to the day containing t; a fill at the window's very end counts in R but in no day. The activity guard runs on these same clock days (04:00 UTC, plus the UTC-day check) |
| LIVE-LIKE | `validation/live_like_v2_prelim.json`: PART 0's code unchanged (`python -m src.validation.prelim_v2`), on 12:00 UTC starts, T* = 2026-10-04 12:00 UTC, as-of 2026-09-30 00:00 UTC, pool end = the as-of. The walk-forward re-made its choices: MIX (lookalikes + REC_60) with bandwidth 0.05, where v1 had REC_60 with 0.10; the direction test failed again, so there is no direction factor. The Oct 4 rerun replaces the file |
| RECENCY | 0.5^(age / 60 days), age = days from the window's start to the latest start in the pool |
| Combined | w = 0.7 × LL / ΣLL + 0.3 × REC / ΣREC |
| Direction | UP if BTCUSDT's close at the end ≥ its close at the start. pi_up = the unweighted share of UP windows. w′ = w × pi_up / Σ_UP w (UP) or w × (1 − pi_up) / Σ_DOWN w (DOWN), so Σw′ = 1 and UP windows carry exactly pi_up |
| Sets, regimes | LOOKALIKE-25, RECENT-25 and the 20 STRESS windows from `validation/validation_set_v2_prelim.json` (12:00 starts); regime labels from the v2 build's outcome table. The sha256 of the weight, set and regime files is part of the tool version |

### Return first: bars and HIT

| Bar | DOWN windows | UP windows |
|---|---|---|
| LENIENT | −1.4965215%: the previous edition's measured #20 cut, the mean of −1.4186% (HK) and −1.5744% (SG). A test checks the constant against the file | 0%: an **ASSUMPTION**. No data exists on the general field in rising markets; the rising final's median finalist made −0.2% |
| MIDDLE | 0% | 0% |
| STRICT | max(0, median R_liq of the 6 gate benchmarks), the v1 median gate | same |

- Every bar is compared with **R_liq**, the return after the system liquidates everything at the end (0.1% on the gross notional still open).
- HIT_b = Σ w′ × 1[R_liq ≥ bar_b]. **HEADLINE_RET = (HIT_LENIENT + HIT_MIDDLE + HIT_STRICT) / 3, the primary score.**
- Report-only:
  - HIT on UP and on DOWN windows, each group's weights renormalized;
  - HIT at Pol's bars: max(0, q67 / q83 / best of the benchmarks' R_liq);
  - HEADLINE_RET on plain R.

### Risk second, and the pick order

- **Daily returns:** at the HKT boundaries (15 for a 12:00 start) and at the UTC boundaries (15). V1–V4 and FLOORED / POL keep their v1 formulas and floors (section 2).
- **CS_HIT** = the w′-weighted mean composite over the windows that clear LENIENT (0 if none). It uses V1 FLOORED on HKT days; the same on UTC days is reported.
- **Tie test:**
  - a paired bootstrap over calendar months of the window start: each draw takes M months with replacement, with all their windows;
  - 2,000 draws, seed 20261002, the same draws for every model;
  - in each draw, HIT = Σ w′ × 1[cleared] / Σ w′ over the drawn windows.
  - For every model: the 90% interval of HEADLINE_RET(model) − HEADLINE_RET(top), where the top is the eligible candidate with the highest HEADLINE_RET. If the interval contains 0, the model is tied with the top.
- **Candidates** are team models only; the 7 benchmarks (CASH included) are reference rows. The pick order:
  1. passes the hard gates;
  2. highest HEADLINE_RET;
  3. inside the tie group, highest CS_HIT;
  4. CS_HITs within 0.05 → the higher min(SCREEN, CONFIRM). This is Pol's measure: REL on the field-best bar over the windows starting 2022-07-01 … 2024-06-30 and 2024-07-01 … 2026-07-25, recomputed on the v2 windows and weights.
- **Flag:** a candidate whose HEADLINE_RET is below CASH's is marked "worse than doing nothing for the top-20 gate".
- **`compare a b`** gives the same month-bootstrap interval for two models.

### Gates (v2)

| Gate | Kind | Rule |
|---|---|---|
| G1 | **hard** | ≥ 10 active HKT days in every window, out of the 15 including the partial first and last. UTC-day counts and the guard-only share are reported |
| G4 | **hard** | The long-only run (every negative target set to 0) completes cleanly: finite numbers, every window, no negative target. Its G1 and G2 are reported, not required |
| G5 | **hard** | Leakage, as in v1 |
| G2 | report-only | Worst R > BTC_HOLD's worst |
| G3 | report-only | No regime cell median R below −10% |
| G6_median | report-only | v1's G6: STRESS worst ≥ BTC_HOLD's worst and median ≥ BTC_HOLD's median |
| G6_worst | report-only | STRESS worst ≥ BTC_HOLD's worst |
| Tail | report-only | Worst R, 5th-percentile R, median and p90 max drawdown, median R of the 10 STRESS crashes and of the 10 rebounds |

### Outputs and versions

- **score.json** (schema `minimax-score/2`) holds the return-first numbers for both pools and, per window: the bars, cleared or not, w, w′ and the in-sample w′, the month, UP or DOWN, and post-holdout or not.
  - Report-only: v1's REL on the same windows (`rel`), Pol's period check, the tail table, and the previous edition's two real windows replayed from cash with their ranks among the real teams (numbers only, `scoring.replay`).
- **The leaderboard:**
  - the latest full run of each model, candidates in the pick order, benchmarks as reference rows, both pools;
  - "old REL" is the primary of tool version `56cb5a2e85d45862`;
  - a separate **return view** (report-only) ranks the same runs by the size of the return: the mean 14-day R_liq weighted with w', with the weighted median, 10th and 90th percentiles, the share of weight above 0, the plain median, worst and best, both pools. HEADLINE_RET says how often a model makes the cut; the return view says by how much it gains. It never changes the pick or the main order;
  - rows of older tool versions stay below, marked as previous versions.
- **Independent check:** `tests/return_first_reference.py` recomputes w′, the HITs, HEADLINE_RET and CS_HIT from the saved outputs without importing the scoring code.

### Known limits (v2)

- **LENIENT in UP windows (0%) is an assumption.** There is no field data for rising markets.
- **One previous round sets the −1.4965% cut**, with about 50 teams per region; we expect about 150 now.
- **The lookalike weights are preliminary** (as-of 2026-09-30). The Oct 4 rerun changes them and therefore the tool version.
- **The post-holdout windows are in-sample** for any model tuned after 2026-10-01. That is why every headline is also shown without them.
- **A first decision whose chain never rejoins the shared history** keeps its own chain to the end of the window. Each report counts these windows.

## 1. Windows and weights

*v1. Scoring v2 replaced the pool (12:00 UTC starts, spent holdout included), the live-like file (v2 preliminary), the recency age and the combined weights; see "Scoring v2" above. Stride, sets, regimes and the event calendar work as described here.*

| Item | Rule | Why |
|---|---|---|
| Pool | Every 14-day window from cash, starting each day at 16:00 UTC (00:00 HKT), 2020-06-01 → 2026-07-25: **2,246 windows**. Uses the harness's own window code, so windows ending after the holdout date (2026-08-08 16:00 UTC) stay sealed | Same start time, length and starting state as the live round |
| Clock time | A window is 14 days of clock time, t0 to t0 + 336 h. Equity is read at the clock hours t0 + k h (the last value at or before each), daily points at t0 + 24h·d, and a fill belongs to the 24 h day of its timestamp. The engine (proposed on `feature/bar-clock-fix`) also runs decisions, fills and the guard on clock hours: a fill due in an hour with no bar waits for the next bar | The panel has 11 gaps of 1–4 h in the scored period. Counting bars stretched 134 windows to 337–341 h and moved every later day boundary and guard hour; the live bot works on clock hours |
| Stride | `stride_days: 1`, so every pool window is scored. A larger stride keeps every n-th start counted back from the newest one, and renormalizes the weights over the kept windows | A full run takes minutes, far below the 30-minute limit that would justify a stride |
| LIVE-LIKE weights | From `validation/live_like_v1.json` (PART 0): no CPI filter, no direction reweighting (PART 0 decided both). Restricted to the scored windows and renormalized. Effective number of windows ≈ 991 | They weight past windows by how much their market resembled the state before the live start, the part of the validation that did predict volatility and dispersion |
| RECENCY weights | 0.5^(age / 60), age = days from the window's end to T* = 2026-10-03 16:00 UTC. The newest scored window is 56 days old, so its weight is 0.52 | Half-life 60 days was chosen in PART 0. It keeps the score anchored on the current market without relying on the similarity model |
| STRESS | The 20 STRESS windows in `validation/validation_set_v1.json`: the 10 sharpest BTC drops and 10 sharpest rebounds. They feed only gate G6, never the average | A strategy must survive extremes, but averaging 20 extreme windows into the score would let one regime dominate |
| Report-only | Flat mean over ALL windows, RECENT25, LOOKALIKE25 (both from the validation artifact), and the 3×3 regime grid. Shown, not in the headline | Context for judgement and the README |
| Regimes | Ex-post terciles of BTC's 14-day return (down/flat/up) × its realized volatility (low/mid/high), from the validation build's outcomes table | The grid shows whether a model only works in one kind of market (gate G3) |
| Event calendar | `validation/event_calendar_v1.csv`: FOMC minutes 2020–2026 and CPI from the BLS release list (2020–2026; Oct 2025 "not published"). Not used in any weight | Kept for event-aware models and the live-window check (CPI 2026-10-14 12:30 UTC, FOMC minutes 2026-10-07 18:00 UTC) |

## 2. Metrics per window

*v1 formulas, unchanged in v2 except the daily points: v2 reads daily equity at the HKT (and UTC) day boundaries of a 12:00 UTC start, not every 24 h from the start.*

From the engine's hourly equity E_0..E_336 of each window, with E_0 = 100,000 USD before the first trade:

| Quantity | Definition |
|---|---|
| Daily equity | D_d = E_(24d), d = 0..14 (16:00 UTC each day) |
| Returns | daily r_d = D_d / D_(d−1) − 1 (14 values); hourly h_k = E_k / E_(k−1) − 1 (336 values) |
| R | E_336 / E_0 − 1: mark-to-market, **primary** |
| R_liq | (E_336 − 0.001 × gross notional open at the end) / E_0 − 1: what closing everything at the end would leave (fees only) |
| MDD | max over k of (1 − E_k / max_(j≤k) E_j), E_0 included |
| m, s, dd | for a series x of length n: m = mean; s = sqrt(Σ(x − m)² / (n − 1)); dd = sqrt(Σ min(x, 0)² / n). Risk-free rate 0. Sharpe = m / s, Sortino = m / dd; a ratio is 0 when m = 0 |

**Four readings of the formula** (the official one is unpublished):

| Variant | Returns | Sharpe | Sortino | Calmar |
|---|---|---|---|---|
| **V1 daily_raw (primary)** | daily r | m / s | m / dd | m / MDD |
| V2 daily_annual | daily r | (m / s)·√365 | (m / dd)·√365 | (m·365) / MDD |
| V3 hourly_annual | hourly h | (m / s)·√8760 | (m / dd)·√8760 | (m·8760) / MDD |
| V4 total_calmar | daily r | m / s | m / dd | R / MDD |

Composite = 0.4·Sortino + 0.3·Sharpe + 0.3·Calmar for every variant.

Why four: annualizing multiplies Sharpe and Sortino by √A but Calmar by A, so the variant decides how much the Calmar term dominates the composite. V1 is the plainest reading (no annualization constant to guess). V4 is the reading where Calmar uses the whole-period return.

**Two denominator conventions**, both always computed:

| Convention | s and dd | MDD in Calmar | Zero denominator |
|---|---|---|---|
| **FLOORED (headline default)** | floored at 0.001 (daily) and 0.001/√24 ≈ 0.000204 (hourly) | floored at 0.002 | cannot happen |
| POL (`backtest/metrics.py`) | not floored | floored at 1e-4 | ratio = 0 (so a window with no losing day gets Sortino 0) |

Why floors: a nearly flat window has a tiny s, dd or MDD, and dividing by it produces ratios in the hundreds that swamp a weighted mean. The floors are small next to real crypto volatility (0.1% a day; 0.2% drawdown), so they bind only in nearly-cash windows. Each report counts how many windows hit each floor.

**Also per window (activity, exposure, costs):**
- active days (16:00-UTC blocks with a trade), and how many came only from the engine's daily-trade guard
- exchange fees / E_0 and spread / E_0
- turnover (Σ|Δw|)
- average and maximum gross exposure, average net exposure (hourly)
- orders, counted by the shared planner's rules (a long-to-short flip is two orders), and the most orders in one decision. The bot's balance and price queries are not counted

## 3. Competition-style score

*v1. In v2, REL on the field-best bar is report-only (score.json `rel`), the primary is HEADLINE_RET, and only G1, G4 and G5 decide eligibility; see "Scoring v2" above.*

**Field proxy:** six benchmarks in the model contract (`src/models/baselines/`), scored on the same windows and cached per tool version:

| Name | Model | Definition |
|---|---|---|
| BTC_HOLD | `team_btc_hold` (Pol's) | 100% BTC |
| EW_DAILY | `team_ew_daily` | equal weights across the day's universe, rebalanced daily |
| ROT_EW | `team_rot_ew` | score = mean over 3/7/14 days of return / own volatility over the same span; hold the top 6, keep while in the top 12; equal weights; book scaled to ≤ 3%/day estimated volatility (30-day covariance); trade on > 5 points of drift |
| ROT_IV | `team_rot_iv` | ROT_EW with inverse-volatility weights and a 2%/day target |
| TREND_2 | `team_trend_2` | BTC and ETH; 40-day EMA with ±3% hysteresis; weight = 0.25 / 30-day annualized volatility, cut to 15% out of trend; decisions every 6 h; trade on > 5 points of drift |
| MOM_SS25 | `team_mom_ss25` | the launch candidate as TEAM_PLAN v1 §3 defines it: `pol_mom_ss`'s code with a frozen copy of its numbers; decisions at 16:00 UTC (TEAM_PLAN says 00:05) and a 3-point band (not in TEAM_PLAN) |

CASH (`team_cash`) is scored as a reference row, not part of the field.

| Step | Rule | Why |
|---|---|---|
| Return gate | gate_w = 1 if R_w ≥ max(0, **best** of the 6 benchmarks' R_w), else 0 (`return_gate_stat: max`; the median bar is reported alongside) | Mirrors "top 20 by return first". About 150 teams in our region make top 20 the top 13%, and the best of six benchmarks sits near their 86th percentile. The median bar (this morning) was a typical competitor, far too easy |
| Robustness (launch rule) | REL ≥ 1.00 in each of four layers: HEADLINE, live-like only, recency only, flat (equal weights). Each layer is measured against the field in that same layer | Baitoey's rule: a launch model must not depend on one weighting. It is not an eligibility gate; it is reported in every score and on the leaderboard |
| CS | CS_w(v) = gate_w × Composite_w(v), for each variant and convention | Risk-adjusted score only where the return cut is passed |
| HEADLINE | 0.70 × (Σ w_live·CS / Σ w_live) + 0.30 × (Σ w_rec·CS / Σ w_rec) | The two layers answer "how would it do in a market like the coming one" and "how is it doing now" |
| REL | HEADLINE(REL) = mean over V1–V4 of HEADLINE(v) / F(v), F(v) = the six benchmarks' mean HEADLINE(v). Per window, CS_w(REL) = mean over v of CS_w(v) / F(v), so the bootstrap and the layers work on it like on any variant | 1.00 = the field average under every reading at once. The readings disagree on what wins (section 7, finding 1); REL needs no bet on one of them |
| Primary | HEADLINE(REL, FLOORED), proposed in the 2026-10-01 review (was V1 FLOORED) | Pending review. V1–V4 and POL are always shown, with the model's rank among all scored runs under each |

**Gates** (all must pass to be eligible; thresholds in `scoring.gates`):

| Gate | Rule | Why |
|---|---|---|
| G1 activity | ≥ 10 active days in 100% of windows. Guard-driven days count, but are reported separately, and a model whose guard-only days exceed 25% of its active days is flagged | The competition requires ≥ 10 active days (8 on one source); the guard is a safety net, not a strategy |
| G2 worst fortnight | worst R over all scored windows > BTC_HOLD's worst | Pol's must-pass check, kept: never worse than simply holding BTC in the worst case |
| G3 regimes | no 3×3 regime cell with median R below −10% | No market type in which the model reliably loses big |
| G4 shorts disabled | a second run with every negative target forced to 0 completes cleanly (finite results, every window) **and passes G1 and G2** | The competition account may not allow shorts; the bot then runs long-only, so that fallback must be active and safe too, not merely run |
| G5 leakage | at 30 decision times: (1) decisions reproduce exactly (Pol's `lookahead_check`, reused); (2) unchanged when every price and volume after t is replaced by random-walk noise; (3) no file or network access inside `targets()` | (1) alone passes a model that reads past t through the arrays behind the view; (2) catches that (tested); (3) catches a model that reads the panel from disk |
| G6 STRESS survival | over the 20 STRESS windows: worst R ≥ BTC_HOLD's worst and median R ≥ BTC_HOLD's median | Survive the sharpest drops and rebounds at least as well as holding BTC |

**compare a b:** the paired HEADLINE(primary) difference, with a 90% weighted **circular** block-bootstrap interval. Circular blocks wrap around the end, so the newest windows, which carry most of the recency weight, are drawn as often as any other (plain moving blocks reached the newest window from one position against 56). Blocks of 56 consecutive windows (about two months: regimes outlast one window length, and 14-window blocks gave intervals that were too narrow, section 7 finding 4), 2,000 resamples, seed 20261003. Each resample recomputes both weighted layers with the drawn windows' own weights.

## 4. Outputs

| Output | Where | Committed? |
|---|---|---|
| Report | `reports/<model>/<YYYYMMDD-HHMM>-score.md`, charts in `reports/<model>/<YYYYMMDD-HHMM>-score/` | Yes |
| Run log | `reports/<model>/<YYYYMMDD-HHMM>.log` (the harness's log) | No |
| score.json | `results/<member>/<YYYYMMDD>-scoring/<model>-<stamp>/score.json`: every number, per window and aggregated. No wall-clock time, so two runs of the same code on the same data are byte-identical | No (2–4 MB); sha256 in the report and the registry |
| Trades | `trades.csv.gz` next to score.json, one row per coin traded | No |
| Registry | `results/scoring/registry.jsonl`: append-only, one line per full run, written under the `scoring-registry` lock (`run/locks/`) | No (shared by every worktree) |
| Leaderboard | `results/scoring/leaderboard.md`: regenerated after every registered run. Full runs and the current tool version only, identical results once, each person's run count next to their best score | No |
| Cache | `results/scoring/cache/<model>/`: per tool version and model code; `--no-cache` recomputes | No |

The **tool version** is a hash of the files that define the numbers (engine, data loader, contract, scoring modules), the `scoring:` and `harness:` config, the data identity, and every field member's code and parameters (they set the return gate and the REL unit of every score). Any change to these starts a new leaderboard, so scores from different formulas are never ranked together.

**The report** starts with:
- the summary: HEADLINE V1–V4 in both conventions with ranks, the gates with reasons, the layer scores, and a comparison with the benchmarks
- the charts: the top-25 live-like equity curves vs BTC_HOLD and the field median, weighted R and MDD histograms, STRESS vs BTC_HOLD, the regime heatmap, exposure, cumulative fees, and active days (strategy vs guard)
- a formulas appendix

## 5. Tests (`pytest -q`)

- `tests/test_scoring_metrics.py`:
  - golden values computed by hand, with the arithmetic in comments: a 15-point equity series checked for every metric, all four variants and both conventions; all-zero returns; no losses (the floor vs POL's zero); MDD with the peak at E_0
  - an independent plain-Python implementation (`tests/scoring_reference.py`) matching to 1e-12 on 1,000 random equity series
- `tests/test_scoring_competition.py`: toy tables for the return gate, CS, the weighted HEADLINE (including renormalization under a stride), the recency half-life, the gates, and the bootstrap
- `tests/test_scoring_run.py`:
  - the engine trace changes nothing
  - two runs give identical score.json
  - CASH scores 0 and fails G1
  - BTC_HOLD equals BTC's move minus the entry costs
  - the leakage gate catches a model that reads past t and one that reads files, and passes honest ones
  - the registry stays valid under 8 concurrent writers
  - every benchmark keeps the contract

## 6. Known limits

- The live formula is unknown; V1–V4 bracket the plausible readings. Treat a model that wins under only one variant with suspicion.
- The field is a proxy for other teams: six simple strategies, not the real competitors.
- The planner's minimum-order rule ($10) is not modelled, so models with many tiny rebalances (e.g. EW_DAILY) trade slightly more in the backtest than they would live.
- **Fixed on 2026-10-01: the engine no longer exceeds 100% gross.** A band-limited rebalance used to buy a new coin in full while drifted holdings stayed above target (up to 112.8% for the field, 129% for pol_trend_ls). The engine now scales the increases down to fit, as `src/execution/planner.py` does (`backtest.engine.fit_gross`). The planner also keeps a 1% cash buffer, which the engine does not.
- **Keep-alive trade** (`harness.keep_alive_weight` 0.002): a guard that finds the book exactly on target trades 0.2% of equity (more BTC, or less of the largest holding) and the next guard reverses it, so an all-cash or single-coin book is still active every day. It costs about 0.004% of equity a window, and the live bot must do the same. With a band of 0 (CASH, BTC_HOLD) the next decision unwinds the nudge, so those days count as strategy days.
- One pool window is not scored: a window start needs a bar, and 2020-12-21 16:00 UTC has none (16:00–18:00 missing). It is listed in score.json; its live-like weight was 1.7e-7. The clock-time engine could run it; it is left out so the pool stays 2,245 windows.
- **Clock time (2026-10-01, `feature/bar-clock-fix`, pending review).** The scoring reads every window by timestamp, and the proposed engine patch steps through clock hours. Only the 134 windows that touch a gap change: per-window R by at most 2.3–7.1% depending on the model (median 0.25–0.7%), REL by at most 0.009, no change in rank or eligibility among the 10 models checked. The scoring change alone, on the bar-counting engine, would wrongly fail models on G1: after a gap the old engine's guard drifts into the next clock day (one `baitoey_mr_4h` window showed 7 active clock days of 14), so the two must be reviewed and merged together.
- **Activity in UTC days.** If the organizers count UTC days, a guard keyed to HKT days is not enough, at 13:00 or 04:00 UTC alike: a day whose only trade is the 17:00 UTC decision fill leaves the next UTC day empty. Before the `guard_utc_day` proposal, 14 MOM_SS25 windows, 72 ROT_EW windows and every BTC_HOLD and CASH window had fewer than 10 active UTC days; with it, every model checked has at least 14 in every window. The scoring reports `active_days_utc` per window; G1 still counts 24 h days from 16:00 UTC.
- **The gaps are trading halts, not missing data.** Binance's own 1-minute archive has no trade in any of the 11 gaps (60–284 silent minutes for BTC and ETH). BTC reopened within 0.05% of its last price every time, as an order book frozen during a halt does. Several gaps start at 02:00 UTC (scheduled maintenance); 2023-03-24 12:39–14:00 UTC was a reported spot-trading halt after a matching-engine bug. Roostoo takes its prices from Binance, so there was no tradable price in those hours. The engine therefore keeps the last price and waits for the next bar. Nothing is filled in from other exchanges: their prices would be ones our venue never traded (checks: `results/book/20261001-bar-clock-fix/gapcheck.md`, `gapedge.md`).
- **Model views count rows.** A gap makes `view.tail(n)` reach back more than n hours in the backtest, while the live store forward-fills gaps, so live rows are hours. Small (11 gaps, nearly all in 2020–21); not changed.
- LIVE-LIKE weights come from the 2026-09-30 validation run; rerun PART 0 on Oct 3 (`python -m src.validation.live_like`) and the tool version changes with the file.
- **UNVERIFIED:** every result that uses windows after 2026-08-08 is in-sample for models tuned on them. The holdout stays sealed here.

## 7. Review, 2026-10-01 (Pol)

The full write-up, with every table, is `reports/review/20261001-scoring-review.md`. In short:

**Verified independently** (not with the engine or `tests/scoring_reference.py`):
- BTC_HOLD: R, MDD and the V1 and V2 composites recomputed from raw BTC closes on 202 windows: largest difference 8.4e-13.
- CASH: R and every composite exactly 0 in all 2,245 windows (before the keep-alive). EW_DAILY: 14 active days everywhere, max gross 100.00%.
- 120 of 120 tests passed on `feature/book-scoring`.

**Findings and changes** (numbers from the field run on tool version `c0f83aa…`, before the changes):

| # | Finding | Evidence | Change |
|---|---|---|---|
| 1 | The unpublished reading decides the winner | Calmar's share of the composite: V1 7–9%, V2 60–66%, V3 68–72%, V4 53–59%. #1 is pol_trend_ls under V1 and V4, team_rot_ew under V2 and V3 | REL proposed as the primary |
| 2 | The leaderboard could rank scores made against different fields | The tool version left out the field members' code and parameters; team_mom_ss25 runs pol_mom_ss's code | Field fingerprint in the tool version |
| 3 | The engine went above 100% gross after trades | Up to 112.8% for the field; pol_trend_ls in 58% of windows, up to 129% | `fit_gross`, as the planner does. The harness cache now keys on the engine code too |
| 4 | 14-window bootstrap blocks overstate certainty | ROT_EW − MOM_SS25 interval: block 14 [−0.005, +0.055], 28 [−0.007, +0.058], 56 [−0.016, +0.059], 112 [−0.029, +0.062] | Blocks of 56 |
| 5 | G4 only checked that the long-only run ran | With G1 and G2 added, pol_mom_ss's long-only fallback had < 10 active days in 7.7% of windows and pol_trend_ls's in 26% (all cash in downtrends) | G4 must pass G1 and G2; the engine's keep-alive trade fixes the cause |
| 6 | The return gate is mostly "do not lose money" | The field median R is ≤ 0 in 49% of windows (59% live-like weighted), so the bar there is R ≥ 0. Gate pass rates 20–35% | None. The number of teams per region is still unknown (PLAN open question 7) |
| 7 | A few windows carry the score | The top 1% of windows (22) give about 25% of the weighted CS sum, the top 5% give 59–72%; 6–9 distinct episodes | None: the competition's own skew. Read compare intervals, not point gaps |
| 8 | Blends score below their best sleeve | Five blends, REL 0.60–1.15 vs 1.32 for team_rot_ew. Faithful: each blend's R tracks its sleeves' average (correlation 0.97–0.99). The gate pays nothing below the bar, and averaging methods whose good windows do not coincide lowers the median R below both | Blends kept as evidence. Two switch orchestrators added; pol_switch_rt leads (REL 1.373) but is not separable from team_rot_ew (1.324, the steadiest across periods and readings) |

**Decision rule.** This score and the per-method rule of `docs/STRATEGY_GUIDE.md` §5 can pick different winners. Proposal: rank eligible models by HEADLINE(REL), and treat a gap whose compare interval includes 0 as a tie, broken by the §5 rule. That needs a reviewed change to `docs/TEAM_PLAN.md` §4.3.

### Afternoon update, 2026-10-01 (Pol, after Baitoey's review)

- **Bar.** About 150 teams in our region (team estimate), so the bar is now the field's best 14-day return, not its median. Low-exposure and vol-capped models fall (ROT_IV 0.87 → 0.12, TREND_2 → 0.24, blends to 0.16–0.63); models that make money in falls or ride uptrends fully invested rise.
- **Robustness rule** (Baitoey): every layer ≥ 1.00. Her rows used the HEADLINE field unit for every layer (flat 2.63 for ROT_EW); each layer is now measured against the field in that layer.
- **Circular bootstrap.** Moving blocks of 56 undersampled the newest windows, which hold half the recency weight. The fix moves MR_4h vs pol_switch_rmax_tl from 39% to 71% of resamples above 0.
- **Results and the pre-registered choice:** `reports/review/20261001-final-selection.md`. Pre-registration: `reports/review/20261001-prereg-strict-bar.md`, committed before scoring.

## 8. Change log

| Date | Version | Change | Why |
|---|---|---|---|
| 2026-10-02 | scoring v2, `feature/return-first` (pending review) | Primary HEADLINE_RET (three return bars on R_liq, live-like and direction-balanced weights); CS_HIT second inside a month-bootstrap tie group; 12:00 UTC starts with the first decision at the start; clock-day HKT and UTC buckets; the spent holdout in the pool behind a switch; only G1, G4, G5 hard; live-like weights v2 (preliminary) | Reasons a–d in "Scoring v2" above; pre-registered in `reports/review/20261002-prereg-return-first.md` before any run |
| 2026-10-01 | v1, tool `56cb5a2e85d45862` | Clock-time engine and guard (`feature/bar-clock-fix`), field-best bar, REL primary | Sections 6 and 7 |

## TEAM SIGN-OFF CHECKLIST

Every row is **pending team review**. To change a value, edit `config.yaml` → `scoring:` in a reviewed merge; the tool version, and therefore the leaderboard, changes with it.

| # | Setting | Current value | Status | Pol (2026-10-01) |
|---|---|---|---|---|
| 1 | Primary variant | REL (was V1 daily_raw) | pending team review | **Change → REL** (finding 1) |
| 2 | Primary convention | FLOORED (POL always reported) | pending team review | Agree. Floors bound in 0 windows of the active models |
| 3 | Floors (FLOORED) | s, dd: 0.001 daily, 0.001/√24 hourly; MDD 0.002 | pending team review | Agree |
| 4 | POL convention | MDD floor 1e-4, s and dd unfloored, zero denominator → 0 | pending team review | Agree (report only) |
| 5 | Composite weights | 0.4 Sortino, 0.3 Sharpe, 0.3 Calmar | pending team review | Agree (organizers' weights) |
| 6 | Annualization | V2 √365 / 365, V3 √8760 / 8760 | pending team review | Agree (24/7 market) |
| 7 | HEADLINE split | 0.70 LIVE-LIKE + 0.30 RECENCY | pending team review | Agree. Both layers lean on the last two months (live-like = REC_60 forecast) |
| 8 | Recency half-life | 60 days, age to T* = 2026-10-03 16:00 UTC | pending team review | Agree (PART 0 chose it on CRPS skill) |
| 9 | LIVE-LIKE weights | `validation/live_like_v1.json`, no CPI filter, no direction factor | pending team review | Agree; rerun on Oct 3 as planned |
| 10 | Return gate | R_w ≥ max(0, **best** R_w of the 6 benchmarks) (was the median) | pending team review | **Change → field best** (about 150 teams: top 20 = top 13%) |
| 11 | Field | BTC_HOLD, EW_DAILY, ROT_EW, ROT_IV, TREND_2, MOM_SS25 (definitions in §3) | pending team review | Agree: matches what other teams' public repos do (vol-targeted momentum, BTC/ETH trend). Now part of the tool version (finding 2) |
| 12 | G1 | ≥ 10 active days in 100% of windows; flag above 25% guard-only days | pending team review | Agree. The keep-alive trade now counts as a guard day |
| 13 | G2 | worst R > BTC_HOLD's worst | pending team review | Agree |
| 14 | G3 | no regime cell median R < −10% | pending team review | Agree |
| 15 | G4 | long-only rerun completes cleanly and passes G1 and G2 (was: completes) | pending team review | **Change → must also pass G1 and G2** (finding 5) |
| 16 | G5 | 30 decisions: determinism + future noise + no I/O | pending team review | Agree |
| 17 | G6 | STRESS worst ≥ BTC_HOLD's worst and median ≥ BTC_HOLD's median | pending team review | Agree |
| 18 | Stride | 1 day (every pool window) | pending team review | Agree |
| 19 | E_0 and R_liq cost | 100,000 USD; 0.1% on the gross notional open at the end | pending team review | Agree |
| 20 | compare | circular blocks of 56 windows (was moving blocks of 14), 2,000 resamples, 90% interval | pending team review | **Change → circular blocks of 56** (finding 4 and the afternoon update) |
| 21 | Shared files | registry, leaderboard and cache in `results/scoring/` | pending team review | Agree |
| 22 | Keep-alive trade | `harness.keep_alive_weight` 0.002 (engine and live bot) | pending team review | New (finding 5). Ask the organizers whether a 0.2% trade reversed the next day counts as an active day (Baitoey). **Answered 2026-10-01 (Book): one trade per day counts as a trading day, so the keep-alive counts** |
| 23 | Robustness rule | REL ≥ 1.00 in the HEADLINE, live-like, recency and flat layers, each against the field in that layer | pending team review | New (Baitoey's proposal, scale fixed) |
| 24 | Clock time | windows, days, decisions, fills and the guard by timestamp (`feature/bar-clock-fix`) | approved by Book 2026-10-01; code review pending (Baitoey) | — (Pol away; Book's proposal) |
| 25 | Guard time | **proposed** `harness.activity_guard_offset_hours` 11: the guard trades at the 04:00 UTC bar (12:00 HKT), was 20 (13:00 UTC); live: fill confirmed from the account, retried every later hour of the day | approved by Book 2026-10-01; code review pending (Pol for `src/live`) | — (Pol away; Book's proposal) |
| 26 | Guard covers the UTC day | **proposed** `harness.guard_utc_day` true: the guard also fires when there has been no fill since 00:00 UTC, so every day counts in UTC and in HKT. Costs +0.003 to +0.06 pp per window on the 10 models checked | approved by Book 2026-10-01; code review pending (Pol for `src/live`). Keeps both day counts covered until the organizers say which one they use | — (Pol away; Book's proposal) |
| 27 | Primary (v2) | HEADLINE_RET = mean of HIT LENIENT, MIDDLE, STRICT on R_liq (was REL) | pending team review (Book's proposal, 2026-10-02) | — |
| 28 | Bars (v2) | LENIENT −1.4965215% in DOWN windows (measured #20 cut), 0% in UP windows (**assumption**); MIDDLE 0%; STRICT max(0, benchmarks' median R_liq) | pending team review | — |
| 29 | Window start (v2) | 12:00 UTC every day; first decision at the start with no previous targets, as live | pending team review | — |
| 30 | Spent holdout (v2) | `include_spent_holdout: true`; every headline also without the 52 post-holdout windows | pending team review | — |
| 31 | Weights (v2) | LL v2 preliminary (PART 0 code on 12:00 starts), REC 0.5^(age/60) from the latest start, 0.7 / 0.3, then the pi_up direction rebalance | pending team review; LL to be rerun on Oct 4 | — |
| 32 | Risk second (v2) | CS_HIT on V1 FLOORED, HKT days; tie group from a calendar-month bootstrap (2,000 draws, seed 20261002, 90%); CS_HIT within 0.05 → min(SCREEN, CONFIRM) | pending team review | — |
| 33 | Gates (v2) | hard: G1 (HKT days, 15 buckets), G4 (runs cleanly), G5; report-only: G2, G3, G6_median, G6_worst | pending team review | — |
