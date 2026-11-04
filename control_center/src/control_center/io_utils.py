"""
io_utils.py – Hilfsfunktionen für Datei- und CSV-Operationen.
"""


from pathlib import Path
from typing import Optional
import csv

def ensure_parent(path: Path) -> None:
    """Erstellt fehlende Verzeichnisse für den Zielpfad."""
    path.parent.mkdir(parents=True, exist_ok=True)

def append_line(path: Path, line: str, add_header: bool = True, csv_header: str = "") -> None:
    """
    Schreibt eine rohe CSV-Zeile (unverändert) in die Datei.
    Hinweis: Wir hängen optionale Felder wie reason=... am Ende an,
    ohne den bestehenden CSV_HEADER zu verändern.
    """
    ensure_parent(path)
    header_needed = add_header and bool(csv_header) and (not path.exists() or path.stat().st_size == 0)
    with path.open("a", encoding="utf-8", newline="") as f:
        if header_needed:
            f.write(csv_header + "\n")
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