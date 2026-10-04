# H1 ("E-breadth"): a brief for the team

For Pol and Baitoey. It explains what H1 does, shows it in six real windows next to vt_mom and the live model
(pol_switch_vt_tl_e20v45), and ends with the numbers and their limits. Sources: the hybrids report
([`20261004-hybrids.md`](../../reports/review/20261004-hybrids.md)) and its pre-registration
([`20261004-prereg-hybrids.md`](../../reports/review/20261004-prereg-hybrids.md)).

## What H1 is
- **It is vt_mom with one change.** vt_mom picks the coins, and H1 holds the same coins, exits them at the same
  times and uses the same volatility cap.
- **The change is in how a new coin is bought.**
  - When the market is weak, H1 buys half first and the rest a few hours later: at 00:00 UTC, or at the next 16:00
    decision for a coin bought at a window's start.
  - "Weak" means breadth below 0.60: fewer than 60% of the 20 most liquid coins are in an up-trend.
  - When breadth is 0.60 or more, H1 buys in full, exactly like vt_mom.
  - Breadth is read only at the decision hour, from data up to that hour.
- **It runs hourly** (book_orch), so between decisions it also trades a coin back towards its target when the coin's
  weight drifts more than 5 points. vt_mom does this only once a day.
- **Status:** registered as book_orch's default (run `033c466d54a7766f`, HEADLINE_RET 0.617 vs vt_mom's 0.609).
  - A paper shadow bot (`mm-book-shadow-h1`) logs its live decisions from 2026-10-04.
  - On that day breadth was 1.00, so H1 was trading exactly like vt_mom.

## How the windows were chosen (fixed rule, no hand-picking)
1. The most recent complete window of each market type in the data, by BTC's 14-day return:
   - RISING: above +2%;
   - FALLING: below −2%;
   - FLAT: within ±2%.
2. The two real rounds of the previous edition: 2026-03-21 (falling) and 2026-04-04 (rising).
3. The window where H1 lost the most to vt_mom, shown for honesty.

| Window | Start (12:00 UTC, 14 days) | BTC | H1 | vt_mom | Live model |
|---|---|---|---|---|---|
| Most recent rising | 2026-09-15 | +9.6% | +28.56% | +27.33% | +36.46% |
| Most recent falling | 2026-09-04 | −3.9% | +20.70% | +20.70% | +22.58% |
| Most recent flat | 2026-09-06 | +0.7% | +13.85% | +13.85% | +15.29% |
| Previous edition, falling round | 2026-03-21 | −4.9% | −0.88% | −1.57% | +3.64% |
| Previous edition, rising round | 2026-04-04 | +13.2% | +7.97% | +9.92% | +0.40% |
| H1's worst against vt_mom | 2021-01-28 | +46.5% | +37.05% | +61.56% | +44.43% |

**How to read each window.**
- **The chart** shows the three equity curves.
- **The gap** is H1's return minus vt_mom's, split into three parts:
  - **staging:** the coins H1 held at half while vt_mom held them in full;
  - **exits:** H1 still holding a coin vt_mom had sold;
  - **other:** everything else, i.e. drift trades, the daily activity trade, fees, and the hourly-vs-daily
    difference.
- **The decision table** (click to open) lists, at the window start and at every 16:00 UTC decision:
  - the breadth, and whether staging was on;
  - each coin's action: full entry, half, top-up, hold or exit, with its reason.

  Rows at 00:00 UTC appear only when a staged half was completed.

## The six windows

### Most recent RISING window: 2026-09-15 (BTC +9.6%)

![H1, vt_mom and the live model, 2026-09-15](figures/h1/rising.svg)

| | H1 | vt_mom | Live model |
|---|---|---|---|
| 14-day return | **+28.56%** | +27.33% | +36.46% |

**H1 minus vt_mom: +1.23 points.** Staging +0.57, exits +0.00, other +0.66 (other = trades back to target when a weight drifts, the daily activity trade, fees, and the hourly-vs-daily difference). Staging was on at 4 of 15 decisions; 8 coins were bought at half, 12 in full.

**In plain words:**

