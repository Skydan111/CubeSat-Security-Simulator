# 🛰️ Mission Report #1 – Phase: Pre-Launch

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
