# Pre-registration: Pol's models under scoring v2, and two robustness checks of v2 (2026-10-02, Pol), before any run

Branch `feature/v2check` = Book's `feature/return-first` (4371453) + `feature/volume` (048c90a), merged locally,
not pushed; tool version `3036a0d8bfdaa6a0` (checked equal to Book's). Book's branch is not changed.

1. **Rescore (registered), resolving DEVIATION 1 of `20261002-return-first.md`:** `pol_switch_vt_tl_e20v45`,
   `pol_mr_cap`, `pol_vt_mvr`, `pol_switch_vtm_tl`, `pol_switch3_cap`. They enter Book's pick order as written.
   No new selection: these models and their parameters were fixed before v2 existed.
2. **Sensitivity, report-only (not registered):** `baitoey_vt_mom` (v2's pick on the full pool) with its momentum
   volatility cap at 4.5%/day instead of 3% (`pol_sens_vtv45`), the change that improved the switch under v1. A
   finding for after the round, not a change of pick.
3. **Robustness of the v2 ranking, report-only** (`results/pol/20261002-v2check/v2_robust.py`, recomputed from the
   score.json per-window tables with Book's w', bars and month bootstrap):
   a. a 0.1% tolerance on every bar (R_liq >= bar + 0.001): removes hits made by keep-alive noise around 0%;
   b. LENIENT DOWN = 0% instead of -1.4965%: the same quantile of a ~150-team field (20261002-hit-metric-review.md);
   c. both.
   Read: if the top model and its tie group are unchanged under a-c, the pick is robust to these two choices; if
   not, the team should know which choice decides it. Nothing here changes Book's pre-registered rule.
