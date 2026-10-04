# Pre-registration: three breadth ideas on top of H1 (emergency trigger, hysteresis, breadth change)

Book, 2026-10-04. Committed on `feature/book-orch` (after 82844d3) **before any of it is built, computed or scored**.
The ideas come from the team (Book's notes). H1 ("E-breadth", registered `033c466d54a7766f`) is the fixed control.

**Rules:**
- one setting per idea, with no threshold grid;
- no writes to `data/`, scratch scoring under `scripts/lock`;
- nothing registered or switched without Book's say;
- the shadow sessions are left running, untouched.

Outputs go to `results/book/20261004-breadth-ideas/`.

## 0. Already tried? (searched before writing this: reports, research notes and models on every local branch)

| Idea | What exists | Verdict |
|---|---|---|
| Breadth used in a rule | v1 short sleeve (breadth < 0.3 at 16:00); batch 4 `book_vt_breadth` (exposure × breadth / 0.6; failed); v3 BH (hourly BTC hedge when breadth < 0.3; failed); H1 (staging while breadth < 0.60 at the decision; passed) | none acts early on a breadth collapse |
| Hysteresis | only on the BTC trend switch (team_trend_2 ±3%, Pol's e20 switch, Baitoey's switch variants) | never on breadth or staging |
| Hourly triggers | v1 shock rule (BTC −5% in 4 h), v3 per-coin trailing stop, v3 BTC hedge | none is a breadth-triggered early decision |
| Breadth change | never used | new |

All three ideas are new.

## 1. The variants

Everything not named here is H1 unchanged: E5 (book_orch with E on, band 0.05), staging gated by breadth at the
decision.

**Breadth.** Breadth = `_trend.breadth(view, book_trend)`, the share of the 20 most liquid point-in-time coins with trend
score ≥ 0.6. With 20 coins it moves in steps of 0.05.
- Breadth at an earlier hour is recomputed from the current view, cut at that hour, with the current point-in-time
  universe.
- Everything reads only data up to the current hour. Tests check no look-ahead.

### A, "H1-emergency": an early decision after a breadth collapse
- The scheduled decisions are exactly H1's.
- At every other hour t with a non-empty book, let t_d be the latest 16:00 UTC decision hour, b_t the breadth at t,
  and b_d the breadth at t_d. **The trigger fires** when **b_t < 0.40** and **b_d − b_t ≥ 0.25**, and the same condition
  was not already true at any hour between t_d and t. So it fires at most once between scheduled decisions.
- **When it fires, H1 makes an early E5 decision at t:**
  - vt_mom re-ranks with the current holdings;
  - a held coin the base drops is exited;
  - a new coin enters by E's rule (staging is on, since b_t < 0.40 < 0.60);
  - **held coins keep their current targets**: no resizing, and a pending staged half is not completed early.
- Until the next 16:00 decision the targets are held, as in H1.
- A half bought at an early decision is normally completed at the next 16:00 decision. The 00:00 top-up only completes
  halves that match the 16:00 decision's weights.
- This is not a full hourly recalculation: the base runs only at a trigger hour.

### B, "H1-hysteresis": a wider on/off boundary
- Staging turns **on when breadth < 0.55** and **off when breadth ≥ 0.65**. In between (0.55 or 0.60) it keeps the
  previous state.
- **The previous state is read from the view.** Walk back from the decision hour itself through the previous 30 daily
  16:00 decision hours; the newest reading outside the band sets the state. If none is decisive within 30 days, H1's
  rule applies (on if < 0.60).
- These are the example values from the notes, not tuned. At a 0.05 step, B differs from H1 only at readings of 0.55
  and 0.60, so a small difference is expected.

### C, "H1-drop": low and falling breadth
- Staging is on only if **breadth < 0.60** and **breadth has fallen by at least 0.10** (two coins of 20) since the
  previous 16:00 decision (t − 24 h; for a window's first hour, the latest 16:00 before it).
- Otherwise new coins enter in full. C stages less often than H1, on a subset of H1's staging decisions.

**Config.** In `book_orch.stage`:
- `gate`: `breadth_hyst` (B) or `breadth_drop` (C), with `gate_on_below: 0.55`, `gate_off_at: 0.65`,
  `gate_memory_days: 30`, `gate_drop_min: 0.10`;
- A: `emergency: {enabled: true, breadth_below: 0.40, drop_min: 0.25}`, with `gate: breadth`.

The defaults stay H1: `gate: breadth`, emergency off.

## 2. Scoring and comparison
- **Scoring:** three scratch runs on the return-first tool (`3036a0d8bfdaa6a0`), all 2,298 windows, band 0.05,
  `uses_shorts` False.
- **Compared with:**
  - H1 (scratch `033c466d54a7766f`, the control);
  - vt_mom (registered `ac38d1af5cdc2e2d`);
  - E5 (scratch `684de91ab6798af8`);
  - the live model (registered `0ec3cf0ca1185b36`), for context.
- **Measures**, as in `reports/review/20261004-prereg-hybrids.md`:
  - the five views (a) to (e), with ranks;
  - paired month-block bootstrap labels (2,000 draws, seed 20261002, 90%) **against H1** and against vt_mom;
  - SCREEN and CONFIRM;
  - worst day, worst R, 5th-percentile R, median and 90th-percentile max drawdown, longest losing streak, single-coin
    blow-up share;
  - fees and turnover per window;
  - the gap by UP, DOWN and flat windows (BTC's 14-day return beyond ±2%);
  - how often staging was on;
  - for A, how often the trigger fired.

## 3. Decision rule (against H1, the control)

A variant is **BETTER THAN H1** only if **all** of these hold:
1. HEADLINE_RET higher than H1's in the full pool, in SCREEN and in CONFIRM.
2. Not "behind" H1 in any of the five views, and not "behind" vt_mom in any of them.
3. Each of these is no worse than H1's:
   - worst R;
   - 5th-percentile R;
   - 90th-percentile max drawdown;
   - single-coin blow-up share.
4. Worst day no more than 0.5 pp worse than H1's, and longest losing streak no more than 1 day longer.
5. Turnover and fees per window each no more than 10% above H1's.

Otherwise the variant is **NOT BETTER**, and H1 stays the control.

The bootstrap label against H1 in view (a) is reported. A variant that passes but is only "tied" with H1 is described
as such: better on the point estimates, not shown to be better. Nothing is registered or switched without Book's
decision.