- In the first four days breadth was low (0.25 to 0.55), so H1 bought its new coins at half and completed them a few hours later. From Sep 18 breadth was near 1.0, and H1 bought in full, exactly like vt_mom.
- The staged halves earned **+0.57 points**: for example, UNI fell 3.6% in the hours after its first half was bought. The different weights and drift trades that followed added +0.66.
- H1 made +28.6% against vt_mom's +27.3%. The live model did better in this window (+36.5%).

<details><summary>Decision table (window start, every 16:00 UTC decision, and 00:00 top-ups)</summary>

| Time (UTC) | Breadth | Staging | Actions |
|---|---|---|---|
| 09-15 12:00 | 0.45 | on | NEAR **half** (rest at the next 16:00 decision); TRX **half** (rest at the next 16:00 decision); UNI **half** (rest at the next 16:00 decision); XLM **full entry** (trend score 1, low volatility); XRP **half** (rest at the next 16:00 decision); ZEC **half** (rest at the next 16:00 decision) |
| 09-15 16:00 | 0.50 | on | ARB **half** (rest at 00:00 UTC); NEAR **top-up** (window-start half completed); TRX **top-up** (window-start half completed); UNI **top-up** (window-start half completed); XRP **exit** (dropped by vt_mom); ZEC **top-up** (window-start half completed); hold: XLM |
| 09-16 00:00 | 0.25 | - | ARB **top-up** (staged half completed); hold: NEAR, TRX, UNI, XLM, ZEC |
| 09-16 16:00 | 0.30 | on | BNB **half** (rest at 00:00 UTC); XLM **exit** (dropped by vt_mom); hold: ARB, NEAR, TRX, UNI, ZEC |
| 09-17 00:00 | 0.45 | - | BNB **top-up** (staged half completed); hold: ARB, NEAR, TRX, UNI, ZEC |
| 09-17 16:00 | 0.50 | on | BMT **half** (rest at 00:00 UTC); TRX **exit** (dropped by vt_mom); hold: ARB, BNB, NEAR, UNI, ZEC |
| 09-18 00:00 | 0.55 | - | BMT **top-up** (staged half completed); hold: ARB, BNB, NEAR, UNI, ZEC |
| 09-18 16:00 | 1.00 | off | BMT **exit** (dropped by vt_mom); SOL **full entry** (staging off); hold: ARB, BNB, NEAR, UNI, ZEC |
| 09-19 16:00 | 0.95 | off | AVAX **full entry** (staging off); BNB **exit** (dropped by vt_mom); hold: ARB, NEAR, SOL, UNI, ZEC |
| 09-20 16:00 | 1.00 | off | hold: ARB, AVAX, NEAR, SOL, UNI, ZEC |
| 09-21 16:00 | 1.00 | off | hold: ARB, AVAX, NEAR, SOL, UNI, ZEC |
| 09-22 16:00 | 1.00 | off | ARB **exit** (dropped by vt_mom); AVAX **exit** (dropped by vt_mom); BTC **full entry** (staging off); SUI **full entry** (staging off); hold: NEAR, SOL, UNI, ZEC |
| 09-23 16:00 | 0.85 | off | AVAX **full entry** (staging off); NEAR **exit** (dropped by vt_mom); TAO **full entry** (staging off); UNI **exit** (dropped by vt_mom); hold: BTC, SOL, SUI, ZEC |
| 09-24 16:00 | 0.90 | off | LTC **full entry** (staging off); ZEC **exit** (dropped by vt_mom); hold: AVAX, BTC, SOL, SUI, TAO |
| 09-25 16:00 | 1.00 | off | BTC **exit** (dropped by vt_mom); ENA **full entry** (staging off); LTC **exit** (dropped by vt_mom); NEAR **full entry** (staging off); hold: AVAX, SOL, SUI, TAO |
| 09-26 16:00 | 1.00 | off | hold: AVAX, ENA, NEAR, SOL, SUI, TAO |
| 09-27 16:00 | 0.95 | off | AVAX **exit** (dropped by vt_mom); ONDO **full entry** (staging off); hold: ENA, NEAR, SOL, SUI, TAO |
| 09-28 16:00 | 1.00 | off | HBAR **full entry** (staging off); SUI **exit** (dropped by vt_mom); hold: ENA, NEAR, ONDO, SOL, TAO |

