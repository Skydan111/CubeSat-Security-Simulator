from __future__ import annotations

import os
import time
import uuid
from pathlib import Path

import paho.mqtt.client as mqtt

from shared.comm.envelope import EnvelopeV1, b64_from_bytes
from shared.comm.topics import telemetry_topic


def _env(name: str, default: str) -> str:
    # Liest Umgebungsvariablen mit Default-Werten.
    return os.getenv(name, default)


def normalize_ts_to_z(line: str) -> str:
    # Normalisiert ts von "...+00:00" nach "...Z" (falls vorhanden).
    parts = line.strip().split(",")
    if len(parts) < 6:
        return line.strip()  # lassen wir später vom Ground rejecten
    ts = parts[0]
    if ts.endswith("+00:00"):
        parts[0] = ts.replace("+00:00", "Z")
    return ",".join(parts)


def is_data_line(line: str) -> bool:
    # Filtert Header/Leerzeilen heraus.
    s = line.strip()
    if not s:
        return False
    if s.lower().startswith("ts,"):
        return False
    return True


def main() -> int:
    broker_host = _env("MQTT_BROKER_HOST", "localhost")
    broker_port = int(_env("MQTT_BROKER_PORT", "1883"))
    sat_id = _env("SAT_ID", "SAT-001")
    interval_s = float(_env("PUBLISH_INTERVAL_S", "2.0"))
    telemetry_file = Path(_env("TELEMETRY_FILE", "data/logs/telemetry.csv"))

    topic = telemetry_topic(sat_id)

    client = mqtt.Client(client_id=f"sat-{sat_id}-file")
    client.connect(broker_host, broker_port, keepalive=30)
    client.loop_start()

    print(f"[satellite] Publishing (follow file) to {topic} via mqtt://{broker_host}:{broker_port}")
    print(f"[satellite] TELEMETRY_FILE={telemetry_file}")

    # Startmodus: "tail" -> nur neue Zeilen ab jetzt senden (nicht die Historie).
    # Falls du einmalig die Historie senden willst: setze START_FROM_END=0.
    start_from_end = _env("START_FROM_END", "1") == "1"

    try:
        # Warten, bis die Datei existiert (Logger könnte später starten)
        while not telemetry_file.exists():
            print(f"[satellite] Waiting for telemetry file: {telemetry_file}")
            time.sleep(1.0)

        with telemetry_file.open("r", encoding="utf-8") as f:
            if start_from_end:
                f.seek(0, 2)  # ans Dateiende springen

            while True:
                pos_before = f.tell()
                line = f.readline()

                if not line:
                    # Keine neuen Daten: kurz schlafen und erneut probieren
                    f.seek(pos_before)
                    time.sleep(interval_s)
                    continue

                if not is_data_line(line):
                    continue

                signed_line = line.strip()

                env = EnvelopeV1(
                    v="1",
                    sat_id=sat_id,
                    msg_type="telemetry",
                    msg_id=str(uuid.uuid4()),
                    ts_utc=EnvelopeV1.now_utc_iso(),
                    qos=1,
                    payload_b64=b64_from_bytes(signed_line.encode("utf-8")),
                )

                client.publish(topic, payload=env.to_json(), qos=1, retain=False)
                print(f"[satellite] TX msg_id={env.msg_id} ts={signed_line.split(',', 1)[0]}")

    finally:
        client.loop_stop()
        client.disconnect()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())