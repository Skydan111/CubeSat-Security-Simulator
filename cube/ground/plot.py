#!/usr/bin/env python3
"""
Mission View — Bodenstations-Telemetrie-Monitor (robuster)

- Liest Telemetrie aus CSV (Schema A: ts,temperature_c,humidity_pct,pressure_hpa,...
                         oder Schema B: ts,temperature,humidity,pressure,...)
- Zeichnet drei Diagramme (Temperatur / Luftfeuchtigkeit / Luftdruck)
- Modi: --once (einmal) oder Live (Standard)
- Flags: --csv (Pfad), --interval, --window, --save (PNG-Snapshot)
"""

import argparse
import time
import pathlib
from typing import Tuple, Dict

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


DEFAULT_CSV = pathlib.Path("cube/data/raw/telemetry.csv")

# akzeptierte Spaltennamen (beide Schemata)
COL_MAP_CANDIDATES: Dict[str, Tuple[str, ...]] = {
    "temperature": ("temperature", "temperature_c", "temp", "temp_c"),
    "humidity": ("humidity", "humidity_pct", "hum", "rh", "rh_pct"),
    "pressure": ("pressure", "pressure_hpa", "press", "press_hpa"),
}


def _resolve_columns(df: pd.DataFrame) -> Dict[str, str]:
    """Finde passende Spaltennamen im df für temperature/humidity/pressure."""
    resolved = {}
    cols = {c.lower(): c for c in df.columns}  # lowercase->original
    for canonical, candidates in COL_MAP_CANDIDATES.items():
        for cand in candidates:
            if cand in cols:
                resolved[canonical] = cols[cand]
                break
        if canonical not in resolved:
            raise SystemExit(
                f"[ERR] Erwartete Spalten nicht gefunden. "
                f"Brauchbar sind z.B. {COL_MAP_CANDIDATES[canonical]} — vorhanden: {list(df.columns)}"
            )
    return resolved


def load_df(csv_path: pathlib.Path) -> pd.DataFrame:
    """Lädt die CSV-Datei und gibt normalisierte Spalten zurück."""
    if not csv_path.exists():
        raise SystemExit(f"[ERR] Telemetrie-Datei nicht gefunden: {csv_path}")

    try:
        df = pd.read_csv(csv_path, parse_dates=["ts"])
    except ValueError as e:
        # Falls 'ts' anders heißt (крайний случай) — сообщаем явно
        raise SystemExit(f"[ERR] Konnte 'ts' nicht parsen: {e}")

    if df.empty:
        return df

    # Sortieren, Spalten auflösen, numerische Typen erzwingen
    df = df.sort_values("ts").dropna(subset=["ts"])
    col = _resolve_columns(df)

    for k in ("temperature", "humidity", "pressure"):
        df[col[k]] = pd.to_numeric(df[col[k]], errors="coerce")

    df = df.dropna(subset=[col["temperature"], col["humidity"], col["pressure"]])

    # Einheitliche Alias-Spalten für Plot
    df = df.rename(columns={
        col["temperature"]: "temperature_norm",
        col["humidity"]: "humidity_norm",
        col["pressure"]: "pressure_norm",
    })
    return df


def _format_time_axis(ax):
    locator = mdates.AutoDateLocator()
    formatter = mdates.ConciseDateFormatter(locator)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)


def draw_once(df: pd.DataFrame, title: str = "CubeSat Telemetrie – Bodenstationsansicht", save_path: pathlib.Path = None):
    """Zeichnet eine statische Telemetrie-Grafik (einmalige Ansicht)."""
    fig, axes = plt.subplots(3, 1, sharex=True, figsize=(9, 7))
    fig.suptitle(title, fontsize=14)

    axes[0].plot(df["ts"], df["temperature_norm"], label="Temperatur (°C)")
    axes[0].set_ylabel("°C")
    axes[0].legend(loc="upper left")
    axes[0].grid(True, linestyle="--", alpha=0.4)

    axes[1].plot(df["ts"], df["humidity_norm"], label="Luftfeuchtigkeit (%)")
    axes[1].set_ylabel("%")
    axes[1].legend(loc="upper left")
    axes[1].grid(True, linestyle="--", alpha=0.4)

    axes[2].plot(df["ts"], df["pressure_norm"], label="Luftdruck (hPa)")
    axes[2].set_ylabel("hPa")
    axes[2].legend(loc="upper left")
    axes[2].grid(True, linestyle="--", alpha=0.4)

    axes[2].set_xlabel("Zeit (UTC)")
    _format_time_axis(axes[2])
    fig.autofmt_xdate()
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)
        print(f"[INFO] Snapshot gespeichert: {save_path}")

    plt.show()