</details>


### Most recent FALLING window: 2026-09-04 (BTC -3.9%)

![H1, vt_mom and the live model, 2026-09-04](figures/h1/falling.svg)

| | H1 | vt_mom | Live model |
|---|---|---|---|
| 14-day return | **+20.70%** | +20.70% | +22.58% |

**H1 minus vt_mom: +0.00 points.** Staging +0.00, exits +0.00, other +0.00 (other = trades back to target when a weight drifts, the daily activity trade, fees, and the hourly-vs-daily difference). Staging was on at 5 of 15 decisions; 0 coins were bought at half, 17 in full.

**In plain words:**

- Breadth stayed at or above 0.60 for the first nine decisions, so H1 bought every new coin in full, as vt_mom does.
- When breadth dropped below 0.60 (Sep 13 to 17), H1 mostly just held its coins, and its one new coin passed the full-entry test (trend score 1, low volatility).
- So H1 made exactly vt_mom's trades and the same +20.7%. The live model made +22.6%.

<details><summary>Decision table (window start, every 16:00 UTC decision, and 00:00 top-ups)</summary>

| Time (UTC) | Breadth | Staging | Actions |
|---|---|---|---|
| 09-04 12:00 | 0.90 | off | AAVE **full entry** (staging off); BNB **full entry** (staging off); BTC **full entry** (staging off); UNI **full entry** (staging off); XPL **full entry** (staging off); ZEC **full entry** (staging off) |
| 09-04 16:00 | 0.90 | off | BNB **exit** (dropped by vt_mom); BTC **exit** (dropped by vt_mom); HEMI **full entry** (staging off); LTC **full entry** (staging off); hold: AAVE, UNI, XPL, ZEC |
| 09-05 16:00 | 0.95 | off | ARB **full entry** (staging off); BNB **full entry** (staging off); HEMI **exit** (dropped by vt_mom); XPL **exit** (dropped by vt_mom); hold: AAVE, LTC, UNI, ZEC |
| 09-06 16:00 | 0.95 | off | AAVE **exit** (dropped by vt_mom); BNB **exit** (dropped by vt_mom); LINK **full entry** (staging off); NEAR **full entry** (staging off); hold: ARB, LTC, UNI, ZEC |
| 09-07 16:00 | 0.95 | off | NEAR **exit** (dropped by vt_mom); WLD **full entry** (staging off); hold: ARB, LINK, LTC, UNI, ZEC |
| 09-08 16:00 | 0.95 | off | BNB **full entry** (staging off); LINK **exit** (dropped by vt_mom); hold: ARB, LTC, UNI, WLD, ZEC |
| 09-09 16:00 | 0.95 | off | NEAR **full entry** (staging off); WLD **exit** (dropped by vt_mom); hold: ARB, BNB, LTC, UNI, ZEC |
| 09-10 16:00 | 0.65 | off | NEAR **exit** (dropped by vt_mom); TRX **full entry** (staging off); hold: ARB, BNB, LTC, UNI, ZEC |
| 09-11 16:00 | 0.65 | off | hold: ARB, BNB, LTC, TRX, UNI, ZEC |
| 09-12 16:00 | 0.65 | off | hold: ARB, BNB, LTC, TRX, UNI, ZEC |
| 09-13 16:00 | 0.40 | on | hold: ARB, BNB, LTC, TRX, UNI, ZEC |
| 09-14 16:00 | 0.45 | on | hold: ARB, BNB, LTC, TRX, UNI, ZEC |
| 09-15 16:00 | 0.50 | on | hold: ARB, BNB, LTC, TRX, UNI, ZEC |
| 09-16 16:00 | 0.30 | on | hold: ARB, BNB, LTC, TRX, UNI, ZEC |
| 09-17 16:00 | 0.50 | on | NEAR **full entry** (trend score 1, low volatility); TRX **exit** (dropped by vt_mom); hold: ARB, BNB, LTC, UNI, ZEC |

</details>


