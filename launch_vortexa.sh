#!/usr/bin/env bash
# Vortexa Studio launcher
# Install as:  mkdir -p ~/bin && ln -sf "$(pwd)/launch_vortexa.sh" ~/bin/texlaunch
# Then just type:  texlaunch

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

PORT_WS="${VORTEXA_PORT:-8766}"
PORT_HTTP="${VORTEXA_HTTP_PORT:-8080}"
HOST="${VORTEXA_HOST:-127.0.0.1}"

echo "=================================================="
echo "  VORTEXA STUDIO v2.1  –  texlaunch"
echo "=================================================="

# Free previous instances
pkill -f "python3 server.py" 2>/dev/null || true
pkill -f "http.server ${PORT_HTTP}" 2>/dev/null || true
sleep 0.8

# Optional dependency check
python3 -c "import websockets, numpy" 2>/dev/null || {
  echo "[*] Installing dependencies..."
  pip install -q -r requirements.txt
}

# Start WebSocket computation bridge
echo "[*] Starting bridge  ws://${HOST}:${PORT_WS}"
VORTEXA_HOST="$HOST" VORTEXA_PORT="$PORT_WS" \
  python3 server.py > server.log 2>&1 &
BRIDGE_PID=$!

# Start static HTTP server for the UI
echo "[*] Starting UI      http://${HOST}:${PORT_HTTP}"
python3 -m http.server "$PORT_HTTP" --bind "$HOST" > http.log 2>&1 &
HTTP_PID=$!

sleep 0.6

if kill -0 "$BRIDGE_PID" 2>/dev/null; then
  echo "    Bridge PID  : $BRIDGE_PID  (ok)"
else
  echo "    Bridge failed – see server.log"
fi
if kill -0 "$HTTP_PID" 2>/dev/null; then
  echo "    HTTP PID    : $HTTP_PID  (ok)"
else
  echo "    HTTP failed – see http.log"
fi

echo ""
echo "Open:   http://127.0.0.1:${PORT_HTTP}"
echo "Stop:   kill $BRIDGE_PID $HTTP_PID"
echo "        or:  pkill -f 'python3 server.py'; pkill -f 'http.server'"
echo "=================================================="
echo "$BRIDGE_PID $HTTP_PID" > .vortexa.pids
