#!/usr/bin/env bash
# Prepare the EC2 host for the bot. Idempotent. Run from a checkout of the repo (see deploy/README.md):
#   bash deploy/setup_ec2.sh
# Works on Ubuntu (apt) and Amazon Linux (dnf/yum): the organizers' launch template does not say which.
set -euo pipefail
APP=/opt/minimax
SRC="$(cd "$(dirname "$0")/.." && pwd)"
ME="$(id -un)"

if command -v apt-get >/dev/null; then
  sudo apt-get update -y
  sudo apt-get install -y python3-venv git chrony
  CHRONY_CONF=/etc/chrony/chrony.conf
  PYBIN=python3
else
  PKG="$(command -v dnf || command -v yum)"
  sudo "$PKG" install -y git chrony
  # Amazon Linux 2023's python3 is 3.9; the pinned packages (numpy 2.2) need Python >= 3.10, so use python3.11
  if sudo "$PKG" install -y python3.11 python3.11-pip; then PYBIN=python3.11; else sudo "$PKG" install -y python3 python3-pip; PYBIN=python3; fi
  CHRONY_CONF=/etc/chrony.conf
fi
"$PYBIN" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' || {
  echo "Python >= 3.10 is needed for deploy/requirements-lock.txt; found $("$PYBIN" --version 2>&1). Install python3.11 and rerun."; exit 1; }

# Clock: the bot signs and schedules on Roostoo's time, but the machine must be close (Roostoo rejects > 60 s).
# Amazon Time Sync Service (169.254.169.123) is the recommended source inside EC2.
if ! grep -q "169.254.169.123" "$CHRONY_CONF"; then
  echo "server 169.254.169.123 prefer iburst minpoll 4 maxpoll 4" | sudo tee -a "$CHRONY_CONF" >/dev/null
fi
sudo systemctl enable chronyd 2>/dev/null || sudo systemctl enable chrony
sudo systemctl restart chronyd 2>/dev/null || sudo systemctl restart chrony
sudo chronyc makestep >/dev/null || true

if [ "$SRC" != "$APP" ]; then
  sudo mkdir -p "$APP" && sudo chown "$ME:$ME" "$APP"
  if [ ! -d "$APP/.git" ]; then git clone "$SRC" "$APP"; else git -C "$APP" pull --ff-only "$SRC"; fi
fi
"$PYBIN" -m venv "$APP/.venv"
"$APP/.venv/bin/pip" install -q --upgrade pip
"$APP/.venv/bin/pip" install -q -r "$APP/deploy/requirements-lock.txt"
mkdir -p "$APP/data/live"
if [ ! -f "$APP/data/live/close_1h.parquet" ] && [ -f "$APP/deploy/seed/close_1h.parquet" ]; then
  cp "$APP/deploy/seed/close_1h.parquet" "$APP/deploy/seed/qv_1h.parquet" "$APP/deploy/seed/store_meta.json" "$APP/data/live/"
  echo "Seeded $APP/data/live from deploy/seed; the bot fetches every later hour itself."
fi
sed "s/^User=ubuntu$/User=$ME/" "$APP/deploy/minimax-bot.service" | sudo tee /etc/systemd/system/minimax-bot.service >/dev/null
sudo systemctl daemon-reload

echo
echo "Installed in $APP (commit $(git -C "$APP" rev-parse --short=12 HEAD)), service user $ME."
echo "Clock check (must say RESULT OK before going live):"
(cd "$APP" && .venv/bin/python -m src.live.runner clock) || echo "CLOCK NOT OK: wait a minute for chrony, then rerun: cd $APP && .venv/bin/python -m src.live.runner clock"
[ -f "$APP/.env" ] || echo "MISSING: $APP/.env with ROOSTOO_API_KEY, ROOSTOO_SECRET_KEY, ROOSTOO_ENV (chmod 600). Type it in yourself."
[ -f "$APP/data/live/close_1h.parquet" ] || echo "MISSING: the seed store in $APP/data/live (deploy/seed/ in the repo; deploy/README.md step 3)."
echo "Then: cd $APP && .venv/bin/python -m src.live.runner run --once   # one hour, by hand, to check"
echo "      sudo systemctl enable --now minimax-bot && journalctl -u minimax-bot -f"
