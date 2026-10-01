# Evaluation: the competition-style score

How the team scores every model the same way, as close as we can get to the competition's own scoring. The code is `backtest/scoring/`, on top of the harness in `backtest/` (`docs/STRATEGY_GUIDE.md`). Every constant lives under `scoring:` in `config.yaml`. **Every setting is pending team review** until the checklist at the end is signed off.

- **Status:** tool built, formulas tested. The team rechecks the formulas before relying on them.
- **The official formula is unpublished** (organizers: "formulas published on Finale Day"). We know only the outline: top 20 by return per region, then 0.4·Sortino + 0.3·Sharpe + 0.3·Calmar. So the score reports four readings of that formula (V1–V4) under two denominator conventions, and picks one as primary.
- **What it does not change:** the per-method pre-registered rule (`docs/STRATEGY_GUIDE.md` §5) and the launch rule (`docs/TEAM_PLAN.md` §4.3). If the team wants this score to pick the live bot, that rule must be amended by a reviewed merge.

## 0. Run it

```bash
cd .worktrees/<member>-<task>
scripts/lock harness-<member> -- nice -n 10 .venv/bin/python -m backtest.run --model <name> --score
.venv/bin/python -m backtest.scoring compare <model_a> <model_b>   # HEADLINE difference with a 90% interval
.venv/bin/python -m backtest.scoring leaderboard                   # regenerate results/scoring/leaderboard.md
.venv/bin/python -m backtest.scoring field                         # re-score CASH and the six benchmarks
```

`--score` adds `reports/<name>/<YYYYMMDD-HHMM>-score.md` and its charts next to the harness's report. The first run of a tool version also scores the six benchmarks (a few minutes); after that they come from the cache.

## 1. Windows and weights

| Item | Rule | Why |
|---|---|---|
| Pool | Every 14-day window from cash, starting each day at 16:00 UTC (00:00 HKT), 2020-06-01 → 2026-07-25: **2,246 windows**. Uses the harness's own window code, so windows ending after the holdout date (2026-08-08 16:00 UTC) stay sealed | Same start time, length and starting state as the live round |
| Stride | `stride_days: 1`, so every pool window is scored. A larger stride keeps every n-th start counted back from the newest one, and renormalizes the weights over the kept windows | A full run takes minutes, far below the 30-minute limit that would justify a stride |
| LIVE-LIKE weights | From `validation/live_like_v1.json` (PART 0): no CPI filter, no direction reweighting (PART 0 decided both). Restricted to the scored windows and renormalized. Effective number of windows ≈ 991 | They weight past windows by how much their market resembled the state before the live start, the part of the validation that did predict volatility and dispersion |
| RECENCY weights | 0.5^(age / 60), age = days from the window's end to T* = 2026-10-03 16:00 UTC. The newest scored window is 56 days old, so its weight is 0.52 | Half-life 60 days was chosen in PART 0. It keeps the score anchored on the current market without relying on the similarity model |
| STRESS | The 20 STRESS windows in `validation/validation_set_v1.json`: the 10 sharpest BTC drops and 10 sharpest rebounds. They feed only gate G6, never the average | A strategy must survive extremes, but averaging 20 extreme windows into the score would let one regime dominate |
| Report-only | Flat mean over ALL windows, RECENT25, LOOKALIKE25 (both from the validation artifact), and the 3×3 regime grid. Shown, not in the headline | Context for judgement and the README |
| Regimes | Ex-post terciles of BTC's 14-day return (down/flat/up) × its realized volatility (low/mid/high), from the validation build's outcomes table | The grid shows whether a model only works in one kind of market (gate G3) |
| Event calendar | `validation/event_calendar_v1.csv`: FOMC minutes 2020–2026 and CPI from the BLS release list (2020–2026; Oct 2025 "not published"). Not used in any weight | Kept for event-aware models and the live-window check (CPI 2026-10-14 12:30 UTC, FOMC minutes 2026-10-07 18:00 UTC) |

