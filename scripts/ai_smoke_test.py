"""Manueller End-to-End-Test der KI-Analyse ohne FastAPI und ohne Raspberry Pi.

Nutzt echte historische Daten aus dem CSV (25.05.2026, 12:39–12:49 UTC, 11 Messpunkte).
`now` wird auf den Zeitpunkt der letzten Messung gesetzt, damit die
Frische-Prüfung historische Daten akzeptiert.

Aufruf aus dem Projektroot:  python scripts/ai_smoke_test.py
"""
import time
from datetime import datetime, timezone

from dashboard.backend.config import MODEL_PATH
from dashboard.backend.services.ai_analyst import AIAnalyst
from dashboard.backend.services.csv_reader import read_all
from dashboard.backend.services.model_loader import load_model
from dashboard.backend.services.prompt_builder import build_prompt

CUTOFF = datetime(2026, 5, 25, 12, 50, tzinfo=timezone.utc)

packets = [p for p in read_all() if p.ts <= CUTOFF]

print("=== Prompt ===")
print(build_prompt(packets))

print("\n=== Modell wird geladen ===")
t0 = time.time()
analyst = AIAnalyst(load_model(str(MODEL_PATH)))
print(f"Geladen in {time.time() - t0:.1f} s")

print("\n=== Generierung läuft (auf Intel-CPU evtl. mehrere Minuten) ===")
t0 = time.time()
report = analyst.analyse(packets, now=packets[-1].ts)
print(f"Fertig in {time.time() - t0:.1f} s\n")
print(report)