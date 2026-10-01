# Evaluation: the competition-style score

How the team scores every model the same way, as close as we can get to the competition's own scoring. The code is `backtest/scoring/`, on top of the harness in `backtest/` (`docs/STRATEGY_GUIDE.md`). Every constant lives under `scoring:` in `config.yaml`. **Every setting is pending team review** until the checklist at the end is signed off.

- **Status:** tool built, formulas tested; reviewed by Pol on 2026-10-01 (section 7: what was verified, what changed, the checklist with Pol's column). Book's and Baitoey's sign-off still pending.
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
| Clock time | A window is 14 days of clock time, t0 to t0 + 336 h. Equity is read at the clock hours t0 + k h (the last value at or before each), daily points at t0 + 24h·d, and a fill belongs to the 24 h day of its timestamp. The engine (proposed on `feature/bar-clock-fix`) also runs decisions, fills and the guard on clock hours: a fill due in an hour with no bar waits for the next bar | The panel has 11 gaps of 1–4 h in the scored period. Counting bars stretched 134 windows to 337–341 h and moved every later day boundary and guard hour; the live bot works on clock hours |
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
