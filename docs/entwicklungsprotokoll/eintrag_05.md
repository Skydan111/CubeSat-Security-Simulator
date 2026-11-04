# Entwicklungsprotokoll #5 – Sichere Schlüssel-Synchronisierung & Erster Datenübertragungstest

**Datum:** 2025-11-05
**Phase:** 🔐 Security Integration / Data Link Test
**Leitung:** Oleg Skydan

---

## 🎯 Ziel der Phase
Ziel dieser Phase war die erfolgreiche Synchronisierung der kryptografischen Schlüssel zwischen Bodenstation und Bordcomputer (OBC) sowie die Durchführung des ersten gesicherten Telemetrie-Transfers.
Damit wurde überprüft, dass die HMAC-SHA256-Signaturen auf beiden Systemen mit demselben geheimen Schlüssel erzeugt und verifiziert werden können.

---

## 🧩 Statusübersicht

| Bereich | Status | Beschreibung |
|----------|---------|--------------|
| Schlüssel-Synchronisierung | ✅ | Gemeinsamer Missionsschlüssel auf Ground & OBC erzeugt und abgeglichen |
| Konfiguration | ✅ | `ground.json` und `mission.json` mit identischem secret Hexwert angelegt |
| Validierung | ✅ | `check_key.py` prüft und bestätigt Schlüsselübereinstimmung |
| Telemetrie (Log) | ✅ | `telemetry.csv` auf dem OBC erfolgreich generiert |
| Datenübertragung | ✅ | Manuelle Übertragung per `scp` auf Ground Station (`data/raw/telemetry.csv`) |
| Integritätsprüfung | ✅ | Datei-Struktur und Signaturen valide und unverändert |

---

## ⚙️ Technische Beschreibung

- **Schlüsselalgorithmus:** HMAC-SHA256
- **Validierungsskript:** `check_key.py`
- **Übertragungsweg:** `scp` (Simulation des gesicherten Links)
- **Dateipfade:**
  - OBC: `/home/pi/obc/logs/telemetry.csv`
  - Ground: `~/cube/data/raw/telemetry.csv`
- **Ergebnis:** Daten authentisch, Signatur gültig, Kommunikation bidirektional bereit

---

## 🧠 Erkenntnisse dieser Phase
- Der HMAC-Schlüssel ist auf beiden Systemen identisch und funktioniert fehlerfrei.
- Die Telemetrie-Datei kann sicher vom OBC zur Bodenstation übertragen werden.
- Damit ist die kryptografische Synchronisation zwischen Ground und OBC abgeschlossen.
- Das System ist nun bereit für automatisierte Datenübertragung über `rsync` oder MQTT.

---

## 🚀 Nächste Schritte (Phase #6 – Automatisierte Datenübertragung)
1. Automatisierte Übertragung der Telemetrie mittels `rsync` oder MQTT.
2. Integration der Signaturprüfung (`verify.py`) im Datenpipeline.
3. Erweiterung des Ground-Dashboards mit Status „processed / rejected“.
4. Finaler Integrationstest zwischen OBC und Ground im Live-Betrieb.

---

> 💬 *„Boden und Orbit sprechen nun dieselbe Sprache – die der Sicherheit.“*
> — Oleg Skydan, Missionsleiter  
