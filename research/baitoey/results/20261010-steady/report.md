# Steady vs bounce profits (exploratory, 2026-10-10)

```
TOP 20 by share of rounds that were steady and positive
model                          steady + bounce + negative steady med bounce med  all med     p10 typ. MDD steady in weak
team_cash                           18%      17%      65%      +0.0%      +0.0%    -0.0%   -0.0%     0.0%            14%
baitoey_mr_bbrsi                    17%      37%      46%      +0.0%      +0.9%    +0.0%   -3.6%     1.0%            12%
baitoey_tg_mom                      14%      36%      50%      +2.8%      +2.2%    -0.0%   -3.5%     3.4%            19%
pol_mom_ss                           9%      42%      49%      +5.0%      +3.3%    +0.1%   -6.1%     4.8%            19%
team_mom_ss25                        9%      42%      49%      +5.0%      +3.3%    +0.1%   -6.1%     4.8%            19%
pol_combo_ms_tl                      8%      41%      51%      +3.9%      +3.5%    -0.1%   -5.4%     5.0%            16%
team_trend_2                         7%      41%      52%      +1.9%      +5.4%    -0.1%   -6.7%     5.2%             0%
baitoey_mr_4h                        7%      47%      45%      +4.5%      +2.9%    +0.6%   -8.0%     5.3%             2%
pol_combo_rtt                        6%      42%      51%      +2.5%      +5.2%    -0.2%   -6.3%     5.8%             7%
pol_mr_cap                           6%      50%      44%      +3.8%      +2.2%    +0.5%   -5.9%     4.1%             2%
baitoey_btc_short_b2                 5%      25%      70%      +3.6%      +1.1%    -0.0%   -2.4%     1.7%             5%
baitoey_ovl_altbtc_b_dual            5%      40%      55%      +2.3%      +4.9%    -0.4%   -7.8%     6.6%             2%
pol_switch_rc                        4%      39%      57%      +0.0%      +9.7%    -0.0%   -9.4%     7.7%             0%
pol_combo_rt                         4%      45%      52%      +3.1%      +5.7%    -0.2%   -7.2%     6.4%             5%
baitoey_btc_short_a2                 4%      28%      69%      +2.6%      +1.0%    -0.0%   -2.2%     1.6%             2%
pol_switch3                          3%      45%      51%      +5.2%      +3.9%    -0.2%   -9.7%     7.2%             2%
baitoey_btc_short_c                  3%      26%      70%      +1.7%      +0.9%    -0.0%   -2.1%     1.1%             2%
baitoey_ovl_altbtc_b_e20             3%      45%      52%      +3.1%      +5.2%    -0.3%   -8.8%     8.1%             5%
pol_trend_ls                         3%      47%      51%      +7.5%      +4.4%    -0.1%   -7.1%     6.5%             5%
pol_switch_rot_mr                    2%      48%      50%      +5.1%      +7.5%    +0.0%  -10.9%     9.2%             0%

Reference models
model                          steady + bounce + negative steady med bounce med  all med     p10 typ. MDD steady in weak
pol_switch_vt_tl_e20v45              1%      50%      49%      +6.7%      +8.9%    +0.3%  -12.1%     9.8%             0%
baitoey_vt_dual                      1%      52%      48%      +5.6%      +8.1%    +0.5%  -10.0%     8.5%             0%
baitoey_vt_mom                       0%      54%      46%          -      +8.4%    +1.2%  -11.7%    10.1%             0%
baitoey_mr_4h                        7%      47%      45%      +4.5%      +2.9%    +0.6%   -8.0%     5.3%             2%
pol_mr_cap                           6%      50%      44%      +3.8%      +2.2%    +0.5%   -5.9%     4.1%             2%
pol_trend_ls                         3%      47%      51%      +7.5%      +4.4%    -0.1%   -7.1%     6.5%             5%
team_btc_hold                        1%      52%      47%     +12.2%      +6.3%    +0.6%  -11.4%     8.6%             2%
team_cash                           18%      17%      65%      +0.0%      +0.0%    -0.0%   -0.0%     0.0%            14%
baitoey_mjt_24_96_d                  1%      49%      51%      +5.4%      +5.8%    -0.1%   -9.8%     8.6%             0%
```

## Mean reversion + short blends

```
All 2,298 rounds (14 days)
  e20 (live)                                           steady +   1% | bounce +  50% | negative  49% | median +0.3%, p10 -12.1%, p90 +23.6%, typical MDD 9.8% || from our -6.6% (day 6, 180 rounds): finish >= 0% 23%, >= +1% 18%, median -6.8%, <= -10% 24%
  mean reversion 4h alone                              steady +   7% | bounce +  47% | negative  45% | median +0.6%, p10 -8.0%, p90 +5.9%, typical MDD 5.3% || from our -6.6% (day 6, 180 rounds): finish >= 0% 0%, >= +1% 0%, median -6.6%, <= -10% 26%
  mean reversion + volume alone                        steady +   6% | bounce +  50% | negative  44% | median +0.5%, p10 -5.9%, p90 +5.1%, typical MDD 4.1% || from our -6.6% (day 6, 180 rounds): finish >= 0% 1%, >= +1% 1%, median -6.2%, <= -10% 20%
  Pol switch3: calm MR / up momentum / down long-short steady +   3% | bounce +  45% | negative  51% | median -0.2%, p10 -9.7%, p90 +10.2%, typical MDD 7.2% || from our -6.6% (day 6, 180 rounds): finish >= 0% 7%, >= +1% 6%, median -7.0%, <= -10% 29%
  Pol switch3_cap (MR on capitulation volume)          steady +   2% | bounce +  48% | negative  51% | median -0.0%, p10 -8.9%, p90 +9.6%, typical MDD 6.4% || from our -6.6% (day 6, 180 rounds): finish >= 0% 6%, >= +1% 6%, median -6.4%, <= -10% 23%
  50% MR 4h + 50% long-short trend                     steady +  16% | bounce +  33% | negative  51% | median -0.1%, p10 -5.2%, p90 +7.0%, typical MDD 4.1% || from our -6.6% (day 6, 180 rounds): finish >= 0% 3%, >= +1% 2%, median -6.8%, <= -10% 13%
  50% MR + volume + 50% long-short trend               steady +  20% | bounce +  32% | negative  48% | median +0.2%, p10 -4.8%, p90 +6.1%, typical MDD 3.7% || from our -6.6% (day 6, 180 rounds): finish >= 0% 1%, >= +1% 1%, median -6.5%, <= -10% 11%
  50% MR 4h + 50% BTC failed-rally short               steady +  18% | bounce +  37% | negative  46% | median +0.3%, p10 -3.8%, p90 +2.9%, typical MDD 2.6% || from our -6.6% (day 6, 180 rounds): finish >= 0% 0%, >= +1% 0%, median -6.7%, <= -10% 11%
  50% MR 4h + 50% large-coin trend (24/96)             steady +  13% | bounce +  35% | negative  52% | median -0.2%, p10 -5.2%, p90 +6.7%, typical MDD 4.1% || from our -6.6% (day 6, 180 rounds): finish >= 0% 3%, >= +1% 3%, median -6.8%, <= -10% 12%
```
