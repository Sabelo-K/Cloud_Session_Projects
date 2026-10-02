import numpy as np
import pandas as pd

from f1 import pace, sectors, telemetry


def _td(col):
    return pd.Series(col, dtype="timedelta64[ns]")


def _race():
    """3 drivers x 10 laps. Lap 2 is a pit lap for VER, lap 3 is under yellow for HAM."""
    rows = []
    base = {"VER": 90.0, "HAM": 90.5, "LEC": 91.0}
    clock = {d: 0.0 for d in base}
    for lap in range(1, 11):
        for pos, d in enumerate(["VER", "HAM", "LEC"], start=1):
            t = base[d] + 0.02 * lap
            clock[d] += t
            rows.append(dict(Driver=d, Team="T" + d, LapNumber=lap, Stint=1 if lap < 6 else 2, Compound="SOFT",
                             LapTime=pd.Timedelta(seconds=t), Time=pd.Timedelta(seconds=clock[d]), Position=pos,
                             PitInTime=pd.Timedelta(seconds=1) if (d == "VER" and lap == 2) else pd.NaT,
                             PitOutTime=pd.NaT, TrackStatus="2" if (d == "HAM" and lap == 3) else "1"))
    df = pd.DataFrame(rows)
    df["PitInTime"] = pd.to_timedelta(df["PitInTime"])
    df["PitOutTime"] = _td([pd.NaT] * len(df))
    return df


def test_tag_laps_gives_reasons():
    t = pace.tag_laps(_race())
    ver2 = t[(t.Driver == "VER") & (t.LapNumber == 2)].iloc[0]
    ham3 = t[(t.Driver == "HAM") & (t.LapNumber == 3)].iloc[0]
    assert ver2["Excluded"] and "pit" in ver2["Reason"]
    assert ham3["Excluded"] and "not green" in ham3["Reason"]
    assert len(pace.clean_laps(_race())) == 28


def test_distribution_stats():
    d = pace.distribution_stats(_race())
    assert list(d["Driver"]) == ["VER", "HAM", "LEC"]
    assert d["delta_to_best"].iloc[0] == 0 and abs(d["delta_to_best"].iloc[2] - 1.0) < 0.05
    assert (d["min"] <= d["q1"]).all() and (d["q3"] <= d["max"]).all()


def test_gap_to_leader_negative_behind():
    g = pace.gap_to_leader(_race())
    last = g[g.LapNumber == 10].set_index("Driver")["GapToLeader"]
    assert last["VER"] == 0 and last["HAM"] < 0 and last["LEC"] < last["HAM"]


def test_consistency_detrended_ignores_linear_trend():
    c = pace.consistency(_race(), detrend=True, min_laps=3)
    assert (c["std"] < 1e-9).all()  # perfectly linear degradation -> no inconsistency
    raw = pace.consistency(_race(), detrend=False, min_laps=3)
    assert (raw["std"] > 0).all()


def test_traffic_counts_laps_close_to_car_ahead():
    t = pace.traffic(_race(), threshold=1.5).set_index("Driver")
    assert t.loc["VER", "in_traffic"] == 0  # leader never has a car ahead
    assert t.loc["HAM", "in_traffic"] >= 1  # early laps: gap to VER is only ~0.5-1.4s
    assert t.loc["LEC", "in_traffic"] >= t.loc["HAM", "in_traffic"]


def test_long_runs_and_run_summary():
    laps = _race()
    runs = pace.long_runs(laps, min_laps=4)
    assert set(runs["Run"]) == {"VER S1", "VER S2", "HAM S1", "HAM S2", "LEC S1", "LEC S2"}
    s = pace.run_summary(runs).set_index("Run")
    assert abs(s.loc["LEC S2", "slope"] - 0.02) < 1e-9
    assert abs(pace.run_summary(runs, fuel_effect=0.02).set_index("Run").loc["LEC S2", "slope"] - 0.04) < 1e-9


def test_season_deficit_percent():
    out = pace.season_deficit({1: _race(), 2: _race()})
    lec = out[(out.Round == 1) & (out.Driver == "LEC")].iloc[0]
    assert lec["deficit_s"] > 0.9 and 1.0 < lec["deficit_pct"] < 1.2
    assert set(out["Round"]) == {1, 2}


# ---- sectors ----

def _sector_laps():
    mk = lambda *s: [pd.Timedelta(seconds=x) for x in s]
    df = pd.DataFrame({
        "Driver": ["A", "A", "B"],
        "Sector1Time": mk(20, 21, 20.5), "Sector2Time": mk(30, 29.5, 30.2), "Sector3Time": mk(25, 25.5, 24.8),
        "LapTime": mk(75, 76, 75.5), "Deleted": [False, False, False],
    })
    return df


