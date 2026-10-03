# Pre-registration: final book_orch steps (macro risk check, "hold longer" test)

Book, 2026-10-03. Written and committed on `feature/book-orch` (after 1788c62) **before anything in parts 1 and 2 is
computed or scored**. Parts 3 to 5 (logging fixes, write-up, batch 4 table) have no decision rule.

Rules for the whole task: no writes to `data/` (including `data/harness/`), no Roostoo calls, no downloads, scoring
runs under `scripts/lock` with `nice -n 10`, nothing registered unless a rule below passes. Outputs go to
`results/book/20261003-final-steps/`.

## 1. Macro risk check (read-only)

**Windows.** The 2,298 scored windows of version A of book_orch v1, which is vt_mom at band 0.05 (every layer off):
`results/book/20261003-book-orch/versions/A/score.json`, run key ae56132997e605aa, tool 3036a0d8bfdaa6a0. Its
HEADLINE_RET matches the registered vt_mom run within 0.00015 (`parity_A.json`). Windows start 12:00 UTC, from
2020-06-01 to 2026-09-15. Per window, the stored values used are R, R_liq, w_final (w′), the three bars and the
three hit flags (`hit_LENIENT`, `hit_MIDDLE`, `hit_STRICT`, which are R_liq ≥ bar).

**State at each window start S** (point in time). The rules:
- **FRED.** A FRED value is the last observation dated strictly before S's UTC date. This is the validation build's
  1-day lag (`_value_before_day`), and weekends and holidays carry the last value. Series are VIXCLS, SP500,
  DTWEXBGS and DGS10, read from the newest pinned snapshot in `data/external/fred`. DTWEXBGS also gets the team's
  existing extra 7-day lag (`validation.macro_lag_days`), because H.10 is published weekly. That makes it stricter
  than a 1-day lag.
- **Derived daily series** (by observation, i.e. business days):

  | Series | Definition |
  |---|---|
  | VIX level | VIX |
  | VIX 5-day change | VIX minus VIX 5 observations earlier (index points) |
  | S&P 20-day return | SP500 / SP500 20 observations earlier − 1 |
  | S&P drawdown depth | 1 − SP500 / its maximum over the 365 calendar days up to that date |
  | Dollar 20-day change | DTWEXBGS / DTWEXBGS 20 observations earlier − 1 |
  | 10-year yield 20-day change | DGS10 minus DGS10 20 observations earlier (percentage points; report only, not in the score) |

- **Percentile rank of a derived value x at S.** Take that series' values dated in the 365 calendar days before x's
  date (x excluded). The rank is the share of them below x, with ties counting half. A rank needs at least 90 days
  of history; with less, it is missing.
- **BTC funding.** The 7-day average at S is the mean of the BTCUSDT 8-hourly funding prints with funding time in
  (S − 7 d, S], from `data/external/binance_futures_ext/fundingRate`. Its percentile is taken among the 7-day
  averages at every print time in the 365 days before S, at least 90 days of history needed. The archive starts
  2020-01, so the 2020 ranks use a shorter history.
- **BTC open interest 7-day change.** OI at the last observation ≤ S, divided by OI at the last observation ≤ S − 7 d,
  minus 1, from `data/external/lob_copy/open_interest`. Report only, not in the score. It is missing where the
  files are (before 2020-09 and after 2026-08-11).

**Macro risk score** (fixed here, not tuned). It is the mean of six percentile ranks, oriented so that high means
stress:
- p(VIX level)
- p(VIX 5-day change)
- 1 − p(S&P 20-day return)
- p(S&P drawdown depth)
- p(dollar 20-day change)
- p(BTC funding 7-day average)

If a rank is missing at S, the score is the mean of the ranks that exist; the report counts such windows.

**Reported, over all windows and for each calendar year of the window start, 2020 to 2026:**
1. **Rank correlations.**
   - Spearman correlation of the score with R, and with each hit flag (0/1).
   - Each comes with a 90% month-block bootstrap interval. The tool's `month_multiplicity` (2,000 draws, seed
     20261002) resamples the calendar months of the pool, or of that year; each window enters a draw as many times
     as its month is drawn.
