#!/usr/bin/env python3
import os, csv, time, json, datetime, random, pathlib

HERE = pathlib.Path(__file__).resolve().parent
CFG = json.load(open(HERE / "config.json", "r"))

CSV_PATH = pathlib.Path(CFG["csv_path"])
CSV_PATH.parent.mkdir(parents=True, exist_ok=True)

def read_bme280():
    """Пытаемся читать реальный сенсор. Если не вышло — кидаем исключение."""
    import board, busio
    from adafruit_bme280 import basic as adafruit_bme280
    i2c = busio.I2C(board.SCL, board.SDA)
    bme = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)
    return {
        "temperature": round(bme.temperature, 2),
        "humidity": round(bme.humidity, 2),
        "pressure": round(bme.pressure, 2)
    }

def simulate():
    """Эмуляция телеметрии: стабильные, но немного шумящие значения."""
    base_t, base_h, base_p = 22.0, 45.0, 1013.0
    return {
        "temperature": round(base_t + random.uniform(-0.5, 0.8), 2),
        "humidity":    round(base_h + random.uniform(-2.0, 2.0), 2),
        "pressure":    round(base_p + random.uniform(-1.5, 1.5), 2),
    }

def get_sample():
    if CFG.get("mode") == "sensor":
        try:
            return read_bme280()
        except Exception as e:
            print(f"[WARN] Sensor fallback to simulate ({e})")
            return simulate()
    return simulate()

def write_header_if_needed(path: pathlib.Path):
    if not path.exists() or path.stat().st_size == 0:
        with open(path, "w", newline="") as f:
            csv.writer(f).writerow(["ts","temperature","humidity","pressure"])

def main():
    write_header_if_needed(CSV_PATH)
    interval = int(CFG.get("sample_interval_sec", 60))
    while True:
        ts = datetime.datetime.now(datetime.UTC).isoformat()
        s = get_sample()
        row = [ts, s["temperature"], s["humidity"], s["pressure"]]
        with open(CSV_PATH, "a", newline="") as f:
            csv.writer(f).writerow(row)
        print(f"[OBC] {row}")
        time.sleep(interval)

if __name__ == "__main__":
    main()
