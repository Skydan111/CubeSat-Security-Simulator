# 🛰️ CubeSat Security Simulator

> **Mission Phase:** 🧪 Phase 3 — Testing & Validation (abgeschlossen)
> **Status:** ✅ Kernsystem stabil
> **Last Update:** 2026-01-04

## 📘 Inhaltsverzeichnis
- [🚀 Missionsübersicht](#-missionsübersicht)
- [🌌 Motivation & Vision](#-motivation--vision)
- [🎯 Missionsziele](#-missionsziele)
- [🧩 Systemarchitektur](#-systemarchitektur)
- [📡 Telemetrie-Pipeline](#-telemetrie-pipeline)
- [🔐 Adaptive Sicherheitsebene](#-adaptivesicherheitsebene)
- [🧠 Technologien](#-technologien)
- [📦 Projektstruktur](#-projektstruktur)
- [⚙️ Installation](#️-installation)
- [👨‍🚀 Autor](#-autor)
- [🗓️ Mission Timeline](#️-mission-timeline)
- [📂 Datenstruktur (Bodenstation)](#-datenstruktur-bodenstation)


## 🚀 Missionsübersicht
Der CubeSat Security Simulator ist ein lern- und ingenieurorientiertes Projekt zur Simulation eines sicheren CubeSat-Telemetriesystems mit klar getrennter Architektur:
 - On-Board Computer (Satellite)
 - Ground Station (Bodenstation)
 - Shared Protocol & Kryptographie

Der Fokus liegt auf Datenintegrität, sicherer Verarbeitung von Telemetrie sowie auf robuster Fehler- und Angriffsbehandlung, angelehnt an reale CubeSat- und Raumfahrtarchitekturen.


---

## 🌌 Motivation & Vision
Moderne CubeSats und vernetzte Raumfahrt-/IoT-Systeme sind stark von zuverlässiger und sicherer Telemetrie abhängig.
Dieses Projekt entstand aus dem Wunsch, praxisnah zu verstehen:
 - wie Sensordaten an Bord eines Satelliten erzeugt werden,
 - wie diese Daten kryptographisch abgesichert werden können,
 - wie eine Bodenstation Daten verifiziert, klassifiziert und sicher verarbeitet.

Ziel ist kein reines Demo-Projekt, sondern ein sauber strukturiertes, testbares und nachvollziehbares System, das reale ingenieurtechnische Prinzipien widerspiegelt.


---

## 🎯 Missionsziele
 - Simulation eines CubeSat-On-Board-Computers (Raspberry Pi + BME280)
 - Signierung jedes Telemetriepakets mit HMAC-SHA256
 - Robuste Verifikation auf der Bodenstation
 - Adaptive Sicherheitslogik (Lockout, Quarantäne, Reject)
 - Vollständige Unit-, Integrations- und Security-Tests

---

## 🧩 Systemarchitektur

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

## 🔐 Adaptive Sicherheits­ebene
Die Bodenstation enthält einen Adaptive Security Manager mit folgenden Eigenschaften:
 - Gleitendes Analysefenster
 - Gewichtete Fehlertypen
 - Erkennung aufeinanderfolgender Fehler
 - Temporäre Lockouts
 - Konfigurierbares Verhalten:
 - drop
 - reject
 - quarantine

Alle sicherheitsrelevanten Ereignisse werden protokolliert in:
 - security.log (lesbar für Menschen)
 - security_audit.jsonl (maschinenlesbar)


---

## 🧠 Technologien
| Komponente | Technologie |
|-------------|-------------|
| Hardware | Raspberry Pi 4 B (4 GB), BME280 Sensor |
| Programmiersprache | Python 3 |
| Kommunikation | MQTT / HTTP |
| Kryptographie | HMAC-SHA256, hashlib |
| Visualisierung | matplotlib / Streamlit |
| Betriebssystem | Raspberry Pi OS (Linux) |

---

## 📦 Projektstruktur

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

## ⚙️ Installation
```bash
git clone https://github.com/olegskydan/CubeSat-Security-Simulator.git
cd CubeSat-Security-Simulator
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
---

## 👨‍🚀 Autor

**Oleg Skydan**
*Student · Wirtschaftsinformatik · Fachschule Wiesau*
**Interessen:** Space Tech · Cybersecurity · IoT-Systeme

💡 *„Jede große Mission beginnt klein – manchmal auf einem Breadboard.“*

---

## 🧭 Mission Timeline

| Phase | Status | Beschreibung |
|------|--------|--------------|
| 🧭 **Pre-Launch & Architektur** | ✅ Abgeschlossen | Projektinitialisierung, Repository-Struktur, klare Trennung von `satellite`, `ground` und `shared`. |
| 🛰️ **Core Telemetrie-Pipeline** | ✅ Abgeschlossen | Sichere Erzeugung, Signierung und Verarbeitung von Telemetriedaten (CSV + HMAC). |
| 🔐 **Adaptive Sicherheitsebene** | ✅ Abgeschlossen | Implementierung des Security Managers mit Lockout-, Quarantäne- und Audit-Logik. |
| 🧪 **Testing & Validation** | ✅ Abgeschlossen | Umfassende Unit-, Integrations- und Security-Tests für Satellite und Ground Station (49 Tests). |
| 🤖 **CI / GitHub Actions** | ⏳ Geplant | Automatisierter Testlauf bei Push & Pull Requests. |
| 🚀 **Live-Hardware-Mission** | ⏳ Geplant | Betrieb auf realer Hardware (Raspberry Pi + BME280) mit echter Telemetrie. |

---

### 🛰️ Datenfluss (Überblick)

1. **OBC (On-Board Computer)** auf dem Raspberry Pi erzeugt Telemetriedaten und schreibt sie lokal in CSV-Dateien.
2. **Ground Station (Mac)** empfängt diese Dateien regelmäßig (z. B. über `scp`, `MQTT` oder `HTTP`) und legt sie in `data/raw/obc/` ab.
3. Danach folgt die Verifizierung, Verarbeitung und Archivierung der Daten.

---

📘 *Dokument aktualisiert: Januar 2026*

---

📡 *Next Phase:* Live Communication & Data Link
