#!/usr/bin/env bash
# MiniMax: switch the EC2 bot to the ROUND (the competition account). Once, before 2026-10-04 12:00 UTC (20:00 HKT),
# by the person who has the competition API key, as ec2-user:   bash /opt/minimax/deploy/go_live_round.sh
# It asks for the key first (hidden, never printed or logged; Ctrl+C there changes nothing), then: stops the bot,
# ends any test run (its state is kept aside, never reused), takes the committed config from GitHub
# (live.mode: live, live.start_at = the round's start), saves the key in .env (mode 600), checks the clock and
# starts the bot. Until live.start_at the bot only records prices; it trades from the round's first hour.
set -euo pipefail
# all in one function: bash parses it before running, so the git pull below cannot change the running script
main() {
cd /opt/minimax
[ "$(id -un)" = ec2-user ] || { echo "Run this as ec2-user (sudo su - ec2-user), not $(id -un)."; exit 1; }
BR=$(git rev-parse --abbrev-ref HEAD)
echo "== 1/5 the committed config on GitHub ($BR)"
git fetch -q origin "$BR"
CFG=$(git show "origin/$BR:config.yaml")
grep -E '^  (model|mode|start_at):' <<<"$CFG" | sed 's/ *#.*//'
grep -q '^  mode: live' <<<"$CFG" || { echo "GitHub's config is not live.mode: live yet: nothing changed."; exit 1; }
grep -qE '^  start_at: "[0-9]' <<<"$CFG" || { echo "GitHub's config has no live.start_at: nothing changed."; exit 1; }

echo "== 2/5 the COMPETITION key (paste each value; nothing shows while you paste; then press Enter)"
read -r -s -p "   competition API key: " K; echo
read -r -s -p "   competition secret key: " S; echo
if [ -z "$K" ] || [ -z "$S" ]; then echo "Nothing pasted: nothing changed."; exit 1; fi

echo "== 3/5 stop the bot, end any test run, take the committed code and config"
sudo systemctl stop minimax-bot
git checkout -- config.yaml
git pull -q --ff-only origin "$BR"
echo "   code now $(git rev-parse --short HEAD)"
sed "s/^User=ubuntu$/User=$(id -un)/" deploy/minimax-bot.service | sudo tee /etc/systemd/system/minimax-bot.service >/dev/null
sudo systemctl daemon-reload                                    # the committed service settings (restart policy)
STAMP=$(date -u +%Y%m%d%H%M)
if [ -f data/live/state.json ]; then
  mv data/live/state.json "data/live/state-before-round-$STAMP.json"
  echo "   the previous run's state kept as data/live/state-before-round-$STAMP.json (never reused)"
fi
umask 077
printf 'ROOSTOO_API_KEY=%s\nROOSTOO_SECRET_KEY=%s\nROOSTOO_ENV=competition\n' "$K" "$S" > .env
chmod 600 .env
unset K S
echo "   key saved in /opt/minimax/.env ($(stat -c '%A %U' .env))"

echo "== 4/5 clock (must say RESULT OK; the bot runs on Roostoo's clock either way)"
.venv/bin/python -m src.live.runner clock | grep -E "offset|RESULT" || true

echo "== 5/5 start"
sudo systemctl start minimax-bot
for _ in $(seq 20); do sleep 3; grep -q '"event": "start"' "data/live/logs/$(date -u +%Y%m%d).jsonl" 2>/dev/null && break; done
systemctl is-active minimax-bot
.venv/bin/python - <<'EOF'
import json, pathlib, datetime
f = pathlib.Path("data/live/logs") / f"{datetime.datetime.now(datetime.timezone.utc):%Y%m%d}.jsonl"
ev = [json.loads(x) for x in f.read_text().splitlines()] if f.exists() else []
st = [e for e in ev if e["event"] == "start"]
if st and st[-1]["mode"] == "live":
    print(f"STARTED: {st[-1]['model']} live, commit {st[-1]['commit']}, trades from {st[-1]['start_at']}")
    print("Until then it only records prices. Check any time:  bash /opt/minimax/deploy/status.sh")
else:
    print("NOT STARTED as expected: run  journalctl -u minimax-bot -n 30  and send the lines (never the .env) to the team")
EOF
}
main "$@"
