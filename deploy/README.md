# Running the bot

The bot is `python -m src.live.runner run`: one registered model, every hour, on Roostoo. Its model and mode
come from `config.yaml` → `live:`, so every change to what it trades is a commit.

| Where | Mode | Key | How it runs |
|---|---|---|---|
| Research server (this one) | `paper`: simulated fills at live Roostoo quotes | none | tmux `mm-pol-live`, rehearsal only |
| Organizers' EC2 (Sydney) | `live` | the **competition** key, typed into `/opt/minimax/.env` by a human | systemd `minimax-bot` |

The runner refuses the competition key unless `MM_HOST=ec2` (set by the systemd unit).

## Every hour

About 45 s after each hour (UTC), the bot does the following:

1. **Bars.** It tops up its hourly bars in this order:
   - Binance's API, if reachable;
   - the next-day archive;
   - Roostoo's last price, for the newest hour only.

   The universe is ranked only on complete days, with Book's rule (top 30 by 30-day volume, ≥ 90 days of history), cut to Roostoo coins.
2. **Decision.** At the model's decision hours (16:00 UTC = 00:00 HKT for daily models), it calls the same `targets()` as the backtest.
   - The shared planner turns targets into orders, 10 s apart. Orders are never retried.
   - An order whose outcome is unknown stops the batch; the next hour re-plans from the real holdings.
3. **Activity guard.** From 21:00 HKT, if the HKT day has no trade yet, it rebalances exactly to the targets. If nothing needs trading, it makes a keep-alive trade (0.2% of equity in BTC, reversed the next day), as the backtest engine does.
4. **Logs and state.** One JSONL line per event goes to `data/live/logs/<YYYYMMDD>.jsonl`, stamped with the git commit; keys are never logged. The state is saved atomically to `data/live/state.json`.

## Before the AWS invite: rehearse here

```bash
cd /home/ubuntu/test/MiniMax/.worktrees/<member>-<task>        # or the root checkout once merged
PY=/home/ubuntu/test/MiniMax/.venv/bin/python                   # the shared venv
$PY -m src.live.runner seed                                     # once: 300 days of bars from the research panel
tmux new -d -s mm-pol-live "scripts/lock live-pol -- nice -n 10 $PY -m src.live.runner run --mode paper"
```

Check it once a day:
- the last `snapshot` line is less than an hour old;
- `active_days` grows by one per HKT day;
- there are no `error` lines.

## When the invite arrives

The organizers' EC2 is reached **only through Session Manager** (browser shell, no SSH key, no `scp`), and the account allows **one instance** (FAQ Q12, Q14). So the code goes through GitHub, which has to be public for the submission anyway. Decide with the team whether that happens now or the repo stays private with a read-only deploy token until Oct 9 (the submission date on the organizers' listing).

1. **Get the code there with its history**, so every log line's commit means something:

   ```bash
   git clone https://github.com/<team>/<repo>.git ~/minimax-src     # in the Session Manager shell
   bash ~/minimax-src/deploy/setup_ec2.sh
   ```

   `setup_ec2.sh` (Ubuntu or Amazon Linux):
   - installs Python, git and chrony, and points chrony at Amazon Time Sync (169.254.169.123);
   - installs the pinned packages (`deploy/requirements-lock.txt`, the versions the backtests ran on) into `/opt/minimax`;
   - installs the systemd unit under the current user;
   - runs the clock check.
2. **The clock must say OK.**

   ```bash
   cd /opt/minimax && .venv/bin/python -m src.live.runner clock
   ```

   It prints the machine clock, Roostoo's clock, the offset, and the NTP status from `timedatectl` and `chronyc tracking`. It must end with `RESULT OK`: offset ≤ `live.clock_warn_s` (2 s) and NTP synchronized.
   - The bot already keeps time by Roostoo's clock: machine clock plus the offset, measured every hour, logged as a `clock` event and warned on above 2 s.
   - Still, a drifting machine clock means something is wrong with the host, so fix it before going live. Roostoo rejects requests more than 60 s off.
3. **Seed the bars.** `setup_ec2.sh` copies `deploy/seed/` (the last 300 days of hourly bars for every panel series,
   committed with the code) into `data/live` when no store is there. The bot then fetches every hour after the seed's
   `complete_through` itself (Binance REST, else the daily archive plus the Roostoo ticker). Without a store the bot
   cannot start: it reads `data/live/close_1h.parquet` at startup. To refresh the seed before a push, copy a running
   paper bot's store, keeping only the bars up to its `complete_through`.
