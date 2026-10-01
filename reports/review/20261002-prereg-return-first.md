# Pre-registration: the return-first score (2026-10-02, Book, before any scoring run)

| | |
|---|---|
| Branch | `feature/return-first` (`.worktrees/book-return-first`), on `feature/realtest` at `f9bbc15` (tool version `56cb5a2e85d45862`) |
| Committed | alone, before any code change, weight rebuild or scoring run of this task |
| Changes after this commit | none. If a rule proves impossible, the closest version is implemented and reported as a **DEVIATION** |
| Not changed | any model's code; the live runner and its config; the launch choice (a team decision) |

## 1. Why

a) **The competition keeps the top 20 by return first,** and only then ranks by Sortino, Sharpe and Calmar. So return must be the primary number. The current primary (REL) multiplies a return gate by a risk composite and averages it. A model can score well there through a few high-ratio windows, even when it misses the cut more often than another model.

b) **Real teams move much less than the market.** In the previous edition's falling round (BTC about −7%):
   - the #20 team made −1.4% (HK, 47 ranked) and −1.6% (SG, 55 ranked);
   - the median team made −2.4% (HK) and −2.8% (SG);
   - holding cash would have ranked about #12 of 47.

   In the rising final, cash ranked #9 of 16. Bars set only by benchmarks are therefore stricter than the real cut. (Source: `results/pol/20261001-final/past_leaderboards_numeric.csv`, numbers only.)

c) **The 14-day direction cannot be predicted; volatility and dispersion can.** The validation's up-probability test failed (no Brier skill), while the 60-day ensemble won the CRPS test. So lookalike weights may decide which kinds of markets count, but not the mix of up and down outcomes. That mix is set from the pool's own share of up windows.

d) **The old G6 median-of-20 test compares two meaningless points.** The 20 STRESS windows are 10 crashes and 10 rebounds, so the median of 20 falls between them. A worst-only G6 repeats G2. Crash windows are already scored as misses by a return-first score.

## 2. Windows and weights

**2.1 Windows**
- **Pool.** A window starts every day at 12:00 UTC, from 2020-06-01 12:00 UTC. The real round starts 2026-10-04 12:00 UTC and lasts 336 h. Each window runs 336 h from $100,000 cash. A start needs a bar, as now.
  - The pool includes every window whose 336 h, plus the 1 h execution lag, end by the last complete hour in `data/`. The harness panel ends at 2026-09-30 00:00 UTC, so the last start is 2026-09-15 12:00 UTC, giving 2,298 windows.
- **Config switch `scoring.include_spent_holdout: true`.** "Post-holdout" windows are those ending after `harness.holdout_from` (2026-08-08 16:00 UTC): 52 starts, 2026-07-26 to 2026-09-15. Every headline is reported twice:
  - on the full pool;
  - on the in-sample pool (2,246 windows). The same rules are applied to that pool alone: weights renormalized over it, `pi_up` recomputed on it, recency age measured from its own latest start, and its own top model and tie group.
- **Decisions.**
  - Each model keeps its own grid: 16:00 UTC + k × `rebalance_hours`.
  - The live bot makes its first decision at its first hour, with no previous targets. So in every window the engine makes an extra first decision at the window start, with empty previous targets.
  - The window's next grid decisions take their previous targets from that first decision. Once one of them equals the shared-history decision at the same time, the shared decisions are used from there on. This is exact: a model is a deterministic function of its view and its previous targets.
  - The universe at a decision is the latest 16:00 UTC universe at or before it, as now and as live.
- **Fills** are as now:
  - a decision at t fills at the close of t + 1 h;
  - the entry trade is exact;
  - the activity guard fires from the 04:00 UTC bar if the HKT day has no fill yet, or if there has been no fill since 00:00 UTC (`guard_utc_day`).

  What changes is that the guard's days become clock days (HKT days starting at 16:00 UTC, as the live bot counts them), not 24 h counted from the window start.
- **Day buckets** (activity and daily returns), for a 12:00 UTC start:

  | Day definition | Boundaries | Buckets |
  |---|---|---|
  | HKT | t0, every 16:00 UTC inside the window, t0 + 336 h | 15 (first 4 h, last 20 h) |
  | UTC | t0, every 00:00 UTC inside, t0 + 336 h | 15 (first and last 12 h) |

  - A fill at clock time τ belongs to the bucket [b, b′) that contains τ, as the live bot dates a fill. A fill at exactly t0 + 336 h is after the end: it counts in costs and R, but not as an active day.

