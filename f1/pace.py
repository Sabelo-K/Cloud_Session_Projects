"""Pure pandas race-pace maths. Input is a laps frame with FastF1-style columns:
Driver, LapNumber, LapTime (timedelta), Stint, Compound, PitInTime, PitOutTime, TrackStatus.
No network or FastF1 import here, so it is unit-testable with synthetic data."""
from __future__ import annotations

import pandas as pd

OUTLIER_FACTOR = 1.07  # laps slower than 107% of a driver's median clean lap are dropped


def with_seconds(laps: pd.DataFrame) -> pd.DataFrame:
    out = laps.copy()
    out["LapSeconds"] = pd.to_timedelta(out["LapTime"]).dt.total_seconds()
    return out


def clean_laps(laps: pd.DataFrame, factor: float = OUTLIER_FACTOR) -> pd.DataFrame:
    """Drop laps without a time, pit in/out laps, non-green laps and slow outliers."""
    df = with_seconds(laps)
    df = df[df["LapSeconds"].notna()]
    df = df[df["PitInTime"].isna() & df["PitOutTime"].isna()]
    df = df[df["TrackStatus"].astype(str).isin(["1", ""])]
    median = df.groupby("Driver")["LapSeconds"].transform("median")
    return df[df["LapSeconds"] <= median * factor]


def race_pace(laps: pd.DataFrame) -> pd.DataFrame:
    """Median clean lap per driver, fastest first, with gap to the best driver."""
    df = clean_laps(laps)
    pace = (
        df.groupby("Driver")["LapSeconds"]
        .agg(median="median", best="min", laps="count")
        .sort_values("median")
        .reset_index()
    )
    if not pace.empty:
        pace["gap_to_best"] = pace["median"] - pace["median"].iloc[0]
    return pace


def stint_summary(laps: pd.DataFrame) -> pd.DataFrame:
    """One row per driver stint: compound, lap range, median clean lap, tyre-deg slope (s/lap)."""
    df = clean_laps(laps)
    rows = []
    for (driver, stint), g in df.groupby(["Driver", "Stint"]):
        slope = None
        if len(g) >= 3:
            slope = _slope(g["LapNumber"], g["LapSeconds"])
        rows.append({
            "Driver": driver, "Stint": int(stint), "Compound": g["Compound"].iloc[0],
            "StartLap": int(g["LapNumber"].min()), "EndLap": int(g["LapNumber"].max()),
            "median": float(g["LapSeconds"].median()), "deg_per_lap": slope,
        })
    return pd.DataFrame(rows)


def _slope(x: pd.Series, y: pd.Series) -> float:
    xm, ym = x.mean(), y.mean()
    denom = ((x - xm) ** 2).sum()
    return float(((x - xm) * (y - ym)).sum() / denom) if denom else 0.0
