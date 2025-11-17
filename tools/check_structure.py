#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check-Skript für das CubeSat Ground-Projekt

Zweck:
  • Prüft Projektstruktur (Verzeichnisse/Dateien)
  • Prüft wichtige Python-Imports (cube.ground, SecurityManager)
  • Prüft, ob Security-Policy geladen werden kann
  • Optional: versucht, einen SecurityManager zu instanzieren

Das Skript ist nur für die Entwicklungs-/Testumgebung gedacht.
"""

from __future__ import annotations

import sys
from pathlib import Path
from importlib import import_module


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _status(ok: bool, msg: str) -> None:
    prefix = "[OK] " if ok else "[ERR]"
    print(f"{prefix} {msg}")


def check_paths_and_files() -> bool:
    ok_all = True

    print("=== Struktur-Check ===")
    cfg = PROJECT_ROOT / "configs" / "security_policy.yaml"
    sm_py = PROJECT_ROOT / "ground_station" / "security_manager.py"
    recv_py = PROJECT_ROOT / "cube" / "ground" / "receiver.py"
    logs_dir = PROJECT_ROOT / "logs"
    quar_dir = PROJECT_ROOT / "data" / "quarantine"
    raw_dir = PROJECT_ROOT / "data" / "raw"
    proc_dir = PROJECT_ROOT / "data" / "processed"
    rej_dir = PROJECT_ROOT / "data" / "rejected"

    for p, desc in [
        (cfg, "configs/security_policy.yaml vorhanden"),
        (sm_py, "ground_station/security_manager.py vorhanden"),
        (recv_py, "cube/ground/receiver.py vorhanden"),
        (logs_dir, "logs/ Verzeichnis vorhanden (für Security-Logs)"),
        (quar_dir, "data/quarantine/ Verzeichnis vorhanden (für Quarantäne)"),
        (raw_dir, "data/raw/ Verzeichnis vorhanden"),
        (proc_dir, "data/processed/ Verzeichnis vorhanden"),
        (rej_dir, "data/rejected/ Verzeichnis vorhanden"),
    ]:
        if p.exists():
            _status(True, desc)
        else:
            _status(False, f"{desc} – FEHLT: {p}")
            ok_all = False

    return ok_all


def check_imports() -> bool:
    ok_all = True
    print("\n=== Import-Check ===")

    # Projektwurzel auf sys.path legen, damit 'cube' und 'ground_station' gefunden werden.
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

    # 1) cube.ground.config.paths
    try:
        paths_mod = import_module("cube.ground.config.paths")
        for attr in ("RAW_PATH", "PROC_PATH", "REJ_PATH", "CSV_HEADER"):
            assert hasattr(paths_mod, attr), f"Attribut {attr} fehlt"
        _status(True, "Import cube.ground.config.paths (RAW/PROC/REJ/CSV_HEADER) ok")
    except Exception as e:
        _status(False, f"Import cube.ground.config.paths fehlgeschlagen: {e}")
        ok_all = False

    # 2) cube.ground.verify
    try:
        verify_mod = import_module("cube.ground.verify")
        verify_fn = getattr(verify_mod, "verify_with_config", None)
        if callable(verify_fn):
            _status(True, "Import cube.ground.verify.verify_with_config ok")
        else:
            raise RuntimeError("verify_with_config ist nicht callable oder fehlt")
    except Exception as e:
        _status(False, f"Import cube.ground.verify fehlgeschlagen: {e}")
        ok_all = False

    # 3) ground_station.security_manager + pyyaml
    try:
        yaml_mod = import_module("yaml")
        _ = yaml_mod  # nur um sicherzugehen, dass Import klappt
        _status(True, "Import yaml (PyYAML) ok")
    except Exception as e:
        _status(False, f"Import yaml fehlgeschlagen (PyYAML installieren?): {e}")
        ok_all = False

    try:
        sm_mod = import_module("ground_station.security_manager")
        SecurityManager = getattr(sm_mod, "SecurityManager", None)
        if SecurityManager is None:
            raise RuntimeError("Klasse SecurityManager fehlt")
        _status(True, "Import ground_station.security_manager.SecurityManager ok")
    except Exception as e:
        _status(False, f"Import ground_station.security_manager fehlgeschlagen: {e}")
        ok_all = False

    return ok_all


def check_security_manager_instance() -> bool:
    """
    Versucht, einen SecurityManager mit der echten Policy zu instanzieren.
    Erstellt dabei ggf. logs/-Verzeichnis und Audit-Datei.
    """
    print("\n=== SecurityManager-Instanzierung ===")
    try:
        sys.path.insert(0, str(PROJECT_ROOT))
        sm_mod = import_module("ground_station.security_manager")
        SecurityManager = getattr(sm_mod, "SecurityManager")
        policy_path = PROJECT_ROOT / "configs" / "security_policy.yaml"
        sm = SecurityManager(str(policy_path))
        _ = sm  # nur um "unused" zu vermeiden
        _status(True, f"SecurityManager erfolgreich mit Policy geladen: {policy_path}")
        return True
    except Exception as e:
        _status(False, f"SecurityManager konnte nicht instanziert werden: {e}")
        return False


def main() -> int:
    print(f"Projektwurzel: {PROJECT_ROOT}\n")

    ok_struct = check_paths_and_files()
    ok_imports = check_imports()
    ok_sm = check_security_manager_instance()

    print("\n=== Zusammenfassung ===")
    if ok_struct and ok_imports and ok_sm:
        _status(True, "Struktur, Importe und SecurityManager sehen gut aus. ✅")
        return 0
    else:
        _status(False, "Es gibt Probleme (siehe Meldungen oben). ❌")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