### Most recent FLAT window: 2026-09-06 (BTC +0.7%)

![H1, vt_mom and the live model, 2026-09-06](figures/h1/flat.svg)

| | H1 | vt_mom | Live model |
|---|---|---|---|
| 14-day return | **+13.85%** | +13.85% | +15.29% |

**H1 minus vt_mom: +0.00 points.** Staging +0.00, exits +0.00, other +0.00 (other = trades back to target when a weight drifts, the daily activity trade, fees, and the hourly-vs-daily difference). Staging was on at 5 of 15 decisions; 0 coins were bought at half, 14 in full.

**In plain words:**

- This window overlaps the falling one by 12 days and tells the same story. Breadth was high (0.65 to 0.95) for the first seven decisions, so every entry was in full.
- While breadth was low (Sep 13 to 17), no new coin needed staging.
- H1 and vt_mom made the same trades and the same +13.85%; the live model made +15.3%.

<details><summary>Decision table (window start, every 16:00 UTC decision, and 00:00 top-ups)</summary>

| Time (UTC) | Breadth | Staging | Actions |
|---|---|---|---|
| 09-06 12:00 | 0.95 | off | ARB **full entry** (staging off); BNB **full entry** (staging off); LTC **full entry** (staging off); NEAR **full entry** (staging off); UNI **full entry** (staging off); ZEC **full entry** (staging off) |
| 09-06 16:00 | 0.95 | off | BNB **exit** (dropped by vt_mom); LINK **full entry** (staging off); hold: ARB, LTC, NEAR, UNI, ZEC |
| 09-07 16:00 | 0.95 | off | NEAR **exit** (dropped by vt_mom); WLD **full entry** (staging off); hold: ARB, LINK, LTC, UNI, ZEC |
| 09-08 16:00 | 0.95 | off | BNB **full entry** (staging off); LINK **exit** (dropped by vt_mom); hold: ARB, LTC, UNI, WLD, ZEC |
| 09-09 16:00 | 0.95 | off | NEAR **full entry** (staging off); WLD **exit** (dropped by vt_mom); hold: ARB, BNB, LTC, UNI, ZEC |
| 09-10 16:00 | 0.65 | off | NEAR **exit** (dropped by vt_mom); TRX **full entry** (staging off); hold: ARB, BNB, LTC, UNI, ZEC |
| 09-11 16:00 | 0.65 | off | hold: ARB, BNB, LTC, TRX, UNI, ZEC |
| 09-12 16:00 | 0.65 | off | hold: ARB, BNB, LTC, TRX, UNI, ZEC |
| 09-13 16:00 | 0.40 | on | hold: ARB, BNB, LTC, TRX, UNI, ZEC |
| 09-14 16:00 | 0.45 | on | hold: ARB, BNB, LTC, TRX, UNI, ZEC |
| 09-15 16:00 | 0.50 | on | hold: ARB, BNB, LTC, TRX, UNI, ZEC |
| 09-16 16:00 | 0.30 | on | hold: ARB, BNB, LTC, TRX, UNI, ZEC |
| 09-17 16:00 | 0.50 | on | NEAR **full entry** (trend score 1, low volatility); TRX **exit** (dropped by vt_mom); hold: ARB, BNB, LTC, UNI, ZEC |
| 09-18 16:00 | 1.00 | off | hold: ARB, BNB, LTC, NEAR, UNI, ZEC |
| 09-19 16:00 | 0.95 | off | AVAX **full entry** (staging off); BNB **exit** (dropped by vt_mom); ENA **full entry** (staging off); LTC **exit** (dropped by vt_mom); hold: ARB, NEAR, UNI, ZEC |

</details>


### Previous edition's falling round: 2026-03-21 (BTC -4.9%)

![H1, vt_mom and the live model, 2026-03-21](figures/h1/round_falling.svg)

| | H1 | vt_mom | Live model |
|---|---|---|---|
| 14-day return | **-0.88%** | -1.57% | +3.64% |

**H1 minus vt_mom: +0.69 points.** Staging +0.45, exits +0.00, other +0.24 (other = trades back to target when a weight drifts, the daily activity trade, fees, and the hourly-vs-daily difference). Staging was on at 14 of 15 decisions; 7 coins were bought at half, 6 in full.

