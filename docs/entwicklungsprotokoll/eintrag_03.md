# Entwicklungsprotokoll #3 – Phase: Control Center Telemetry Visualization

**Datum:** 2025-11-06
**Phase:** Control Center Development
**Lead:** Oleg Skydan

---

## 🎯 Ziel der Phase
Entwicklung und Test eines Telemetrie-Visualisierungsmoduls im Leitstand.
Das Ziel dieser Phase war es, eingehende Sensordaten aus der Sensor-Simulation (Raspberry Pi / Sensorrechner)
in Echtzeit anzuzeigen und zu analysieren.

---

## 🧩 Statusübersicht

| Bereich | Status | Beschreibung |
|----------|---------|--------------|
| Datenquelle | ✅ | CSV-Format für Telemetrie erfolgreich definiert |
| Datenimport | ✅ | Funktion `load_df()` liest und sortiert Telemetrie korrekt |
| Visualisierung | ✅ | Matplotlib-basierte Diagramme für Temperatur, Feuchtigkeit, Druck |
| Live-Modus | ✅ | Echtzeit-Update alle 2 Sekunden mit Fenster von 300 Messpunkten |
| CLI-Steuerung | ✅ | Parameter `--once`, `--interval`, `--window` implementiert |
| Fehlermanagement | ✅ | Saubere Abbrüche und Fehlermeldungen bei leeren Dateien |

---

## 📊 Technische Beschreibung

### Modul: `ground/plot.py`

Das Visualisierungsmodul stellt eine grafische Live-Ansicht der Telemetriedaten bereit.

#### 🔍 Hauptfunktionen

| Funktion | Beschreibung |
|-----------|---------------|
| `load_df()` | Liest `cube/data/telemetry.csv`, wandelt Zeitstempel um und sortiert nach Zeit |
| `draw_once()` | Zeichnet eine statische Ansicht mit drei Diagrammen (Temperatur, Feuchtigkeit, Druck) |
| `live_loop()` | Aktualisiert die Diagramme periodisch, um Echtzeit-Telemetrie anzuzeigen |
| `main()` | CLI-Schnittstelle: steuert Moduswahl (`--once` / Live) und Parameter |

#### ⚙️ Visualisierte Variablen
- Temperatur (°C)
- Luftfeuchtigkeit (%)
- Luftdruck (hPa)

#### 📈 Diagrammstruktur
Jedes Diagramm wird separat in einer gemeinsamen Zeitachse (UTC) dargestellt.
Aktualisierung erfolgt in konfigurierbaren Intervallen (Standard: 2 Sekunden).

#### 🧠 Fehlerbehandlung
- Keine Datei → `[ERR] Telemetrie-Datei nicht gefunden`
- Leere Datei → `[ERR] Telemetrie-Datei ist leer. Bitte OBC-Logger zuerst starten.`
- Manueller Abbruch → `[GROUND] Live-Ansicht vom Benutzer gestoppt.`

---

## 🧠 Erkenntnisse dieser Phase
- Die Nutzung von **pandas** und **matplotlib** ist für Echtzeit-Darstellungen äußerst effizient.
- Durch den **Live-Modus** entsteht ein realistisches Gefühl eines laufenden Messbetriebs.
- Die klare CLI-Struktur erleichtert die Integration in automatisierte Skripte (z. B. `receiver.py`).
- Diese Visualisierung dient als Basis für das zukünftige **Leitstand-Dashboard (Streamlit)**.

---

## 🚀 Nächste Schritte (Phase #4 – Integration des Sensorrechners)

1. Implementierung des Moduls `bme_log.py` auf dem Raspberry Pi (On-Board Computer).
2. Erfassen echter Sensordaten über den BME280-Sensor (I²C).
3. HMAC-Signierung und Übertragung an den Leitstand.
4. Erweiterung der Visualisierung um Sicherheitsereignisse und Statusmeldungen.

---

> 💬 *„Ein System ist erst dann echt, wenn die Daten auf dem Bildschirm lebendig werden.“*
> — Oleg Skydan, Projektleiter
