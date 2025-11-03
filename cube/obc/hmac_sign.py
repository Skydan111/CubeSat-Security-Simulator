import hmac, hashlib, binascii

def sign_payload(secret_hex: str, payload_bytes: bytes) -> str:
    key = binascii.unhexlify(secret_hex)
    mac = hmac.new(key, payload_bytes, hashlib.sha256).hexdigest()
    return mac
