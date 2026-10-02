"""Fastest-lap comparison maths (pure pandas/numpy). Telemetry frames need Distance (m),
Time (timedelta, from lap start) and Speed (km/h), as FastF1's add_distance() produces."""
from __future__ import annotations

import numpy as np
import pandas as pd


def _seconds(t: pd.Series) -> np.ndarray:
    sec = pd.to_timedelta(t).dt.total_seconds().to_numpy()
    return sec - sec[0]  # zero at the start of the lap slice


def compare_laps(tel_a: pd.DataFrame, tel_b: pd.DataFrame, step: float = 5.0) -> pd.DataFrame:
    """Resample both laps onto a shared distance grid. delta > 0 means B is behind A at that point."""
    end = min(tel_a["Distance"].max(), tel_b["Distance"].max())
    grid = np.arange(0.0, end, step)
    ta = np.interp(grid, tel_a["Distance"], _seconds(tel_a["Time"]))
    tb = np.interp(grid, tel_b["Distance"], _seconds(tel_b["Time"]))
    return pd.DataFrame({
        "Distance": grid,
        "SpeedA": np.interp(grid, tel_a["Distance"], tel_a["Speed"]),
        "SpeedB": np.interp(grid, tel_b["Distance"], tel_b["Speed"]),
        "Delta": tb - ta,
    })


def best_lap_times(laps: pd.DataFrame) -> pd.DataFrame:
    """Fastest lap per driver (qualifying or race), sorted, with gap to the fastest."""
    df = laps.dropna(subset=["LapTime"]).copy()
    df["LapSeconds"] = pd.to_timedelta(df["LapTime"]).dt.total_seconds()
    best = df.groupby("Driver")["LapSeconds"].min().sort_values().reset_index()
    if not best.empty:
        best["gap_to_pole"] = best["LapSeconds"] - best["LapSeconds"].iloc[0]
    return best
