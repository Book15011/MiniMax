# Pre-registration: a take-profit overlay on baitoey_vt_mom (Baitoey, 2026-10-06)

Written and committed before any code runs on data. Not edited after results exist; results go to
`results/baitoey/20261006-tp-overlay/` and reports committed under `research/baitoey/results/`.

## The overlay (Baitoey's spec)

- At each daily decision (the window's first decision and every 16:00 UTC), for each coin held after that decision's
  trades, a resting limit sell at decision_price x (1 + tp_pct) for tp_fraction of the position. decision_price is
  the coin's close at the decision bar.
- It fills only if a LATER hourly bar's high reaches the target: the first eligible bar is the one after the decision's
  fill bar (the engine fills a decision at the next bar's close), the last is the next decision bar (the order is
  cancelled at the next decision). Fill at the target price, maker fee 0.05%. Never the bar that set the target.
- After a fill the proceeds stay in cash until the next decision. There, if the model still holds the coin, the normal
  rebalance buys the sold part back at that fill bar's close, with the taker fee and the coin's half-spread; if the
  model drops the coin, the overlay saves that sale's cost.

| Run | tp_pct | tp_fraction |
|---|---|---|
| A | none | none (vt_mom as registered) |
| B | 8% | 1.0 |
| C | 12% | 1.0 |
| D | 8% | 0.5 |

## Method

The registered baitoey_vt_mom run (tool version 3036a0d8bfdaa6a0): its hourly equity paths and its trade log give each
coin's holdings hour by hour (units after a trade = weight after x equity / close). The overlay changes the path only
through its events: between a fill and the next decision fill bar the sold part is cash instead of the coin; at that
bar the difference is settled (buy-back cost or saved sale cost) and carried forward as a change in account size.
Hourly highs come from the Binance 1-hour klines (data/binance_spot/klines_1h, read-only) and, from 2026-09-01, the
1-minute data resampled; a coin with no high falls back to its close. Fortnight return = R_liq of the 14-day window
(12:00 UTC starts). REL = Pol's period REL (backtest.scoring.returnfirst.pol_period_rel: field-best bar, V1-V4
FLOORED composites, 0.7 live-like + 0.3 recency weights) on the overlay's per-window metrics (window_metrics, HKT
day points). Check: A must reproduce vt_mom's registered period_check (SCREEN 1.029, CONFIRM 2.562).

Periods (windows by start date, config.yaml harness.periods): SCREEN 2022-07-01 to 2024-06-30, CONFIRM 2024-07-01 to
2026-07-25. **SCREEN first; its report is committed; then CONFIRM is run once, with nothing changed.**
Script: `research/baitoey/tp_overlay.py`; tests: `tests/test_baitoey_tp_overlay.py`.

Reported per period and variant: median, 75th and 90th percentile fortnight return; how often a take-profit order
fills (share of coin-decisions, and fills per round); after a fill, how often the coin is bought back higher vs lower
than the fill price; fees per round (the engine's fees and spread plus the overlay's maker fees and buy-back costs,
less saved sale costs, per $100,000 at the window start); REL and REL minus A's REL.

## Verdict (fixed now)

A variant is **better** in a period if its REL is at least 0.05 above A's and its median fortnight return is not lower
than A's. **Propose** a variant only if it is better in both SCREEN and CONFIRM. Otherwise **keep vt_mom without a
take-profit**.

## Known limits, stated before running

- An overlay on the registered paths: the model's later decisions are unchanged (it would size slightly differently
  with a different account size; the change is carried as a proportional scale). The buy-back ignores the band (any
  coin still held is bought back). Guard trades are taken from the log as they were.
- Hourly highs from Binance; Roostoo's limit-order matching is UNVERIFIED (a live limit may fill less often).
- The post-holdout windows are not in either period. The round is live; nothing here changes the live bot.

## Addendum before any run (2026-10-06)

vt_mom's log has guard trades every day at 04:00 UTC that resize each holding (by -20% to +22% at the 1st/99th
percentile; none sells a coin to zero). Taken "as they were" after a fill, they would sell units the overlay has
already sold (a short remnant) or buy back early. So, for the coin whose order filled only: the overlay skips that
coin's trades between the fill and the next decision fill bar (it holds the cash, as the spec says, and keeps the
unsold part fixed). At that bar it trades from its own holding to the model's holding, at the taker fee plus the coin's
half-spread, and the model's own cost for that trade is credited back. Other coins' guard trades are taken as they
were. Written before any overlay number exists; nothing else changes.
