# CubeSat Secure Telemetry Simulator

End-to-end abgesicherte Telemetrie-Pipeline von einem simulierten CubeSat-Satelliten (Raspberry Pi) zur Bodenstation mit HMAC-SHA256 Integritätsschutz, Anti-Replay-Mechanismen und adaptiver Sicherheit.

---

## Was dieses Projekt demonstriert

- **End-to-End Systemdesign** — Vollständige Datenkette von Sensordatenerfassung bis zur verifizierten Speicherung
- **HMAC-SHA256 Integritätsschutz** — Kryptographische Absicherung gegen Payload-Manipulation
- **Deduplication** — Erkennung und Verwerfung doppelter Nachrichten (msg_id Cache)
- **Freshness / Anti-Replay** — Zeitbasierte Verifikation zur Verhinderung von Replay-Angriffen
- **Routing-Pipeline** — Automatische Klassifikation in processed / rejected / quarantine
- **Adaptive Security** — Lockout-Mechanismus bei wiederholten Sicherheitsverletzungen
- **Testabdeckung** — 52 Tests (Unit, Integration, Security) mit vollständiger CI-Fähigkeit
- **Betrieb auf Raspberry Pi** — Lauffähig auf echter Hardware mit BME280-Sensor

---

## Systemarchitektur

```
┌─────────────────────────────────────┐
│   Satellite (Raspberry Pi / Sim)    │
├─────────────────────────────────────┤
│  BME280 Sensor / Simulation         │
│           ↓                         │
│  Telemetry Format                   │
│  ts,temp,hum,press,mode             │
│           ↓                         │
│  HMAC-SHA256 Signing                │
│  (Shared Secret)                    │
│           ↓                         │
│  MQTT Publisher                     │
│  Envelope V1 (JSON + Base64)        │
└─────────────────────────────────────┘
           ↓
    ┌─────────────┐
    │ MQTT Broker │  Topic: cubesat/v1/{sat_id}/telemetry
    │ (Mosquitto) │  QoS: 1
    └─────────────┘
           ↓
┌─────────────────────────────────────┐
│      Ground Station (macOS)         │
├─────────────────────────────────────┤
│  MQTT Subscriber                    │
│           ↓                         │
│  Envelope Validation                │
│  (Schema, Required Fields)          │
│           ↓                         │
│  Deduplication                      │
│  (msg_id LRU Cache)                 │
│           ↓                         │
│  Freshness Check                    │
│  (ts_utc ± MAX_SKEW)                │
│           ↓                         │
│  HMAC Verification                  │
│  (Constant-Time Compare)            │
│           ↓                         │
│  Decision & Routing                 │
│  • Lockout-Check                    │
│  • Security Event Logging           │
│           ↓                         │
│  Storage                            │
│  ├─ data/processed/    (valid)      │
│  ├─ data/rejected/     (bad sig)    │
│  └─ data/quarantine/   (lockout)    │
└─────────────────────────────────────┘
```

**Verarbeitungs-Pipeline:**
```
Envelope → Dedup → Freshness → Verify → Decision → Routing
                                  ↓         ↓
                              rejected  lockout?
                                          ↓
                                    quarantine
```

**Modulstruktur:**
- `shared/` — Protokolldefinition und Kryptographie (Single Source of Truth)
- `satellite/` — Telemetrieerzeugung und MQTT Publishing
- `ground/` — Empfang, Verifikation und Routing

---

## Sicherheitsmodell

### Bedrohungen und Kontrollen

| Bedrohung | Kontrolle | Implementierung |
|-----------|-----------|-----------------|
| **Payload-Manipulation** | HMAC-SHA256 | Signatur über kanonischen Payload, Constant-Time Verify |
| **Replay-Angriffe** | Freshness + Sliding Window | ts_utc ± MAX_SKEW, msg_id Dedup-Cache (LRU) |
| **Duplicate Messages** | Deduplication | UUID v4 msg_id, Cache der letzten N Nachrichten |
| **Wiederholte ungültige Versuche** | Adaptive Security (Lockout) | Gewichtete Fehlerzählung, Schwellwert-basierter Lockout |

### HMAC-SHA256 Details

