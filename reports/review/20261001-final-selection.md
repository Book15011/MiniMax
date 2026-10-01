# Final model selection under the field-best bar (2026-10-01, Pol)

| | |
|---|---|
| Branch | `feature/final` (`.worktrees/pol-final`): `feature/live-runner` plus Baitoey's `feature/mom-ss` (merged, not rewritten) |
| Pre-registration | `reports/review/20261001-prereg-strict-bar.md`, commit `1287b57`, before any of its candidates was scored |
| Runs | 28: every registered model of every member, Baitoey's chosen study variants (built exactly as her study scripts build them), the field, and the 3 pre-registered switches |
| Raw results | `results/pol/20261001-final/scores/*.json`, `final_table.csv`; scripts `rescore.py`, `final.py`, `boot.py`, `lomo.py`, `where.py` (not committed) |
| Status | Recommendation for the team. Needs Baitoey's review (`baitoey_mr_4h` is registered in her package) and the team's launch decision |

## 1. What changed since this morning, and why

- **About 150 teams in our region → the bar is the field's best.**
  - Top 20 by return is the top 13%. The median of six benchmarks (this morning's bar) is a typical competitor, far too easy.
  - The best of six sits near their 86th percentile, the closest available proxy (`scoring.return_gate_stat: max`, floored at 0).
  - REL under the median bar stays in every report for comparison. Scores on the two bars are not comparable with each other.
- **No cap on trades per minute, only 30 API calls/min.** The bot now spaces orders 3 s apart (`live.order_spacing_s`), within its own 20 calls/min.
- **Baitoey's review** (`feature/scoring-v2` confirmed, 142/142 tests) brought three proposals:
  1. **Ask the organizers whether the keep-alive trade counts as active.** Open.
  2. **The robustness rule**, adopted: REL ≥ 1.00 in every layer.
     - Her rows divided every layer by the HEADLINE's field unit, which is why ROT_EW showed 2.63 flat.
     - Each layer is now measured against the field in that same layer.
  3. **A broad-universe check**, done (section 4).
- **A bug in `compare`, fixed.**
  - Moving bootstrap blocks reached the newest window from one position, against 56 for a middle one, while the last 56 windows hold 48% of the recency weight. Every lead built on recent windows was understated.
  - Blocks are now circular (`block_indices`, tested).

## 2. All runs on the field-best bar (REL, 1.00 = field average)

Columns:
- **Robust layers** = live-like / recency / flat, each against the field in that layer.
- **SCREEN / CONFIRM** = REL within 2022-07 → 2024-06 and 2024-07 → 2026-07.
- **Pass** = the weighted share of windows that clear the bar.

| Run | REL | Eligible | Robust layers | Robust? | REL, median bar | SCREEN / CONFIRM | Pass | Median R | 90th pct R | Worst R |
|---|---|---|---|---|---|---|---|---|---|---|
| **MR_4h** (= `baitoey_mr_4h`) | **3.06** | yes | 2.84 / 3.56 / 1.10 | yes | 2.09 | 2.99 / 2.88 | 23% | +0.5% | +6.1% | −29.5% |
| VT_B0_4h (`baitoey_vt_mom`, no exits, 4 h) | 2.42 | yes | 1.92 / 3.59 / 1.02 | yes | 1.70 | 1.31 / 2.99 | 23% | +0.9% | +19.0% | −33.0% |
| **pol_switch_rmax_tl** (pre-registered) | **2.22** | yes | 2.35 / 1.90 / 2.18 | yes | 1.37 | 2.76 / 1.70 | 22% | −0.2% | +22.8% | −27.8% |
| pol_trend_ls | 2.12 | yes | 2.42 / 1.43 / 1.16 | yes | 1.31 | 3.07 / 1.28 | 22% | +0.1% | +10.6% | −16.3% |
| baitoey_vt_mom (B, 24 h) | 2.05 | yes | 1.38 / 3.57 / 1.14 | yes | 1.72 | 0.69 / 2.71 | 19% | +1.0% | +18.7% | −27.1% |
| pol_switch_rmax_mr (pre-registered) | 2.03 | yes | 1.85 / 2.45 / 1.78 | yes | 1.64 | 1.78 / 2.28 | 14% | −0.4% | +22.4% | −31.1% |
| baitoey_rot_max | 1.99 | **no** (G2, G3, G6: worst −48.6%) | 1.99 / 1.97 / 1.97 | yes | 1.31 | 2.10 / 2.04 | 24% | +0.7% | +24.2% | −48.6% |
| pol_switch_rt | 1.91 | yes | 2.05 / 1.57 / 1.43 | yes | 1.37 | 2.56 / 1.22 | 18% | −0.3% | +17.6% | −25.2% |
| pol_switch_rot_mr (pre-registered) | 1.63 | yes | 1.47 / 2.00 / 0.83 | no | 1.52 | 1.44 / 1.67 | 13% | −0.1% | +15.5% | −27.5% |
| team_rot_ew | 1.59 | yes | 1.32 / 2.21 / 1.31 | yes | 1.32 | 1.44 / 1.69 | 15% | +0.5% | +17.3% | −34.1% |
| team_btc_hold | 1.54 | no (G2, G3) | 1.39 / 1.86 / 1.48 | yes | 1.15 | 1.43 / 1.54 | 20% | +0.6% | +16.9% | −42.2% |
| VT_C_24h | 1.50 | yes | 1.07 / 2.48 / 0.91 | no | 1.63 | 0.53 / 1.92 | 16% | +0.8% | +17.6% | −27.1% |
| DIP_4h | 1.44 | yes | 1.52 / 1.26 / 1.35 | yes | 1.35 | 1.53 / 1.03 | 16% | +0.7% | +17.6% | −29.8% |
| team_ew_daily | 1.39 | no (G2, G3, G6) | 1.73 / 0.63 / 2.20 | no | 1.08 | 1.63 / 1.50 | 14% | −0.0% | +22.8% | −54.7% |
| baitoey_switch_mr | 1.36 | yes | 1.38 / 1.32 / 0.89 | no | 1.29 | 1.19 / 1.37 | 16% | +0.6% | +11.8% | −28.7% |
| baitoey_mr_bbrsi (24 h) | 1.36 | yes | 1.66 / 0.67 / 0.74 | no | 1.11 | 1.55 / 1.31 | 13% | +0.0% | +3.4% | −24.1% |
| CORE_4h | 1.24 | yes | 1.00 / 1.79 / 0.67 | no | 1.33 | 0.84 / 1.53 | 13% | +0.7% | +17.9% | −27.6% |
| pol_mom_ss / team_mom_ss25 | 1.12 | yes | 1.12 / 1.14 / 0.66 | no | 0.90 | 1.02 / 0.95 | 15% | +0.0% | +7.5% | −15.3% |
| baitoey_rot_dip | 0.88 | yes | 0.86 / 0.94 / 0.65 | no | 1.18 | 0.99 / 0.76 | 9% | +0.1% | +16.5% | −34.2% |
| baitoey_tg_mom | 0.88 | yes | 0.80 / 1.07 / 0.50 | no | 0.62 | 1.17 / 0.71 | 12% | +0.1% | +5.7% | −12.8% |
| baitoey_breakout | 0.60 | yes | 0.72 / 0.34 / 0.46 | no | 0.61 | 1.57 / 0.28 | 10% | −0.0% | +8.2% | −20.2% |
| pol_switch_rc | 0.59 | yes | 0.68 / 0.39 / 0.67 | no | 0.79 | 1.01 / 0.46 | 7% | −0.0% | +17.2% | −21.4% |
| pol_combo_rt | 0.47 | yes | 0.63 / 0.11 / 0.22 | no | 0.99 | 0.83 / 0.25 | 5% | −0.3% | +13.4% | −16.3% |
| team_trend_2 | 0.24 | yes | 0.32 / 0.04 / 0.30 | no | 0.67 | 0.38 / 0.19 | 3% | −0.1% | +11.4% | −17.9% |
| pol_combo_rb | 0.16 | yes | 0.11 / 0.29 / 0.10 | no | 1.15 | 0.14 / 0.18 | 2% | +0.6% | +16.4% | −32.8% |
| team_rot_iv | 0.12 | yes | 0.12 / 0.12 / 0.04 | no | 0.87 | 0.10 / 0.12 | 3% | +0.5% | +11.9% | −24.5% |
| team_cash | 0.01 | yes | 0.01 / 0.00 / 0.01 | no | 0.01 | 0.01 / 0.01 | 6% | −0.0% | +0.0% | −0.0% |

What the stricter bar does:
- **Who rises:** models that make money in calm or falling markets (mean reversion, long/short trend), and models fully invested in uptrends (the concentrated rotation in a switch).
- **Who falls:** vol-capped and low-exposure books (ROT_IV, TREND_2, `baitoey_tg_mom`).
- **Blends fall hardest** (0.16–0.47).

## 3. The pre-registered rule, applied

1. **Eligible and robust (9):** MR_4h, VT_B0_4h, `pol_switch_rmax_tl`, `pol_trend_ls`, `baitoey_vt_mom`, `pol_switch_rmax_mr`, `pol_switch_rt`, `team_rot_ew`, DIP_4h.
2. **By REL:** MR_4h (3.06) first, VT_B0_4h (2.42) second.
3. **Tie-break.** MR_4h − VT_B0_4h has a 90% interval that includes 0 (circular blocks: [−1.41, +2.41]), so the tie-break decides: min(SCREEN, CONFIRM) is 2.88 for MR_4h and 1.31 for VT_B0_4h.
4. **Result: MR_4h**, registered as `baitoey_mr_4h`.

## 4. How solid the lead is

**Paired differences (REL, 90% interval, blocks of 56):** moving blocks (before the fix) against circular blocks (now).

| a − b | Point | Moving | Share > 0 | Circular | Share > 0 |
|---|---|---|---|---|---|
| MR_4h − pol_switch_rmax_tl | +0.85 | [−1.45, +1.32] | 39% | [−1.10, +2.72] | 71% |
| MR_4h − VT_B0_4h | +0.64 | [−1.88, +1.71] | 46% | [−1.41, +2.41] | 70% |
| MR_4h − pol_trend_ls | +0.94 | [−1.44, +1.30] | 41% | [−1.00, +2.72] | 75% |
| MR_4h − team_rot_ew | +1.47 | [−1.23, +2.30] | 62% | [−0.85, +3.58] | 84% |
| pol_switch_rmax_tl − pol_trend_ls | +0.09 | [−0.61, +0.63] | 55% | [−0.51, +0.62] | 61% |
| pol_switch_rmax_tl − team_rot_ew | +0.62 | [−0.81, +2.05] | 76% | [−0.53, +1.77] | 82% |

**Dependence on a few windows:**

| Run | REL | Worst leave-one-month-out | Without its best episode | Without its best 2 | Share of score from top 1% / 5% | Episodes in top 1% |
|---|---|---|---|---|---|---|
| MR_4h | 3.06 | 1.74 (Jul 2026) | 1.92 | 1.73 | 50% / 91% | 3 |
| VT_B0_4h | 2.42 | 1.96 (Jul 2026) | 1.95 | 1.51 | 47% / 93% | 3 |
| pol_switch_rmax_tl | 2.22 | 2.00 (Apr 2022) | 2.00 | 1.90 | 35% / 74% | 5 |
| pol_trend_ls | 2.12 | 1.90 (Apr 2022) | 1.91 | 1.68 | 31% / 75% | 7 |
| pol_switch_rmax_mr | 2.03 | 1.58 (Jul 2026) | 1.56 | 1.30 | 62% / 92% | 6 |
| team_rot_ew | 1.59 | 1.20 (Apr 2026) | 1.22 | 1.14 | 47% / 92% | 6 |

- **MR_4h stays first in 73 of 74 leave-one-month-out runs.** The exception is dropping July 2026, where `pol_switch_rmax_tl` leads (2.00 vs 1.74).

**Where the score comes from.** In 31% of the weight, every benchmark lost (bar = 0).

| Run | Pass when bar = 0 | Pass when bar > 0 | Score from bar-0 windows | Median R when passing |
|---|---|---|---|---|
| MR_4h | 27% | 21% | 15% | +3.9% |
| VT_B0_4h | 17% | 25% | 9% | +10.0% |
| pol_switch_rmax_tl | 23% | 21% | 19% | +10.6% |
| pol_trend_ls | 39% | 14% | 36% | +4.2% |
| team_rot_ew | 0% | 21% | 0% | +13.0% |

**Survivorship** (broad universe: every panel series, including coins that died; the field rescored the same way):
- MR_4h 2.62
- VT_B0_4h 2.13
- `pol_switch_rmax_tl` 2.09
- `pol_trend_ls` 1.87
- `team_rot_ew` 1.96

The order of the top three holds.

**Reading:**
- **MR_4h is the strongest model** on this bar, the median bar and the broad universe, and it is consistent across SCREEN and CONFIRM.
- **It wins calm markets:** small steady gains (+3.9% median when it passes) beat a field that barely moves.
- **Its lead leans on recent calm months.** Without July 2026 it is 1.74. It scores only 1.10 flat, and half its score comes from 3 episodes.
- **The rule's choice fits the forecast.** The live window is forecast calm: Book's PART 0, as of Sep 30, puts BTC volatility near the 25th percentile and dispersion near the 36th.
- **`pol_switch_rmax_tl` is the all-weather alternative:**
  - flat 2.18;
  - never below 1.90 when any month or its two best episodes are dropped;
  - concentrated rotation in uptrends, long/short trend otherwise.

## 5. The best of each method

| Method (owner) | Best run | REL | Note |
|---|---|---|---|
| Mean reversion (Baitoey) | `baitoey_mr_4h` (MR_4h) | 3.06 | the pre-registered pick |
| Momentum (Baitoey) | VT_B0_4h | 2.42 | not yet a registered model; SCREEN 1.31 against CONFIRM 2.99 (recent) |
| Selector / switch (Pol) | `pol_switch_rmax_tl` | 2.22 | all-weather; uses Baitoey's `baitoey_rot_max` in uptrends, which is ineligible alone (worst −48.6%) but eligible inside the switch (worst −27.8%) |
| Trend (Pol) | `pol_trend_ls` | 2.12 | best at falls (36% of its score) |
| Momentum, field design (Book) | `team_rot_ew` | 1.59 | the steadiest long-only rotation; never scores in falls |

## 6. Recommendation and what is needed

1. **Launch model:** `baitoey_mr_4h`, the pre-registered pick.
2. **Proposed contingency, to agree before Oct 3.** Book reruns PART 0 as of Oct 3. If it no longer forecasts a calm window (forecast BTC volatility above the pool median), launch `pol_switch_rmax_tl` instead.
3. **Paper-trading both now** on live Roostoo prices:
   - tmux `mm-pol-paper-mr4h`, state in `data/live_mr4h`;
   - tmux `mm-pol-paper-swtl`, state in `data/live_swtl`.
4. **Baitoey:**
   - review `baitoey_mr_4h` (a thin subclass of her model with her parameters);
   - ask the organizers about the keep-alive trade;
   - consider registering VT_B0_4h.
5. **Book:** review the scoring changes (field-best bar, per-layer robustness, circular blocks). They need sign-off in `docs/EVALUATION.md`.
6. **Holdout:** the sealed holdout (from 2026-08-08) is opened once, on Oct 3, for the frozen launch model only.

**Competition rules, checked for both finalists:**
- **Directional only:** MR_4h buys oversold coins expecting a rebound; the switch holds momentum longs or trend longs and shorts. Neither does market making, arbitrage, pair trading or HFT.
- **No leverage:** shorts are 1x collateral, and gross is ≤ 100% after every trade (engine `fit_gross`, live planner).
- **Pace:** decisions every 4 h (MR_4h) or 24 h, at most about 7 orders per decision. That stays inside 30 API calls a minute: the bot uses ≤ 20 and spaces orders 3 s apart.
- **Activity:** a strategy trade or the guard every HKT day. On an all-cash day, MR_4h's activity comes from the keep-alive trade (about 30% of its active days), hence the question to the organizers.
- **Paper bots on live prices (first hour, 09:00 UTC):**
  - MR_4h: no coin oversold, so all cash.
  - The switch: BTC in trend, so the top 4 momentum coins at 25% each, 99% gross.

## 7. Limits

- **Everything here is in-sample.** These models were designed with 2020–2026 data in view; the holdout and the live round are the only true tests.
- **About 150 teams is an estimate**, and the best of six benchmarks is a proxy for the real top-20 cut.
- **The keep-alive trade's status as an active day is UNVERIFIED** (question to the organizers).
- **I did not try any variant beyond the three pre-registered switches.** Every extra variant tried would make the best-looking one more likely to be luck.
