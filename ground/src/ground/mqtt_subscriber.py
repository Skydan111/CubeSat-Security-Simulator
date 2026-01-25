from __future__ import annotations

import os
import sys
from typing import Optional

import paho.mqtt.client as mqtt

from shared.comm.envelope import EnvelopeV1, bytes_from_b64
from shared.comm.topics import telemetry_topic
from shared.protocol.signed_csv import verify_signed_line


def _env(name: str, default: str) -> str:
    # Liest Umgebungsvariablen mit Default-Werten.
    return os.getenv(name, default)


def on_connect(client: mqtt.Client, userdata: object, flags: dict, rc: int) -> None:
    # Callback: wird bei erfolgreicher Verbindung aufgerufen.
    sat_id: str = userdata["sat_id"]  # type: ignore[index]
    topic = telemetry_topic(sat_id)

    if rc != 0:
        print(f"[ground] MQTT connect failed rc={rc}", file=sys.stderr)
        return

    print(f"[ground] Connected. Subscribing to {topic}")
    client.subscribe(topic, qos=1)


def on_message(client: mqtt.Client, userdata: object, msg: mqtt.MQTTMessage) -> None:
    raw = msg.payload.decode("utf-8", errors="replace")

    try:
        env = EnvelopeV1.from_json(raw)

        signed_bytes = bytes_from_b64(env.payload_b64)
        signed_line = signed_bytes.decode("utf-8")

        secret_hex = userdata["secret_hex"]  # type: ignore[index]

        if not verify_signed_line(signed_line, secret_hex):
            print(
                f"[ground] REJECT msg_id={env.msg_id} reason=invalid_signature",
                file=sys.stderr,
            )
            return

        print(
            f"[ground] ACCEPT msg_id={env.msg_id} ts={env.ts_utc} payload={signed_line}"
        )

    except Exception as e:
        print(
            f"[ground] ERROR topic={msg.topic} err={e}",
            file=sys.stderr,
        )


def main() -> int:
    broker_host = _env("MQTT_BROKER_HOST", "localhost")
    broker_port = int(_env("MQTT_BROKER_PORT", "1883"))
    sat_id = _env("SAT_ID", "SAT-001")
    secret_hex = _env("SAT_SECRET_HEX", "deadbeef")

    client = mqtt.Client(
        client_id=f"ground-{sat_id}",
        userdata={
            "sat_id": sat_id,
            "secret_hex": secret_hex,
            },
            )
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"[ground] Connecting to mqtt://{broker_host}:{broker_port} (sat_id={sat_id})")
    client.connect(broker_host, broker_port, keepalive=30)
    client.loop_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
