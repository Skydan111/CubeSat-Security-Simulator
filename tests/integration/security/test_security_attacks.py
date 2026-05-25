from pathlib import Path

from ground import receiver
from shared.crypto.hmac_sha256 import sign as hmac_sign
from ground import input_modes
from ground import packet_pipeline



CSV_HEADER_STR = "ts,temperature_c,humidity_pct,pressure_hpa,mode,sig"
SECRET = "aabbccddeeff00112233445566778899"


def patch_paths(monkeypatch, tmp_path: Path):
    raw = tmp_path / "data" / "raw" / "telemetry.csv"
    proc = tmp_path / "data" / "processed" / "telemetry.csv"
    rej = tmp_path / "data" / "rejected" / "telemetry.csv"

    monkeypatch.setattr(input_modes, "RAW_PATH", raw)
    monkeypatch.setattr(packet_pipeline, "PROC_PATH", proc)
    monkeypatch.setattr(packet_pipeline, "REJ_PATH", rej)

    return raw, proc, rej



def data_lines(path: Path):
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    if lines and lines[0] == CSV_HEADER_STR:
        return lines[1:]
    return lines


def verify_with_secret(payload_bytes: bytes, mac_hex: str) -> bool:
    payload = payload_bytes.decode("utf-8")
    return hmac_sign(payload, SECRET) == mac_hex


def make_signed_line(payload: str) -> str:
    return f"{payload},{hmac_sign(payload, SECRET)}"


def test_attack_tamper_payload_is_rejected(monkeypatch, tmp_path):
    raw, proc, rej = patch_paths(monkeypatch, tmp_path)
    monkeypatch.setattr(packet_pipeline, "verify_with_config", verify_with_secret)

    payload = "2025-11-24T17:52:54Z,22.50,45.20,1013.20,NOMINAL"
    line = make_signed_line(payload)

    # Подменяем одно значение в payload, подпись оставляем прежней
    tampered = line.replace("22.50", "22.51", 1)

    input_modes.ingest_raw_line(tampered)
    packet_pipeline.handle_line(tampered, secman=None, source="attack")

    assert data_lines(proc) == []
    out = data_lines(rej)
    assert len(out) == 1
    assert "reason=invalid_signature" in out[0]


def test_attack_truncated_or_empty_mac_is_rejected_as_malformed(monkeypatch, tmp_path):
    raw, proc, rej = patch_paths(monkeypatch, tmp_path)
    monkeypatch.setattr(packet_pipeline, "verify_with_config", verify_with_secret)

    # Пустой MAC: split_payload_mac -> empty_mac -> Exception -> malformed_packet
    line = "2025-11-24T17:52:54Z,22.50,45.20,1013.20,NOMINAL,   "

    input_modes.ingest_raw_line(line)
    packet_pipeline.handle_line(line, secman=None, source="attack")

    assert data_lines(proc) == []
    out = data_lines(rej)
    assert len(out) == 1
    assert "verify_error=" in out[0]
