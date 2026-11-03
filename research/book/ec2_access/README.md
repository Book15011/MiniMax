# EC2 access: how the bot's instance was reached (Oct 14-15)

The route that worked from a Windows PC, step by step. Facts observed on Oct 14-15; AWS permissions may change.

## Target

| Item | Value |
|---|---|
| Instance | `i-0fcf5ff7472a15e52` |
| Region | `ap-southeast-2` |
| Bot checkout | `/opt/minimax`, owned by `ec2-user` |
| Bot Python | `/opt/minimax/.venv/bin/python` |
| Bot status script | `deploy/status.sh` (read-only) |

## What the hackathon role allows (observed)

- Allowed: `ssm start-session` with `--document-name AWS-StartInteractiveCommand` (one command per session).
- Denied: `ssm send-command`, plain interactive shell sessions, `ec2 describe-instances`, session listing.
- Keys are temporary (`ASIA...` + session token) from the AWS access portal. They expired after ~15-60 min; an
  expired key shows as `403 ... Forbidden` on StartSession. Get a fresh block and rerun `keys_to_session.py`.

## One-time setup (local PC)

```
python -m venv venv
venv\Scripts\pip install awscli==1.46.1 boto3
venv\Scripts\python get_plugin.py        # unpacks the official Session Manager plugin into plugin_dl\, no installer
```

## Each time

1. Copy the temporary-credentials block from the AWS access portal.
2. `venv\Scripts\python keys_to_session.py` and paste it (Ctrl+Z, Enter). This writes `session.json` here.
   `session.json` is gitignored; keep it on the local PC (AGENTS.md §2.3: never commit or paste keys) and delete it
   when done.
3. Check the connection: `venv\Scripts\python sess.py script probe.sh` prints hostname, uptime and UTC time.

## Running things

| Need | Command | Notes |
|---|---|---|
| Short command | `python sess.py raw "<cmd>"` | No single quotes allowed (it runs inside `bash -c '...'`). |
| Script file | `python sess.py script file.sh` | Sent gzip+base64; must be under ~3,400 chars encoded. The script must print something or the session hangs. |
| Read-only bot status | `python sess.py script status.sh` | `deploy/status.sh`, current commit, uncommitted changes. |
| Long Python job | `python make_bg_runner.py job.py` then `python sess.py script run_job.sh` | Runs with `nohup` under the bot's venv, output to `/tmp/job.out`; survives key expiry. Read later with `read_job.sh`. |
| Large file | `python upload.py local_file /tmp/name` | 3,000-char base64 pieces, one session each; prints sha256 on both sides. |

## Moving code (git bundle)

1. On metallurgy-server: `git bundle create /tmp/x.bundle <base>..<branch>` and copy the bundle to the local PC.
2. `python upload.py x.bundle /tmp/x.bundle`; compare the two sha256 values.
3. On EC2, through a script run with `sess.py`, as `ec2-user` in `/opt/minimax`: check `sha256sum -c`, check
   `git status --porcelain --untracked-files=no` is empty and `git rev-parse HEAD` is the expected commit, then
   `git bundle verify` and `git fetch /tmp/x.bundle <branch>:<branch>`. Fetching does not change the checked-out
   files or the running bot.

AGENTS.md §2.3: the competition key lives only on EC2 and is used only by the running bot; it is never used for
manual Roostoo calls.