**In plain words:**

- Breadth was low (0.15 to 0.55) for almost the whole round, so H1 bought each of its seven new coins half first: WLFI, LINK, FIL, TAO, DOGE and FET.
- Prices kept slipping, so buying half first lost less. Staging added **+0.45 points** and the knock-on effects +0.24.
- H1 lost 0.88% against vt_mom's 1.57%. The live model, which switches to trend shorts when BTC trends down, made +3.64%.

<details><summary>Decision table (window start, every 16:00 UTC decision, and 00:00 top-ups)</summary>

| Time (UTC) | Breadth | Staging | Actions |
|---|---|---|---|
| 03-21 12:00 | 0.60 | off | ETH **full entry** (staging off); FET **full entry** (staging off); SOL **full entry** (staging off); TAO **full entry** (staging off); TRX **full entry** (staging off); ZEC **full entry** (staging off) |
| 03-21 16:00 | 0.45 | on | hold: ETH, FET, SOL, TAO, TRX, ZEC |
| 03-22 16:00 | 0.15 | on | hold: ETH, FET, SOL, TAO, TRX, ZEC |
| 03-23 16:00 | 0.20 | on | hold: ETH, FET, SOL, TAO, TRX, ZEC |
| 03-24 16:00 | 0.30 | on | WLFI **half** (rest at 00:00 UTC); ZEC **exit** (dropped by vt_mom); hold: ETH, FET, SOL, TAO, TRX |
| 03-25 00:00 | 0.35 | - | WLFI **top-up** (staged half completed); hold: ETH, FET, SOL, TAO, TRX |
| 03-25 16:00 | 0.55 | on | LINK **half** (rest at 00:00 UTC); WLFI **exit** (dropped by vt_mom); hold: ETH, FET, SOL, TAO, TRX |
| 03-26 00:00 | 0.60 | - | LINK **top-up** (staged half completed); hold: ETH, FET, SOL, TAO, TRX |
| 03-26 16:00 | 0.15 | on | FET **exit** (dropped by vt_mom); FIL **half** (rest at 00:00 UTC); TAO **exit** (dropped by vt_mom); WLFI **half** (rest at 00:00 UTC); hold: ETH, LINK, SOL, TRX |
| 03-27 00:00 | 0.25 | - | FIL **top-up** (staged half completed); WLFI **top-up** (staged half completed); hold: ETH, LINK, SOL, TRX |
| 03-27 16:00 | 0.15 | on | SOL **exit** (dropped by vt_mom); TAO **half** (rest at 00:00 UTC); hold: ETH, FIL, LINK, TRX, WLFI |
| 03-28 00:00 | 0.15 | - | TAO **top-up** (staged half completed); hold: ETH, FIL, LINK, TRX, WLFI |
| 03-28 16:00 | 0.15 | on | DOGE **half** (rest at 00:00 UTC); FET **half** (rest at 00:00 UTC); FIL **exit** (dropped by vt_mom); LINK **exit** (dropped by vt_mom); hold: ETH, TAO, TRX, WLFI |
| 03-29 00:00 | 0.15 | - | DOGE **top-up** (staged half completed); FET **top-up** (staged half completed); hold: ETH, TAO, TRX, WLFI |
| 03-29 16:00 | 0.15 | on | hold: DOGE, ETH, FET, TAO, TRX, WLFI |
| 03-30 16:00 | 0.20 | on | hold: DOGE, ETH, FET, TAO, TRX, WLFI |
| 03-31 16:00 | 0.20 | on | hold: DOGE, ETH, FET, TAO, TRX, WLFI |
| 04-01 16:00 | 0.35 | on | hold: DOGE, ETH, FET, TAO, TRX, WLFI |
| 04-02 16:00 | 0.25 | on | hold: DOGE, ETH, FET, TAO, TRX, WLFI |
| 04-03 16:00 | 0.30 | on | hold: DOGE, ETH, FET, TAO, TRX, WLFI |

</details>