- **Algorithmus:** HMAC-SHA256 (RFC 2104)
- **Schlüssel:** Symmetrischer Shared Secret (hexadezimal)
- **Signatur-Scope:** `ts,temperature_c,humidity_pct,pressure_hpa,mode`
- **Ausgabe:** 64 Hex-Zeichen
- **Verifikation:** `hmac.compare_digest()` (Constant-Time, Timing-Attack-resistent)

### Anti-Replay Mechanismen

**1. Freshness Check (Transport-Layer)**
- Envelope-Timestamp `ts_utc` wird gegen Systemzeit geprüft
- Erlaubter Skew: ± 120 Sekunden (konfigurierbar)
- Zu alte oder zukünftige Nachrichten werden verworfen

**2. Deduplication (msg_id Cache)**
- Jede Nachricht hat eindeutige `msg_id` (UUID v4)
- Ground hält LRU-Cache der letzten 500 msg_id
- Duplicate → Drop + Audit-Log

### Adaptive Security

**Gleitendes Zeitfenster:**
- Ground Station analysiert Fehler der letzten 60 Sekunden
- Gewichtete Fehlertypen:
  - `invalid_signature`: 1.0 (kritisch)
  - `malformed_packet`: 0.5 (medium)
  - `duplicate`: 0.1 (niedrig)

**Lockout-Trigger:**
- ≥ 5 aufeinanderfolgende Fehler, ODER
- Gewichtete Fehlerquote ≥ 70%

**Lockout-Verhalten:**
- Lockout-Check erfolgt **nach** erfolgreicher HMAC-Verifikation im Decision-Stage
- Pipeline: `Verify → Decision (Lockout-Check) → Routing`
- Bei aktivem Lockout: Nachricht wird in `data/quarantine/` geschrieben
- Fehlgeschlagene Verifikationen landen weiterhin in `data/rejected/`
- Audit-Log: `lockout_triggered` Event

**Rationale:**
- Verifikation wird immer durchgeführt (Security Events müssen erfasst werden)
- Decision-Stage prüft Lockout-Status basierend auf bisherigem Fehlerverlauf
- Quarantine sammelt Nachrichten während aktiver Anomalie-Phasen

---

## Design Decisions

### Warum HMAC-SHA256?

- **Symmetrische Kryptographie:** Performant, ideal für IoT/Embedded
- **Integritätsfokus:** Erkennung von Manipulation, nicht Verschlüsselung
- **Standard-Algorithmus:** Weit verbreitet, gut analysiert (FIPS 180-4)
- **Keine PKI erforderlich:** Vereinfacht Deployment in Demo-Umgebung

**Trade-off:** Shared Secret muss auf beiden Seiten sicher vorliegen.

### Warum klare Modultrennung (satellite / ground / shared)?

- **Single Source of Truth:** Protokolländerungen erfolgen ausschließlich in `shared/`
- **Testbarkeit:** Jedes Modul ist isoliert unit-testbar
- **Keine Abhängigkeitszyklen:** Klare Importrichtung (satellite/ground → shared)
- **Deployability:** Satellite und Ground können getrennt deployed werden

### Warum Tests auf mehreren Ebenen?

- **Unit-Tests:** Schnell, isoliert, hohe Abdeckung von Basisfunktionen (Crypto, Protocol)
- **Integration-Tests:** End-to-End Verifikation mit realen Configs
- **Security-Tests:** Angriffssimulationen (Tampering, Replay, Malformed Packets)

**Ergebnis:** 52 Tests, alle grün, CI-ready.

### Warum MQTT (nicht HTTP/REST)?

- **Pub/Sub-Modell:** Entkopplung von Sender und Empfänger
- **QoS-Support:** Garantierte Zustellung (QoS 1)
- **Low Overhead:** Effizienter als HTTP für IoT
- **Broker als Puffer:** Nachrichten werden bei Offline-Ground gepuffert

**Trade-off:** Zusätzliche Infrastruktur (Broker) erforderlich.

---

## Schnellstart

### Voraussetzungen

- Python 3.11
- Docker (für MQTT Broker)
- macOS oder Linux

### Installation

