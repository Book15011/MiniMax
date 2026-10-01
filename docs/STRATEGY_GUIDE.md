# Strategy guide: build, test and compare a model

Every member builds their own models. One harness scores them all the same way, and the best of the three in each method wins by the rule in §5. Read `AGENTS.md` first.

## 1. Quick start

```bash
cd /home/ubuntu/test/MiniMax
scripts/wt new <member> <model>                 # your own worktree and branch
cd .worktrees/<member>-<model>
cp src/models/_template.py src/models/<member>/<member>_<name>.py   # edit it; uncomment MODEL = ...
# add your parameters to config.yaml under `models:`, below your "# --- <member> ---" marker
.venv/bin/python -m backtest.run --list
scripts/lock harness-<member> -- nice -n 10 .venv/bin/python -m backtest.run --model <member>_<name> --score
pytest -q                                       # includes a contract test for every registered model
git add src/models/<member>/<member>_<name>.py config.yaml reports/<member>_<name>/
git commit -m "Add <member>_<name>: <what it does and why>"
```

A run takes under a minute for a daily model, plus about a minute for `--score` (a few minutes the first time, while the benchmarks are scored). It writes:
- `reports/<model>/<YYYYMMDD-HHMM>.md`: commit it
- with `--score`, `<YYYYMMDD-HHMM>-score.md` and its chart folder: commit them
- a `.log` next to them: never committed

§4.1 explains the score.

## 2. The model contract (`src/contracts.py`)

A model is a module `src/models/<member>/<name>.py` that defines `MODEL`, an object with:

- **`spec`**, a `ModelSpec`:

  | Field | Meaning |
  |---|---|
  | `name` | Starts with your member name; equals the file name |
  | `method` | `momentum`, `trend` or `selector` (§3) |
  | `author` | Your member name |
  | `rebalance_hours` | A decision every N hours (1, 2, 3, 4, 6, 8, 12 or 24), anchored at 16:00 UTC (00:00 HKT) |
  | `band` | At a decision, a coin trades only if its weight is off target by more than this |
  | `uses_shorts` | Must be True if any target can be negative |
  | `description` | One line: what it holds and why |

- **`targets(view)`**, which returns a pandas Series of signed weights by series id (`"BTCUSDT"`, …): long > 0, short < 0, **sum of |w| ≤ 1**, and only ids in `view.universe`.

`view` (`MarketView`) contains only data from bars that closed at or before the decision time `view.t`. The future is not reachable, by construction:

| Field | Content |
|---|---|
| `view.close`, `view.quote_volume` | Hourly bars, UTC close-time index, every series |
| `view.universe` | Coins the model may hold now: Roostoo-listed coins in the day's point-in-time top-30 by volume |
| `view.params` | Your block from `config.yaml` → `models:` |
| `view.prev_targets` | Your previous decision (for stickiness or hysteresis) |
| `view.tail(hours)` | The last N hours of close and volume for the universe. Use this first; slicing the full history is slow |

**Rules:**
- Pure: no files, network, clock or randomness.
- Every tunable number lives in `config.yaml`.
- If shorting turns out to be disabled on the competition account, the bot runs your model long-only. So design the long book to stand on its own, or give the model a `long_only` parameter.

The harness checks the contract at every decision: it rejects NaN, coins outside the universe, gross > 1, and shorts without `uses_shorts`. It also re-runs a few decisions to confirm they reproduce exactly.

## 3. Methods

| Method | What belongs here | Example |
|---|---|---|
| `momentum` | Ranks coins against each other and holds the relative winners (optionally shorts the losers) | `pol_mom_ss` |
| `trend` | Judges each coin, or the market, against its own past: long up-trends, flat or short down-trends | `pol_trend_ls` |
| `selector` | Combines or switches between other models by market state or recent performance | none yet: must pass the selection ladder (§6) |

A selector can call other models' `targets()` inside its own `targets()`: they're pure functions of the same view.

## 4. How the harness scores a model

- **Windows:** every day at 16:00 UTC (00:00 HKT, the live start time) from 2020-06-01, 14 days long, **starting from cash**, like the contest.
- **Trading:**
  - A decision at bar *t* fills at the close of bar *t + 1*.
  - Costs: 0.10% per side, long or short, plus each coin's real half-spread from the saved Roostoo ticker (5 bps if unknown).
  - Between decisions nothing trades.
- **Activity guard:** if an HKT day has no trade by hour 20 (20:00 HKT), the engine rebalances exactly to the standing target. The live engine does the same.
- **Universe:** the validation build's point-in-time top-30 by 30-day volume (with 90 days of history), limited to coins Roostoo lists (`harness.universe: roostoo`).
- **Window sets:**

  | Set | Windows |
  |---|---|
  | SCREEN | Starts 2022-07-01 … 2024-06-30 |
  | CONFIRM | Starts 2024-07-01 … 2026-07-25 |
  | ALL | Every start from 2020-06-01 (context) |
  | LOOKALIKE25 | The 25 lookalikes from `validation/validation_set_v1.json` |
  | RECENT25 | The 25 most recent non-overlapping windows |
  | HOLDOUT | Windows ending after 2026-08-08 16:00 UTC. **Sealed**; opened once, with `--holdout`, for the frozen launch model only |

