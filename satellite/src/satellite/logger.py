#!/usr/bin/env python3
"""
Satellite Logger – Erfasst Sensordaten (BME280) und schreibt signierte Telemetrie in CSV.

Liest Konfiguration aus configs/satellite.yaml und signiert jeden Datensatz mit HMAC-SHA256.
"""
import csv, time, pathlib, yaml
import os
from .sensors.bme280 import BME280Reader
from shared.protocol.signed_csv import format_signed_line

HERE = pathlib.Path(__file__).resolve().parent

def write_header_if_needed(path):
    if not path.exists() or path.stat().st_size == 0:
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["ts","temperature_c","humidity_pct","pressure_hpa","mode","sig"])

def main():
    CFG = yaml.safe_load(open(HERE.parents[2] / "configs" / "satellite.yaml", "r"))

    CSV_PATH = pathlib.Path(CFG["csv_path"])
    if not CSV_PATH.is_absolute():
        CSV_PATH = HERE.parents[2] / CSV_PATH
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    sensor = BME280Reader()
    write_header_if_needed(CSV_PATH)
    interval = int(CFG["interval_sec"])
    secret_hex = os.getenv("SAT_SECRET_HEX")
    if secret_hex is None:
            raise RuntimeError("SAT_SECRET_HEX nicht gesetzt. Bitte Umgebungsvariable setzen.")

    print(f"[OBC] logging to {CSV_PATH} every {interval}s ... Ctrl+C to stop")
    while True:
        telemetry_unsigned = sensor.read()

        line = format_signed_line(telemetry_unsigned, secret_hex)   # ts,temp,hum,press,mode,sig
        row = line.split(",")

        with open(CSV_PATH, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(row)

        print("[OBC]", ",".join(row[:5]), "->", row[5][:8])
        time.sleep(interval)

if __name__ == "__main__":
    main()
