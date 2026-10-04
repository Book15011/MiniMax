# Pre-registration: limit orders with a 2-5 minute wait, then market; shorts at market (Baitoey, 2026-10-05)

Written and committed before any run. Not edited after results exist; results go to
`results/baitoey/20261005-limit-exec/` and a report committed under `research/baitoey/results/`.

## Question

The live model (pol_switch_vt_tl_e20v45) trades with market orders: 0.1% fee plus half the spread. Roostoo charges
0.05% for limit (maker) fills. Would placing each long buy or sell as a limit order first, waiting W minutes, then
sending the rest at market, cost less? Shorts stay at market. Execution only: the same trades, the same strategy.

## Method

- **Trades:** the registered e20v45 run's trade log (`results/pol/20261002-scoring/pol_switch_vt_tl_e20v45-20261002-0620/trades.csv.gz`),
  windows starting 2025-09-01 to 2026-09-15 (inside the 1-minute data), coins with 1-minute Binance data. Spot trades
  only (weight before and after both >= 0); any trade touching a short stays at market and is left out of the
  comparison.
- **Prices:** mid at the trade hour T = the close of the 1-minute bar ending at T; half-spread h = the coin's half-spread
  from the Roostoo snapshot (the backtest's own spreads).
- **Market now (base):** cost h + 0.10% of the notional.
- **Limit then market:** a buy limit at the bid (mid - h), or at the mid, fills if a 1-minute low within the next W
  minutes trades strictly below it (sells mirror with highs and the ask); a fill costs (limit - mid) / mid + 0.05%.
  Unfilled: a market order at minute W at that minute's ask, cost (mid_W - mid) / mid + h + 0.10% (the move during the
  wait counts). Full fill or none (no partial fills); queue position ignored.
- **Runs:** W = 2 and 5 minutes, limit at the bid/ask (passive) and at the mid.

## Verdict (fixed now)

- **Worth proposing to the team** only if the passive limit saves at least 0.02% of the notional on average for both
  W = 2 and W = 5, and saves money in at least 3 of the 4 quarters (2025-Q4 to 2026-Q3) for both.
- Report-only: mid pricing, fill rates, buys vs sells, by trade kind (decision, entry, guard), and the saving per
  14-day round (notional-weighted saving over the round's trades, per $100,000).

## Known limits, stated before running

- Roostoo's limit-order matching is UNVERIFIED; Binance 1-minute lows and highs stand in for it, and a fill needs the
  price to trade through the limit.
- Overlapping windows repeat calendar trades; averages are per trade in the log.
- The live runner sends market orders; a limit-then-market rule would be new live code (Pol's area) that must cancel,
  confirm the filled part with query_order, and only then send the rest at market (AGENTS.md: never auto-retry
  orders), within 20 API calls a minute. Nothing here changes the live bot.
