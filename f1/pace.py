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


def lap_chart_frame(laps: pd.DataFrame, show_all: bool = False) -> pd.DataFrame:
    """Frame for the lap-time line chart. By default pit, non-green and slow-outlier laps are
    blanked (NaN) so the line breaks there instead of a red-flag lap squashing the y-axis."""
    df = with_seconds(laps)
    if not show_all:
        keep = clean_laps(laps).index
        df.loc[~df.index.isin(keep), "LapSeconds"] = float("nan")
    return df.sort_values(["Driver", "LapNumber"])


FUEL_EFFECT_S_PER_LAP = 0.03  # approx. time gained per lap as fuel burns off


def compound_degradation(laps: pd.DataFrame, fuel_effect: float = FUEL_EFFECT_S_PER_LAP) -> pd.DataFrame:
    """Per-compound tyre degradation: slope of fuel-corrected clean lap time vs tyre age
    (needs a TyreLife column), pooled over all drivers. Positive slope = tyres losing pace."""
    df = clean_laps(laps).dropna(subset=["TyreLife", "Compound"])
    df = df.assign(Corrected=df["LapSeconds"] + fuel_effect * df["LapNumber"])
    rows = []
    for compound, g in df.groupby("Compound"):
        if len(g) < 5 or g["TyreLife"].nunique() < 3:
            continue
        rows.append({"Compound": compound, "laps": len(g),
                     "deg_per_lap": _slope(g["TyreLife"], g["Corrected"]),
                     "fastest": float(g["Corrected"].min())})
    return pd.DataFrame(rows, columns=["Compound", "laps", "deg_per_lap", "fastest"])


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
    bounds = laps.groupby(["Driver", "Stint"])["LapNumber"].agg(["min", "max"])  # incl. pit laps
    rows = []
    for (driver, stint), g in df.groupby(["Driver", "Stint"]):
        slope = None
        if len(g) >= 3:
            slope = _slope(g["LapNumber"], g["LapSeconds"])
        rows.append({
            "Driver": driver, "Stint": int(stint), "Compound": g["Compound"].iloc[0],
            "StartLap": int(bounds.loc[(driver, stint), "min"]),
            "EndLap": int(bounds.loc[(driver, stint), "max"]),
            "median": float(g["LapSeconds"].median()), "deg_per_lap": slope,
        })
    return pd.DataFrame(rows)


def _slope(x: pd.Series, y: pd.Series) -> float:
    xm, ym = x.mean(), y.mean()
    denom = ((x - xm) ** 2).sum()
    return float(((x - xm) * (y - ym)).sum() / denom) if denom else 0.0