**2.2 Lookalike weights v2 (preliminary).**
- **Method.** The existing PART 0 code, unchanged (`src.validation.build`, then `src.validation.live_like`), run through a small wrapper with these inputs:
  - validation grid hour 12:00 UTC (the window starts);
  - T* = 2026-10-04 12:00 UTC (the round's start);
  - as-of = 2026-09-30 00:00 UTC (the last complete hour in `data/`);
  - pool end H = the as-of. The holdout is spent, so the lookalike pool must cover every scored window.
- **Data.** The harness panel already in `data/validation/`: no download and no rebuild. Every intermediate table goes to `results/`; nothing in `data/` is written.
- **Outputs.**
  - `validation/live_like_v2_prelim.json` and `validation/validation_set_v2_prelim.json` (its LOOKALIKE-25, RECENT-25 and STRESS sets, with 12:00 starts), with their reports.
  - The v1 files are not touched. The Oct 4 rerun replaces the v2 files.
- **Choices left to the code.** The walk-forward re-makes the ensemble and bandwidth choices with the unchanged rules. The weights are used without a direction factor.
- **STOP condition.** If the rerun's direction test now passes (it failed in v1), I stop and report before scoring.
- **Reported:** the top 10 lookalike windows, and how much weight moved vs v1. v1's 16:00 start is matched to the same day's 12:00 start; the measure is total variation, ½ Σ |w_v2 − w_v1|.

**2.3 Recency weights:** REC = 0.5^(age / 60 days), where age = days from the window's start to the latest window start in the pool.

**2.4 Combined weight:** w = 0.7 × LL / ΣLL + 0.3 × REC / ΣREC, sums over the pool.

**2.5 Direction rebalance**
- A window is UP if BTCUSDT's close at its end (t0 + 336 h) is ≥ its close at the start, else DOWN. Each close is the last one at or before that hour.
- `pi_up` = the unweighted share of UP windows in the pool. The validation reported 0.54; it is reported here.
- w′ = w × pi_up / Σ_UP w for UP windows, and w × (1 − pi_up) / Σ_DOWN w for DOWN windows, so Σw′ = 1.

## 3. Return first: three bars and HIT

**3.1** The bars use **R_liq**: mark-to-market at the end minus 0.1% on the gross notional still held (the system liquidates at the end). Plain R is reported alongside, as report-only.

**3.2 Bars, per window**

| Bar | DOWN windows | UP windows |
|---|---|---|
| LENIENT | **−1.4965215%**, the measured #20 cut (see below) | **0%**, an **ASSUMPTION** |
| MIDDLE | 0% | 0% |
| STRICT | max(0, median R_liq of the 6 gate benchmarks in the same window) | same |

- **LENIENT DOWN:** the mean of the two #20 returns, −1.4186090% (HK) and −1.5744340% (SG), in `past_leaderboards_numeric.csv`, rounded to 1e-9. That is the "−1.5%" of the task. A test checks that the constant equals that mean.
- **LENIENT UP:** no data exists on the general field in rising markets, so 0% is labelled as an assumption in the config and the docs. The rising final's median finalist made −0.2%.
- **STRICT:** the 6 gate benchmarks are BTC_HOLD, EW_DAILY, ROT_EW, ROT_IV, TREND_2 and MOM_SS25. This is the current median return gate.

**3.3** HIT_b = Σ over windows of w′ × 1[R_liq ≥ bar_b]. **HEADLINE_RET = (HIT_LENIENT + HIT_MIDDLE + HIT_STRICT) / 3: the primary score.**

**3.4 Report-only**
- HIT on UP and on DOWN windows separately, with each group's w′ renormalized to 1.
- HIT at Pol's bars: max(0, the 6 benchmarks' q67 / q83 / best R_liq), as in `results/pol/20261001-final/bars2.py` (pandas linear quantiles), but on R_liq.
- HEADLINE_RET on plain R.

## 4. Risk second, and the pick order

**4.1 Daily returns and composites**
- Equity at the HKT boundaries of 2.1 gives 15 daily returns; the same at the UTC boundaries gives another 15.
- Composites V1–V4, FLOORED and POL, use the existing formulas and floors for each day definition. V3 is hourly and does not depend on the days.
- **Primary composite = V1 FLOORED on HKT days.**

**4.2 CS_HIT** = the w′-weighted mean of the primary composite over the windows that clear the LENIENT bar. It is 0 if no window clears it.

**4.3 Tie test**
- Paired block bootstrap over calendar months (UTC) of the window start: each draw takes M months with replacement from the pool's M months, together with all their windows. 2,000 draws, numpy `default_rng(20261002)`, the same draws for every model.
- In each draw, HIT_b = Σ w′ × 1[R_liq ≥ bar_b] / Σ w′ over the drawn windows (with repeats), and HEADLINE_RET follows.
- The top model is the eligible candidate with the highest HEADLINE_RET. For every model, the statistic is HEADLINE_RET(model) − HEADLINE_RET(top), with a 90% interval from its 5th and 95th percentiles. If the interval contains 0, the model is tied with the top.

