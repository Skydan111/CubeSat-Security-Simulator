#!/usr/bin/env python3
"""
paths.py – Pfaddefinitionen für die Datenverarbeitung auf der Bodenstation

Alle Pfade verweisen auf das zentrale Verzeichnis:
    data/{raw, processed, rejected, archive}

Wird von receiver.py, verify.py und plot.py importiert.
"""

from pathlib import Path

# ------------------------------------------------------------
# 🧭 Basisverzeichnisse
# ------------------------------------------------------------

# Projektstamm (eine Ebene über cube/)
ROOT_DIR = Path(__file__).resolve().parents[4]

# Hauptordner für Daten
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------
# 📂 Standardpfade
# ------------------------------------------------------------

RAW_PATH = DATA_DIR / "raw" / "telemetry.csv"                # ungeprüfte Rohdaten (Receiver-Eingang)
PROC_PATH = DATA_DIR / "processed" / "telemetry.csv"         # verifizierte, gültige Daten
REJ_PATH = DATA_DIR / "rejected" / "telemetry_rejected.csv"  # verworfene Datensätze (Signatur ungültig)
ARCHIVE_DIR = DATA_DIR / "archive"                           # für alte Missionen / Backups

# CSV-Kopfzeile (wird bei Bedarf automatisch hinzugefügt)
CSV_HEADER = "ts,temperature_c,humidity_pct,pressure_hpa,mode,sig"
