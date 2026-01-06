from __future__ import annotations

import os
import sys
from typing import Optional

import paho.mqtt.client as mqtt

from shared.comm.envelope import EnvelopeV1
from shared.comm.topics import telemetry_topic


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
    # Callback: wird bei eingehenden Nachrichten aufgerufen.
    raw = msg.payload.decode("utf-8", errors="replace")

    try:
        env = EnvelopeV1.from_json(raw)
        print(f"[ground] RX topic={msg.topic} msg_id={env.msg_id} ts={env.ts_utc}")
    except Exception as e:
        print(f"[ground] Invalid message on {msg.topic}: {e} raw={raw}", file=sys.stderr)


def main() -> int:
    broker_host = _env("MQTT_BROKER_HOST", "localhost")
    broker_port = int(_env("MQTT_BROKER_PORT", "1883"))
    sat_id = _env("SAT_ID", "SAT-001")

    client = mqtt.Client(client_id=f"ground-{sat_id}", userdata={"sat_id": sat_id})
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"[ground] Connecting to mqtt://{broker_host}:{broker_port} (sat_id={sat_id})")
    client.connect(broker_host, broker_port, keepalive=30)
    client.loop_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
