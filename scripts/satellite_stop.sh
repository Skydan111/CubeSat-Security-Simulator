#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PID_DIR="${PID_DIR:-.run}"

stop_pidfile () {
  local f="$1"
  local name="$2"
  if [[ -f "$f" ]]; then
    local pid
    pid="$(cat "$f")"
    if kill -0 "$pid" 2>/dev/null; then
      echo "[satellite_stop] Stopping $name pid=$pid"
      kill "$pid" || true
    fi
    rm -f "$f"
  else
    echo "[satellite_stop] No $name pid file."
  fi
}

stop_pidfile "$PID_DIR/publisher.pid" "publisher"
stop_pidfile "$PID_DIR/logger.pid" "logger"
echo "[satellite_stop] DONE"