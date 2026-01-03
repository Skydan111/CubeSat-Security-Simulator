"""
SecurityManager – Adaptives Sicherheitsmodul für die Ground Station

Funktionen:
    • Analyse eingehender Ereignisse (verifiziert / verworfen)
    • Bewertung eines gleitenden Zeitfensters
    • Gewichtete Fehlerrate (unterschiedliche Fehler-Typen werden unterschiedlich gewichtet)
    • Auslösen eines temporären Lockouts
    • Audit-Logging (JSONL) + Security-Log (über logging.Logger)
"""

from __future__ import annotations
import time
import json
import os
import threading
import collections
import logging
from dataclasses import dataclass
from typing import Deque, Optional, Dict, Any
import yaml


# --------------------------------------------------------------
# Datenstruktur eines einzelnen Sicherheitsereignisses
# --------------------------------------------------------------

@dataclass
class SecurityEvent:
    ts: float            # Zeitstempel (Unix-Zeit)
    ok: bool             # True = verifiziert, False = Fehler
    reason: str          # Grund: "ok" | "invalid_signature" | "corrupt_payload" | ...
    meta: Dict[str, Any] # Zusatzinfos (Quelle, Paket-ID, Länge usw.)


# --------------------------------------------------------------
# Hauptklasse: SecurityManager
# --------------------------------------------------------------

