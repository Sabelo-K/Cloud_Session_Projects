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


def test_parse_standings_tolerates_missing_position():
    payload = {"MRData": {"StandingsTable": {"StandingsLists": [{"DriverStandings": [
        {"points": "0", "positionText": "-", "Driver": {"code": "ZZZ", "familyName": "Zed"}}]}]}}}
    df = standings.parse_standings(payload, 3)
    assert df.loc[0, "Driver"] == "ZZZ" and pd.isna(df.loc[0, "Position"])


def _stack_res(labels):
    import numpy as np
    d = np.arange(0.0, 500.0, 5.0)
    return {l: pd.DataFrame({"Distance": d, "Speed": d, "Throttle": d / 5, "Brake": d * 0, "nGear": d * 0 + 3, "RPM": d * 20}) for l in labels}


def test_telemetry_stack_trace_style():
    from f1 import charts
    fig = charts.telemetry_stack(_stack_res(["LEC|5", "HAM|7"]), {"LEC": "#E8002D", "HAM": "#E8002D"}, {})
    assert fig.layout.hovermode == "x unified"
    assert fig.layout.plot_bgcolor == charts.TRACE_BG
    assert [b.label for b in fig.layout.updatemenus[0].buttons] == ["Reset Zoom"]
    assert {t.name for t in fig.data} == {"LEC", "HAM"}  # one lap per driver: short tooltip names


def test_telemetry_stack_keeps_lap_in_name_for_two_laps_of_one_driver():
    from f1 import charts
    fig = charts.telemetry_stack(_stack_res(["LEC|5", "LEC|7"]), {"LEC": "#E8002D"}, {})
    assert {t.name for t in fig.data} == {"LEC · lap 5", "LEC · lap 7"}


def test_long_run_violin_one_violin_per_driver_with_tyre_legend():
    from f1 import charts
    runs = pd.DataFrame({"Driver": ["VER"] * 3 + ["NOR"] * 3, "Adjusted": [90.1, 90.3, 90.2, 90.6, 90.5, 90.7],
                         "LapNumber": [1, 2, 3, 1, 2, 3], "Compound": ["SOFT", "SOFT", "MEDIUM", "MEDIUM"] * 1 + ["HARD", "HARD"][:2]})
    fig = charts.long_run_violin(runs, {"VER": "#3671C6", "NOR": "#FF8000"})
    assert [t.name for t in fig.data if t.type == "violin"] == ["VER", "NOR"]  # quickest average first
    assert {t.name for t in fig.data if t.type == "scatter"} == {"SOFT", "MEDIUM", "HARD"}
    assert "+0.400s" in fig.layout.annotations[1].text


def test_speed_with_corners_hover_lists_every_driver_and_the_corner():
    from f1 import charts
    res = {k: df.assign(TimeS=df["Distance"] / 80.0) for k, df in _stack_res(["LEC|5", "HAM|7"]).items()}
    corners = pd.DataFrame({"Number": [1, 2], "Distance": [100.0, 400.0]})
    fig = charts.speed_with_corners(res, {"LEC": "#E8002D", "HAM": "#E8002D"}, {}, corners)
    assert fig.layout.hovermode == "x unified"
    speed = [t for t in fig.data if t.yaxis == "y"]
    assert len(speed) == 2 and all("km/h" in t.hovertemplate for t in speed)
    assert speed[0].customdata[20] == "Corner T1<br>" and speed[0].customdata[0] == ""  # tag only within 60 m of a corner
    assert speed[0].customdata[50] == ""  # 250 m is far from both corners


