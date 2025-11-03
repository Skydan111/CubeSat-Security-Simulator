#!/usr/bin/env python3
"""
Mission View — Ground Station Telemetry Monitor
- Читает cube/data/telemetry.csv
- Рисует 3 графика (темп / влажн / давление)
- Режимы: одноразовый (--once) и "живой" (по умолчанию)
"""

import argparse
import time
import pathlib
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

CSV_PATH = pathlib.Path("cube/data/telemetry.csv")


def load_df() -> pd.DataFrame:
    if not CSV_PATH.exists():
        raise SystemExit(f"[ERR] Telemetry file not found: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH, parse_dates=["ts"])
    if df.empty:
        return df
    df = df.sort_values("ts")
    return df


def draw_once(df: pd.DataFrame):
    fig, axes = plt.subplots(3, 1, sharex=True, figsize=(9, 7))
    fig.suptitle("CubeSat Telemetry – Ground Station View", fontsize=14)

    # Температура
    axes[0].plot(df["ts"], df["temperature"], label="Temperature (°C)")
    axes[0].set_ylabel("°C")
    axes[0].legend(loc="upper left")
    axes[0].grid(True, linestyle="--", alpha=0.4)

    # Влажность
    axes[1].plot(df["ts"], df["humidity"], label="Humidity (%)")
    axes[1].set_ylabel("%")
    axes[1].legend(loc="upper left")
    axes[1].grid(True, linestyle="--", alpha=0.4)

    # Давление
    axes[2].plot(df["ts"], df["pressure"], label="Pressure (hPa)")
    axes[2].set_ylabel("hPa")
    axes[2].legend(loc="upper left")
    axes[2].grid(True, linestyle="--", alpha=0.4)

    axes[2].set_xlabel("Time (UTC)")
    axes[2].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    fig.autofmt_xdate()
    plt.tight_layout()
    plt.show()


def live_loop(interval_sec: float = 2.0, window: int = 300):
    """Перерисовывает графики каждые interval_sec секунд.
    window — сколько последних точек держать на экране (для читаемости).
    """
    plt.ion()
    fig, axes = plt.subplots(3, 1, sharex=True, figsize=(9, 7))
    fig.suptitle("CubeSat Telemetry – LIVE", fontsize=14)

    try:
        while True:
            df = load_df()
            if not df.empty:
                # ограничим окно последних N точек
                if len(df) > window:
                    df = df.iloc[-window:]

                for ax in axes:
                    ax.cla()

                # Температура
                axes[0].plot(df["ts"], df["temperature"], label="Temperature (°C)")
                axes[0].set_ylabel("°C")
                axes[0].legend(loc="upper left")
                axes[0].grid(True, linestyle="--", alpha=0.4)

                # Влажность
                axes[1].plot(df["ts"], df["humidity"], label="Humidity (%)")
                axes[1].set_ylabel("%")
                axes[1].legend(loc="upper left")
                axes[1].grid(True, linestyle="--", alpha=0.4)

                # Давление
                axes[2].plot(df["ts"], df["pressure"], label="Pressure (hPa)")
                axes[2].set_ylabel("hPa")
                axes[2].legend(loc="upper left")
                axes[2].grid(True, linestyle="--", alpha=0.4)

                axes[2].set_xlabel("Time (UTC)")
                axes[2].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
                fig.autofmt_xdate()
                plt.tight_layout()

            plt.pause(0.001)  # отдаём управление окну
            time.sleep(interval_sec)

    except KeyboardInterrupt:
        print("\n[GROUND] Live view stopped by user.")
    finally:
        plt.ioff()
        plt.show()


def main():
    parser = argparse.ArgumentParser(description="Ground Station Telemetry Monitor")
    parser.add_argument("--once", action="store_true", help="draw one static figure and exit")
    parser.add_argument("--interval", type=float, default=2.0, help="refresh interval (sec) in live mode")
    parser.add_argument("--window", type=int, default=300, help="show last N samples in live mode")
    args = parser.parse_args()

    df = load_df()
    if df.empty:
        raise SystemExit("[ERR] Telemetry file is empty. Run OBC logger first.")

    if args.once:
        draw_once(df)
    else:
        live_loop(interval_sec=args.interval, window=args.window)


if __name__ == "__main__":
    main()
