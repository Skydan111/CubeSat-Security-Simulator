"""
BME280-Sensorreader für das OBC (On-Board Computer)

Funktionen:
- Versucht zuerst echten Hardwarezugriff via I2C (smbus2 + bme280)
- Fällt bei Fehlern automatisch auf einen Simulationsmodus zurück
- Liefert einheitliche Telemetriedaten:
    ts, temperature_c, humidity_pct, pressure_hpa, mode
"""

import time
import random
from datetime import datetime, timezone

# ============================================
# Hardware-Initialisierung (I2C BME280)
# ============================================

_HW = False
_hw_error = None

try:
    import smbus2
    import bme280 as bme280_lib

    I2C_PORT = 1
    BME280_ADDRESS = 0x77  # Dein Sensor: Adresse 0x77

    _bus = smbus2.SMBus(I2C_PORT)
    _calibration_params = bme280_lib.load_calibration_params(_bus, BME280_ADDRESS)

    _HW = True
except Exception as e:
    # Falls Hardware oder Treiber nicht verfügbar sind → Simulationsmodus aktiv
    _hw_error = e
    _HW = False


# ============================================
# Hauptklasse: BME280Reader
# ============================================

class BME280Reader:
    """
    Liest Telemetriedaten vom BME280-Sensor.
    Bei echter Hardware:
        - Temperatur (°C)
        - Luftfeuchtigkeit (%)
        - Luftdruck (hPa)
    Im Simulationsmodus:
        - Erzeugt realistisch wirkende Zufallswerte
    """

    def __init__(self):
        self.sim_start = time.time()

    # ----------------------------------------
    # Ein Messpunkt (Hardware oder Simulation)
    # ----------------------------------------
    def read(self) -> dict:
        """
        Liefert ein Telemetriepaket als dict:
            {
                "ts": ISO-UTC-Zeitstempel,
                "temperature_c": float,
                "humidity_pct": float,
                "pressure_hpa": float,
                "mode": "hardware" | "sim"
            }
        """

        ts = datetime.now(timezone.utc).isoformat()

        # ===== Hardware-Pfad =====
        if _HW:
            try:
                data = bme280_lib.sample(_bus, BME280_ADDRESS, _calibration_params)
                return {
                    "ts": ts,
                    "temperature_c": round(float(data.temperature), 2),
                    "humidity_pct": round(float(data.humidity), 2),
                    "pressure_hpa": round(float(data.pressure), 2),
                    "mode": "hardware"
                }
            except Exception as e:
                # Während der Laufzeit ist ein Fehler aufgetreten → Fallback auf Simulation
                # (Fehler kann optional geloggt werden)
                global _hw_error
                _hw_error = e
                # kein return hier → wir fallen unten in den Simulationspfad

        # ===== Simulationsmodus =====
        t = time.time() - self.sim_start
        temp = 22.0 + 1.5 * (random.random() - 0.5) + 0.5 * (1 if int(t / 30) % 2 == 0 else -1)
        hum = 45.0 + 5.0 * (random.random() - 0.5)
        pres = 1013.0 + 2.0 * (random.random() - 0.5)

        return {
            "ts": ts,
            "temperature_c": round(temp, 2),
            "humidity_pct": round(hum, 2),
            "pressure_hpa": round(pres, 2),
            "mode": "sim"
        }
