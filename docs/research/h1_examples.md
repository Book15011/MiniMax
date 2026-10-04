# How H1 trades: one rising, one falling and one neutral window

Each example is a 14-day backtest window from 12:00 UTC, starting with $100,000 in cash.

**When H1 checks and what it does:**
- It checks every hour.
- At the start and at **16:00 UTC** each day, it decides which coins to hold (vt_mom's choice).
- At that check it reads **breadth**: the share of the 20 most liquid coins in an up-trend.
  - **Breadth below 0.60** (a weak market): it buys a new coin **half first**, and the rest at 00:00 UTC.
    For a coin bought at the window start, the rest comes at 16:00.
    Exception: a coin with a perfect trend score and below-median volatility is still bought in full.
  - **Breadth 0.60 or more:** it buys new coins **in full**.
- Between those checks it only sells a coin back to its target if the coin's weight drifts more than 5 points.
- Orders fill one hour after the check.

**How to read the tables:**
- Each row is one check that traded.
- "→ 12%" is the coin's share of equity after the trade.
- **Not listed:** about 5 tiny trades a day (about $200 each) that keep the account active for the competition
  (the daily activity trade). Their total is given under each table.
- All three windows come from the registered H1 run; the full brief is [h1_brief.md](h1_brief.md).

## Rising market: 2026-09-15 to 09-29 (BTC +9.6%)

**Result:** H1 +28.56%, vt_mom +27.33%, live model +36.46%. Staging was on at 4 of 15 daily decisions.

| Check (UTC) | Breadth | Buys | Sells |
|---|---|---|---|
| 09-15 12:00 (start) | 0.45 → half first | NEAR $6.7k (half → 7%); TRX $6.7k (half → 7%); UNI $6.7k (half → 7%); XLM $13.4k (full: strong, calm coin → 13%); XRP $6.7k (half → 7%); ZEC $6.7k (half → 7%) | - |
| 09-15 16:00 | 0.50 → half first | ARB $6.2k (half → 6%); NEAR $5.8k (2nd half → 13%); TRX $5.8k (2nd half → 13%); UNI $6.1k (2nd half → 13%); ZEC $5.9k (2nd half → 13%) | XRP $6.6k (exit) |
| 09-16 00:00 | 00:00 top-up | ARB $6.1k (2nd half → 13%) | - |
| 09-16 16:00 | 0.30 → half first | BNB $6.6k (half → 7%) | XLM $12.0k (exit) |
| 09-17 00:00 | 00:00 top-up | BNB $7.0k (2nd half → 13%) | - |
| 09-17 16:00 | 0.50 → half first | BMT $6.2k (half → 6%) | TRX $12.4k (exit) |
| 09-18 00:00 | 00:00 top-up | BMT $6.5k (2nd half → 11%) | - |
| 09-18 16:00 | 1.00 → full | SOL $13.7k (full → 11%) | BMT $12.8k (exit) |
| 09-18 17:00 | between checks | - | NEAR $6.1k (drift back → 11%) |
| 09-19 16:00 | 0.95 → full | AVAX $13.3k (full → 11%) | BNB $14.0k (exit) |
| 09-22 16:00 | 1.00 → full | BTC $16.8k (full → 13%); SUI $16.8k (full → 13%) | ARB $14.1k (exit); AVAX $14.5k (exit) |
| 09-23 16:00 | 0.85 → full | AVAX $19.2k (full → 15%); TAO $19.2k (full → 15%) | NEAR $17.0k (exit); UNI $14.8k (exit) |
| 09-24 16:00 | 0.90 → full | LTC $20.8k (full → 16%) | ZEC $19.5k (exit) |
| 09-25 16:00 | 1.00 → full | ENA $15.1k (full → 12%); NEAR $15.1k (full → 12%) | BTC $20.4k (exit); LTC $20.1k (exit); SUI $7.3k (resize → 12%) |
| 09-25 22:00 | between checks | - | TAO $6.6k (drift back → 12%) |
| 09-27 16:00 | 0.95 → full | ONDO $15.4k (full → 12%) | AVAX $15.9k (exit) |
| 09-28 16:00 | 1.00 → full | HBAR $15.5k (full → 12%) | SUI $14.4k (exit) |

Not listed: 66 daily activity trades, $71.1k in all. All trades: 110, fees $590.

## Falling market: 2026-03-21 to 04-04 (BTC -4.9%)

**Result:** H1 -0.88%, vt_mom -1.57%, live model +3.64%. Staging was on at 14 of 15 daily decisions.

| Check (UTC) | Breadth | Buys | Sells |
|---|---|---|---|
| 03-21 12:00 (start) | 0.60 → full | ETH $15.0k (full → 15%); FET $15.0k (full → 15%); SOL $15.0k (full → 15%); TAO $15.0k (full → 15%); TRX $15.0k (full → 15%); ZEC $15.0k (full → 15%) | - |
| 03-24 16:00 | 0.30 → half first | WLFI $8.1k (half → 8%) | ZEC $14.9k (exit) |
| 03-25 00:00 | 00:00 top-up | WLFI $8.3k (2nd half → 16%) | - |
| 03-25 16:00 | 0.55 → half first | LINK $8.2k (half → 8%) | WLFI $16.2k (exit) |
| 03-26 00:00 | 00:00 top-up | LINK $8.2k (2nd half → 15%) | - |
| 03-26 16:00 | 0.15 → half first | FIL $8.5k (half → 8%); WLFI $8.5k (half → 8%) | FET $15.5k (exit); TAO $16.2k (exit) |
| 03-27 00:00 | 00:00 top-up | FIL $8.6k (2nd half → 17%); WLFI $8.4k (2nd half → 17%) | - |
| 03-27 16:00 | 0.15 → half first | TAO $8.3k (half → 8%) | SOL $13.8k (exit) |
| 03-28 00:00 | 00:00 top-up | TAO $8.4k (2nd half → 17%) | - |
| 03-28 16:00 | 0.15 → half first | DOGE $8.2k (half → 8%); FET $8.2k (half → 8%) | FIL $16.1k (exit); LINK $15.1k (exit) |
| 03-29 00:00 | 00:00 top-up | DOGE $8.2k (2nd half → 16%); FET $8.3k (2nd half → 16%) | - |

Not listed: 54 daily activity trades, $17.7k in all. All trades: 81, fees $332.

## Neutral (flat) market: 2026-09-06 to 09-20 (BTC +0.7%)

**Result:** H1 +13.85%, vt_mom +13.85%, live model +15.29%. Staging was on at 5 of 15 daily decisions.

| Check (UTC) | Breadth | Buys | Sells |
|---|---|---|---|
| 09-06 12:00 (start) | 0.95 → full | ARB $14.4k (full → 14%); BNB $14.4k (full → 14%); LTC $14.4k (full → 14%); NEAR $14.4k (full → 14%); UNI $14.4k (full → 14%); ZEC $14.4k (full → 14%) | - |
| 09-06 16:00 | 0.95 → full | LINK $13.6k (full → 13%) | BNB $14.2k (exit) |
| 09-07 16:00 | 0.95 → full | WLD $12.8k (full → 13%) | NEAR $13.0k (exit) |
| 09-08 16:00 | 0.95 → full | BNB $13.4k (full → 14%) | LINK $12.9k (exit) |
| 09-09 16:00 | 0.95 → full | NEAR $13.0k (full → 13%) | WLD $12.7k (exit) |
| 09-10 16:00 | 0.65 → full | TRX $14.6k (full → 16%) | NEAR $12.4k (exit) |
| 09-17 16:00 | 0.50 → half first | NEAR $12.3k (full: strong, calm coin → 12%) | TRX $14.3k (exit) |
| 09-18 03:00 | between checks | - | ARB $6.2k (drift back → 12%); BNB $1.5k (drift back → 12%); LTC $1.6k (drift back → 12%); NEAR $1.0k (drift back → 12%); UNI $4.8k (drift back → 12%); ZEC $2.4k (drift back → 12%) |
| 09-19 16:00 | 0.95 → full | AVAX $11.4k (full → 10%); ENA $11.4k (full → 10%) | BNB $13.4k (exit); LTC $13.0k (exit) |

Not listed: 78 daily activity trades, $51.8k in all. All trades: 106, fees $364.
