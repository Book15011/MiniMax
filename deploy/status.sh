#!/usr/bin/env bash
# MiniMax: how is the bot doing? Read-only: no keys, no exchange calls, changes nothing.
#    bash /opt/minimax/deploy/status.sh            (on EC2, any user)
cd "$(dirname "$0")/.." || exit 1
echo "service   $(systemctl is-active minimax-bot 2>/dev/null) since $(systemctl show -p ActiveEnterTimestamp --value minimax-bot 2>/dev/null)"
echo "code      $(git rev-parse --short HEAD) on $(git rev-parse --abbrev-ref HEAD)$(git diff --quiet || echo ' (LOCAL EDITS)')"
echo "config    $(grep -E '^  (model|mode|start_at):' config.yaml | sed 's/ *#.*//; s/^ *//' | tr '\n' ' ')"
echo "key file  $([ -f .env ] && stat -c '%A %U' .env || echo MISSING)"
PY=.venv/bin/python; [ -x "$PY" ] || PY=python3
"$PY" - <<'EOF'
import json, pathlib
from datetime import datetime, timedelta, timezone
d = pathlib.Path("data/live")
st = json.loads((d / "state.json").read_text()) if (d / "state.json").exists() else {}
print(f"state     account {st.get('account', '?')}, mode {st.get('mode', '?')}, last hour {st.get('last_bar')}, "
      f"last decision {st.get('last_decision')}, round start {st.get('round_start')}")
if st.get("locked_at"):
    print(f"LOCKED    end-of-round lock-in since {st['locked_at']}: holding cash to the end (live.endgame)")
now = datetime.now(timezone.utc)
ev = []
for f in sorted((d / "logs").glob("*.jsonl"))[-3:]:
    ev += [json.loads(x) for x in f.read_text().splitlines() if x.strip()]
snap = [e for e in ev if e["event"] == "snapshot"]
if snap:
    s = snap[-1]
    age = (now - datetime.fromisoformat(s["ts"])).total_seconds() / 60
    line = f"equity    ${s['equity']:,.2f} at bar {s['bar'][:16]} UTC ({age:.0f} min ago{'; LATE' if age > 70 else ''})"
    if s.get("waiting_until"):
        line += f"; waiting for the round, trades from {str(s['waiting_until'])[:16]} UTC"
    elif s.get("round_over"):
        line += "; the round is over, no more trades"
    else:
        line += f"; gross {s.get('gross', 0):.2f}, active days {s.get('active_days')}"
        if st.get("round_start_equity"):
            line += f"; round return {s['equity'] / st['round_start_equity'] - 1:+.2%}"
    print(line)
    w = s.get("weights") or {}
    if w:
        print("holdings  " + ", ".join(f"{k.split('/')[0]} {v:+.0%}" for k, v in sorted(w.items(), key=lambda kv: -abs(kv[1]))))
dec = [e for e in ev if e["event"] == "decision"]
if dec:
    print(f"decision  {dec[-1]['bar'][:16]} UTC: {len(dec[-1].get('targets') or {})} positions")
trades = [e for e in ev if e["event"] in ("rebalance", "guard", "keep_alive", "endgame") and e.get("fills")]
if trades:
    t = trades[-1]
    print(f"trade     {t['bar'][:16]} UTC {t['event']}: " + ", ".join(sorted({f['status'] for f in t['fills']})))
err = [e for e in ev if e["event"] == "error" and now - datetime.fromisoformat(e["ts"]) < timedelta(hours=24)]
print(f"errors    {len(err)} in the last 24 h" + (f"; latest: {err[-1]['error'][:160]}" if err else ""))
EOF
