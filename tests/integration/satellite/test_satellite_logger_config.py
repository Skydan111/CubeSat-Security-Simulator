import yaml
from pathlib import Path
import pytest

from shared.protocol.signed_csv import verify_signed_line
from satellite import logger as sat_logger
from shared.protocol.telemetry_csv import TelemetryUnsigned


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


def test_logger_uses_real_satellite_json_config(monkeypatch, tmp_path):
    # Строим временную структуру так, чтобы HERE.parents[2] == tmp_path
    # Нужно: tmp_path/configs/satellite.json
    # Значит HERE должен быть: tmp_path/x/y/z  (тогда parents[2] == tmp_path)
    fake_here = tmp_path / "x" / "y" / "z"
    fake_here.mkdir(parents=True, exist_ok=True)

    configs_dir = tmp_path / "configs"
    configs_dir.mkdir(parents=True, exist_ok=True)

    cfg = {
        "mode": "simulate",
        "csv_path": "logs/telemetry.csv",
        "interval_sec": 60,
    }
    (configs_dir / "satellite.yaml").write_text(yaml.safe_dump(cfg),)

    # Подменяем HERE в модуле logger
    monkeypatch.setattr(sat_logger, "HERE", fake_here)

    # Подменяем сенсор
    monkeypatch.setattr(sat_logger, "BME280Reader", lambda: SensorStub([{
        "ts": "2025-11-24T17:52:54.510195+00:00",
        "temperature_c": 22.5,
        "humidity_pct": 45.2,
        "pressure_hpa": 1013.2,
        "mode": "sim",
    }]))


    # Останавливаем после 1 итерации
    monkeypatch.setattr(sat_logger.time, "sleep", lambda _sec: (_ for _ in ()).throw(KeyboardInterrupt))

    monkeypatch.setenv("SAT_SECRET_HEX", "a54f2e7b3c9084ee2a6b9f1d77c4a3e9b2d1c0f4e6a8b0c2d4f6e8a0c1d2e3f4")

    with pytest.raises(KeyboardInterrupt):
        sat_logger.main()


    # csv_path относительный => должен резолвиться относительно tmp_path
    csv_path = tmp_path / "logs" / "telemetry.csv"
    assert csv_path.exists()

    lines = csv_path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "ts,temperature_c,humidity_pct,pressure_hpa,mode,sig"
    assert len(lines) == 2

    data_line = lines[1]
    assert verify_signed_line(data_line, "a54f2e7b3c9084ee2a6b9f1d77c4a3e9b2d1c0f4e6a8b0c2d4f6e8a0c1d2e3f4") is True
