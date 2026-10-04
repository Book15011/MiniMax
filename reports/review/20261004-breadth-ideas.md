# Breadth ideas A, B, C on top of H1: all three NOT BETTER than H1 (2026-10-04, Book)

| | |
|---|---|
| Pre-registration | `reports/review/20261004-prereg-breadth-ideas.md` (`105ded0`), committed before any code or run |
| Code | `47bba00`: gates `breadth_hyst` (B) and `breadth_drop` (C), the emergency early decision (A); off by default, with tests (312 passed) |
| Scratch runs | A 0.6175 (95 minutes), B 0.6187 (22 minutes), C 0.6100 (24 minutes), in `results/book/20261004-breadth-ideas/versions/` |
| Analysis | `ideas.py`, `ideas.json`; hourly breadth from `breadth_hourly.py` (not committed) |
| Not done | registration, any change to the live bot; no writes to `data/` |

**Already tried?** No. The search before the pre-registration found:
- no early decision on a breadth collapse;
- no hysteresis on breadth (only on the BTC switch);
- no breadth-change rule.

All three ideas were new, and each was tested at one setting (no grid).

**Result:** none of A, B or C is BETTER THAN H1. H1 stays the control.
- **B** (hysteresis 0.55 / 0.65) comes closest: its point estimates are a little better, and it is statistically
  ahead of H1 in views (a) and (b). But its 5th-percentile R and 90th-percentile drawdown are worse by 0.005 pp and
  0.003 pp, so it fails rule 3.
- **A** (emergency trigger) changes almost nothing.
- **C** (drop) clearly loses.

## 1. Decision table

Each cell gives the score and its rank among the 7, then the bootstrap label against H1 / against vt_mom (90%,
month blocks).