- **Scores per window:**
  - return, max drawdown
  - **Composite A:** daily returns, annualized ratios, Calmar on the annualized return
  - **Composite B:** hourly returns, annualized ratios, Calmar on the raw 14-day return
  - both composites = 0.4·Sortino + 0.3·Sharpe + 0.3·Calmar; the official formula is published only on Finale Day, so we look at both
  - active days, turnover, fees, most orders in a day

### 4.1 How to score your model: the competition-style score

`--score` scores the model the way the competition probably will. The full definition, with every constant and the team sign-off checklist, is in `docs/EVALUATION.md`.

1. **Each window gets a composite:** 0.4·Sortino + 0.3·Sharpe + 0.3·Calmar.
   - The official formula is unpublished, so four readings are computed: V1 daily_raw (primary), V2 daily_annual, V3 hourly_annual, V4 total_calmar.
   - Each reading is computed under two denominator conventions: FLOORED (primary) and POL (this harness's).
2. **Return gate:** a window counts only if the model's 14-day return is ≥ 0 and ≥ the median of six benchmarks: BTC_HOLD, EW_DAILY, ROT_EW, ROT_IV, TREND_2 and MOM_SS25, in `src/models/baselines/`.
3. **HEADLINE** = 0.70 × the gated composite weighted by live-likeness (PART 0) + 0.30 × the same weighted by recency (half-life 60 days).
4. **Gates G1–G6.** All must pass for the model to be eligible:
   - G1: ≥ 10 active days in every window
   - G2: worst fortnight better than BTC hold
   - G3: no regime cell with median return below −10%
   - G4: still runs with shorts disabled
   - G5: no look-ahead or I/O
   - G6: survives the 20 STRESS windows at least as well as BTC hold

**Reading `<stamp>-score.md`:**
- The summary line gives HEADLINE V1 FLOORED, its rank among all scored runs, and whether the model is eligible.
- The tables give the other variants and conventions, why each gate passed or failed, the layer scores, and the benchmarks on the same windows.
- The charts follow.

**Comparing two models:** `python -m backtest.scoring compare <a> <b>` gives the HEADLINE difference with a 90% block-bootstrap interval. An interval that includes 0 means no clear winner.

**Leaderboard:** `results/scoring/leaderboard.md` lists every full run of the current tool version, with each person's run count next to their best score.

Two things to know:
- **G5 runs your `targets()` with file and network access blocked.** Keep it pure.
- **The score does not replace the §5 rule.** It runs alongside it until the team signs off the checklist in `docs/EVALUATION.md`.

## 5. Choosing the best model in a method (pre-registered)

Run `python -m backtest.compare --method <method>`. It writes `reports/compare/<method>/<YYYYMMDD-HHMM>.md`.

1. **Must-pass**, on SCREEN + CONFIRM windows:
   - at least 10 active days in **every** window
   - worst fortnight **better than BTC hold's**
   - every re-checked decision reproduces exactly
2. **Rank** the passing models in each of SCREEN and CONFIRM on four scores, higher being better:
   - median composite A
   - median composite B
   - worst-10% return
   - share of positive windows

   The period score is the mean of the four ranks.
3. **Combined** = the mean of the SCREEN and CONFIRM scores. The lowest wins; ties go to the better CONFIRM score, then lower turnover.
4. **Deadline:** models registered by **Oct 1, 20:00 HKT** compete. The comparison runs after that, and its report is committed as the record.

LOOKALIKE25 and RECENT25 are shown for judgement and the README, but don't enter the rule.

## 6. The selection ladder (selectors only)

A selector goes live only if, walking forward week by week from 2022-07, its picks beat every rung below. Each rung is scored on the realized 14 days after each decision, with a margin whose 90% interval is above zero in **both** SCREEN and CONFIRM:

| Rung | Meaning |
|---|---|
| Fixed | The momentum winner, held throughout (no selection) |
| Blend | Equal mix of the method winners |
| History | Best model on all windows so far |
| Recent | Best model over the last 25 non-overlapping windows |
| Random | Average of the candidates (the floor) |
| Oracle | Best in hindsight (the ceiling, shown for headroom only) |

The ladder runs as `python -m backtest.selection` (build item H2).

## 7. Launch and upgrades

- **Launch rule:** `docs/TEAM_PLAN.md` §4.3.
- **Upgrades during the round:** a candidate replaces the live model only if it wins the §5 rule against it and has paper-traded for 3 days without errors. Each upgrade is a reviewed merge with its report. No strategy changes in the last 3 days of the round.

## 8. Good practice

- **Keep the first version simple.** A clear rule that passes must-pass beats a clever one that doesn't.
- **Keep models fast.** Slice `view.tail()` early. A daily model should finish a full run in under a minute.
- **Don't tune on CONFIRM, LOOKALIKE25 or RECENT25.** Pick parameters on SCREEN; CONFIRM is the check.
- **Explain the idea in plain words** in the module docstring. It feeds the README, and the judges read it.
