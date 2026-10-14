# How Roostoo really fills our orders, and what it means for tick scalping (2026-10-14, Book)

Measured on the competition account (STO/USD, about $200 an order, `fillprobe.py`, run on EC2 with the bot's own
client), plus the four sleeve probe buys of Oct 13/14. Quotes from our public-ticker recorder
(`results/book/scalp/quotes/`, 6 s samples).

## What Roostoo does

| Order | What happened | Rule it implies |
|---|---|---|
| Market buy | Filled at once at the shown **ask** (0.0364), taker fee 0.1% in USD | "The price you see is the fill price" holds for market orders: you pay the ask |
| Resting buy at the bid (4 orders, Oct 13/14) | Never filled, 24-200 s each, while the bid sat exactly at its price; the **last** price stayed one step above every time | A resting buy needs a trade at or below its price (last <= P), or the ask to come down to it; bid = price is not enough |
| Resting sell at the ask (= the last price) | Unfilled for 5+ minutes while the bid stayed one step below | A resting sell needs the **bid** to reach it; last = price is not enough |
| Order query after a cancel | Every cancelled, unfilled buy (4 of 4) came back CANCELED with `FilledQuantity` = the whole quantity | Never trust a cancelled order's filled quantity; check the wallet (fixed in `c1b521a`) |

## Why the backtest said 85-88% wins

The paper sleeve and every scalping backtest assumed a resting buy fills as soon as the bid equals its price. That reading was an assumption. On our account it does not
happen, and those fills were the whole edge.

## Scalping under the measured rules (Oct 8-13 recorded quotes, live lots BONK 41.3k / STO 12.5k / PEPE 6.2k)

| Loop | Buy fills when | Stop | Win | Per day |
|---|---|---|---|---|
| Resting buy, sell +1 step | a trade prints <= price (best case) | 2 steps | 76% | -1.6% |
| Same | same | 4 steps | 87% | -0.5% |
| Same | same | 8 steps | 92% | -1.3% |
| Same, no stop | same | none | 100% | +0.2% (closed trips only: it mostly sits on unsold coins) |
| Resting buy, sell +1 step | the ask comes down to price | 2 steps | 42% | -10.6% |
| Market buy (at the ask), sell +1 step | at once | 2 steps | 30% | -29% |

No version has an edge: the buy fills mostly when the price is already falling, and the sell needs a real move up.

## Files

- `fillprobe.py`: the live experiment (market buy; limit sell at the ask; market sell; limit buy one step under the
  bid; limit sell one step up; limit buy at the bid for 8 minutes; always ends flat).
- The backtest above and the sweep below ran on a research branch, on our recorded quotes.

Still running when this was written: the experiment's buy-one-step-below and buy-at-the-bid-for-8-minutes steps.