def live_loop(csv_path: pathlib.Path, interval_sec: float = 2.0, window: int = 300, save_path: pathlib.Path = None):
    """
    Aktualisiert die Diagramme alle interval_sec Sekunden.
    window – Anzahl der letzten Datenpunkte, die angezeigt werden (für Lesbarkeit).
    """
    plt.ion()
    fig, axes = plt.subplots(3, 1, sharex=True, figsize=(9, 7))
    fig.suptitle("CubeSat Telemetrie – LIVE", fontsize=14)

    last_mtime = None
    last_rows = 0

    try:
        while True:
            if not csv_path.exists():
                print(f"[WARN] Datei fehlt (warte): {csv_path}")
                plt.pause(interval_sec)
                continue

            mtime = csv_path.stat().st_mtime
            need_redraw = (mtime != last_mtime)

            if not need_redraw:
                # Keine Änderung — sanft weiter
                plt.pause(interval_sec)
                continue

            df = load_df(csv_path)

            if df.empty:
                for ax in axes:
                    ax.cla()
                    ax.text(0.5, 0.5, "Keine Daten", ha="center", va="center", transform=ax.transAxes)
                plt.pause(interval_sec)
                last_mtime = mtime
                last_rows = 0
                continue

            # Begrenzung auf die letzten N Messpunkte
            if len(df) > window:
                df = df.iloc[-window:]

            for ax in axes:
                ax.cla()

            axes[0].plot(df["ts"], df["temperature_norm"], label="Temperatur (°C)")
            axes[0].set_ylabel("°C")
            axes[0].legend(loc="upper left")
            axes[0].grid(True, linestyle="--", alpha=0.4)

            axes[1].plot(df["ts"], df["humidity_norm"], label="Luftfeuchtigkeit (%)")
            axes[1].set_ylabel("%")
            axes[1].legend(loc="upper left")
            axes[1].grid(True, linestyle="--", alpha=0.4)

            axes[2].plot(df["ts"], df["pressure_norm"], label="Luftdruck (hPa)")
            axes[2].set_ylabel("hPa")
            axes[2].legend(loc="upper left")
            axes[2].grid(True, linestyle="--", alpha=0.4)

            axes[2].set_xlabel("Zeit (UTC)")
            _format_time_axis(axes[2])
            fig.autofmt_xdate()
            plt.tight_layout()

            if save_path:
                plt.savefig(save_path, dpi=150)

            last_mtime = mtime
            last_rows = len(df)
            plt.pause(interval_sec)

    except KeyboardInterrupt:
        print("\n[GROUND] Live-Ansicht vom Benutzer gestoppt.")
    finally:
        plt.ioff()
        plt.show()


def main():
    parser = argparse.ArgumentParser(description="Bodenstations-Telemetrie-Monitor")
    parser.add_argument("--csv", type=pathlib.Path, default=DEFAULT_CSV, help="Pfad zur Telemetrie-CSV")
    parser.add_argument("--once", action="store_true", help="einmalige Darstellung und beenden")
    parser.add_argument("--interval", type=float, default=2.0, help="Aktualisierungsintervall (Sekunden) im Live-Modus")
    parser.add_argument("--window", type=int, default=300, help="Zeige die letzten N Messpunkte im Live-Modus")
    parser.add_argument("--save", type=pathlib.Path, help="Optional: Pfad zum Speichern eines PNG-Snapshots")
    args = parser.parse_args()

    df = load_df(args.csv)
    if df.empty and args.once:
        raise SystemExit("[ERR] Telemetrie-Datei ist leer. Bitte OBC-Logger zuerst starten.")

    if args.once:
        draw_once(df, save_path=args.save)
    else:
        live_loop(csv_path=args.csv, interval_sec=args.interval, window=args.window, save_path=args.save)


if __name__ == "__main__":
    main()
