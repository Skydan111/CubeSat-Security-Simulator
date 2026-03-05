# Systemarchitektur

## Überblick

Das CubeSat-Telemetriesystem ist eine End-to-End-Pipeline zur sicheren Übertragung von Sensordaten vom Satelliten (Raspberry Pi) zur Bodenstation (Ground).

Die Architektur folgt einem dreischichtigen Modell:
- **Satellite** — Sensordatenerfassung und kryptographische Signierung
- **Transport Layer** — MQTT-basierte Nachrichtenübertragung mit Envelope-Protokoll
- **Ground Station** — Empfang, Verifikation und Routing

Zentrale Designprinzipien:
- Klare Modultrennung (keine Vermischung von Verantwortlichkeiten)
- `shared/` als Single Source of Truth für Protokoll und Kryptographie
- Vollständige Testbarkeit auf allen Ebenen
- Keine impliziten PYTHONPATH-Abhängigkeiten (editable installs)

---

## Komponentendiagramm

```
┌─────────────────────────────────────┐
│      Satellite (Raspberry Pi)       │
├─────────────────────────────────────┤
│  BME280 Sensor / Simulation         │
│           ↓                         │
│  Telemetry Logger                   │
│  • Format: TelemetryUnsigned        │
│  • CSV: ts,temp,hum,press,mode      │
│           ↓                         │
│  HMAC-SHA256 Signing                │
│  • Secret: Shared Key (hex)         │
│  • Output: 64 hex chars             │
│           ↓                         │
│  MQTT Publisher                     │
│  • Envelope V1 (JSON)               │
│  • Payload: Base64(Signed CSV)      │
└─────────────────────────────────────┘
           ↓
    MQTT Broker (Mosquitto)
    Topic: cubesat/v1/SAT-001/telemetry
    QoS: 1
           ↓
┌─────────────────────────────────────┐
│       Ground Station (macOS)        │
├─────────────────────────────────────┤
│  MQTT Subscriber                    │
│           ↓                         │
│  Envelope Validation                │
│  • JSON Schema (V1)                 │
│  • Required fields check            │
│           ↓                         │
│  Deduplication                      │
│  • msg_id cache (LRU)               │
│  • Duplicate → Drop + Log           │
│           ↓                         │
│  Freshness Check                    │
│  • ts_utc ± MAX_SKEW                │
│  • Too old/future → Drop            │
│           ↓                         │
│  HMAC Verification                  │
│  • Decode Base64 payload            │
│  • Verify signature                 │
│           ↓                         │
│  Adaptive Security Check            │
│  • Lockout detection                │
│  • Quarantine if locked             │
│           ↓                         │
│  Routing Pipeline                   │
│  ├─ data/processed/   (valid)       │
│  ├─ data/rejected/    (bad sig)     │
│  └─ data/quarantine/  (lockout)     │
└─────────────────────────────────────┘
```

---

## Modulstruktur

### `shared/` — Protokoll & Kryptographie

Source of Truth für alle protokollrelevanten Definitionen.

```
shared/src/shared/
├── crypto/
│   └── hmac_sha256.py       # HMAC-SHA256 sign/verify
├── protocol/
│   ├── telemetry_csv.py     # TelemetryUnsigned format
│   └── signed_csv.py        # Signed payload operations
└── comm/
    ├── envelope.py          # MQTT Envelope V1 schema
    └── topics.py            # Topic naming schema
```

**Verantwortlichkeiten:**
- Definition von Datenformaten (Telemetrie, Signed Payload)
- Kryptographische Operationen (Sign/Verify)
- Envelope-Schema für MQTT-Transport
- Kein I/O, keine Seiteneffekte (rein funktional)

---

### `satellite/` — Telemetrieerzeugung

On-Board Computer Logik (Raspberry Pi).

```
satellite/src/satellite/
├── sensors/
│   └── bme280.py            # BME280 Reader + Simulation
├── logger.py                # CSV Logger mit HMAC-Signing
└── mqtt_publisher_from_file.py        # MQTT Publishing
```

