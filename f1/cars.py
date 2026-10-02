"""Car performance by team across a season: qualifying gap, race-pace gap and top speed per round. Pure pandas."""
from __future__ import annotations

import pandas as pd

from f1 import pace, summary

COLUMNS = ["Round", "Team", "QualiGapPct", "RacePaceGapPct", "TopSpeed", "TopSpeedGap"]


def _team_best_lap(quali: pd.DataFrame) -> pd.Series:
    order = summary.quali_order(quali).dropna(subset=["Team"])
    return order.groupby("Team")["Best"].min()


def _team_race_pace(race: pd.DataFrame) -> pd.Series:
    p = pace.race_pace(race)
    teams = race.dropna(subset=["Team"]).groupby("Driver")["Team"].first()
    p["Team"] = p["Driver"].map(teams)
    return p.dropna(subset=["Team"]).groupby("Team")["median"].mean()


def _team_top_speed(*sessions: pd.DataFrame) -> pd.Series:
    parts = []
    for laps in sessions:
        if laps is not None and "SpeedST" in laps.columns:
            parts.append(laps.dropna(subset=["SpeedST", "Team"]).groupby("Team")["SpeedST"].max())
    return pd.concat(parts, axis=1).max(axis=1) if parts else pd.Series(dtype=float)


def team_rounds(quali_by_round: dict, race_by_round: dict) -> pd.DataFrame:
    """One row per round and team: QualiGapPct (best lap vs the pole team, %), RacePaceGapPct (median pace vs the
    fastest team, %), TopSpeed (km/h, best speed-trap reading in either session) and TopSpeedGap (km/h below the fastest team)."""
    rows = []
    for rnd in sorted(set(quali_by_round) | set(race_by_round)):
        quali, race = quali_by_round.get(rnd), race_by_round.get(rnd)
        q = _team_best_lap(quali) if quali is not None else pd.Series(dtype=float)
        r = _team_race_pace(race) if race is not None else pd.Series(dtype=float)
        s = _team_top_speed(quali, race)
        for team in sorted(set(q.index) | set(r.index) | set(s.index)):
            rows.append({
                "Round": rnd, "Team": team,
                "QualiGapPct": (q[team] / q.min() - 1) * 100 if team in q.index else float("nan"),
                "RacePaceGapPct": (r[team] / r.min() - 1) * 100 if team in r.index else float("nan"),
                "TopSpeed": s.get(team, float("nan")),
                "TopSpeedGap": (s.max() - s[team]) if team in s.index else float("nan"),
            })
    return pd.DataFrame(rows, columns=COLUMNS)


def season_profile(rounds: pd.DataFrame) -> pd.DataFrame:
    """Season average per team of each measure, ranked by race pace (best first)."""
    if rounds.empty:
        return pd.DataFrame(columns=["Team", "QualiGapPct", "RacePaceGapPct", "TopSpeedGap", "Rounds"])
    g = rounds.groupby("Team")
    out = g[["QualiGapPct", "RacePaceGapPct", "TopSpeedGap"]].mean()
    out["Rounds"] = g["Round"].nunique()
    return out.sort_values("RacePaceGapPct").reset_index()
