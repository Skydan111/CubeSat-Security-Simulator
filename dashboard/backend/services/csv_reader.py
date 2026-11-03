import csv
from collections import deque
from typing import Iterator

from ground.config.paths import CSV_HEADER, PROC_PATH
from dashboard.backend.models import TelemetryPacket

FIELDS = CSV_HEADER.split(",")


def _iter_rows() -> Iterator[dict]:
    """Liest PROC_PATH robust (fail-secure):
    - Datei fehlt -> keine Zeilen statt Exception
    - Kopfzeile optional: Spalten kommen aus CSV_HEADER, nicht aus Zeile 1
    - unvollstaendige Zeilen werden uebersprungen
    """
    if not PROC_PATH.exists():
        return
    with open(PROC_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f, fieldnames=FIELDS):
            if row["ts"] == FIELDS[0]:
                continue  # Kopfzeile
            values = {k: row[k] for k in FIELDS}
            if any(v is None or v == "" for v in values.values()):
                continue  # unvollstaendige Zeile
            yield values


def read_all() -> list[TelemetryPacket]:
    return [TelemetryPacket(**row) for row in _iter_rows()]


def read_latest() -> TelemetryPacket | None:
    last = None
    for row in _iter_rows():
        last = row
    return TelemetryPacket(**last) if last else None


def read_last_n(n: int = 60) -> list[TelemetryPacket]:
    return [TelemetryPacket(**row) for row in deque(_iter_rows(), maxlen=n)]
