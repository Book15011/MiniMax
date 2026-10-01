# Review of `feature/book-scoring`, and what changed (2026-10-01)

| | |
|---|---|
| Reviewer | Pol (with Claude Code) |
| Reviewed | `feature/book-scoring` at `298eb78`: scoring, baselines, the field, selection (`compare`) |
| Changes | `feature/scoring-v2`, stacked on it: `56905e4`, `3ab4e4b`, `7ad0c9b`, `0dbb6e7` and the docs commit after them |
| Tool version | before `c0f83aa56ae994e9` → after `ce40153bf480e315` (new leaderboard) |
| Tests | 120/120 on Book's branch; 137/137 on `feature/scoring-v2` |
| Status | **Needs Book's review**, then merge after `feature/book-scoring`. Settings stay "pending team review" until the checklist in `docs/EVALUATION.md` is signed off |

## 1. Summary

1. **Book's scoring is correct where it can be checked.** BTC_HOLD matches my own arithmetic from raw prices to 8.4e-13 on 202 windows; CASH is exactly 0; EW_DAILY behaves. The structure (return gate, then the composite, two weighted layers, six gates, a paired bootstrap) mirrors the competition well.
2. **Eight findings, five fixed in code:**
   - REL replaces V1 as the proposed primary, so no single unpublished reading decides.
   - The field's code and parameters are now part of the tool version.
   - The engine no longer exceeds 100% gross after trades.
   - Bootstrap blocks are 56 windows, not 14.
   - G4 checks that the long-only fallback is still active and safe; a keep-alive trade fixes what it found.
3. **Blends of existing methods score below their best part.** The return gate pays nothing below the bar, and averaging two methods dilutes each one's winning windows. **Switching** between methods by BTC's trend state works better.
4. **Ranking now** (REL, 1.00 = field average, all eligible):

   | Model | REL |
   |---|---|
   | `pol_switch_rt` | 1.373 |
   | `team_rot_ew` | 1.324 |
   | `pol_trend_ls` | 1.314 |
   | `pol_mom_ss` | 0.897 |

   **The plan's launch candidate (MOM-SS) is below the field average, and below BTC held.** Among the top three the intervals overlap. ROT_EW is the steadiest: REL 1.36 in both SCREEN and CONFIRM, 1.32–1.33 under every reading.

## 2. Book's six questions on the baselines

| Question | CASH | BTC_HOLD | EW_DAILY |
|---|---|---|---|
| 1. Runs without errors? | Yes | Yes | Yes |
| 2. Score looks reasonable? | 0 (FLOORED) | V1 0.076, REL 1.15: above three of the active models (finding 6) | V1 0.074, REL 1.08 |
| 3. Metrics correct? | R and every composite exactly 0 in 2,245 windows | **Recomputed independently** from raw BTC closes: R, MDD, V1 and V2 composites match to 8.4e-13 on 202 windows | 14 active days everywhere, max gross 100.00%, fees 0.15% of E_0 a window |
| 4. Gates as expected? | Fails G1 (never trades) | Fails G1 (one trade), G2 and G3 | Fails G2, G3, G6 (worst fortnight −54.7%) |
| 5. Registered? | Yes, leaderboard regenerated | Yes | Yes |
| 6. Makes sense vs the others? | Floor | Yes, but it beats MOM_SS25, ROT_IV and TREND_2 | Yes |

With the keep-alive trade (finding 5), CASH and BTC_HOLD are now active every day, so they pass G1. CASH scores 0.007 under FLOORED. Under POL it scores 0.32 REL, because unfloored ratios explode on a nearly flat equity curve. That supports FLOORED as the primary convention.

## 3. Findings

Numbers in this section are from the field run on tool version `c0f83aa…`, before the changes, unless marked.

### Finding 1: the unpublished reading decides the winner → REL

Share of the composite (gated windows, HEADLINE weights) from each term:

| Model | V1 Sortino / Sharpe / Calmar | V2 | V3 | V4 |
|---|---|---|---|---|
| team_rot_ew | 67% / 24% / 9% | 26% / 9% / 64% | 19% / 10% / 71% | 32% / 11% / 57% |
| team_mom_ss25 | 70% / 23% / 8% | 29% / 9% / 61% | 22% / 10% / 68% | 35% / 11% / 54% |
| pol_trend_ls | 72% / 20% / 7% | 31% / 9% / 60% | 20% / 9% / 71% | 37% / 10% / 53% |

