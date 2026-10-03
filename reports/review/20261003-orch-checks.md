# Read-only checks on book_orch v2 (2026-10-03, Book)

| | |
|---|---|
| Plan and decision rules | `reports/review/20261003-orch-checks-plan.md` (`f2ee1d4`), committed before anything was computed |
| Inputs | the stored v2 forecasts (`validation/book_orch_v2_forecasts.json`); A′ and E's saved per-window outputs and trade logs; `data/`, read-only |
| Not done | training, scoring runs, registration, downloads, Roostoo calls, writes to `data/` |
| Scripts and outputs | `results/book/20261003-orch-checks/` (`check1.py` … `check6.py`, `check<n>.json`). Every job ran in under 20 s |

## Conclusions

| Check | One line |
|---|---|
| 1. Volatility-controlled ranking | **Rule fails: stop the ML line.** Within each volatility third, high-q coins earn slightly *less* than low-q coins (0 of 3 groups positive, 0 of 4 years). A low-q filter would also have removed A′ picks that did *better* |
| 2. Overextended entries | **No sell signal.** The most extended entries did best on average (daily RSI > 80: +9.3% over 7 days, t 2.3), with deeper worst drops (−14% vs −9%). Per-year signs are mixed |
| 3. Breakdown shorts | **Rule fails: no short rule.** Every variant loses at every horizon (−0.45% to −0.67% net at 24 h, t −3 to −11), with 90th-percentile bounces of +8% (24 h) and +15% (72 h) |
| 4. Behaviour vs rules | **Trading matches the rules.** The only anomalies: two exits of coins that left the universe carry no log record (the trades are correct), a misleading reason text for E's window-start stages, and window-start churn in 10.5% of windows |
| 5. Fees | About 0.36% of E₀ per window. Two thirds come from 16:00 decisions and exits. Guard trades are 68% of A′'s trades but 7% of its fees. Maker-fee upper bound: 0.17% per window (UNVERIFIED) |
| 6. Data | **No tokenized stocks.** The equity index is the S&P 500 via FRED, daily from 2016-09-30. FRED series are point-in-time only with a one-day lag (and CPI with its release lag) |

## 1. Is the ranking skill worth money once volatility is controlled?
- **Data:** 46,546 hours and 880,816 coin-hours.
- **Method:** every hour, coins are split into volatility thirds; within each third, the top half by q is compared with the bottom half.
- **Units:** "raw" is the 8-hour return in %; "risk-adjusted" is r_8 / σ8. t-stats use day blocks.

| Group | Raw spread (t) | Risk-adjusted (t) | IC within group (t) | Raw spread, 2023 / 2024 / 2025 / 2026 |
|---|---|---|---|---|
| Low volatility | −0.006% (−0.6) | −0.002 (−0.4) | +0.025 (5.8) | +0.003% / −0.027% / −0.002% / −0.035% |
| Mid | −0.007% (−0.5) | −0.004 (−0.9) | +0.023 (6.0) | −0.024% / −0.016% / −0.009% / −0.056% |
| High | −0.023% (−1.0) | −0.007 (−1.5) | +0.025 (6.1) | −0.087% / −0.029% / −0.028% / +0.011% |
| Pooled | −0.012% (−1.2) | −0.005 (−1.5) | +0.024 (9.7) | −0.036% / −0.024% / −0.013% / −0.026% |

**Decision rule:**
- Groups positive with t ≥ 2: **0 of 3** (needed 2).
- Years with a positive pooled spread among 2023–2026: **0 of 4** (needed 3).
- **The ML line stops.**

The rank IC is real (+0.024 within every volatility third), but it lives in the middle of the ranking. The top and bottom halves earn the same, so there is nothing to trade.

**Filter test** (A′ picks at 1,938 decisions, 16:00 UTC; 10,392 picks with a forecast, 2,530 of them in the bottom fifth of q):

| | Bottom-fifth picks | Other picks | Difference | Same-day excess (t) | Same-day excess by year, 2021 … 2026 |
|---|---|---|---|---|---|
| Next 24 h | +0.369% | +0.128% | **+0.24 pp** | +0.20% (t 2.1) | +0.39 / −0.02 / +0.30 / +0.49 / −0.14 / +0.39 % |
| Next 72 h | +0.596% | +0.457% | +0.14 pp | +0.12% (t 0.6) | +0.77 / −0.36 / +0.10 / +0.64 / −0.23 / +0.70 % |

