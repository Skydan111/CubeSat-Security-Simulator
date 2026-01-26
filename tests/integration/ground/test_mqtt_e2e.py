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


ROOT = Path(__file__).resolve().parents[3]  # .../CubeSat
COMPOSE_FILE = ROOT / "docker-compose.mqtt.yml"

RAW_FILE = ROOT / "data" / "raw" / "telemetry.csv"
PROCESSED_FILE = ROOT / "data" / "processed" / "telemetry.csv"
REJECTED_FILE = ROOT / "data" / "rejected" / "telemetry.csv"
QUAR_FILE = ROOT / "data" / "quarantine" / "telemetry.csv"


def _count_csv_lines(path: Path) -> int:
    # Zählt Datenzeilen (ohne Header). Falls Datei fehlt -> 0.
    if not path.exists():
        return 0
    n = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        if line.lower().startswith("ts,"):
            continue
        n += 1
    return n


def _wait_until(predicate, timeout_s: float = 30.0, poll_s: float = 0.2) -> None:
    # Polling-Helper für asynchrone E2E-Tests.
    start = time.monotonic()
    while True:
        if predicate():
            return
        if time.monotonic() - start > timeout_s:
            raise AssertionError("Timeout while waiting for condition.")
        time.sleep(poll_s)


def _wait_for_subscriber_ready(sub_proc: subprocess.Popen[str], timeout_s: float = 8.0) -> None:
    # Wartet, bis der Subscriber "Subscribing to ..." ausgibt.
    # Das ist unser Signal, dass connect+subscribe fertig ist.
    start = time.monotonic()
    out_lines: list[str] = []

    while True:
        if sub_proc.poll() is not None:
            out = "".join(out_lines) + (sub_proc.stdout.read() if sub_proc.stdout else "")
            err = sub_proc.stderr.read() if sub_proc.stderr else ""
            raise AssertionError(f"Subscriber exited early.\nSTDOUT:\n{out}\nSTDERR:\n{err}")

        if sub_proc.stdout:
            line = sub_proc.stdout.readline()
            if line:
                out_lines.append(line)
                if "Subscribing to" in line or "Connected. Subscribing to" in line:
                    return

        if time.monotonic() - start > timeout_s:
            out = "".join(out_lines) + (sub_proc.stdout.read() if sub_proc.stdout else "")
            err = sub_proc.stderr.read() if sub_proc.stderr else ""
            raise AssertionError(f"Subscriber not ready in time.\nSTDOUT:\n{out}\nSTDERR:\n{err}")

        time.sleep(0.05)


def test_mqtt_end_to_end_50_messages() -> None:
    sat_id = "SAT-001"
    secret_hex = "deadbeef"
    topic = telemetry_topic(sat_id)

    # --- Docker Broker hochfahren ---
    subprocess.run(
        ["docker", "compose", "-f", str(COMPOSE_FILE), "up", "-d"],
        check=True,
        cwd=str(ROOT),
    )

    # Broker braucht manchmal kurz zum "ready" werden
    time.sleep(0.5)

    before_raw = _count_csv_lines(RAW_FILE)
    before_proc = _count_csv_lines(PROCESSED_FILE)
    before_rej = _count_csv_lines(REJECTED_FILE)
    before_quar = _count_csv_lines(QUAR_FILE)

    # --- Subscriber starten (als eigener Prozess) ---
    env = os.environ.copy()
    env["SAT_ID"] = sat_id
    env["SAT_SECRET_HEX"] = secret_hex
    env["MQTT_BROKER_HOST"] = "localhost"
    env["MQTT_BROKER_PORT"] = "1883"
    env["DEDUP_CACHE_SIZE"] = "500"
    env["MAX_SKEW_SECONDS"] = "120"
    env["SECURITY_POLICY_PATH"] = "configs/security_policy.yaml"
    env["PYTHONUNBUFFERED"] = "1"

    sub_proc = subprocess.Popen(
        ["python", "-u", "ground/src/ground/mqtt_subscriber.py"],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    try:
        # Warten bis connect+subscribe wirklich aktiv ist
        _wait_for_subscriber_ready(sub_proc, timeout_s=8.0)

        # --- MQTT Publisher (Test) ---
        client = mqtt.Client(client_id="test-publisher")
        client.connect("localhost", 1883, keepalive=30)
        client.loop_start()

        n = 50
        infos = []
        for _ in range(n):
            unsigned = TelemetryUnsigned(
                ts=EnvelopeV1.now_utc_iso(),
                temperature_c=22.5,
                humidity_pct=45.0,
                pressure_hpa=1013.2,
                mode="NOMINAL",
            )
            signed_line = format_signed_line(unsigned, secret_hex)
            signed_bytes = signed_line.encode("utf-8")

            env_msg = EnvelopeV1(
                v="1",
                sat_id=sat_id,
                msg_type="telemetry",
                msg_id=os.urandom(8).hex(),
                ts_utc=EnvelopeV1.now_utc_iso(),
                qos=1,
                payload_b64=b64_from_bytes(signed_bytes),
            )
            info = client.publish(topic, payload=env_msg.to_json(), qos=1, retain=False)
            infos.append(info)

        # QoS1: kurz warten, bis alle publish calls "done" sind
        for info in infos:
            info.wait_for_publish(timeout=3)

        client.loop_stop()
        client.disconnect()

        # --- Warten, bis processed N neue Zeilen hat ---
        try:
            _wait_until(lambda: _count_csv_lines(PROCESSED_FILE) >= before_proc + n, timeout_s=40.0)
        except AssertionError:
            out = sub_proc.stdout.read() if sub_proc.stdout else ""
            err = sub_proc.stderr.read() if sub_proc.stderr else ""
            raise AssertionError(f"Timeout waiting for processed lines.\nSTDOUT:\n{out}\nSTDERR:\n{err}")

        after_raw = _count_csv_lines(RAW_FILE)
        after_proc = _count_csv_lines(PROCESSED_FILE)
        after_rej = _count_csv_lines(REJECTED_FILE)
        after_quar = _count_csv_lines(QUAR_FILE)

        assert after_proc == before_proc + n
        assert after_raw >= before_raw + n
        assert after_rej == before_rej
        assert after_quar == before_quar

    finally:
        # Subscriber sauber beenden
        if sub_proc.poll() is None:
            sub_proc.terminate()
            try:
                sub_proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                sub_proc.kill()

        # Broker runterfahren
        subprocess.run(
            ["docker", "compose", "-f", str(COMPOSE_FILE), "down"],
            check=False,
            cwd=str(ROOT),
        )