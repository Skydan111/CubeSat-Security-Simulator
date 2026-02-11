#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PID_DIR="${PID_DIR:-.run}"

if [[ -f "$PID_DIR/subscriber.pid" ]]; then
  PID="$(cat "$PID_DIR/subscriber.pid")"
  if kill -0 "$PID" 2>/dev/null; then
    echo "[ground_stop] Stopping subscriber pid=$PID"
    kill "$PID" || true
  fi
  rm -f "$PID_DIR/subscriber.pid"
else
  echo "[ground_stop] No subscriber pid file."
fi

echo "[ground_stop] Stopping docker broker..."
docker compose -f docker-compose.mqtt.yml down || true