| | **A emergency** | **B hysteresis** | **C drop** | H1 (control) | E5 | vt_mom | Live: e20v45 |
|---|---|---|---|---|---|---|---|
| (a) as now | 0.618 (#2) tied / tied | **0.619 (#1)** **ahead** [+0.000, +0.004] / ahead | 0.610 (#4) tied / tied | 0.617 (#3) | 0.583 (#6) | 0.609 (#5) | 0.568 (#7) |
| (b) without post-holdout | 0.561 tied / tied | 0.563 **ahead** / ahead | **0.565 (#1)** tied / ahead | 0.561 | 0.564 | 0.556 | 0.501 |
| (c) years equal | 0.511 tied / tied | **0.515 (#1)** tied / ahead | 0.512 tied / tied | 0.511 | 0.504 | 0.510 | 0.461 |
| (d) UP only | 0.804 tied / tied | 0.804 tied / tied | 0.802 tied / tied | 0.803 | 0.774 | **0.805** | 0.699 |
| (e) DOWN only | 0.396 tied / tied | 0.398 tied / ahead | 0.382 **behind** [−0.027, −0.001] / ahead | 0.396 | 0.357 | 0.376 | **0.412** |
| SCREEN / CONFIRM | 0.453 / 0.589 | 0.450 / 0.593 | 0.447 / 0.596 | 0.448 / 0.593 | 0.453 / 0.597 | 0.447 / 0.584 | 0.430 / 0.502 |
| Worst day | −14.7% | −14.7% | −14.6% | −14.7% | −14.7% | −14.7% | −15.4% |
| Worst R | −30.04% | −30.04% | −30.84% | −30.04% | −29.74% | −30.84% | **−26.11%** |
| 5th-percentile R | −14.99% | −14.94% | −15.33% | −14.94% | **−14.80%** | −15.73% | −15.34% |
| Max drawdown, median / 90th percentile | 9.8% / 17.97% | 9.8% / 17.96% | 10.1% / 18.55% | 9.8% / 17.96% | 9.7% / 17.91% | 10.1% / 18.71% | 9.8% / 18.93% |
| Longest losing streak | 12 days | 12 | 12 | 12 | 12 | 12 | **9** |
| Single-coin blow-up share | 3.57% | **3.48%** | 3.83% | 3.52% | 3.66% | 3.96% | 7.27% |
| Fees per window / turnover | 0.351% / 3.48 | 0.349% / 3.46 | 0.359% / 3.56 | 0.349% / 3.46 | 0.341% / 3.38 | 0.362% / 3.59 | 0.531% / 5.31 |
| Windows whose R differs from H1 | 578 | 333 | 1,647 | 0 | 1,574 | 1,879 | 2,296 |

## 2. Rule against H1 (pre-registered)

| Rule | A emergency | B hysteresis | C drop |
|---|---|---|---|
| 1. HEADLINE_RET higher in full, SCREEN, CONFIRM | **fails**: CONFIRM 0.5890 vs 0.5933 | passes: 0.6187 / 0.4497 / 0.5933 vs 0.6173 / 0.4480 / 0.5933 | **fails**: full 0.6100, SCREEN 0.4473 |
| 2. Not behind H1 or vt_mom in any view | passes (tied everywhere) | passes (ahead of H1 in a, b) | **fails**: behind H1 in (e) |
| 3. Worst R, 5th pct R, p90 MDD, blow-up no worse | **fails**: 5th pct, p90 MDD, blow-up | **fails**: 5th pct −14.942% vs −14.937%; p90 MDD 17.964% vs 17.962% | **fails**: all four |
| 4. Worst day, streak | passes | passes | passes |
| 5. Turnover and fees ≤ 1.10 × H1 | passes | passes | passes |
| **Label** | **NOT BETTER** | **NOT BETTER** | **NOT BETTER** |

## 3. How the ideas behaved

**Staging share at 16:00 decisions:**
- H1: 57.4%;
- B: 56.9% (B differs from H1 only at readings of 0.55 and 0.60);
- C: 12.4% (it stages only when breadth is both low and falling).

**A's trigger:** in the hourly breadth series it fires 123 times in 6.3 years (about 20 a year), spread over all hours.
It changes 578 windows. The early decision trades new entries at the trigger hour, and that costs a little in
falling windows (−0.11 pp per window vs H1).

**Gap vs H1 by market type**, mean R per window in pp:

| | UP (1,003) | DOWN (808) | Flat (487) |
|---|---|---|---|
| A | −0.01 | −0.11 | −0.02 |
| B | +0.01 | −0.01 | +0.00 |
| C | **+0.14** | **−0.19** | +0.03 (HIT −0.032) |

**Reading:**
- **C** gives back much of H1's protection in falling markets, for a small gain in rising ones.
- **B** is H1 with a slightly different boundary.
- **A**'s hourly emergency acts too rarely, and at the wrong moments, to help.

## 4. Appendix: H1 with the live lock-in (report-only, asked during the round)

The rule as configured on the live bot: from day 10, at +3%, sell everything and hold cash. The script reproduces
Pol's and Baitoey's published lock-in numbers exactly (vt_mom 0.6371, e20v45 0.6079, and their CS_HIT and ~150-team
cut). Script and output: `results/book/20261004-breadth-ideas/h1_lockin.py`, `h1_lockin.json`.

| With lock-in | HEADLINE_RET | vs e20v45 + lock-in | CS_HIT | ~150-team cut | Worst R | Mean R |
|---|---|---|---|---|---|---|
| H1 | **0.6445** | +0.037 [−0.005, +0.083], tied | 0.440 | 0.370 | −30.1% | +4.11% |
| e20v45 (live) | 0.6079 | — | **0.470** | **0.390** | **−26.2%** | +3.99% |
| vt_mom | 0.6371 | +0.029, tied (behind H1 + lock-in) | 0.433 | 0.351 | −30.9% | +3.96% |
| pol_abl_shock | 0.6367 | +0.029, tied | 0.431 | 0.348 | −26.8% | +3.86% |

## 5. Caveats (UNVERIFIED)
- **Same data:** the ideas came from the team's notes after H1 was found on these same 2,298 windows. In-sample.
- **B's edge is tiny:** +0.0015. Being "ahead" reflects how little B changes, not a large effect.
- **A has no live test.** Its emergency decision has not run in shadow mode.

## 6. Recommendation
- **Keep H1 as it is.** None of the three ideas passes the rule fixed before computing.
- **The code stays in `book_orch`, off by default.** It is tested, and turning any of it on would need a new
  pre-registered test.
