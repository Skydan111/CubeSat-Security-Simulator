# Entwicklungsprotokoll #7 – Adaptive Security Mode
**Datum:** 2025-11-19
**Status:** ✅ Abgeschlossen
**Phase:** 🔒 Intelligente Sicherheitslogik & Anomalieerkennung

---

## 🧩 Zusammenfassung
In dieser Phase wurde der Leitstand erfolgreich um einen **adaptiven Sicherheitsmodus** erweitert.
Das System analysiert eingehende Telemetrie, erkennt sicherheitskritische Muster (invalid signatures, malformed packets, hohe Fehlerraten) und aktiviert automatisch Lockouts, Quarantäne oder Drop-Mechanismen.

Das Ergebnis ist eine **resiliente, selbstregulierende Telemetrie-Pipeline**, die Manipulationen erkennt und autonom darauf reagiert.

---

## 🔧 Durchgeführte Schritte

### 1. **Sicherheitsrichtlinie (YAML-Policy) implementiert**
- Einführung der Datei `configs/security_policy.yaml`
- Definition aller sicherheitsrelevanten Parameter:
  - Analysefenster (window_seconds)
  - maximale Fehlerrate (max_fail_ratio)
  - Mindestanzahl an Ereignissen (min_events_in_window)
  - sofortiger Lockout nach X Fehlern (consecutive_fail_threshold)
  - Lockoutdauer und Cooldown-Phase
  - Gewichtung verschiedener Fehlertypen
  - Aktionen während Lockout (drop / quarantine / reject)
  - Pfade für Logging und Audit-Dateien
- Policy wird automatisch geladen und validiert.

---

### 2. **SecurityManager entwickelt**
- Zentrale Sicherheitskomponente des Leitstands erstellt.
- Funktionen implementiert:
  - Sliding-Window-Auswertung aller Verify-Events
  - Berechnung der Weighted Fail Ratio
  - Erkennung sicherheitskritischer Muster
  - Aktivierung der Lockout-Phase
  - Quarantäne- oder Drop-Verhalten während Lockout
- Einführung von zwei Log-Systemen:
  - **security.log** (menschlich lesbar, rotierbar)
  - **security_audit.jsonl** (maschinenlesbar)
- Konsistente Zeitstempel (UTC).
- Schutz vor doppelten Loggern implementiert.

---

### 3. **Receiver erweitert**
- Lockout-Check **vor** der HMAC-Verifikation ergänzt.
- Korrektes Routing:
  - processed.csv
  - rejected.csv
  - quarantine.csv (bei Lockout)
- Erweiterte Fehlerklassifikation:
  - `invalid_signature`
  - `malformed_packet`
  - `corrupt_payload`
- CLI um neue Parameter erweitert:
  - `--simulate`
  - `--simulate-count`
  - `--security-policy`
  - `--security-log`
  - `--security-audit`
  - `--quarantine-csv`
- Verbesserungen der Robustheit und Pfadbehandlung.

---

### 4. **End-to-End Tests**
- **Test 1:** Normale Simulation → keine Sperre.
- **Test 2:** Serienfehler → Lockout korrekt ausgelöst.
- **Test 3:** Pakete während Lockout → Quarantäne.
- **Test 4:** Cooldown-Phase → reduzierte Sensitivität wie geplant.
- Sämtliche Logs und Audit-Einträge erfolgreich validiert.

---

## 📊 Datenfluss-Diagramme

### **Mermaid Flowchart**
```mermaid
flowchart TD

A[Telemetry Packet Incoming] --> B{SecurityManager: Lockout active?}
B -- Ja --> C[Action during Lockout]
C -->|quarantine| Q[Write to quarantine.csv]
C -->|drop| D[Drop Packet]
C -->|reject| R[Write to rejected.csv]

B -- Nein --> V[Verify HMAC]
V -->|valid| P[Write to processed.csv]
V -->|invalid| J[Write to rejected.csv]

V --> L[SecurityManager.on_verification_result()]
L --> E{Trigger Lockout?}
E -- Ja --> K[Enable Lockout]
E -- Nein --> P2[Continue Normal Operation]
```

---

### **ASCII Sequence Diagram**
```
┌─────────────────────┐
│  Incoming Packet    │
└──────────┬──────────┘
           ▼
   ┌───────────────┐
   │ Lockout check?│
   └───────┬───────┘
   Yes     │    No
   ▼       │      ▼
┌───────────────────┐    ┌──────────────────────────┐
│ Apply lockout     │    │ Verify HMAC signature    │
│ action:           │    └───────────┬──────────────┘
│  drop/quarantine  │                │
└───────────────────┘       valid    │    invalid
                              ▼      │        ▼
                         ┌──────────────────┐
                         │ processed.csv    │
                         └──────────────────┘
                                         ┌───────────────────┐
                                         │ rejected.csv      │
                                         └───────────────────┘
```

---

## 📈 Resultat
✅ Adaptives Sicherheitssystem vollständig implementiert
✅ Schutz vor manipulierten Datenpaketen
✅ Resiliente Telemetrie-Pipeline
✅ Maschinelle und menschliche Logs integriert
✅ System verhält sich stabil unter Last und Angriffsmustern

---

## ⚙️ Nächster Schritt
🔧 **Phase 8 – Integration des physischen Sensors (BME280-Modul)**
→ Erste echte Sensordaten werden signiert, gesendet und durch die gesamte Sicherheitskette verarbeitet.

---

📘 *Report erstellt von Oleg Skydan – Warehouse-Monitor-Projekt (Fachschule Wiesau)*

