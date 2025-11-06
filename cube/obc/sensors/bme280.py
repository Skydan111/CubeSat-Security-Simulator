import time, random
from datetime import datetime, timezone

# Пытаемся работать с реальным BME280
try:
    import board, busio
    import adafruit_bme280
    _HW = True
except Exception:
    _HW = False

class BME280Reader:
    def __init__(self):
        self.sim_start = time.time()
        if _HW:
            i2c = busio.I2C(board.SCL, board.SDA)
            self.bme = adafruit_bme280.Adafruit_BME280_I2C(i2c)  # addr 0x76/0x77
            self.bme.sea_level_pressure = 1013.25

    def read(self):
        ts = datetime.now(timezone.utc).isoformat()
        if _HW:
            return {
                "ts": ts,
                "temperature_c": round(float(self.bme.temperature), 2),
                "humidity_pct": round(float(self.bme.humidity), 2),
                "pressure_hpa": round(float(self.bme.pressure), 2),
                "mode": "hardware"
            }
        # --- симулятор ---
        t = time.time() - self.sim_start
        temp = 22.0 + 1.5 * (random.random() - 0.5) + 0.5 * (1 if int(t/30)%2==0 else -1)
        hum  = 45.0 + 5.0 * (random.random() - 0.5)
        pres = 1013.0 + 2.0 * (random.random() - 0.5)
        return {
            "ts": ts,
            "temperature_c": round(temp, 2),
            "humidity_pct": round(hum, 2),
            "pressure_hpa": round(pres, 2),
            "mode": "sim"
        }
