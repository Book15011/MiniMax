# Pre-registration: model choice under the field-best bar (2026-10-01, written before any of it is scored)

**Why a new bar.** About 150 teams in our region (team estimate) means top 20 by return is the top 13%. The scoring bar becomes the field's best 14-day return in each window (`scoring.return_gate_stat: max`; the best of six benchmarks sits near their 86th percentile), floored at 0. The morning's median bar is reported alongside.

**Hypotheses:**
- H1: in up markets the bar is the best of BTC held, equal weight and the momentum rotations, so concentrated, fully invested momentum clears it more often than vol-capped books.
- H2: in down markets every benchmark loses and the bar is 0, so a sleeve that makes small steady gains or profits from falls (mean reversion, long/short trend) clears it with a high composite.

**New candidates.** Three switches; nothing else is added after results are seen. Sleeve parameters are the existing config blocks. The state is team_trend_2's BTC trend rule (40-day EMA, ±3% hysteresis), untuned. `prev: own`.

| Model | BTC in trend | Out of trend | Decisions |
|---|---|---|---|
| pol_switch_rmax_tl | baitoey_rot_max (top 4, fully invested) | pol_trend_ls (long/short) | 24 h |
| pol_switch_rot_mr | team_rot_ew | baitoey_mr_bbrsi on 4-hour bars (MR_4h) | 4 h |
| pol_switch_rmax_mr | baitoey_rot_max | MR_4h | 4 h |

**Compared with:** every registered model of every member, and Baitoey's chosen study variants (MR_4h, DIP_4h, CORE_4h, VT_B0_4h, VT_C_24h), all rescored on the same tool version.

**Decision rule for the launch recommendation:**
1. Eligible: G1–G6 pass.
2. Robust: REL ≥ 1.00 in all four layers (headline, live-like only, recency only, flat), each against the field in that layer.
3. Rank by HEADLINE REL under the field-best bar.
4. Take the top model, unless its 90% interval against the runner-up (blocks of 56) includes 0. In that case take the one with the higher min(SCREEN REL, CONFIRM REL).
5. Report-only, for the top three: REL under the median bar, and a broad-universe run (every panel series, including coins that died: the survivorship check).
