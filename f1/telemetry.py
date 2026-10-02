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


CONTINUOUS = ["Speed", "Throttle", "RPM", "X", "Y", "TimeS"]
DISCRETE = ["Brake", "nGear", "DRS"]  # held as steps when resampling, never interpolated


def prepare_lap(tel: pd.DataFrame) -> pd.DataFrame:
    """Sort by distance, drop repeated distances and add TimeS (seconds from the start of the lap)."""
    df = tel.sort_values("Distance").drop_duplicates("Distance").copy()
    df["TimeS"] = pd.to_timedelta(df["Time"]).dt.total_seconds()
    df["TimeS"] -= df["TimeS"].iloc[0]
    if "Brake" in df:
        df["Brake"] = df["Brake"].astype(float)
    return df


def resample_lap(tel: pd.DataFrame, step: float = 5.0, end: float | None = None) -> pd.DataFrame:
    """Put one lap on a regular distance grid. Continuous channels are interpolated; brake, gear and DRS keep
    the last known value (step), so they stay genuine on/off or integer states."""
    df = prepare_lap(tel)
    dist = df["Distance"].to_numpy(float)
    grid = np.arange(0.0, end if end is not None else dist.max(), step)
    out = {"Distance": grid}
    for c in CONTINUOUS:
        if c in df:
            out[c] = np.interp(grid, dist, df[c].to_numpy(float))
    idx = np.clip(np.searchsorted(dist, grid, side="right") - 1, 0, len(dist) - 1)
    for c in DISCRETE:
        if c in df:
            out[c] = df[c].to_numpy()[idx]
    return pd.DataFrame(out)


def resample_all(tels: dict, step: float = 5.0) -> dict:
    """Resample several laps onto one shared grid that ends where the shortest lap ends."""
    end = min(prepare_lap(t)["Distance"].max() for t in tels.values())
    return {k: resample_lap(t, step, end) for k, t in tels.items()}


def delta_vs_reference(res: dict, ref: str) -> dict:
    """Cumulative time difference to the reference lap along the lap (seconds). Positive = slower than the
    reference at that point, negative = ahead."""
    return {k: df["TimeS"] - res[ref]["TimeS"] for k, df in res.items()}


def track_dominance(res: dict, segment_m: float = 25.0) -> pd.DataFrame:
    """Cut the lap into segments of `segment_m` metres and name the lap that crossed each one fastest
    (segment traversal time, not top speed). Gain = how much quicker the winner was than the runner-up."""
    labels = list(res)
    ref = res[labels[0]]
    end = ref["Distance"].max()
    bounds = np.arange(0.0, end, segment_m)
    bounds = np.append(bounds, end) if bounds[-1] < end else bounds
    times = np.vstack([np.diff(np.interp(bounds, res[k]["Distance"], res[k]["TimeS"])) for k in labels])
    x = np.interp(bounds, ref["Distance"], ref["X"])
    y = np.interp(bounds, ref["Distance"], ref["Y"])
    order = np.sort(times, axis=0)
    gain = order[1] - order[0] if len(labels) > 1 else np.zeros(times.shape[1])
    return pd.DataFrame({
        "Start": bounds[:-1], "X0": x[:-1], "Y0": y[:-1], "X1": x[1:], "Y1": y[1:],
        "Winner": [labels[i] for i in times.argmin(axis=0)], "Gain": gain,
    })


def corner_speeds(res: dict, corners: pd.DataFrame, window: float = 60.0, threshold: float = 150.0) -> pd.DataFrame:
    """Apex (minimum) speed of each lap inside +-window metres of each corner. A corner is 'High' speed when
    the mean apex speed across the compared laps is at least `threshold` km/h, else 'Low'."""
    lap_len = max(df["Distance"].max() for df in res.values())
    dist = corners["Distance"].astype(float)
    if dist.max() > lap_len * 1.5:  # some FastF1 versions give corner distance in 1/10 m
        dist = dist / 10.0
    rows = []
    for number, cd in zip(corners["Number"], dist):
        apex = {}
        for k, df in res.items():
            sel = df[(df["Distance"] - cd).abs() <= window]
            if not sel.empty:
                apex[k] = float(sel["Speed"].min())
        if not apex:
            continue
        cls = "High" if np.mean(list(apex.values())) >= threshold else "Low"
        best = max(apex, key=apex.get)
        rows.append(pd.DataFrame({"Corner": int(number), "Distance": cd, "Lap": list(apex), "ApexSpeed": list(apex.values()),
                                  "Winner": [k == best for k in apex], "Class": cls}))
    cols = ["Corner", "Distance", "Lap", "ApexSpeed", "Winner", "Class"]
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=cols)


def apex_wins(corner_df: pd.DataFrame) -> pd.DataFrame:
    """Number of corners each lap had the highest apex speed in, split by High/Low speed class."""
    wins = corner_df[corner_df["Winner"]].groupby(["Class", "Lap"]).size().rename("Wins").reset_index()
    every = corner_df.groupby(["Class", "Lap"]).size().rename("Corners").reset_index()
    return every.merge(wins, on=["Class", "Lap"], how="left").fillna({"Wins": 0}).astype({"Wins": int})
