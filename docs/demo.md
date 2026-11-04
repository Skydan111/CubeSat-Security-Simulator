# Quickstart & Demo

## Voraussetzungen

- **Python 3.11** (empfohlen via Homebrew auf macOS)
- **Docker** (für lokalen MQTT Broker)
- **Git**
- **macOS** oder **Linux**

Optional:
- Raspberry Pi 4B mit BME280 Sensor (für Hardware-Tests)

---

## Installation

### 1. Repository klonen

```bash
git clone https://github.com/Skydan111/warehouse-monitor.git
cd warehouse-monitor
```

### 2. Virtuelle Umgebung erstellen

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

**Hinweis:** Auf manchen Systemen heißt der Befehl `python3` statt `python3.11`.

### 3. Entwicklungsabhängigkeiten installieren

```bash
pip install -r requirements-dev.txt
```

**Installiert:**
- `pytest` (Testing Framework)
- `paho-mqtt` (MQTT Client für Tests)

### 4. Projekt-Packages installieren (editable mode)

```bash
pip install -e shared
pip install -e control_center
pip install -e zone_sensor
```

**Was passiert:**
- `shared` wird installiert (keine externen Dependencies)
- `control_center` wird installiert inkl. `pandas`, `matplotlib`, `paho-mqtt`, `pyyaml`
- `zone_sensor` wird installiert inkl. `paho-mqtt`, `adafruit-circuitpython-bme280`

### 5. Installation verifizieren

```bash
pytest --co -q
```

**Erwartetes Ergebnis:** Liste aller 52 Tests ohne Fehler.

---

## MQTT Broker starten

Das System nutzt Eclipse Mosquitto als MQTT Broker.

### Broker starten

```bash
docker compose -f docker-compose.mqtt.yml up -d
```

**Broker läuft auf:**
- Host: `localhost`
- Port: `1883`
- Kein TLS (Demo-Modus)

### Broker-Status prüfen

```bash
docker compose -f docker-compose.mqtt.yml ps
```

### Broker stoppen

```bash
docker compose -f docker-compose.mqtt.yml down
```

---

## Zonensensor starten

Der Zonensensor läuft auf dem Sensorrechner (Raspberry Pi), der Sensordaten erfasst, signiert und via MQTT publiziert.

### Start

```bash
./scripts/zone_sensor_start.sh
```

**Was passiert:**
1. BME280 Sensor wird gelesen (oder simuliert, falls kein Hardware-Sensor verfügbar)
2. Telemetriedaten werden formatiert: `ts,temp,hum,press,mode`
3. HMAC-SHA256 Signatur wird erzeugt
4. Daten werden als JSON Envelope via MQTT publiziert
   - Topic: `warehouse/v1/ZONE-01/telemetry`
   - QoS: 1

### Logs prüfen

```bash
tail -f logs/logger.log
```

**Beispiel-Log:**
```
2026-02-25 15:20:05 [INFO] BME280 Sensor initialized (simulation mode)
2026-02-25 15:20:05 [INFO] Published telemetry to warehouse/v1/ZONE-01/telemetry
```

### Status prüfen

```bash
./scripts/zone_sensor_status.sh
```

### Stoppen

```bash
./scripts/zone_sensor_stop.sh
```

---

## Leitstand starten

Der Leitstand empfängt MQTT-Nachrichten, verifiziert Signaturen und routet Daten basierend auf Validierungsergebnis.

### Start

```bash
./scripts/control_center_start.sh
```

**Was passiert:**
1. MQTT Topic wird subscribed: `warehouse/v1/ZONE-01/telemetry`
2. Empfangene Nachrichten werden validiert:
   - Envelope-Schema prüfen
   - Deduplication (msg_id)
   - Freshness Check (ts_utc)
   - HMAC-Signatur verifizieren
   - Adaptive Security (Lockout-Prüfung)
3. Routing:
   - Gültig → `data/processed/`
   - Ungültige Signatur → `data/rejected/`
   - Lockout → `data/quarantine/`

### Logs prüfen

```bash
tail -f logs/control_center_subscriber.log
```

**Beispiel-Log:**
```
2026-02-25 15:20:06 [INFO] Received message on warehouse/v1/ZONE-01/telemetry
2026-02-25 15:20:06 [INFO] HMAC verification: PASS
2026-02-25 15:20:06 [INFO] Routed to data/processed/telemetry_20260225.csv
```

