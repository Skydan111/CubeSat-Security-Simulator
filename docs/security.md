# Sicherheitsmodell

## Überblick

Das Sicherheitskonzept des CubeSat-Telemetriesystems schützt die Datenintegrität und -authentizität auf der Kommunikationsstrecke zwischen Satellite und Ground Station.

Der Fokus liegt auf:
- **Integrität** — Erkennung von Manipulationen am Payload
- **Replay-Resistenz** — Verhinderung von Wiederholungsangriffen
- **Anomalie-Erkennung** — Adaptive Reaktion auf verdächtige Muster

**Nicht abgedeckt:**
- Vertraulichkeit (Payload ist nicht verschlüsselt)
- Authentifizierung der Endpunkte (Shared Secret, kein PKI)
- Transport-Security (MQTT ohne TLS in Demo-Umgebung)

---

## Bedrohungsmodell

| Bedrohung | Beschreibung | Kontrolle | Layer |
|-----------|--------------|-----------|-------|
| **Payload-Manipulation** | Angreifer ändert Telemetriedaten während der Übertragung | HMAC-SHA256 Signaturprüfung | Application |
| **Replay-Angriffe** | Angreifer sendet alte Nachrichten erneut | Freshness Check + msg_id Deduplication | Transport + Application |
| **Duplicate Messages** | Netzwerk/Broker sendet Nachricht mehrfach (QoS 1) | msg_id Deduplication (LRU Cache) | Transport |
| **Wiederholte ungültige Versuche** | Angreifer sendet kontinuierlich ungültige Nachrichten | Adaptive Security (Lockout) | Application |
| **Malformed Packets** | Beschädigte oder absichtlich fehlerhafte Nachrichten | Schema-Validierung, Fehlerbehandlung | Application |

**Nicht adressierte Bedrohungen (Demo-Scope):**
- Man-in-the-Middle (kein TLS)
- Side-Channel-Angriffe (z.B. Timing)
- DoS auf Broker-Ebene
- Physischer Zugriff auf Satellite/Ground

---

## HMAC-SHA256 Integritätsschutz

### Kryptographisches Verfahren

**Algorithmus:** HMAC-SHA256 (RFC 2104 + FIPS 180-4)

**Schlüssel:**
- Symmetrischer Shared Secret (hexadezimal kodiert)
- Länge: empfohlen ≥ 32 Bytes (256 Bit)
- Verteilung: manuell (Demo), später: Key Management Service

**Signatur-Erzeugung (Satellite):**
```python
payload = "ts,temp,hum,press,mode"
signature = hmac.new(key=secret, msg=payload.encode(), digestmod=hashlib.sha256).hexdigest()
# Ausgabe: 64 Hex-Zeichen
```

**Signatur-Verifikation (Ground):**
```python
expected_sig = hmac.new(key=secret, msg=payload.encode(), digestmod=hashlib.sha256).hexdigest()
is_valid = hmac.compare_digest(received_sig, expected_sig)  # Constant-time
```

### Signatur-Scope

Die Signatur wird über den **kanonischen Payload** berechnet:
```
ts,temperature_c,humidity_pct,pressure_hpa,mode
```

**Nicht signiert:**
- Envelope-Felder (msg_id, ts_utc, etc.) — Transport-Layer
- Die Signatur selbst

**Kanonische Form:**
- Exakte Feldanzahl (5 Felder)
- Komma-separiert, keine Leerzeichen
- Numerische Werte mit 2 Dezimalstellen (z.B. `23.50`)

### Angriffsvektoren und Schutz

| Angriff | Schutz |
|---------|--------|
| Payload-Änderung | Signatur wird ungültig → rejected/ |
| Signatur-Entfernung | Schema-Validierung erkennt fehlendes Feld → malformed |
| Signatur-Ersetzen (ohne Schlüssel) | HMAC-Verifikation schlägt fehl → rejected/ |
| Known-Plaintext | HMAC ist resistent (One-Way-Function) |
| Timing-Angriff auf Verify | `hmac.compare_digest()` ist constant-time |

---

## Anti-Replay: Freshness + Sliding Window

Replay-Schutz erfolgt auf **zwei Ebenen**:

### 1. Freshness Check (Transport-Layer)

**Mechanismus:**
- Envelope-Feld `ts_utc` wird mit aktueller Zeit verglichen
- Erlaubter Skew: ± MAX_SKEW_SECONDS (z.B. 120 Sekunden)

**Validierung:**
```python
now = datetime.now(timezone.utc)
msg_time = datetime.fromisoformat(envelope["ts_utc"])
skew = abs((now - msg_time).total_seconds())

if skew > MAX_SKEW_SECONDS:
    # Drop: Nachricht zu alt oder zu weit in der Zukunft
```

**Schutz gegen:**
- Sehr alte Nachrichten (Replay nach Stunden/Tagen)
- Nachrichten mit Zukunfts-Timestamps (ungültige Uhren)

**Limitierungen:**
- Erfordert synchronisierte Uhren (NTP auf Satellite + Ground)
- Skew-Fenster ist Kompromiss: zu klein → false positives, zu groß → Replay-Fenster

