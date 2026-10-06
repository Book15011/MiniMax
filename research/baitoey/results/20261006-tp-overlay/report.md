# Take-profit overlay on baitoey_vt_mom: verdict

Pre-registration: `research/baitoey/prereg/20261006-tp-overlay.md` (with its pre-run addendum on guard trades).
Per-period tables: `report-SCREEN.md` (committed before CONFIRM ran) and `report-CONFIRM.md` (run once).
A reproduces vt_mom's registered period_check exactly (SCREEN 1.0292, CONFIRM 2.5616).

| Variant | SCREEN REL vs A | SCREEN median | CONFIRM REL vs A | CONFIRM median | Better in both? |
|---|---|---|---|---|---|
| A: no take-profit | 1.029 | +0.34% | 2.562 | +0.10% | — |
| B: 8%, all | -0.173 | +0.45% | -1.384 | -0.97% | no |
| C: 12%, all | -0.264 | +0.29% | -1.444 | -0.34% | no |
| D: 8%, half | -0.160 | +0.48% | -1.267 | -0.53% | no |

**Verdict: keep vt_mom without a take-profit.** No variant is better in either period.

- The take-profit cuts the winning rounds: the 90th percentile fortnight return falls from +17.2% to +11.7% (B) in
  CONFIRM and from +15.9% to +14.0% in SCREEN. Those rounds carry REL.
- After a fill, the coin is about as often higher as lower at the next decision (CONFIRM B: 3,609 higher, 3,581
  lower; SCREEN B: 2,944 / 3,358), so selling at the target adds no edge but adds fees (+0.10% to +0.19% per round).
- Limits: an overlay on the registered paths. Five 2025 listings in CONFIRM (ASTER, AVNT, PUMP, WLFI, XPL) have no
  hourly klines and use the close instead of the high, so their orders fill less often. Roostoo's limit matching is
  UNVERIFIED.
