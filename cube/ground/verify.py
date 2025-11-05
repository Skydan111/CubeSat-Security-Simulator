import hmac, hashlib, binascii, json, os, pathlib

# --- Neue Sektion: Laden der Konfiguration ---
HERE = pathlib.Path(__file__).resolve().parent
CFG_PATH = HERE / "config" / "ground.json"

def _load_secret_hex() -> str:
    """
    Bezieht den geheimen Schlüssel (Hex) aus:
    1) Umgebungsvariable HMAC_SECRET_HEX (falls gesetzt),
    2) sonst aus config/ground.json ("hmac_secret").
    """
    env = os.getenv("HMAC_SECRET_HEX")
    if env:
        return env.strip()
    with open(CFG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    return cfg["hmac_secret"].strip()


# --- Deine ursprüngliche Funktion bleibt unverändert ---
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
    key = binascii.unhexlify(secret_hex)
    expected = hmac.new(key, payload_bytes, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, mac_hex)


# --- Zusatzfunktion: Automatische Variante ---
def verify_with_config(payload_bytes: bytes, mac_hex: str) -> bool:
    """Lädt den geheimen Schlüssel automatisch aus config/ground.json."""
    secret = _load_secret_hex()
    return verify(secret, payload_bytes, mac_hex)
