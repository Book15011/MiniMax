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

## How it shares the account with the hourly bot

- **The hourly bot** (`src.live.runner`, `live.sleeve` in `config.yaml`) sizes its model on the account minus the
  sleeve:
  - it never trades the sleeve's pairs;
  - it never spends the sleeve's free cash (read from `data/live/sleeve.json`);
  - without that file it keeps the sleeve's whole capital aside.
- **When the sleeve's capital changes** (including switching it on or off), the model re-decides at the next hour and
  trades every difference. That frees the sleeve's cash, or puts it back to work.
- **The round's return and the end-of-round lock-in** use the whole account. When the lock fires, the sleeve
  flattens and stops (`respect_lock`).
- **API calls:** the sleeve keeps its own ceiling (`calls_per_minute: 12`). It places no new orders in minutes 0–6 of
  each hour, which belong to the hourly bot, so together they stay under the exchange's 30 a minute.

## Switching it on (team runs these; Claude doesn't touch EC2 or keys)

1. **Canary on the TEST account first,** from the research server with the test key, through a repo script:
   `python -m src.live.fillcheck --limit --pair STO/USD --sizes 1000`.
   - **Pass if:** a buy at the bid fills within seconds as MAKER at 0.05%, and a sell one step up fills when the bid
     reaches it.
2. **Commit** `live.sleeve.enabled: true` with the agreed `capital_usd` and `lots_usd` on the launch branch, and pull
   it on EC2.
3. **Restart the hourly bot once**, so it reads the sleeve split: `sudo systemctl restart minimax-bot`.
   - It resumes from its state.
   - At the next hour it re-decides on its smaller share and sells down to free the sleeve's cash.
4. **Install and start the sleeve:**
   `sudo cp deploy/minimax-sleeve.service /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable --now minimax-sleeve`.
   - Until the hourly bot has freed the cash, its buys are refused and it waits (`waiting_for_cash` in its log).
5. **Watch:** `python -m src.live.sleeve status`, plus its log `data/live/logs/sleeve-YYYYMMDD.jsonl`.

## Stopping it

| What | How |
|---|---|
| **Flatten and stop** | Create `data/live/sleeve.KILL`, or commit `enabled: false`, then restart the hourly bot so it takes the cash back |
| **Automatic stops** | Daily loss 3% (no new buys until the next HKT day); total loss 8% of its capital (flatten and stop); 5 API errors in a row; 10 minutes before `live.end_at`; the end-of-round lock-in |
| **An order whose outcome is unknown** | The sleeve stops at once, to be reconciled before restarting |

## Still unverified

- **Our order latency from EC2.** The research server takes 1.5–6 s to reach Roostoo.
- **Whether Roostoo fills our orders the way the measured rule says.** That is the canary.
- **`CoinChange` / `UnitChange` in order replies:** the exact sign and fee convention. The sleeve uses absolute values.