### Previous edition's rising round: 2026-04-04 (BTC +13.2%)

![H1, vt_mom and the live model, 2026-04-04](figures/h1/round_rising.svg)

| | H1 | vt_mom | Live model |
|---|---|---|---|
| 14-day return | **+7.97%** | +9.92% | +0.40% |

**H1 minus vt_mom: -1.95 points.** Staging -3.89, exits +0.00, other +1.94 (other = trades back to target when a weight drifts, the daily activity trade, fees, and the hourly-vs-daily difference). Staging was on at 5 of 15 decisions; 7 coins were bought at half, 12 in full.

**In plain words:**

- The round started with weak breadth (0.25), so H1 bought all six starting coins at half and completed them only at the 16:00 decision four hours later. In those hours STO rose 21%.
- That cost **−3.89 points**. book_orch's hourly rebalancing later sold part of STO's spike before it fell back, which recovered about half of it (other: +1.94).
- H1 made +7.97% against vt_mom's +9.92%. The live model made +0.40%.

<details><summary>Decision table (window start, every 16:00 UTC decision, and 00:00 top-ups)</summary>

| Time (UTC) | Breadth | Staging | Actions |
|---|---|---|---|
| 04-04 12:00 | 0.25 | on | FET **half** (rest at the next 16:00 decision); STO **half** (rest at the next 16:00 decision); TAO **half** (rest at the next 16:00 decision); TRX **half** (rest at the next 16:00 decision); WLFI **half** (rest at the next 16:00 decision); ZEC **half** (rest at the next 16:00 decision) |
| 04-04 16:00 | 0.25 | on | FET **top-up** (window-start half completed); STO **top-up** (window-start half completed); TAO **top-up** (window-start half completed); TRX **top-up** (window-start half completed); WLFI **top-up** (window-start half completed); ZEC **top-up** (window-start half completed) |
| 04-05 16:00 | 0.30 | on | WLFI **exit** (dropped by vt_mom); XPL **half** (rest at 00:00 UTC); hold: FET, STO, TAO, TRX, ZEC |
| 04-06 00:00 | 0.45 | - | XPL **top-up** (staged half completed); hold: FET, STO, TAO, TRX, ZEC |
| 04-06 16:00 | 0.60 | off | hold: FET, STO, TAO, TRX, XPL, ZEC |
| 04-07 16:00 | 0.45 | on | hold: FET, STO, TAO, TRX, XPL, ZEC |
| 04-08 16:00 | 0.75 | off | ETH **full entry** (staging off); FET **exit** (dropped by vt_mom); NEAR **full entry** (staging off); TAO **exit** (dropped by vt_mom); hold: STO, TRX, XPL, ZEC |
| 04-09 16:00 | 0.60 | off | BTC **full entry** (staging off); ETH **exit** (dropped by vt_mom); FIL **full entry** (staging off); PUMP **full entry** (staging off); STO **exit** (dropped by vt_mom); ZEC **exit** (dropped by vt_mom); hold: NEAR, TRX, XPL |
| 04-10 16:00 | 0.60 | off | hold: BTC, FIL, NEAR, PUMP, TRX, XPL |
| 04-11 16:00 | 0.65 | off | ETH **full entry** (staging off); PUMP **exit** (left the universe); TRX **exit** (dropped by vt_mom); ZEC **full entry** (staging off); hold: BTC, FIL, NEAR, XPL |
| 04-12 16:00 | 0.65 | off | hold: BTC, ETH, FIL, NEAR, XPL, ZEC |
| 04-13 16:00 | 0.45 | on | hold: BTC, ETH, FIL, NEAR, XPL, ZEC |
| 04-14 16:00 | 0.65 | off | hold: BTC, ETH, FIL, NEAR, XPL, ZEC |
| 04-15 16:00 | 0.65 | off | BTC **exit** (dropped by vt_mom); TRX **full entry** (staging off); hold: ETH, FIL, NEAR, XPL, ZEC |
| 04-16 16:00 | 0.85 | off | ENA **full entry** (staging off); XPL **exit** (dropped by vt_mom); hold: ETH, FIL, NEAR, TRX, ZEC |
| 04-17 16:00 | 0.90 | off | AAVE **full entry** (staging off); BTC **full entry** (staging off); FIL **exit** (left the universe); NEAR **exit** (dropped by vt_mom); XRP **full entry** (staging off); ZEC **exit** (dropped by vt_mom); hold: ENA, ETH, TRX |

