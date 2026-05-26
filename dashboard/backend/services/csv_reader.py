import csv
from ground.config.paths import PROC_PATH
from dashboard.backend.models import TelemetryPacket




def read_all() -> list[TelemetryPacket]:
    packets = []
    with open(PROC_PATH, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            packet = TelemetryPacket(**row)
            packets.append(packet)
    return packets

def read_latest() -> TelemetryPacket | None:
    with open(PROC_PATH, newline="") as f:
        reader = csv.DictReader(f)
        last = None
        for row in reader:
            last = TelemetryPacket(**row)
        return last