def _two_laps(lap_a=90.0, lap_b=90.4):
    """Two laps round the same circle; B's Distance channel drifts 40 m ahead mid-lap (as a dropout does)."""
    import numpy as np
    out = {}
    for name, lap in (("A|1", lap_a), ("B|1", lap_b)):
        t = np.linspace(0, lap, 600)
        ang = 2 * np.pi * t / lap
        dist = 5000 * t / lap + (40 * (t > lap / 2) if name == "B|1" else 0)
        out[name] = pd.DataFrame({"Distance": dist, "Time": pd.to_timedelta(t, unit="s"), "Speed": 200.0, "X": 800 * np.cos(ang),
                                  "Y": 800 * np.sin(ang), "Throttle": 100.0, "RPM": 11000.0, "Brake": 0.0, "nGear": 6, "DRS": 0})
    return out


def test_delta_follows_track_position_not_distance_and_ends_at_the_lap_time_gap():
    import numpy as np
    res = telemetry.resample_all(_two_laps(), step=5.0)
    d = telemetry.delta_vs_reference(res, "A|1")["B|1"]
    assert d.iloc[0] == 0 and abs(d.iloc[-1] - 0.4) < 1e-6  # B is 0.4 s slower over the lap
    assert d.iloc[:-10].diff().abs().max() < 0.05  # no jump where B's Distance channel drifted (the last few points sit at the cut)


def test_delta_pins_to_sector_times():
    res = telemetry.resample_all(_two_laps(), step=5.0)
    splits = {"A|1": (30.0, 30.0, 30.0), "B|1": (30.3, 30.0, 30.1)}  # B loses 0.3 s in S1, level in S2, 0.1 s more in S3
    d = telemetry.delta_vs_reference(res, "A|1", splits)["B|1"]
    rt = res["A|1"]["TimeS"].to_numpy()
    assert abs(d.iloc[(abs(rt - 30.0)).argmin()] - 0.3) < 0.02
    assert abs(d.iloc[(abs(rt - 60.0)).argmin()] - 0.3) < 0.02


def test_stint_degradation_one_trace_per_stint_dashed_after_first():
    import pandas as pd
    from f1 import charts, pace, tyres

    rows = [{"Driver": "VER", "Stint": s, "LapNumber": n, "LapSeconds": 90 + 0.1 * n, "Compound": "HARD" if s == 1 else "MEDIUM",
             "LapInRun": n - (1 if s == 1 else 11), "Run": f"VER S{s}", "Adjusted": 90 + 0.1 * n}
            for s, laps in ((1, range(1, 9)), (2, range(11, 19))) for n in laps]
    runs = pd.DataFrame(rows)
    summary = pd.DataFrame({"Run": ["VER S1", "VER S2"], "Driver": "VER", "Stint": [1, 2], "Compound": ["HARD", "MEDIUM"]})
    label = {r: f"{r} {tyres.letter(c)}" for r, c in zip(summary["Run"], summary["Compound"])}
    fig = charts.stint_degradation(runs, summary, {"VER": "#3671C6"}, label)
    assert [t.name for t in fig.data] == list(label.values())
    assert [t.line.dash for t in fig.data] == ["solid", "dash"]
    assert fig.layout.legend.itemclick == "toggle"


def test_speed_map_colours_by_channel_and_fills_gaps():
    import numpy as np
    import pandas as pd
    from f1 import charts

    n = 40
    tel = pd.DataFrame({"X": np.linspace(0, 400, n), "Y": np.zeros(n), "Speed": np.linspace(100, 300, n),
                        "nGear": np.repeat([3, 5, 7, 8], n // 4), "Throttle": np.full(n, 100.0), "Brake": [False] * n})
    fig = charts.speed_map(tel)
    dots = fig.data[-1]
    assert len(dots.x) > n  # densified
    assert min(dots.marker.color) == 100 and max(dots.marker.color) == 300
    assert "Speed" in dots.hovertemplate and "Brake" in dots.hovertemplate
    gear = charts.speed_map(tel, "nGear").data[-1]
    assert set(gear.marker.color) == {3, 5, 7, 8}
    assert list(gear.marker.colorbar.tickvals) == [3, 4, 5, 6, 7, 8]