**Verantwortlichkeiten:**
- Sensordaten lesen (BME280 oder Simulation)
- Telemetrie formatieren (`shared.protocol.telemetry_csv`)
- HMAC-Signatur erzeugen (`shared.crypto.hmac_sha256`)
- Envelope erstellen und via MQTT publizieren

**Abhängigkeiten:**
- `cubesat-shared` (protokoll + crypto)
- `paho-mqtt` (MQTT Client)
- `adafruit-circuitpython-bme280` (BME280 Sensor)

---

### `ground/` — Empfang & Verifikation

Bodenstation (macOS / Linux).

```
ground/src/ground/
├── mqtt_subscriber.py       # MQTT Subscription
├── receiver.py              # Ingestion & Routing Pipeline
├── verify.py                # HMAC Verification
└── security/
    └── security_manager.py  # Adaptive Security (Lockout)
```

**Verantwortlichkeiten:**
- MQTT Nachrichten empfangen und Envelope validieren
- Deduplication (msg_id Cache)
- Freshness-Prüfung (ts_utc)
- HMAC-Signatur verifizieren
- Adaptive Security (Lockout bei Anomalien)
- Routing: processed / rejected / quarantine

**Abhängigkeiten:**
- `cubesat-shared` (protokoll + crypto)
- `paho-mqtt` (MQTT Client)
- `pandas` (optional, für Analyse)
- `matplotlib` (optional, für Visualisierung)
- `pyyaml` (Config-Parsing)

---

## MQTT Transport Envelope (V1)

Der MQTT-Layer nutzt ein JSON-Envelope, um Metadaten (Transport-Layer) vom eigentlichen Payload (Application-Layer) zu trennen.

### Envelope Schema

```json
{
  "v": "1",
  "sat_id": "SAT-001",
  "msg_type": "telemetry",
  "msg_id": "b7d3b4fb-1f7a-4c4a-9b22-2d1c6f2a9e8a",
  "ts_utc": "2026-02-25T15:20:00Z",
  "qos": 1,
  "payload_b64": "BASE64_ENCODED_SIGNED_CSV"
}
```

**Felder:**
- `v` (string) — Envelope-Version, muss "1" sein
- `sat_id` (string) — Satellite ID (z.B. "SAT-001")
- `msg_type` (string) — Nachrichtentyp ("telemetry")
- `msg_id` (string) — Eindeutige Message-ID (UUID v4)
- `ts_utc` (string) — UTC Timestamp (ISO-8601)
- `qos` (number) — MQTT QoS-Level (0/1/2)
- `payload_b64` (string) — Base64-kodiertes Signed Payload

### Signed Payload (innerhalb payload_b64)

Nach Base64-Dekodierung:
```
ts,temperature_c,humidity_pct,pressure_hpa,mode,sig
2026-02-25T15:20:00Z,23.50,45.20,1013.25,sim,a1b2c3d4...
```

Signatur (`sig`) ist HMAC-SHA256 über die ersten 5 Felder.

---

## Datenfluss

### Satellite → Ground (Normale Telemetrie)

1. **Sensor lesen**
   - BME280 oder Simulation
   - Rückgabe: `TelemetryUnsigned(ts, temp, hum, press, mode)`

2. **Payload formatieren**
   - `format_payload()` → CSV ohne Signatur

3. **HMAC-Signatur erzeugen**
   - `sign(secret, payload)` → 64 Hex-Zeichen

4. **Signed CSV erstellen**
   - `format_signed_line()` → vollständige CSV-Zeile

5. **Envelope erstellen**
   - Base64-Encoding des Signed Payload
   - JSON Envelope mit Metadaten (msg_id, ts_utc, etc.)

6. **MQTT Publish**
   - Topic: `cubesat/v1/{sat_id}/telemetry`
   - QoS: 1
   - Payload: JSON Envelope

