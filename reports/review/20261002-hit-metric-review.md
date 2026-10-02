# Review of Book's return-first pre-registration (`feature/return-first` 0e9280b), Pol, 2026-10-02

Reviewed: `reports/review/20261002-prereg-return-first.md` (the code is not written yet). To see what the rule does
before Book's run, I approximated it on the existing score files (`results/pol/20261002-volume/hit_preview_book.py`):
16:00 starts, plain R instead of R_liq, v1 weights with Book's direction rebalance (pi_up 0.534), and his three bars
(LENIENT -1.4965% DOWN / 0% UP, MIDDLE 0%, STRICT max(0, median of the six)). Book's own run will differ in detail.

## Agreed

- Return first, risk second, exactly as the competition ranks. R_liq (the system liquidates at the end), the
  direction rebalance, month-block bootstrap ties, 12:00 UTC starts, holdout shown with and without, benchmarks and
  CASH as reference rows, the independent recomputation and the expectations written in advance: all good.
- G6 median-of-20 straddling 10 crashes and 10 rebounds is a fair criticism.
- The design handles CASH: in the approximation CASH scores 0.329, second to last (LENIENT 0.685, MIDDLE 0.239,
  STRICT 0.062), so "do nothing" cannot win. (My first preview, before the pre-registration was on the server, used
  a looser reading and ranked CASH first. That was wrong and is withdrawn.)

## Main point: the bars assume a ~50-team field

-1.4965% is the #20 return of fields of 47 and 55 teams, the top 36-43%. Our region has about 150 teams (team
estimate), where #20 is the top 13%. Taking the same quantile in the same leaderboards:

| Round (market) | Teams | #20 return | Top 13% (≈ #20 of 150) |
|---|---|---|---|
| 455 (falling) | 47 | -1.42% | +0.60% |
| 456 (falling) | 55 | -1.57% | -0.00% |
| 469 Final (rising) | 16 | n/a | +8.08% (thin sample) |

If the field is ~150, LENIENT DOWN should be about 0%, which makes it the same as MIDDLE. In UP windows, all three
bars sit at or below 0% / the benchmark median, far below where the real cut was. Suggestion: write down the expected
field size in the pre-registration as a DEVIATION or an assumption. If it is ~150, either set LENIENT DOWN = 0% or
report the headline both ways, and add a field-relative UP bar (q83 or best of the six, Pol's bars, which bracket the
real cut). The approximation shows what is at stake:

| Model (approximate) | HEADLINE_RET (Book's bars) | HIT at a ~150-team cut (DOWN +0.6%, UP best-of-six) |
|---|---|---|
| baitoey_vt_mom | **0.531** | 0.237 |
| team_btc_hold (ref) | 0.518 | 0.238 |
| pol_mr_cap | 0.514 | 0.245 |
| baitoey_mr_bbrsi | 0.486 | 0.119 |
| baitoey_mr_4h | 0.475 | 0.243 |
| baitoey_rot_max | 0.459 | **0.265** |
| pol_switch_vt_tl (launch pick) | 0.425 | 0.232 |
| team_cash (ref) | 0.329 | 0.000 |

At the ~150-team cut every serious model clears it in roughly 23-27% of windows. The spread is small, so the
bootstrap tie group will be wide: the risk tie-break and the real-market checks will decide more than HEADLINE_RET.

## Smaller points

1. **Score the volume models too (Book's DEVIATION).** `feature/volume` sits on the same base (f9bbc15) and only adds
   files plus appended config blocks, so `git merge feature/volume` in `book-return-first` should be clean. It
   brings `pol_mr_cap`, which passes G6 in both forms anyway (stress median +0.11% vs BTC -0.67%), and the live
   feed's ticker-volume fix. Book's call; I have not touched his branch.
2. **UP windows have two identical 0% bars** (LENIENT and MIDDLE), so a +0.01% rally window counts twice. It is
   intended as an assumption, but under a ~150-team field it rewards near-flat returns in rallies (BTC_HOLD HIT_UP is
   1.0 by construction).
3. **Near-zero noise.** With R_liq >= 0% as a bar, keep-alive noise of +-0.07% decides hits for low-exposure models;
   a 0.05-0.1% tolerance would remove that.
4. **Tails.** With G2/G3/G6 report-only, nothing hard stops a model whose rare losses are large. The tail table is a
   good start; consider one hard floor (e.g. 5th-percentile R not below BTC hold's).
