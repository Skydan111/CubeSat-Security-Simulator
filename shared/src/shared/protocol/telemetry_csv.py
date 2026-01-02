from __future__ import annotations

from dataclasses import dataclass


HEADER = ["ts", "temperature_c", "humidity_pct", "pressure_hpa", "mode", "sig"]


@dataclass(frozen=True)
class TelemetryUnsigned:
    ts: str                    # ISO 8601 string with timezone, e.g. 2025-11-24T17:52:54.510195+00:00
    temperature_c: float
    humidity_pct: float
    pressure_hpa: float
    mode: str


def format_payload(u: TelemetryUnsigned) -> str:
    # Канонический формат как в твоём реальном файле: ISO ts + 2 decimals
    return f"{u.ts},{u.temperature_c:.2f},{u.humidity_pct:.2f},{u.pressure_hpa:.2f},{u.mode}"


def parse_payload(payload: str) -> TelemetryUnsigned:
    parts = payload.strip().split(",")
    if len(parts) != 5:
        raise ValueError(f"Expected 5 CSV fields (without sig), got {len(parts)}: {parts}")

    ts, temp_s, hum_s, pres_s, mode = parts
    return TelemetryUnsigned(
        ts=ts,
        temperature_c=float(temp_s),
        humidity_pct=float(hum_s),
        pressure_hpa=float(pres_s),
        mode=mode,
    )
