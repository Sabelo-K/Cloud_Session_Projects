"""Pure pandas race-pace maths. Input is a laps frame with FastF1-style columns:
Driver, LapNumber, LapTime (timedelta), Stint, Compound, PitInTime, PitOutTime, TrackStatus.
No network or FastF1 import here, so it is unit-testable with synthetic data."""
from __future__ import annotations

import numpy as np
import pandas as pd

from f1 import tyres

OUTLIER_FACTOR = 1.07  # laps slower than 107% of a driver's median clean lap are dropped


def with_seconds(laps: pd.DataFrame) -> pd.DataFrame:
    out = laps.copy()
    out["LapSeconds"] = pd.to_timedelta(out["LapTime"]).dt.total_seconds()
    return out


GREEN = {"1", "", "nan", "None"}


def tag_laps(laps: pd.DataFrame, factor: float = OUTLIER_FACTOR) -> pd.DataFrame:
    """Every lap with LapSeconds, an Excluded flag and the Reason it was excluded from representative pace
    (no lap time, pit in/out lap, not green flag, or slower than `factor` x the driver's median)."""
    df = with_seconds(laps)
    reason = pd.Series("", index=df.index, dtype=object)
    reason[df["LapSeconds"].isna()] = "no lap time"
    pit = pd.Series(False, index=df.index)
    for col in ("PitInTime", "PitOutTime"):
        if col in df:
            pit |= df[col].notna()
    reason[pit & (reason == "")] = "pit in/out lap"
    if "TrackStatus" in df:
        ts = df["TrackStatus"].astype(str)
        bad = ~ts.isin(GREEN) & (reason == "")
        reason[bad] = "not green (track status " + ts[bad] + ")"
    ok = reason == ""
    median = df["LapSeconds"].where(ok).groupby(df["Driver"]).transform("median")
    reason[ok & (df["LapSeconds"] > median * factor)] = f"slow outlier (>{factor * 100:.0f}% of driver median)"
    df["Reason"] = reason
    df["Excluded"] = reason != ""
    return df


def clean_laps(laps: pd.DataFrame, factor: float = OUTLIER_FACTOR) -> pd.DataFrame:
    """Laps that count towards representative pace (see tag_laps for what is dropped)."""
    df = tag_laps(laps, factor)
    return df[~df["Excluded"]]


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
    df = df[df["Compound"].map(tyres.normalise) != tyres.UNKNOWN]  # unknown tyres would pool different compounds
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
            "Driver": driver, "Stint": int(stint), "Compound": tyres.stint_compound(g["Compound"]),
            "StartLap": int(bounds.loc[(driver, stint), "min"]),
            "EndLap": int(bounds.loc[(driver, stint), "max"]),
            "median": float(g["LapSeconds"].median()), "deg_per_lap": slope,
        })
    return pd.DataFrame(rows, columns=["Driver", "Stint", "Compound", "StartLap", "EndLap", "median", "deg_per_lap"])


def _slope(x: pd.Series, y: pd.Series) -> float:
    xm, ym = x.mean(), y.mean()
    denom = ((x - xm) ** 2).sum()
    return float(((x - xm) * (y - ym)).sum() / denom) if denom else 0.0


def teammate_gaps(laps: pd.DataFrame) -> pd.DataFrame:
    """Race-pace gap inside each team (its two drivers with the most clean laps).
    gap > 0 means the second driver is slower. Needs a Team column."""
    if "Team" not in laps.columns:
        return pd.DataFrame(columns=["Team", "Faster", "Slower", "gap", "laps"])
    pace = race_pace(laps)
    team = laps.dropna(subset=["Team"]).groupby("Driver")["Team"].first()
    pace["Team"] = pace["Driver"].map(team)
    rows = []
    for t, g in pace.dropna(subset=["Team"]).groupby("Team"):
        if len(g) < 2:
            continue
        a, b = g.nlargest(2, "laps").sort_values("median").to_dict("records")
        rows.append({"Team": t, "Faster": a["Driver"], "Slower": b["Driver"],
                     "gap": b["median"] - a["median"], "laps": int(min(a["laps"], b["laps"]))})
    return pd.DataFrame(rows, columns=["Team", "Faster", "Slower", "gap", "laps"]).sort_values("gap").reset_index(drop=True)