---

### 2. Deduplication (msg_id Cache)

**Mechanismus:**
- Jede Nachricht hat eindeutige `msg_id` (UUID v4)
- Ground hält LRU-Cache der letzten N msg_id (z.B. N=500)
- Duplicate msg_id → Drop + Audit-Log

**Implementierung:**
```python
seen_msg_ids = collections.deque(maxlen=500)

if envelope["msg_id"] in seen_msg_ids:
    # Duplicate erkannt
    log_security_event("duplicate", msg_id=msg_id)
    return  # Drop

seen_msg_ids.append(envelope["msg_id"])
```

**Schutz gegen:**
- Exakte Replays (identische Nachricht mehrfach gesendet)
- QoS-1-Duplikate (MQTT Broker sendet bei Unsicherheit mehrfach)

**Cache-Größe:**
- Sliding Window: letzte 500 Nachrichten
- Bei Telemetrie-Rate von 1 msg/10s → ca. 83 Minuten Abdeckung
- Trade-off: Speicher vs. Replay-Fenster

---

### Kombination beider Mechanismen

**Beispiel-Szenario:**

1. Angreifer zeichnet Nachricht `msg_id=ABC` auf (ts_utc=10:00)
2. Nach 5 Minuten: Replay-Versuch mit gleicher Nachricht
   - Freshness: OK (innerhalb 120s Skew)
   - Dedup: **FAIL** (msg_id bereits im Cache) → **DROP**

3. Nach 2 Stunden: Erneuter Replay-Versuch
   - Freshness: **FAIL** (ts_utc zu alt) → **DROP**
   - Dedup wird nicht erreicht

**Ergebnis:** Robuster Schutz über kurze (Dedup) und lange (Freshness) Zeiträume.

---

## Adaptive Security (Lockout-Mechanismus)

### Motivation

Bei normalem Betrieb sind gelegentliche fehlerhafte Nachrichten akzeptabel (Netzwerkfehler, Hardware-Glitches).

**Aber:** Wiederholte, konsistente Fehler deuten auf:
- Aktiven Angriff (z.B. Brute-Force auf Signatur)
- Kompromittierte Satellite
- Fehlkonfiguration

**Adaptive Security** reagiert dynamisch auf Fehlermuster.

---

### Gleitendes Zeitfenster

Ground Station hält Ereignisprotokoll der letzten N Sekunden (z.B. 60s):

```python
events = [
    {"ts": "10:00:05", "type": "invalid_signature"},
    {"ts": "10:00:08", "type": "malformed_packet"},
    {"ts": "10:00:12", "type": "invalid_signature"},
    ...
]
```

**Trim-Logik:**
- Alte Events (älter als Zeitfenster) werden entfernt
- Nur aktuelle Events zählen für Anomalie-Erkennung

---

### Gewichtete Fehlertypen

Nicht alle Fehler sind gleich kritisch:

| Event Type | Gewicht | Begründung |
|------------|---------|------------|
| `invalid_signature` | 1.0 | Kritisch: HMAC ungültig → mögliche Manipulation |
| `malformed_packet` | 0.5 | Medium: Beschädigte Nachricht, weniger verdächtig |
| `duplicate` | 0.1 | Niedrig: QoS-1-Artefakt, meist harmlos |

**Konfiguration:** `configs/security_policy.yaml`

---

### Lockout-Schwellwerte

**1. Consecutive Fails (Folge-Fehler):**
```yaml
consecutive_fails_lockout: 5
```
Wenn ≥ 5 aufeinanderfolgende Fehler → **LOCKOUT**

**2. Weighted Ratio (Fehlerquote):**
```yaml
lockout_threshold: 0.7  # 70%
```
Wenn gewichtete Fehlerquote ≥ 70% → **LOCKOUT**

**Berechnung:**
```python
total_weight = sum(weight(event) for event in window)
total_events = len(window)
ratio = total_weight / total_events

if ratio >= lockout_threshold:
    trigger_lockout()
```

---

### Lockout-Verhalten

**Bei aktivem Lockout:**

1. **Vor HMAC-Verifikation:**
   - Nachricht wird direkt in `data/quarantine/` geschrieben
   - Keine teure HMAC-Berechnung
   - Audit-Log: `lockout_quarantine`

2. **Nach erfolgreicher Verifikation:**
   - Lockout wird **nicht** aufgehoben
   - Erfordert manuellen Eingriff oder Timeout

**Ziel:**
- Schutz vor Resource-Exhaustion (HMAC-Berechnung ist teuer)
- Signal an Operator: "Anomalie erkannt, prüfen erforderlich"

---

### Beispiel-Szenario

**Timeline:**

| Zeit | Event | Action | Lockout? |
|------|-------|--------|----------|
| 10:00:00 | valid | processed | Nein |
| 10:00:05 | invalid_signature (1.0) | rejected | Nein |
| 10:00:10 | invalid_signature (1.0) | rejected | Nein |
| 10:00:15 | invalid_signature (1.0) | rejected | Nein |
| 10:00:20 | invalid_signature (1.0) | rejected | Nein |
| 10:00:25 | invalid_signature (1.0) | rejected | **JA** (5 consecutive) |
| 10:00:30 | valid (aber Lockout aktiv) | **quarantine** | JA |

