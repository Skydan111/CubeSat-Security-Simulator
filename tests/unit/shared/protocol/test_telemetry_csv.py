import pytest

from shared.protocol.telemetry_csv import HEADER, TelemetryUnsigned, format_payload, parse_payload


def make_unsigned():
    return TelemetryUnsigned(
        ts="2025-11-24T17:52:54.510195+00:00",
        temperature_c=21.5,
        humidity_pct=45.2,
        pressure_hpa=1013.2,
        mode="NOMINAL",
    )


def test_header_contract_is_stable():
    assert HEADER == ["ts", "temperature_c", "humidity_pct", "pressure_hpa", "mode", "sig"]


def test_format_payload_is_canonical_two_decimals():
    u = make_unsigned()
    payload = format_payload(u)

    # Проверяем точный формат, чтобы подпись была стабильной
    assert payload == "2025-11-24T17:52:54.510195+00:00,21.50,45.20,1013.20,NOMINAL"


def test_parse_payload_roundtrip_from_format():
    u = make_unsigned()
    payload = format_payload(u)
    parsed = parse_payload(payload)

    assert parsed.ts == u.ts
    assert parsed.mode == u.mode
    assert parsed.temperature_c == pytest.approx(u.temperature_c)
    assert parsed.humidity_pct == pytest.approx(u.humidity_pct)
    assert parsed.pressure_hpa == pytest.approx(u.pressure_hpa)


def test_parse_payload_strips_outer_whitespace():
    u = make_unsigned()
    payload = "  " + format_payload(u) + "  "
    parsed = parse_payload(payload)
    assert parsed == u


@pytest.mark.parametrize("bad_payload", [
    "a,b,c,d",              # 4 поля
    "a,b,c,d,e,f",          # 6 полей
    "",                     # 0 полей
])
def test_parse_payload_rejects_wrong_field_count(bad_payload):
    with pytest.raises(ValueError):
        parse_payload(bad_payload)


def test_parse_payload_converts_numeric_fields_to_float():
    payload = "2025-11-24T17:52:54+00:00,21.50,45.20,1013.20,NOMINAL"
    u = parse_payload(payload)
    assert isinstance(u.temperature_c, float)
    assert isinstance(u.humidity_pct, float)
    assert isinstance(u.pressure_hpa, float)
