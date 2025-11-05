import hmac, hashlib, binascii

def verify(secret_hex: str, payload_bytes: bytes, mac_hex: str) -> bool:
    """
    Überprüft eine HMAC-SHA256-Signatur.

    Parameter:
        secret_hex (str): Geheimer Schlüssel im Hex-Format.
        payload_bytes (bytes): Die originalen Nutzdaten (z. B. Telemetriedaten).
        mac_hex (str): Die empfangene HMAC-Signatur im Hex-Format.

    Rückgabe:
        bool – True, wenn die Signatur gültig ist, sonst False.
    """
    # Konvertiert den Hex-Schlüssel in Byte-Form
    key = binascii.unhexlify(secret_hex)

    # Berechnet die erwartete Signatur (HMAC-SHA256)
    expected = hmac.new(key, payload_bytes, hashlib.sha256).hexdigest()

    # Sichere Vergleichsmethode, um Zeitangriffs-Lecks zu vermeiden
    return hmac.compare_digest(expected, mac_hex)
