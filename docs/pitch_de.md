# Projektbeschreibung & Pitch

## Kurzbeschreibung

Das CubeSat Secure Telemetry Simulator-Projekt demonstriert eine vollständige, abgesicherte Telemetrie-Pipeline von einem simulierten Satelliten (Raspberry Pi) zu einer Bodenstation. Der Fokus liegt auf Datenintegrität durch HMAC-SHA256, Replay-Resistenz durch Freshness-Checks und Deduplication, sowie adaptive Sicherheit durch einen Lockout-Mechanismus bei Anomalien. Die Architektur folgt klaren Designprinzipien: strikte Modultrennung (satellite/ground/shared), testgetriebene Entwicklung mit 52 automatisierten Tests, und vollständige Reproduzierbarkeit. Das System ist lauffähig auf echter Hardware (Raspberry Pi mit BME280-Sensor) und nutzt MQTT als realistischen IoT-Transportkanal.

---

## 2-Minuten Elevator Pitch

"Guten Tag. Ich habe ein Projekt entwickelt, das zeigt, wie man Sensordaten von einem Satelliten sicher zur Bodenstation überträgt.

Das Problem: Wenn Telemetriedaten über ein Netzwerk gesendet werden, können sie manipuliert, wiederholt oder verfälscht werden. In echten Satellitensystemen ist das kritisch – fehlerhafte Daten können zu falschen Entscheidungen führen.

Meine Lösung besteht aus drei Komponenten:

Erstens: Der Satellite – simuliert auf einem Raspberry Pi mit echtem BME280-Sensor. Er liest Temperatur, Luftfeuchtigkeit und Druck, signiert jeden Datensatz mit HMAC-SHA256, und sendet ihn via MQTT an die Bodenstation.

Zweitens: Der MQTT-Broker als realistischer Transportkanal – das ist der Standard in IoT-Systemen. Nachrichten werden mit QoS-1 garantiert zugestellt, und ich nutze ein JSON-Envelope-Protokoll mit Base64-kodierten Payloads.

Drittens: Die Ground Station – sie empfängt Nachrichten, validiert das Envelope-Schema, führt Deduplication durch, prüft Freshness gegen Replay-Angriffe, und verifiziert die HMAC-Signatur. Nur gültige Daten landen in 'processed'. Manipulierte Daten gehen nach 'rejected'. Und bei wiederholten Sicherheitsverletzungen greift ein adaptiver Lockout-Mechanismus, der verdächtige Nachrichten in 'quarantine' schreibt.

Was hebt das Projekt hervor?

**Sicherheit**: Jede Schicht ist abgesichert – Transport-Layer mit Dedup und Freshness, Application-Layer mit HMAC und Lockout. Ich habe Angriffssimulationen implementiert: Tampering, Replay, Malformed Packets – alles wird korrekt erkannt und behandelt.

**Architektur**: Strikte Modultrennung. 'shared' ist die Single Source of Truth für Protokoll und Kryptographie. 'satellite' und 'ground' haben klare, nicht überlappende Verantwortlichkeiten. Das macht das System testbar und wartbar.

**Testabdeckung**: 52 automatisierte Tests – Unit-Tests für Crypto und Protokoll, Integration-Tests für End-to-End-Flows, Security-Tests für Angriffe. Alle Tests sind CI-ready und laufen ohne externe Abhängigkeiten außer Docker.

**Realitätsnähe**: Das läuft auf echter Hardware. Ich habe es auf einem Raspberry Pi deployed, mit echtem BME280-Sensor. Die Daten sind real, die Signaturen sind echt, der Datenfluss ist live.

Technisch nutze ich Python 3.11 mit klarer Package-Struktur (editable installs, pyproject.toml), HMAC-SHA256 für Integrität, MQTT für Transport, und eine adaptive Security-Policy die aus YAML geladen wird.

Das Projekt zeigt, dass ich End-to-End-Systeme bauen kann – von Hardware-Integration über sichere Protokolle bis zu getesteten, produktionsnahen Pipelines. Es demonstriert Verständnis für Cybersecurity-Prinzipien: Defense in Depth, Fail Secure, und Audit Logging.

Der Code ist vollständig dokumentiert – Architektur, Sicherheitsmodell, Quickstart-Guide, alles auf Deutsch. Jemand kann das Repo klonen, den Anweisungen folgen, und in 5 Minuten das System laufen haben.

Was ich daraus gelernt habe: Wie man komplexe Sicherheitsanforderungen in einfache, testbare Module übersetzt. Wie man Protokolle designed, die sowohl robust als auch erweiterbar sind. Und wie wichtig es ist, von Anfang an auf Testbarkeit zu achten.