**Ergebnis:** Nach dem 5. Fehler wird Lockout aktiviert. Selbst gültige Nachrichten landen in Quarantäne.

---

## Konfiguration

Sicherheitsparameter sind in `configs/security_policy.yaml` definiert:

```yaml
security:
  enabled: true

  window_seconds: 60
  consecutive_fails_lockout: 5
  lockout_threshold: 0.7

  weights:
    invalid_signature: 1.0
    malformed_packet: 0.5
    duplicate: 0.1
```

**Vorteile:**
- Keine Hardcoding im Code
- Anpassbar ohne Code-Änderung
- Testbar mit unterschiedlichen Policies

---

## Audit-Logging

Alle sicherheitsrelevanten Ereignisse werden protokolliert:

### Human-Readable Log (`logs/security.log`)

```
2026-02-25 15:20:05 [WARNING] Invalid signature detected. msg_id=abc123
2026-02-25 15:20:12 [CRITICAL] Lockout triggered. consecutive_fails=5
```

### Machine-Readable Log (`logs/security_audit.jsonl`)

```json
{"ts": "2026-02-25T15:20:05Z", "event": "invalid_signature", "msg_id": "abc123", "sat_id": "SAT-001"}
{"ts": "2026-02-25T15:20:12Z", "event": "lockout_triggered", "reason": "consecutive_fails", "count": 5}
```

**Stripped Metadata:**
- Keine Secrets (HMAC-Schlüssel)
- Keine vollständigen Payloads
- Nur Event-Typ, IDs, Timestamps

---

## Grenzen & Annahmen

### Demo-Umgebung

**Nicht produktionsreif:**
- Shared Secret in Config-Dateien (keine Rotation)
- Kein Hardware Security Module (HSM)
- Keine TLS/mTLS auf MQTT
- Kein zentrales Secret Management

### HMAC-Limitierungen

**Integrität, nicht Vertraulichkeit:**
- HMAC schützt gegen Manipulation
- Payload ist **nicht verschlüsselt**
- Telemetriedaten sind im Klartext übertragen

**Shared Secret:**
- Symmetrisch: Beide Seiten kennen Schlüssel
- Kompromittierung einer Seite → gesamtes System unsicher
- Keine Forward Secrecy

### Replay-Schutz

**Time-Sync-Abhängigkeit:**
- Freshness Check erfordert NTP
- Clock-Drift → False Positives/Negatives

**Cache-Größe:**
- LRU Cache ist begrenzt (z.B. 500 Einträge)
- Sehr alte Replays (außerhalb Cache) könnten durchkommen
- In Praxis: Freshness Check fängt diese ab

### Adaptive Security

**False Positives:**
- Netzwerkprobleme könnten Lockout triggern
- Erfordert manuellen Eingriff

**Keine automatische Recovery:**
- Lockout bleibt bis manuell gelöst oder System-Neustart

---

## Security Testing

Sicherheitseigenschaften werden in `tests/integration/security/` geprüft:

### Test Coverage

- **Tampering** — Manipulierte Payloads werden rejected
- **Replay** — Duplicate msg_id wird erkannt und gedropped
- **Malformed** — Fehlerhafte Envelope/Payload führen zu Fehlermeldung
- **Lockout** — Wiederholte Fehler triggern Quarantine

### Test-Strategie

- Unit-Tests: Crypto-Funktionen (sign/verify)
- Integration-Tests: End-to-End mit MQTT
- Security-Tests: Angriffssimulationen

---

## Empfehlungen für Produktionsumgebung

### Kurzfristig (Quick Wins)

1. **TLS für MQTT**
   - Broker mit TLS-Zertifikat
   - Client-seitige Zertifikatsvalidierung

2. **Secret Management**
   - Secrets aus Umgebungsvariablen (nicht Config-Dateien)
   - Rotation-Mechanismus

3. **Monitoring & Alerting**
   - Security-Events in SIEM
   - Alarm bei Lockout

### Mittelfristig

4. **mTLS (Mutual TLS)**
   - Client-Zertifikate für Satellite
   - Broker prüft Client-Identität

5. **Rate Limiting**
   - Broker-seitige Limits pro sat_id
   - Schutz vor Flooding

6. **Key Rotation**
   - Regelmäßiger HMAC-Schlüsselwechsel
   - Unterstützung für Schlüssel-Versioning

### Langfristig

7. **PKI-basierte Authentifizierung**
   - Asymmetrische Kryptographie (z.B. Ed25519)
   - Zertifikatsketten

8. **Payload-Verschlüsselung**
   - AES-GCM für Vertraulichkeit
   - Zusätzlich zu HMAC (Encrypt-then-MAC)

9. **Hardware Security Module (HSM)**
   - Schlüssel verlassen nie HSM
   - FIPS 140-2/3 Compliance

---

*Letzte Aktualisierung: Februar 2026*
