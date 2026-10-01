# Team update, 2026-10-01 (Pol)

Everything below is on `feature/live-runner` (`.worktrees/pol-live-runner`), which stacks on `feature/scoring-v2`, which stacks on Book's `feature/book-scoring`. **Nothing is merged into `main` yet.** Each branch needs a reviewer (`scripts/wt merge … --reviewed-by …`).

## 1. Review of Book's scoring → `feature/scoring-v2`

Full write-up: `reports/review/20261001-scoring-review.md`. Checklist with my column: `docs/EVALUATION.md` (end).

- **Verified independently.**
  - BTC_HOLD matches my own calculation from raw prices to 8e-13 on 202 windows.
  - CASH is exactly 0; EW_DAILY behaves.
  - Book's 120 tests pass.
- **Five fixes:**
  1. **REL** is the proposed primary score. It is each reading's score divided by the field average, averaged over V1–V4 (1.00 = field average), because the four readings disagree on which model wins.
  2. The field's code and parameters are now part of the tool version, so the leaderboard never mixes fields.
  3. The engine no longer exceeds 100% gross after trades (it reached 112–129%).
  4. Bootstrap blocks are 56 windows, not 14 (14 overstated certainty).
  5. G4 now checks that the long-only fallback stays active and safe. It found `pol_mom_ss` and `pol_trend_ls` inactive in 8–26% of windows when clipped to long-only. A **keep-alive trade** in the engine (0.2% of equity, reversed the next day) fixes that, and the live bot does the same.
- **Known limits, no code change:**
  - The return gate is mostly "do not lose money" (the field median is ≤ 0 in about half the windows).
  - About 25% of the score comes from the top 1% of windows.

## 2. Combinations of methods

- **Blends score below their best part.** Five blends scored REL 0.60–1.15, against 1.32 for the best single model. The return gate pays nothing below the bar, and averaging methods dilutes each one's winning windows.
- **Switching works better.** `pol_switch_rt` holds the momentum rotation while BTC is in trend (40-day EMA ±3%, untuned) and long/short trend otherwise. It scores **REL 1.373, the best so far**.

## 3. Leaderboard now (REL, FLOORED, 1.00 = field average; all eligible)

| Model | REL | SCREEN / CONFIRM | Worst 14 days |
|---|---|---|---|
| `pol_switch_rt` (switch) | 1.373 | 1.89 / 1.06 | −25.2% |
| `team_rot_ew` (top-6 momentum, ≤ 3%/day vol) | 1.324 | 1.36 / 1.36 | −34.1% |
| `pol_trend_ls` | 1.314 | 2.04 / 0.83 | −16.3% |
| `pol_combo_rb` (BTC + rotation) | 1.152 | 1.60 / 1.22 | −32.8% |
| `pol_mom_ss` (TEAM_PLAN v1 launch candidate) | 0.897 | 0.92 / 0.79 | −15.3% |

- **The top three cannot be separated.** The 90% intervals of their differences include 0.
- **The switch's lead comes from 2022–24.** In 2024–26, ROT_EW is better.
- **ROT_EW is the steadiest:** the same REL in both periods and under all four readings.
- **MOM-SS is clearly beaten** by the switch and by `pol_trend_ls` (intervals above 0).
- Full leaderboard: `results/scoring/leaderboard.md`.

## 4. The live bot (E2) → `feature/live-runner`

`python -m src.live.runner run` runs one model every hour, in paper or live mode. Runbook: `deploy/README.md`.

- **Same decision code as the backtest.** The coin universe is Book's rule; it matched `universe.parquet` on all 63 real days checked.
- **Activity:** the guard at 21:00 HKT and the keep-alive trade work exactly as in the backtest.
- **Logs and state:** JSONL logs stamped with the commit, and restarts resume from saved state.
- **Data:** hourly bars from Binance's API, or the next-day archive plus Roostoo's prices when the API is blocked (it is blocked on this server).
- **Safety:**
  - the competition key is refused off EC2;
  - nothing trades before Oct 4 00:00 HKT;
  - emergency exit = commit `live.model: team_cash` (never a manual trade);
  - a refused short switches the bot to long-only.
- **Paper bot running here since 2026-10-01 05:09 UTC** (tmux `mm-pol-live`). First hour: 6 coins bought at 10.8% each, equity 99,925.
- **EC2 deploy kit:** a systemd unit, an idempotent setup script, and pinned package versions (pandas 2.3.3 and numpy 2.2.6, as in the backtests).

## 5. Decisions needed

| # | Decision | Who | By |
|---|---|---|---|
| 1 | Sign off the `docs/EVALUATION.md` checklist (my column: REL, G4, blocks of 56, keep-alive) | Book, Baitoey | Oct 1 |
| 2 | One decision rule: rank eligible models by REL; a gap whose interval includes 0 is a tie, broken by the SCREEN/CONFIRM consistency rule (amends TEAM_PLAN §4.3) | all | Oct 2 |
| 3 | Launch model. Proposal: ROT_EW's design as a team momentum model (steadiest), with `pol_switch_rt` as the alternative. Drop MOM-SS | all | Oct 2 |
| 4 | Test key into `.env` (`ROOSTOO_ENV=test`), then `python -m src.live.selfcheck --orders`: fills, fees, shorts, the short-position format | key holder | before EC2 |

## 6. Review and merge order

| Order | Branch | Content | Suggested reviewer |
|---|---|---|---|
| 1 | `feature/process-v2` | AGENTS v2 (no fixed roles), TEAM_PLAN v2 | Book |
| 2 | `feature/harness` | harness, contract, first models | Book |
| 3 | `feature/roostoo-client` | client, planner, paper broker, self-check | Baitoey |
| 4 | `feature/book-part0` | live-like weights, fair CRPS, event calendar | Pol |
| 5 | `feature/book-scoring` | the scoring (reviewed in section 1) | Pol |
| 6 | `feature/scoring-v2` | this review's fixes, combinations, switches | Book |
| 7 | `feature/live-runner` | the bot and the deploy kit | Book or Baitoey |

Also open:
- `feature/selection-ladder`: **defer until after launch**. Its finding (pickers do not beat holding one model) is in TEAM_PLAN v2; its fair-CRPS file is superseded by Book's `src/validation/crps.py`; REL plus `compare` now decide the launch model. Rebasing it needs one fix in `backtest/evaluate.py` (Pol);
- `feature/contracts-view-fields` (shared contract: needs all three);
- `feature/teamplan-insample-note`;
- Baitoey's `feature/mom-ss`: score `baitoey_tg_mom` with `--score` against `pol_switch_rt`.

## 7. For anyone adding a model today

```bash
python -m backtest.run --model <name> --score                 # report in reports/<name>/, leaderboard in results/scoring/
python -m backtest.scoring compare <name> pol_switch_rt       # interval; includes 0 = no clear difference
```

REL is the headline number. A model that goes to cash is now active every day through the keep-alive trade.
