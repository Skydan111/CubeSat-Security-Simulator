from pathlib import Path

THRESHOLDS = {
    "temperature_c": {"min": 2.0, "max": 8.0},
    "humidity_pct":  {"min": 30.0, "max": 70.0},
    "pressure_hpa":  {"min": 940.0, "max": 1020.0},
}
LOCAL_TZ = "Europe/Berlin"
BUSINESS_HOURS = (6, 20)      # Betriebszeit 06:00–20:00 Lokalzeit
ANALYSIS_WINDOW_MIN = 30      # Analysezeitraum wie im Trainingsdatensatz
MAX_DATA_AGE_MIN = 5          # älter → keine Analyse (fail-secure)
MIN_DATA_POINTS = 10          # weniger → keine Analyse (Modell kennt nur 30/120 Punkte)
MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "warehouse_model.gguf"