```bash
# Repository klonen
git clone https://github.com/Skydan111/CubeSat-Security-Simulator.git
cd CubeSat-Security-Simulator

# Virtuelle Umgebung erstellen
python3.11 -m venv .venv
source .venv/bin/activate

# Dev-Dependencies installieren
pip install -r requirements-dev.txt

# Projekt-Packages installieren (editable mode)
# Dependencies werden automatisch aus pyproject.toml gezogen
pip install -e shared
pip install -e ground
pip install -e satellite

# Installation verifizieren
pytest
```

### MQTT Broker starten

```bash
docker compose -f docker-compose.mqtt.yml up -d
```

Broker läuft auf `localhost:1883`.

### Satellite starten

```bash
./scripts/satellite_start.sh
```

Satellite liest BME280 (oder Simulation), signiert Telemetrie und publisht via MQTT.

### Ground Station starten

```bash
./scripts/ground_start.sh
```

Ground subscribt MQTT-Topic, verifiziert Signaturen und routet Daten.

### Logs prüfen

```bash
tail -f logs/satellite.log
tail -f logs/ground.log
tail -f logs/security_audit.jsonl
```

### Datenfluss verifizieren

```bash
ls -lh data/processed/
tail data/processed/*.csv
```

### Stoppen

```bash
./scripts/satellite_stop.sh
./scripts/ground_stop.sh
docker compose -f docker-compose.mqtt.yml down
```

**Weitere Details:** Siehe [docs/demo.md](docs/demo.md)

---

## Projektstruktur

```
CubeSat/
├── satellite/
│   ├── src/satellite/
│   │   ├── logger.py              # CSV Logger + HMAC Signing
│   │   ├── mqtt_publisher.py      # MQTT Publishing
│   │   └── sensors/
│   │       └── bme280.py           # BME280 Reader + Simulation
│   └── pyproject.toml
│
├── ground/
│   ├── src/ground/
│   │   ├── receiver.py             # Ingestion & Routing Pipeline
│   │   ├── verify.py               # HMAC Verification
│   │   ├── mqtt_subscriber.py      # MQTT Subscription
│   │   └── security/
│   │       └── security_manager.py # Adaptive Security (Lockout)
│   └── pyproject.toml
│
├── shared/
│   ├── src/shared/
│   │   ├── crypto/
│   │   │   └── hmac_sha256.py      # HMAC Sign/Verify
│   │   ├── protocol/
│   │   │   ├── telemetry_csv.py    # Telemetry Format
│   │   │   └── signed_csv.py       # Signed Payload Operations
│   │   └── comm/
│   │       ├── envelope.py         # MQTT Envelope V1 Schema
│   │       └── topics.py           # Topic Naming
│   └── pyproject.toml
│
├── configs/
│   ├── satellite.json              # Satellite Config
│   ├── ground.json                 # Ground Config
│   └── security_policy.yaml        # Security Policies (Lockout-Thresholds)
│
├── tests/
│   ├── unit/
│   │   ├── shared/                 # Crypto, Protocol Tests
│   │   ├── ground/                 # Receiver, Security Manager Tests
│   │   └── satellite/              # Logger, Sensor Tests
│   └── integration/
│       ├── ground/                 # End-to-End Pipeline Tests
│       └── security/               # Attack Simulation Tests
│
├── scripts/
│   ├── satellite_start.sh          # Satellite starten
│   ├── ground_start.sh             # Ground starten
│   └── *_status.sh, *_stop.sh      # Status/Stop-Skripte
│
├── examples/
│   ├── telemetry_good.csv          # Gültige Telemetrie
│   ├── telemetry_bad_sig.csv       # Ungültige Signatur
│   └── telemetry_corrupted.csv     # Malformed Packet
│
├── docs/
│   ├── architecture.md             # Systemarchitektur (detailliert)
│   ├── security.md                 # Sicherheitsmodell (detailliert)
│   └── demo.md                     # Demo-Szenarien & Troubleshooting
│
├── requirements-dev.txt            # Dev Dependencies (pytest, paho-mqtt)
├── docker-compose.mqtt.yml         # MQTT Broker (Mosquitto)
└── README.md
```

---

## Teststrategie

### Testabdeckung

**Aktueller Stand: 52 Tests**