### Security Audit Log

```bash
tail -f logs/security_audit.jsonl | jq
```

**Beispiel:**
```json
{
  "ts": "2026-02-25T15:20:06Z",
  "event": "signature_verified",
  "msg_id": "a1b2c3d4-...",
  "zone_id": "ZONE-01"
}
```

### Status prüfen

```bash
./scripts/control_center_status.sh
```

### Stoppen

```bash
./scripts/control_center_stop.sh
```

---

## Datenfluss verifizieren

### Processed Data anzeigen

```bash
ls -lh data/processed/
```

**Erwartete Dateien:**
```
telemetry_20260225.csv
```

### Letzte Telemetriedaten anzeigen

```bash
tail data/processed/telemetry_20260225.csv
```

**Beispiel-Ausgabe:**
```
ts,temperature_c,humidity_pct,pressure_hpa,mode,sig
2026-02-25T15:20:00Z,23.50,45.20,1013.25,sim,a1b2c3d4e5f6...
2026-02-25T15:20:10Z,23.52,45.18,1013.26,sim,f6e5d4c3b2a1...
```

### Rejected Data (ungültige Signaturen)

```bash
ls -lh data/rejected/
tail data/rejected/*.csv
```

### Quarantine Data (Lockout)

```bash
ls -lh data/quarantine/
tail data/quarantine/*.csv
```

---

## Tests ausführen

### Alle Tests

```bash
pytest
```

**Erwartetes Ergebnis:**
- 49 Tests erfolgreich
- 3 Tests übersprungen (MQTT Integration, erfordern Docker-Broker)

### Nur Unit-Tests

```bash
pytest tests/unit/
```

**Abdeckung:**
- Crypto (HMAC sign/verify)
- Protocol (CSV parsing)
- Security Manager (Lockout, Windowing)
- Zonensensor-Logger
- Sensor Simulation

### Nur Integration-Tests

```bash
pytest tests/integration/
```

**Abdeckung:**
- End-to-End Receiver Pipeline
- Zonensensor-Logger mit realer Config
- Security Attacks (Tampering)

### Nur Security-Tests

```bash
pytest tests/integration/security/
```

**Szenarien:**
- Manipulierte Payloads
- Replay-Angriffe
- Malformed Packets

### Verbose Output

```bash
pytest -v
```

### Mit Code Coverage

```bash
pip install pytest-cov
pytest --cov=shared --cov=control_center --cov=zone_sensor
```

---

## Demo-Szenarien

### Szenario 1: Normale Telemetrie (End-to-End)

**Ziel:** Verifizieren, dass gültige Telemetriedaten korrekt verarbeitet werden.

**Schritte:**

1. MQTT Broker starten
   ```bash
   docker compose -f docker-compose.mqtt.yml up -d
   ```

2. Leitstand starten
   ```bash
   ./scripts/control_center_start.sh
   ```

3. Zonensensor starten
   ```bash
   ./scripts/zone_sensor_start.sh
   ```

4. Warten (ca. 30 Sekunden)

5. Verarbeitung prüfen
   ```bash
   ls data/processed/
   tail data/processed/*.csv
   ```

**Erwartetes Ergebnis:**
- Dateien in `data/processed/`
- Gültige CSV-Zeilen mit korrekten Signaturen
- Keine Einträge in `data/rejected/` oder `data/quarantine/`

---

### Szenario 2: Manipulierte Daten (Bad Signature)

**Ziel:** Verifizieren, dass manipulierte Daten erkannt und rejected werden.

**Vorbereitung:**
- Beispieldatei mit ungültiger Signatur liegt in `examples/telemetry_bad_sig.csv`

**Schritte:**

1. Leitstand läuft (siehe Szenario 1)

2. Manipulierte Datei manuell verarbeiten
   ```bash
   python -m control_center.receiver --file examples/telemetry_bad_sig.csv
   ```

3. Ergebnis prüfen
   ```bash
   tail data/rejected/*.csv
   tail logs/security_audit.jsonl
   ```

**Erwartetes Ergebnis:**
- Zeile landet in `data/rejected/`
- Security Audit Log enthält `invalid_signature` Event
- Leitstand-Log: `[WARNING] Invalid signature detected`

---