def test_best_sectors_and_ultimate():
    best = sectors.best_sectors(_sector_laps()).set_index("Driver")
    assert best.loc["A", "Theoretical"] == 20 + 29.5 + 25
    assert best.loc["A", "Unused"] == 75 - 74.5
    u = sectors.ultimate_lap(sectors.best_sectors(_sector_laps()))
    assert u["owners"] == {"S1": "A", "S2": "A", "S3": "B"} and abs(u["total"] - 74.3) < 1e-9


def test_sector_deficits_ranked():
    d = sectors.sector_deficits(sectors.best_sectors(_sector_laps()))
    assert list(d["Driver"]) == ["A", "B"]
    assert abs(d["Total"].iloc[0] - 0.2) < 1e-9 and abs(d["Total"].iloc[1] - 1.2) < 1e-9
    assert d["Total"].is_monotonic_increasing


def test_deleted_laps_are_ignored():
    laps = _sector_laps()
    laps.loc[0, "Deleted"] = True
    best = sectors.best_sectors(laps).set_index("Driver")
    assert best.loc["A", "S1"] == 21


def test_sector_regions():
    tel = pd.DataFrame({"Time": pd.to_timedelta(np.arange(0, 10, 1.0), unit="s")})
    r = sectors.sector_regions(tel, s1=3.0, s2=4.0)
    assert list(r) == [1, 1, 1, 2, 2, 2, 2, 3, 3, 3]


# ---- telemetry ----

def _lap(speed, secs_per_100m=2.0, brake_from=300, length=1000.0):
    dist = np.arange(0, length + 1, 7.3)
    return pd.DataFrame({
        "Distance": dist, "Speed": speed + 50 * np.sin(dist / 150), "Throttle": 100.0, "RPM": 10000.0,
        "nGear": (dist // 200 + 3).astype(int), "Brake": dist > brake_from, "X": dist * 10, "Y": np.sin(dist / 300) * 500,
        "Time": pd.to_timedelta(dist / 100 * secs_per_100m + 600, unit="s"),
    })


def test_resample_keeps_discrete_values():
    r = telemetry.resample_lap(_lap(200), step=5.0)
    assert set(r["Brake"].unique()) <= {0.0, 1.0}
    assert set(r["nGear"].unique()) <= set(range(3, 9))
    assert r["TimeS"].iloc[0] == 0


def test_resample_all_same_grid():
    res = telemetry.resample_all({"a": _lap(200, length=1000), "b": _lap(200, length=900)}, step=5.0)
    assert len(res["a"]) == len(res["b"])


def test_delta_vs_reference_sign():
    res = telemetry.resample_all({"fast": _lap(200, 2.0), "slow": _lap(200, 2.1)})
    d = telemetry.delta_vs_reference(res, "fast")
    assert d["fast"].abs().max() == 0 and d["slow"].iloc[-1] > 0.9  # slower => positive


def test_track_dominance_winner_and_gain():
    res = telemetry.resample_all({"fast": _lap(200, 2.0), "slow": _lap(200, 2.2)})
    dom = telemetry.track_dominance(res, segment_m=50)
    assert (dom["Winner"] == "fast").all() and (dom["Gain"] > 0).all()
    assert len(dom) == 20


def test_corner_speeds_and_wins():
    fast, slow = _lap(220), _lap(180)
    res = telemetry.resample_all({"fast": fast, "slow": slow})
    corners = pd.DataFrame({"Number": [1, 2], "Distance": [236.0, 700.0]})
    cs = telemetry.corner_speeds(res, corners, window=40, threshold=150)
    assert set(cs["Corner"]) == {1, 2} and (cs[cs["Winner"]]["Lap"] == "fast").all()
    w = telemetry.apex_wins(cs)
    assert w[w["Lap"] == "fast"]["Wins"].sum() == 2
    # corner distances given in 1/10 m are rescaled
    cs10 = telemetry.corner_speeds(res, corners.assign(Distance=corners["Distance"] * 10), window=40)
    assert set(cs10["Corner"]) == {1, 2}


def test_run_summary_residual_std_zero_for_linear_run():
    s = pace.run_summary(pace.long_runs(_race(), min_laps=4))
    assert (s["resid_std"] < 1e-9).all()


def test_pit_stops():
    laps = _race()
    laps["Compound"] = ["SOFT" if x < 6 else "HARD" for x in laps["LapNumber"]]
    laps["TyreLife"] = [x if x < 6 else x - 5 for x in laps["LapNumber"]]
    stops = pace.pit_stops(laps)
    ver = stops[stops.Driver == "VER"].iloc[0]
    assert ver["Lap"] == 5 and ver["From"] == "SOFT" and ver["To"] == "HARD" and ver["NewTyreAge"] == 1
    assert len(stops) == 3
