from pathlib import Path
import pytest

from ground import receiver
from shared.crypto.hmac_sha256 import sign as hmac_sign


CSV_HEADER_STR = "ts,temperature_c,humidity_pct,pressure_hpa,mode,sig"
SECRET = "aabbccddeeff00112233445566778899"


class SecmanSimple:
    """
    Интеграционный стаб:
    - если locked=True, on_packet_before_verify блокирует
    - после verify фиксирует события
    """
    def __init__(self, locked=False, action="quarantine"):
        self.locked = locked
        self.action = action
        self.events = []
        self.before = 0

    def on_packet_before_verify(self, meta):
        self.before += 1
        return not self.locked

    def action_when_locked(self):
        return self.action

    def on_verification_result(self, ok, reason, meta):
        self.events.append((ok, reason, meta))


def patch_paths(monkeypatch, tmp_path: Path):
    raw = tmp_path / "data" / "raw" / "telemetry.csv"
    proc = tmp_path / "data" / "processed" / "telemetry.csv"
    rej = tmp_path / "data" / "rejected" / "telemetry.csv"

    monkeypatch.setattr(receiver, "RAW_PATH", raw)
    monkeypatch.setattr(receiver, "PROC_PATH", proc)
    monkeypatch.setattr(receiver, "REJ_PATH", rej)
    monkeypatch.setattr(receiver, "CSV_HEADER", CSV_HEADER_STR)
    return raw, proc, rej


def data_lines(path: Path):
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    if lines and lines[0] == CSV_HEADER_STR:
        return lines[1:]
    return lines


def make_signed_line(payload: str) -> str:
    sig = hmac_sign(payload, SECRET)
    return f"{payload},{sig}"


def test_pipeline_ok_goes_to_processed(monkeypatch, tmp_path):
    raw, proc, rej = patch_paths(monkeypatch, tmp_path)

    # verify_with_config принимает payload_bytes и mac_hex
    def verify_with_config(payload_bytes: bytes, mac_hex: str) -> bool:
        payload = payload_bytes.decode("utf-8")
        return hmac_sign(payload, SECRET) == mac_hex

    monkeypatch.setattr(receiver, "verify_with_config", verify_with_config)

    payload = "2025-11-24T17:52:54Z,22.50,45.20,1013.20,NOMINAL"
    line = make_signed_line(payload)

    sec = SecmanSimple(locked=False)
    receiver.ingest_raw_line(line)
    receiver.handle_line(line, secman=sec, source="it")

    assert data_lines(raw) == [line]
    assert data_lines(proc) == [line]
    assert data_lines(rej) == []
    assert sec.events and sec.events[0][0] is True


def test_pipeline_bad_sig_goes_to_rejected(monkeypatch, tmp_path):
    raw, proc, rej = patch_paths(monkeypatch, tmp_path)

    def verify_with_config(payload_bytes: bytes, mac_hex: str) -> bool:
        payload = payload_bytes.decode("utf-8")
        return hmac_sign(payload, SECRET) == mac_hex

    monkeypatch.setattr(receiver, "verify_with_config", verify_with_config)

    payload = "2025-11-24T17:52:54Z,22.50,45.20,1013.20,NOMINAL"
    line = f"{payload},WRONGSIG"

    sec = SecmanSimple(locked=False)
    receiver.ingest_raw_line(line)
    receiver.handle_line(line, secman=sec, source="it")

    assert data_lines(raw) == [line]
    assert data_lines(proc) == []
    out = data_lines(rej)
    assert len(out) == 1
    assert "reason=invalid_signature" in out[0]
    assert sec.events and sec.events[0][0] is False


def test_pipeline_lockout_quarantines_before_verify(monkeypatch, tmp_path):
    raw, proc, rej = patch_paths(monkeypatch, tmp_path)

    # если lockout — verify не должен иметь значения
    monkeypatch.setattr(receiver, "verify_with_config", lambda *_: True)

    payload = "2025-11-24T17:52:54Z,22.50,45.20,1013.20,NOMINAL"
    line = make_signed_line(payload)

    sec = SecmanSimple(locked=True, action="quarantine")
    qpath = tmp_path / "data" / "quarantine" / "telemetry.csv"

    receiver.ingest_raw_line(line)
    receiver.handle_line(line, secman=sec, source="it", quarantine_path=qpath)

    assert data_lines(raw) == [line]
    assert data_lines(proc) == []
    assert data_lines(rej) == []
    q = data_lines(qpath)
    assert len(q) == 1
    assert "reason=lockout_active" in q[0]
    # verify_result не должен писаться, т.к. мы вышли до verify
    assert sec.events == []
