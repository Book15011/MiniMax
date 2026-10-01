# Pre-registration: return-maximizing versions of team_rot_ew (Baitoey, 2026-10-01)

Written and committed before any run of these variants. Not edited after results exist; results go to
`results/baitoey/20261001-rot-max-study/`.

## Question

The score is return first (a window counts only if it beats the field median and 0). Do fully invested, more
concentrated versions of the ROT_EW rotation pass the return gate more often and score higher REL than ROT_EW,
and what do they cost in risk?

## Variants

Code: `src/models/baitoey/baitoey_rot_max.py` (reuses `team_rot_ew.rotation_targets`). Parameters: `config.yaml`
→ `models: baitoey_rot_max`. Common to all: ROT_EW’s score (mean over 3, 7 and 14 days of return over volatility
of the span), keep a holding while it ranks in the top 12, equal weights, long only, daily decision at 16:00 UTC,
5-point band, harness costs, guard and keep-alive (tool version `ce40153`).

| Variant | k (coins held) | Gross | Volatility cap | Gate |
|---|---|---|---|---|
| A | 6 | 1.0 | none | none |
| B | 4 | 1.0 | none | none |
| C | 3 | 1.0 | none | none |
| D | 4 | 1.0 | none | all cash when BTC closed below its 20-day average at the decision hour on 2 days in a row |

- No volatility cap: `target_daily_vol` = infinity, so ROT_EW’s scaling never shrinks the book (gross 1.0).
- D’s gate: daily closes are the closes 24 h apart ending at the decision; the 20-day average includes that day;
  the gate is checked again at every daily decision (no memory). Missing BTC data leaves the gate open.

## The only choice made on SCREEN

SCREEN = windows starting 2022-07-01 … 2024-06-30 (16:00 UTC). A–D are ranked on four SCREEN scores (higher is
better): share of windows passing the return gate, median 14-day return R, 75th percentile R, worst-10% R. The
lowest mean rank is the preferred candidate; a tie goes to the lower turnover. No parameter is varied. Phase 1
(`python -m research.baitoey.rot_max_study screen`) prints only SCREEN numbers and writes `choice.json`.

## The one CONFIRM look

Phase 2 (`... rot_max_study confirm`) runs once, after `choice.json`. For A–D and team_rot_ew: median, 75th and 90th
percentile R and worst-10% R on SCREEN and CONFIRM (windows from 2024-07-01), the share of windows passing the
return gate, REL (HEADLINE REL FLOORED), gates G1–G6, exchange fees and spread as % of equity per window, and
`compare` against team_rot_ew (paired REL CS difference, 90% block-bootstrap interval, blocks of 56). REL leans on
2025–26 windows, so it is part of this look and is not used for the choice. Report-only robustness: REL of the
live-like layer, the recency layer and the flat mean. Nothing changes after phase 2; the holdout stays sealed.

## Expected risks, stated before running

- Without the volatility cap, G2 (worst fortnight better than BTC_HOLD’s) and G3 (no regime cell median below −10%)
  may fail, especially for C (3 coins).
- Universe = coins Roostoo lists today (survivorship flatters momentum, more so for concentrated books).
