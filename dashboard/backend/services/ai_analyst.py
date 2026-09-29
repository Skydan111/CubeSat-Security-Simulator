"""Fassade für die KI-Analyse: Validierung → Prompt → Chat-Template → Generierung.

Der Endpoint kennt nur diese Klasse. Modell-Laden (model_loader) und
Prompt-Format (prompt_builder) bleiben dahinter verborgen.
"""
import threading
from datetime import datetime, timedelta, timezone

from llama_cpp import Llama

from dashboard.backend.config import MAX_DATA_AGE_MIN, MIN_DATA_POINTS
from dashboard.backend.models import TelemetryPacket
from dashboard.backend.services.prompt_builder import build_prompt, select_window

# Llama-3-Chat-Template exakt wie beim Fine-Tuning (ohne System-Prompt).
# <|begin_of_text|> fehlt bewusst: llama-cpp fügt das BOS-Token selbst hinzu,
# sonst stünde es doppelt am Anfang.
_TEMPLATE = (
    "<|start_header_id|>user<|end_header_id|>\n\n"
    "{content}<|eot_id|>"
    "<|start_header_id|>assistant<|end_header_id|>\n\n"
)

MAX_TOKENS = 768      # Berichte im Datensatz: ~400–600 Tokens
TEMPERATURE = 0.3     # niedrig = sachlich und reproduzierbar


class AnalysisUnavailable(Exception):
    """Analyse wird bewusst verweigert (fail-secure), z. B. veraltete Daten."""


class AIAnalyst:
    def __init__(self, llm: Llama):
        self._llm = llm
        # Llama-Objekt ist nicht thread-safe → immer nur eine Generierung gleichzeitig
        self._lock = threading.Lock()

    def analyse(self, packets: list[TelemetryPacket], now: datetime | None = None) -> str:
        """Blockierend (CPU-Inferenz dauert). Im Endpoint nicht im Event-Loop aufrufen."""
        if not packets:
            raise AnalysisUnavailable("Keine Telemetriedaten vorhanden.")

        now = now or datetime.now(timezone.utc)
        age = now - packets[-1].ts
        if age > timedelta(minutes=MAX_DATA_AGE_MIN):
            raise AnalysisUnavailable(
                f"Letzte Messung ist {int(age.total_seconds() // 60)} Minuten alt – "
                "keine aktuellen Daten für eine Analyse."
            )

        window = select_window(packets)
        if len(window) < MIN_DATA_POINTS:
            raise AnalysisUnavailable(
                f"Zu wenige Messdaten ({len(window)} von mindestens {MIN_DATA_POINTS})."
            )

        prompt = _TEMPLATE.format(content=build_prompt(window))

        with self._lock:
            result = self._llm(
                prompt,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                stop=["<|eot_id|>"],
            )
        return result["choices"][0]["text"].strip()