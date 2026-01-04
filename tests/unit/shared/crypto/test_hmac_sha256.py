import pytest

from shared.crypto.hmac_sha256 import sign, verify


SECRET = "aabbccddeeff00112233445566778899"
PAYLOAD = "temp=21.5,pressure=1013.2,ts=1700000000"


def test_sign_is_deterministic():
    sig1 = sign(PAYLOAD, SECRET)
    sig2 = sign(PAYLOAD, SECRET)
    assert sig1 == sig2


def test_verify_accepts_valid_signature():
    sig = sign(PAYLOAD, SECRET)
    assert verify(PAYLOAD, SECRET, sig) is True


def test_verify_rejects_modified_payload():
    sig = sign(PAYLOAD, SECRET)
    tampered = PAYLOAD + "X"
    assert verify(tampered, SECRET, sig) is False


def test_verify_rejects_wrong_secret():
    sig = sign(PAYLOAD, SECRET)
    wrong_secret = "deadbeefdeadbeefdeadbeefdeadbeef"
    assert verify(PAYLOAD, wrong_secret, sig) is False


def test_verify_strips_whitespace():
    sig = sign(PAYLOAD, SECRET)
    assert verify(PAYLOAD, f"  {SECRET}  ", f" {sig} ") is True


def test_signature_format_is_hex_sha256():
    sig = sign(PAYLOAD, SECRET)
    assert isinstance(sig, str)
    assert len(sig) == 64
    int(sig, 16)  # не должно бросать исключение
