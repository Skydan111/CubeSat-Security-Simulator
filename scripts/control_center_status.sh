#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "[control_center_status] docker containers:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | sed -n '1p;/warehouse/p' || true

echo
echo "[control_center_status] subscriber:"
if [[ -f .run/subscriber.pid ]] && kill -0 "$(cat .run/subscriber.pid)" 2>/dev/null; then
  echo "RUNNING pid=$(cat .run/subscriber.pid)"
else
  echo "NOT RUNNING"
fi

echo
echo "[control_center_status] last processed lines:"
tail -n 3 data/processed/telemetry.csv 2>/dev/null || echo "(no processed file yet)"