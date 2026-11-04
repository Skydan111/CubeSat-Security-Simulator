from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict


@dataclass(frozen=True)
class GuardConfig:
    # Dedup: Anzahl der zuletzt gesehenen msg_id pro sat_id.
    dedup_size: int = 500
    # Freshness: erlaubte Zeitabweichung in Sekunden (Replay/Clock Skew Schutz).
    max_skew_seconds: int = 120


class DedupLRU:
    def __init__(self, max_size: int) -> None:
        self._max_size = max_size
        self._lru: "OrderedDict[str, None]" = OrderedDict()

    def seen_before(self, msg_id: str) -> bool:
        # Prüft, ob msg_id bereits gesehen wurde und aktualisiert LRU.
        if msg_id in self._lru:
            self._lru.move_to_end(msg_id)
            return True
        self._lru[msg_id] = None
        if len(self._lru) > self._max_size:
            self._lru.popitem(last=False)
        return False


class MqttMessageGuard:
    def __init__(self, cfg: GuardConfig) -> None:
        self._cfg = cfg
        self._dedup_by_sat: Dict[str, DedupLRU] = {}

    def is_duplicate(self, sat_id: str, msg_id: str) -> bool:
        # Dedup pro Satellite-ID.
        cache = self._dedup_by_sat.get(sat_id)
        if cache is None:
            cache = DedupLRU(self._cfg.dedup_size)
            self._dedup_by_sat[sat_id] = cache
        return cache.seen_before(msg_id)

    def is_fresh(self, ts_utc: str) -> bool:
        # Prüft, ob ts_utc innerhalb des erlaubten Zeitfensters liegt.
        # Erwartetes Format: ISO-8601 mit 'Z' oder +00:00.
        msg_time = _parse_utc(ts_utc)
        now = datetime.now(timezone.utc)
        skew = abs((now - msg_time).total_seconds())
        return skew <= self._cfg.max_skew_seconds


def _parse_utc(ts_utc: str) -> datetime:
    # Parst ISO-8601 UTC Timestamp.
    s = ts_utc.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        # Falls tz fehlt, erzwingen wir UTC (defensiv).
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)