def distribution_stats(laps: pd.DataFrame) -> pd.DataFrame:
    """Per-driver clean-lap distribution: n, min, q1, median, mean, q3, max, and median gap to the best driver."""
    df = clean_laps(laps)
    g = df.groupby("Driver")["LapSeconds"]
    out = pd.DataFrame({
        "laps": g.count(), "min": g.min(), "q1": g.quantile(0.25), "median": g.median(),
        "mean": g.mean(), "q3": g.quantile(0.75), "max": g.max(),
    }).sort_values("median").reset_index()
    if not out.empty:
        out["delta_to_best"] = out["median"] - out["median"].iloc[0]
    return out


def gap_to_leader(laps: pd.DataFrame) -> pd.DataFrame:
    """Gap to the race leader at the end of each lap, in seconds. Sign convention: 0 for the leader and
    NEGATIVE for cars behind (so 'below zero = behind'). Needs the cumulative session Time column."""
    df = laps.dropna(subset=["Time"]).copy()
    df["T"] = pd.to_timedelta(df["Time"]).dt.total_seconds()
    lead = df.groupby("LapNumber")["T"].transform("min")
    df["GapToLeader"] = -(df["T"] - lead)
    return df[["Driver", "LapNumber", "GapToLeader"]].sort_values(["Driver", "LapNumber"])


def consistency(laps: pd.DataFrame, detrend: bool = True, min_laps: int = 5) -> pd.DataFrame:
    """Lap-time standard deviation per driver over clean laps (lower = more consistent). With detrend=True
    a straight line is removed from each stint first, so tyre wear and fuel burn are not counted as inconsistency."""
    df = clean_laps(laps)
    rows = []
    for drv, g in df.groupby("Driver"):
        if detrend:
            parts = []
            for _, s in g.groupby("Stint"):
                if len(s) >= 3:
                    fit = np.polyfit(s["LapNumber"].astype(float), s["LapSeconds"], 1)
                    parts.append(s["LapSeconds"] - np.polyval(fit, s["LapNumber"].astype(float)))
            vals = pd.concat(parts) if parts else pd.Series(dtype=float)
        else:
            vals = g["LapSeconds"]
        if len(vals) >= min_laps:
            rows.append({"Driver": drv, "std": float(vals.std()), "laps": int(len(vals))})
    return pd.DataFrame(rows, columns=["Driver", "std", "laps"]).sort_values("std").reset_index(drop=True)


def traffic(laps: pd.DataFrame, threshold: float = 1.5) -> pd.DataFrame:
    """Laps finished within `threshold` seconds of the car directly ahead (a traffic indicator, not proof
    of lost downforce). Gap at the line = this car's lap-end Time minus the Time of the car one position up."""
    df = laps.dropna(subset=["Time", "Position"]).drop_duplicates(["Driver", "LapNumber"]).copy()
    df["T"] = pd.to_timedelta(df["Time"]).dt.total_seconds()
    df["Position"] = df["Position"].astype(int)
    ahead = df[["LapNumber", "Position", "T"]].copy()
    ahead["Position"] += 1
    m = df.merge(ahead.rename(columns={"T": "T_ahead"}), on=["LapNumber", "Position"], how="left")
    m["in_traffic"] = (m["T"] - m["T_ahead"]) <= threshold
    out = m.groupby("Driver").agg(laps=("LapNumber", "count"), in_traffic=("in_traffic", "sum")).reset_index()
    out["in_traffic"] = out["in_traffic"].astype(int)
    return out.sort_values("in_traffic", ascending=False).reset_index(drop=True)


