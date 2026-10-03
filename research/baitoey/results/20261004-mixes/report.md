# Split the money between two models (scoring v2)

Pre-registration: `research/baitoey/prereg/20261004-mixes.md`. Two separate sub-accounts on the cached v2 paths,
method of Pol's endgame2.py. Main columns with the live lock-in on the whole account; the last two without it.

Check: e20v45's unmodified path gives HEADLINE_RET 0.5682 (score file 0.5682), CS_HIT 0.384 (0.384).

| Run | Money split | HEADLINE_RET | vs E0 | CS_HIT | ~150-team cut | Mean R | Worst R | Without lock: HEADLINE_RET / CS_HIT | Real rounds (falling R1 HK/SG · rising Final) |
|---|---|---|---|---|---|---|---|---|---|
| E0 | pol_switch_vt_tl_e20v45 alone | **0.608** | +0.000 | 0.470 | 0.390 | +4.0% | -26.2% | 0.568 / 0.384 | +3.4% #2/#5 · +0.2% #9 |
| X1-40 | 40% pol_switch_vt_tl_e20v45 / 60% pol_abl_shock | **0.613** | +0.005 | 0.452 | 0.345 | +3.9% | -22.6% | 0.587 / 0.366 | -0.4% #17/#11 · +6.9% #3 |
| X1-50 | 50% pol_switch_vt_tl_e20v45 / 50% pol_abl_shock | **0.617** | +0.009 | 0.450 | 0.350 | +3.9% | -23.2% | 0.587 / 0.365 | +0.2% #9/#7 · +5.7% #3 |
| X1-60 | 60% pol_switch_vt_tl_e20v45 / 40% pol_abl_shock | **0.614** | +0.006 | 0.464 | 0.368 | +4.0% | -23.7% | 0.576 / 0.380 | +0.9% #4/#6 · +4.6% #5 |
| X2-40 | 40% pol_switch_vt_tl_e20v45 / 60% pol_mr_cap | **0.543** | -0.065 | 0.427 | 0.216 | +1.7% | -18.2% | 0.537 / 0.356 | +0.2% #9/#6 · -0.3% #9 |
| X2-50 | 50% pol_switch_vt_tl_e20v45 / 50% pol_mr_cap | **0.551** | -0.056 | 0.432 | 0.232 | +2.1% | -18.7% | 0.540 / 0.359 | +0.8% #5/#6 · -0.2% #9 |
| X2-60 | 60% pol_switch_vt_tl_e20v45 / 40% pol_mr_cap | **0.556** | -0.052 | 0.448 | 0.258 | +2.5% | -20.1% | 0.539 / 0.369 | +1.3% #4/#5 · -0.2% #9 |
| X3-40 | 40% baitoey_vt_mom / 60% pol_mr_cap | **0.579** | -0.029 | 0.420 | 0.226 | +1.7% | -26.2% | 0.572 / 0.363 | -2.3% #24/#26 · +3.4% #6 |
| X3-50 | 50% baitoey_vt_mom / 50% pol_mr_cap | **0.586** | -0.022 | 0.424 | 0.234 | +2.1% | -27.0% | 0.579 / 0.361 | -2.4% #25/#26 · +4.5% #6 |
| X3-60 | 60% baitoey_vt_mom / 40% pol_mr_cap | **0.595** | -0.013 | 0.423 | 0.242 | +2.5% | -27.8% | 0.579 / 0.360 | -2.6% #28/#27 · +5.5% #4 |

- X1 (pol_switch_vt_tl_e20v45 + pol_abl_shock): 50/50 better, neighbours hold -> **PROPOSE**.
- X2 (pol_switch_vt_tl_e20v45 + pol_mr_cap): 50/50 not better, neighbours do not hold -> **KEEP E20V45 ALONE**.
- X3 (baitoey_vt_mom + pol_mr_cap): 50/50 not better, neighbours hold -> **KEEP E20V45 ALONE**.

Tool version: 3036a0d8bfdaa6a0.

Note (read with the verdict): X1-50 passes on the worst round (-23.2% vs -26.2%) with HEADLINE_RET +0.009, but its
~150-team cut share (the top-20 proxy) is 0.040 lower than E0 (0.350 vs 0.390) and its CS_HIT 0.020 lower (0.450 vs
0.470). In the real falling round it ranks #9/#7 instead of #2/#5; in the rising Final #3 instead of #9.
