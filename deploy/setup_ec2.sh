#!/usr/bin/env bash
# Prepare an Ubuntu EC2 host for the bot. Idempotent. Run from a checkout of the repo:
#   bash deploy/setup_ec2.sh            (see deploy/README.md for the steps before and after)
set -euo pipefail
APP=/opt/minimax
SRC="$(cd "$(dirname "$0")/.." && pwd)"

sudo apt-get update -y
sudo apt-get install -y python3-venv git chrony
sudo systemctl enable --now chrony            # Roostoo rejects requests more than 60 s off its clock

if [ "$SRC" != "$APP" ]; then
  sudo mkdir -p "$APP" && sudo chown "$USER:$USER" "$APP"
  if [ ! -d "$APP/.git" ]; then git clone "$SRC" "$APP"; else git -C "$APP" pull --ff-only "$SRC"; fi
fi
python3 -m venv "$APP/.venv"
"$APP/.venv/bin/pip" install -q --upgrade pip
"$APP/.venv/bin/pip" install -q -r "$APP/deploy/requirements-lock.txt"
mkdir -p "$APP/data/live"
sudo cp "$APP/deploy/minimax-bot.service" /etc/systemd/system/minimax-bot.service
sudo systemctl daemon-reload

echo
echo "Installed in $APP (commit $(git -C "$APP" rev-parse --short=12 HEAD))."
[ -f "$APP/.env" ] || echo "MISSING: $APP/.env with ROOSTOO_API_KEY, ROOSTOO_SECRET_KEY, ROOSTOO_ENV (chmod 600). Type it in yourself."
[ -f "$APP/data/live/close_1h.parquet" ] || echo "MISSING: the seed store in $APP/data/live (deploy/README.md step 3)."
echo "Then: cd $APP && .venv/bin/python -m src.live.runner run --once   # one hour, by hand, to check"
echo "      sudo systemctl enable --now minimax-bot && journalctl -u minimax-bot -f"
