from fastapi import APIRouter
from dashboard.backend.services.csv_reader import read_all, read_latest, read_last_n
from dashboard.backend.config import THRESHOLDS


router = APIRouter(prefix="/telemetry")

@router.get("/history")
def get_history():
    return read_all()

@router.get("/latest")
def get_latest():
    return read_latest()

@router.get("/stats")
def get_stats():
    packets = read_last_n(60)
    return {
        "temperature": _summary([p.temperature_c for p in packets]),
        "humidity":    _summary([p.humidity_pct for p in packets]),
        "pressure":    _summary([p.pressure_hpa for p in packets]),
    }


def _summary(values: list[float]) -> dict:
    """Min/Max/Avg; ohne Daten None-Werte statt Exception (fail-secure)."""
    if not values:
        return {"min": None, "max": None, "avg": None}
    return {"min": min(values), "max": max(values), "avg": round(sum(values) / len(values), 2)}


@router.get("/thresholds")
def get_thresholds():
    return THRESHOLDS