</details>


### Where H1 lost the most to vt_mom: 2021-01-28 (BTC +46.5%)

![H1, vt_mom and the live model, 2021-01-28](figures/h1/h1_worst.svg)

| | H1 | vt_mom | Live model |
|---|---|---|---|
| 14-day return | **+37.05%** | +61.56% | +44.43% |

**H1 minus vt_mom: -24.52 points.** Staging +0.00, exits +0.00, other -24.52 (other = trades back to target when a weight drifts, the daily activity trade, fees, and the hourly-vs-daily difference). Staging was on at 0 of 15 decisions; 0 coins were bought at half, 14 in full.

**In plain words:**

- Here H1 made exactly vt_mom's picks: breadth stayed above 0.60 all window, so it never staged a coin.
- The whole gap (−24.5 points) is book_orch's hourly trading rule. As DOGE rallied, its weight drifted past the band, so book_orch sold it back towards its target. Then DOGE jumped 70% in one hour, while vt_mom, which rebalances only once a day, still held a weight of 0.20 against book_orch's 0.06.
- This comes from the hourly engine that every book_orch version shares, even with every layer off, not from H1's staging. It is the single largest window gap in the backtest, and it was already known from v1's parity check.

<details><summary>Decision table (window start, every 16:00 UTC decision, and 00:00 top-ups)</summary>

| Time (UTC) | Breadth | Staging | Actions |
|---|---|---|---|
| 01-28 12:00 | 0.65 | off | AAVE **full entry** (staging off); CRV **full entry** (staging off); DOGE **full entry** (staging off); DOT **full entry** (staging off); LINK **full entry** (staging off); UNI **full entry** (staging off) |
| 01-28 16:00 | 0.76 | off | hold: AAVE, CRV, DOGE, DOT, LINK, UNI |
| 01-29 16:00 | 0.88 | off | hold: AAVE, CRV, DOGE, DOT, LINK, UNI |
| 01-30 16:00 | 0.82 | off | DOGE **exit** (dropped by vt_mom); DOT **exit** (dropped by vt_mom); SOL **full entry** (staging off); XRP **full entry** (staging off); hold: AAVE, CRV, LINK, UNI |
| 01-31 16:00 | 0.94 | off | hold: AAVE, CRV, LINK, SOL, UNI, XRP |
| 02-01 16:00 | 0.94 | off | BNB **full entry** (staging off); DOGE **full entry** (staging off); SOL **exit** (left the universe); XRP **exit** (dropped by vt_mom); hold: AAVE, CRV, LINK, UNI |
| 02-02 16:00 | 1.00 | off | hold: AAVE, BNB, CRV, DOGE, LINK, UNI |
| 02-03 16:00 | 1.00 | off | hold: AAVE, BNB, CRV, DOGE, LINK, UNI |
| 02-04 16:00 | 1.00 | off | ETH **full entry** (staging off); LINK **exit** (dropped by vt_mom); hold: AAVE, BNB, CRV, DOGE, UNI |
| 02-05 16:00 | 1.00 | off | hold: AAVE, BNB, CRV, DOGE, ETH, UNI |
| 02-06 16:00 | 1.00 | off | AAVE **exit** (dropped by vt_mom); ADA **full entry** (staging off); hold: BNB, CRV, DOGE, ETH, UNI |
| 02-07 16:00 | 1.00 | off | hold: ADA, BNB, CRV, DOGE, ETH, UNI |
| 02-08 16:00 | 1.00 | off | hold: ADA, BNB, CRV, DOGE, ETH, UNI |
| 02-09 16:00 | 1.00 | off | AAVE **full entry** (staging off); CRV **exit** (dropped by vt_mom); FIL **full entry** (staging off); UNI **exit** (dropped by vt_mom); hold: ADA, BNB, DOGE, ETH |
| 02-10 16:00 | 1.00 | off | hold: AAVE, ADA, BNB, DOGE, ETH, FIL |

