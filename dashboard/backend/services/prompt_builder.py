"""Baut den User-Prompt für das feinjustierte Warehouse-Modell.

Das Format entspricht exakt "Format C" des Trainingsdatensatzes
(Temperatur + Luftfeuchtigkeit, mit Kontext). Die Funktion ist bewusst
"pure": keine Uhrzeit-Abfrage, kein I/O — dadurch einfach testbar.
Die Frische-Prüfung (sind die Daten aktuell?) übernimmt ai_analyst.
"""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from dashboard.backend.config import (
    ANALYSIS_WINDOW_MIN,
    BUSINESS_HOURS,
    LOCAL_TZ,
    THRESHOLDS,
)
from dashboard.backend.models import TelemetryPacket

INSTRUCTION = "Analysiere die Telemetriedaten und erstelle einen Bericht für den Lageroperator."

# (Feld im TelemetryPacket, Anzeigename im Prompt, Einheit)
# Druck ist bewusst ausgeschlossen (keine operative Relevanz im Lager).
PARAMETERS = [
    ("temperature_c", "Temperatur", "°C"),
    ("humidity_pct", "Luftfeuchtigkeit", "%"),
]

_TZ = ZoneInfo(LOCAL_TZ)


def _fmt(value: float) -> str:
    """10.44 -> '10,4' (deutsches Zahlenformat wie im Datensatz)."""
    return f"{value:.1f}".replace(".", ",")


def _signed(value: float) -> str:
    """2.4 -> '+2,4', -2.4 -> '-2,4'."""
    return ("+" if value >= 0 else "-") + _fmt(abs(value))


def _deviation(value: float, limits: dict) -> float:
    """>0 = Überschreitung, <0 = Unterschreitung, 0 = im Sollbereich."""
    if value > limits["max"]:
        return value - limits["max"]
    if value < limits["min"]:
        return value - limits["min"]
    return 0.0


def _select_window(packets: list[TelemetryPacket]) -> list[TelemetryPacket]:
    """Nur Pakete der letzten ANALYSIS_WINDOW_MIN Minuten (zeitbasiert, nicht Anzahl).

    Erwartet Pakete in chronologischer Reihenfolge (so schreibt sie der Logger).
    """
    if not packets:
        raise ValueError("Keine Telemetriedaten vorhanden")
    latest_ts = packets[-1].ts
    window_start = latest_ts - timedelta(minutes=ANALYSIS_WINDOW_MIN)
    return [p for p in packets if p.ts > window_start]


def _anomaly_start(window: list[TelemetryPacket], field: str, limits: dict) -> datetime:
    """Geht vom neuesten Paket rückwärts, solange der Wert in dieselbe Richtung abweicht."""
    latest_dev = _deviation(getattr(window[-1], field), limits)
    start = window[-1].ts
    for packet in reversed(window):
        dev = _deviation(getattr(packet, field), limits)
        if dev == 0 or (dev > 0) != (latest_dev > 0):
            break
        start = packet.ts
    return start


def _kontext(ts: datetime) -> str:
    """Betriebskontext aus Lokalzeit. Formulierungen 1:1 aus dem Datensatz."""
    local = ts.astimezone(_TZ)
    if local.weekday() >= 5:
        return "Wochenende, Lager geschlossen, kein Personal vor Ort"
    start_h, end_h = BUSINESS_HOURS
    if not (start_h <= local.hour < end_h):
        return "Nacht, Lager geschlossen, kein Personal vor Ort"
    return "Werktag, aktiver Betriebszeitraum"


def build_prompt(packets: list[TelemetryPacket]) -> str:
    """Instruction + Leerzeile + Input im Format C des Trainingsdatensatzes."""
    window = _select_window(packets)
    latest = window[-1]
    lines = ["Parameter: Temperatur + Luftfeuchtigkeit"]

    for field, name, unit in PARAMETERS:
        lim = THRESHOLDS[field]
        lines.append(
            f"Schwellenwert {name}: min {_fmt(lim['min'])}{unit} / max {_fmt(lim['max'])}{unit}"
        )

    anomaly_starts = []
    for field, name, unit in PARAMETERS:
        lim = THRESHOLDS[field]
        value = getattr(latest, field)
        dev = _deviation(value, lim)
        line = f"Aktueller Wert {name}: {_fmt(value)}{unit} | "
        if dev == 0:
            line += "Status: im Sollbereich"
        else:
            start = _anomaly_start(window, field, lim)
            anomaly_starts.append(start)
            minutes = max(1, round((latest.ts - start).total_seconds() / 60))
            kind = "Überschreitung" if dev > 0 else "Unterschreitung"
            line += f"{kind}: {_signed(dev)}{unit}, Andauer: {minutes} Minuten"
        lines.append(line)

    lines.append(
        f"Analysezeitraum: letzte {ANALYSIS_WINDOW_MIN} Minuten ({len(window)} Messpunkte)"
    )

    for field, name, unit in PARAMETERS:
        values = [getattr(p, field) for p in window]
        avg = sum(values) / len(values)
        lines.append(
            f"Durchschnitt {name}: {_fmt(avg)}{unit} | "
            f"Minimum: {_fmt(min(values))}{unit} | Maximum: {_fmt(max(values))}{unit}"
        )

    if anomaly_starts:
        begin = min(anomaly_starts).astimezone(_TZ)
        lines.append(f"Beginn der Anomalie: {begin:%H:%M:%S}")

    lines.append(f"Kontext: {_kontext(latest.ts)}")

    return f"{INSTRUCTION}\n\n" + "\n".join(lines)