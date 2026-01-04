import pytest

from satellite.sensors import bme280


def test_bme280_reader_sim_returns_expected_schema(monkeypatch):
    # Гарантируем сим-режим (без железа)
    monkeypatch.setattr(bme280, "_HW", False)

    r = bme280.BME280Reader()
    d = r.read()

    assert isinstance(d, dict)

    # ключи
    for k in ["ts", "temperature_c", "humidity_pct", "pressure_hpa", "mode"]:
        assert k in d

    # типы
    assert isinstance(d["ts"], str)
    assert d["ts"]  # не пустая строка

    assert isinstance(d["temperature_c"], float)
    assert isinstance(d["humidity_pct"], float)
    assert isinstance(d["pressure_hpa"], float)

    # режим
    assert d["mode"] == "sim"


def test_bme280_reader_values_are_rounded_to_two_decimals(monkeypatch):
    monkeypatch.setattr(bme280, "_HW", False)

    r = bme280.BME280Reader()
    d = r.read()

    # Проверяем, что значения соответствуют округлению до 2 знаков.
    # Это не про точность сенсора, а про стабильность формата.
    assert d["temperature_c"] == pytest.approx(round(d["temperature_c"], 2))
    assert d["humidity_pct"] == pytest.approx(round(d["humidity_pct"], 2))
    assert d["pressure_hpa"] == pytest.approx(round(d["pressure_hpa"], 2))
