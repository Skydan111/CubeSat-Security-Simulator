#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"


export SAT_ID="${SAT_ID:-SAT-001}"
export SAT_SECRET_HEX="${SAT_SECRET_HEX:-a54f2e7b3c9084ee2a6b9f1d77c4a3e9b2d1c0f4e6a8b0c2d4f6e8a0c1d2e3f4}"
export HMAC_SECRET_HEX="${HMAC_SECRET_HEX:-$SAT_SECRET_HEX}"

export MQTT_BROKER_HOST="${MQTT_BROKER_HOST:-localhost}"
export MQTT_BROKER_PORT="${MQTT_BROKER_PORT:-1883}"

export SECURITY_POLICY_PATH="${SECURITY_POLICY_PATH:-configs/security_policy.yaml}"
export DEDUP_CACHE_SIZE="${DEDUP_CACHE_SIZE:-500}"
export MAX_SKEW_SECONDS="${MAX_SKEW_SECONDS:-120}"

SUB_LOG="${SUB_LOG:-logs/control_center_subscriber.log}"
PID_DIR="${PID_DIR:-.run}"
mkdir -p "$(dirname "$SUB_LOG")" "$PID_DIR"

echo "[control_center_start] Project: $ROOT"
echo "[control_center_start] Starting MQTT broker (docker compose)..."
docker compose -f docker-compose.mqtt.yml up -d

echo "[control_center_start] Activating venv..."
source .venv/bin/activate


if [[ -f "$PID_DIR/subscriber.pid" ]] && kill -0 "$(cat "$PID_DIR/subscriber.pid")" 2>/dev/null; then
  echo "[control_center_start] Subscriber already running (pid=$(cat "$PID_DIR/subscriber.pid"))."
else
  echo "[control_center_start] Starting subscriber..."

  nohup python control_center/src/control_center/mqtt_subscriber.py >"$SUB_LOG" 2>&1 &
  echo $! > "$PID_DIR/subscriber.pid"
  echo "[control_center_start] Subscriber pid=$(cat "$PID_DIR/subscriber.pid"), log=$SUB_LOG"
fi

