"""
input_modes.py – Empfangsmodi.
"""

import sys
from pathlib import Path
import datetime
from typing import Optional
from ground.mqtt_guard import MqttMessageGuard
from ground.io_utils import append_line
from ground.config.paths import RAW_PATH
from ground.packet_pipeline import handle_line, is_header


def ingest_raw_line(line: str) -> None:
    """Schreibt eine unveränderte Zeile in RAW (Eingangsspur)."""
    append_line(RAW_PATH, line)

def receive_simulated(n: int = 3, secman: Optional[object] = None, quarantine_path: Optional[Path] = None) -> None:
    """Einfacher Simulator mit absichtlicher Fakesignatur."""
    print("[GROUND] Simulierter Empfang gestartet …")
    for _ in range(n):
        ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        line = f"{ts},22.5,45.1,1013.7,sim,FAKESIGN"
        ingest_raw_line(line)  # RAW nur hier (kein Doppel im handle_line)
        handle_line(line, secman=secman, source="simulate", quarantine_path=quarantine_path)

def receive_from_file(
        path: Path, guard: Optional[MqttMessageGuard] = None, secman: Optional[object] = None, quarantine_path: Optional[Path] = None) -> None:
    """Liest eine CSV-Datei und verarbeitet sie Zeile für Zeile."""
    # TODO: apply guard.is_duplicate() and guard.is_fresh() per line (pkt 6)
    if not path.exists():
        raise SystemExit(f"[ERR] Datei nicht gefunden: {path}")
    same_as_raw = path.resolve() == RAW_PATH.resolve()
    print(f"[GROUND] Lese Datei: {path}")
    with path.open("r", encoding="utf-8") as f:
        first = f.readline()
        if first and not is_header(first):
            if not same_as_raw:
                ingest_raw_line(first)
            handle_line(first, secman=secman, source="file", quarantine_path=quarantine_path)
        for line in f:
            if is_header(line):
                continue
            if not same_as_raw:
                ingest_raw_line(line)
            handle_line(line, secman=secman, source="file", quarantine_path=quarantine_path)

def receive_from_stdin(secman: Optional[object] = None, quarantine_path: Optional[Path] = None) -> None:
    """Liest Telemetrie über STDIN (Pipe)."""
    print("[GROUND] Warte auf STDIN (Ctrl+C zum Beenden) …")
    try:
        for line in sys.stdin:
            if is_header(line):
                continue
            ingest_raw_line(line)  # RAW für STDIN (keine Duplikate in handle_line)
            handle_line(line, secman=secman, source="stdin", quarantine_path=quarantine_path)
    except KeyboardInterrupt:
        print("\n[GROUND] Empfang manuell gestoppt.")