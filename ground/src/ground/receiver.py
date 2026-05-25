#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ground Receiver: Einstiegspunkt – CSV-Telemetrie mit Adaptiver Sicherheit.

Pipeline-Stufen:
  RAW (Eingang) → VERIFY (HMAC) → PROCESSED / REJECTED / QUARANTINE
"""

import sys
import argparse
from pathlib import Path

from ground.input_modes import receive_simulated, receive_from_file, receive_from_stdin


def try_import_secman():
    """Versucht SecurityManager zu importieren. Wirft RuntimeError wenn der Import fehlschlägt."""
    try:
        from ground.security.security_manager import SecurityManager
        return SecurityManager
    except Exception as e:
        raise RuntimeError("Fehlender SecurityManager: " + str(e))


SecurityManager = try_import_secman()


def main() -> int:
    parser = argparse.ArgumentParser(description="Ground Receiver – CSV-Telemetrie mit Adaptiver Sicherheit")
    parser.add_argument("--simulate", action="store_true", help="Simulierter Empfang")
    parser.add_argument("--simulate-count", type=int, default=3)
    parser.add_argument("--file", type=Path, help="CSV-Datei einlesen")
    parser.add_argument("--stdin", action="store_true", help="Lesen von STDIN")
    parser.add_argument("--security-policy", default="configs/security_policy.yaml")
    parser.add_argument("--security-log", default=None)
    parser.add_argument("--security-audit", default=None)
    parser.add_argument("--quarantine-csv", type=Path, default=Path("data/quarantine/telemetry.csv"))
    args = parser.parse_args()

    try:
        with SecurityManager(args.security_policy, security_log_path=args.security_log, audit_log_path=args.security_audit) as secman:
            if args.simulate:
                receive_simulated(n=args.simulate_count, secman=secman, quarantine_path=args.quarantine_csv)
            elif args.file:
                receive_from_file(args.file, secman=secman, quarantine_path=args.quarantine_csv)
            elif args.stdin:
                receive_from_stdin(secman=secman, quarantine_path=args.quarantine_csv)
            else:
                print("[GROUND] Receiver bereit. --simulate | --file <pfad> | --stdin")
        return 0
    except Exception as e:
        print(f"[SECURITY] Fehler ({e})")
        raise RuntimeError("SecurityManager konnte nicht initialisiert werden: " + str(e))


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[GROUND] Abbruch durch Benutzer.")
        sys.exit(130)
    except Exception as e:
        print(f"[FATAL] Unhandled error: {e}", file=sys.stderr)
        sys.exit(1)
