# Tick-scalping sleeve: what it is, and how the team would switch it on (EXPERIMENTAL)

**Status: built and tested, not deployed.**
- Going live needs:
  1. the team's decision;
  2. `AGENTS.md` §2.6 amended through a reviewed merge (branch `feature/agents-tick-scalp`);
  3. the rollout below.
- Nothing runs unless `live.sleeve.enabled: true` is committed.

## What it does

- **The pairs:** BONK, STO and PEPE, where one price step (about 0.25%) is more than two maker fees (0.10%).
- **The loop, per coin:**
  - a limit buy at the bid;
  - a limit sell one step above the entry;
  - after a win, the next buy goes one step below the sell;
  - a stop at −2 steps (market sell);
  - a 60-minute pause after 3 stops within an hour.
- **Lots:** fixed USD per coin (`live.sleeve.lots_usd`).
- **Why it earns:** Roostoo fills a resting buy as soon as its bid reaches the price (no queue), and its bid flickers
  between neighbouring steps.
- **The organisers** say this is allowed and won't be disqualified, but judges won't value it as a strategy.

**Evidence, this code, replayed on Roostoo's own recorded prices** (`python -m src.live.sleeve replay`, Oct 5 12:11 →
Oct 7 10:00 HKT, 46 h, $60k sleeve at the default lots):

| Setting | Result |
|---|---|
| Default | **+15.6%** if never throttled (checks every 6 s) |
| Checks every 12 s | +12.1% |

- The bot's limiter caps the process at 20 calls a minute, so the live result should fall between the two.
- **The simulator** (a separate simulator study) agrees: +13–17% at the
  default lots.

## How it runs: one process, one instance

- **A thread of the hourly bot**, started when `live.sleeve.enabled`. It shares the bot's rate limiter (the whole
  process stays at 20 calls/min or fewer).
- **Minutes 0–5 of each hour belong to the hourly model.** No new sleeve orders then; stops still run.
- **Isolation:** if the sleeve thread fails or stops itself, the hourly model keeps running.
- **`mode: paper`:** no orders. Fills are simulated on the live quotes with Roostoo's measured rule, in
  `data/live/sleeve-paper.json`. It takes nothing from the model.
- **`mode: live`:** it trades. The model sizes itself on the account minus the sleeve:
  - it never trades the sleeve's pairs;
  - it never spends the sleeve's free cash (from `data/live/sleeve.json`);
  - when the sleeve's capital changes, it re-decides at the next hour;
  - when the sleeve has stopped for good and holds nothing, it takes the cash back.
- **The whole account** sets the round's return and the end-of-round lock-in. By default the lock does **not** stop
  the sleeve (`respect_lock: false`): its steady gains count toward the top-20 gate and its risk ratios.
- **Its log** is `data/live/logs/sleeve/YYYYMMDD.jsonl`. `deploy/status.sh` shows a `sleeve` line.

## Robustness

| Situation | What happens |
|---|---|
| Books | Booked from each fill's quantity, price and commission. Partial fills are read after every cancel. Coins are checked against the wallet every 5 minutes |
| An order whose outcome is unknown (timeout, 5xx) | Rebuilt from the exchange's open orders and the wallet. Not fatal |
| API errors | Back off from 30 s, doubling to 5 min. Only 60 minutes of continuous failure flattens and stops it |
| A refused buy (the model hasn't freed the cash yet, or any refusal) | That coin backs off. Before a live buy the wallet's free USD is checked (at most once a minute) |
| Edge breaker | A coin pauses 2 h if its last 30 trips lost money with a win rate under 60%. Normal trading never went below 67%; a broken fill rule gives 40–55% |
| A price step too small | No new buys while one step is under 0.15% of the price |
| A config change (paper → live, capital, lots) | Picked up at start, and logged |

## Switching it on: only through code updates (commit → pull on EC2 → restart, the allowed update path)

There is no test-account canary (team decision, 2026-10-08).

1. **Update A: paper inside the live bot.** Commit `enabled: true` (`mode: paper` is the default).
   - The live model is untouched.
   - After about a day, check `python -m src.live.sleeve status --mode paper` and the sleeve's log.
2. **Update B: live with a small capital** (`mode: live`, `capital_usd` about 10–20k, lots in the same proportions).
   - **Check:** buys at the bid fill within seconds as MAKER at 0.05%, sells fill when the bid reaches them, and
     there are no `rejected` or `reconcile_coins` storms.
3. **Update C: the agreed size,** if B behaves like the replays.

## Stopping it

| What | How |
|---|---|
| **Flatten and stop** | Create `data/live/sleeve.KILL`, or commit `enabled: false` / `mode: paper` and update. The model takes the cash back at the next hour |
| **Automatic** | Daily loss 3% (no new buys until the next HKT day); total loss 8% of its capital (flatten and stop); 60 min of API failure; 10 minutes before `live.end_at`; the edge breaker (per coin, 2 h) |

## Still unverified

- **Our order latency from EC2.** The research server takes 1.5–6 s to reach Roostoo.
- **Whether Roostoo fills our own orders as the measured rule says.** Update B is the check.
- **The exact fee fields in order replies.** Books use the quantity, the price and the commission, and coins are
  reconciled with the wallet.
