from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

import paho.mqtt.client as mqtt

from shared.comm.envelope import EnvelopeV1, b64_from_bytes
from shared.comm.topics import telemetry_topic
from shared.protocol.signed_csv import format_signed_line
from shared.protocol.telemetry_csv import TelemetryUnsigned


ROOT = Path(__file__).resolve().parents[3]
COMPOSE_FILE = ROOT / "docker-compose.mqtt.yml"

PROCESSED_FILE = ROOT / "data" / "processed" / "telemetry.csv"


def _count(path: Path) -> int:
    # Zählt Datenzeilen (ohne Header). Falls Datei fehlt -> 0.
    if not path.exists():
        return 0
    return sum(
        1
        for l in path.read_text(encoding="utf-8").splitlines()
        if l.strip() and not l.lower().startswith("ts,")
    )


def test_mqtt_tampering_drop_and_log() -> None:
    sat_id = "SAT-001"
    secret_hex = "deadbeef"
    topic = telemetry_topic(sat_id)

    subprocess.run(
        ["docker", "compose", "-f", str(COMPOSE_FILE), "up", "-d"],
        check=True,
        cwd=str(ROOT),
    )
    time.sleep(0.5)

    before_ok = _count(PROCESSED_FILE)

    env = os.environ.copy()
    env["SAT_ID"] = sat_id
    env["SAT_SECRET_HEX"] = secret_hex
    env["MQTT_BROKER_HOST"] = "localhost"
    env["MQTT_BROKER_PORT"] = "1883"
    env["PYTHONUNBUFFERED"] = "1"
    env["SECURITY_POLICY_PATH"] = "configs/security_policy.yaml"

    sub = subprocess.Popen(
        ["python", "-u", "ground/src/ground/mqtt_subscriber.py"],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        # Subscriber Zeit geben für connect/subscribe
        time.sleep(1.0)

        client = mqtt.Client(client_id="tamper-test")
        client.connect("localhost", 1883, keepalive=30)
        client.loop_start()

        unsigned = TelemetryUnsigned(
            ts=EnvelopeV1.now_utc_iso(),
            temperature_c=22.5,
            humidity_pct=45.0,
            pressure_hpa=1013.2,
            mode="NOMINAL",
        )

        # korrekt signierte Zeile
        signed_line = format_signed_line(unsigned, secret_hex)

        # TAMPERING: Payload ändern, Signatur bleibt unverändert -> muss invalid werden
        tampered_line = signed_line.replace("22.50", "99.99")

        env_msg = EnvelopeV1(
            v="1",
            sat_id=sat_id,
            msg_type="telemetry",
            msg_id="tamper-001",
            ts_utc=EnvelopeV1.now_utc_iso(),
            qos=1,
            payload_b64=b64_from_bytes(tampered_line.encode("utf-8")),
        )

        info = client.publish(topic, payload=env_msg.to_json(), qos=1, retain=False)
        info.wait_for_publish(timeout=3)

        client.loop_stop()
        client.disconnect()

        # Verarbeitung abwarten
        time.sleep(2.0)

        after_ok = _count(PROCESSED_FILE)
        assert after_ok == before_ok, "Tampered message must not be processed"

    finally:
        # Subscriber stoppen und Logs lesen
        if sub.poll() is None:
            sub.terminate()
            try:
                sub.wait(timeout=3)
            except subprocess.TimeoutExpired:
                sub.kill()

        out = sub.stdout.read() if sub.stdout else ""
        err = sub.stderr.read() if sub.stderr else ""

        subprocess.run(
            ["docker", "compose", "-f", str(COMPOSE_FILE), "down"],
            cwd=str(ROOT),
            check=False,
        )

    # Erwartung: sauberer Log-Eintrag (mindestens invalid signature / reject)
    combined = (out + "\n" + err).lower()
    assert ("reject" in combined) or ("invalid_signature" in combined) or ("invalid signature" in combined), (
        f"Expected tampering to be logged (reject/invalid_signature). Output was:\nSTDOUT:\n{out}\nSTDERR:\n{err}"
    )