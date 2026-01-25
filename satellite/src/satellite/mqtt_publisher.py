from __future__ import annotations


import os
import time
import uuid

import paho.mqtt.client as mqtt

from shared.comm.envelope import EnvelopeV1, b64_from_bytes
from shared.comm.topics import telemetry_topic
from shared.protocol.signed_csv import format_signed_line
from shared.protocol.telemetry_csv import TelemetryUnsigned


def _env(name: str, default: str) -> str:
    # Liest Umgebungsvariablen mit Default-Werten.
    return os.getenv(name, default)

def build_signed_payload_bytes(secret_hex: str) -> bytes:
    # Baut eine signierte Telemetrie-CSV-Zeile und gibt sie als Bytes zurück.

    # Demo-Telemetrie (später: echte Sensorwerte)
    unsigned = TelemetryUnsigned(
        ts=EnvelopeV1.now_utc_iso(),
        temperature_c=22.5,
        humidity_pct=45.0,
        pressure_hpa=1013.2,
        mode="NOMINAL",
    )

    signed_line = format_signed_line(unsigned, secret_hex)

    # MQTT transportiert Bytes → später Base64 im Envelope
    return signed_line.encode("utf-8")


def main() -> int:
    broker_host = _env("MQTT_BROKER_HOST", "localhost")
    broker_port = int(_env("MQTT_BROKER_PORT", "1883"))
    sat_id = _env("SAT_ID", "SAT-001")
    interval_s = float(_env("PUBLISH_INTERVAL_S", "2.0"))
    secret_hex = _env("SAT_SECRET_HEX", "deadbeef")

    topic = telemetry_topic(sat_id)

    client = mqtt.Client(client_id=f"sat-{sat_id}")
    client.connect(broker_host, broker_port, keepalive=30)
    client.loop_start()

    print(f"[satellite] Publishing to {topic} via mqtt://{broker_host}:{broker_port}")

    try:
        while True:
            signed_bytes = build_signed_payload_bytes(secret_hex)

            env = EnvelopeV1(
                v="1",
                sat_id=sat_id,
                msg_type="telemetry",
                msg_id=str(uuid.uuid4()),
                ts_utc=EnvelopeV1.now_utc_iso(),
                qos=1,
                payload_b64=b64_from_bytes(signed_bytes),
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
