# 🛰️ CubeSat Security Simulator

> **Mission Phase:** 🛰️ System Integration
> **Status:** 🧩 Hardware Deployment in Progress
> **Last Update:** 2025-11-05

## 📘 Inhaltsverzeichnis
- [🚀 Missionsübersicht](#-missionsübersicht)
- [🌌 Motivation & Vision](#-motivation--vision)
- [🎯 Missionsziele](#-missionsziele)
- [🧩 Systemarchitektur](#-systemarchitektur)
- [🔐 Sicherheitsebene](#-sicherheitsebene)
- [🧠 Technologien](#-technologien)
- [📦 Projektstruktur](#-projektstruktur)
- [⚙️ Installation](#️-installation)
- [👨‍🚀 Autor](#-autor)
- [🗓️ Mission Timeline](#️-mission-timeline)
- [🧭 Mission Log](#-mission-log)
- [📂 Datenstruktur (Bodenstation)](#-datenstruktur-bodenstation)


## 🚀 Missionsübersicht
**CubeSat Security Simulator** ist eine Lern- und Forschungsplattform, die die Architektur eines Mini-Satelliten (CubeSat) mit Fokus auf **Telemetrie und Cybersicherheit** simuliert.
Das Projekt zeigt, wie Sensordaten sicher gesammelt, signiert, übertragen und auf der Bodenstation überprüft werden können.

---

## 🌌 Motivation & Vision
Die Idee zu diesem Projekt entstand aus dem Wunsch, praxisnah zu verstehen, wie sich Cybersicherheit, eingebettete Systeme und Raumfahrttechnologien verbinden lassen.
In einer Zeit, in der Mini-Satelliten (CubeSats) und vernetzte IoT-Systeme immer häufiger eingesetzt werden, ist der Schutz der Datenkommunikation ein entscheidender Faktor für die Zuverlässigkeit und Sicherheit moderner Technologie.

Ziel dieses Projekts ist es, nicht nur einen funktionierenden Prototyp zu entwickeln, sondern eine Lernplattform zu schaffen, die die Prinzipien sicherer Kommunikation im Weltraum greifbar macht.
Der **CubeSat Security Simulator** soll zeigen, dass man auch mit einfachen, frei verfügbaren Komponenten ein komplexes, realistisches System modellieren und die Grundlagen von Kryptographie, Datenübertragung und Systemsicherheit verstehen kann.

Langfristig sehe ich dieses Projekt als Basis für weitere Forschung oder Ausbildung im Bereich **IoT- und Space-Security**.
Es soll Studierenden, Entwicklern und Ingenieuren als Inspiration dienen, wie man aus einer Idee ein technisch sauberes, sicherheitsorientiertes System mit realem Nutzen aufbauen kann.

---

## 🎯 Missionsziele
- Aufbau eines CubeSat-Telemetriesystems mit einem **Raspberry Pi 4**
- Implementierung einer **HMAC-SHA256-Signatur** zum Schutz der Daten
- Aufbau einer Kommunikationsverbindung zwischen Bordcomputer und Bodenstation
- Visualisierung von Telemetriedaten (Temperatur, Luftfeuchtigkeit, Druck) und Sicherheitsereignissen

---

## 🧩 Systemarchitektur

```text
+-----------------------+             +-----------------------+
|   On-Board Computer   |             |     Bodenstation      |
|    (Raspberry Pi 4)   |             |    (Laptop / Server)  |
|-----------------------|             |-----------------------|
| BME280 Sensor (I²C)   |── Telemetrie → MQTT / HTTP Receiver |
| Datenlogger (CSV)     |             | Signatur-Verifikation |
| HMAC-Signierung       |← Befehle ───│ Visualisierung / Logs |
+-----------------------+             +-----------------------+
```
---

## 🔐 Sicherheits­ebene
- Jedes Telemetriepaket wird mit **HMAC-SHA256** und einem geheimen Schlüssel signiert.
- Die Empfängerseite überprüft die Signatur und verwirft manipulierte oder wiederholte Pakete.
- Alle Ereignisse werden in **security.log** protokolliert.

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
├── cube/                      # Hauptprojekt: Code und Dokumentation
│   ├── obc/                   # On-Board Computer (Raspberry Pi)
│   │   ├── bme_log.py         # Erfassung der Sensordaten (BME280)
│   │   ├── hmac_sign.py       # HMAC-Signierung der Telemetrie
│   │   └── config.json        # Gerätekonfiguration (Keys, Sensor-ID, etc.)
│   │
│   ├── ground/                # Bodenstation (Laptop / Server)
│   │   ├── receiver.py        # Empfang von Telemetriedaten
│   │   ├── verify.py          # Signaturprüfung der Datensätze
│   │   └── plot.py            # Visualisierung & Diagramme
│   │
│   └── docs/                  # Missionsdokumentation & Architektur
│       ├── architecture.png
│       ├── mission_report_1.md
│       ├── mission_report_2.md
│       └── hardware/          # lokale Fotos, nicht versioniert (.gitignore)
│
├── data/                      # Missionsdaten (nicht versioniert)
│   ├── raw/                   # unbearbeitete Daten direkt vom OBC
│   ├── processed/             # validierte & bereinigte Datensätze
│   ├── reports/               # Berichte, Diagramme, Auswertungen
│   ├── archive/               # ältere archivierte Datensätze (ZIP)
│   └── rejected/              # ungültige Datensätze (Signaturfehler)
│
├── venv/                      # Virtuelle Python-Umgebung
├── .gitignore
├── README.md
└── requirements.txt
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

## 🗓️ Mission Timeline

| Phase | Status | Description |
|--------|---------|-------------|
| 🧭 **Pre-Launch Setup** | ✅ Completed | Repository initialized, Python environment created, project structure defined. |
| 🛰️ **System Architecture Build** | ✅ Completed | OBC and Ground Station modules implemented, telemetry flow verified. |
| 📊 **Telemetry Visualization** | ✅ Completed | CSV data logging and real-time plotting functional. |
| 🔐 **Security Layer Integration** | 🚧 In Progress | Implementing HMAC-SHA256 data signing and verification. |
| 🌐 **Live Data Link (Raspberry → Ground)** | ⏳ Planned | Establish real MQTT/HTTP communication channel. |
| 🚀 **Mission Control Dashboard** | ⏳ Planned | Streamlit interface for monitoring telemetry and events. |

---

## 🧭 Mission Log

| Date       | Phase / Update | Summary |
|-------------|----------------|----------|
| **2025-11-03** | 🛰️ *Pre-Launch Complete* | Initial repository structure established. On-Board Computer (OBC) and Ground Station modules implemented. Basic telemetry simulation and real-time plotting verified. |
| **2025-11-03** | 🧩 *Mission Documentation* | README structured with system architecture, technology stack, and installation guide. Mission Log initialized for ongoing development tracking. |

---

## 📂 Datenstruktur (Bodenstation)

Alle Telemetriedaten, die vom Bordcomputer (Raspberry Pi / OBC) empfangen werden, werden im Verzeichnis **`data/`** gespeichert und verarbeitet.
Diese Struktur dient der klaren Organisation, Validierung und Archivierung der Missionsdaten.
```text
data/
├─ raw/obc/YYYY/YYYY-MM/telemetry_YYYY-MM-DD[_HH]_obc.csv   # Rohdaten direkt vom Bordcomputer
├─ processed/                                                # geprüfte und bereinigte Daten
├─ reports/                                                  # Berichte, Diagramme, Auswertungen
├─ archive/                                                  # ältere archivierte Daten (z. B. ZIP)
└─ rejected/                                                 # verworfene Datensätze (ungültige Signatur)
```
---

### 🧩 Format der Telemetrie-Dateien (CSV)

Jede Zeile repräsentiert eine einzelne Messung der Sensoren.
Die Datei enthält immer eine Kopfzeile mit folgenden Spalten:

ts,temperature_c,humidity_pct,pressure_hpa,mode,sig

**Spaltenbeschreibung:**

| Feld | Typ | Beschreibung |
|------|------|--------------|
| `ts` | Datum/Zeit (UTC) | Zeitstempel im ISO 8601-Format, z. B. `2025-11-05T14:15:00Z` |
| `temperature_c` | Float | Temperatur in °C |
| `humidity_pct` | Float | Luftfeuchtigkeit in % |
| `pressure_hpa` | Float | Luftdruck in hPa |
| `mode` | String | Modus: `sim` (Simulation) oder `real` (Realdaten) |
| `sig` | String | HMAC-Signatur des Datensatzes (hexadezimal) |

---

### 🗂️ Benennung der Dateien
```text
telemetry_YYYY-MM-DD_obc.csv        # Tageslog
telemetry_YYYY-MM-DDTHH_obc.csv     # Stundenlog bei hohem Datenvolumen
```
**Beispiele:**
```text
telemetry_2025-11-05_obc.csv
telemetry_2025-11-05T14_obc.csv
```
🕒 Alle Zeitstempel und Dateinamen verwenden **UTC-Zeit**, um Verwechslungen mit Zeitzonen zu vermeiden.

---

### 🔄 Datenfluss und Speicherung

- Neue Dateien werden in `data/raw/obc/...` gespeichert
- Nach erfolgreicher Signaturprüfung werden sie nach `data/processed/` verschoben
- Ungültige Dateien kommen nach `data/rejected/`
- Alte Datensätze werden regelmäßig nach `data/archive/` archiviert
- Auswertungen und Diagramme liegen in `data/reports/`

---

### 🚫 Git-Ignore-Regeln

Um das Repository sauber zu halten, werden reale Daten nicht versioniert.
In `.gitignore` sind folgende Regeln eingetragen:
```text
data/raw/
data/processed/
data/archive/
data/rejected/
*.zip
*.7z
```
In jeder Unterordner befindet sich eine `.gitkeep`-Datei, damit die Struktur im Repository erhalten bleibt.

---

### 🛰️ Datenfluss (Überblick)

1. **OBC (On-Board Computer)** auf dem Raspberry Pi erzeugt Telemetriedaten und schreibt sie lokal in CSV-Dateien.
2. **Ground Station (Mac)** empfängt diese Dateien regelmäßig (z. B. über `scp`, `MQTT` oder `HTTP`) und legt sie in `data/raw/obc/` ab.
3. Danach folgt die Verifizierung, Verarbeitung und Archivierung der Daten.

---

📘 *Dokument aktualisiert: November 2025 — Version 1.0 Datenstruktur-Spezifikation*

---

📡 *Next Phase:* Integration of live BME280 sensor data and secure HMAC transmission from Raspberry Pi → Ground Station.