**Unit-Tests (42 Tests)**
- `shared/crypto/` — HMAC Sign/Verify (6 Tests)
- `shared/protocol/` — Telemetry & Signed CSV Parsing (14 Tests)
- `ground/receiver/` — Routing-Pipeline (8 Tests)
- `ground/security/` — Security Manager, Lockout, Windowing (7 Tests)
- `satellite/logger/` — CSV Logger, HMAC Integration (3 Tests)
- `satellite/sensors/` — BME280 Simulation (2 Tests)

**Integration-Tests (7 Tests)**
- End-to-End Receiver Pipeline (4 Tests)
- MQTT End-to-End (1 Test, erfordert Docker)
- Satellite Logger mit realer Config (1 Test)
- Security Attacks (Tampering, Replay) (2 Tests)

**Security-Tests (3 Tests)**
- Payload-Manipulation → rejected (1 Test)
- Malformed Packets → Fehlerbehandlung (1 Test)
- MQTT Replay → Dedup (1 Test, erfordert Docker)

### Test-Ausführung

```bash
# Alle Tests
pytest

# Nur Unit-Tests
pytest tests/unit/

# Nur Security-Tests
pytest tests/integration/security/

# Mit Ausgabe
pytest -v

# Mit Coverage
pytest --cov=shared --cov=ground --cov=satellite
```

### CI/CD-Kompatibilität

- Keine externen Abhängigkeiten außer Docker (für MQTT-Tests)
- MQTT-Tests können übersprungen werden (49 Tests ohne Docker)
- Reproduzierbare Umgebung via `pyproject.toml` und `requirements-dev.txt`

---

## Grenzen & Annahmen

### Demo-Umgebung

Dieses Projekt ist eine Lern- und Demonstrationsumgebung. Folgende Aspekte sind **nicht produktionsreif:**

**Secret Management:**
- Shared Secret liegt in Konfigurationsdateien (nicht verschlüsselt)
- Keine Schlüsselrotation
- Kein Hardware Security Module (HSM)

**Netzwerk-Security:**
- MQTT ohne TLS (lokal unverschlüsselt)
- Kein mTLS (Mutual TLS)
- Keine Broker-ACLs (Topic-basierte Zugriffskontrolle)

**Skalierbarkeit:**
- Single-Satellite-Design (keine Multi-Tenancy)
- In-Memory Dedup-Cache (nicht persistent)
- Keine Datenbank für Langzeitarchivierung

### Technische Trade-offs

**HMAC statt asymmetrischer Kryptographie:**
- ✅ Performant, einfach zu implementieren
- ❌ Shared Secret muss auf beiden Seiten vorliegen
- ❌ Keine Forward Secrecy

**Payload nicht verschlüsselt:**
- ✅ Fokus auf Integrität (ausreichend für Demo)
- ❌ Telemetriedaten im Klartext übertragen
- Produktionsumgebung würde zusätzlich AES-GCM o.ä. benötigen

**Freshness Check erfordert Zeit-Synchronisation:**
- ✅ Einfacher Replay-Schutz
- ❌ Abhängig von NTP (Clock-Drift kann zu False Positives führen)

### Empfehlungen für Produktionsumgebung

Siehe [docs/security.md](docs/security.md) für detaillierte Empfehlungen:
- TLS/mTLS für MQTT
- Secret Management (KMS, Vault)
- PKI-basierte Authentifizierung
- Payload-Verschlüsselung (Encrypt-then-MAC)
- Rate Limiting & DoS-Schutz
- Time-Series Database (InfluxDB)
- Monitoring & Alerting (Grafana, Prometheus)

---

## Weiterführende Dokumentation

- [Systemarchitektur](docs/architecture.md) — Detaillierte Architektur, Datenfluss, Modulstruktur
- [Sicherheitsmodell](docs/security.md) — Bedrohungsmodell, Kryptographie, Adaptive Security
- [Demo & Quickstart](docs/demo.md) — Installation, Demo-Szenarien, Troubleshooting
- [MQTT Interface](docs/mqtt-interface.md) — Envelope-Schema, Topic-Naming, QoS-Regeln

---

## Autor

**Oleg Skydan**
Student Wirtschaftsinformatik – Fachschule Wiesau

**Schwerpunkte:**
- Cybersecurity
- Embedded Systems
- Distributed Systems
- Secure Communication

---

## Lizenz

Dieses Projekt ist zu Lern- und Demonstrationszwecken erstellt.

---

*README aktualisiert: Februar 2026*
