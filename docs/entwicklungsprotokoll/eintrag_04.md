# Entwicklungsprotokoll #4 – OBC Telemetry & Security Module

**Datum:** 2025-11-06
**Phase:** On-Board Computer (OBC) Deployment
**Lead:** Oleg Skydan

---

## 🎯 Ziel der Phase
Ziel dieser Etappe war es, den Bordcomputer (OBC) des CubeSat Security Simulators vollständig zu konfigurieren.
Dazu gehören:
- Einrichtung des Telemetrie-Loggers auf dem Raspberry Pi,
- Implementierung der Daten-Signierung mittels HMAC-SHA256,
- Definition der zentralen Konfigurationsdatei `config.json`.

---

## 🧩 Komponentenübersicht

| Datei | Funktion | Beschreibung |
|--------|-----------|--------------|
| `bme_log.py` | Telemetrieerfassung | Liest Sensordaten (BME280 oder Simulation) und schreibt sie im CSV-Format. |
| `hmac_sign.py` | Kryptografische Signierung | Erzeugt HMAC-SHA256-Signaturen für jedes Datenset. |
| `config.json` | Systemkonfiguration | Definiert Betriebsmodus, Pfade, Intervall und Geheimschlüssel. |

---

## ⚙️ Funktionsweise (OBC)

```text
[Raspberry Pi 4]
│
├── bme_log.py
│   ├─ liest BME280 Sensorwerte (oder Simulation)
│   ├─ ruft HMAC-Signatur auf (hmac_sign.py)
│   └─ schreibt CSV: /home/pi/obc/logs/telemetry.csv
│
├── hmac_sign.py
│   └─ erzeugt Signaturen mit geheimem Schlüssel (HMAC-SHA256)
│
└── config.json
    ├─ mode: simulate / sensor
    ├─ csv_path: /home/pi/obc/logs/telemetry.csv
    ├─ sample_interval_sec: 60
    └─ secret_hex: <missionsschlüssel>
```

---

## 🔐 Sicherheitsprinzip

	•	Jede Messung wird mit HMAC-SHA256 signiert.
	•	Der geheime Schlüssel (secret_hex) ist nur auf dem OBC gespeichert.
	•	Die Bodenstation überprüft die Signatur über verify.py und verwirft manipulierte Daten.
	•	Damit ist sichergestellt, dass keine Telemetrie verfälscht werden kann.

---

## 🧠 Erkenntnisse dieser Phase

	•	OBC kann sowohl im Simulationsmodus als auch mit echtem BME280-Sensor betrieben werden.
	•	Pfade werden dynamisch aus config.json geladen – volle Flexibilität bei Deployment.
	•	Die Datenstruktur ist kompatibel mit der Bodenstations-Software (plot.py, receiver.py).
	•	Das System kann ohne Internetverbindung vollständig autark Telemetrie generieren und sichern.

---

## 🚀 Nächste Schritte

	1.	Integration des realen BME280-Sensors auf dem Raspberry Pi.
	2.	Signierung der Telemetriedaten mit hmac_sign.py.
	3.	Übertragung zur Bodenstation über SSH, HTTP oder MQTT.
	4.	Validierung der Signaturen mit verify.py auf der Bodenstation.

---

>> 🧭 „Der Bordcomputer arbeitet stabil – das Herz der Mission schlägt.“
>> — Oleg Skydan, Missionsleiter
