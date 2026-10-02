import pandas as pd

from f1 import cars, summary


def lap(drv, team, n, secs, comp="SOFT", stint=1, t_end=None, speed=320.0, deleted=False):
    return dict(Driver=drv, Team=team, LapNumber=n, LapTime=pd.Timedelta(seconds=secs) if secs else pd.NaT,
                Time=pd.Timedelta(seconds=t_end if t_end is not None else n * 90), Compound=comp, Stint=stint,
                TyreLife=float(n), PitInTime=pd.NaT, PitOutTime=pd.NaT, TrackStatus="1", SpeedST=speed, Deleted=deleted)


def quali():
    return pd.DataFrame([
        lap("VER", "RB", 1, 80.5, speed=330), lap("VER", "RB", 2, 80.0, speed=335),
        lap("HAM", "FER", 1, 80.2, comp="MEDIUM", speed=325), lap("HAM", "FER", 2, 79.9, deleted=True),  # fastest lap deleted
        lap("NOR", "MCL", 1, 81.0, speed=320),
    ])


def race():
    rows = []
    for n in range(1, 6):   # NOR wins, VER one lap down, HAM retires after 2 laps
        rows.append(lap("NOR", "MCL", n, 90.0 + n * 0.1, t_end=n * 90.0, stint=1 if n < 4 else 2, comp="MEDIUM" if n < 4 else "HARD"))
    for n in range(1, 5):
        rows.append(lap("VER", "RB", n, 90.5, t_end=n * 91.0))
    for n in range(1, 3):
        rows.append(lap("HAM", "FER", n, 91.0, t_end=n * 89.0))  # earlier on the clock but far fewer laps
    return pd.DataFrame(rows)


def test_quali_order_ignores_deleted_laps_and_reports_gap_tyre_and_speed():
    q = summary.quali_order(quali())
    assert list(q["Driver"]) == ["VER", "HAM", "NOR"]
    assert q["Gap"].round(3).tolist() == [0.0, 0.2, 1.0]  # HAM's 79.9 was deleted, so 80.2 counts
    assert q.loc[q.Driver == "HAM", "Tyre"].iloc[0] == "MEDIUM"
    assert q.loc[q.Driver == "VER", "TopSpeed"].iloc[0] == 335


def test_race_classification_orders_by_laps_then_time_and_counts_stops():
    r = summary.race_classification(race())
    assert list(r["Driver"]) == ["NOR", "VER", "HAM"]
    nor = r.iloc[0]
    assert (nor["Laps"], nor["Stops"], nor["Strategy"]) == (5, 1, "M-H")
    assert r.iloc[1]["Stops"] == 0 and r.iloc[1]["Strategy"] == "S"


def test_places_gained_and_fastest_lap():
    q, r = summary.quali_order(quali()), summary.race_classification(race())
    moves = summary.places_gained(q, r).set_index("Driver")
    assert moves.loc["NOR", "Gained"] == 2 and moves.loc["VER", "Gained"] == -1 and moves.loc["HAM", "Gained"] == -1
    assert summary.fastest_lap(r)[0] == "NOR"


def test_top_speeds_sorted_with_team():
    t = summary.top_speeds(quali())
    assert list(t["Driver"]) == ["VER", "HAM", "NOR"] and t["TopSpeed"].iloc[0] == 335
    assert summary.top_speeds(quali().drop(columns="SpeedST")).empty


def test_empty_inputs_do_not_crash():
    assert summary.race_classification(race().iloc[0:0]).empty
    assert summary.quali_order(quali().iloc[0:0]).empty


def test_car_performance_gaps():
    table = cars.team_rounds({1: quali()}, {1: race()})
    t = table.set_index("Team")
    assert t.loc["RB", "QualiGapPct"] == 0 and round(t.loc["FER", "QualiGapPct"], 3) == round((80.2 / 80.0 - 1) * 100, 3)
    assert t.loc["MCL", "RacePaceGapPct"] == 0 and t.loc["RB", "RacePaceGapPct"] > 0
    assert t.loc["RB", "TopSpeedGap"] == 0 and t.loc["MCL", "TopSpeedGap"] == 15  # 335 vs 320 (race laps have 320)


def test_car_performance_handles_missing_sessions_and_profile():
    table = cars.team_rounds({1: quali()}, {2: race()})
    assert set(table["Round"]) == {1, 2}
    assert table[(table.Round == 1) & (table.Team == "RB")]["RacePaceGapPct"].isna().all()
    prof = cars.season_profile(table)
    assert set(prof["Team"]) == {"RB", "FER", "MCL"} and prof["Rounds"].max() == 2
    assert cars.season_profile(cars.team_rounds({}, {})).empty
