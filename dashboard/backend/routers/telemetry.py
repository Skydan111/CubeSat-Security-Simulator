from fastapi import APIRouter
from dashboard.backend.services.csv_reader import read_all, read_latest, read_last_n


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

    temps = [p.temperature_c for p in packets]
    min_temp = min(temps)
    max_temp = max(temps)
    avg_temp = round(sum(temps) / len(temps), 2)

    hum = [p.humidity_pct for p in packets]
    min_hum = min(hum)
    max_hum = max(hum)
    avg_hum = round(sum(hum) / len(hum), 2)

    press = [p.pressure_hpa for p in packets]
    min_press = min(press)
    max_press = max(press)
    avg_press = round(sum(press) / len(press), 2)

    return {
            "temperature": {"min": min_temp, "max": max_temp, "avg": avg_temp},
            "humidity":    {"min": min_hum,  "max": max_hum,  "avg": avg_hum},
            "pressure":    {"min": min_press,"max": max_press,"avg": avg_press},
        }


