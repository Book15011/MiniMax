# Pre-registration: plateau check of baitoey_vt_mom under scoring v2 (Baitoey, 2026-10-02)

Written and committed before any run. Not edited after results exist; results go to
`results/baitoey/20261002-vt-plateau/` and a report committed under `research/baitoey/results/`.

## Question

`baitoey_vt_mom` leads the scoring-v2 leaderboard (HEADLINE_RET 0.609, tool version `3036a0d8bfdaa6a0`). Its
settings were fixed before testing (`20261001-volume-timing.md`) but never nudged. Is 0.609 a plateau (nearby
settings score about the same) or a peak (part luck)? And how much do the volume rule and the 7/14-day lookbacks add?

## Runs

One setting changed at a time; everything else as registered in `config.yaml` (`models: baitoey_vt_mom`).

| Run | Change | Role |
|---|---|---|
| P0 | none | base: must reproduce the leaderboard's 0.609 |
| P1 | `early_exit: false` (volume rule off) | ablation: what the volume rule adds |
| P2 | lookbacks 3/7/14 (ROT_EW's) | neighbour |
| P3 | top 4, kept while in the top 8 | neighbour |
| P4 | top 8, kept while in the top 16 | neighbour |
| P5 | lookbacks 5/10 | neighbour |
| P6 | lookbacks 10/21 | neighbour |
| P7 | exit volume ratio 1.25 | neighbour |
| P8 | exit volume ratio 2.0 | neighbour |
| P9 | ban after a breakdown 12 h | neighbour |
| P10 | ban after a breakdown 48 h | neighbour |
| P11 | volatility cap 2%/day | neighbour (4.5% is already scored: 0.616) |

The keep rank stays at twice the number held, as in ROT_EW. Run in this order, one at a time (the harness uses
up to 8 workers), with `score_model` exactly as `--score` runs it, but not registered: nothing reaches the
leaderboard. Script: `research/baitoey/vt_plateau.py`.

## Verdict (fixed now)

- **Plateau** if every neighbour (P2-P11) passes the hard gates and has HEADLINE_RET >= P0 - 0.03 (the team's tie
  margin). Otherwise **peak**, and the report names the settings that fall off.
- P1 is reported as the volume rule's contribution (P0 - P1); it is not part of the verdict.
- Report-only for every run: HEADLINE_RET without the post-holdout windows, hits on the three bars, hit rate in
  strong falls and strong rises (the leaderboard's market types), weighted median and mean 14-day R_liq, worst R_liq,
  the two real-round replays with ranks, guard share of active days, turnover and fees.

## Known limits, stated before running

- The post-holdout windows (Jul-Sep 2026) are in the pool and were already seen; the in-sample column shows the
  result without them.
- Eleven comparisons: one neighbour falling below the margin by chance is possible; the report shows all of them.
- Universe = coins Roostoo lists today (survivorship; flatters momentum), as for every model on the leaderboard.
- No setting is changed after this check because of its results, before the launch decision.
