from fastapi import FastAPI
from dashboard.backend.routers.telemetry import router as telemetry_router

app = FastAPI()

app.include_router(telemetry_router)

