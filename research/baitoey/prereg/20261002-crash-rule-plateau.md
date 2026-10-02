# Pre-registration: robustness check of the crash rule (pol_abl_shock) under scoring v2 (Baitoey, 2026-10-02)

Written and committed before any run. Not edited after results exist; results go to
`results/baitoey/20261002-crash-plateau/` and a report committed under `research/baitoey/results/`.

## Question

`pol_abl_shock` (Pol) = `baitoey_vt_mom` unchanged, plus a crash rule checked every hour: if BTC has fallen at
least 5% over 4 hours at any hour of the last 24 hours, hold cash. It is a launch option: officially 0.607 (tool
`3036a0d8bfdaa6a0`), worst 14-day R_liq -26.8% against vt_mom's -30.9%. Its three settings (5%, 4 h, 24 h) were set
once and never nudged. Is the insurance robust to them?

## Runs

One setting changed at a time; everything else as in `config.yaml` (`models: pol_abl_shock`).

| Run | Change | Role |
|---|---|---|
| S0 | none | base: the registered run (read from the registry) |
| S1 / S2 | drop threshold 4% / 6% | neighbours |
| S3 / S4 | drop window 2 h / 8 h | neighbours |
| S5 / S6 | cash pause 12 h / 48 h | neighbours |

The window is fixed at 4 h in Pol's file, so S3 and S4 use `src/models/baitoey/_shock_window.py`, a research-only
subclass that reads the window from `shock_hours` (with 4 it is pol_abl_shock exactly, tested). Pol's file is not
changed. Scored one at a time with `score_model` like `--score`, not registered. Script:
`research/baitoey/shock_plateau.py`. Reference: `baitoey_vt_mom` (registered).

## Verdict (fixed now)

- **Score holds** if every neighbour passes the hard gates and has HEADLINE_RET >= S0 - 0.03 (the team's margin).
- **Insurance holds** if every neighbour's worst 14-day R_liq is above vt_mom's (-30.9%).
- **Robust** if both hold. Otherwise **not robust**, naming the runs that fail.
- Report-only: HEADLINE_RET without the post-holdout windows, hit rates in strong falls, mild falls, mild rises,
  strong rises and volatile windows, weighted median and mean R_liq, the two real-round replays, guard share, fees.

## Known limits, stated before running

- The crash rule was proposed after earlier results (exploratory, Pol's report `20261002-new-rules.md`).
- The post-holdout windows (Jul-Sep 2026) are in the pool and were already seen.
- Six comparisons: one neighbour falling short by chance is possible; the report shows all of them.
- No setting is changed because of this check before the launch decision.
