# 🛰️ Mission Report #2 – Phase: System Boot & Telemetry Simulation

**Datum:** 2025-11-04
**Phase:** System Boot & Telemetry Simulation
**Lead:** Oleg Skydan

---

## 🎯 Missionsziel
Erfolgreicher Systemstart des Raspberry Pi („pi-cube“) und erste Tests der Telemetrie-Simulation.
Ziel dieser Phase war die Inbetriebnahme des On-Board-Computers, die Einrichtung des SSH-Zugangs und die Erzeugung der ersten Telemetriedaten im CSV-Format.

---

## 🧩 Statusübersicht

| Bereich | Status | Beschreibung |
|----------|---------|---------------|
| Hardwaremontage | ✅ | Raspberry Pi 4 mit Heatsinks, Gehäuse und MicroSD vorbereitet |
| OS-Installation | ✅ | Raspberry Pi OS Lite (64 bit) via Imager installiert |
| Netzwerk & SSH | ✅ | Hostname **pi-cube**, Verbindung über WLAN & SSH erfolgreich |
| Systemdiagnose | ✅ | Temperatur (≈ 39 °C), `htop` Systemüberwachung getestet |
| Telemetrie-Logger | ✅ | `main.py` Simulation erzeugt CSV mit signierten Datensätzen |
| Sicherheit | ✅ | HMAC-Signaturen aktiv, Signaturlog erfolgreich geprüft |

---

## ⚙️ Technische Details

- **Hostname:** pi-cube.local
- **System:** Debian Trixie (64-bit, Kernel 6.12.47)
- **SSH-Zugriff:** aktiv, Authentifizierung via Passwort
- **Temperatur:** 38.9 °C unter Leerlauf
- **Datei:** `~/obc/logs/telemetry.csv` enthält valide Datenpunkte + Signatur

---

## 📊 Beispiel Telemetrie-Auszug
```text
ts,temperature_c,humidity_pct,pressure_hpa,mode,sig
2025-11-04T14:15:08Z,22.1,45.37,1013.75,sim,051d03ad8e328941ec6eca213433af9eed7
```

---

## 🚀 Nächste Schritte (Woche 2)

1. **Integration realer Sensorik (BME280)**
   – I²C-Schnittstelle aktivieren
   – Testskript `bme280.py` anpassen

2. **Automatischer Missionsstart**
   – Service (`systemd`) für Autostart von Telemetrie-Logging konfigurieren

3. **Datenupload vorbereiten**
   – Entwurf für `receiver.py` (MQTT oder HTTP)

---

## 📓 Kommentar des Missionsleiters

> *„Der Pi-Cube lebt!
>  Systemdiagnose stabil, Telemetrie läuft,
>  und die Mission erreicht Orbit-Level-1.“*
>  — **Oleg Skydan**, Missionsleiter

---

📁 *Lokale Logs und Signaturdateien gespeichert unter* `~/obc/logs/`
🛰️ *System bereit für Phase 3: Sensorintegration.*