Dropping low-q picks would have removed the picks that did *better*, so it is no use as a filter.

## 2. Do overextended entries do worse? (report-only)
- **Entries:** 1,769 new A′ entries, June 2020 to September 2026.
- **Columns:** mean return after 1, 3 and 7 days, with the day-block t on the 7-day mean, and the mean of the worst drop within 7 days. "7 d minus the rest" is the bucket's 7-day mean minus the other entries' that year, in pp.

| Bucket | n | 1 d | 3 d | 7 d (t) | Worst drop, 7 d | 7 d minus the rest, 2020 … 2026 (pp) |
|---|---|---|---|---|---|---|
| Daily RSI < 70 | 1,478 | +0.17% | +0.42% | +0.52% (1.1) | −9.1% | −8.5 −8.0 +5.6 −6.1 −16.6 −2.9 +4.5 |
| RSI 70–80 | 196 | +1.91% | +2.95% | +4.86% (3.1) | −10.0% | +13.1 −0.5 −2.3 +6.9 +3.8 +2.4 +3.1 |
| RSI > 80 | 95 | +2.56% | +4.31% | **+9.29% (2.3)** | **−14.0%** | −19.3 +17.2 −17.9 +2.6 +35.7 +3.4 −13.5 |
| 7-day return / volatility: low third | 590 | +0.05% | −0.08% | −0.32% (−0.5) | −9.4% | −2.6 −3.9 −1.0 −0.7 −4.0 −1.7 −1.9 |
| mid | 589 | +0.28% | +1.14% | +1.81% (2.3) | −8.6% | −2.3 −1.7 +2.7 −0.2 −2.5 +0.3 +4.6 |
| high | 590 | +1.11% | +1.52% | +3.38% (3.1) | −10.5% | +4.8 +5.3 −1.8 +0.9 +5.6 +1.5 −3.1 |
| Distance above the 20-day average: low third | 590 | +0.04% | +0.01% | −0.41% (−0.7) | −9.2% | −4.6 −0.7 −1.9 −1.0 −5.2 +0.0 −3.6 |
| mid | 589 | +0.07% | +0.10% | +0.67% (0.9) | −9.0% | −2.1 −6.1 +3.3 −3.5 −2.5 −3.5 +3.8 |
| high | 590 | +1.23% | +2.21% | +3.94% (3.6) | −10.3% | +5.7 +6.1 −1.7 +4.0 +6.7 +3.8 −1.3 |

**The 10 entries with the worst 7-day drop:**

| Entry (16:00 UTC) | Coin | Daily RSI | Hourly RSI | 7 d ret / vol | Distance above 20 d (vol units) | 7 d return | Worst drop |
|---|---|---|---|---|---|---|---|
| 2026-08-09 | TUT | 98.7 | 57.0 | 12.1 | 14.1 | −78.5% | −80.4% |
| 2021-05-16 | XLM | 63.0 | 51.8 | 0.7 | 2.5 | −58.8% | −58.8% |
| 2026-09-04 | HEMI | 62.8 | 37.4 | 0.2 | 2.1 | −52.1% | −55.9% |
| 2021-05-17 | AAVE | 56.4 | 48.3 | 0.4 | 1.0 | −31.5% | −55.2% |
| 2022-05-05 | NEAR | 36.2 | 21.4 | −0.5 | −3.6 | −37.7% | −50.8% |
| 2021-05-19 | CRV | 35.4 | 27.8 | −0.8 | −3.4 | −26.5% | −50.7% |
| 2022-05-06 | SHIB | 28.4 | 42.0 | −1.0 | −6.2 | −35.7% | −50.6% |
| 2022-05-06 | ICP | 27.0 | 40.7 | −0.9 | −4.6 | −30.8% | −50.4% |
| 2022-05-06 | FIL | 24.9 | 42.0 | −1.0 | −4.3 | −35.3% | −49.0% |
| 2021-05-13 | CRV | 57.1 | 46.5 | 0.2 | 2.1 | −36.6% | −48.6% |

**Who the worst cases are:**
- Only one of the ten (TUT) was overextended at entry. The others are crash weeks: May 2021 and the May 2022 collapse, several of them bought already oversold.
- **PUMP:** 7 entries. The worst was on 2026-01-16 (daily RSI 65.8, 4.7 volatility units above its 20-day average): −16.4% after 7 days, worst drop −18.8%.
- An overextension cap would have caught TUT but given up the strong average of the extended buckets. UNVERIFIED: whether a cap at an extreme level only (for example RSI > 95) helps would need its own test.

