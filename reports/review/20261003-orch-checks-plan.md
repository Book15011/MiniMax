# Plan: read-only checks on book_orch v2 (2026-10-03, Book)

Committed before anything is computed. Inputs:
- the stored v2 forecasts (`validation/book_orch_v2_forecasts.json` and the files it pins);
- the saved per-window outputs of A′ and E (`results/book/20261003-book-orch-v2/versions/`);
- `data/`, read-only.

No training, scoring, registration or downloads. Outputs go to `results/book/20261003-orch-checks/` only.

## Common definitions
- **Period:** forecast rows from 2021-06-07 16:00 UTC, with a label.
- **r_H:** close(t + 1 h + H) / close(t + 1 h) − 1, from the bars stamped exactly then: entry one hour after the signal, the engine's lag.
- **σ8:** the coin's 30-day hourly volatility × √8.
- **Day-block t-stats:** the statistic is averaged per UTC day, then t = mean / sd × √(number of days). For 72-hour returns, which overlap across days, the blocks are 3 consecutive days.

## Check 1: is the ranking skill worth money once volatility is controlled?
- **Hours used:** hours with at least 9 liquid coins that have q, r_8 and σ.
- **Groups:** every hour, coins are split into volatility terciles by rank: group = ⌊3 (rank − 1) / n⌋.
- **Halves:** within a group of m coins, the ⌊m/2⌋ highest q against the ⌊m/2⌋ lowest q (the middle coin is dropped when m is odd).
- **Spreads, per hour and group:**
  - raw spread = mean r_8 of the top half − bottom half;
  - risk-adjusted spread = the same with r_8 / σ8;
  - group IC = Spearman correlation of q with r_8 within the group.
- **Pooled:** per hour, the mean of the three groups.
- **DECISION RULE.** A v3 forecaster is worth building only if:
  - the **raw** volatility-controlled spread is > 0 with day-block t ≥ 2 in at least **2 of the 3 groups**, AND
  - the pooled raw spread is > 0 in at least **3 of 2023, 2024, 2025, 2026**.

  Otherwise the ML line stops. The risk-adjusted spread and the IC are reported but do not enter the rule.
- **Filter test** (report-only):
  - At each 16:00 UTC decision, take A′'s long targets (its saved hourly targets). A pick is "bottom fifth" when its q is in the lowest 20% of the liquid universe at that hour (percentile rank ≤ 0.2). Picks without a forecast are left out.
  - Reported:
    - the count of bottom-fifth picks;
    - the mean next-24 h and 72 h return of bottom-fifth picks minus the other picks;
    - a t-stat on the same-day excess return of the bottom-fifth picks (day blocks; 3-day blocks for 72 h).

## Check 2: overextended entries (report-only)
- **Entries:** a coin's target in A′'s saved hourly target history goes from 0 to above 0. Each real entry counts once. Window-start entries from cash repeat the same picks and are not added.
- **Measures at entry, data up to t:**
  - Wilder RSI(14) on daily closes (closes at t − 24 h × k);
  - Wilder RSI(14) on hourly closes;
  - 7-day return / (7-day hourly volatility × √168);
  - (close / mean of the 20 daily closes − 1) / the std of the 20 daily returns.
- **Afterwards, from the fill at t + 1 h:** the return after 1, 3 and 7 days, and the worst close-to-entry drop within 7 days.
- **Buckets:** daily RSI < 70, 70–80, > 80; terciles of the other two measures over all entries.
- **Reported:** counts, means, day-block t-stats, per-year signs, and the 10 entries with the worst 7-day drop.

## Check 3: short after a confirmed breakdown? (report-only event study)
- **Event:** at hour t, a coin in the liquid universe at t closes below its lowest close of the previous 24 hours (t − 24 h … t − 1 h), with that hour's quote volume ≥ 1.5 × its mean hourly quote volume over the previous 720 hours (missing = 0).
  - After an event, the same coin has no new event for 24 hours.
  - vt_mom's own definition (24-hour volume ≥ 1.5 × its 7-day average for 24 hours) does not match, so it is shown as an information row only.
- **Variants:**
  - (a) all events;
  - (b) breadth < 0.3 (the stored feature: the liquid universe's up-trend share) AND BTC's close below the mean of its hourly closes over the last 20 days;
  - (c) (b), and the coin's close at t + 4 h still below the broken 24-hour low, entering one hour after that (t + 5 h).
- **Short P&L at H = 8, 24, 72 h after entry:** −(close(entry + H) / close(entry) − 1) − (0.10% + 0.10% + 2 × the engine's half-spread).
- **The bounce:** the 90th percentile of the largest rise above entry within H.
- **DECISION RULE.** A short rule is worth pre-registering only if some variant (a, b or c) has:
  - mean net P&L > 0 with day-block t ≥ 2 (3-day blocks at 72 h), at 24 h or at 72 h, AND
  - a positive mean in at least **3 of 2023, 2024, 2025, 2026** at that same horizon.

  Otherwise no short rule is pre-registered. With 3 variants × 2 horizons tested, a pass is reported with that multiplicity noted.

## Checks 4–6 (report-only)
- **Check 4:** the six windows are rebuilt from the saved trade logs, with `explain()` / `coin_log` records from re-running the model hourly from each window's start (no scoring).
- **Check 5:** trades are classified as:
  - window-start entry;
  - guard;
  - exit (to 0);
  - target change at a 16:00 decision;
  - E's staged second half (target change at 00:00);
  - drift-band (target unchanged);

  using the saved shared target history. The maker saving is an upper bound and UNVERIFIED.
- **Check 6:** a listing of `data/`, with nothing downloaded.
