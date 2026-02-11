#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# === CONFIG (при желании вынеси в .env) ===
export SAT_ID="${SAT_ID:-SAT-001}"
export SAT_SECRET_HEX="${SAT_SECRET_HEX:-a54f2e7b3c9084ee2a6b9f1d77c4a3e9b2d1c0f4e6a8b0c2d4f6e8a0c1d2e3f4}"
export HMAC_SECRET_HEX="${HMAC_SECRET_HEX:-$SAT_SECRET_HEX}"

export MQTT_BROKER_HOST="${MQTT_BROKER_HOST:-localhost}"
export MQTT_BROKER_PORT="${MQTT_BROKER_PORT:-1883}"

export SECURITY_POLICY_PATH="${SECURITY_POLICY_PATH:-configs/security_policy.yaml}"
export DEDUP_CACHE_SIZE="${DEDUP_CACHE_SIZE:-500}"
export MAX_SKEW_SECONDS="${MAX_SKEW_SECONDS:-120}"

SUB_LOG="${SUB_LOG:-logs/ground_subscriber.log}"
PID_DIR="${PID_DIR:-.run}"
mkdir -p "$(dirname "$SUB_LOG")" "$PID_DIR"

echo "[ground_start] Project: $ROOT"
echo "[ground_start] Starting MQTT broker (docker compose)..."
docker compose -f docker-compose.mqtt.yml up -d

echo "[mac_start] Activating venv..."
source .venv/bin/activate

# если subscriber уже запущен — не дублируем
if [[ -f "$PID_DIR/subscriber.pid" ]] && kill -0 "$(cat "$PID_DIR/subscriber.pid")" 2>/dev/null; then
  echo "[ground_start] Subscriber already running (pid=$(cat "$PID_DIR/subscriber.pid"))."
else
  echo "[ground_start] Starting subscriber..."
  # важное: без ~ в имени файла :)
  nohup python ground/src/ground/mqtt_subscriber.py >"$SUB_LOG" 2>&1 &
  echo $! > "$PID_DIR/subscriber.pid"
  echo "[ground_start] Subscriber pid=$(cat "$PID_DIR/subscriber.pid"), log=$SUB_LOG"
fi

echo "[ground_start] Starting plot (GUI)..."
python ground/src/ground/plot.py --csv data/processed/telemetry.csv --interval 2 --window 120