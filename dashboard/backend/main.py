import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from dashboard.backend.config import MODEL_PATH
from dashboard.backend.routers.analysis import router as analysis_router
from dashboard.backend.routers.stream import router as stream_router
from dashboard.backend.routers.telemetry import router as telemetry_router
from dashboard.backend.services.ai_analyst import AIAnalyst
from dashboard.backend.services.model_loader import load_model

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Modell genau einmal beim Start laden (~36 s auf Intel-CPU).
    # Fehlt die Datei, läuft das Monitoring trotzdem; /analyse meldet dann
    # explizit 503 statt still zu scheitern.
    if MODEL_PATH.exists():
        app.state.analyst = AIAnalyst(load_model(str(MODEL_PATH)))
        logger.info("KI-Modell geladen: %s", MODEL_PATH)
    else:
        app.state.analyst = None
        logger.warning("KI-Modell nicht gefunden: %s – /analyse deaktiviert", MODEL_PATH)
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(telemetry_router)
app.include_router(stream_router)
app.include_router(analysis_router)

# Muss nach den Routern stehen, sonst fängt "/" alle Pfade ab
app.mount("/", StaticFiles(directory="dashboard/frontend", html=True), name="frontend")