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
    if not path.exists():
        return 0
    return sum(
        1
        for l in path.read_text(encoding="utf-8").splitlines()
        if l.strip() and not l.lower().startswith("ts,")
    )


def test_mqtt_replay_drop_duplicate_and_log() -> None:
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
    env["DEDUP_CACHE_SIZE"] = "500"
    env["MAX_SKEW_SECONDS"] = "120"

    sub = subprocess.Popen(
        ["python", "-u", "ground/src/ground/mqtt_subscriber.py"],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        time.sleep(1.0)

        client = mqtt.Client(client_id="replay-test")
        client.connect("localhost", 1883, keepalive=30)
        client.loop_start()

        unsigned = TelemetryUnsigned(
            ts=EnvelopeV1.now_utc_iso(),
            temperature_c=22.5,
            humidity_pct=45.0,
            pressure_hpa=1013.2,
            mode="NOMINAL",
        )
        signed_line = format_signed_line(unsigned, secret_hex)
        payload_b64 = b64_from_bytes(signed_line.encode("utf-8"))

        # Gleicher msg_id zweimal -> 2. Mal muss DROP_DUPLICATE sein
        msg_id = "replay-001"

        env_msg_1 = EnvelopeV1(
            v="1",
            sat_id=sat_id,
            msg_type="telemetry",
            msg_id=msg_id,
            ts_utc=EnvelopeV1.now_utc_iso(),
            qos=1,
            payload_b64=payload_b64,
        )
        env_msg_2 = EnvelopeV1(
            v="1",
            sat_id=sat_id,
            msg_type="telemetry",
            msg_id=msg_id,  # gleiche ID!
            ts_utc=EnvelopeV1.now_utc_iso(),
            qos=1,
            payload_b64=payload_b64,
        )

        info1 = client.publish(topic, payload=env_msg_1.to_json(), qos=1, retain=False)
        info1.wait_for_publish(timeout=3)

        # Mini-Pause, damit 1. Nachricht verarbeitet wird
        time.sleep(0.5)

        info2 = client.publish(topic, payload=env_msg_2.to_json(), qos=1, retain=False)
        info2.wait_for_publish(timeout=3)

        client.loop_stop()
        client.disconnect()

        time.sleep(2.0)

        after_ok = _count(PROCESSED_FILE)

        # Nur die erste Nachricht darf in processed landen
        assert after_ok == before_ok + 1

    finally:
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

    combined = (out + "\n" + err).lower()
    assert "drop_duplicate" in combined or "duplicate" in combined, (
        f"Expected replay to be logged as duplicate. Output was:\nSTDOUT:\n{out}\nSTDERR:\n{err}"
    )