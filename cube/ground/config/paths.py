"""
Pfaddefinitionen für Datenverarbeitung auf der Bodenstation.
Alle Pfade verweisen auf das data/-Verzeichnis im Projektstamm.
"""

from pathlib import Path

# Basis: Projektstamm (eine Ebene über /cube)
ROOT_DIR = Path(__file__).resolve().parents[3]   # geht von cube/ground/config/ → zurück zum Projektstamm
DATA_DIR = ROOT_DIR / "data"

RAW_PATH = DATA_DIR / "raw" / "telemetry.csv"
PROC_PATH = DATA_DIR / "processed" / "telemetry.csv"
REJ_PATH = DATA_DIR / "rejected" / "telemetry_rejected.csv"
ARCHIVE_DIR = DATA_DIR / "archive"

CSV_HEADER = "ts,temperature_c,humidity_pct,pressure_hpa,mode,sig"
