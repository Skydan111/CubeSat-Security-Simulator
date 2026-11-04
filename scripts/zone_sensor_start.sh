#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

source .venv/bin/activate

export ZONE_ID="${ZONE_ID:-ZONE-01}"
export MQTT_BROKER_HOST="${MQTT_BROKER_HOST:-192.168.2.32}"
export MQTT_BROKER_PORT="${MQTT_BROKER_PORT:-1883}"


export TELEMETRY_FILE="${TELEMETRY_FILE:-data/logs/telemetry.csv}"
export PUBLISH_INTERVAL_S="${PUBLISH_INTERVAL_S:-2.0}"
export START_FROM_END="${START_FROM_END:-1}"

PID_DIR="${PID_DIR:-.run}"
mkdir -p "$PID_DIR" "$(dirname "$TELEMETRY_FILE")" logs

echo "[zone_sensor_start] Project: $ROOT"
echo "[zone_sensor_start] TELEMETRY_FILE=$TELEMETRY_FILE"
echo "[zone_sensor_start] MQTT: $MQTT_BROKER_HOST:$MQTT_BROKER_PORT"

# 1) Logger
if [[ -f "$PID_DIR/logger.pid" ]] && kill -0 "$(cat "$PID_DIR/logger.pid")" 2>/dev/null; then
  echo "[zone_sensor_start] Logger already running (pid=$(cat "$PID_DIR/logger.pid"))."
else
  echo "[zone_sensor_start] Starting logger..."
  nohup python -m zone_sensor.logger > logs/logger.log 2>&1 &
  echo $! > "$PID_DIR/logger.pid"
  echo "[zone_sensor_start] Logger pid=$(cat "$PID_DIR/logger.pid"), log=logs/logger.log"
fi

# 2) Publisher (follow file)
if [[ -f "$PID_DIR/publisher.pid" ]] && kill -0 "$(cat "$PID_DIR/publisher.pid")" 2>/dev/null; then
  echo "[zone_sensor_start] Publisher already running (pid=$(cat "$PID_DIR/publisher.pid"))."
else
  echo "[zone_sensor_start] Starting publisher_from_file..."
  nohup python -m zone_sensor.mqtt_publisher_from_file > logs/publisher.log 2>&1 &
  echo $! > "$PID_DIR/publisher.pid"
  echo "[zone_sensor_start] Publisher pid=$(cat "$PID_DIR/publisher.pid"), log=logs/publisher.log"
fi

echo "[zone_sensor_start] DONE"