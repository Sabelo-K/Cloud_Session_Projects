"""Championship progression from Jolpica per-round driver standings JSON."""
from __future__ import annotations

import pandas as pd


def _int_or_none(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def parse_standings(payload: dict, round_no: int) -> pd.DataFrame:
    """One round's Jolpica driverStandings response -> rows of Driver, Round, Points, Position."""
    lists = payload["MRData"]["StandingsTable"]["StandingsLists"]
    if not lists:
        return pd.DataFrame(columns=["Driver", "Round", "Points", "Position"])
    return pd.DataFrame(
        [{
            "Driver": d["Driver"].get("code") or d["Driver"]["familyName"][:3].upper(),
            "Round": round_no,
            "Points": float(d["points"]),
            "Position": _int_or_none(d.get("position") or d.get("positionText")),
        } for d in lists[0]["DriverStandings"]]
    )


def progression(frames: list[pd.DataFrame]) -> pd.DataFrame:
    """Stack per-round frames; drivers absent in a round carry their last points forward."""
    if not frames:
        return pd.DataFrame(columns=["Driver", "Round", "Points", "Position"])
    allr = pd.concat(frames, ignore_index=True)
    grid = allr.pivot(index="Round", columns="Driver", values="Points").sort_index().ffill().fillna(0.0)
    return grid.reset_index().melt(id_vars="Round", var_name="Driver", value_name="Points")
