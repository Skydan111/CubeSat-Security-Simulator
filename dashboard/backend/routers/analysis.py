"""KI-Analyse-Endpoint.

Bewusst `def` statt `async def`: Die CPU-Inferenz blockiert ~1 Minute.
FastAPI führt sync-Endpoints in einem Threadpool aus, dadurch laufen
SSE-Stream und andere Endpoints während der Analyse weiter.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from dashboard.backend.services.ai_analyst import AnalysisUnavailable
from dashboard.backend.services.csv_reader import read_last_n

router = APIRouter()

# Mehr als genug für das 30-Minuten-Fenster bei 1 Paket/Minute;
# die zeitbasierte Auswahl passiert im prompt_builder.
PACKETS_TO_READ = 60


@router.post("/analyse")
def analyse(request: Request):
    analyst = request.app.state.analyst
    if analyst is None:
        raise HTTPException(status_code=503, detail="KI-Modell nicht verfügbar.")

    try:
        report = analyst.analyse(read_last_n(PACKETS_TO_READ))
    except AnalysisUnavailable as e:
        raise HTTPException(status_code=409, detail=str(e))

    return {
        "report": report,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }