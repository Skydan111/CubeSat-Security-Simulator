# 🛰️ CubeSat Security Simulator

> **Mission Phase:** 🟢 Pre-Launch
> **Status:** Initial Setup
> **Last Update:** 2025-11-03

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
+-----------------------+               +-----------------------+
|   On-Board Computer   |               |    Bodenstation       |
|  (Raspberry Pi 4)     |               |   (Laptop / Server)   |
|-----------------------|               |-----------------------|
| BME280 Sensor (I²C)   |── Telemetrie →│ MQTT / HTTP Receiver  |
| Datenlogger (CSV)     |               | Signatur-Verifikation  |
| HMAC-Signierung       |← Befehle ──   │ Visualisierung / Logs |
+-----------------------+               +-----------------------+
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
cube/
├── obc/                # Bordcomputer
│   ├── bme_log.py      # Erfassung der Telemetrie
│   ├── hmac_sign.py    # Daten-Signierung
│   └── config.json
├── ground/             # Bodenstation
│   ├── receiver.py
│   ├── verify.py
│   └── plot.py
├── docs/               # Dokumentation & Schaubilder
│   ├── architecture.png
│   └── mission_report.md
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

---

## 👨‍🚀 Autor
**Oleg Skydan**
Student · Wirtschaftsinformatik · Fachschule Wiesau
Interessen: Space Tech · Cybersecurity · IoT-Systeme

💡 *„Jede große Mission beginnt klein – manchmal auf einem Breadboard.“*