**4.4 Candidates and pick order.** Candidates are team models only. The 7 benchmarks, CASH included, are reference rows. Pick order:
1. passes the hard gates (PART 5);
2. highest HEADLINE_RET;
3. inside the tie group (the top model plus every eligible candidate tied with it), highest CS_HIT;
4. tie-break on CS_HIT:
   - if other tie-group members are within 0.05 of the best CS_HIT, the one among them with the higher min(SCREEN, CONFIRM) wins;
   - this is Pol's measure (`bars2.py`): REL on the field-best bar over the windows starting 2022-07-01 … 2024-06-30 (SCREEN) and 2024-07-01 … 2026-07-25 (CONFIRM);
   - it is recomputed here on the new windows, with the new per-window composites, LL v2 and the new recency weights. Pol's own numbers (tool `56cb5a2e`) are shown alongside.

The leaderboard repeats the procedure on the rest of the tie group, then lists the other eligible candidates by HEADLINE_RET, then the ineligible ones. Any candidate whose HEADLINE_RET is below CASH's is flagged **"worse than doing nothing for the top-20 gate"**.

## 5. Gates

**Hard (eligibility)**
- **G1:** at least 10 active HKT days in every window, out of the 15 buckets including the partial first and last. Also reported: UTC-day counts and the share of active days that come only from the guard.
- **G4:** a run with every negative target set to 0 completes cleanly: finite numbers in every window, every window present, no negative target. Whether that run passes G1 and G2 is reported, not required.
- **G5:** the leakage check passes (unchanged).

**Report-only**
- **G2:** worst R > BTC_HOLD's worst.
- **G3:** no regime cell with median R below −10%. Labels come from the v2 build's outcome table for 12:00 starts.
- **G6 median-of-20:** worst ≥ BTC_HOLD's worst and median ≥ BTC_HOLD's median.
- **G6 worst-of-20:** worst ≥ BTC_HOLD's worst.
- Both G6 forms use the v2 STRESS set.
- **Tail table** (plain R): worst R, 5th-percentile R, median and p90 max drawdown, and the median R of the 10 crash and of the 10 rebound STRESS windows.

## 6. Recheck and sanity expectations

**6.1 Unit tests:**
- the weights sum to 1, and the UP share equals pi_up;
- the bars on 5 hand-built windows;
- HIT and HEADLINE_RET by hand for 2 toy models;
- the bootstrap is deterministic under its seed;
- the LENIENT constant equals the past-leaderboard mean;
- 15 HKT and 15 UTC buckets for a 12:00 UTC start;
- the first decision falls at the window start, with empty previous targets.

**6.2 Independent recomputation.** A standalone script that imports nothing from `backtest/` recomputes w′, the three HITs, HEADLINE_RET and CS_HIT for three models: the top eligible model, CASH and BTC_HOLD. It reads:
- the saved per-window outputs (`score.json` of the model and of the 6 benchmarks);
- the LL v2 file;
- the panel's BTC closes.

It must match to 1e-12.

**6.3 Expectations, written before any run (actual vs expected is reported)**

| Model | Expected |
|---|---|
| CASH | HIT_LENIENT ≥ 1 − pi_up: it loses only keep-alive fees, so it clears −1.5% in every DOWN window (HIT_DOWN, LENIENT = 100%). In an UP window it clears 0% only when its 0.2% keep-alive BTC position gains more than its fees; that share is not predicted. In DOWN windows that position mostly loses, so its MIDDLE and STRICT HIT_DOWN are low (≤ 25%). HIT_STRICT ≤ HIT_MIDDLE, because the STRICT bar is never below 0. |
| BTC_HOLD | HIT_UP on LENIENT and MIDDLE ≥ 90%: it misses only UP windows where BTC rose less than its costs, about 0.25%. HIT_DOWN is low, ≤ 30%: it clears −1.5% only in mild declines. |
| Candidates | Every candidate below CASH on HEADLINE_RET is listed. |

**6.4 Engine consistency.** For pol_switch_vt_tl, team_rot_ew and baitoey_mr_4h, the windows starting at 12:00 UTC and at 16:00 UTC on the same day should differ only by the 4-hour shift.
- **Expectation:** median |ΔR| ≤ 1 percentage point.
- **Flag:** anything above 1 pp.

**6.5** The full test suite passes.

## 7. Models scored

Every model in the scoring registry whose code is on this branch:
- **Candidates:** the 13 on the current leaderboard (baitoey_mr_4h, baitoey_mr_bbrsi, baitoey_rot_max, baitoey_tg_mom, baitoey_vt_mom, pol_mom_ss, pol_switch3, pol_switch_rmax_mr, pol_switch_rmax_tl, pol_switch_rot_mr, pol_switch_rt, pol_switch_vt_tl, pol_trend_ls), plus 6 registered only in an older tool version (pol_combo_all, pol_combo_ms_tl, pol_combo_rb, pol_combo_rt, pol_combo_rtt, pol_switch_rc).
- **Benchmarks:** the 7.

Four models were registered from `feature/volume` on 2026-10-01 between 16:21 and 16:39 UTC: pol_vt_mvr, pol_mr_cap, pol_switch_vtm_tl and pol_switch3_cap. Their code is not on this branch, so they cannot be scored from it. That is recorded as a **DEVIATION**.

The tool version changes, and every full run registers under it. Rows from older tool versions stay on the leaderboard, marked as a previous version.
