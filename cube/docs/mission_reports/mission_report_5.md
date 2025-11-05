# 🛰️ Mission Report #5 – Secure Key Sync & First Data Transmission Test
**Date:** 2025-11-05
**Status:** ✅ Completed
**Phase:** 🔐 Security Integration / Data Link Test

---

## 🧩 Summary
In this phase, the Ground Station (Mac) and the On-Board Computer (Raspberry Pi 4) were successfully synchronized and linked through a simulated secure telemetry transmission.

The mission verified that the **HMAC-SHA256 key** used for signing and verifying telemetry data is identical on both systems, ensuring data authenticity and integrity.

A first manual data transfer of `telemetry.csv` from the OBC to the Ground Station was completed using `scp`, confirming bidirectional communication readiness.

---

## 🛰️ Actions Performed
1. Generated and synchronized a shared **HMAC secret** between Ground and OBC.
2. Created `ground.json` and `mission.json` configuration files with identical secret values.
3. Implemented a validation script (`check_key.py`) confirming key match.
4. Verified telemetry generation on Raspberry Pi (`/home/pi/obc/logs/telemetry.csv`).
5. Simulated the first manual data transmission via `scp` to `data/raw/telemetry.csv` on the Ground Station.
6. Confirmed file integrity and structure.

---

## 📡 Result
✅ Ground and OBC are cryptographically synchronized.
✅ Secure telemetry data successfully transferred from OBC → Ground.
⚙️ Next phase: Automate transmission via `rsync` or MQTT, integrate signature verification and data pipeline (processed / rejected / visualization).

---

📘 *Report prepared by Oleg Skydan – CubeSat Security Simulator Project (Fachschule Wiesau)*
