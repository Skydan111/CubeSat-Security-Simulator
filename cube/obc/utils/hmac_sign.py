import hmac, hashlib, binascii

def sign_payload(secret_hex: str, payload_bytes: bytes) -> str:
    """
    Erzeugt eine HMAC-SHA256-Signatur für die angegebenen Nutzdaten.

    Parameter:
        secret_hex (str): Geheimer Schlüssel im Hex-Format.
        payload_bytes (bytes): Die zu signierenden Daten.

    Rückgabe:
        str – Signatur im Hex-Format.
    """
    # Konvertiert den geheimen Schlüssel von Hex zu Bytes
    key = binascii.unhexlify(secret_hex)

    # Erzeugt die HMAC-SHA256-Signatur
    mac = hmac.new(key, payload_bytes, hashlib.sha256).hexdigest()

    # Gibt die hexadezimale Signatur zurück
    return mac
