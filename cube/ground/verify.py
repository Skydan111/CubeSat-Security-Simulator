import hmac, hashlib, binascii

def verify(secret_hex: str, payload_bytes: bytes, mac_hex: str) -> bool:
    key = binascii.unhexlify(secret_hex)
    expected = hmac.new(key, payload_bytes, hashlib.sha256).hexdigest()
    # защищённое сравнение, чтобы не «протекало» время сравнения
    return hmac.compare_digest(expected, mac_hex)
