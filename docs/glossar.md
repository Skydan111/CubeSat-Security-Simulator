# Glossar

Einheitliche Begriffe für Code, Dokumentation und Präsentation des Warehouse Monitors.

**Grundregel:** Bezeichner im Code (Verzeichnisse, Pakete, Variablen, Funktionen) sind englisch. Alles Sichtbare – Dokumentation, Kommentare, Logausgaben, Dashboard – ist deutsch.

## Systemkomponenten

| Begriff (Deutsch) | Bezeichner im Code | Bedeutung |
|---|---|---|
| **Zonensensor** | `zone_sensor/` | Messpunkt in einer Lagerzone: Raspberry Pi mit BME280. Erfasst Temperatur und Luftfeuchtigkeit, signiert jeden Messwert (HMAC-SHA256) und publiziert ihn per MQTT. |
| **Sensorrechner** | – | Der Raspberry Pi 4B, auf dem der Zonensensor läuft. |
| **Leitstand** | `control_center/` | Zentrale Stelle, an der die Daten aus dem Lager zusammenlaufen. Empfängt Nachrichten, prüft Signatur, Frische und Duplikate und leitet sie nach *processed*, *rejected* oder *quarantine* weiter. |
| **Dashboard** | `dashboard/` | Web-Oberfläche für den Bediener: Live-Werte, Grenzwert-Alarme, Statistiken und KI-Analyse. |
| **Gemeinsames Protokoll** | `shared/` | Nachrichtenformat (Envelope), Telemetrie-Format und Kryptographie – die einzige Quelle für Formate, die Zonensensor und Leitstand gemeinsam nutzen. |

## Kommunikation

| Begriff (Deutsch) | Bezeichner im Code | Bedeutung |
|---|---|---|
| **Zonen-ID** | `zone_id`, `ZONE_ID` | Kennung der Lagerzone und damit des Zonensensors, z. B. `ZONE-01`. |
| **Geräteschlüssel** | `SENSOR_SECRET_HEX` | Geheimer HMAC-Schlüssel des Zonensensors. Gehört zum Gerät, nicht zur Zone. |
| **MQTT-Topic** | `warehouse/v1/{zone_id}/telemetry` | Kanal, über den ein Zonensensor seine Telemetrie veröffentlicht. |
| **Envelope** | `EnvelopeV1` | JSON-Hülle einer MQTT-Nachricht mit `zone_id`, `msg_id`, Zeitstempel und signierter Nutzlast (Base64). |
| **Telemetrie** | `telemetry` | Laufend übertragene Messwerte (Temperatur, Luftfeuchtigkeit). Üblicher Begriff im industriellen IoT. |
| **Messlauf** | – | Ein zusammenhängender Zeitraum der Datenerfassung. |
