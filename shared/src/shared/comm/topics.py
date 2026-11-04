from __future__ import annotations

def telemetry_topic(zone_id: str) -> str:
    # Baut den Telemetry-Topic gemäß MQTT Contract v1.
    return f"warehouse/v1/{zone_id}/telemetry"
