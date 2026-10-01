# Pre-registration: real-market checks, two new switches, a trading-volume study (2026-10-01, before any of it is run)

## What the real leaderboard changed

Roostoo's public `/v1/leader_board` gives the previous edition's final returns (numbers only; no names or personal fields were kept).

| Round | Ranked teams | #1 | #5 | #10 | #20 | Median |
|---|---|---|---|---|---|---|
| Round 1 HK (10 days) | 47 | +6.8% | +0.8% | +0.0% | −1.4% | −2.4% |
| Round 1 SG (10 days) | 55 | +10.8% | +0.9% | −0.2% | −1.6% | −2.8% |

The real top-20 cut sat between our median bar (0% that week) and our field-best bar (+1.3%). So the true bar is uncertain.

## Amended decision rule (applies to the launch recommendation from now on)

1. Eligible (G1–G6) and robust (REL ≥ 1.00 in every layer on the field-best bar).
2. Rank by the **mean rank across four bars**: the six benchmarks' median, 67th percentile, 83rd percentile and best, each floored at 0.
3. Ties (mean ranks within 0.5): the higher min(SCREEN REL, CONFIRM REL).

## New candidates (no others will be added after results)

Both use `prev: own`, untuned state rules and the sleeves' existing parameters.

| Model | States | Decisions |
|---|---|---|
| pol_switch3 | calm BTC (Baitoey's rule: 30-day vol below its 1-year median) → MR_4h · up (team_trend_2's rule) → baitoey_vt_mom · down → pol_trend_ls | 4 h |
| pol_switch_vt_tl | up → baitoey_vt_mom · down → pol_trend_ls | 24 h |

## Trading-volume study (report-only)

The real leaderboard's top 20 traded 3–4× their capital in 10 days, against 7–14× for the median team.

**Grid:**
- `baitoey_vt_mom` and `pol_switch_rmax_tl`
- band ∈ {0.01, 0.10} and rebalance ∈ {72 h}, against their defaults

**Report:** turnover and REL under the four bars.

**Adoption rule:** a variant replaces its default only if it beats it under all four bars and in SCREEN and CONFIRM.

## Real-market checks (report-only, no re-ranking)

1. **Replay of the previous edition's real windows** (Mar 21–31 and Apr 4–14), ranked among the real teams' returns. Done for the existing models; it will be repeated for the new ones.
2. **The sealed holdout** (windows ending after 2026-08-08 16:00 UTC; never used for any choice), opened now at the team's request.
   - **Models:** baitoey_mr_4h, baitoey_vt_mom, pol_switch_rmax_tl, pol_switch_rmax_mr, pol_trend_ls, pol_switch3, pol_switch_vt_tl, team_rot_ew, pol_mom_ss and the six benchmarks.
   - **Report:** median R, worst R, and the share of windows clearing each bar.
   - **Flag:** a model that clears the field-best bar less often than BTC_HOLD in the holdout.
3. **The test account** (live fills, fees, order sizes), when the test key is in `.env`.
