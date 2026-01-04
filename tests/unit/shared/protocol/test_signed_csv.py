import pytest

from shared.protocol.signed_csv import (
    format_signed_line,
    parse_signed_line,
    verify_signed_line,
)
from shared.protocol.telemetry_csv import TelemetryUnsigned, format_payload
from shared.crypto.hmac_sha256 import sign as hmac_sign


SECRET = "aabbccddeeff00112233445566778899"

def test_parse_signed_line_ts_is_string():
    u = make_unsigned()
    line = format_signed_line(u, SECRET)
    parsed = parse_signed_line(line)
    assert isinstance(parsed.unsigned.ts, str)

def make_unsigned():
    # Подстрой поля под реальный TelemetryUnsigned в telemetry_csv.py,
    # если у тебя другие имена/порядок.
    return TelemetryUnsigned(
        ts="1700000000",
        temperature_c=21.5,
        humidity_pct=45.2,
        pressure_hpa=1013.2,
        mode="NOMINAL",
    )


def test_format_signed_line_has_6_fields_and_valid_sig():
    u = make_unsigned()
    line = format_signed_line(u, SECRET)

    parts = line.split(",")
    assert len(parts) == 6

    payload = ",".join(parts[:5])
    sig = parts[5]
    assert sig == hmac_sign(payload, SECRET)


def test_parse_signed_line_roundtrip_unsigned_fields():
    u = make_unsigned()
    line = format_signed_line(u, SECRET)

    parsed = parse_signed_line(line)
    assert parsed.unsigned == u
    assert isinstance(parsed.sig, str)
    assert len(parsed.sig) == 64


def test_verify_signed_line_accepts_valid_line():
    u = make_unsigned()
    line = format_signed_line(u, SECRET)
    assert verify_signed_line(line, SECRET) is True


def test_verify_signed_line_rejects_tampered_payload():
    u = make_unsigned()
    line = format_signed_line(u, SECRET)

    # Подмена одного символа в payload-части
    tampered = line.replace("21.5", "21.6", 1)
    assert verify_signed_line(tampered, SECRET) is False


def test_verify_signed_line_rejects_wrong_secret():
    u = make_unsigned()
    line = format_signed_line(u, SECRET)

    wrong_secret = "deadbeefdeadbeefdeadbeefdeadbeef"
    assert verify_signed_line(line, wrong_secret) is False


def test_parse_signed_line_raises_on_wrong_field_count():
    with pytest.raises(ValueError):
        parse_signed_line("a,b,c")  # явно не 6 полей


def test_verify_uses_canonical_payload_from_parsed_unsigned():
    """
    Ключевой тест семантики: verify подписывает/проверяет не "сырой текст строки",
    а канонический payload, полученный через parse_payload + format_payload.

    Это важно зафиксировать, чтобы потом никто случайно не поменял смысл verify().
    """
    u = make_unsigned()
    canonical_payload = format_payload(u)
    canonical_sig = hmac_sign(canonical_payload, SECRET)

    # Сделаем строку с теми же значениями, но в "текстово-другом" виде,
    # который parse_payload должен прочитать и привести к каноническому виду.
    # Пример: лишние нули/пробелы (если parse_payload это допускает).
    # Если parse_payload строгое и не принимает такое — этот тест адаптируем под реальные правила.
    funky_line = f"{u.ts},21.500,45.200,1013.200,{u.mode},{canonical_sig}"

    # Мы ожидаем True, если parse_payload принимает такое представление и
    # format_payload нормализует обратно в canonical_payload.
    assert verify_signed_line(funky_line, SECRET) is True