---

### Ground: Empfang & Verifikation

1. **MQTT Subscribe**
   - Empfang der JSON-Nachricht

2. **Envelope Validation**
   - JSON-Schema prüfen
   - Pflichtfelder vorhanden?
   - Version == "1"?

3. **Deduplication**
   - `msg_id` bereits im Cache?
   - Ja → Drop + Audit-Log
   - Nein → Weiter

4. **Freshness Check**
   - `ts_utc` innerhalb ± MAX_SKEW_SECONDS?
   - Nein → Drop + Log
   - Ja → Weiter

5. **Payload dekodieren**
   - Base64-Dekodierung von `payload_b64`

6. **HMAC Verification**
   - Signatur verifizieren
   - Ungültig → rejected/
   - Gültig → Weiter

7. **Adaptive Security Check**
   - Lockout aktiv?
   - Ja → quarantine/
   - Nein → processed/

---

## Architekturprinzipien

### 1. Klare Verantwortlichkeiten

Keine Vermischung von:
- Protokolldefinition (shared/)
- Telemetrieerzeugung (satellite/)
- Verifikation und Routing (ground/)

Änderungen am Protokoll erfolgen **ausschließlich** in `shared/`.

### 2. Single Source of Truth

`shared/` definiert:
- Telemetrie-Format
- Signatur-Verfahren
- Envelope-Schema
- Topic-Naming

Satellite und Ground importieren aus `shared/`, definieren aber nichts selbst.

### 3. Testbarkeit

Alle Module sind unit-testbar:
- `shared/` — keine I/O, rein funktional
- `satellite/` — Sensor-Simulation verfügbar
- `ground/` — Verification isoliert testbar

Integrationstests prüfen End-to-End-Fluss.

### 4. Editable Installs (kein PYTHONPATH)

Entwicklung nutzt:
```bash
pip install -e shared
pip install -e ground
pip install -e satellite
```

Keine manuellen PYTHONPATH-Manipulationen nötig.

### 5. Konfigurierbarkeit

Sicherheitsparameter in `configs/security_policy.yaml`:
- Lockout-Schwellwerte
- Fehlergewichte
- Zeitfenster

Keine Hardcoding von Policies im Code.

---

## Technology Stack

| Komponente | Technologie |
|------------|-------------|
| Programmiersprache | Python 3.11 |
| MQTT Broker | Eclipse Mosquitto 2 |
| MQTT Client | paho-mqtt 1.6.1 |
| Kryptographie | HMAC-SHA256 (hashlib) |
| Sensor | BME280 (adafruit-circuitpython-bme280) |
| Testing | pytest 9.0.2 |
| Config | YAML (pyyaml 6.0.1) |
| Hardware | Raspberry Pi 4B (4GB) |

---

## Deployment-Szenarien

### Lokales Setup (Demo)

- Satellite: Python-Skript auf Raspberry Pi
- MQTT Broker: Docker auf macOS
- Ground: Python-Skript auf macOS

### Produktionsnahes Setup (geplant)

- Satellite: Systemd-Service auf Raspberry Pi
- MQTT Broker: Cloud (z.B. AWS IoT Core)
- Ground: Server mit TLS/mTLS
- Secret Management: Vault / KMS

---

## Erweiterbarkeit

### Geplante Erweiterungen

- **Command Downlink** — Ground → Satellite Befehle
- **TLS/mTLS** — Verschlüsselte MQTT-Verbindung
- **Multi-Satellite** — Mehrere Satelliten parallel
- **Time-Series DB** — InfluxDB für Langzeitarchivierung
- **Dashboarding** — Grafana für Echtzeit-Monitoring

### Constraints

Änderungen an folgenden Komponenten erfordern Breaking Changes:
- Envelope Schema (V1 → V2)
- Signed Payload Format
- HMAC-Schlüssel (nicht rotierbar ohne Neustart)

---

*Letzte Aktualisierung: Februar 2026*