- V1 makes Calmar irrelevant; V2 and V3 make it dominant. The textbook reading annualizes the ratios (V2/V3), so betting on V1 alone is risky.
- The #1 model flips between readings: pol_trend_ls under V1 and V4, team_rot_ew under V2 and V3.
- **REL** = HEADLINE(v) / the field's mean HEADLINE(v), averaged over V1–V4. 1.00 = field average under every reading. It is linear in the per-window CS, so the bootstrap and the layers work unchanged. A test checks that the field itself averages exactly 1.00.

### Finding 2: the leaderboard could rank scores made against different fields → fingerprint

The field sets every model's return gate, but the tool version left out the field members' code and parameters. team_mom_ss25 runs `pol_mom_ss`'s code, so tuning pol_mom_ss silently changed every model's gate. Now the version hashes each field member's sources and parameters. A test checks that it moves when a field parameter changes, and stays put when a non-field model changes.

### Finding 3: the engine exceeded 100% gross after trades → `fit_gross`

| Model | Windows above 100% | Max gross |
|---|---|---|
| pol_trend_ls | 58.2% | 1.291 |
| team_rot_ew | 19.1% | 1.029 |
| team_mom_ss25 | 15.2% | 1.073 |
| team_rot_iv | 11.4% | 1.128 |
| team_trend_2 | 4.2% | 1.042 |

- Cause: a band-limited rebalance bought new coins in full while drifted holdings stayed above target.
- Fix: reductions in full, increases scaled down together to fit, as the live planner does.
- After the fix, gross right after every trade is at most 1.000000. Hourly gross can still exceed 100% between trades when shorts are open (price drift, not new exposure): up to 1.24 for pol_trend_ls.
- **Also fixed:** the harness cache keyed only on the model file. An engine change, or a change to a reused base class or a combination's sleeves, left stale results. It now hashes the engine files and every reachable `src.models` module.

### Finding 4: 14-window bootstrap blocks overstate certainty → 56

ROT_EW − MOM_SS25, V1 FLOORED, same 2,000 resamples:

| Block (windows) | Interval | Share > 0 |
|---|---|---|
| 14 | [−0.0054, +0.0552] | 90% |
| 28 | [−0.0068, +0.0578] | 89% |
| 56 | [−0.0162, +0.0592] | 83% |
| 112 | [−0.0291, +0.0619] | 77% |

Windows overlap 13 days in 14, and market regimes last months. 56 (about two months) is a compromise. The interval still widens at 112, so even 56 may understate the uncertainty a little; treat a borderline interval as a tie.

### Finding 5: G4 only checked that the long-only run ran → stricter G4 and a keep-alive trade

| Long-only fallback | Windows with ≥ 10 active days (need 100%) |
|---|---|
| pol_mom_ss | 92.3% |
| pol_trend_ls | 74.0% |

- If the exchange refuses shorts, the bot runs long-only. Clipped to long-only, these models go all-cash in downtrends, and the activity guard had nothing to trade. That would breach the competition's activity rule.
- G4 now requires the fallback to pass G1 and G2.
- **The engine's keep-alive trade** fixes the cause. When the guard finds the book exactly on target, it trades 0.2% of equity (more BTC, or less of the largest holding) and the next guard reverses it. Cost: about 0.004% of equity a window. After it, both fallbacks are active in 100% of windows.
- **The live bot must do the same** (E2).

### Finding 6: the return gate is mostly "do not lose money" (no change)

- The six benchmarks' median R is ≤ 0 in 49% of windows (59% live-like weighted), so there the bar is just R ≥ 0.
- Gate pass rates: 20–35% (BTC_HOLD 34%, ROT_EW 35%, MOM_SS25 27%).
- The real bar is the 20th-best return in our region, and the number of teams is still unknown (PLAN open question 7). With more than about 40 teams, the bar is above the field median and every pass rate here is optimistic.

### Finding 7: a few windows carry the score (no change)

- The top 1% of windows (22) give about 25% of the weighted CS sum; the top 5% give 59–72%. They come from 6–9 distinct episodes.
- This skew is the competition's own (14-day Sortino is heavy-tailed). Read compare intervals, not point gaps.

