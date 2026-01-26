from __future__ import annotations

import os
import sys
from typing import Optional

import paho.mqtt.client as mqtt

from shared.comm.envelope import EnvelopeV1, bytes_from_b64
from shared.comm.topics import telemetry_topic
from shared.protocol.signed_csv import verify_signed_line
from ground.mqtt_guard import GuardConfig, MqttMessageGuard
from ground.receiver import ingest_raw_line, handle_verified_line
from ground.security.security_manager import SecurityManager
from pathlib import Path


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

        guard: MqttMessageGuard = userdata["guard"]  # type: ignore[index]

        # 1) Dedup
        if guard.is_duplicate(env.sat_id, env.msg_id):
            print(f"[ground] DROP_DUPLICATE msg_id={env.msg_id}", file=sys.stderr)
            return

        # 2) Freshness
        if not guard.is_fresh(env.ts_utc):
            print(f"[ground] DROP_STALE msg_id={env.msg_id} ts={env.ts_utc}", file=sys.stderr)
            return

        # 3) Decode Signed Payload
        signed_bytes = bytes_from_b64(env.payload_b64)
        signed_line = signed_bytes.decode("utf-8")

        # 4) Verify signature
        secret_hex = userdata["secret_hex"]  # type: ignore[index]
        if not verify_signed_line(signed_line, secret_hex):
            print(f"[ground] REJECT_BAD_SIG msg_id={env.msg_id}", file=sys.stderr)
            return

        # 5) ACCEPT (Pipeline-Integration kommt im nächsten Schritt)
        secman = userdata["secman"]  # type: ignore[index]
        qpath = userdata["quarantine_path"]  # type: ignore[index]

        # Optional: RAW Spur für Forensik/Debug (unverändert)
        ingest_raw_line(signed_line)

        # Übergabe an die bestehende Pipeline (ohne erneute Signaturprüfung)
        handle_verified_line(
            signed_line,
            secman=secman,
            source="mqtt",
            quarantine_path=qpath,
        )

        print(f"[ground] ACCEPT msg_id={env.msg_id} ts={env.ts_utc}")

    except Exception as e:
        print(f"[ground] ERROR topic={msg.topic} err={type(e).__name__}: {e}", file=sys.stderr)


def main() -> int:
    broker_host = _env("MQTT_BROKER_HOST", "localhost")
    broker_port = int(_env("MQTT_BROKER_PORT", "1883"))
    sat_id = _env("SAT_ID", "SAT-001")
    secret_hex = _env("SAT_SECRET_HEX", "deadbeef")

    policy_path = _env("SECURITY_POLICY_PATH", "configs/security_policy.yaml")
    secman = SecurityManager(policy_path=policy_path)

    quarantine_path = Path("data/quarantine/telemetry.csv")
    dedup_size = int(_env("DEDUP_CACHE_SIZE", "500"))
    max_skew = int(_env("MAX_SKEW_SECONDS", "120"))
    guard = MqttMessageGuard(GuardConfig(dedup_size=dedup_size, max_skew_seconds=max_skew))

    client = mqtt.Client(
        client_id=f"ground-{sat_id}",
        userdata={
            "sat_id": sat_id,
            "secret_hex": secret_hex,
            "guard": guard,
            "secman": secman,
            "quarantine_path": quarantine_path,
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
