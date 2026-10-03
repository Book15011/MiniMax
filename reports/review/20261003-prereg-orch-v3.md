# Pre-registration: book_orch v3 (score-robustness view, a per-coin trailing stop, a BTC-only hedge)

Book, 2026-10-03. Committed on `feature/book-orch` (after f9ce047) **before anything below is computed, built or
scored**.

**Rules for the task:**
- no writes to `data/`, no Roostoo calls, no downloads;
- scratch scoring path, with scoring runs under `scripts/lock` and `nice -n 10`;
- **one** registered run, and only if a version passes its keep rule.

Outputs go to `results/book/20261003-book-orch-v3/`.

## 0. Why

**Stop-losses on momentum** (the team's evidence, from published work; not re-checked here, UNVERIFIED):
- **Stocks:** a study of stop-losses on stock momentum found that they cut momentum's crash losses.
- **Crypto:** a 147-coin study (2015–2022) found the same.
- **Long-only:** a long-only replication shows mainly lower drawdowns and a higher Sortino ratio.

The authors are not named, under the team rule of no names from outside the team in docs.

**Why the stop is wide (k = 3).** Our own breakdown check showed bounces. Shorting a confirmed breakdown lost money
in every variant, and the 90th-percentile bounce was +8% within 24 hours and +15% within 72 hours
(`reports/review/20261003-orch-checks.md`, check 3).

**Why only BTC is hedged.**
- Single-coin shorts failed because they bounce: v1's short sleeve won 46% of its short-days, and v2's confident
  FALL calls were followed by rises.
- Trend shorts did raise the switch model's DOWN-window pass rate: pol_switch_vt_tl's HIT DOWN is 0.444 against
  vt_mom's 0.376 (`reports/review/20261003-batch4-results.md` on `feature/book-batch4`).

## 1. Score-robustness view (read-only, saved outputs only; done first)

**The question.** Does vt_mom's lead come mainly from the recent rally? This part is report-only and changes no rule.

**Models and saved outputs.** All are on tool `3036a0d8bfdaa6a0`, with the same 2,298 windows and the same w′.

| Model | Saved output |
|---|---|
| vt_mom | registered `ac38d1af5cdc2e2d` |
| SW = pol_switch_vt_tl | registered `1c21b2428e2291e6` |
| E, R | v2 scratch, base A′ at band 0.015 |
| book_vt_dual, book_vt_breadth, book_vt_top4 | registered `5ccb581e175dacbe`, `9440b892f63591b8`, `0865aca641d7b83c` |
| top-15 | scratch H15, `da09d8bf369b4e22` |

**Weight shares** (of total w′, the HEADLINE weight):
- on the 52 post-holdout windows;
- on windows starting in the last 90 days of window starts (start > last start − 90 days).

**Effective number of independent fortnights.**
- Windows are grouped into non-overlapping 14-day blocks of their start date, b = ⌊(start − first start) / 14 days⌋.
- Each block's weight W_b is the sum of its windows' w′.
- n_eff = (Σ W_b)² / Σ W_b² (Kish).
- Reported for the weights of views (a), (b) and (c).

**HEADLINE_RET views.** Each is the mean over the three bars of the weighted share of windows clearing the bar.

| View | Windows | Weights |
|---|---|---|
| (a) as now | all | w′ (`w_final`) |
| (b) without post-holdout | non-post-holdout | the tool's in-sample weights (`w_final_in_sample`) |
| (c) each calendar year 2021–2026 weighted equally | the six years; 2020's windows are left out | w′ renormalised within each year; the six yearly values averaged |
| (d) UP windows only | UP | w′ renormalised within UP |
| (e) DOWN windows only | DOWN | w′ renormalised within DOWN |

Each recomputation must reproduce the stored value where one exists: (a) the stored headline, (b) the stored
in-sample headline, (d) and (e) the stored hit_up and hit_down averaged over the three bars.

**Reported per view:**
- each model's value and rank among the 8 (1 = highest);
- the paired bootstrap against vt_mom. This uses the tool's `month_multiplicity` (2,000 draws, seed 20261002, the
  full pool's calendar months, the same draws for every model and view), with each view recomputed in every draw.
  It gives a 90% interval of the difference, labelled ahead, tied or behind.

## 2. New layers in `book_orch` (each switchable; defaults off)

**Base A.**
- `baitoey_vt_mom` at band **0.05**, with the option-1 hold (between decisions, the last decision's targets are
  returned unchanged) and the option-2 previous-holdings rule (the base sees book_orch's current long targets).
- v2's layers (R, E, F, FS) stay off.
- **Default change:** `book_orch`'s band goes from 0.015 (v2's A′) back to 0.05, as in v1.

**Parity check, before any layer is scored.** A on this code is compared against the registered vt_mom run. It
needs |HEADLINE_RET difference| ≤ 0.003 and a median |per-window R difference| ≤ 0.02 pp, as v1's check did
(v1's A gave 0.60859 vs 0.60874). If it fails, I **STOP** and report.

### 2.1 TS: per-coin trailing stop (checked every hour)

**Stop level.**
- σ_d(c, h) = `_trend.hourly_vol(close, h, [c], 30)` × √24. That is the 30-day hourly volatility (sample standard
  deviation of hourly returns on the clock grid) scaled to a day.
- H7(c, h) = the highest hourly close of c over (h − 7 days, h], which is 168 hourly closes including h; missing
  hours are skipped.
- The stop condition S(c, h) is **close(c, h) < H7(c, h) × (1 − k × σ_d(c, h))**. It is false when the close at h,
  H7 or σ_d is missing.
- **k = 3** (primary). **TS-k2: k = 2**, report-only.

**Exit.** A held long coin with S(c, t) gets target 0 at hour t. The engine fills it at the next bar (t + 1 h) as a
market order (taker fee and spread).

**Cool-down, derived from the view alone** (as the shock rule does).
- C(t) = the coins with S(c, h) at any of the 48 hourly closes t − 47 h … t.
- "The stop fired" is read as "the stop condition held", whether or not the coin was held then. For a held coin
  this is the same thing; the model keeps no memory beyond the view, so it cannot tell otherwise.
- A coin in C(t) is never targeted. Whenever the base runs, it runs on the universe without C(t), so the
  next-ranked coin can take the slot (as vt_mom's own early-exit filter works). The base runs at decisions, on an
  empty book, and in B′, each with C at that time.

**Between decisions.** The option-1 hold, minus stopped coins. Removed weight stays in cash; the other coins are not
resized.

**At the next 16:00 UTC decision** the base decides normally, without C(t), with the current long targets as its
previous holdings. It may refill.

**Empty book at a non-decision hour.** The model's view cannot tell a window's first hour from a book emptied by
stops.
- Normally the base runs, as at a window start, without C(t).
- **Exception:** one of the coins the base would pick on the full universe (from an empty book at t) has had S at
  any hour since the latest 16:00 decision. Then the book stays in cash until the next decision.
- This keeps "removed weight stays in cash until the next decision" when stops empty the whole book.
- The report counts how often it applies: full stop-outs, and delayed window starts.

### 2.2 BH: BTC-only hedge (checked every hour)

**State.**
- Pol's switch-state code is imported, not copied: `src.models.pol._combo.btc_state(view, p)`.
- p = team_trend_2's parameters with `ema_days: 20`, the same block as `pol_switch_vt_tl_e20v45`'s `switch`. That
  is BTC against its 20-day EMA of hourly closes, with ±3% hysteresis, the state replayed every 6 hours over
  120 days.
- **DOWN** = `btc_state(...) == "down"`. In Pol's code an undecided state also counts as down.

**Breadth.** `_trend.breadth(view, book_trend)` < **0.3**: the share of the 20 liquid coins in an up-trend.

**Action, when both hold.**
- Target BTCUSDT = **−min(0.20, 1 − the long gross at t)**, using only cash the longs leave. Longs are never cut.
- No hedge that hour if:
  - BTCUSDT is held long (a coin cannot be long and short at once, and netting would cut a long);
  - BTCUSDT is not in the universe;
  - the room is ≤ 0.

**Closing.** When either condition ends, the target is 0. The engine always executes an exit, so closing is never
filtered. Changes in hedge size trade only beyond the band, as for any coin.

**Costs.** The engine's: 0.10% to open, 0.10% to close, plus the spread.

**Shorts in versions with BH.** `uses_shorts` is True only for these versions. The tool's G4 long-only run (shorts
clipped) must pass.

### 2.3 Versions (scratch, all 2,298 windows, return-first tool)
- **A**
- **TS** (k = 3)
- **TS-k2** (report-only)
- **BH**
- **TS+BH**

A 20-window smoke run (stride 115) of every version comes first, for correctness only: gross ≤ 1, stops and the
hedge fire and close, and the attribution replay equals R.

## 3. Keep rules vs A (each PASS or FAIL)

| Rule | Definition |
|---|---|
| K1 | HEADLINE_RET higher than A's in the full pool, in SCREEN and in CONFIRM. SCREEN and CONFIRM are w′ renormalised within the `harness.periods` dates, as in v2. The tool's paired month bootstrap label against A is reported, not required |
| K2 | HIT DOWN higher than A's, and HIT UP not lower than A's by more than 0.02 (each the mean of the three bars) |
| K3 | Worst R not worse than A's: ≥ A's worst R |
| K4 | Mean turnover per window ≤ 1.25 × A's |
| K6 | Drop the round(10% × 2,298) = 230 windows where R_liq(version) − R_liq(A) is largest. On the rest, the version's HEADLINE_RET (w′ renormalised) ≥ A's |
| K7 | BH and TS+BH only: median R over the 10 rebound stress windows (`tail.full.stress_rebounds_median_R`) ≥ A's − 0.01. n/a for TS and TS-k2 |
| K8 | Single-coin blow-up share ≤ A's. This is the share of all scored windows with R < 0 where one coin (BTC's short included) caused more than 40% of the summed losses of the losing coins, from `backtest.orch_attrib` (the replay must equal R) |

**PASS** = every applicable rule passes (n/a counts as a pass).

**Registered run (ONE at most).**
- If TS and BH both pass:
  - TS+BH counts if it passes K1 to K8 itself;
  - otherwise the passing layer with the higher full-pool HEADLINE_RET is registered.
- If only one of TS and BH passes, that one is registered.
- TS-k2 is never registered.

**How a run is registered.**
1. The passing version's switches are set as `book_orch`'s defaults in `config.yaml`, in their own commit.
2. One run of `backtest.scoring.report.score_and_publish` follows. It writes `results/scoring/` and `reports/`, and
   the scoring cache `results/scoring/cache`, never `data/`.
3. If that would write to `data/`, I stop and ask.

**DEFENSIVE ALTERNATIVE label** (not registered: a team choice of risk preference). It applies to TS, BH or TS+BH
when **all** of these hold:
- K1 fails, but the full-pool HEADLINE_RET is no more than 0.01 below A's;
- SCREEN and CONFIRM are both ≥ A's;
- HIT DOWN ≥ A's + 0.03;
- worst R ≥ A's + 3 pp;
- K4, K6, K7 and K8 pass.

For TS-k2 the label is computed as information only.

## 4. Reported (report-only unless named above)

**Versions table:**
- HEADLINE_RET: full, without post-holdout, SCREEN, CONFIRM; HIT UP and DOWN;
- worst R and median max drawdown;
- the Sortino component: the per-window Sortino ratio of the primary composite (V1 FLOORED, HKT days), as the
  median and the w′-weighted mean;
- mean turnover and fees per window (% of E₀);
- K1 to K8, and the labels.

**TS:**
- **Stops per window.** A stop exit is an exit fill (w_before > 0, w_after 0) whose decision hour (fill − 1 h) has
  S true for that coin. The mean is over all windows.
- **Unique stop events** = distinct (coin, decision hour), across windows.
- **Next returns.** For each event, the 1-, 3- and 7-day return from the exit fill's close.
- **Per coin:**
  - events;
  - P&L avoided vs bounces missed: per event, effect = −w × r_7d (also r_3d), where w is the mean exited weight
    across the windows that contain the event. Avoided = Σ max(0, effect); missed = Σ max(0, −effect);
  - the exact net effect: Σ over windows of the coin's contribution under TS minus under A, from
    `backtest.orch_attrib`, per window and in % of E₀.
- **Full stop-outs and delayed window starts** (section 2.1).

**BH:**
- **Activation.** Hours and distinct UTC days with a BTC short target in the shared target history; the share of
  windows with any hedge.
- **BTC short win rate, per episode.** An episode is a run of consecutive hours with a short target. Its P&L is
  −(BTC close at the closing fill / close at the opening fill − 1) − (0.002 + 2 × the half-spread), ignoring size
  changes. The win rate is the share of episodes above 0.
- **Rebound and drop medians** (stress sets).
