#!/usr/bin/env bash
# Vortexa Studio — desktop / web LAN launch
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
export VORTEXA_PORT="${VORTEXA_PORT:-8766}"
export HTTP_PORT="${HTTP_PORT:-8080}"

# Stop previous
pkill -f "python3 server.py" 2>/dev/null || true
pkill -f "http.server ${HTTP_PORT}" 2>/dev/null || true
sleep 0.5

python3 server.py &
SPID=$!
python3 -m http.server "$HTTP_PORT" --bind 0.0.0.0 &
HPID=$!

IP=$(hostname -I 2>/dev/null | awk '{print $1}')
echo "Vortexa Studio desktop"
echo "  Local  → http://127.0.0.1:${HTTP_PORT}/?v=311"
if [ -n "$IP" ]; then
  echo "  LAN    → http://${IP}:${HTTP_PORT}/?v=311"
fi
echo "  WS     → ws://127.0.0.1:${VORTEXA_PORT}"
echo "PIDs server=$SPID http=$HPID  (Ctrl+C to stop this script only; use texoff or kill to stop services)"
wait
