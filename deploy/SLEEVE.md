# Tick-scalping sleeve: what it is, and how the team would switch it on (EXPERIMENTAL)

**Status: built and tested, not deployed.**
- Switching it on needs **all** of these:
  1. the team's decision;
  2. `AGENTS.md` §2.6 amended through a reviewed merge (it still says "no market-making");
  3. a passed canary.
- Nothing here runs unless `live.sleeve.enabled: true` is committed.

## What it does

- **The pairs:** BONK, STO and PEPE, the three Roostoo pairs where one price step (about 0.25%) is more than two maker
  fees (0.10%).
- **The loop, per coin:**
  - a limit buy at the bid;
  - a limit sell one step above the entry;
  - after a win, the next buy goes one step below the sell;
  - a stop at −2 steps (market sell);
  - a 60-minute pause after 3 stops within an hour.
- **Lots:** fixed USD per coin (`live.sleeve.lots_usd`).
- **Evidence:**
  - `reports/review/20261006-tick-scalp-results.md` §7 on `an earlier branch`: the replay on Roostoo's own recorded prices
    makes about +13–17% of $100k over 46–56 h at the default lots, positive in rising, falling and flat
    windows;
- **Why it works:** Roostoo fills a resting buy as soon as its bid reaches the price (no queue), and its bid flickers
  between neighbouring steps.
- **The organisers** say this is allowed and won't be disqualified, but judges won't value it as a strategy. It would
  not survive a real order book.

## How it runs: one process, one instance

- **A thread of the hourly bot.** The sleeve is not a separate service: `src.live.runner` starts it as a thread when
  `live.sleeve.enabled`. One instance, one process.
- **One shared ceiling.** The sleeve's client shares the bot's rate limiter, so the whole process stays under
  `execution.calls_per_minute` (20).
  - The sleeve places no new orders in minutes 0–6 of each hour, which belong to the hourly model. In those minutes
    it polls every 30 s; its stops still run.
- **Isolation.** If the sleeve thread fails or stops itself, the hourly model keeps running (tested).
- **`mode: paper`:** no orders. Fills are simulated on the live quotes with Roostoo's measured rule, in
  `data/live/sleeve-paper.json`. It takes nothing from the model.
- **`mode: live`:** it trades. The hourly model then sizes itself on the account minus the sleeve:
  - it never trades the sleeve's pairs;
  - it never spends the sleeve's free cash (read from `data/live/sleeve.json`; without it, the whole capital is kept
    aside);
  - when the sleeve's capital changes, the model re-decides at the next hour and frees or reclaims the cash.
- **The whole account** sets the round's return and the end-of-round lock-in. When the lock fires, the sleeve
  flattens and stops.

## Switching it on: only through code updates (commit → pull on EC2 → restart, the allowed update path)

There is no test-account canary (team decision, 2026-10-08). The paper steps replace it.

1. **Update A: paper inside the live bot.** Commit `live.sleeve: {enabled: true, mode: paper}` on the launch branch
   and update EC2 as usual.
   - The live model is untouched. The sleeve paper-trades on EC2's own quotes and latency.
   - Check `python -m src.live.sleeve status --mode paper` and `data/live/logs/sleeve-*.jsonl` for a day.
2. **Update B: live with a small capital** (the canary in practice): `mode: live`, `capital_usd` about 10–20k, lots
   in the same proportions.
   - At the next hour the model re-decides on its share and frees the cash. The sleeve waits for it
     (`waiting_for_cash`).
   - **Check the fills:** buys at the bid fill within seconds, the role is MAKER at 0.05%, and sells fill when the bid
     reaches them.
3. **Update C: the agreed size,** if B behaves like the paper runs.

## Stopping it

| What | How |
|---|---|
| **Flatten and stop** | Create `data/live/sleeve.KILL` (a file the bot reads), or commit `enabled: false` / `mode: paper` and update. The model takes the cash back at the next hour |
| **Automatic stops** | Daily loss 3% (no new buys until the next HKT day); total loss 8% of its capital (flatten and stop); 5 API errors in a row; 10 minutes before `live.end_at`; the end-of-round lock-in; an order whose outcome is unknown (stop; reconcile before the next update) |

## Still unverified

- **Our order latency from EC2.** The research server takes 1.5–6 s to reach Roostoo.
- **Whether Roostoo fills our own orders the way the measured rule says.** Update B is the check.
- **`CoinChange` / `UnitChange` in order replies:** the exact sign and fee convention. The sleeve uses absolute values.
