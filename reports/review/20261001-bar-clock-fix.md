# Clock time and the daily-trade guard (Book, 2026-10-01)

For review by **Baitoey**, with **Pol** informed (he was away when this was written).

Branch `feature/bar-clock-fix` (worktree `.worktrees/book-bar-clock-fix`), based on `feature/final` at c4bb917. **Not merged.**

The numbers below come from scratch runs of 10 models with the tool's own functions. Nothing was registered.

## 1. What the audit found (at c4bb917)

| Part | Days, schedule and guard | After a missed poll or a missing bar | The guard |
|---|---|---|---|
| Live runner (`src/live/runner.py`) | **Clock time.** The hour comes from the machine's UTC clock (lines 224–231). The day is the 16:00-UTC block containing the bar (69–72). Decisions run on the 16:00 grid, or when overdue (143–147). Roostoo server time is used only to sign requests | **Nothing shifts.** Missed hours are not replayed (19–20, 231–243). An overdue decision runs at the next hour, and the day boundary comes from the timestamp | Fires from the 13:00 UTC bar (21:00 HKT, `into_day >= 21`, 206–209), processed at about 13:00:45. A day counts as active if any fill says FILLED (161–164), but `LiveBroker.execute` maps a reply with no status ("SENT") to FILLED and never checks the account (`broker.py` 95–96). It retries only at 14:00 and 15:00 UTC, and only when an order is explicitly refused |
| Backtest engine (`backtest/engine.py`) | **Bar counts.** A window is 336 bars (159–161; `evaluate.py` 139). The day is (h − 1) // 24 bars (167), and the guard fires at the 21st bar of each 24-bar block (169). Decisions are clock hours that have a bar (59–62); a window start must have a bar (`evaluate.py` 53) | **Everything after a gap shifts.** The panel has 11 gaps of 1–4 h in the scored period, so 134 of 2,245 windows ran 337–341 h. After the gap, day boundaries and the guard moved by the gap length while decisions stayed on clock hours | Exactly one try per day, at the 21st bar. No fill check is needed in a backtest, and there is no retry |

## 2. The commits

| # | Commit | What | Pol's files touched |
|---|---|---|---|
| 1 | 34b86a6 | Scoring reads every window by clock time: equity at t0 + k h (the last value at or before), daily points at t0 + 24h·d, the window ends at t0 + 336 h, and a fill belongs to the 24 h day of its timestamp | none |
| 2 | ee55e4b | Engine in clock time, a **proposal** (details below this table) | `backtest/engine.py`, `backtest/evaluate.py` (2 lines); also Book's `backtest/scoring/leakage.py` |
| 3 | bddfdce | Guard at the **04:00 UTC** bar (offset 11, was 20). Live: a fill counts only when the account's position moved, otherwise it is UNCONFIRMED and retried every later hour of the day, up to 12 tries | `config.yaml`, `src/live/runner.py`, `tests/test_live.py` (one expected hour) |
| 4 | 6ac7b2f | Guard also covers the **UTC day** (`harness.guard_utc_day`): a guard hour after 00:00 UTC fires when there has been no fill since 00:00 UTC | `backtest/engine.py`, `backtest/evaluate.py`, `config.yaml`, `src/live/runner.py`, `tests/test_scoring_run.py` (keep-alive test now expects a guard every day) |

What commit 2 changes in the engine:
- The simulator steps through every clock hour.
- An hour with no bar has no price, and any due fill or guard waits for the next bar.
- A decision is still made at its clock hour; the view then carries the last prices up to t, as the live store does. This goes through one helper, `view_frames`, used by `compute_targets`, the determinism check and the leakage check.
- Without gaps, results are identical.

**How to merge:**
- **Commits 1 and 2 must merge together.** With the old engine, the clock-time scoring alone shows the old guard drifting into the next clock day after a gap. One `baitoey_mr_4h` window had only 7 active clock days and failed G1.
- **Commits 3 and 4 are separate proposals.** Commit 4 also works with the old guard hour.

## 3. Measured effects (10 models, scratch runs)

**Commits 1 + 2 (clock time):**
- Only the 134 gap windows change.
- Per-window R moves by at most 2.3–7.1% depending on the model (median 0.25–0.7%).
- REL moves by at most 0.009, with no change in rank or eligibility.

**Guard proposals** (REL FLOORED, all with the clock-time engine):

| Model | Guard 13:00 UTC | 04:00 UTC | 04:00 UTC + UTC day | Windows < 10 UTC days: 13:00 → 04:00 + UTC | Costs/E0 per window: 13:00 → 04:00 + UTC |
|---|---|---|---|---|---|
| baitoey_mr_4h | 3.058 | 3.005 (**G6 fails**) | 3.026 (**G6 fails**) | 165 → 0 | 0.43% → 0.44% |
| pol_trend_ls | 2.113 | 2.178 | 2.181 | 2 → 0 | 0.57% → 0.63% |
| pol_switch_rt | 1.905 | 2.050 | 1.784 | 5 → 0 | 0.62% → 0.67% |
| team_rot_ew | 1.592 | 1.615 | 1.666 | 72 → 0 | 0.32% → 0.34% |
| team_mom_ss25 | 1.129 | 1.100 | 1.082 | 14 → 0 | 0.54% → 0.58% |
| team_btc_hold, team_cash | — | — | — | 2,245 → 0 | ≤ 0.003 pp more |

- The ranking of these models is the same under all three guard settings.
- `baitoey_mr_4h` passes G6 by 0.01 pp with the guard at 13:00, and fails it by 0.05–0.06 pp with either 04:00 variant: it was on a knife edge already.

## 4. Open points
- **Who reviews what.** Under AGENTS.md v1 (still the merged version), `src/live/` is Pol's area, so commits 3 and 4 need Pol as reviewer. Under v2, Baitoey can review them.
- **The fill check applies to every order.** It sits in `Runner.trade`, so it covers decision rebalances too, not only the guard. The keep-alive and guard orders are where it matters most.
- **Hourly models get no live guard.** The runner skips the guard in any hour that had a decision (line 208), so a model with `rebalance_hours` 1 never gets one. No such model is registered. Not changed.
- **Model views count rows.** In the backtest, `view.tail(n)` reaches back more than n hours across a gap; the live store forward-fills. This is small and not changed.
- **UNVERIFIED:**
  - whether the organizers count active days in UTC or HKT
  - whether keep-alive trades count as "strategy trades"
  - that the EC2 clock is NTP-synced
- **Timing.** If any of this merges before the Oct 3 16:00 UTC rerun, the tool version changes, so every model must be rescored on the new version.
