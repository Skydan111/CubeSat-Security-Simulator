"""
packet_pipeline.py – Datenverarbeitung + Adaptive Security.
"""

from pathlib import Path
import datetime
from typing import Optional, Tuple, Dict, Any
from ground.config.paths import PROC_PATH, REJ_PATH
from ground.verify import verify_with_config
from ground.io_utils import append_line



def split_payload_mac(line: str) -> Tuple[bytes, str]:
    """
    Trennt Payload und MAC anhand des letzten Kommas.
    Liefert (payload_bytes, mac_hex) oder wirft ValueError mit Grundcode.
    """
    try:
        payload, mac = line.rsplit(",", 1)
    except ValueError:
        raise ValueError("no_mac_delimiter")
    mac = mac.strip()
    if not mac:
        raise ValueError("empty_mac")
    return payload.encode("utf-8"), mac

def is_header(line: str) -> bool:
    """Erkennt CSV-Header anhand des Beginns mit 'ts,'."""
    return line.lower().startswith("ts,")

def check_lockout(
        pkt_id: str,
        line: str,
        meta: Dict[str, Any],
        secman: Optional[object] = None,
        quarantine_path: Optional[Path] = None) -> bool:
    if secman and hasattr(secman, "on_packet_before_verify"):
        if not secman.on_packet_before_verify(meta):
            action = getattr(secman, "action_when_locked", lambda: "reject")()
            reason = "lockout_active"
            if action == "drop":
                print(f"[LOCKED] dropped id={pkt_id}")
                return False
            elif action == "quarantine":
                qpath = quarantine_path or Path("data/quarantine/telemetry.csv")
                append_line(qpath, line.rstrip() + f",reason={reason}")
                print(f"[LOCKED] quarantined id={pkt_id}")
                return False
            else:
                append_line(REJ_PATH, line.rstrip() + f",reason={reason}")
                print(f"[LOCKED] rejected id={pkt_id}")
                return False
    return True


def handle_line(
    line: str,
    secman: Optional[object] = None,
    source: str = "unknown",
    quarantine_path: Optional[Path] = None
) -> None:
    """
    Verarbeitet eine einzelne Telemetrie-Zeile:
      • optionaler Lockout-Check (Adaptive Security) vor Verify,
      • Verify (HMAC),
      • Routing: PROCESSED oder REJECTED (oder QUARANTINE bei aktivem Lockout).
    Mutiert die Eingabezeile nicht (für Debug/Forensik).
    """
    if not line.strip():
        return

    pkt_id = (line.split(",", 1)[0] or f"ts-{int(datetime.datetime.now(datetime.UTC).timestamp())}").strip()
    meta = {"source": source, "packet_id": pkt_id, "len": len(line)}

    # 0) Lockout vor Verify prüfen
    if not check_lockout(pkt_id, line, meta, secman, quarantine_path):
        return


    # 1) Verify HMAC (mit differenzierten Fehlercodes)
    verify_reason = "ok"
    rej_line = None
    try:
        payload, mac = split_payload_mac(line)
        ok = verify_with_config(payload, mac)
        if not ok:
            verify_reason = "invalid_signature"
    except Exception as e:
        ok = False
        verify_reason = "malformed_packet"
        rej_line = line.rstrip() + f",verify_error={e}"

    # 2) Ergebnis an SecurityManager melden (Fenster/Auslöser/Lockout)
    if secman and hasattr(secman, "on_verification_result"):
        secman.on_verification_result(ok=ok, reason=verify_reason, meta=meta)

    # 3) Schreiben in Ziel (ohne doppelte RAW-Einträge)
    if ok:
        append_line(PROC_PATH, line)
        print("[OK] processed")
    else:
        out_line = rej_line or (line if "reason=" in line else line.rstrip() + f",reason={verify_reason}")
        append_line(REJ_PATH, out_line)
        print(f"[REJECTED] {verify_reason}")

def handle_verified_line(
    line: str,
    secman: Optional[object] = None,
    source: str = "unknown",
    quarantine_path: Optional[Path] = None
) -> None:
    """
    Verarbeitet eine bereits verifizierte Telemetrie-Zeile (Signatur wurde extern geprüft).
    Beibehält Lockout-Logik und Pipeline-Routing (PROCESSED / QUARANTINE / REJECTED).
    """
    if not line.strip():
        return

    pkt_id = (line.split(",", 1)[0] or f"ts-{int(datetime.datetime.now(datetime.UTC).timestamp())}").strip()
    meta = {"source": source, "packet_id": pkt_id, "len": len(line), "transport": "mqtt"}

    # 0) Lockout vor Verarbeitung prüfen (wie in handle_line)
    if not check_lockout(pkt_id, line, meta, secman, quarantine_path):
        return

    # 1) SecurityManager informieren: ok=true (weil Signatur schon geprüft wurde)
    if secman and hasattr(secman, "on_verification_result"):
        secman.on_verification_result(ok=True, reason="ok", meta=meta)

    # 2) Routing: verifizierte Zeile -> PROCESSED
    append_line(PROC_PATH, line)
    print("[OK] processed (mqtt)")