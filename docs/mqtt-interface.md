# MQTT Interface Contract (v1)

## Ziel
Implementierung eines realen Kommunikationskanals zwischen Satellite (On-Board Computer) und Ground Station
über MQTT, ohne Änderungen an der bestehenden Architektur (satellite/ground/shared).

Dieses Dokument definiert Topics, Message Envelope, QoS-Regeln sowie Anti-Replay/Dedup-Verhalten.

---

## Begriffe
- Satellite: On-Board Computer Simulator (Raspberry Pi).
- Ground: Ground Station / Receiver Pipeline.
- Broker: MQTT Broker (z. B. Mosquitto).
- Signed Payload: vorhandenes Format aus shared/ (HMAC-SHA256 Signatur/Verifikation).

---

## MQTT Topics (v1)

### Basispräfix
cubesat/v1/<sat_id>/...

### Uplink: Telemetry
- Topic: cubesat/v1/<sat_id>/telemetry
- Richtung: Satellite → Ground

### Downlink: Command (später)
- Topic: cubesat/v1/<sat_id>/command
- Richtung: Ground → Satellite

### Status / Presence (optional)
- Topic: cubesat/v1/<sat_id>/status

---

## QoS / Retain (Startkonfiguration)

### Telemetry
- QoS: 1
- retain: false

### Command (später)
- QoS: 1
- retain: false

### Status (optional)
- QoS: 0 oder 1
- retain: nach Bedarf (initial: false)

Begründung: QoS1 ist realistisch für IoT-Telemetrie und erzwingt korrektes Dedup-Verhalten (Duplicate Messages sind möglich).

---

## Message Format: Transport Envelope (JSON) + Signed Payload

MQTT Message Payload ist ein JSON-Objekt (UTF-8).
Der eigentliche fachliche Payload bleibt unverändert: vorhandener Signed Payload aus shared/
wird als Base64 in payload_b64 transportiert.

### Envelope Schema (v1)
Felder:
- v (string): Envelope-Version. Muss "1" sein.
- sat_id (string): Satellite ID.
- msg_type (string): "telemetry" (später auch `"command"`).
- msg_id (string): Eindeutige Message-ID (UUID v4 empfohlen).
- ts_utc (string): UTC Timestamp (ISO-8601, z. B. `2026-01-06T15:20:00Z`).
- qos (number): QoS-Level (0/1/2). Nur für Diagnose/Logging.
- payload_b64 (string): Base64-kodiertes Signed Payload (bytes).

### Beispiel (Telemetry)
```json
{
  "v": "1",
  "sat_id": "SAT-001",
  "msg_type": "telemetry",
  "msg_id": "b7d3b4fb-1f7a-4c4a-9b22-2d1c6f2a9e8a",
  "ts_utc": "2026-01-06T15:20:00Z",
  "qos": 1,
  "payload_b64": "BASE64_ENCODED_SIGNED_PAYLOAD_BYTES"
}
```

## Sicherheitsregeln (Application Layer)

### Verifikation (Ground)

Reihenfolge der Verarbeitung in Ground:

1. Envelope JSON validieren
   (Pflichtfelder vorhanden, `v == "1"`).

2. Dedup prüfen
   (`msg_id` bereits gesehen → **drop + log**).

3. Freshness prüfen
   (`ts_utc` innerhalb erlaubtem Zeitfenster → sonst **drop + log**).

4. Signed Payload aus payload_b64 decodieren.

5. Signatur/HMAC über bestehende shared/ Logik verifizieren.

6. Nur bei erfolgreicher Verifikation:
   Übergabe an die Receiver Pipeline.

---

### Anti-Replay / Dedup

- Ground hält pro sat_id einen LRU-Cache der letzten N msg_id
  (z. B. `N = 500`).

- Wenn msg_id bereits vorhanden ist →
  Nachricht wird verworfen (**Duplicate**).

- Zusätzlich wird ein Zeitfenster MAX_SKEW_SECONDS
  (z. B. 120 Sekunden) geprüft.
  Wenn ts_utc zu alt oder zu weit in der Zukunft liegt → verwerfen.

---

## Transport Security (späterer Schritt)

### Initialversion

- MQTT ohne TLS ist zulässig (lokales Setup).
- HMAC / Signed Payload bleibt immer aktiv.

### Später

- TLS / mTLS
- Broker-ACLs (topic-based Zugriffskontrolle)

---

## Definition of Done (Phase 4 – Minimal)

1. Satellite publiziert Telemetry via MQTT (QoS 1).
2. Ground empfängt Nachrichten, dedupliziert sie,
   prüft Freshness und verifiziert die Signatur.
3. Integration Test startet einen lokalen Broker
   und prüft 50–100 Nachrichten End-to-End.
4. Security Tests:
   - Tampering
   - Replay
   führen zu Drop + sauberem Log.
