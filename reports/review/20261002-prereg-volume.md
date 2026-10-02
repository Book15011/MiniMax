# Pre-registration: volume variants (2026-10-02, Pol), written before any of them was scored

**Status: exploratory.** The ideas come from a signal study (`results/pol/20261002-volume/vol_ic.py`, `vol_topk.py`,
`vol_regime.py`, `vol_timing.py`) on 2021-2026 data, which overlaps the harness windows. A pass here is weaker evidence
than the 2026-10-01 picks; it can change the launch pick only through the rule below.

## Variants (parameters fixed from the study's a-priori bins, not tuned on the harness)

| Model | Change vs its base | Base |
|---|---|---|
| `pol_vt_mvr` | book x 0.5 while the universe's 24 h quote volume < 0.85 x its 30-day daily average | `baitoey_vt_mom` |
| `pol_mr_cap` | new entries only while the coin's 24 h volume > 1.0 x its 7-day normal | `baitoey_mr_4h` |
| `pol_switch_vtm_tl` | up-state sleeve = `pol_vt_mvr` | `pol_switch_vt_tl` (launch pick) |
| `pol_switch3_cap` | calm-state sleeve = `pol_mr_cap` | `pol_switch3` |

## Rule

1. Each variant is compared with its base on the same tool version: four-bar rule of `20261001-prereg-realtest.md`
   (eligible + robust, mean rank over median / q67 / q83 / best bars, ties within 0.5 by min(SCREEN, CONFIRM)).
2. A variant **replaces the launch pick** only if it is eligible and robust, ranks above `pol_switch_vt_tl` by that rule,
   and is not worse than its own base in either SCREEN or CONFIRM on the best bar.
3. Otherwise it is recorded as a negative or neutral result. No re-tuning of the thresholds after scoring.
