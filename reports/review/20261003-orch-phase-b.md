# book_orch Phase B: no layer passes its keep rule, so nothing is registered (2026-10-03, Book)

| | |
|---|---|
| Pre-registration | `reports/review/20261003-prereg-orch.md` (`9f8640d`) |
| Phase A | `reports/review/20261003-orch-phase-a.md` (`71cfb2a`) |
| Hold-rule change | `d085fce` |
| Tool | `3036a0d8bfdaa6a0`. Every version on the scratch path; no registered run (none qualified) |
| Scratch outputs | `results/book/20261003-book-orch/` (`versions/<v>/score.json`, `phaseb.json`, `parity_A.json`, `ml_diag.json`) |
| Scoring lock | batch 4 had finished its Phase B (`551451c`) and no scoring lock was held, so the orch runs started then |

## 1. Parity of version A after the hold change: PASS

Between decisions the model now returns its last decision's targets unchanged, as `pol_abl_shock` does (team decision, option 1; DEVIATION D4).

| | A | baitoey_vt_mom | Tolerance |
|---|---|---|---|
| HEADLINE_RET | 0.60859 | 0.60874 | \|diff\| 0.00015 ≤ 0.003: **pass** |
| without post-holdout | 0.55626 | 0.55644 | |
| Median \|per-window R diff\| | 0.0 pp (2,061 of 2,298 windows identical) | | ≤ 0.02 pp: **pass** |
| Trades back to the daily targets between decisions (drift past the band) | 415, in 309 windows | 0 | reported |

**The 5 windows that contribute most to the A vs vt_mom difference** (w′ × bar flips / 3; they sum to −0.00015):

| Window start | Contribution | Bars flipped | R_liq: A vs vt_mom |
|---|---|---|---|
| 2024-10-04 | −0.000147 | STRICT −1 (bar +3.99%) | +3.84% vs +4.11% |
| 2021-06-19 | +0.0000004 | all three +1 | +0.09% vs −5.02% |
| 2021-06-21 | +0.0000004 | all three +1 | +5.03% vs −0.33% |
| 2021-06-20 | +0.0000004 | all three +1 | +4.37% vs −0.95% |
| 2021-01-28 | −0.0000000 | STRICT −1 | +36.99% vs +61.50% |

For reference, under the rejected drift hold the top 5 were post-holdout windows from 2026-07-27 to 08-05. Each lost all three bars (A −1.3% to −2.5% against vt_mom 0.0% to +1.1%), and together they explained the −0.028.

## 2. Phase B table (A is the reference; A equals vt_mom within the tolerance)

| | A | S | S-cash | P | X |
|---|---|---|---|---|---|
| Status | reference | layer test | report-only | report-only | layer test |
| HEADLINE_RET, full | **0.6086** | 0.6077 | 0.6073 | 0.6150 | 0.5969 |
| without post-holdout | 0.5563 | 0.5560 | 0.5554 | 0.5563 | 0.5408 |
| SCREEN | 0.4465 | 0.4383 | 0.4307 | 0.4247 | 0.4335 |
| CONFIRM | 0.5840 | 0.5896 | 0.5924 | 0.5894 | 0.5699 |
| HIT UP / DOWN | 0.804 / 0.376 | 0.800 / 0.380 | 0.790 / 0.390 | 0.785 / 0.413 | 0.784 / 0.375 |
| ALL_PERIOD_RET (natural weights, diagnostic) | 0.6028 | 0.6021 | 0.6019 | 0.6100 | 0.5914 |
| Mean / median / worst R | +2.98% / +1.26% / −30.8% | +2.60% / +1.00% / −28.9% | +2.19% / +0.78% / −26.8% | +2.43% / +1.16% / −27.4% | +2.84% / +0.92% / −27.9% |
| CS_HIT | 0.369 | 0.368 | 0.360 | 0.375 | 0.371 |
| Turnover; fees / E_0 per window | 3.60; 0.363% | 3.70; 0.373% | 3.82; 0.384% | 3.01; 0.303% | 4.45; 0.445% |
| Tactical uplift vs A (w′-weighted mean R_liq) | — | −0.05 pp | −0.12 pp | −0.54 pp | −0.09 pp |
| Extra costs vs A (fees + spread) | — | +0.011 pp | +0.024 pp | −0.069 pp | +0.096 pp |
| Guard-only share of active days | 48% | 47% | 47% | 49% | 36% |
| Band trades between decisions (excl. shock trades) | 415 | 740 (+1,355 shock trades) | 328 (+3,183 shock trades) | 205 | 451 |
| STRESS rebound / drop medians | +21.4% / −18.1% | +21.3% / −18.2% | +20.9% / −18.8% | +19.2% / −16.5% | +18.4% / −14.7% |
| Eligible (G1, G4, G5) | yes | yes | yes | yes | yes (G4: long-only run clean) |

**Not scored:**
- T, T-shuffled, ST and X-shuffled: the ML gate failed.
- C and C-maker: no layer passed, and ST does not exist.

**Shock, scored period:**
- 79 episodes and 200 trigger hours;
- 2,330 hours (166 days) with the rule active.

**Filter pass rate:** n/a (T dropped). From the ML diagnostics: 75.6% of held coin-decisions.

## 3. Keep rule (vs A)