## 3. Short after a confirmed breakdown? (report-only event study)
- **Event:** the hour's close is below the previous 24-hour low, on ≥ 1.5 × the 30-day average hourly volume; 24-hour cooldown per coin; liquid coins.
- **Short P&L** is net of 0.10% + 0.10% + 2 × the half-spread. Entry is one hour after the signal, or at t + 5 h for variant c.

| Variant | Events | H | Mean net (t) | Median | Winners | 90th-pct bounce | Mean by year, 2023 / 2024 / 2025 / 2026 |
|---|---|---|---|---|---|---|---|
| a, all | 11,725 | 8 h | −0.32% (−12.3) | −0.39% | 41.5% | +4.3% | −0.55 / −0.52 / −0.13 / −0.18 % |
| | | 24 h | −0.67% (−11.0) | −0.59% | 42.7% | +8.1% | −0.88 / −1.08 / −0.33 / −0.03 % |
| | | 72 h | −1.00% (−7.4) | −0.47% | 46.8% | +15.1% | −1.40 / −1.76 / −0.31 / −0.09 % |
| b, breadth < 0.3 and BTC below its 20-day average | 4,348 | 8 h | −0.32% (−7.3) | −0.45% | 41.1% | +4.4% | −0.33 / −0.30 / −0.38 / −0.18 % |
| | | 24 h | −0.53% (−5.5) | −0.69% | 41.6% | +7.8% | −0.15 / −0.45 / −0.73 / −0.11 % |
| | | 72 h | −0.79% (−3.8) | −0.61% | 45.5% | +14.3% | +0.14 / −1.26 / −1.16 / −0.50 % |
| c, b and still below the level 4 h later | 3,211 | 8 h | −0.25% (−3.3) | −0.38% | 41.3% | +4.3% | −0.22 / −0.57 / −0.33 / −0.25 % |
| | | 24 h | −0.45% (−3.0) | −0.58% | 44.1% | +8.3% | +0.10 / −0.30 / −0.59 / −0.10 % |
| | | 72 h | −0.75% (−2.8) | −0.50% | 46.2% | +14.6% | −0.06 / −1.09 / −1.28 / −0.26 % |
| info: vt_mom's own definition (24 h volume vs its 7-day average) | 2,548 | 24 h | −1.14% (−6.7) | −0.92% | 40.2% | +10.4% | −0.87 / −1.25 / −1.51 / −0.28 % |

**Decision rule:**
- No variant has a positive mean with t ≥ 2 at 24 h or 72 h, and at most 1 of 4 years is positive.
- **No short rule is pre-registered.**
- Shorting a confirmed breakdown buys the bounce: winners are 41–47%, and the typical 24-hour adverse move at the 90th percentile is +8%.

## 4. Does the strategy behave as written? (log walk-through)
**Method:** the saved trade logs were replayed hour by hour against the model's own decisions and reasons. These come from `explain()`, re-run hourly from each window's start, as the engine's first decisions and the live bot do.

| Window (12:00 UTC start) | R: A′ / E | Trades: A′ / E | Re-run equals the engine's targets from hour | Max gross | Unexplained trades |
|---|---|---|---|---|---|
| (i) 2026-03-21, real falling round | −1.4% / −1.1% | 102 / 86 | 76 / 84 | 1.0000 | 0 |
| (ii) 2026-04-04, real rising final | +11.2% / +9.0% | 119 / 105 | 124 / 124 | 1.0000 | **2 / 2** (see A1) |
| (iii) A′'s worst window | −31.2% / −31.2% | 106 / 100 | 244 / 252 | 0.988 / 1.000 | 0 |
| (iv) E beat A′ by the most | −9.3% / −3.1% | 123 / 107 | 316 / 324 | 1.0000 | 0 |
| (v) E lost to A′ by the most | +43.1% / +37.5% | 105 / 96 | 100 / 100 | 1.0000 | 0 |
| (vi) 2026-09-15, most recent complete | +25.3% / +26.3% | 127 / 114 | never: the window's own chain persists (as in the tool's 210 non-converging windows) | 0.987 | 0 |