### Finding 8: blends score below their best sleeve → switch instead (section 5)

## 4. Changes on `feature/scoring-v2`

| Commit | What |
|---|---|
| `56905e4` | Engine: `fit_gross` (gross ≤ 100% after trades); harness cache keys on the engine code and every reachable model module |
| `3ab4e4b` | REL (proposed primary), field fingerprint in the tool version, stricter G4, compare blocks of 56 |
| `7ad0c9b` | Keep-alive trade (`harness.keep_alive_weight` 0.002); five blends; cache keys that follow sleeves transitively |
| `0dbb6e7` | Two switch orchestrators |
| docs | `docs/EVALUATION.md` section 7 and Pol's checklist column, `STRATEGY_GUIDE`, `PROJECT_MAP`, this report, the score reports |

Changes to Book's files: `backtest/scoring/*` (REL, fingerprint, G4, version), two of his tests (the pinned primary; the CASH and BTC_HOLD exact checks now set the keep-alive to 0, with a new keep-alive test), and the CASH/BTC_HOLD descriptions.

## 5. Combinations of existing methods

Every combination is a registered model (`src/models/pol/`, method `selector`). Its sleeves are existing models run on the same view, each with its own previous decision replayed, so the combination is view-only and passes G5. Sleeve parameters are YAML anchors to the sleeves' own blocks.

**Blends** (weights, netted, gross ≤ 1):

| Model | Sleeves | REL | Gate pass | REL comp. when passed | Median R |
|---|---|---|---|---|---|
| pol_combo_rb | BTC hold + ROT_EW, 50/50 | 1.152 | 33% | 3.54 | +0.64% |
| pol_combo_rt | ROT_EW + pol_trend_ls, 50/50 | 0.995 | 23% | 4.29 | −0.31% |
| pol_combo_ms_tl | pol_mom_ss + pol_trend_ls, 50/50 | 0.923 | 24% | 3.85 | −0.04% |
| pol_combo_all | all seven, equal | 0.630 | 25% | 2.57 | +0.42% |
| pol_combo_rtt | ROT_EW + pol_trend_ls + TREND_2, thirds | 0.597 | 18% | 3.29 | −0.18% |
| *for reference: ROT_EW* | | *1.324* | *35%* | *3.76* | *+0.54%* |
| *pol_trend_ls* | | *1.314* | *32%* | *4.15* | *+0.12%* |

- **The blends are faithful.** Each blend's 14-day R tracks the average of its sleeves' (correlation 0.97–0.99, mean gap about 0).
- **They lose on the gate, not on quality.** When a blend passes the gate, its composite is the highest (4.29). But averaging ROT_EW and pol_trend_ls, whose good windows do not coincide (correlation +0.42), drops the median R to −0.27%, below both. So the gate passes in 23% of windows instead of 35%.
- With an all-or-nothing gate, diversifying inside the book lowers the expected score.

