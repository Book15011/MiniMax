# Pre-registration: a fast large-cap trend long/short family (Baitoey, 2026-10-10)

Written and committed before any code runs on data; not edited after results; no tuning after results.
Research only; the live bot is frozen (2026-10-10) and nothing here changes it.

## Why, and what is not used

A team observed in this round trades the five largest coins long or short on a fast trend signal and gained while
we lost (reconstruction on Book's branch, 25/33 trades matched; exact rules unknown). This study tests the **generic
method family** (trend-following on the majors, long or short, volatility-sized), a standard public technique; our
repo already holds a public version (Pol's `pol_ext_trend824`, EMA 8/24, scored 0.304 on v2). **No constant fitted
to that team's trades is used, no team is named, and no code is copied** (AGENTS.md rule 7). Parameters below are
chosen from first principles and fixed now.

## The model (baitoey_mjt_*)

- Universe: BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, XRPUSDT (the five most liquid; majors fall in a more orderly way and
  squeeze less than small coins: big-coin shorts reached +10% in only 1-3 of 25 weak cases, alts in 5-9).
- Signal per coin: s = EMA_fast / EMA_slow - 1 on hourly closes. |s| < 0.25% -> no position (a dead band below
  about half a typical hourly move, so near-zero signals do not flip the book and pay 0.1%+ fees each way).
- Weights: sign(s) / (30-day daily volatility), normalised to gross 1, each coin capped at 30%, then the whole book
  scaled down so its 30-day covariance daily volatility is at most 3% (the team's vt_mom risk budget). Gross <= 100%
  (AGENTS.md). Long when s > 0, short when s < 0.
- Spec band 0.05 (the team standard).

| Parameter | Values | Why |
|---|---|---|
| EMA pair (hours) | 6/24, 12/48, 24/96 | Three trend horizons, each slow = 4 x fast (fast enough to react, slow enough to filter noise). 6/24 reacts within a day, the speed this market rewarded; 12/48 and 24/96 test whether a slower filter avoids the bounces that cost our faster switches on 8-9 Oct. The public 8/24 is already scored. |
| Decision cadence | daily (16:00 UTC), every 6 hours (04, 10, 16, 22 UTC) | Daily is cheapest and matches the observed cadence; 6-hourly answers a bounce within hours (slow reaction was the failure mode on 8-9 Oct). |

Six models: baitoey_mjt_06_24_d, _06_24_6h, _12_48_d, _12_48_6h, _24_96_d, _24_96_6h.

## Scoring, reading and the recovery analysis

Each model: `backtest.run --model <name> --score2`. Reported: weak-board median / p10 / p90 and rank; all-window
median / p10 / p90; HEADLINE_RET, REL SCREEN / CONFIRM, gates G1-G6, turnover, fees; this round replayed on live
prices from 2026-10-04 12:00 UTC (Book's replay engine).

**Worth a forward paper test** if: weak-board conservative score above e20v45's, REL SCREEN and CONFIRM each >= 1.0
(above the field average), and no hard gate fails. Six variants are compared, so one may pass by chance.

Recovery for the rest of the round (from about day 6): past rounds where e20v45 was within 3 points of our loss on
day 6 (two starting points: -8.4%, the last reported live figure, and -11.6%, the cash-start replay on 10 Oct 03:00
HKT; the real figure is UNVERIFIED), then the last 8 days with (a) e20v45, (b) a switch to each variant, (c) a 70/30
e20v45 / variant blend (hourly return mix, rebalancing costs ignored). Reported: share finishing at +1% or better,
median, p10, p90, share at -15% or worse.
