import io
import yaml
import builtins
from pathlib import Path

import pytest

from shared.protocol.signed_csv import verify_signed_line


# Важно: импортируем именно модуль, чтобы monkeypatch работал по атрибутам модуля
from satellite import logger as sat_logger
from shared.protocol.telemetry_csv import TelemetryUnsigned


SECRET = "aabbccddeeff00112233445566778899"


class SensorStub:
    def __init__(self, readings):
        self._it = iter(readings)

    def read(self):
        d = next(self._it)
        return TelemetryUnsigned(
            ts=d["ts"],
            temperature_c=d["temperature_c"],
            humidity_pct=d["humidity_pct"],
            pressure_hpa=d["pressure_hpa"],
            mode=d["mode"],
        )


def make_cfg(csv_path: Path, interval_sec=1):
    return {
        "csv_path": str(csv_path),          # делаем absolute, чтобы не зависеть от HERE.parents
        "interval_sec": interval_sec,
    }


def patch_config_open(monkeypatch, cfg_dict):
    """
    Подменяем builtins.open так, чтобы вызов json.load(open(...satellite.json...))
    возвращал наш cfg.
    """
    real_open = builtins.open

    def fake_open(path, mode="r", *args, **kwargs):
        if str(path).endswith("configs/satellite.yaml") and "r" in mode:
            return io.StringIO(yaml.safe_dump(cfg_dict))
        return real_open(path, mode, *args, **kwargs)


    monkeypatch.setattr(builtins, "open", fake_open)


def read_csv_lines(path: Path):
    return path.read_text(encoding="utf-8").splitlines()


def test_logger_writes_one_valid_signed_line(monkeypatch, tmp_path):
    csv_path = tmp_path / "telemetry.csv"
    cfg = make_cfg(csv_path)

    # конфиг
    patch_config_open(monkeypatch, cfg)

    # сенсор: одно чтение
    reading = {
        "ts": "2025-11-24T17:52:54.510195+00:00",
        "temperature_c": 22.5,
        "humidity_pct": 45.2,
        "pressure_hpa": 1013.2,
        "mode": "NOMINAL",
    }
    monkeypatch.setattr(sat_logger, "BME280Reader", lambda: SensorStub([reading]))

    # останавливаем цикл после первой итерации
    monkeypatch.setattr(sat_logger.time, "sleep", lambda _sec: (_ for _ in ()).throw(KeyboardInterrupt))

    monkeypatch.setenv("SAT_SECRET_HEX", SECRET)

    with pytest.raises(KeyboardInterrupt):
        sat_logger.main()


    lines = read_csv_lines(csv_path)
    assert len(lines) == 2  # header + 1 строка

    header = lines[0]
    data_line = lines[1]

    assert header == "ts,temperature_c,humidity_pct,pressure_hpa,mode,sig"

    parts = data_line.split(",")
    assert len(parts) == 6
    assert verify_signed_line(data_line, SECRET) is True

    # каноничные 2 decimals (важно для стабильного HMAC)
    assert parts[1] == "22.50"
    assert parts[2] == "45.20"
    assert parts[3] == "1013.20"
    assert parts[4] == "NOMINAL"


def test_logger_appends_and_header_not_duplicated(monkeypatch, tmp_path):
    csv_path = tmp_path / "telemetry.csv"
    cfg = make_cfg(csv_path)

    patch_config_open(monkeypatch, cfg)

    readings = [
        {
            "ts": "2025-11-24T17:52:54.510195+00:00",
            "temperature_c": 22.5,
            "humidity_pct": 45.2,
            "pressure_hpa": 1013.2,
            "mode": "NOMINAL",
        },
        {
            "ts": "2025-11-24T17:52:55.510195+00:00",
            "temperature_c": 22.6,
            "humidity_pct": 45.1,
            "pressure_hpa": 1013.1,
            "mode": "NOMINAL",
        },
    ]
    monkeypatch.setattr(sat_logger, "BME280Reader", lambda: SensorStub(readings))

    # sleep: после 2-й итерации выходим
    call_count = {"n": 0}

    def fake_sleep(_sec):
        call_count["n"] += 1
        if call_count["n"] >= 2:
            raise KeyboardInterrupt

    monkeypatch.setattr(sat_logger.time, "sleep", fake_sleep)

    monkeypatch.setenv("SAT_SECRET_HEX", SECRET)

    with pytest.raises(KeyboardInterrupt):
        sat_logger.main()


    lines = read_csv_lines(csv_path)
    assert lines[0] == "ts,temperature_c,humidity_pct,pressure_hpa,mode,sig"
    assert len(lines) == 3  # header + 2 строки

    assert verify_signed_line(lines[1], SECRET) is True
    assert verify_signed_line(lines[2], SECRET) is True


def test_write_header_if_needed_does_not_overwrite_existing(monkeypatch, tmp_path):
    csv_path = tmp_path / "telemetry.csv"
    csv_path.write_text("ts,temperature_c,humidity_pct,pressure_hpa,mode,sig\nX\n", encoding="utf-8")

    sat_logger.write_header_if_needed(csv_path)

    # файл не должен быть перезаписан только header’ом
    lines = read_csv_lines(csv_path)
    assert lines[0] == "ts,temperature_c,humidity_pct,pressure_hpa,mode,sig"
    assert lines[1] == "X"