2. **Top fifth vs the rest.**
   - The top fifth is the windows with score ≥ the 80th percentile of the score over all 2,298 windows. That one
     cutoff is used in every year, so the yearly counts differ.
   - For each group: count, mean R, median R, worst R, and HIT per bar. HIT is the tool's definition: the w′-weighted
     share of windows with R_liq ≥ the window's stored bar, with w′ renormalised within the group. Also the mean of
     the three HITs.
   - Unweighted shares are report only.
   - The t of the mean-R difference (top − rest) is the difference divided by its standard deviation across the same
     2,000 month-block draws.
3. **Approximate brake** (labelled approximate in the report).
   - In top-fifth windows, R_liq is multiplied by 0.5, and each hit is recomputed against the window's stored bars.
   - HEADLINE_RET is recomputed on the full pool with w′: the mean over the three bars of the weighted hit share.
   - Path effects are ignored: the brake's own trades, fees, the guard, and any change in the following decisions.
   - Check: with no scaling, the recomputation must reproduce A's stored HEADLINE_RET (0.6086).

**Decision rule.** A macro brake is worth pre-registering only if **all** of these hold:
- **D1.** Pooled over all windows, mean R in the top fifth is below the rest, with t ≤ −2.
- **D2.** In at least 4 of the 7 years 2020 to 2026, the top fifth has **both** a lower mean R **and** a lower HIT
  (mean of the three bars) than the rest of that year. A year with no top-fifth window does not count.
- **D3.** The approximate brake's HEADLINE_RET is higher than A's stored HEADLINE_RET.

Otherwise stop: no macro brake. A pass would only lead to a separate pre-registration. No brake is built or scored
in this task.

## 2. "Hold longer" test (2 scratch scoring runs, return-first tool, band 0.05)

**Versions.**
- **H15** (primary): `baitoey_vt_mom` with `keep_rank` 15 instead of 12.
- **H18** (report only): `keep_rank` 18.

Everything else is unchanged. This is vt_mom's own config parameter, so the runs use a parameter override with no
code change and no subclass. The band is the model's own 0.05.

**Baseline.** The registered vt_mom run on the same tool (3036a0d8bfdaa6a0): run key ac38d1af5cdc2e2d,
`results/book/20261001-scoring/baitoey_vt_mom-20261001-1825/score.json`, with its trade log.

**Runs.**
- `backtest.scoring.score.score_model` on the full pool (2,298 windows), with a scratch registry and leaderboard
  under `results/book/20261003-final-steps/scratch/`.
- Run under `scripts/lock book-final-steps-score`, with `nice -n 10`.
- The tool's cache is `results/scoring/cache` (scoring.cache_dir), as for every scoring run. Nothing is written to
  `data/`.

**Keep rule for H15 vs vt_mom** (all three must hold):
- **K1.** HEADLINE_RET is higher in the full pool, **and** higher in SCREEN, **and** higher in CONFIRM. SCREEN and
  CONFIRM are HEADLINE_RET over the windows starting in `harness.periods` SCREEN (2022-07-01 to 2024-06-30) and
  CONFIRM (2024-07-01 to 2026-07-25), with w′ renormalised within the period. This is the same computation as the
  v2 keep rule.
- **K2.** Turnover is lower: mean per-window turnover strictly below vt_mom's.
- **K3.** Worst R (worst per-window R) is no more than 2 pp below vt_mom's.

**Report only:**
- The bootstrap label. This is the tool's tie test against vt_mom: 90% month-block interval of the HEADLINE_RET
  difference, giving ahead, tied or behind.
- Fees per window (mean fees_e0, % of starting equity).
- Round trips within 24 h per window. An entry is a fill taking a coin from 0 to a positive weight. A round trip is
  an entry followed by a fill taking that coin back to 0 within 24 hours.
- Also HIT UP/DOWN and mean, median and worst R, for H15 and H18.

**Registration.** H15 is registered only if K1 to K3 all pass. Registration must not write to `data/`. If the
registration path would write there, I stop and ask. H18 is never registered.
