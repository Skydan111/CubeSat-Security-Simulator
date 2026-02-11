#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

source .venv/bin/activate

export SAT_ID="${SAT_ID:-SAT-001}"
export MQTT_BROKER_HOST="${MQTT_BROKER_HOST:-192.168.2.32}"   # IP твоего Mac
export MQTT_BROKER_PORT="${MQTT_BROKER_PORT:-1883}"

# Файл телеметрии, который пишет logger (должен совпадать с configs/satellite.json)
export TELEMETRY_FILE="${TELEMETRY_FILE:-data/logs/telemetry.csv}"
export PUBLISH_INTERVAL_S="${PUBLISH_INTERVAL_S:-2.0}"
export START_FROM_END="${START_FROM_END:-1}"

PID_DIR="${PID_DIR:-.run}"
mkdir -p "$PID_DIR" "$(dirname "$TELEMETRY_FILE")" logs

echo "[satellite_start] Project: $ROOT"
echo "[satellite_start] TELEMETRY_FILE=$TELEMETRY_FILE"
echo "[satellite_start] MQTT: $MQTT_BROKER_HOST:$MQTT_BROKER_PORT"

# 1) Logger
if [[ -f "$PID_DIR/logger.pid" ]] && kill -0 "$(cat "$PID_DIR/logger.pid")" 2>/dev/null; then
  echo "[satellite_start] Logger already running (pid=$(cat "$PID_DIR/logger.pid"))."
else
  echo "[satellite_start] Starting logger..."
  nohup python -m satellite.logger > logs/logger.log 2>&1 &
  echo $! > "$PID_DIR/logger.pid"
  echo "[satellite_start] Logger pid=$(cat "$PID_DIR/logger.pid"), log=logs/logger.log"
fi

# 2) Publisher (follow file)
if [[ -f "$PID_DIR/publisher.pid" ]] && kill -0 "$(cat "$PID_DIR/publisher.pid")" 2>/dev/null; then
  echo "[satellite_start] Publisher already running (pid=$(cat "$PID_DIR/publisher.pid"))."
else
  echo "[satellite_start] Starting publisher_from_file..."
  nohup python satellite/src/satellite/mqtt_publisher_from_file.py > logs/publisher.log 2>&1 &
  echo $! > "$PID_DIR/publisher.pid"
  echo "[satellite_start] Publisher pid=$(cat "$PID_DIR/publisher.pid"), log=logs/publisher.log"
fi

echo "[satellite_start] DONE"