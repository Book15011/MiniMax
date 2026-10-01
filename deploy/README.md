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

## When the invite arrives (target: Oct 2)

1. **Get the code there with its history**, so every log line's commit means something:

   ```bash
   git -C /home/ubuntu/test/MiniMax bundle create results/pol/minimax.bundle main   # research server
   # copy minimax.bundle to EC2, then on EC2:
   git clone minimax.bundle ~/minimax-src && bash ~/minimax-src/deploy/setup_ec2.sh
   ```

   `setup_ec2.sh` installs Python, chrony (clock sync) and the pinned packages (`deploy/requirements-lock.txt`, the versions the backtests ran on) into `/opt/minimax`, and installs the systemd unit.
2. **Seed the bars.** Copy `data/live/close_1h.parquet`, `qv_1h.parquet` and `store_meta.json` from the research server's paper bot to `/opt/minimax/data/live/`. They are current to the hour.
3. **Keys.** A teammate types `/opt/minimax/.env` by hand, then runs `chmod 600 /opt/minimax/.env`:

   ```
   ROOSTOO_API_KEY=...
   ROOSTOO_SECRET_KEY=...
   ROOSTOO_ENV=competition
   ```

   Never paste a key into a chat, a prompt or a commit.
4. **Is Binance's API reachable from EC2?**

   ```bash
   curl -s -o /dev/null -w '%{http_code}\n' 'https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1h&limit=1'
   ```

   200 means exact hourly bars. Anything else means the archive-plus-ticker fallback, which works (it runs that way here) but needs the bot running all the time so no hour goes unrecorded.
5. **Paper first.** With `live.mode: paper`:
   - run `cd /opt/minimax && .venv/bin/python -m src.live.runner run --once` and read the JSONL log;
   - then `sudo systemctl enable --now minimax-bot` and let it run at least a day.

## Going live (Oct 3, before 16:00 UTC = Oct 4 00:00 HKT)

1. Commit on `main`, reviewed: `live.mode: live`, the chosen `live.model`, and `live.start_at: "2026-10-03 16:00"`.
2. On EC2:

   ```bash
   git -C /opt/minimax pull /path/to/minimax.bundle main
   sudo systemctl stop minimax-bot
   mv /opt/minimax/data/live/state.json /opt/minimax/data/live/state-paper.json   # paper and live never share state
   sudo systemctl start minimax-bot && journalctl -u minimax-bot -f
   ```

3. Started any time before 16:00 UTC, the bot only records bars until the 16:00 bar. Then it makes its first decision and trades every difference from cash.

## During the round

- **Watch:** `journalctl -u minimax-bot -f`, and `tail -f /opt/minimax/data/live/logs/$(date -u +%Y%m%d).jsonl`.
- **Change anything** (model, parameters, code): commit on `main` → new bundle → `git pull` on EC2 → `sudo systemctl restart minimax-bot`. A new `live.model` decides at the next hour, and the active days are kept.
- **Emergency exit:** never trade by hand; manual trades are against the rules. Commit `live.model: team_cash` and restart. At the next hour the bot sells everything and stays active through the keep-alive trade.
- **Shorts refused:** if the exchange answers "does not allow short positions", the bot trades long-only from then on (G4 in `docs/EVALUATION.md` checks that this fallback stays active and safe).
- **Clock:** the bot measures its offset to Roostoo's server time every hour and signs with it.

## Not verified yet

- Whether Binance's API is reachable from EC2 (step 4).
- The format of `/v6/short_positions`: if the bot cannot read it, it switches to long-only.
- Fills, fees and limits on the competition account. Run `python -m src.live.selfcheck --orders` with the test key first.
- Whether Roostoo caps trades per minute this round (the bot spaces orders 10 s apart).
