import pandas as pd

from f1 import pace


def _laps():
    rows = []
    for drv, base in (("VER", 90.0), ("NOR", 90.5)):
        for lap in range(1, 11):
            rows.append(dict(Driver=drv, LapNumber=lap, Stint=1, Compound="MEDIUM",
                             LapTime=pd.Timedelta(seconds=base + 0.1 * lap),
                             PitInTime=pd.NaT, PitOutTime=pd.NaT, TrackStatus="1"))
    df = pd.DataFrame(rows)
    df["PitOutTime"] = pd.Series([pd.NaT] * len(df), dtype="timedelta64[ns]")
    df["PitInTime"] = pd.Series([pd.NaT] * len(df), dtype="timedelta64[ns]")
    df.loc[0, "PitOutTime"] = pd.Timedelta(seconds=1)          # out lap, dropped
    df.loc[1, "TrackStatus"] = "4"                              # safety car, dropped
    df.loc[2, "LapTime"] = pd.Timedelta(seconds=120)            # outlier, dropped
    df.loc[3, "LapTime"] = pd.NaT                               # no time, dropped
    return df


def test_clean_laps_drops_pit_sc_outlier_and_missing():
    c = pace.clean_laps(_laps())
    ver = c[c["Driver"] == "VER"]
    assert sorted(ver["LapNumber"]) == [5, 6, 7, 8, 9, 10]
    assert len(c[c["Driver"] == "NOR"]) == 10


def test_race_pace_orders_and_gap():
    p = pace.race_pace(_laps())
    assert list(p["Driver"]) == ["VER", "NOR"]
    assert p["gap_to_best"].iloc[0] == 0
    assert p["gap_to_best"].iloc[1] > 0.2


def test_stint_summary_degradation_slope():
    s = pace.stint_summary(_laps())
    nor = s[s["Driver"] == "NOR"].iloc[0]
    assert abs(nor["deg_per_lap"] - 0.1) < 1e-6
    assert nor["StartLap"] == 1 and nor["EndLap"] == 10


def test_lap_chart_frame_blanks_dirty_laps_unless_show_all():
    df = _laps()
    hidden = pace.lap_chart_frame(df)
    assert hidden["LapSeconds"].isna().sum() == 4  # pit-out, SC, outlier, missing
    shown = pace.lap_chart_frame(df, show_all=True)
    assert shown["LapSeconds"].isna().sum() == 1  # only the genuinely missing time


def test_compound_degradation_recovers_slope():
    rows = []
    for lap in range(1, 21):
        rows.append(dict(Driver="VER", LapNumber=lap, Stint=1, Compound="SOFT", TyreLife=lap,
                         LapTime=pd.Timedelta(seconds=90 + 0.08 * lap - 0.03 * lap),  # 0.08 deg, fuel -0.03
                         PitInTime=pd.NaT, PitOutTime=pd.NaT, TrackStatus="1"))
    df = pd.DataFrame(rows)
    df["PitOutTime"] = pd.Series([pd.NaT] * len(df), dtype="timedelta64[ns]")
    df["PitInTime"] = pd.Series([pd.NaT] * len(df), dtype="timedelta64[ns]")
    deg = pace.compound_degradation(df)
    assert abs(deg.loc[0, "deg_per_lap"] - 0.08) < 1e-6
