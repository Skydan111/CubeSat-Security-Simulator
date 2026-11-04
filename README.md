# Warehouse Monitor

Sichere IoT-Pipeline zur Überwachung von Lagerbedingungen – vom physischen Sensor über eine geschützte Übertragungsschicht bis zum Echtzeit-Dashboard mit KI-Assistent, der Anomalien für den Bediener interpretiert.

Ein Zonensensor (Raspberry Pi mit BME280) misst Temperatur und Luftfeuchtigkeit in einer Lagerzone, signiert jeden Messwert mit HMAC-SHA256 und überträgt ihn per MQTT an den Leitstand. Dort werden Signatur, Frische und Duplikate geprüft; nur verifizierte Daten erreichen das Dashboard. Anti-Replay-Mechanismen und eine adaptive Sicherheitslogik schützen die Übertragung gegen Manipulation und Wiederholungsangriffe.

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
│   Zonensensor (Raspberry Pi / Sim)  │
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
    │ MQTT Broker │  Topic: warehouse/v1/{zone_id}/telemetry
    │ (Mosquitto) │  QoS: 1
    └─────────────┘
           ↓
┌─────────────────────────────────────┐
│          Leitstand (macOS)          │
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
- `zone_sensor/` — Telemetrieerzeugung und MQTT Publishing
- `control_center/` — Empfang, Verifikation und Routing

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
- Der Leitstand hält LRU-Cache der letzten 500 msg_id
- Duplicate → Drop + Audit-Log

### Adaptive Security

**Gleitendes Zeitfenster:**
- Der Leitstand analysiert Fehler der letzten 60 Sekunden
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

### Warum klare Modultrennung (zone_sensor / control_center / shared)?

- **Single Source of Truth:** Protokolländerungen erfolgen ausschließlich in `shared/`
- **Testbarkeit:** Jedes Modul ist isoliert unit-testbar
- **Keine Abhängigkeitszyklen:** Klare Importrichtung (zone_sensor/control_center → shared)
- **Deployability:** Zonensensor und Leitstand können getrennt deployed werden

### Warum Tests auf mehreren Ebenen?

- **Unit-Tests:** Schnell, isoliert, hohe Abdeckung von Basisfunktionen (Crypto, Protocol)
- **Integration-Tests:** End-to-End Verifikation mit realen Configs
- **Security-Tests:** Angriffssimulationen (Tampering, Replay, Malformed Packets)

**Ergebnis:** 52 Tests, alle grün, CI-ready.

### Warum MQTT (nicht HTTP/REST)?

- **Pub/Sub-Modell:** Entkopplung von Sender und Empfänger
- **QoS-Support:** Garantierte Zustellung (QoS 1)
- **Low Overhead:** Effizienter als HTTP für IoT
- **Broker als Puffer:** Nachrichten werden bei nicht erreichbarem Leitstand gepuffert

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
git clone https://github.com/Skydan111/warehouse-monitor.git
cd warehouse-monitor

# Virtuelle Umgebung erstellen
python3.11 -m venv .venv
source .venv/bin/activate

# Dev-Dependencies installieren
pip install -r requirements-dev.txt

# Projekt-Packages installieren (editable mode)
# Dependencies werden automatisch aus pyproject.toml gezogen
pip install -e shared
pip install -e control_center
pip install -e zone_sensor

# Installation verifizieren
pytest
```

### MQTT Broker starten

```bash
docker compose -f docker-compose.mqtt.yml up -d
```

Broker läuft auf `localhost:1883`.

### Zonensensor starten

```bash
./scripts/zone_sensor_start.sh
```

Der Zonensensor liest BME280 (oder Simulation), signiert Telemetrie und publisht via MQTT.

### Leitstand starten

```bash
./scripts/control_center_start.sh
```

Der Leitstand abonniert das MQTT-Topic, verifiziert Signaturen und routet Daten.

### Logs prüfen

```bash
tail -f logs/logger.log
tail -f logs/control_center_subscriber.log
tail -f logs/security_audit.jsonl
```

### Datenfluss verifizieren

```bash
ls -lh data/processed/
tail data/processed/*.csv
```

### Stoppen

```bash
./scripts/zone_sensor_stop.sh
./scripts/control_center_stop.sh
docker compose -f docker-compose.mqtt.yml down
```

**Weitere Details:** Siehe [docs/demo.md](docs/demo.md)

---

## Projektstruktur

```
warehouse-monitor/
├── zone_sensor/
│   ├── src/zone_sensor/
│   │   ├── logger.py              # CSV Logger + HMAC Signing
│   │   ├── mqtt_publisher_from_file.py  # MQTT Publishing
│   │   └── sensors/
│   │       └── bme280.py           # BME280 Reader + Simulation
│   └── pyproject.toml
│
├── control_center/
│   ├── src/control_center/
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
│   ├── zone_sensor.yaml            # Zonensensor-Konfiguration
│   ├── control_center.json         # Leitstand-Konfiguration
│   └── security_policy.yaml        # Security Policies (Lockout-Thresholds)
│
├── tests/
│   ├── unit/
│   │   ├── shared/                 # Crypto, Protocol Tests
│   │   ├── control_center/         # Receiver, Security Manager Tests
│   │   └── zone_sensor/            # Logger, Sensor Tests
│   └── integration/
│       ├── control_center/         # End-to-End Pipeline Tests
│       └── security/               # Attack Simulation Tests
│
├── scripts/
│   ├── zone_sensor_start.sh        # Zonensensor starten
│   ├── control_center_start.sh     # Leitstand starten
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
- `control_center/receiver/` — Routing-Pipeline (8 Tests)
- `control_center/security/` — Security Manager, Lockout, Windowing (7 Tests)
- `zone_sensor/logger/` — CSV Logger, HMAC Integration (3 Tests)
- `zone_sensor/sensors/` — BME280 Simulation (2 Tests)

**Integration-Tests (7 Tests)**
- End-to-End Receiver Pipeline (4 Tests)
- MQTT End-to-End (1 Test, erfordert Docker)
- Zonensensor-Logger mit realer Config (1 Test)
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
pytest --cov=shared --cov=control_center --cov=zone_sensor
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
- Ein-Zonen-Design (keine Multi-Tenancy)
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
- [Glossar](docs/glossar.md) — Verbindliche Begriffe (Zonensensor, Leitstand, Zonen-ID …)
- [Entwicklungsprotokoll](docs/entwicklungsprotokoll/README.md) — Chronik der Entwicklung seit November 2025

---

## Technische Erkenntnisse aus diesem Projekt

Dieses Projekt war für mich eine praktische Übung im systematischen Denken über Softwarearchitektur.
Ich habe eine Telemetrie-Pipeline mit klar getrennten Komponenten (Zonensensor, Shared, Leitstand) entworfen und Datenflüsse bewusst strukturiert.

Während der Entwicklung musste ich technische Entscheidungen abwägen, zum Beispiel HMAC vs. asymmetrische Kryptografie oder MQTT vs. HTTP, und deren Auswirkungen verstehen.

Ein wichtiger Schwerpunkt war „Security by Design“: Signaturprüfung, Replay-Schutz, konsistente Serialisierung und Fail-Fast-Validierung sind bewusst Teil der Architektur.

Außerdem habe ich gelernt, KI nicht nur als Codegenerator zu nutzen, sondern als Werkzeug zur Analyse von Architekturentscheidungen und zur strukturierten Problemlösung.

Das Projekt diente vor allem dazu, praktische Erfahrung mit sicherer Datenübertragung, modularer Architektur und dem Einsatz von KI als Entwicklungspartner zu sammeln.

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
