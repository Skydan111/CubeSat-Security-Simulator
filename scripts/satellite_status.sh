#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "[satellite_status] logger:"
if [[ -f .run/logger.pid ]] && kill -0 "$(cat .run/logger.pid)" 2>/dev/null; then
  echo "RUNNING pid=$(cat .run/logger.pid)"
else
  echo "NOT RUNNING"
fi

echo "[satellite_status] publisher:"
if [[ -f .run/publisher.pid ]] && kill -0 "$(cat .run/publisher.pid)" 2>/dev/null; then
  echo "RUNNING pid=$(cat .run/publisher.pid)"
else
  echo "NOT RUNNING"
fi

echo
echo "[satellite_status] last telemetry lines:"
tail -n 3 data/logs/telemetry.csv 2>/dev/null || echo "(no telemetry file yet)"