## 2. Metrics per window

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
| Return gate | gate_w = 1 if R_w ≥ max(0, median of the 6 benchmarks' R_w), else 0 | Mirrors "top 20 by return first": a window only scores if the model beat a typical competitor and didn't lose money |
| CS | CS_w(v) = gate_w × Composite_w(v), for each variant and convention | Risk-adjusted score only where the return cut is passed |
| HEADLINE | 0.70 × (Σ w_live·CS / Σ w_live) + 0.30 × (Σ w_rec·CS / Σ w_rec) | The two layers answer "how would it do in a market like the coming one" and "how is it doing now" |
| Primary | HEADLINE(V1, FLOORED) | Pending review. V2–V4 and POL are always shown, with the model's rank among all scored runs under each |

**Gates** (all must pass to be eligible; thresholds in `scoring.gates`):

| Gate | Rule | Why |
|---|---|---|
| G1 activity | ≥ 10 active days in 100% of windows. Guard-driven days count, but are reported separately, and a model whose guard-only days exceed 25% of its active days is flagged | The competition requires ≥ 10 active days (8 on one source); the guard is a safety net, not a strategy |
| G2 worst fortnight | worst R over all scored windows > BTC_HOLD's worst | Pol's must-pass check, kept: never worse than simply holding BTC in the worst case |
| G3 regimes | no 3×3 regime cell with median R below −10% | No market type in which the model reliably loses big |
| G4 shorts disabled | a second run with every negative target forced to 0 completes cleanly (finite results, every window) | The competition account may not allow shorts; the bot then runs long-only |
| G5 leakage | at 30 decision times: (1) decisions reproduce exactly (Pol's `lookahead_check`, reused); (2) unchanged when every price and volume after t is replaced by random-walk noise; (3) no file or network access inside `targets()` | (1) alone passes a model that reads past t through the arrays behind the view; (2) catches that (tested); (3) catches a model that reads the panel from disk |
| G6 STRESS survival | over the 20 STRESS windows: worst R ≥ BTC_HOLD's worst and median R ≥ BTC_HOLD's median | Survive the sharpest drops and rebounds at least as well as holding BTC |

**compare a b:** the paired HEADLINE(primary) difference, with a 90% weighted moving-block bootstrap interval. Blocks of 14 consecutive windows (one window length, so overlapping windows stay together), 2,000 resamples, seed 20261003. Each resample recomputes both weighted layers with the drawn windows' own weights.

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

The **tool version** is a hash of the files that define the numbers (engine, data loader, contract, scoring modules), the `scoring:` and `harness:` config, and the data identity. Any change to these starts a new leaderboard, so scores from different formulas are never ranked together.

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
- **The engine can hold more than 100% gross**, which the live planner cannot.
  - Cause: after a band-limited rebalance (`backtest/engine.py`), the engine buys a new coin in full, but holdings that drifted above target by less than the band are not trimmed. Cash goes negative.
  - Live behaviour: `src/execution/planner.py` scales buys down to fit the free cash.
  - Size: on 2026-10-01 this showed up in 11–19% of windows for ROT_EW, ROT_IV and MOM_SS25 and 4% for TREND_2, up to 112.8% gross. Each report shows the max gross.
  - Owner: this is the engine owner's call; the scoring does not change the engine's fills.
- One pool window cannot be run: 2020-12-21 16:00 UTC has no bar in the panel (16:00–18:00 missing). It is listed in score.json; its live-like weight was 1.7e-7.
- LIVE-LIKE weights come from the 2026-09-30 validation run; rerun PART 0 on Oct 3 (`python -m src.validation.live_like`) and the tool version changes with the file.
- **UNVERIFIED:** every result that uses windows after 2026-08-08 is in-sample for models tuned on them. The holdout stays sealed here.

## TEAM SIGN-OFF CHECKLIST

Every row is **pending team review**. To change a value, edit `config.yaml` → `scoring:` in a reviewed merge; the tool version, and therefore the leaderboard, changes with it.

| # | Setting | Current value | Status |
|---|---|---|---|
| 1 | Primary variant | V1 daily_raw | pending team review |
| 2 | Primary convention | FLOORED (POL always reported) | pending team review |
| 3 | Floors (FLOORED) | s, dd: 0.001 daily, 0.001/√24 hourly; MDD 0.002 | pending team review |
| 4 | POL convention | MDD floor 1e-4, s and dd unfloored, zero denominator → 0 | pending team review |
| 5 | Composite weights | 0.4 Sortino, 0.3 Sharpe, 0.3 Calmar | pending team review |
| 6 | Annualization | V2 √365 / 365, V3 √8760 / 8760 | pending team review |
| 7 | HEADLINE split | 0.70 LIVE-LIKE + 0.30 RECENCY | pending team review |
| 8 | Recency half-life | 60 days, age to T* = 2026-10-03 16:00 UTC | pending team review |
| 9 | LIVE-LIKE weights | `validation/live_like_v1.json`, no CPI filter, no direction factor | pending team review |
| 10 | Return gate | R_w ≥ max(0, median R_w of the 6 benchmarks) | pending team review |
| 11 | Field | BTC_HOLD, EW_DAILY, ROT_EW, ROT_IV, TREND_2, MOM_SS25 (definitions in §3) | pending team review |
| 12 | G1 | ≥ 10 active days in 100% of windows; flag above 25% guard-only days | pending team review |
| 13 | G2 | worst R > BTC_HOLD's worst | pending team review |
| 14 | G3 | no regime cell median R < −10% | pending team review |
| 15 | G4 | long-only rerun completes cleanly | pending team review |
| 16 | G5 | 30 decisions: determinism + future noise + no I/O | pending team review |
| 17 | G6 | STRESS worst ≥ BTC_HOLD's worst and median ≥ BTC_HOLD's median | pending team review |
| 18 | Stride | 1 day (every pool window) | pending team review |
| 19 | E_0 and R_liq cost | 100,000 USD; 0.1% on the gross notional open at the end | pending team review |
| 20 | compare | blocks of 14 windows, 2,000 resamples, 90% interval | pending team review |
| 21 | Shared files | registry, leaderboard and cache in `results/scoring/` | pending team review |
