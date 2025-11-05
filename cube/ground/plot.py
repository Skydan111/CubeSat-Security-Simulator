#!/usr/bin/env python3
"""
Mission View — Bodenstations-Telemetrie-Monitor

Funktionen:
- Liest cube/data/telemetry.csv
- Zeichnet drei Diagramme (Temperatur / Luftfeuchtigkeit / Luftdruck)
- Modi: Einmalige Darstellung (--once) oder Live-Modus (Standard)
"""

import argparse
import time
import pathlib
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

CSV_PATH = pathlib.Path("cube/data/telemetry.csv")


def load_df() -> pd.DataFrame:
    """Lädt die CSV-Datei und gibt sie als DataFrame zurück."""
    if not CSV_PATH.exists():
        raise SystemExit(f"[ERR] Telemetrie-Datei nicht gefunden: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH, parse_dates=["ts"])
    if df.empty:
        return df
    df = df.sort_values("ts")
    return df


def draw_once(df: pd.DataFrame):
    """Zeichnet eine statische Telemetrie-Grafik (einmalige Ansicht)."""
    fig, axes = plt.subplots(3, 1, sharex=True, figsize=(9, 7))
    fig.suptitle("CubeSat Telemetrie – Bodenstationsansicht", fontsize=14)

    # Temperatur
    axes[0].plot(df["ts"], df["temperature"], label="Temperatur (°C)")
    axes[0].set_ylabel("°C")
    axes[0].legend(loc="upper left")
    axes[0].grid(True, linestyle="--", alpha=0.4)

    # Luftfeuchtigkeit
    axes[1].plot(df["ts"], df["humidity"], label="Luftfeuchtigkeit (%)")
    axes[1].set_ylabel("%")
    axes[1].legend(loc="upper left")
    axes[1].grid(True, linestyle="--", alpha=0.4)

    # Luftdruck
    axes[2].plot(df["ts"], df["pressure"], label="Luftdruck (hPa)")
    axes[2].set_ylabel("hPa")
    axes[2].legend(loc="upper left")
    axes[2].grid(True, linestyle="--", alpha=0.4)

    axes[2].set_xlabel("Zeit (UTC)")
    axes[2].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    fig.autofmt_xdate()
    plt.tight_layout()
    plt.show()


def live_loop(interval_sec: float = 2.0, window: int = 300):
    """
    Aktualisiert die Diagramme alle interval_sec Sekunden.
    window – Anzahl der letzten Datenpunkte, die angezeigt werden (für Lesbarkeit).
    """
    plt.ion()
    fig, axes = plt.subplots(3, 1, sharex=True, figsize=(9, 7))
    fig.suptitle("CubeSat Telemetrie – LIVE", fontsize=14)

    try:
        while True:
            df = load_df()
            if not df.empty:
                # Begrenzung auf die letzten N Messpunkte
                if len(df) > window:
                    df = df.iloc[-window:]

                for ax in axes:
                    ax.cla()

                # Temperatur
                axes[0].plot(df["ts"], df["temperature"], label="Temperatur (°C)")
                axes[0].set_ylabel("°C")
                axes[0].legend(loc="upper left")
                axes[0].grid(True, linestyle="--", alpha=0.4)

                # Luftfeuchtigkeit
                axes[1].plot(df["ts"], df["humidity"], label="Luftfeuchtigkeit (%)")
                axes[1].set_ylabel("%")
                axes[1].legend(loc="upper left")
                axes[1].grid(True, linestyle="--", alpha=0.4)

                # Luftdruck
                axes[2].plot(df["ts"], df["pressure"], label="Luftdruck (hPa)")
                axes[2].set_ylabel("hPa")
                axes[2].legend(loc="upper left")
                axes[2].grid(True, linestyle="--", alpha=0.4)

                axes[2].set_xlabel("Zeit (UTC)")
                axes[2].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
                fig.autofmt_xdate()
                plt.tight_layout()

            plt.pause(0.001)  # gibt die Kontrolle an das Fenster zurück
            time.sleep(interval_sec)

    except KeyboardInterrupt:
        print("\n[GROUND] Live-Ansicht vom Benutzer gestoppt.")
    finally:
        plt.ioff()
        plt.show()


def main():
    """CLI-Parser für den Bodenstations-Monitor."""
    parser = argparse.ArgumentParser(description="Bodenstations-Telemetrie-Monitor")
    parser.add_argument("--once", action="store_true", help="einmalige Darstellung und beenden")
    parser.add_argument("--interval", type=float, default=2.0, help="Aktualisierungsintervall (Sekunden) im Live-Modus")
    parser.add_argument("--window", type=int, default=300, help="Zeige die letzten N Messpunkte im Live-Modus")
    args = parser.parse_args()

    df = load_df()
    if df.empty:
        raise SystemExit("[ERR] Telemetrie-Datei ist leer. Bitte OBC-Logger zuerst starten.")

    if args.once:
        draw_once(df)
    else:
        live_loop(interval_sec=args.interval, window=args.window)


if __name__ == "__main__":
    main()
