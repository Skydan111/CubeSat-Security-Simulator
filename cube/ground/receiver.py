#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ground Receiver: CSV-Telemetrie-Empfang mit HMAC-Verify und Adaptiver Sicherheit.

Pipeline-Stufen:
  RAW (Eingang) → VERIFY (HMAC) → PROCESSED / REJECTED / QUARANTINE
  + Adaptive Security Mode:
      • Überwacht Ereignismuster (ok/fail)
      • Sperrt temporär bei Anomalien (Lockout)
      • Aktionen: drop | quarantine | reject
      • Alle Ereignisse/Auffälligkeiten werden im SecurityManager geloggt
Reduziert Abhängigkeiten und bleibt robust bei fehlender Infrastruktur.
"""

import sys
import argparse
from pathlib import Path
import datetime
from typing import Optional, Tuple
import csv

# ==== Adapter-Funktionen mit Fehlerdiagnose ==== #

def try_import_paths():
    """Versucht projektinterne Pfade zu importieren, fällt andernfalls mit verständlicher Meldung."""
    try:
        from cube.ground.config.paths import RAW_PATH, PROC_PATH, REJ_PATH, CSV_HEADER
        return RAW_PATH, PROC_PATH, REJ_PATH, CSV_HEADER
    except Exception:
        # Klarer Fehler – ohne diese Pfade ist die Pipeline nicht definiert.
        raise RuntimeError("Fehlende Pfaddefinitionen: cube.ground.config.paths nicht gefunden.")

def try_import_verify():
    """Versucht HMAC-Verify-Callback zu importieren. Fallback: einmalige Warnung, immer False."""
    try:
        from cube.ground.verify import verify_with_config
        return verify_with_config
    except Exception:
        _warned = {"done": False}
        def dummy_verify(_payload: bytes, _mac: str) -> bool:
            if not _warned["done"]:
                print("[WARN] HMAC-Verify-Callback nicht geladen! Eingabe wird nicht geprüft (fallback=always-false).")
                _warned["done"] = True
            return False
        return dummy_verify

def try_import_secman():
    """Versucht SecurityManager zu importieren. Fallback: Dummy, der alles erlaubt und nichts loggt."""
    try:
        from ground_station.security_manager import SecurityManager
        return SecurityManager
    except Exception:
        class DummySecman:
            def on_packet_before_verify(self, *_a, **_kw): return True
            def action_when_locked(self): return "reject"
            def on_verification_result(self, **_kw): pass
        return DummySecman

# ==== Pfad- und Funktionsbindung ==== #

RAW_PATH, PROC_PATH, REJ_PATH, CSV_HEADER = try_import_paths()
verify_with_config = try_import_verify()
SecurityManager = try_import_secman()

# ==== Hilfsfunktionen für Datei-/CSV-Operationen ==== #

def ensure_parent(path: Path) -> None:
    """Erstellt fehlende Verzeichnisse für den Zielpfad."""
    path.parent.mkdir(parents=True, exist_ok=True)

def append_line(path: Path, line: str, add_header: bool = True) -> None:
    """
    Schreibt eine rohe CSV-Zeile (unverändert) in die Datei.
    Hinweis: Wir hängen optionale Felder wie reason=... am Ende an,
    ohne den bestehenden CSV_HEADER zu verändern.
    """
    ensure_parent(path)
    header_needed = add_header and (not path.exists() or path.stat().st_size == 0)
    with path.open("a", encoding="utf-8", newline="") as f:
        if header_needed:
            f.write(CSV_HEADER + "\n")
        f.write(line.rstrip("\n") + "\n")

def append_csv(path: Path, fields: list[str], header_fields: Optional[list[str]] = None) -> None:
    """
    Alternative mit csv.writer (korrekte Maskierung von Kommas/Quotes).
    Derzeit nicht zwingend notwendig; behalten wir als Option vor.
    """
    ensure_parent(path)
    header_needed = bool(header_fields) and (not path.exists() or path.stat().st_size == 0)
    with path.open("a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if header_needed:
            w.writerow(header_fields)
        w.writerow(fields)

def split_payload_mac(line: str) -> Tuple[bytes, str]:
    """
    Trennt Payload und MAC anhand des letzten Kommas.
    Liefert (payload_bytes, mac_hex) oder wirft ValueError mit Grundcode.
    """
    try:
        payload, mac = line.rsplit(",", 1)
    except ValueError:
        raise ValueError("no_mac_delimiter")
    mac = mac.strip()
    if not mac:
        raise ValueError("empty_mac")
    return payload.encode("utf-8"), mac

def is_header(line: str) -> bool:
    """Erkennt CSV-Header anhand des Beginns mit 'ts,'."""
    return line.lower().startswith("ts,")

# ==== Datenverarbeitung + Adaptive Security ==== #

def handle_line(
    line: str,
    secman: Optional[object] = None,
    source: str = "unknown",
    quarantine_path: Optional[Path] = None
) -> None:
    """
    Verarbeitet eine einzelne Telemetrie-Zeile:
      • optionaler Lockout-Check (Adaptive Security) vor Verify,
      • Verify (HMAC),
      • Routing: PROCESSED oder REJECTED (oder QUARANTINE bei aktivem Lockout).
    Mutiert die Eingabezeile nicht (für Debug/Forensik).
    """
    if not line.strip():
        return

    pkt_id = (line.split(",", 1)[0] or f"ts-{int(datetime.datetime.now(datetime.UTC).timestamp())}").strip()
    meta = {"source": source, "packet_id": pkt_id, "len": len(line)}

    # 0) Lockout vor Verify prüfen
    if secman and hasattr(secman, "on_packet_before_verify"):
        if not secman.on_packet_before_verify(meta):
            action = getattr(secman, "action_when_locked", lambda: "reject")()
            reason = "lockout_active"
            if action == "drop":
                print(f"[LOCKED] dropped id={pkt_id}")
                return
            elif action == "quarantine":
                qpath = quarantine_path or Path("data/quarantine/telemetry.csv")
                append_line(qpath, line.rstrip() + f",reason={reason}")
                print(f"[LOCKED] quarantined id={pkt_id}")
                return
            else:
                append_line(REJ_PATH, line.rstrip() + f",reason={reason}")
                print(f"[LOCKED] rejected id={pkt_id}")
                return

    # 1) Verify HMAC (mit differenzierten Fehlercodes)
    verify_reason = "ok"
    rej_line = None
    try:
        payload, mac = split_payload_mac(line)
        ok = verify_with_config(payload, mac)
        if not ok:
            verify_reason = "invalid_signature"
    except Exception as e:
        ok = False
        verify_reason = "malformed_packet"
        rej_line = line.rstrip() + f",verify_error={e}"

    # 2) Ergebnis an SecurityManager melden (Fenster/Auslöser/Lockout)
    if secman and hasattr(secman, "on_verification_result"):
        secman.on_verification_result(ok=ok, reason=verify_reason, meta=meta)

    # 3) Schreiben in Ziel (ohne doppelte RAW-Einträge)
    if ok:
        append_line(PROC_PATH, line)
        print("[OK] processed")
    else:
        out_line = rej_line or (line if "reason=" in line else line.rstrip() + f",reason={verify_reason}")
        append_line(REJ_PATH, out_line)
        print(f"[REJECTED] {verify_reason}")

def ingest_raw_line(line: str) -> None:
    """Schreibt eine unveränderte Zeile in RAW (Eingangsspur)."""
    append_line(RAW_PATH, line)

# ==== Empfangsmodi ==== #

def receive_simulated(n: int = 3, secman: Optional[object] = None, quarantine_path: Optional[Path] = None) -> None:
    """Einfacher Simulator mit absichtlicher Fakesignatur."""
    print("[GROUND] Simulierter Empfang gestartet …")
    for _ in range(n):
        ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        line = f"{ts},22.5,45.1,1013.7,sim,FAKESIGN"
        ingest_raw_line(line)  # RAW nur hier (kein Doppel im handle_line)
        handle_line(line, secman=secman, source="simulate", quarantine_path=quarantine_path)

def receive_from_file(path: Path, secman: Optional[object] = None, quarantine_path: Optional[Path] = None) -> None:
    """Liest eine CSV-Datei und verarbeitet sie Zeile für Zeile."""
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

# ==== CLI ==== #

def main() -> int:
    parser = argparse.ArgumentParser(description="Ground Receiver – CSV-Telemetrie mit Adaptiver Sicherheit")
    parser.add_argument("--simulate", action="store_true", help="Simulierter Empfang")
    parser.add_argument("--simulate", action="store_true", help="Simulierter Empfang")
    parser.add_argument(
        "--simulate-count",
        type=int,
        default=3,
        help="Anzahl simulierter Pakete im Simulationsmodus"
    )
    parser.add_argument("--file", type=Path, help="CSV-Datei einlesen")
    parser.add_argument("--stdin", action="store_true", help="Lesen von STDIN")
    parser.add_argument("--security-policy", default="configs/security_policy.yaml", help="Pfad zur Sicherheits-Policy (YAML)")
    parser.add_argument("--security-log", default=None, help="Override Security-Log-Pfad")
    parser.add_argument("--security-audit", default=None, help="Override Security-Audit-JSONL-Pfad")
    parser.add_argument("--quarantine-csv", type=Path, default=Path("data/quarantine/telemetry.csv"),
                        help="Pfad für Quarantäne-CSV bei aktivem Lockout (Policy=quarantine)")
    args = parser.parse_args()

    # SecurityManager-Init, tolerant bei fehlender Policy/Modul
    try:
        secman = SecurityManager(args.security_policy, security_log_path=args.security_log, audit_log_path=args.security_audit)
    except Exception as e:
        print(f"[SECURITY] Adaptive Security deaktiviert ({e})")
        secman = None

    if args.simulate:
        receive_simulated(
            n=args.simulate_count,
            secman=secman,
            quarantine_path=args.quarantine_csv
        )
    elif args.file:
        receive_from_file(args.file, secman=secman, quarantine_path=args.quarantine_csv)
    elif args.stdin:
        receive_from_stdin(secman=secman, quarantine_path=args.quarantine_csv)
    else:
        print("[GROUND] Receiver bereit. --simulate | --file <pfad> | --stdin")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[GROUND] Abbruch durch Benutzer.")
        sys.exit(130)
    except Exception as e:
        print(f"[FATAL] Unhandled error: {e}", file=sys.stderr)
        sys.exit(1)
