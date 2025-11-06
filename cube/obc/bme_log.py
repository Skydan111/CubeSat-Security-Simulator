#!/usr/bin/env python3
import csv, json, os, hmac, hashlib, time, pathlib, binascii
from sensors.bme280 import BME280Reader

HERE = pathlib.Path(__file__).resolve().parent
CFG = json.load(open(HERE / "config" / "mission.json", "r"))
CSV_PATH = pathlib.Path(CFG["csv_path"])
CSV_PATH.parent.mkdir(parents=True, exist_ok=True)


def sign_csv(payload_str: str, secret_hex: str) -> str:

    key = binascii.unhexlify(secret_hex.strip())
    return hmac.new(key, payload_str.encode("utf-8"), hashlib.sha256).hexdigest()

def write_header_if_needed(path):
    if not path.exists() or path.stat().st_size == 0:
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["ts","temperature_c","humidity_pct","pressure_hpa","mode","sig"])

def main():
    sensor = BME280Reader()
    write_header_if_needed(CSV_PATH)
    interval = int(CFG["interval_sec"])
    secret_hex = CFG["hmac_secret"]

    print(f"[OBC] logging to {CSV_PATH} every {interval}s ... Ctrl+C to stop")
    while True:
        d = sensor.read()

        payload = f"{d['ts']},{d['temperature_c']:.2f},{d['humidity_pct']:.2f},{d['pressure_hpa']:.2f},{d['mode']}"
        sig = sign_csv(payload, secret_hex)


        with open(CSV_PATH, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([d["ts"], f"{d['temperature_c']:.2f}", f"{d['humidity_pct']:.2f}",
                             f"{d['pressure_hpa']:.2f}", d["mode"], sig])

        print("[OBC]", payload, "->", sig[:8])
        time.sleep(interval)

if __name__ == "__main__":
    main()
