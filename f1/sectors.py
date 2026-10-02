"""Sector maths: best sectors, theoretical (sum of best sectors) laps and deficits. Pure pandas."""
from __future__ import annotations

import pandas as pd

SECTOR_COLS = ["Sector1Time", "Sector2Time", "Sector3Time"]
NAMES = ["S1", "S2", "S3"]


def sector_seconds(laps: pd.DataFrame) -> pd.DataFrame:
    """Laps with S1/S2/S3/LapSeconds in seconds; deleted laps are dropped."""
    df = laps.copy()
    if "Deleted" in df:
        df = df[~df["Deleted"].fillna(False).astype(bool)]
    for col, name in zip(SECTOR_COLS, NAMES):
        df[name] = pd.to_timedelta(df[col]).dt.total_seconds()
    df["LapSeconds"] = pd.to_timedelta(df["LapTime"]).dt.total_seconds()
    return df


def best_sectors(laps: pd.DataFrame) -> pd.DataFrame:
    """Per driver: best S1/S2/S3, the sum of them (their own theoretical lap) and their best real lap."""
    df = sector_seconds(laps)
    g = df.groupby("Driver")
    out = g[NAMES].min()
    out["Theoretical"] = out[NAMES].sum(axis=1, min_count=3)
    out["BestLap"] = g["LapSeconds"].min()
    out["Unused"] = out["BestLap"] - out["Theoretical"]
    return out.sort_values("Theoretical").reset_index()


def ultimate_lap(best: pd.DataFrame) -> dict:
    """Best sector across all drivers, who set each, and their sum. This composite mixes drivers, so it may not
    be achievable by any single car on a single lap."""
    owners, times = {}, {}
    for n in NAMES:
        col = best.dropna(subset=[n])
        if col.empty:
            continue
        i = col[n].idxmin()
        owners[n], times[n] = col.loc[i, "Driver"], float(col.loc[i, n])
    return {"owners": owners, "times": times, "total": sum(times.values()) if len(times) == 3 else None}


def sector_deficits(best: pd.DataFrame) -> pd.DataFrame:
    """Each driver's best sectors minus the best sector overall (seconds), plus their total, ranked by total."""
    out = best[["Driver"] + NAMES].copy()
    for n in NAMES:
        out[n] = out[n] - out[n].min()
    out["Total"] = out[NAMES].sum(axis=1)
    return out.sort_values("Total").reset_index(drop=True)


def sector_regions(tel: pd.DataFrame, s1: float, s2: float) -> pd.Series:
    """Sector (1/2/3) of every telemetry sample, from the lap's S1 and S2 times (seconds from lap start)."""
    t = pd.to_timedelta(tel["Time"]).dt.total_seconds()
    t = t - t.iloc[0]
    return pd.Series(1 + (t >= s1).astype(int) + (t >= s1 + s2).astype(int), index=tel.index)
