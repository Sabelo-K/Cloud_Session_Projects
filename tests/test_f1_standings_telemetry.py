import pandas as pd

from f1 import standings, telemetry


def _payload(points):
    return {"MRData": {"StandingsTable": {"StandingsLists": [{"DriverStandings": [
        {"position": str(i + 1), "points": str(p), "Driver": {"code": c, "familyName": c}}
        for i, (c, p) in enumerate(points)]}]}}}


def test_parse_standings():
    df = standings.parse_standings(_payload([("VER", 25), ("NOR", 18)]), 1)
    assert list(df["Driver"]) == ["VER", "NOR"] and df["Round"].eq(1).all()
    assert df.loc[0, "Points"] == 25.0


def test_progression_carries_points_forward():
    f1 = standings.parse_standings(_payload([("VER", 25), ("NOR", 18)]), 1)
    f2 = standings.parse_standings(_payload([("VER", 43)]), 2)  # NOR missing in round 2
    prog = standings.progression([f1, f2])
    nor = prog[(prog["Driver"] == "NOR") & (prog["Round"] == 2)]["Points"].iloc[0]
    assert nor == 18.0


def _tel(speed_scale, secs_per_100m):
    dist = pd.Series(range(0, 1001, 10), dtype=float)
    return pd.DataFrame({"Distance": dist, "Speed": 200 * speed_scale,
                         "Time": pd.to_timedelta(dist / 100 * secs_per_100m, unit="s") + pd.Timedelta(seconds=500)})


def test_compare_laps_delta_positive_when_b_slower():
    cmp = telemetry.compare_laps(_tel(1.0, 1.0), _tel(0.9, 1.1))
    assert cmp["Delta"].iloc[0] == 0  # both zeroed at the start
    assert cmp["Delta"].iloc[-1] > 0.9
    assert (cmp["SpeedA"] > cmp["SpeedB"]).all()


def test_best_lap_times_gap():
    laps = pd.DataFrame({"Driver": ["A", "A", "B"],
                         "LapTime": pd.to_timedelta([80.5, 80.0, 80.4], unit="s")})
    best = telemetry.best_lap_times(laps)
    assert list(best["Driver"]) == ["A", "B"]
    assert abs(best["gap_to_pole"].iloc[1] - 0.4) < 1e-9
