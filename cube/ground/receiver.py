#!/usr/bin/env python3
"""
Ground Receiver – Telemetrie-Empfang mit HMAC-Verify und Daten-Pipeline

Ablauf:
  raw (empfangen) → verify (HMAC) → processed / rejected
"""

import argparse
import sys
import datetime
from pathlib import Path

# Importiert zentrale Pfade und Header-Definition
from cube.ground.config.paths import RAW_PATH, PROC_PATH, REJ_PATH, CSV_HEADER
# HMAC-Überprüfung (mit Schlüssel aus ground/config/ground.json)
from cube.ground.verify import verify_with_config


# ============================================================
# 🧩 Hilfsfunktionen
# ============================================================

def _ensure_parent(p: Path):
    """Erstellt übergeordnete Verzeichnisse, falls sie noch nicht existieren."""
    p.parent.mkdir(parents=True, exist_ok=True)


def _append_line(path: Path, line: str, ensure_header: bool = True):
    """Schreibt eine Zeile in die angegebene CSV-Datei und fügt Kopfzeile hinzu, falls nötig."""
    _ensure_parent(path)
    need_header = ensure_header and (not path.exists() or path.stat().st_size == 0)
    with path.open("a", encoding="utf-8") as f:
        if need_header:
            f.write(CSV_HEADER + "\n")
        f.write(line.rstrip("\n") + "\n")


def _split_payload_mac(line: str) -> tuple[bytes, str]:
    """Trennt Nutzdaten (payload) und MAC-Signatur anhand des letzten Kommas."""
    payload, mac = line.rsplit(",", 1)
    return payload.encode("utf-8"), mac.strip()


def _is_header(s: str) -> bool:
    """Erkennt Kopfzeilen anhand des Beginns mit 'ts,'."""
    return s.lower().startswith("ts,")


# ============================================================
# 🚀 Hauptfunktionen – Datenverarbeitung
# ============================================================

def handle_line(line: str):
    """Verarbeitet eine einzelne Telemetrie-Zeile:
       - prüft Signatur (HMAC)
       - schreibt Ergebnis nach processed oder rejected
    """
    if not line.strip():
        return
    try:
        payload_bytes, mac_hex = _split_payload_mac(line)
        ok = verify_with_config(payload_bytes, mac_hex)
    except Exception as e:
        ok = False
        line = line.rstrip("\n") + f",verify_error={e}"

    if ok:
        _append_line(PROC_PATH, line)
        print("[OK] processed")
    else:
        _append_line(REJ_PATH, line)
        print("[REJECTED] signature invalid")


def ingest_raw_line(line: str):
    """Schreibt Rohdaten (unverifiziert) in data/raw/telemetry.csv."""
    _append_line(RAW_PATH, line)


# ============================================================
# 📡 Empfangsmodi
# ============================================================

def receive_simulated(n: int = 3):
    """Simulierter Empfang (Testmodus ohne echte Datei)."""
    print("[GROUND] Simulierter Empfang gestartet …")
    for _ in range(n):
        ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        # absichtliche Fake-Signatur – wird zu 'rejected' führen
        line = f"{ts},22.5,45.1,1013.7,sim,FAKESIGN"
        ingest_raw_line(line)
        handle_line(line)


def receive_from_file(path: Path):
    """Liest eine lokale CSV-Datei ein, prüft jede Zeile und schreibt sie in die Pipeline."""
    if not path.exists():
        raise SystemExit(f"[ERR] Datei nicht gefunden: {path}")

    same_as_raw = path.resolve() == RAW_PATH.resolve()
    print(f"[GROUND] Lese Datei: {path}")

    with path.open("r", encoding="utf-8") as f:
        first = f.readline()
        if first:
            if not _is_header(first):
                if not same_as_raw:
                    ingest_raw_line(first)
                handle_line(first)

        for line in f:
            if _is_header(line):
                continue
            if not same_as_raw:
                ingest_raw_line(line)
            handle_line(line)


def receive_from_stdin():
    """Empfängt Telemetrie-Daten über STDIN (Pipe)."""
    print("[GROUND] Warte auf STDIN (Ctrl+C zum Beenden) …")
    try:
        for line in sys.stdin:
            if _is_header(line):
                continue
            # STDIN wird als Datenstrom behandelt → keine Duplikate in raw
            handle_line(line)
    except KeyboardInterrupt:
        print("\n[GROUND] Empfang manuell gestoppt.")


# ============================================================
# 🧭 CLI-Einstiegspunkt
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Ground Receiver – Telemetrie-Empfang")
    parser.add_argument("--simulate", action="store_true", help="Simulierter Empfang (Test)")
    parser.add_argument("--file", type=Path, help="CSV-Datei einlesen und verarbeiten")
    parser.add_argument("--stdin", action="store_true", help="Aus STDIN lesen (Pipe)")
    args = parser.parse_args()

    if args.simulate:
        receive_simulated()
    elif args.file:
        receive_from_file(args.file)
    elif args.stdin:
        receive_from_stdin()
    else:
        print("[GROUND] Receiver bereit. Wähle eine Quelle: --simulate | --file <pfad> | --stdin")
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
