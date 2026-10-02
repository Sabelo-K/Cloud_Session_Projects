"""Race-weekend summary maths: qualifying order, race classification, places gained and strategy strings.
Pure pandas on FastF1-style laps frames, so it is unit-testable without Streamlit or the network."""
from __future__ import annotations

import pandas as pd

from f1 import pace, tyres


def _valid(laps: pd.DataFrame) -> pd.DataFrame:
    df = laps.dropna(subset=["LapTime"]).copy()
    if "Deleted" in df.columns:
        df = df[~df["Deleted"].fillna(False).astype(bool)]
    df["LapSeconds"] = pd.to_timedelta(df["LapTime"]).dt.total_seconds()
    return df


def strategy_string(laps: pd.DataFrame) -> str:
    """Tyre letters in stint order, e.g. 'M-H-S' (a driver's laps in one session)."""
    if "Stint" not in laps.columns:
        return ""
    letters = [tyres.letter(tyres.stint_compound(g["Compound"])) for _, g in laps.dropna(subset=["Stint"]).groupby("Stint")]
    return "-".join(letters)


def quali_order(laps: pd.DataFrame) -> pd.DataFrame:
    """One row per driver ranked by best valid lap: Pos, Driver, Team, Best, Gap, Tyre (compound of the best lap), TopSpeed."""
    df = _valid(laps)
    if df.empty:
        return pd.DataFrame(columns=["Pos", "Driver", "Team", "Best", "Gap", "Tyre", "TopSpeed"])
    rows = []
    for drv, g in df.groupby("Driver"):
        best = g.loc[g["LapSeconds"].idxmin()]
        top = laps.loc[laps["Driver"] == drv, "SpeedST"].max() if "SpeedST" in laps.columns else float("nan")
        rows.append({"Driver": drv, "Team": best.get("Team"), "Best": float(best["LapSeconds"]),
                     "Tyre": tyres.normalise(best.get("Compound")), "TopSpeed": top})
    out = pd.DataFrame(rows).sort_values("Best").reset_index(drop=True)
    out.insert(0, "Pos", range(1, len(out) + 1))
    out["Gap"] = out["Best"] - out["Best"].iloc[0]
    return out[["Pos", "Driver", "Team", "Best", "Gap", "Tyre", "TopSpeed"]]


def race_classification(laps: pd.DataFrame) -> pd.DataFrame:
    """Finishing order from the laps: most laps completed first, then who crossed the line first on their last lap.
    Columns: Pos, Driver, Team, Laps, Stops, Strategy, Fastest (best valid lap), Median (clean-lap pace)."""
    cols = ["Pos", "Driver", "Team", "Laps", "Stops", "Strategy", "Fastest", "Median"]
    if laps.empty:
        return pd.DataFrame(columns=cols)
    valid = _valid(laps)
    median = pace.race_pace(laps).set_index("Driver")["median"] if len(laps) else pd.Series(dtype=float)
    rows = []
    for drv, g in laps.groupby("Driver"):
        g = g.sort_values("LapNumber")
        last = g.iloc[-1]
        fast = valid.loc[valid["Driver"] == drv, "LapSeconds"].min() if (valid["Driver"] == drv).any() else float("nan")
        stints = g["Stint"].dropna().nunique() if "Stint" in g.columns else 1
        rows.append({"Driver": drv, "Team": last.get("Team"), "Laps": int(g["LapNumber"].max()),
                     "_t": pd.to_timedelta(last.get("Time")) if pd.notna(last.get("Time")) else pd.NaT,
                     "Stops": max(int(stints) - 1, 0), "Strategy": strategy_string(g),
                     "Fastest": fast, "Median": float(median.get(drv, float("nan")))})
    out = pd.DataFrame(rows).sort_values(["Laps", "_t"], ascending=[False, True]).reset_index(drop=True)
    out.insert(0, "Pos", range(1, len(out) + 1))
    return out[cols]


def places_gained(quali: pd.DataFrame, race: pd.DataFrame) -> pd.DataFrame:
    """Qualifying rank against race finish for drivers in both. Gained > 0 means they finished ahead of where they qualified."""
    m = quali[["Driver", "Team", "Pos"]].rename(columns={"Pos": "Qualified"}).merge(
        race[["Driver", "Pos"]].rename(columns={"Pos": "Finished"}), on="Driver")
    m["Gained"] = m["Qualified"] - m["Finished"]
    return m.sort_values("Gained", ascending=False).reset_index(drop=True)


def fastest_lap(race: pd.DataFrame) -> tuple[str, float] | None:
    """(driver, seconds) of the quickest race lap in a classification, or None."""
    r = race.dropna(subset=["Fastest"])
    if r.empty:
        return None
    i = r["Fastest"].idxmin()
    return str(r.loc[i, "Driver"]), float(r.loc[i, "Fastest"])


def top_speeds(laps: pd.DataFrame) -> pd.DataFrame:
    """Highest speed-trap reading per driver, fastest first."""
    if "SpeedST" not in laps.columns or laps["SpeedST"].dropna().empty:
        return pd.DataFrame(columns=["Driver", "Team", "TopSpeed"])
    g = laps.dropna(subset=["SpeedST"]).groupby("Driver")
    out = g["SpeedST"].max().rename("TopSpeed").reset_index()
    teams = laps.dropna(subset=["Team"]).groupby("Driver")["Team"].first()
    out["Team"] = out["Driver"].map(teams)
    return out.sort_values("TopSpeed", ascending=False).reset_index(drop=True)[["Driver", "Team", "TopSpeed"]]
