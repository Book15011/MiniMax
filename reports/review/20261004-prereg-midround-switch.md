# Pre-registration: switching the live bot mid-round, from e20v45 to another model

Book, 2026-10-04, during the live round. The live bot started the round at 20:00 HKT with
`pol_switch_vt_tl_e20v45` (e20v45) and holds its coins. Every score so far starts a model from cash on day 0 for 14
days. This test asks a different question: **if we redeploy model X on day k, it inherits e20v45's coins and return
so far and runs the remaining 14 − k days. Does that beat staying with e20v45?** Committed before any of it is
computed.

**Rules:**
- report-only, nothing registered or switched;
- no writes to `data/`, no Roostoo calls;
- the live bot, its config and EC2 are not touched;
- the shadow sessions and the paper comparison are left running.

## 1. What is compared

- **Stay:** e20v45 for the whole 14-day window, its scored path.
- **Switch(X, k):** e20v45 from cash at t0 until t0 + k days (12:00 UTC, 20:00 HKT), then X for the rest of the
  window.
- **X:**
  - `pol_abl_shock` (vt_mom with the crash rule);
  - `baitoey_vt_mom`;
  - `book_orch` (H1).
- **k:** 1, 2, 3, 5 and 7 days.
- **Population:** every scored window t0 (2,298) whose switch time t0 + k days is itself a scored window start. The
  last k windows drop out.

**How a switch behaves live** (`src/live/runner.py` on main): the account keeps its coins, and the new model's state
starts empty (no previous targets). Its first decision comes at the next hour, and it trades exactly to that
decision.

**What that means here:**
- X's decisions after the switch equal X's decisions from cash at the switch time. A model only sees the market and
  its own previous targets, and those are empty after a switch.
- X's path after the switch is therefore X's own scored window that starts at t0 + k days, cut at t0 + 14 days.
- The combined return is e20v45's equity at hour 24k, times X's equity from its start to hour 24(14 − k).
- **One correction:** X's window from cash pays a full entry, while a switch only trades the difference from
  e20v45's weights at the switch. That entry is replaced by the switch's own cost, computed with the same fees and
  half-spreads: |X's entry weights − e20v45's weights at hour 24k|.
- R_liq charges the liquidation cost on X's gross at the end, as the tool does.
- Paths are replayed from each registered run's trade log. Check: k = 0 reproduces X's score and k = 14 reproduces
  e20v45's.

**Lock-in.** The same rule as the live config: from day 10, at +3%, sell everything at the next hour. It is applied
on the combined path and shown as a second set of columns.

## 2. Measures

For every (X, k), and for stay:
- HEADLINE_RET with the tool's bars and weights of each window t0;
- mean R, worst R and 5th-percentile R;
- the share of windows where the switch ended higher than staying;
- the mean switch cost;
- a paired month-block bootstrap of the HEADLINE_RET difference against stay (2,000 draws, seed 20261002, 90%).

Each is reported:
- (a) over all windows;
- (b) over **the windows whose market state at the switch time matches the state at this round's start:** BTC's
  20-day trend switch (Pol's `btc_state`, e20v45's own switch) up, and breadth ≥ 0.60.

## 3. Decision rule

**SWITCH TO X AT DAY k IS WORTH IT** only if all of these hold:
1. HEADLINE_RET is "ahead" of stay in view (b) (the 90% interval of the difference above 0).
2. It is not "behind" stay in view (a).
3. Worst R is no more than 2 pp worse than stay's, and 5th-percentile R no more than 1 pp worse, in (a).

Otherwise the label is **STAY WITH e20v45**. The lock-in columns are report-only.

## 4. Caveats, stated now
- **State (b) is the state at the switch, not a forecast.** The 14-day direction is not predictable
  (`docs/EVALUATION.md`).
- **Days k ≥ 1 are in the future.** The test tells us what a switch on that day would have done historically, not
  what it will do in this round.
- **The cost correction uses weights at hour 24k.** The live switch fills about one hour later.