**Switches** (one method in full at a time, by BTC's trend state). The rule is TREND_2's (40-day EMA, ±3% hysteresis), untuned and fixed before scoring:

| Model | In trend | Out of trend | REL | Worst R | STRESS worst | Lowest regime cell |
|---|---|---|---|---|---|---|
| **pol_switch_rt** | ROT_EW | pol_trend_ls (shorts) | **1.373** | −25.2% | −13.6% | −4.1% |
| pol_switch_rc | ROT_EW | cash (keep-alive) | 0.794 | −21.4% | −16.1% | −4.2% |

### Recheck of the leaders

| Model | V1 | V2 | V3 | V4 | REL | SCREEN REL | CONFIRM REL |
|---|---|---|---|---|---|---|---|
| pol_switch_rt | 1.454 | 1.362 | 1.287 | 1.388 | 1.373 | 1.89 | 1.06 |
| team_rot_ew | 1.317 | 1.327 | 1.323 | 1.331 | 1.324 | 1.36 | 1.36 |
| pol_trend_ls | 1.422 | 1.298 | 1.216 | 1.319 | 1.314 | 2.04 | 0.83 |
| team_btc_hold | 1.103 | 1.162 | 1.181 | 1.147 | 1.148 | 1.32 | 1.13 |
| pol_combo_rb | 1.130 | 1.158 | 1.169 | 1.151 | 1.152 | 1.60 | 1.22 |
| pol_mom_ss | 0.941 | 0.882 | 0.878 | 0.889 | 0.897 | 0.92 | 0.79 |

(SCREEN = windows starting 2022-07-01 → 2024-06-30, CONFIRM = 2024-07-01 → 2026-07-25; weights renormalized within each.)

Paired HEADLINE(REL) differences, 90% interval, blocks of 56:

| a − b | Difference | Interval | Share > 0 |
|---|---|---|---|
| pol_switch_rt − team_rot_ew | +0.049 | [−0.331, +0.620] | 68% |
| pol_switch_rt − pol_trend_ls | +0.059 | [−0.313, +0.651] | 66% |
| pol_switch_rt − team_btc_hold | +0.225 | [−0.214, +1.009] | 86% |
| **pol_switch_rt − pol_mom_ss** | +0.476 | **[+0.105, +0.937]** | 98% |
| **pol_trend_ls − pol_mom_ss** | +0.416 | **[+0.019, +0.751]** | 96% |
| team_rot_ew − pol_mom_ss | +0.427 | [−0.187, +0.948] | 87% |

**Reading:**
- MOM-SS is clearly beaten.
- The top three are not separable. The switch's lead comes from SCREEN (2022–24, where shorting in the downtrend paid); in CONFIRM, ROT_EW is ahead.
- **ROT_EW is the steadiest**: the same REL in both periods and under all four readings.
- I stopped adding variants here: every extra variant tried makes the best-looking one more likely to be luck.

## 6. Recommendations (team decisions)

1. **Sign off `docs/EVALUATION.md`'s checklist**, with my column: three changes (REL primary, G4, blocks of 56) and one new row (keep-alive).
2. **One decision rule.** Rank eligible models by HEADLINE(REL). Treat a gap whose 56-block interval includes 0 as a tie, broken by the STRATEGY_GUIDE §5 rule (consistency in SCREEN and CONFIRM). This amends TEAM_PLAN §4.3.
3. **Launch candidate.** Under that rule, ROT_EW's design: top-6 risk-adjusted momentum, equal weights, ≤ 3%/day book volatility. It is currently a field benchmark (method `reference`), so it needs a team-owned momentum copy with frozen parameters. pol_switch_rt is the alternative if we want short exposure in downtrends. **Drop MOM-SS** as the default.
4. **Live bot (E2):** the keep-alive trade and the guard, exactly as the engine does them.
5. **Teammates' models** (due Oct 1, 20:00 HKT): score with `--score` and compare against `pol_switch_rt` and `team_rot_ew`. Baitoey's `baitoey_tg_mom` (BTC-trend-gated momentum) is the closest relative of the switch and should be scored next.

## 7. Not done, and unverified

- **In-sample:** every model here was designed with 2020–2026 data in view. The holdout (from 2026-08-08) stays sealed until the launch model is frozen on Oct 3.
- The number of teams per region (which sets the real return bar) is UNVERIFIED.
- Whether the competition account allows shorts is UNVERIFIED until the test-key self-check (`python -m src.live.selfcheck --orders`) runs.
- Book's other branches (`feature/contracts-view-fields`, which needs all three reviewers, and `feature/teamplan-insample-note`) and Baitoey's `feature/mom-ss` were not reviewed here.
- Merging: `feature/scoring-v2` stacks on Book's branch, which stacks on `feature/harness`, `feature/roostoo-client` and `feature/book-part0`. `feature/selection-ladder` also edits `backtest/evaluate.py`; expect one small conflict there (the Simulator call).

## 8. Reproduce

```bash
cd /home/ubuntu/test/MiniMax/.worktrees/pol-scoring-v2
source /home/ubuntu/test/MiniMax/.venv/bin/activate
pytest -q                                                   # 137 passed
python -m backtest.scoring field                            # CASH + the six benchmarks
python -m backtest.run --model pol_switch_rt --score        # any model; reports/<model>/<stamp>-score.md
python -m backtest.scoring compare pol_switch_rt team_rot_ew
cat /home/ubuntu/test/MiniMax/results/scoring/leaderboard.md
```

The analysis scripts behind sections 3 and 5 are in `results/pol/20261001-scoring-review/` (`a1.py`–`a5.py`, not committed).