4. **Keys.** A teammate types `/opt/minimax/.env` by hand in the Session Manager shell, then runs `chmod 600 /opt/minimax/.env`:

   ```
   ROOSTOO_API_KEY=...
   ROOSTOO_SECRET_KEY=...
   ROOSTOO_ENV=competition
   ```

   Never paste a key into a chat, a prompt or a commit.
5. **Is Binance's API reachable from EC2?**

   ```bash
   curl -s -o /dev/null -w '%{http_code}\n' 'https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=1'
   ```

   200 means exact hourly bars. Anything else means the archive-plus-ticker fallback, which works (it runs that way here) but needs the bot running all the time so no hour goes unrecorded.
6. **Paper first.** With `live.mode: paper`:
   - run `cd /opt/minimax && .venv/bin/python -m src.live.runner run --once` and read the JSONL log;
   - then `sudo systemctl enable --now minimax-bot` and let it run until the switch.

## Going live (before Oct 4 12:00 UTC = 20:00 HKT)

The round is Roostoo competition 538: **2026-10-04 12:00 UTC → 2026-10-18 12:00 UTC**, $100,000 start, 0.1% taker and 0.05% maker fees, no leverage (from `/v1/competition_list`).

1. The launch branch (`feature/launch-e20v45`) already has `live.mode: live`, `live.model` and
   `live.start_at: "2026-10-04 12:00"` committed.
2. On EC2, before 12:00 UTC, the person who has the competition key runs this as ec2-user:

   ```bash
   bash /opt/minimax/deploy/go_live_round.sh
   ```

   - It asks for the key and secret first: hidden prompts, never printed. Ctrl+C there changes nothing.
   - Then it stops the bot and ends any test run, keeping that run's state aside, never reused.
   - It pulls the committed config, writes `.env` (`ROOSTOO_ENV=competition`, mode 600), checks the clock and
     starts the bot.
   - The bot refuses to start if `state.json` belongs to another account or to a run that began before
     `live.start_at`. It also refuses the competition key without `live.start_at`. So a test run's positions
     can never carry into the round.

   `bash /opt/minimax/deploy/status.sh` (read-only) shows:
   - the service and the config;
   - the last equity, round return and holdings;
   - the last decision and trade;
   - errors in the last 24 h.
3. Started any time before 12:00 UTC, the bot only records bars until the 12:00 bar. Then it makes its first decision and trades every difference from cash. Its next daily decision is at 16:00 UTC, on the research grid.

## During the round

- **Watch:** `journalctl -u minimax-bot -f`, and `tail -f /opt/minimax/data/live/logs/$(date -u +%Y%m%d).jsonl`.
- **Change anything** (model, parameters, code): commit on `main` → `git pull` on EC2 → `sudo systemctl restart minimax-bot`. A new `live.model` decides at the next hour, and the active days are kept.
- **Never stop the bot or override it by hand** (FAQ Q28: manual intervention is prohibited). The only restarts are deploying a committed change. At the end the system liquidates by itself (Q29).
- **Emergency exit:** never trade by hand; manual trades are against the rules. Commit `live.model: team_cash` and restart. At the next hour the bot sells everything and stays active through the keep-alive trade.
- **Shorts refused:** if the exchange answers "does not allow short positions", the bot trades long-only from then on (G4 in `docs/EVALUATION.md` checks that this fallback stays active and safe).
- **Clock:** the bot keeps time by Roostoo's server clock (offset re-measured every hour, `clock` events in the JSONL log). A `warning` or `error` level means the host's NTP has a problem: check `chronyc tracking`.

## Verified (2026-10-02, on EC2 and the TEST account)

- **Machine and network.** Binance's API is reachable from EC2 (200). The clock is synced (Amazon Time Sync). The
  launch template is Amazon Linux 2023; the setup installs Python 3.11.
- **Balance.** `/v3/balance` answers `SpotWallet` (plus an empty `MarginWallet`), not the documented `Wallet`.
  The client reads both.
- **Orders** (`selfcheck --orders`):
  - Market orders fill at the quote with a 0.1% fee.
  - LIMIT orders rest as PENDING/MAKER and cancel.
  - Shorts open, list in `/v6/short_positions` and close.
- **Live run.** On the test account it bought its 6 coins and confirmed every fill.
- **Rate limit.** No cap on trades per minute, only 30 API calls/min (FAQ Q22–23); the bot uses ≤ 20 and spaces
  orders 3 s apart.
- **Still unknown:** the competition account itself (it opens at the round's start).
