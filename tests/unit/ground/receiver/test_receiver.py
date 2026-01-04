import pytest
from pathlib import Path

from ground import receiver


CSV_HEADER_STR = "ts,temperature_c,humidity_pct,pressure_hpa,mode,sig"


class SecmanStub:
    def __init__(self, locked=False, action="reject"):
        self.locked = locked
        self.action = action
        self.before_calls = []
        self.after_calls = []

    def on_packet_before_verify(self, meta):
        self.before_calls.append(meta)
        return not self.locked

    def action_when_locked(self):
        return self.action

    def on_verification_result(self, ok, reason, meta):
        self.after_calls.append((ok, reason, meta))


def patch_paths(monkeypatch, tmp_path: Path):
    raw = tmp_path / "data" / "raw" / "telemetry.csv"
    proc = tmp_path / "data" / "processed" / "telemetry.csv"
    rej = tmp_path / "data" / "rejected" / "telemetry.csv"

    monkeypatch.setattr(receiver, "RAW_PATH", raw)
    monkeypatch.setattr(receiver, "PROC_PATH", proc)
    monkeypatch.setattr(receiver, "REJ_PATH", rej)
    monkeypatch.setattr(receiver, "CSV_HEADER", CSV_HEADER_STR)

    return raw, proc, rej


def read_file_lines(path: Path):
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines()


def data_lines(path: Path):
    """Возвращает строки без заголовка (если он есть)."""
    lines = read_file_lines(path)
    if not lines:
        return []
    if lines[0] == CSV_HEADER_STR:
        return lines[1:]
    return lines


# -------------------------
# split_payload_mac
# -------------------------

def test_split_payload_mac_ok():
    payload, mac = receiver.split_payload_mac("a,b,c,SIG\n")
    assert payload == b"a,b,c"
    assert mac == "SIG"


def test_split_payload_mac_no_delimiter():
    with pytest.raises(ValueError) as e:
        receiver.split_payload_mac("abcdef")
    assert str(e.value) == "no_mac_delimiter"


def test_split_payload_mac_empty_mac():
    with pytest.raises(ValueError) as e:
        receiver.split_payload_mac("a,b,c,   ")
    assert str(e.value) == "empty_mac"


# -------------------------
# handle_line routing
# -------------------------

def test_handle_line_writes_processed_on_ok(monkeypatch, tmp_path):
    raw, proc, rej = patch_paths(monkeypatch, tmp_path)

    monkeypatch.setattr(receiver, "verify_with_config", lambda payload, mac: True)

    sec = SecmanStub(locked=False)
    line = "2025-11-24T17:52:54Z,22.50,45.20,1013.20,NOMINAL,DEADBEEF"
    receiver.handle_line(line, secman=sec, source="unit")

    assert data_lines(proc) == [line]
    assert data_lines(rej) == []

    # SecurityManager получит after-call
    assert len(sec.after_calls) == 1
    ok, reason, meta = sec.after_calls[0]
    assert ok is True
    assert reason == "ok"
    assert meta["source"] == "unit"


def test_handle_line_writes_rejected_on_invalid_signature(monkeypatch, tmp_path):
    raw, proc, rej = patch_paths(monkeypatch, tmp_path)

    monkeypatch.setattr(receiver, "verify_with_config", lambda payload, mac: False)

    sec = SecmanStub(locked=False)
    line = "2025-11-24T17:52:54Z,22.50,45.20,1013.20,NOMINAL,BADSIG"
    receiver.handle_line(line, secman=sec, source="unit")

    assert data_lines(proc) == []
    out = data_lines(rej)
    assert len(out) == 1
    assert "reason=invalid_signature" in out[0]


def test_handle_line_marks_malformed_packet(monkeypatch, tmp_path):
    raw, proc, rej = patch_paths(monkeypatch, tmp_path)

    # verify_with_config не должен вызываться, но пусть будет
    monkeypatch.setattr(receiver, "verify_with_config", lambda payload, mac: True)

    sec = SecmanStub(locked=False)
    # нет последней запятой => split_payload_mac кинет no_mac_delimiter
    line = "THIS_IS_NOT_CSV_AT_ALL"
    receiver.handle_line(line, secman=sec, source="unit")

    assert data_lines(proc) == []
    out = data_lines(rej)
    assert len(out) == 1
    assert "verify_error=" in out[0]

    # SecurityManager должен получить reason=malformed_packet
    assert sec.after_calls[0][1] == "malformed_packet"

def test_handle_line_lockout_quarantine(monkeypatch, tmp_path):
    raw, proc, rej = patch_paths(monkeypatch, tmp_path)
    monkeypatch.setattr(receiver, "verify_with_config", lambda payload, mac: True)

    sec = SecmanStub(locked=True, action="quarantine")
    qpath = tmp_path / "data" / "quarantine" / "telemetry.csv"

    line = "2025-11-24T17:52:54Z,22.50,45.20,1013.20,NOMINAL,SIG"
    receiver.handle_line(line, secman=sec, source="unit", quarantine_path=qpath)

    # Не должно уйти ни в processed, ни в rejected
    assert data_lines(proc) == []
    assert data_lines(rej) == []

    q = data_lines(qpath)
    assert len(q) == 1
    assert "reason=lockout_active" in q[0]


# -------------------------
# receive_from_file and RAW duplication invariant
# -------------------------

def test_receive_from_file_does_not_duplicate_when_reading_raw(monkeypatch, tmp_path):
    raw, proc, rej = patch_paths(monkeypatch, tmp_path)
    monkeypatch.setattr(receiver, "verify_with_config", lambda payload, mac: True)

    # создаём RAW файл (header + 1 строка)
    line = "2025-11-24T17:52:54Z,22.50,45.20,1013.20,NOMINAL,SIG"
    raw.parent.mkdir(parents=True, exist_ok=True)
    raw.write_text(CSV_HEADER_STR + "\n" + line + "\n", encoding="utf-8")

    receiver.receive_from_file(raw, secman=None)

    # RAW не должен быть “перезаписан/дописан” заново тем же line
    assert data_lines(raw) == [line]
    # processed должен получить line
    assert data_lines(proc) == [line]


def test_receive_from_file_ingests_raw_when_source_is_not_raw(monkeypatch, tmp_path):
    raw, proc, rej = patch_paths(monkeypatch, tmp_path)
    monkeypatch.setattr(receiver, "verify_with_config", lambda payload, mac: True)

    src = tmp_path / "input.csv"
    line1 = "2025-11-24T17:52:54Z,22.50,45.20,1013.20,NOMINAL,SIG1"
    line2 = "2025-11-24T17:53:54Z,22.60,45.10,1013.10,NOMINAL,SIG2"
    src.write_text(CSV_HEADER_STR + "\n" + line1 + "\n" + line2 + "\n", encoding="utf-8")

    receiver.receive_from_file(src, secman=None)

    # RAW должен получить обе строки ровно по одному разу
    assert data_lines(raw) == [line1, line2]
    # processed тоже получит обе
    assert data_lines(proc) == [line1, line2]