In all six windows:
- the replayed weights match the log's `w_before` (largest mismatch 3e-17);
- no hour is missing from the panel;
- gross never exceeds 1;
- every guard trade falls at 04:00 UTC on a day with no fill since 00:00 UTC.

**Anomaly list:**

| # | Finding | Where / how often | Assessment |
|---|---|---|---|
| A1 | Exits with no reason in `explain()`: PUMP on 2026-04-11 and FIL on 2026-04-17, both at the 17:00 fill | window (ii), A′ and E | **Logging gap, not a trading error.** Both coins left the point-in-time universe at that 16:00 update. The model drops them before deciding, as the contract requires, but writes no record. The shadow log needs an "exit: left the universe" record (not fixed here: read-only task) |
| A2 | E's reason text for window-start stages says "the rest at 00:00 UTC", but those coins complete at the 16:00 decision 4 hours later, as the rule says | every window | Wording only; the timing is right |
| A3 | Bought at the 12:00 window start, sold at the 16:00 decision 4 hours later | 241 of 2,298 windows (10.5%), 305 coins; e.g. XRP in (vi) | The first decision uses 12:00 data and the regular one 16:00 data. Cost ≈ 0.004% of E₀ per window on average. Same in E |
| A4 | Bought and fully sold within 24 hours | 1.64 per window over all windows; 1–7 in the six | Almost all are the base dropping a coin at the next 16:00 decision (exactly 24 h), plus A3 |
| A5 | Any buy followed by a sell of the same coin within 24 h | 17–44 per window | Mostly guard trades re-trading small drifts (guard → guard, guard → exit) |
| A6 | Trades under $500 | 25–75 per window | **All are guard trades.** The guard rebalances every coin exactly to target, so small drifts become small trades |
| A7 | All starting coins bought in the same hour | all six windows, A′ and E | Yes: every starting coin at hour 1 (13:00 UTC); E's staged ones at half size |
| A8 | E's second halves | 70 staged coins | **All on time:** 35 topped up at 00:00 (filled at 01:00); 31 window-start stages completed at the 16:00 decision; 4 exited before completion; none topped up while broken down |
| A9 | Exposure above 1, or gaps | none | Max gross 1.0000; no missing hours |

**Sample window, hour by hour: (vi) from 2026-09-15 12:00, version E, the first 64 hours** (decision time → fills one hour later; guard trades, which fire only on days without a fill, come later in the window):

| Decision (UTC) | Decisions | Fills one hour later (coin, type, weight change, size, fee) | Gross after |
|---|---|---|---|
| 09-15 12:00 | NEAR, TRX, UNI, XRP, ZEC: stage (new coin, half now); XLM: enter in full (trend score 1, volatility below the median) | the six as window-start entries: XLM +0.134 ($13,420, fee $13.42); the others +0.067 ($6,710, fee $6.71 each) | 0.470 |
| 09-15 16:00 | XRP: exit (the base dropped it); ARB: stage | NEAR, TRX, UNI, ZEC completed (+0.059 to +0.061, about $5,800–6,100 each); XRP exit −0.066 ($6,569); ARB +0.063 ($6,238) | 0.699 |
| 09-16 00:00 | ARB: top-up (staged coin completed) | ARB +0.062 ($6,070, fee $6.07) | 0.758 |
| 09-16 16:00 | XLM: exit (the base dropped it); BNB: stage | BNB +0.066 ($6,642); XLM exit −0.119 ($11,959) | 0.710 |
| 09-17 00:00 | BNB: top-up | BNB +0.068 ($7,042) | 0.789 |
| 09-17 02:00 | — | ZEC drift-band −0.015 ($1,601) | 0.773 |
| 09-17 13:00 | — | TRX drift-band +0.016 ($1,665) | 0.794 |
| 09-17 16:00 | TRX: exit (the base dropped it); BMT: stage | TRX exit −0.129 ($14,069); BMT +0.056 ($6,170); ARB, NEAR, UNI, ZEC rebalanced down (−0.018 to −0.030) | 0.635 |
| 09-18 00:00 | BMT: top-up | BMT +0.058 ($6,445) | 0.698 |
| 09-18 02:00 | — | ARB drift-band −0.015 ($1,735) | 0.691 |

The full hour-by-hour records of all 12 walk-throughs are in `check4.json`.

## 5. Fee audit (all 2,298 windows)
- **Method:** trades are classified with the saved shared target history.
- **Approximation:** during a window's own first decisions the shared targets can differ, so a few start-of-window trades may be misfiled. The walk-through in check 4 re-ran those exactly and found no unexplained trades.

