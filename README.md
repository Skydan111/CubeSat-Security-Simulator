# 🛰️ CubeSat Security Simulator

> **Mission Phase:** Testing & Validation (abgeschlossen)
> **Status:** Kernsystem stabil
> **Last Update:** 2026-01-04

## Inhaltsverzeichnis
- [Missionsübersicht](#-missionsübersicht)
- [Zielsetzung](#-zielsetzung)
- [Systemarchitektur](#-systemarchitektur)
- [Telemetrie-Pipeline](#-telemetrie-pipeline)
- [Sicherheitskonzept](#-sicherheitskonzept)
- [Teststrategie](#-teststrategie)
- [Technologien](#-technologien)
- [Projektstruktur](#-projektstruktur)
- [Installation & Tests](#️-installation&tests)
- [Autor](#-autor)
- [Mission Timeline](#️-mission-timeline)
- [Datenstruktur (Bodenstation)](#-datenstruktur-bodenstation)


## Missionsübersicht
Der **CubeSat Security Simulator** ist ein ingenieurorientiertes Lernprojekt zur Simulation eines sicheren Telemetriesystems für einen CubeSat.

Das Projekt modelliert die vollständige Datenkette von der Telemetrieerzeugung auf dem On-Board Computer bis zur Verifikation und Verarbeitung auf der Bodenstation.
Der Fokus liegt auf **Datenintegrität, Sicherheit, klarer Architektur und Testbarkeit**.


---

## Zielsetzung

- Simulation eines CubeSat-On-Board-Computers (Satellite)
- Erfassung von Sensordaten (BME280 oder Simulation)
- Kryptographische Absicherung der Telemetrie mittels HMAC-SHA256
- Verifikation und Klassifikation eingehender Daten auf der Bodenstation
- Robuste Behandlung fehlerhafter oder manipulierter Pakete
- Vollständige Unit-, Integrations- und Security-Tests

---

## Systemarchitektur

```text
+------------------------+            +--------------------------+
|       Satellite        |            |       Bodenstation       |
|  (Raspberry Pi / Sim)  |            |     (Laptop / Server)    |
|------------------------|            |--------------------------|
| BME280 Sensor / Sim    |── CSV ───▶ | Receiver-Pipeline        |
| Telemetry Logger       |            |  • RAW-Ingestion         |
| HMAC-Signierung        |            |  • HMAC-Verifikation     |
+------------------------+            |  • Adaptive Security     |
                                      |  • Routing (processed /  |
                                      |    rejected / quarantine)|
                                      +--------------------------+
```
---

## 📡 Telemetrie-Pipeline (ASCII-Diagramm)
```text
Satellite
  └─ Sensor lesen
  └─ Payload formatieren
  └─ HMAC-Signatur erzeugen
  └─ CSV-Zeile anhängen

Ground Station
  RAW → VERIFY → SECURITY →
     ├─ processed/
     ├─ rejected/
     └─ quarantine/


Die Pipeline ist bewusst pull-basiert (z. B. via scp) gehalten, um Robustheit und Nachvollziehbarkeit zu gewährleisten.
```
---

## Sicherheitskonzept

### Kryptographie
- HMAC-SHA256
- Gemeinsamer geheimer Schlüssel (hexadezimal)
- Signatur über den vollständigen Payload

### Adaptive Sicherheitsebene (Ground Station)
- Gleitendes Analysefenster
- Gewichtete Fehlertypen
- Erkennung aufeinanderfolgender Fehler
- Temporäre Lockouts bei Anomalien
- Konfigurierbare Reaktion:
  - drop
  - reject
  - quarantine

### Logging
- `security.log` (lesbares Log)
- `security_audit.jsonl` (maschinenlesbar)

---

## Teststrategie

Testing ist ein integraler Bestandteil des Projekts.

### Abgedeckte Ebenen

**Unit-Tests**
- Kryptographie (HMAC)
- Protokoll-Parsing (CSV / Signed Payload)
- Security Manager (Policy, Lockout, Windowing)
- Satellite Logger
- Sensor-Abstraktion

**Integrations-Tests**
- End-to-End Satellite → Ground Pipeline
- Nutzung realer Konfigurationsdateien
- Verifikation der vollständigen Datenkette

**Security-Tests**
- Manipulierte Payloads (Tampering)
- Ungültige oder abgeschnittene Pakete
- Lockout- und Quarantäneverhalten

Aktueller Stand:
- 49 Tests
- Alle Tests erfolgreich (`pytest -q`)

---

## Technologien
| Komponente | Technologie |
|-------------|-------------|
| Hardware | Raspberry Pi 4 B (4 GB), BME280 Sensor |
| Programmiersprache | Python 3 |
| Kommunikation | MQTT / HTTP |
| Kryptographie | HMAC-SHA256, hashlib |
| Visualisierung | matplotlib / Streamlit |
| Betriebssystem | Raspberry Pi OS (Linux) |

---

## Projektstruktur

```text
CubeSat/
├── satellite/              # On-Board Computer
│   └── src/satellite/
│       ├── logger.py
│       └── sensors/
│           └── bme280.py
│
├── ground/                 # Bodenstation
│   └── src/ground/
│       ├── receiver.py
│       └── security/
│           └── security_manager.py
│
├── shared/                 # Gemeinsames Protokoll & Kryptographie
│   └── src/shared/
│       ├── crypto/
│       └── protocol/
│
├── configs/
│   ├── satellite.json
│   └── security_policy.yaml
│
├── tests/
│   ├── unit/
│   └── integration/
│
├── requirements*.txt
└── README.md
```
---

## Installation & Tests
```bash
git clone https://github.com/olegskydan/CubeSat-Security-Simulator.git
cd CubeSat-Security-Simulator
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
```

---

## Mission Timeline

| Phase | Status | Beschreibung |
|------|--------|--------------|
| Pre-Launch & Architektur | Abgeschlossen | Projektstruktur, Modultrennung, Architekturdefinition |
| Core Telemetrie-Pipeline | Abgeschlossen | Signierung und Verarbeitung der Telemetriedaten |
| Adaptive Sicherheitsebene | Abgeschlossen | Security Manager, Lockout- und Audit-Logik |
| Phase 3: Testing & Validation | Abgeschlossen | Unit-, Integrations- und Security-Tests |
| Phase 4: Secure Satellite-to-Ground Communication | Geplant | Reale Datenübertragung (z. B. MQTT) |
| Live-Hardware-Betrieb | Geplant | Betrieb auf realer Hardware |

---

## Autor

Oleg Skydan
Student Wirtschaftsinformatik – Fachschule Wiesau

Schwerpunkte:
- Cybersecurity
- Embedded Systems
- Distributed Systems
- Secure Communication

---

### Datenfluss (Überblick)

1. **OBC (On-Board Computer)** auf dem Raspberry Pi erzeugt Telemetriedaten und schreibt sie lokal in CSV-Dateien.
2. **Ground Station (Mac)** empfängt diese Dateien regelmäßig (z. B. über `scp`, `MQTT` oder `HTTP`) und legt sie in `data/raw/obc/` ab.
3. Danach folgt die Verifizierung, Verarbeitung und Archivierung der Daten.

---

*Dokument aktualisiert: Januar 2026*

---

*Next Phase:* Live Communication & Data Link
