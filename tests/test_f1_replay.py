import numpy as np
import pandas as pd

from f1 import charts, replay


def tel(duration=10.0, speed_offset=0.0):
    t = np.linspace(0, duration, 201)
    d = np.linspace(0, 1000, 201)
    return pd.DataFrame({"Distance": d, "Time": pd.to_timedelta(t, unit="s"), "Speed": 200 + speed_offset + 10 * np.sin(t),
                         "Throttle": 100.0, "Brake": t > 8, "nGear": np.where(t < 5, 5, 6), "RPM": 10000.0, "DRS": 0,
                         "X": d * 2.0, "Y": d * 1.0})


def run(label="NOR", duration=10.0, splits=(3.0, 3.5, 3.5), colour="#FF8000", tyre="SOFT", speed_offset=0.0):
    return dict(label=label, colour=colour, tl=replay.timeline(tel(duration, speed_offset)), splits=splits, lap_time=duration,
                tyre=tyre, lap=7)


def test_timeline_is_regular_and_ends_at_the_lap_end():
    tl = replay.timeline(tel())
    assert tl["T"].iloc[0] == 0 and abs(tl["T"].iloc[-1] - 10.0) < 1e-9
    assert np.allclose(np.diff(tl["T"].iloc[:-2]), replay.STEP)
    assert set(tl.columns) == {"T", "X", "Y", "Speed", "Throttle", "nGear", "Brake"}
    assert tl["nGear"].iloc[0] == 5 and tl["nGear"].iloc[-1] == 6 and not tl["Brake"].iloc[0] and tl["Brake"].iloc[-1]


def test_splits_from_row_needs_all_three_sectors():
    row = {"Sector1Time": pd.Timedelta(seconds=28.5), "Sector2Time": pd.Timedelta(seconds=30), "Sector3Time": pd.Timedelta(seconds=25.25)}
    assert replay.splits_from_row(row) == (28.5, 30.0, 25.25)
    assert replay.splits_from_row({**row, "Sector2Time": pd.NaT}) is None
    assert replay.splits_from_row({}) is None


def test_sectors_appear_only_after_the_car_passes_them():
    r = run()
    assert replay.state_at(r, 0.0)["sectors"] == [None, None, None]
    assert replay.state_at(r, 2.9)["sectors"] == [None, None, None]
    assert replay.state_at(r, 3.0)["sectors"] == [3.0, None, None]
    assert replay.state_at(r, 6.6)["sectors"] == [3.0, 3.5, None]
    last = replay.state_at(r, 10.0)
    assert last["sectors"] == [3.0, 3.5, 3.5] and last["finished"]
    assert replay.state_at(r, 99.0)["clock"] == 10.0  # a finished lap stops the clock


def test_state_reports_position_speed_and_gear_at_the_moment():
    st = replay.state_at(run(), 5.0)
    assert abs(st["x"] - 1000.0) < 15 and st["gear"] in (5, 6) and 189 < st["speed"] < 211


def test_quickest_sector_is_purple_among_two_or_more():
    a = run("A", splits=(3.0, 3.6, 3.4))
    b = run("B", splits=(3.1, 3.5, 3.4))
    cols = replay.sector_colours([a, b])
    assert cols[0] == [replay.PURPLE, replay.WHITE, replay.PURPLE] and cols[1] == [replay.WHITE, replay.PURPLE, replay.PURPLE]
    assert replay.sector_colours([a]) == [[replay.WHITE] * 3]
    assert replay.sector_colours([a, run("C", splits=None)])[0] == [replay.WHITE] * 3  # nothing to compare against


def test_panel_text_fills_in_as_time_passes_and_handles_missing_splits():
    runs = [run("NOR"), run("PIA", splits=None, tyre="MEDIUM", colour="#FF8000")]
    early = replay.panel_html(runs, 1.0)
    late = replay.panel_html(runs, 10.0)
    assert "NOR" in early and "S1 <span" in early and "3.000" not in early
    assert "3.000" in late and "3.500" in late and "finished" in late and "Soft" in late and "Medium" in late
    assert replay.fmt_time(85.4) == "1:25.400" and replay.fmt_time(28.123) == "28.123"


def test_results_table():
    t = replay.results_table([run("NOR"), run("PIA", splits=None)])
    assert list(t["Driver"]) == ["NOR", "PIA"] and t["S1"].tolist() == ["3.000", ""] and t["Lap time"].iloc[0] == "10.000"


def test_replay_figure_has_a_frame_per_step_and_play_controls():
    runs = [run("NOR"), run("PIA", duration=10.5, speed_offset=5)]
    fig = charts.lap_replay(runs, speed=2.0)
    assert len(fig.frames) == len(runs[1]["tl"])  # as many as the longest lap
    assert [b.label for b in fig.layout.updatemenus[0].buttons] == ["▶ Play", "⏸ Pause", "↺ Reset"]
    assert fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] == 50  # 0.1 s of lap per 50 ms at 2x
    last = fig.frames[-1]
    assert last.layout.annotations[0].text.count("finished") == 2
    assert "3.000" in fig.frames[40].layout.annotations[0].text  # S1 has been passed by 4 s
    # the shorter lap's dot waits at the line while the longer one finishes
    assert fig.frames[-1].data[1].x[0] == fig.frames[len(runs[0]["tl"]) - 1].data[1].x[0]