Das nächste, was ich damit machen würde: TLS für MQTT hinzufügen, PKI-basierte Authentifizierung implementieren, und eine Time-Series-Datenbank für Langzeitarchivierung integrieren. Aber der Kern – die sichere, getestete Pipeline – steht.

Vielen Dank. Haben Sie Fragen?"

---

## Kernbotschaften (Fallback für kürzere Formate)

### 30-Sekunden-Version

"Ich habe eine sichere Telemetrie-Pipeline für einen simulierten CubeSat gebaut. Sensordaten vom Raspberry Pi werden mit HMAC-SHA256 signiert, via MQTT übertragen, und auf der Bodenstation gegen Manipulation und Replay-Angriffe verifiziert. 52 automatisierte Tests, klare Architektur, lauffähig auf echter Hardware. Das Projekt zeigt End-to-End-Systemdesign mit Fokus auf Cybersecurity."

### Technische Highlights (für technisches Publikum)

- **Kryptographie:** HMAC-SHA256 (Constant-Time Verify, Timing-Attack-resistent)
- **Anti-Replay:** Dual-Layer (Freshness Check + msg_id Deduplication mit LRU-Cache)
- **Adaptive Security:** Gleitendes Zeitfenster, gewichtete Fehlertypen, Schwellwert-basierter Lockout
- **Protokoll:** MQTT mit JSON Envelope V1, QoS-1, Base64-kodierte Signed Payloads
- **Architektur:** Strikte Modultrennung (shared als Single Source of Truth)
- **Tests:** 52 Tests (Unit, Integration, Security) – vollständig automatisiert
- **Hardware:** Raspberry Pi 4B, BME280 Sensor (I2C), lauffähig in Produktion

### Warum ist das relevant?

**Für Arbeitgeber:**
- Demonstriert Verständnis von Secure System Design
- Zeigt praktische Umsetzung von Cybersecurity-Prinzipien (nicht nur Theorie)
- Beweist Fähigkeit, komplexe Systeme zu strukturieren und zu testen
- Hardware-Integration + Software-Entwicklung kombiniert
- Dokumentation auf professionellem Niveau

**Für Studienprojekte / Portfolio:**
- Geht über typische "Hello World"-Projekte hinaus
- Zeigt reale Problemlösung (IoT Security ist aktuelles Thema)
- Vollständig reproduzierbar (andere können es nachbauen)
- Open Source, professionell dokumentiert

**Für weiterführende Arbeiten:**
- Basis für Bachelor/Master-Thesis (z.B. Erweiterung um mTLS, PKI, etc.)
- Vorlage für ähnliche Secure-IoT-Projekte
- Lernressource für andere Studierende

---

## Häufige Fragen & Antworten

**F: Warum HMAC statt asymmetrischer Kryptographie?**
A: HMAC ist performant und ausreichend für Integritätsschutz. In einer Demo-Umgebung mit einem Satellite und einer Ground Station ist Shared Secret Management vertretbar. Für Produktionsumgebungen würde ich PKI empfehlen, aber der Fokus hier liegt auf Integrität, nicht auf Authentifizierung.

**F: Wie wird Replay verhindert?**
A: Dual-Layer: Freshness Check prüft, ob die Nachricht zeitlich aktuell ist (±120s), und Deduplication erkennt identische msg_id. Kombination beider Mechanismen bietet robusten Schutz.

**F: Was passiert bei einem Lockout?**
A: Nach dem Schwellwert (z.B. 5 aufeinanderfolgende Fehler) werden nachfolgende Nachrichten in Quarantäne geschrieben – auch wenn die Signatur gültig ist. Das verhindert Resource-Exhaustion bei Angriffen und signalisiert Anomalien.

**F: Ist das produktionsreif?**
A: Nein, es ist eine Demonstrationsumgebung. Für Produktion fehlen: TLS/mTLS, Secret Rotation, HSM, persistente Dedup-Datenbank, Rate Limiting, etc. Aber die Architektur ist sauber und erweiterbar.

**F: Warum Python, nicht C/C++?**
A: Python ist ideal für Rapid Prototyping und demonstriert Architektur-Prinzipien klar. Für Performance-kritische Embedded Systems würde ich Rust oder C++ wählen, aber hier ist Lesbarkeit wichtiger.

**F: Wie lange hat das Projekt gedauert?**
A: Etwa 6–8 Wochen iterative Entwicklung. Inklusive Hardware-Setup, Protokoll-Design, Implementierung, Testing, und Dokumentation.

---

*Dokument erstellt: Februar 2026*