| | K1 (full, SCREEN, CONFIRM) | K2 (DOWN; UP −0.02) | K3 (worst −2 pp) | K4 (turnover ≤ 1.25×) | K5 | K6 (C only) | K7 (rebound −1 pp) | Kept? |
|---|---|---|---|---|---|---|---|---|
| S | **FAIL** (full −0.0009, SCREEN −0.008, CONFIRM +0.006) | pass | pass (+1.9 pp) | pass (1.03×) | n/a | (0.624 vs 0.630) | pass (−0.07 pp) | **no** |
| X | **FAIL** (all three lower) | **FAIL** (UP 0.7835 vs 0.7843 limit) | pass (+2.9 pp) | pass (1.235×) | n/a (no ML) | (0.620 vs 0.637) | **FAIL** (−3.0 pp) | **no** |
| S-cash (report-only) | FAIL | pass | pass | pass | n/a | | pass (−0.5 pp) | — |
| P (report-only) | FAIL (SCREEN −0.022) | pass | pass | pass (0.84×) | n/a | | FAIL (−2.2 pp) | — |

**Combination C: empty, so nothing is registered**, as pre-registered.

## 4. Short sleeve X (no-ML candidates: coins in no up-trend)

| Item | Value |
|---|---|
| Activation | 803 of 2,311 16:00 decisions (35%) |
| Average sleeve size when active | 18.0% of equity |
| Hit rate of the shorts | **46.4%** of 3,361 short-days gained after costs |
| Fees paid by the sleeve | 0.091% of E_0 per window (1,407 windows had a sleeve) |
| Rebound windows, A vs X | median +21.4% vs +18.4% |

**Per rebound window (A vs X):**
- lower under X: 2021-07-17 (+14.4% vs +10.8%), 2022-01-24 (+14.2% vs +9.2%), 2022-03-15 (+18.6% vs +18.0%), 2023-03-10 (+19.5% vs +16.6%), 2025-04-09 (+23.3% vs +18.7%);
- identical (sleeve off): the other five.

**Reading:** the sleeve cuts the drop windows (median −14.7% vs −18.1%) and the worst fortnight. But it loses more often than it wins, pays 0.09% a window in fees, and gives back 3 pp in rebounds (squeeze risk).

## 5. ML diagnostics (report-only, not a gate; from the trained models, no retraining)

| Period | Pooled IC, mu3 (the gate's statistic) | a) Daily cross-sectional rank IC (t, days > 0) | b) Labels shuffled over the whole period [5–95%] | c) Labels shuffled within each day: seed 0 / mean [5–95%] |
|---|---|---|---|---|
| All (43,724 rows, 1,914 days) | +0.052 | **+0.020** (t +3.2, 52%) | +0.006 [−0.008, +0.008] | **+0.050** / +0.050 [+0.048, +0.051] |
| 2021 (from July) | +0.066 | +0.044 (t +2.0) | +0.001 | +0.050 / +0.052 |
| 2022 | +0.036 | +0.002 (t +0.1) | +0.002 | +0.027 / +0.033 |
| 2023 | +0.079 | +0.012 (t +0.8) | −0.008 | +0.077 / +0.078 |
| 2024 | +0.057 | +0.016 (t +1.1) | −0.027 | +0.058 / +0.059 |
| 2025 | +0.049 | +0.048 (t +3.5) | +0.024 | +0.036 / +0.037 |
| 2026 | −0.016 | +0.007 (t +0.4) | −0.004 | −0.015 / −0.012 |

**What it shows:**
- The within-day shuffle (c) keeps 0.050 of the 0.052 pooled IC, so almost all of it is market timing: the daily average return is predictable from the market-wide features.
- Coin picking (a) is +0.020 on average, significant overall (t 3.2) but concentrated in 2021 and 2025, and about 0 in 2022–2024 and 2026.
- The true null (b) is about 0, as it should be. Two single-year seed-0 values (2024, 2025) fall outside their 5–95% bands, which is chance.
- The 1-day forecast's daily rank IC is +0.008.

## 6. DEVIATIONS

1. **D1:** the adjustment's rescale shrinks only the upward tilts (it kept the pre-registered bounds). Not used, since T was dropped.
2. **D2:** the first model is retrained on 2021-07-01, by the rule; the pre-registration's "2021-06-01" was a miscalculation.
3. **D3:** the sleeve's candidates are `trend`, by the pre-registered rule for a failed gate.
4. **D4:** the hold rule. The drift hold failed parity (0.0277; median 0.11 pp), so it was replaced, on the team's decision, by returning the last decision unchanged. No engine change.

**Also noted:** `feature/book-batch4` was rebased after the merge `4dc473d`. The content merged here (`src/models/book/`, its tests) is identical to the rebased branch.

## 7. For Pol (not fixed here)

- **Trades back to stale targets.** `pol_abl_shock`'s cached run contains 333 trades away from any shock: the engine trades an hourly model back to its stale daily targets when a weight drifts past the band. That penalizes its score slightly. book_orch has the same mechanism: 415 such trades in A.
- **Hard-coded hour.** `pol_abl_shock` hard-codes its 16:00 UTC decision hour (`GRID_HOUR`).

## 8. Recommendation

**No orchestrator layer earns its place on vt_mom under the pre-registered rule.**
- **Keep `baitoey_vt_mom` alone.**
- **The shock rule is a tail-risk choice, not a return gain.** It improves the worst fortnight by 1.9 pp (halving longs) or 4.0 pp (cash), for −0.001 HEADLINE_RET and slightly more trading. The team can adopt it as a risk preference, outside this keep rule.
- **P scored the highest full-pool HEADLINE_RET (0.615),** but fails SCREEN and the rebound check. This is UNVERIFIED and would need its own pre-registration.
- **For an ML v2:** test the daily cross-sectional IC with a within-day shuffle control, not the pooled IC with a within-month shuffle.
