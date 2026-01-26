from __future__ import annotations

def telemetry_topic(sat_id: str) -> str:
    # Baut den Telemetry-Topic gemäß MQTT Contract v1.
    return f"cubesat/v1/{sat_id}/telemetry"