### Szenario 3: Lockout-Test (Adaptive Security)

**Ziel:** Verifizieren, dass wiederholte ungültige Nachrichten Lockout auslösen.

**Schritte:**

1. Leitstand läuft

2. 5 ungültige Nachrichten nacheinander senden (simuliert)
   ```bash
   for i in {1..5}; do
     python -m control_center.receiver --file examples/telemetry_bad_sig.csv
     sleep 2
   done
   ```

3. Security-Status prüfen
   ```bash
   tail logs/security_audit.jsonl | jq '.event' | grep lockout
   ```

4. Weitere (gültige) Nachricht senden
   ```bash
   python -m control_center.receiver --file examples/telemetry_good.csv
   ```

5. Routing prüfen
   ```bash
   ls data/quarantine/
   ```

**Erwartetes Ergebnis:**
- Nach 5 ungültigen Nachrichten: Lockout aktiviert
- Audit Log: `lockout_triggered` Event
- Nachfolgende Nachricht (auch wenn gültig) landet in `data/quarantine/`

---

### Szenario 4: MQTT Replay-Angriff

**Ziel:** Verifizieren, dass Duplicate msg_id erkannt wird.

**Voraussetzung:** Docker-Broker läuft, MQTT-Tests aktiviert

**Schritte:**

```bash
pytest tests/integration/security/test_mqtt_replay.py -v
```

**Test-Logik:**
1. Gültige Nachricht wird via MQTT gesendet
2. Identische Nachricht (gleiche msg_id) wird erneut gesendet
3. Leitstand erkennt Duplikat und verwirft es

**Erwartetes Ergebnis:**
- Test: PASS
- Erste Nachricht: `data/processed/`
- Zweite Nachricht: Gedropped (Audit-Log: `duplicate` Event)

---

## Troubleshooting

### Problem: "ModuleNotFoundError: No module named 'shared'"

**Ursache:** Editable Install fehlt.

**Lösung:**
```bash
pip install -e shared
pip install -e control_center
pip install -e zone_sensor
```

---

### Problem: "Docker daemon not running"

**Ursache:** Docker ist nicht gestartet.

**Lösung:**
- macOS: Docker Desktop starten
- Linux: `sudo systemctl start docker`

---

### Problem: "MQTT connection failed"

**Ursache:** Broker läuft nicht oder falscher Port.

**Prüfen:**
```bash
docker compose -f docker-compose.mqtt.yml ps
```

**Broker neu starten:**
```bash
docker compose -f docker-compose.mqtt.yml down
docker compose -f docker-compose.mqtt.yml up -d
```

---

### Problem: "All tests failed"

**Ursache:** Wahrscheinlich fehlende Dependencies oder falsche Python-Version.

**Prüfen:**
```bash
python --version  # Sollte 3.11.x sein
pip list | grep warehouse
```

**Neu installieren:**
```bash
pip install -r requirements-dev.txt
pip install -e shared -e control_center -e zone_sensor
```

---

### Problem: "Permission denied" bei Skripten

**Ursache:** Skripte sind nicht ausführbar.

**Lösung:**
```bash
chmod +x scripts/*.sh
```

---

## Nächste Schritte

Nach erfolgreicher Demo:

1. **Logs analysieren**
   - `logs/logger.log` — Telemetrie-Erzeugung
   - `logs/control_center_subscriber.log` — Verarbeitung
   - `logs/security_audit.jsonl` — Security-Events

2. **Konfiguration anpassen**
   - `configs/security_policy.yaml` — Lockout-Schwellwerte
   - `configs/zone_sensor.yaml` — Telemetrie-Intervall
   - `configs/control_center.json` — MQTT-Verbindung

3. **Hardware-Tests**
   - Raspberry Pi mit BME280 Sensor aufsetzen
   - `zone_sensor/` Code auf Pi deployen
   - Echte Sensorwerte über MQTT senden

4. **Visualisierung**
   - `control_center/src/control_center/plot_csv.py` — Telemetrie plotten
   - Grafana-Integration (geplant)

5. **Weiterführende Docs**
   - [Architektur](architecture.md) — Systemdesign im Detail
   - [Security](security.md) — Bedrohungsmodell & Kontrollen
   - [MQTT Interface](mqtt-interface.md) — Protokoll-Spezifikation

---

*Letzte Aktualisierung: Februar 2026*
