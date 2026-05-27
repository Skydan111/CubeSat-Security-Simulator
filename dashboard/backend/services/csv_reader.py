import csv
from ground.config.paths import PROC_PATH
from dashboard.backend.models import TelemetryPacket
from collections import deque




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

def read_last_n(n: int = 60) -> list[TelemetryPacket]:
    with open(PROC_PATH, newline="") as f:
        reader = csv.DictReader(f)
        last_n = deque(reader, maxlen=n)
    return [TelemetryPacket(**row) for row in last_n]