class SecurityManager:
    """
    Adaptive Sicherheitslogik:
        • führt ein Fenster von Ereignissen
        • berechnet weighted fail ratio
        • erkennt verdächtige Muster
        • aktiviert temporäre Lockouts
        • führt Audit-Log (JSONL) und Security-Log (Logging)
    """

    def __init__(self, policy_path: str, security_log_path: Optional[str] = None, audit_log_path: Optional[str] = None):
    # Policy laden
        with open(policy_path, "r", encoding="utf-8") as f:
            self.policy = yaml.safe_load(f) or {}

        # Konfiguration aus Policy
        self.window_seconds = float(self.policy.get("window_seconds", 120))
        self.max_fail_ratio = float(self.policy.get("max_fail_ratio", 0.4))
        self.min_events_in_window = int(self.policy.get("min_events_in_window", 10))
        self.consecutive_fail_threshold = int(self.policy.get("consecutive_fail_threshold", 5))

        self.lockout_seconds = int(self.policy.get("lockout_seconds", 60))
        self.cooldown_seconds = int(self.policy.get("cooldown_seconds", 90))
        self.action_during_lockout = str(self.policy.get("action_during_lockout", "quarantine"))
        self.weights = dict(self.policy.get("weights", {}))

        # Log-Pfade (überschreibbar per CLI)
        self.security_log_path = security_log_path or self.policy.get("security_log_path", "logs/security.log")
        self.audit_log_path = audit_log_path or self.policy.get("audit_log_path", "logs/security_audit.jsonl")

        os.makedirs(os.path.dirname(self.security_log_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.audit_log_path), exist_ok=True)

        # Datenstrukturen für das Analysefenster
        self._events: Deque[SecurityEvent] = collections.deque()
        self._lock = threading.Lock()
        self._lockout_until: float = 0.0
        self._consecutive_fail = 0

        # Logger für sicherheitsrelevante Ereignisse
        self._logger = logging.getLogger("security")
        self._logger.setLevel(logging.INFO)
        # Verhindert, dass Meldungen zusätzlich noch über den Root-Logger dupliziert werden
        self._logger.propagate = False

        # File-/Stream-Handler nur einmal hinzufügen
        # (sonst bei mehrfacher Instanzierung doppelte Logs)
        if not self._logger.handlers:
            handlers = []

            # FileHandler für das Security-Log
            fh = logging.FileHandler(self.security_log_path, encoding="utf-8")
            fh.setLevel(logging.INFO)
            handlers.append(fh)

            # Konsolen-Handler für Realtime-Ausgabe im Terminal
            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)
            handlers.append(ch)

            # Gemeinsames Format für alle Handler
            fmt = logging.Formatter(
                fmt="%(asctime)s [%(levelname)s] %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S"
            )
            for h in handlers:
                h.setFormatter(fmt)
                self._logger.addHandler(h)

        # Audit-Datei (JSONL) für maschinenlesbare Auswertung
        self._audit_fp = open(self.audit_log_path, "a", encoding="utf-8")

    def __del__(self):
        """Sicheres Schließen der Audit-Datei."""
        try:
            self._audit_fp.close()
        except Exception:
            pass

    # ----------------------------------------------------------
    # Öffentliche API
    # ----------------------------------------------------------

    def is_locked(self) -> bool:
        """True, wenn sich das System aktuell im Lockout befindet."""
        return time.time() < self._lockout_until

    def action_when_locked(self) -> str:
        """Rückgabe des in der Policy definierten Verhaltens."""
        return self.action_during_lockout

    def on_packet_before_verify(self, meta: Dict[str, Any]) -> bool:
        """
        Wird VOR der HMAC-Verifikation aufgerufen.
        Gibt zurück:
            True  – Paket darf verifiziert werden
            False – Paket wird sofort nach Policy behandelt (Lockout aktiv)
        """
        if self.is_locked():
            self._audit("lockout_drop", ok=False, reason="lockout_active", meta=meta)
            return False
        return True

    def on_verification_result(self, ok: bool, reason: str, meta: Dict[str, Any]):
        """
        Wird NACH der HMAC-Verifikation aufgerufen.
        Registriert das Ereignis, aktualisiert die Fensterstatistik
        und prüft, ob ein Lockout ausgelöst werden muss.
        """

        now = time.time()
        ev = SecurityEvent(ts=now, ok=ok, reason=(reason if not ok else "ok"), meta=meta)

        with self._lock:
            self._events.append(ev)
            self._trim_window(now)

            # Aktualisierung der "consecutive fails"
            if ok:
                self._consecutive_fail = 0
            else:
                self._consecutive_fail += 1

            # Prüfen, ob Lockout ausgelöst wird
            if self._should_lock(now):
                self._enable_lockout(now, trigger=reason)

        # Security-Log (lesbares Log)
        level = logging.INFO if ok else logging.WARNING
        self._logger.log(level, f"verify_result ok={ok} reason={reason} meta={self._safe_meta(meta)}")

        # Audit-Log (JSONL)
        self._audit("verify_result", ok=ok, reason=reason, meta=meta)

    # ----------------------------------------------------------
    # Interne Logik
    # ----------------------------------------------------------

    def _trim_window(self, now: float):
        """Entfernt alte Ereignisse außerhalb des Analysefensters."""
        border = now - self.window_seconds
        while self._events and self._events[0].ts < border:
            self._events.popleft()

    def _weighted_fail_ratio(self) -> float:
        """
        Berechnet die gewichtete Fehlerrate:
            Summe(Fehlergewicht) / Summe(Gewichte aller Events)
        """
        if not self._events:
            return 0.0

        total_w = 0.0
        fail_w = 0.0

        for ev in self._events:
            w = 1.0
            if not ev.ok:
                w = float(self.weights.get(ev.reason, 1.0))
                fail_w += w
            total_w += w

        return (fail_w / total_w) if total_w > 0 else 0.0

    def _should_lock(self, now: float) -> bool:
        """
        Entscheidet, ob ein Lockout ausgelöst werden soll.
        Basierend auf:
            • Anzahl aufeinanderfolgender Fehler
            • gewichteter Fehlerrate
            • Cooldown-Verhalten
        """

        # Sofort-Lockout bei X Fehlern hintereinander
        if self._consecutive_fail >= self.consecutive_fail_threshold:
            return True

        # Untergrenze für Fenstergröße
        if len(self._events) < self.min_events_in_window:
            return False

        # Cooldown: System reagiert weniger empfindlich
        cooldown_factor = 1.0
        if 0 < (now - self._lockout_until) < self.cooldown_seconds:
            cooldown_factor = 0.2

        ratio = self._weighted_fail_ratio()
        return ratio >= (self.max_fail_ratio * (1.0 + cooldown_factor))

    def _enable_lockout(self, now: float, trigger: str):
        """Aktiviert einen Lockout und protokolliert ihn."""
        self._lockout_until = now + self.lockout_seconds
        self._consecutive_fail = 0

        self._logger.error(f"SECURITY LOCKOUT enabled for {self.lockout_seconds}s (trigger={trigger})")
        self._audit("lockout_enabled", ok=False, reason=trigger, meta={"until": self._lockout_until})

    # ----------------------------------------------------------
    # Logging / Audit
    # ----------------------------------------------------------

    def _audit(self, event: str, ok: bool, reason: str, meta: Dict[str, Any]):
        """Schreibt einen Datensatz in das Audit-JSONL."""
        rec = {
            "ts": time.time(),
            "event": event,
            "ok": ok,
            "reason": reason,
            "meta": meta,
        }
        self._audit_fp.write(json.dumps(rec, ensure_ascii=False) + "\n")
        self._audit_fp.flush()

    @staticmethod
    def _safe_meta(meta: Dict[str, Any]) -> Dict[str, Any]:
        """
        Bereinigt Metadaten von sensiblen Feldern
        (z. B. HMAC-Key, Geheimnisse), bevor sie ins Log gehen.
        """
        keys_to_strip = {"hmac", "secret", "key"}
        return {k: ("***" if k in keys_to_strip else v) for k, v in meta.items()}
