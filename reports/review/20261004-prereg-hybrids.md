# Pre-registration: hybrids H1 ("E-breadth") and H2 ("E-trend"), and the decision table for the team

Book, 2026-10-04. Committed on `feature/book-orch` (after 476d3bc) **before anything below is built, computed or
scored**. The hybrids are exactly the two proposed in `reports/review/20261004-e-decision.md`, section 4.4.

**Rules for the task:**
- the shadow sessions keep running untouched;
- no writes to `data/`;
- scratch scoring, under `scripts/lock`;
- **one** registered run, and only if a hybrid is a CANDIDATE.

Outputs go to `results/book/20261004-hybrids/`.

## 1. The hybrids
Both are E5 (book_orch with E on at band 0.05; everything else as in the E decision: base vt_mom with its config,
the option-1 hold and option-2 previous holdings, every other layer off). The one change is that E's staging is gated
by a market condition.

**H1, "E-breadth".**
- At every base decision (the 16:00 UTC decision, and any decision on an empty book, e.g. a window's first hour),
  compute breadth_t = `_trend.breadth(view, book_trend)`: the share of the 20 most liquid point-in-time coins with
  trend score ≥ 0.6.
- If breadth_t < **0.60**, E's staging rule applies unchanged:
  - a new coin enters in full if its trend score is 1 and its 30-day volatility is below the median of the base's
    coins, otherwise at half (`fraction` 0.5);
  - the half is completed at 00:00 UTC if the coin is still in B′ and not broken down, else at the next 16:00 decision.
- If breadth_t ≥ 0.60, every new coin enters in full.

**H2, "E-trend".**
- At every base decision, read BTC's state with Pol's switch code, imported and not copied:
  `src/models/pol/_combo.btc_state(view, {team_trend_2's parameters, ema_days: 20})`.
  - This is a 20-day EMA of hourly closes with ±3% hysteresis, replayed every 6 hours over 120 days: the same state as
    v3's BH and pol_switch_vt_tl_e20v45's switch.
  - An undecided state counts as down, as in Pol's code.
- If the state is **down**, E's staging rule applies as above. If it is **up**, every new coin enters in full.

**Both hybrids:**
- **The condition is read at the decision time only**, from the view at that hour (data up to it). It is not read
  between decisions, and a staged half's 00:00 completion follows E unchanged whatever the condition is then. Tests
  check that the gate uses the decision's view, and that the targets do not change when later bars change or vanish.
- **Config:** `book_orch.stage.gate` takes `none` (the default: plain E, so E5 is unchanged), `breadth` or `btc_down`.
  The other keys are `gate_breadth_max: 0.60` and `gate_state: {<<: *team_trend_2, ema_days: 20}`. The defaults of
  every other layer are unchanged.
- **Scoring:** a scratch run on the return-first tool (`3036a0d8bfdaa6a0`), all 2,298 windows, band 0.05,
  `uses_shorts` False, under `scripts/lock`.

## 2. The comparison set and the measures

| Model | Source |
|---|---|
| vt_mom | registered `ac38d1af5cdc2e2d` |
| E5 | scratch `684de91ab6798af8` |
| The live model, pol_switch_vt_tl_e20v45 | registered `0ec3cf0ca1185b36` |
| H1, H2 | the new scratch runs |

**The five views** are as in `reports/review/20261003-prereg-orch-v3.md` section 1:
- (a) as now;
- (b) without post-holdout (the tool's in-sample weights);
- (c) each year 2021–2026 weighted equally;
- (d) UP only;
- (e) DOWN only.

**Ranks** are among the 5 models. **Bootstrap labels** are against vt_mom: paired, the tool's `month_multiplicity`
(2,000 draws, seed 20261002), a 90% interval, labelled ahead, tied or behind.

**Resilience**, as in `reports/review/20261004-e-decision.md` section 4.3, from each window's hourly replay of its trade
log:

| Measure | Definition |
|---|---|
| Worst day | the worst full UTC day inside any window |
| Worst R | the worst 14-day return |
| 5th-percentile R | the 5th percentile of the 14-day returns |
| Max drawdown | the median and the 90th percentile of the per-window maximum drawdown |
| Longest losing streak | the most consecutive negative full UTC days inside one window |
| Single-coin blow-up share | K8's definition, from `backtest.orch_attrib` |

Fees are the mean per window, in % of E₀.

**Also reported for H1 and H2:**
- **The share of decisions where staging was on:** the gate's condition at every 16:00 UTC decision in the scored
  period, and at every window's first hour (12:00 UTC).
- **The gap vs vt_mom by market type:** UP if BTC's 14-day return is above +2%, DOWN if below −2%, flat otherwise. It is
  given as the mean R gap and the w′-weighted HIT gap.

## 3. Rules (each PASS or FAIL, against vt_mom)

- **C1.** HEADLINE_RET higher than vt_mom's in the full pool, **and** in SCREEN, **and** in CONFIRM. SCREEN and CONFIRM
  are computed as in the earlier keep rules: w′ renormalised within `harness.periods`.
- **C2.** Not "behind" vt_mom in any of the five views (a) to (e).
- **C3.** Each of these is no worse than vt_mom's:
  - worst R ≥ vt_mom's;
  - 5th-percentile R ≥ vt_mom's;
  - 90th-percentile max drawdown ≤ vt_mom's;
  - single-coin blow-up share ≤ vt_mom's.

**Labels:**

| Label | Condition |
|---|---|
| **CANDIDATE** | C1, C2 and C3 all pass |
| **RESILIENT TIE** (a team preference, not registered) | C2 and C3 pass, C1 fails, and the full-pool HEADLINE_RET is no more than 0.01 below vt_mom's |
| **Not adopted** | otherwise |

**Registration (one run at most):**
- If exactly one hybrid is a CANDIDATE, it is registered. If both are, the one with the higher full-pool HEADLINE_RET is
  registered.
- **How.** First, shadow bot `a` is pinned explicitly to every layer off, so that a later restart cannot pick up a new
  default. Then the hybrid's switches are set as `book_orch`'s defaults in `config.yaml`, in their own commit. Then one
  `backtest.scoring.report.score_and_publish` run follows (it writes `results/scoring/` and `reports/`).
- If that path would write to `data/`, I stop and ask.
