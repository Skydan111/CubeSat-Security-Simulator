import hmac
import hashlib
import binascii


def sign(payload_str: str, secret_hex: str) -> str:
    key = binascii.unhexlify(secret_hex.strip())
    return hmac.new(key, payload_str.encode("utf-8"), hashlib.sha256).hexdigest()


def verify(payload_str: str, secret_hex: str, sig_hex: str) -> bool:
    expected = sign(payload_str, secret_hex)
    return hmac.compare_digest(expected, sig_hex.strip())
