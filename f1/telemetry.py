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


def _slow_points(speed: np.ndarray, min_drop: float) -> list[int]:
    """Indices of local speed minima that the car climbs at least `min_drop` km/h away from on both sides."""
    found = []
    for i in range(1, len(speed) - 1):
        if not (speed[i] <= speed[i - 1] and speed[i] < speed[i + 1]):
            continue
        j = i
        while j > 0 and speed[j - 1] >= speed[i]:  # climb away to the left until something slower comes
            j -= 1
        k = i
        while k < len(speed) - 1 and speed[k + 1] >= speed[i]:
            k += 1
        if min(speed[j:i + 1].max(), speed[i:k + 1].max()) - speed[i] >= min_drop:
            found.append(i)
    return found


def _tight_points(x: np.ndarray, y: np.ndarray, step: float, min_curve: float, min_turn: float, join: float) -> list[int]:
    """Indices of the sharpest point of each stretch of track that bends (heading change per metre above `min_curve`)
    by at least `min_turn` degrees in total. Finds flat-out kinks that show no dip in speed. X and Y are in 1/10 m."""
    box = np.ones(5) / 5
    sx = np.convolve(np.pad(x / 10, 2, mode="edge"), box, "valid")
    sy = np.convolve(np.pad(y / 10, 2, mode="edge"), box, "valid")
    heading = np.unwrap(np.arctan2(np.gradient(sy), np.gradient(sx)))
    curve = np.convolve(np.pad(np.abs(np.gradient(heading)) / step, 2, mode="edge"), box, "valid")
    bend, out, i, reach = curve > min_curve, [], 0, max(1, int(join / step))
    while i < len(bend):
        if not bend[i]:
            i += 1
            continue
        j = i
        while j + 1 < len(bend) and bend[j + 1:j + 1 + reach].any():
            j += 1
        if np.degrees(abs(heading[min(j + 1, len(heading) - 1)] - heading[i])) >= min_turn:
            out.append(i + int(np.argmax(curve[i:j + 1])))
        i = j + 1
    return out


def estimate_corners(tel: pd.DataFrame, step: float = 5.0, merge: float = 60.0) -> pd.DataFrame:
    """Guess corner positions from one lap, for circuits where FastF1 has no official corner map: slow points plus tight
    bends, merged when closer than `merge` metres, numbered in lap order. Columns Number, Distance, X, Y, Estimated (True).
    Checked against the official 2026 maps it finds about 80% of the real corners and few extra ones, so numbers can differ
    from the real ones."""
    cols = ["Number", "Distance", "X", "Y", "Estimated"]
    if tel is None or len(tel) < 20 or not {"Distance", "Speed", "X", "Y"} <= set(tel.columns):
        return pd.DataFrame(columns=cols)
    df = tel.sort_values("Distance").drop_duplicates("Distance")
    dist = df["Distance"].to_numpy(float)
    grid = np.arange(0.0, dist.max(), step)
    if len(grid) < 20:
        return pd.DataFrame(columns=cols)
    x, y = np.interp(grid, dist, df["X"].to_numpy(float)), np.interp(grid, dist, df["Y"].to_numpy(float))
    speed = np.interp(grid, dist, df["Speed"].to_numpy(float))
    speed = np.convolve(np.pad(speed, 1, mode="edge"), np.ones(3) / 3, mode="valid")
    points = sorted(set(_slow_points(speed, 5.0)) | set(_tight_points(x, y, step, 0.005, 10.0, 20.0)))
    kept: list[int] = []
    for i in points:
        if kept and (i - kept[-1]) * step < merge:
            continue
        kept.append(i)
    at = grid[kept]
    return pd.DataFrame({"Number": range(1, len(kept) + 1), "Distance": at, "X": x[kept], "Y": y[kept], "Estimated": True})[cols]