| Type | A′: trades / window | A′: median size | A′: fees, % of E₀ / window | A′: share of fees | E: trades / window | E: median size | E: fees, % of E₀ / window | E: share of fees |
|---|---|---|---|---|---|---|---|---|
| 16:00 decision (entries, rebalances) | 14.2 | $9,251 | 0.125% | 34.3% | 17.6 | $5,144 | 0.097% | 27.9% |
| Exit (to 0) | 9.8 | $11,994 | 0.121% | 33.2% | 9.8 | $11,753 | 0.118% | 33.8% |
| Window-start entry | 6.0 | $11,932 | 0.072% | 19.9% | 6.0 | $6,439 | 0.043% | 12.2% |
| Staged second half (00:00) | — | — | — | — | 6.8 | $5,860 | 0.041% | 11.7% |
| Drift-band (target unchanged) | 6.1 | $1,725 | 0.019% | 5.3% | 9.2 | $2,097 | 0.034% | 9.8% |
| Guard | **76.8** | **$237** | 0.026% | 7.2% | 45.8 | $250 | 0.016% | 4.6% |
| Other target change | 0.02 | | 0.000% | 0.1% | 0.02 | | 0.000% | 0.1% |
| **Total** | **112.9** | **$455** | **0.364%** (0.418% with spread) | | **95.1** | **$1,527** | **0.349%** (0.401% with spread) | |

**Small trades:**
- A′: trades under 1% of equity are 65% of all trades but only **6.0% of fees**; trades under $500 number 135,500, nearly all guard trades.
- E: 46% of trades and 3.8% of fees.

**Maker upper bound** (every entry and decision trade at 0.05% instead of 0.10%): −0.169% of E₀ per window for A′ and −0.166% for E, or −0.18% including guard trades. **UNVERIFIED**: it assumes every order fills as a maker at the touch.

## 6. Data inventory (`data/`, nothing downloaded)

| Data | Symbols | Range | Frequency | Point-in-time? |
|---|---|---|---|---|
| **S&P 500 index** (FRED, `external/fred`) | SP500 | 2016-09-30 → 2026-09-29 | daily, business days | Yes with a one-day lag (official close; FRED keeps only 10 years) |
| VIX (FRED) | VIXCLS | 1990-01-02 → 2026-09-28 | daily | Yes with a one-day lag |
| US 10-year yield, broad dollar index, WTI oil (FRED) | DGS10, DTWEXBGS, DCOILWTICO | from 1962 / 2006 / 1986 → late Sept 2026 | daily | Yes with a one-day lag; the dollar index may be revised (UNVERIFIED) |
| Fed funds target (upper), CPI (FRED) | DFEDTARU, CPIAUCNS | 2008 → 2026-09-29; 1913 → 2026-08 | daily; monthly | Fed target yes. CPI no by date: only with its release lag (the validation build assumes the 16th of the next month) |
| Macro features X1–X8 (`validation/features.parquet`, from the files above) | CPI growth, Fed direction, yield change, dollar change, S&P vs its 200-day average, VIX, oil change | 2020-01-01 → 2026-09-29 | daily at 16:00 UTC | **Yes**: FRED observations dated before t's UTC day; CPI by assumed release |
| Funding rates, USD-M futures (`external/binance_futures_ext`) | 61 symbols (54 of the 58 universe coins) | 2020-01 → 2026-09 | 8-hourly prints, monthly files | Yes, by funding time; no October file |
| Derived `funding8h_mean72.parquet` | 61 columns | 2018-01-01 → 2026-09-30 | hourly | Derived; how it was built is UNVERIFIED |
| BTC funding (`external/lob_copy`, `external/binance_futures`) | BTC | 2020-01 → 2026-08 | 8-hourly | Yes |
| BTC open interest (`external/lob_copy`) | BTC | 2020-09-01 → 2026-08-11 | intraday snapshots, daily files | Yes, by snapshot time |
| BTC futures metrics: open interest, top-trader and taker long/short ratios | BTC | 2026-08-12 → 2026-09-29 | 5-minute | Yes; 7 weeks only |
| **Tokenized stocks** | **none** | — | — | Spot klines (84 symbols, 1 h; 65 symbols, 1 m) and Roostoo's 88 pairs are all crypto. **PAXG** (a gold token) is the only non-crypto asset |
