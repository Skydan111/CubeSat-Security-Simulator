from __future__ import annotations

import os
import time
import uuid

import paho.mqtt.client as mqtt

from shared.comm.envelope import EnvelopeV1
from shared.comm.topics import telemetry_topic


def _env(name: str, default: str) -> str:
    # Liest Umgebungsvariablen mit Default-Werten.
    return os.getenv(name, default)


def main() -> int:
    broker_host = _env("MQTT_BROKER_HOST", "localhost")
    broker_port = int(_env("MQTT_BROKER_PORT", "1883"))
    sat_id = _env("SAT_ID", "SAT-001")
    interval_s = float(_env("PUBLISH_INTERVAL_S", "2.0"))

    topic = telemetry_topic(sat_id)

    client = mqtt.Client(client_id=f"sat-{sat_id}")
    client.connect(broker_host, broker_port, keepalive=30)
    client.loop_start()

    print(f"[satellite] Publishing to {topic} via mqtt://{broker_host}:{broker_port}")

    try:
        while True:
            env = EnvelopeV1(
                v="1",
                sat_id=sat_id,
                msg_type="telemetry",
                msg_id=str(uuid.uuid4()),
                ts_utc=EnvelopeV1.now_utc_iso(),
                qos=1,
                payload_b64="AA==",  # Platzhalter für Signed Payload (wird im nächsten Schritt ersetzt)
            )
            payload = env.to_json()
            client.publish(topic, payload=payload, qos=1, retain=False)
            print(f"[satellite] TX msg_id={env.msg_id}")
            time.sleep(interval_s)
    finally:
        client.loop_stop()
        client.disconnect()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
