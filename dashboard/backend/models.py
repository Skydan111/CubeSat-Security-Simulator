from pydantic import BaseModel
from datetime import datetime

class TelemetryPacket(BaseModel):
    ts: datetime
    temperature_c: float
    humidity_pct: float
    pressure_hpa: float
    mode: str
    sig: str