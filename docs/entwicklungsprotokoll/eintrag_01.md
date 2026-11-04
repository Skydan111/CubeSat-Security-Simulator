# Entwicklungsprotokoll #1 – Phase: Pre-Launch

**Datum:** 2025-11-03
**Phase:** Pre-Launch (Initial Setup)
**Lead:** Oleg Skydan

---

## 🎯 Missionsziel
Vorbereitung der technischen und dokumentarischen Grundlage
für das CubeSat Security Simulator Projekt.
Ziel dieser Phase war es, die Entwicklungsumgebung, Repository-Struktur
und Dokumentation aufzubauen, bevor mit der Sensorintegration begonnen wird.

---

## 🧩 Statusübersicht

| Bereich | Status | Beschreibung |
|----------|---------|---------------|
| Entwicklungsumgebung | ✅ | macOS mit Python 3.13, VS Code, Git eingerichtet |
| Repository-Struktur | ✅ | cube/, ground/, docs/ erstellt |
| Virtuelle Umgebung | ✅ | venv initialisiert und getestet |
| README | ✅ | erstellt, formatiert, GitHub-kompatibel ausgerichtet |
| Mission Reports | 🟢 | Basisdokument erstellt |
| Hardware | ⏳ | Raspberry Pi 4 + Sensor BME280 in Lieferung |

---

## ⚙️ Technische Grundlage
- **Programmiersprache:** Python 3
- **Versionierung:** Git / GitHub
- **Dokumentation:** Markdown, deutschsprachig
- **IDE:** Visual Studio Code
- **System:** macOS

---

## 🧠 Erkenntnisse dieser Phase
- GitHub-Rendering benötigt exaktes Schließen von Codeblöcken (```text … ```).
- Markdown-Tables und ASCII-Diagramme verhalten sich stabil, wenn korrekt eingerückt.
- Sauberes README ist entscheidend für die Projektpräsentation und spätere Skalierung.

---

## 🚀 Nächste Schritte (Woche 1)

1. **Raspberry Pi vorbereiten**
   - microSD mit Raspberry Pi OS (Lite) flashen
   - SSH aktivieren, Hostname `pi-cube` setzen
   - Verbindung zum WLAN konfigurieren

2. **Sensorintegration**
   - BME280 anschließen (I²C)
   - Erstes Testskript `bme_log.py` schreiben
   - Telemetriedaten (Temperatur, Luftfeuchtigkeit, Druck) lokal loggen

3. **Datenübertragung (optional vorbereiten)**
   - MQTT-Broker-Setup auf Bodenstation planen
   - Entwurf für `receiver.py` skizzieren

---

## 📓 Kommentar des Missionsleiters

> *„Der Pre-Launch war erfolgreich abgeschlossen.
>  Alle Systeme sind bereit, der CubeSat tritt in die Telemetrie-Vorbereitungsphase ein.“*
>  — **Oleg Skydan**, Missionsleiter

## 🧰 Hardware Arrival Log
**Mission Phase:** Ground System Deployment
**Date:** 2025-11-04
**Engineer:** O. Skydan

### 📦 Received Components

#### 🧠 Core System
| Component | Description | Status |
|------------|--------------|--------|
| **Raspberry Pi 4 Model B (4 GB RAM)** | Main on-board computer for telemetry simulation and secure data transmission | ✅ |
| **Power Supply (USB-C 15 W)** | Stable power source for Raspberry Pi | ✅ |
| **Micro HDMI Cable** | Video output connection for setup and diagnostics | ✅ |
| **MicroSD Card (64 GB, SanDisk Ultra)** | Primary storage and OS medium | ✅ |
| **Heatsinks × 3** | Passive cooling for CPU, RAM and LAN chip | ✅ |
| **Protective Case** | Physical housing for board protection | ✅ |

#### 🔬 Prototyping & Testing Kit
| Component | Description | Status |
|------------|--------------|--------|
| **Breadboards (830 & 400 points)** | Modular prototyping surfaces for sensor & telemetry circuits | ✅ |
| **Jumper Wires (≈ 126 pcs)** | Male-to-male and female-to-male connectors for quick wiring | ✅ |

### 🖼️ Visual Inspection
Photos confirm that all items are factory-sealed, undamaged and match expected configuration.
The breadboard kit provides full flexibility for rapid prototyping of the CubeSat Security Simulator telemetry module.

### 🪜 Next Steps
1. Assemble Raspberry Pi and attach heatsinks.
2. Flash OS image (Raspberry Pi OS Lite 64-bit) to microSD.
3. Configure SSH access and network connection.
4. Begin integration of sensor module (BME280) for telemetry testing.

> 🛰️ *“Every ground station starts with a single wire.”*

📁 *All visual inspection photos stored locally at* `docs/hardware/` *(not pushed to GitHub for repository optimization).*

### 🖼️ Visual Inspection

All components have been received in perfect condition.
Below are local reference images from the inspection phase (stored offline for repository optimization):

📦 [01_kit_overview.jpg — Kit Overview](hardware/01_kit_overview.jpg)

🔌 [02_breadboard_set.jpg — Breadboard Set](hardware/02_breadboard_set.jpg)

🧠 [03_raspberry_unboxing.jpg — Raspberry Pi Unboxing](hardware/03_raspberry_unboxing.jpg)
