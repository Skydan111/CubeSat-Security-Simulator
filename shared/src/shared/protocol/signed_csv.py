from __future__ import annotations

from dataclasses import dataclass

from shared.crypto.hmac_sha256 import sign as hmac_sign, verify as hmac_verify
from shared.protocol.telemetry_csv import TelemetryUnsigned, format_payload, parse_payload


@dataclass(frozen=True)
class TelemetrySigned:
    unsigned: TelemetryUnsigned
    sig: str


def format_signed_line(u: TelemetryUnsigned, secret_hex: str) -> str:

    payload = format_payload(u)
    sig = hmac_sign(payload, secret_hex)
    return f"{payload},{sig}"


def parse_signed_line(line: str) -> TelemetrySigned:

    parts = line.strip().split(",")
    if len(parts) != 6:
        raise ValueError(f"Expected 6 CSV fields (with sig), got {len(parts)}: {parts}")

    payload = ",".join(parts[:5])
    sig = parts[5]
    u = parse_payload(payload)
    return TelemetrySigned(unsigned=u, sig=sig)


def verify_signed_line(line: str, secret_hex: str) -> bool:

    tsig = parse_signed_line(line)
    payload = format_payload(tsig.unsigned)
    return hmac_verify(payload, secret_hex, tsig.sig)
