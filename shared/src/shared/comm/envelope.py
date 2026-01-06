from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict


@dataclass(frozen=True)
class EnvelopeV1:
    v: str
    sat_id: str
    msg_type: str
    msg_id: str
    ts_utc: str
    qos: int
    payload_b64: str

    @staticmethod
    def now_utc_iso() -> str:
        # Liefert UTC-Zeitstempel im ISO-8601 Format (UTC, ohne Mikrosekunden).
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    def to_json(self) -> str:
        # Serialisiert den Envelope zu kompaktem JSON für MQTT Transport.
        return json.dumps(self.__dict__, separators=(",", ":"))

    @staticmethod
    def from_json(raw: str) -> "EnvelopeV1":
        # Parst JSON und validiert Minimalfelder für Envelope v1.
        obj: Dict[str, Any] = json.loads(raw)

        if obj.get("v") != "1":
            raise ValueError("Invalid envelope version (expected '1').")

        required = ["sat_id", "msg_type", "msg_id", "ts_utc", "qos", "payload_b64"]
        for k in required:
            if k not in obj:
                raise ValueError(f"Missing field: {k}")

        return EnvelopeV1(
            v="1",
            sat_id=str(obj["sat_id"]),
            msg_type=str(obj["msg_type"]),
            msg_id=str(obj["msg_id"]),
            ts_utc=str(obj["ts_utc"]),
            qos=int(obj["qos"]),
            payload_b64=str(obj["payload_b64"]),
        )


def b64_from_bytes(data: bytes) -> str:
    # Kodiert Bytes nach Base64 (ASCII) für JSON Payload.
    return base64.b64encode(data).decode("ascii")


def bytes_from_b64(data_b64: str) -> bytes:
    # Decodiert Base64 String zurück nach Bytes.
    return base64.b64decode(data_b64.encode("ascii"))
