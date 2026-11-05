#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ ! -x "$ROOT/.venv/bin/python" || ! -d "$ROOT/Question-generation-project-integrated-frontend/node_modules" ]]; then
  echo "Dependencies are missing. Follow README.md setup instructions first." >&2
  exit 1
fi

listener_pid() {
  lsof -tiTCP:"$1" -sTCP:LISTEN 2>/dev/null | head -n 1
}

EXISTING_API_PID="$(listener_pid 8000 || true)"
EXISTING_WEB_PID="$(listener_pid 5173 || true)"
if [[ -n "$EXISTING_API_PID" && -n "$EXISTING_WEB_PID" ]]; then
  if curl --fail --silent --max-time 2 http://127.0.0.1:8000/health >/dev/null \
      && curl --fail --silent --max-time 2 http://127.0.0.1:5173/upload >/dev/null; then
    echo "Question Paper Generator is already running at http://127.0.0.1:5173"
    exit 0
  fi
  echo "Ports 8000 and 5173 are occupied, but the existing app did not answer its health checks." >&2
  echo "Listeners: backend PID $EXISTING_API_PID; frontend PID $EXISTING_WEB_PID." >&2
  exit 1
fi
if [[ -n "$EXISTING_API_PID" || -n "$EXISTING_WEB_PID" ]]; then
  echo "Cannot start because one required port is already occupied." >&2
  [[ -z "$EXISTING_API_PID" ]] || echo "Port 8000: PID $EXISTING_API_PID" >&2
  [[ -z "$EXISTING_WEB_PID" ]] || echo "Port 5173: PID $EXISTING_WEB_PID" >&2
  exit 1
fi

API_PID=""
WEB_PID=""
cleanup() {
  [[ -z "$API_PID" ]] || kill "$API_PID" 2>/dev/null || true
  [[ -z "$WEB_PID" ]] || kill "$WEB_PID" 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 130' INT TERM
(cd "$ROOT/Question-Paper-Generation-main" && exec "$ROOT/.venv/bin/python" -m uvicorn main:app --host 127.0.0.1 --port 8000) &
API_PID=$!
(cd "$ROOT/Question-generation-project-integrated-frontend" && exec node node_modules/vite/bin/vite.js) &
WEB_PID=$!
echo "Open http://127.0.0.1:5173 — press Ctrl+C to stop."
while kill -0 "$API_PID" 2>/dev/null && kill -0 "$WEB_PID" 2>/dev/null; do sleep 1; done
echo "A server stopped. Stopping its companion; check the error above (ports 8000 and 5173 must be free)." >&2
exit 1
