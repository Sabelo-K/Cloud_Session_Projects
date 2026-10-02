import pandas as pd

from f1 import pace, style


def test_team_color_matches_and_falls_back():
    assert style.team_color("Scuderia Ferrari") == "#E8002D"
    assert style.team_color("Red Bull Racing") == "#3671C6"
    assert style.team_color("Unknown Team", 1) == style.FALLBACK[1]
    assert style.team_color(None) == style.FALLBACK[0]


def test_driver_styles_dashes_second_teammate():
    laps = pd.DataFrame({"Driver": ["HAM", "LEC", "RUS"], "Team": ["Ferrari", "Ferrari", "Mercedes"]})
    colours, dashes = style.driver_styles(laps)
    assert colours["HAM"] == colours["LEC"] == "#E8002D"
    assert {dashes["HAM"], dashes["LEC"]} == {"solid", "dash"}
    assert dashes["RUS"] == "solid"


def test_driver_styles_without_team_column():
    assert style.driver_styles(pd.DataFrame({"Driver": ["A"]})) == ({}, {})


def _race(speeds):
    rows = []
    for drv, team, base in speeds:
        for lap in range(1, 9):
            rows.append(dict(Driver=drv, Team=team, LapNumber=lap, Stint=1, Compound="SOFT",
                             LapTime=pd.Timedelta(seconds=base), PitInTime=pd.NaT, PitOutTime=pd.NaT, TrackStatus="1"))
    df = pd.DataFrame(rows)
    df["PitInTime"] = pd.Series([pd.NaT] * len(df), dtype="timedelta64[ns]")
    df["PitOutTime"] = df["PitInTime"]
    return df


def test_teammate_gaps():
    laps = _race([("VER", "Red Bull", 90.0), ("PER", "Red Bull", 90.4), ("HAM", "Mercedes", 90.2), ("RUS", "Mercedes", 90.1)])
    g = pace.teammate_gaps(laps)
    rb = g[g["Team"] == "Red Bull"].iloc[0]
    assert rb["Faster"] == "VER" and abs(rb["gap"] - 0.4) < 1e-9
    merc = g[g["Team"] == "Mercedes"].iloc[0]
    assert merc["Faster"] == "RUS" and abs(merc["gap"] - 0.1) < 1e-9
    assert list(g["Team"]) == ["Mercedes", "Red Bull"]  # sorted by gap


def test_teammate_gaps_without_team_column():
    assert pace.teammate_gaps(_race([("A", "T", 90.0)]).drop(columns="Team")).empty