def long_runs(laps: pd.DataFrame, min_laps: int = 5) -> pd.DataFrame:
    """Clean laps from stints with at least `min_laps` clean laps, labelled 'DRV S<stint>' with the lap index in the run (lap number counted from the run's first clean lap)."""
    df = clean_laps(laps).dropna(subset=["Stint"]).sort_values(["Driver", "Stint", "LapNumber"])
    df = df.assign(Run=df["Driver"] + " S" + df["Stint"].astype(int).astype(str))
    df = df[df.groupby("Run")["LapNumber"].transform("count") >= min_laps].copy()
    df["LapInRun"] = df["LapNumber"] - df.groupby("Run")["LapNumber"].transform("min") + 1  # keeps gaps from excluded laps
    return df


def run_summary(runs: pd.DataFrame, fuel_effect: float = 0.0) -> pd.DataFrame:
    """Per long run: laps, mean, median, std and a degradation slope (s per lap of run). fuel_effect (s/lap) is
    added back per lap run so burning fuel is not mistaken for a fast tyre (0 = raw)."""
    rows = []
    for run, g in runs.groupby("Run"):
        y = g["LapSeconds"] + fuel_effect * g["LapInRun"]
        slope = _slope(g["LapInRun"], y)
        intercept = float(y.mean() - slope * g["LapInRun"].mean())
        resid = y - (slope * g["LapInRun"] + intercept)
        rows.append({"Run": run, "Driver": g["Driver"].iloc[0], "Stint": int(g["Stint"].iloc[0]),
                     "Compound": tyres.stint_compound(g["Compound"]), "laps": len(g), "mean": float(g["LapSeconds"].mean()),
                     "median": float(g["LapSeconds"].median()), "std": float(g["LapSeconds"].std()),
                     "resid_std": float(resid.std()), "slope": slope, "intercept": intercept})
    cols = ["Run", "Driver", "Stint", "Compound", "laps", "mean", "median", "std", "resid_std", "slope", "intercept"]
    return pd.DataFrame(rows, columns=cols).sort_values("median").reset_index(drop=True)


def season_deficit(round_laps: dict) -> pd.DataFrame:
    """Race pace per round and driver as a deficit to that race's fastest driver, in seconds and in percent
    (percent lets circuits of different lengths be compared). Pace = median clean lap."""
    rows = []
    for rnd, laps in round_laps.items():
        p = race_pace(laps)
        if p.empty:
            continue
        best = p["median"].min()
        team = laps.dropna(subset=["Team"]).groupby("Driver")["Team"].first() if "Team" in laps else {}
        for r in p.itertuples():
            rows.append({"Round": rnd, "Driver": r.Driver, "Team": team.get(r.Driver), "median": r.median,
                         "deficit_s": r.median - best, "deficit_pct": (r.median / best - 1) * 100})
    return pd.DataFrame(rows, columns=["Round", "Driver", "Team", "median", "deficit_s", "deficit_pct"])


def pit_stops(laps: pd.DataFrame) -> pd.DataFrame:
    """One row per stop: the lap the stint ended on, tyres before and after, and the age of the new set."""
    rows = []
    for drv, g in laps.dropna(subset=["Stint"]).groupby("Driver"):
        stints = g.sort_values("LapNumber").groupby("Stint")
        order = sorted(stints.groups)
        for prev, nxt in zip(order, order[1:]):
            a, b = stints.get_group(prev), stints.get_group(nxt)
            age = b["TyreLife"].iloc[0] if "TyreLife" in b else None
            rows.append({"Driver": drv, "Lap": int(a["LapNumber"].max()), "From": tyres.stint_compound(a["Compound"]),
                         "To": tyres.stint_compound(b["Compound"]), "NewTyreAge": age})
    return pd.DataFrame(rows, columns=["Driver", "Lap", "From", "To", "NewTyreAge"]).sort_values(["Lap", "Driver"]).reset_index(drop=True)
