# Pre-registration: E at band 0.05 (E5), the decision table, and quick-exit breakdown shorts

Book, 2026-10-04. Committed on `feature/book-orch` (after 4ebe776) **before anything below is computed or
scored**. It covers the two decision rules of this task: part 1 (E5 vs vt_mom) and part 5 (quick-exit breakdown
shorts). Parts 2 to 4 and 6 have no decision rule: part 4 is descriptive, and nothing is tuned on it.

**Rules for the task:**
- no writes to `data/`;
- no Roostoo calls except the paper bots' public price reads;
- scratch scoring, under `scripts/lock`;
- nothing registered unless the part 1 rule passes **and** Book says so.

Outputs go to `results/book/20261004-e-decision/`.

## 1. E5 and the decision table

### 1.1 E5
- **E5** = `book_orch` with only E (confidence-staged entries) on, at band **0.05** (the model's band since `e3b6c0e`).
- E's parameters are unchanged from v2: a new coin enters in full if its trend score is 1 and its volatility is below
  the median of the base's coins, otherwise at half (`fraction` 0.5). The half is completed at 00:00 UTC
  (`topup_hours` 8), or at the next 16:00 decision for a coin staged at another hour.
- E5 is scored on the scratch path over all 2,298 windows, under `scripts/lock`.

**Check, before scoring.** E5's targets equal v2 E's: the model's targets do not depend on the band, and FS is off.
The engine trades a coin only when |target − weight| > band (exits always trade). So a staged half from an empty
position executes only if the half-weight is above 0.05.
- On v2 E's saved target history I report the distribution of staged half-weights and the share ≤ 0.05.
- After scoring, from E5's trade log, I report the share of staged halves with no entry fill at the next hour.

### 1.2 Models
| Model | Source |
|---|---|
| E5 | the new scratch run |
| vt_mom | registered `ac38d1af5cdc2e2d` |
| the live model, pol_switch_vt_tl_e20v45 | registered `0ec3cf0ca1185b36`, on tool `3036a0d8bfdaa6a0`, so it is not re-scored |

### 1.3 Views
The five views are exactly as in `reports/review/20261003-prereg-orch-v3.md` section 1:

| View | Definition |
|---|---|
| (a) as now | the stored full-pool HEADLINE_RET |
| (b) without post-holdout | the tool's in-sample weights |
| (c) each calendar year 2021–2026 weighted equally | w′ within each year |
| (d) UP only | w′ renormalised within UP windows |
| (e) DOWN only | w′ renormalised within DOWN windows |

- **Ranks** are among these 3 models.
- **Bootstrap:** paired, against vt_mom. It uses the tool's `month_multiplicity` (2,000 draws, seed 20261002), the
  same draws for every model and view, and a 90% interval of the difference.
- **Labels:** ahead (interval above 0), behind (below 0), tied (contains 0).

**Also reported** (not part of the rule):
- worst R;
- median max drawdown;
- the single-coin blow-up share (K8's definition, from `backtest.orch_attrib`);
- fees per window;
- the mean number of coins bought in a window's first hour (entry fills at hour 1).

### 1.4 Rule
**E5 is a "STATISTICALLY TIED ALTERNATIVE" to vt_mom if its bootstrap label is tied or ahead in ALL five views.**
Otherwise vt_mom stands.

The label is a preference choice for the team, not a claim of better returns. Nothing is registered unless the
rule passes and Book says so.

## 5. Quick-exit breakdown shorts (read-only event study)

**Events.** Check 3's events, recomputed by its own definitions (`results/book/20261003-orch-checks/check3.py`):
- a close below the previous 24-hour low, on ≥ 1.5 × the 30-day average hourly volume, liquid coins, with a 24-hour
  cool-down per coin;
- variant **a**: all events;
- variant **b**: breadth < 0.3 and BTC below its 20-day average;
- variant **c**: b, and still below the level 4 hours later.

**Entry.** The close 1 hour after the signal (variant c: t + 5 h, as in check 3).

**Cost.** One short round trip: 0.10% + 0.10% + 2 × the engine's half-spread of the coin.

**Short return.** g_k = −(close at entry + k h / entry close − 1), on hourly closes.

**Reported first:** the raw net P&L, g_k − cost, at k = 1, 2 and 4 hours, for a, b and c.

**THE pre-registered exit rule (one set).**
- Take profit at g_k ≥ +0.6%, stop at g_k ≤ −1.2%, maximum hold 4 hours.
- It is checked on the hourly closes k = 1, 2, 3, 4: exit at the first k that hits the target or the stop, otherwise
  at k = 4.
- Net P&L = g_exit − cost.
- A missing close ends the trade at the last available close; an event with no close at k = 1 is dropped.

**Information only** (not part of any rule):
- the sets +0.4% / −0.8% / 2 h and +1.0% / −2.0% / 8 h;
- a **re-short** variant of the pre-registered set: after a take-profit exit at hour k, if a close within the next
  4 hours (k + 1 … k + 4) is below the previous 24-hour low, short again at that close, under the same exit rule.
  Only one re-short is allowed per event, and the event's P&L is the sum of both legs.

**t-statistic.** As in check 3: day-block t. Net P&L is averaged per UTC day of the signal, then
t = mean / sd × √(number of days).

**DECISION RULE.** The quick-exit short is worth pre-registering as a strategy only if, for at least one of
variants a, b and c (as in check 3), the ONE pre-registered set has **both**:
- a mean net P&L > 0 with t ≥ 2;
- a positive mean net P&L in at least 3 of 2023, 2024, 2025 and 2026.

Otherwise it is not pursued.

**Reported:**
- event counts;
- mean and median net P&L, win rate, t;
- the mean per year;
- the worst loss;
- how often the stop fires before the target (and the share of time exits).
