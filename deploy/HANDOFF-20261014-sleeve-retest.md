# Handoff to Pol: fix the sleeve and re-test it at $5k (2026-10-14, Book)

Hand this whole file to your coding agent. Branch `feature/sleeve-fix` on the research server repo
(`/home/ubuntu/test/MiniMax`), three commits on top of the live code:

| Commit | What |
|---|---|
| `1a83d90` | the live code now on EC2 (unchanged) |
| `c1b521a` | the fix: two bookkeeping bugs in `src/live/sleeve.py`, with 2 new tests |
| `d1ca8e8` | the sleeve at test size: `capital_usd: 5000`, `lots_usd: {"STO/USD": 5000}`, probe on |

## Rules for the agent (read first)

1. Do the steps in order. Change nothing else.
2. **A step is done only when its output shows the expected lines.** After every step, send Book the **raw output**
   of the listed commands, copied as it is. A summary like "it worked" is not enough.
3. If any output differs from what is expected: **stop**, send the output, wait.
4. Never edit files on EC2 by hand. Never run `git reset --hard` or `git clean`. Never delete anything in `data/`
   (move it). Never open or print `.env`.
5. Restart only inside minutes :10-:50 of an hour, and never between 15:50 and 16:10 UTC (the daily decision).

## Why

Yesterday (2026-10-13 16:24-16:30 UTC) the sleeve stopped after one test buy, from two bookkeeping bugs, not a
real loss:
1. Its STO test buy never filled and was cancelled. Roostoo's order query returned it CANCELED with the full
   quantity as filled, and the sleeve booked a $5k buy that never happened.
2. The wallet check then found 0 STO, zeroed the coins, but did not give the $5k back. The books showed -8.33%
   and the -8% total-loss limit stopped it for good.

The fix books a cancelled buy only as far as the wallet holds the coins, and gives back the cost of coins the
wallet does not hold. Both new tests fail on `1a83d90` and pass with the fix; the full suite passes (274).

The real question is still open: whether Roostoo fills our buy when the bid only **equals** its price. The test
(probe) answers it: up to 5 STO buys of $5k at the bid.

## Step A: put `feature/sleeve-fix` on EC2

The research server cannot reach GitHub. Move the branch the way you moved `1a83d90` (for example: on your
laptop, fetch `feature/sleeve-fix` from the research server, push it to GitHub, then fetch it on EC2). Then on EC2:

```bash
cd /opt/minimax
sudo -u ec2-user git fetch origin feature/sleeve-fix
sudo -u ec2-user git checkout feature/sleeve-fix
sudo -u ec2-user git log --oneline -4
sudo -u ec2-user git diff --stat 1a83d90
bash deploy/status.sh | head -4
```

**Expected:** the log shows this handoff commit, `d1ca8e8`, `c1b521a`, `1a83d90` (same hashes: commits move
unchanged). The diff lists only `config.yaml`, `deploy/HANDOFF-20261014-sleeve-retest.md`, `src/live/sleeve.py`,
`tests/test_sleeve.py`. Status shows `service active` and no `(LOCAL EDITS)`. The running bot keeps its old code
until the restart in step B.

## Step B: clear the stopped sleeve and restart

```bash
cd /opt/minimax
sudo -u ec2-user mv data/live/sleeve.json data/live/sleeve.json.stopped-20261013
sudo systemctl restart minimax-bot
sleep 90
bash deploy/status.sh
sudo -u ec2-user tail -n 15 data/live/logs/sleeve/$(date -u +%Y%m%d).jsonl
```

**Expected:**
- status: `service active`, code `... on feature/sleeve-fix`, model still `book_e20combo_brk_cash`;
- sleeve log: `"event": "start"` with `"capital": 5000.0` and `"coins": {"STO/USD": 5000.0}`, then an
  `"event": "order"` STO BUY of about $5,000.

The hourly model is unchanged, so it does not re-decide. At the next hour it frees $5k for the sleeve by trimming
its coins a little (a few dollars of fees).

## Step C: watch the test (15-60 minutes)

```bash
cd /opt/minimax
sudo -u ec2-user grep -h '"event": "probe' data/live/logs/sleeve/*.jsonl | tail -n 8
sudo -u ec2-user grep -h -E '"event": "(fill|fill_not_in_wallet|reconcile_cash|flatten|rejected|sleeve_thread)"' data/live/logs/sleeve/*.jsonl | tail -n 20
bash deploy/status.sh
```

Send Book this output **every 15 minutes** until one of these:

| You see | Meaning | Do |
|---|---|---|
| `"event": "probe_done"` with `"status": "passed"` | our buys at the bid do fill: the edge is real | keep it running at $5k; send Book the output; wait |
| `"event": "probe_done"` with `"status": "failed"`, then `flatten` "probe: buys at the bid did not fill" | Roostoo does not fill us that way: the strategy cannot work for us | nothing; it stopped for good and the hourly model takes the $5k back at the next hour |
| `flatten` for any other reason (`total_loss`, errors), a traceback, or repeated `rejected` | a new problem | stop; send the output; do not retry |

## Step D: 100% to the sleeve (only after a PASS, and only on Book's message)

Not prepared as a commit. If the probe passes and Book says go, the change is three lines in `config.yaml`
(`live.model: team_cash`; `live.sleeve.capital_usd: 80000`;
`live.sleeve.lots_usd: {"BONK/USD": 55100, "STO/USD": 16600, "PEPE/USD": 8300}`), committed, then a restart. The
model change makes the bot sell the hourly model's coins at once; that is intended. Verify the same way as step B
(sleeve `capital_change`, then trips and wins growing in the status line).

## Stop the sleeve at any time

```bash
sudo -u ec2-user touch /opt/minimax/data/live/sleeve.KILL
```

It flattens and stops; the hourly model takes the cash back at the next hour. No restart needed.
