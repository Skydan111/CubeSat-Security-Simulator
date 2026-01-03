#!/usr/bin/env python3
"""
verify.py – HMAC-Signaturprüfung für Telemetriedaten

Funktionen:
 - Lädt geheimen Schlüssel aus config/ground.json oder Umgebungsvariable
 - Verifiziert HMAC-SHA256-Signaturen
 - Wird vom Receiver-Modul verwendet
"""

import hmac, hashlib, binascii, json, os, pathlib
from shared.protocol.signed_csv import verify_signed_line

# --- Neue Sektion: Laden der Konfiguration ---
from ground.config.paths import ROOT_DIR
CFG_PATH = ROOT_DIR / "configs" / "ground.json"

def _load_secret_hex() -> str:
    """
    Bezieht den geheimen Schlüssel (Hex) aus:
    1) Umgebungsvariable HMAC_SECRET_HEX (falls gesetzt),
    2) sonst aus config/ground.json ("hmac_secret").
    """
    env = os.getenv("HMAC_SECRET_HEX")
    if env:
        return env.strip()
    with open(CFG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    return cfg["hmac_secret"].strip()


# --- Deine ursprüngliche Funktion bleibt unverändert ---
def verify(secret_hex: str, payload_bytes: bytes, mac_hex: str) -> bool:
    """
    Überprüft eine HMAC-SHA256-Signatur.

    Parameter:
        secret_hex (str): Geheimer Schlüssel im Hex-Format.
        payload_bytes (bytes): Die originalen Nutzdaten (z. B. Telemetriedaten).
        mac_hex (str): Die empfangene HMAC-Signatur im Hex-Format.

    Rückgabe:
        bool – True, wenn die Signatur gültig ist, sonst False.
    """
    key = binascii.unhexlify(secret_hex)
    expected = hmac.new(key, payload_bytes, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, mac_hex)


# --- Zusatzfunktion: Automatische Variante ---
def verify_with_config(payload_bytes: bytes, mac_hex: str) -> bool:
    """Lädt den geheimen Schlüssel automatisch aus config/ground.json."""
    secret = _load_secret_hex()
    return verify(secret, payload_bytes, mac_hex)

def verify_csv_line_with_config(line: str) -> bool:
    """
    Проверяет строку телеметрии формата:
    ts,temperature_c,humidity_pct,pressure_hpa,mode,sig
    Секрет берётся из env HMAC_SECRET_HEX или из ground/config/ground.json
    """
    secret = _load_secret_hex()
    return verify_signed_line(line, secret)

def main():
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("csv_path", help="Path to telemetry CSV")
    args = ap.parse_args()

    ok = 0
    bad = 0

    with open(args.csv_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line or line.startswith("ts,"):
                continue

            if verify_csv_line_with_config(line):
                ok += 1
            else:
                bad += 1
                print(f"[FAIL] line {i}: {line}")

    print(f"[DONE] ok={ok} bad={bad}")


if __name__ == "__main__":
    main()