</details>

## Summary

### Over all 2,298 backtest windows (June 2020 to September 2026)
**The five score views:**
- the score as the competition is weighted now (a);
- without the most recent windows (b);
- every year weighted the same (c);
- rising and falling windows only (d, e).

Each cell shows the score (rank among the five; label against vt_mom from a 90% month-block bootstrap). The rows below
the views are risk measures.

| | H1 | H2 | E5 | vt_mom | Live model |
|---|---|---|---|---|---|
| (a) current weights | 0.617 (#1, ahead) | 0.611 (#2, tied) | 0.583 (#4, tied) | 0.609 (#3) | 0.568 (#5, behind) |
| (b) without the newest windows | 0.561 (#2, tied) | 0.559 (#3, tied) | 0.564 (#1, tied) | 0.556 (#4) | 0.501 (#5, behind) |
| (c) every year equal | 0.511 (#1, tied) | 0.510 (#3, tied) | 0.504 (#4, tied) | 0.510 (#2) | 0.461 (#5, behind) |
| (d) rising windows only | 0.803 (#2, tied) | 0.799 (#3, tied) | 0.774 (#4, behind) | 0.805 (#1) | 0.699 (#5, behind) |
| (e) falling windows only | 0.396 (#2, ahead) | 0.388 (#3, ahead) | 0.357 (#5, tied) | 0.376 (#4) | 0.412 (#1, tied) |
| Worst day | -14.7% | -14.7% | -14.7% | -14.7% | -15.4% |
| Worst 14-day return | -30.0% | -29.9% | -29.7% | -30.8% | -26.1% |
| 5th-percentile return | -14.9% | -15.2% | -14.8% | -15.7% | -15.3% |
| Median max drawdown | 9.8% | 9.8% | 9.7% | 10.1% | 9.8% |
| 90th-percentile max drawdown | 18.0% | 18.3% | 17.9% | 18.7% | 18.9% |
| Longest losing streak (days) | 12 | 12 | 12 | 12 | 9 |
| Single-coin blow-up share | 3.52% | 3.39% | 3.66% | 3.96% | 7.27% |
| Fees per 14 days (% of starting equity) | 0.349% | 0.351% | 0.341% | 0.362% | 0.531% |

| vs vt_mom, per 14-day window | Rising (BTC > +2%) | Falling (< -2%) | Flat |
|---|---|---|---|
| H1 | -0.21 points (ahead in 29%) | +0.38 points (ahead in 57%) | -0.01 points (ahead in 43%) |
| H2 | -0.16 points (ahead in 24%) | +0.28 points (ahead in 53%) | -0.12 points (ahead in 31%) |
| E5 (no gate) | -0.48 points (ahead in 41%) | +0.37 points (ahead in 61%) | -0.09 points (ahead in 52%) |

**What it shows:**
- In falling windows, H1 keeps the advantage of buying half first: +0.38 points per window against vt_mom.
- In rising windows, it gives back much less than E5 (staging every time) did: −0.21 against −0.48.
- That is why it scores higher overall, with a slightly better worst window and drawdowns.

### Honest caveats
- **The edge is small.** +0.009 HEADLINE_RET overall, and only +0.0015 in the SCREEN period. Only two of the five
  views (current weights, and falling windows) separate H1 from vt_mom; the others are statistical ties.
- **The idea came from the same history.** H1 was designed after analysing E5 over these same 2,298 windows: staging
  paid in falling markets and cost in rising ones. Its rule was fixed in writing before it was run, but the backtest is
  not independent evidence for the idea itself.
- **Two hybrids were tested.** H1 and H2 both passed; H1 was the better of the two. Choosing the better of two adds a
  little optimism to its numbers.
- **The live round is the first out-of-sample test.** The shadow bots for vt_mom, E5 and H1 log their decisions, but
  their paper results are never used to decide.
- **The hourly engine** can differ from vt_mom's daily rebalancing in extreme hours (the 2021-01-28 window). This is
  shared by every book_orch version and already included in all the numbers above.
