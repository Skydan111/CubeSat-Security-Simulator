from fastapi import FastAPI
from dashboard.backend.routers.telemetry import router as telemetry_router
from dashboard.backend.routers.stream import router as stream_router

app = FastAPI()

app.include_router(telemetry_router)
app.include_router(stream_router)

