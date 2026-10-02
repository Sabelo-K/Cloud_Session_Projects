"""Saved-session store and the sync command, using synthetic data (no network)."""
import numpy as np
import pandas as pd
import pytest

from f1 import data, store, sync


@pytest.fixture(autouse=True)
def _tmp_store(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "ROOT", tmp_path / "store")
    monkeypatch.delenv("F1_OFFLINE", raising=False)


def make_laps():
    rows = []
    for drv, base in (("VER", 90.0), ("HAM", 90.4)):
        for lap in range(1, 6):
            rows.append(dict(Driver=drv, Team="T", LapNumber=float(lap), LapTime=pd.Timedelta(seconds=base + lap * 0.1),
                             Time=pd.Timedelta(seconds=base * lap), Compound="SOFT", Deleted=None if lap == 1 else lap == 3,
                             TrackStatus="1", LapStartDate=pd.Timestamp("2026-09-27 13:00:00") + pd.Timedelta(seconds=base * lap)))
    laps = pd.DataFrame(rows)
    laps["Deleted"] = laps["Deleted"].astype(object)
    return laps


def make_tel(seed=0):
    d = np.arange(0, 5000, 20.0)
    return pd.DataFrame({"Distance": d, "Time": pd.to_timedelta(d / 80, unit="s"), "Speed": 200 + seed + 50 * np.sin(d / 400),
                         "Throttle": 100.0, "Brake": d % 400 < 40, "nGear": 6, "RPM": 11000.0, "DRS": 0, "X": d * 2.0, "Y": d * 3.0,
                         "Source": "interpolation"})


def save(mode="fastest"):
    laps = make_laps()
    picks = sync.laps_to_save(laps, mode)
    tel = {p: make_tel(i) for i, p in enumerate(picks)}
    corners = pd.DataFrame({"Number": [1, 2], "Distance": [300.0, 900.0], "X": [1.0, 2.0], "Y": [3.0, 4.0]})
    weather = pd.DataFrame({"Time": pd.to_timedelta([0, 60], unit="s"), "AirTemp": [20.0, 21.0], "Rainfall": [False, False]})
    store.write_session(2026, 13, "R", laps, weather, corners, tel, mode)
    return laps, picks


def test_laps_round_trip_keeps_dtypes_and_cleans_object_bools():
    laps, _ = save()
    back = store.read_laps(2026, 13, "R")
    assert len(back) == len(laps)
    assert back["LapTime"].dtype == laps["LapTime"].dtype
    assert pd.api.types.is_datetime64_any_dtype(back["LapStartDate"])
    assert back["Deleted"].dtype == bool and back["Deleted"].sum() == 2  # lap 3 for each driver; the None became False
    assert list(back["Driver"]) == list(laps["Driver"])


def test_laps_to_save_fastest_skips_deleted_and_all_keeps_every_timed_lap():
    laps = make_laps()
    assert sync.laps_to_save(laps, "none") == []
    assert dict(sync.laps_to_save(laps, "fastest")) == {"VER": 1, "HAM": 1}
    laps.loc[(laps.Driver == "VER") & (laps.LapNumber == 1), "Deleted"] = True
    assert dict(sync.laps_to_save(laps, "fastest"))["VER"] == 2
    assert len(sync.laps_to_save(laps, "all")) == 10 - 3  # VER lap 1 and both lap 3s are deleted


def test_telemetry_round_trip_and_missing_picks():
    save()
    got = store.read_telemetry(2026, 13, "R", (("VER", 1), ("HAM", 1), ("VER", 4)))
    assert set(got) == {"VER|1", "HAM|1"}  # lap 4 was never saved
    frame = got["VER|1"]
    assert list(frame.columns) == store.TELEMETRY_COLUMNS
    assert frame["Speed"].dtype == "float64" and frame["Brake"].dtype == bool
    assert frame["Time"].dtype == make_tel()["Time"].dtype
    assert np.allclose(frame["Distance"], make_tel()["Distance"])


def test_fastest_lap_pick_uses_laps_table():
    save()
    got = store.read_telemetry(2026, 13, "R", (("HAM", None),))
    assert list(got) == ["HAM|1"]


def test_no_telemetry_saved_returns_none_and_lists_nothing():
    save("none")
    assert store.read_telemetry(2026, 13, "R", (("VER", 1),)) is None
    assert store.stored_telemetry_laps(2026, 13, "R") == set()


def test_saved_sessions_index():
    save()
    assert store.saved_sessions()[0]["round"] == 13 and store.saved_rounds(2026) == [13] and store.saved_rounds(2025) == []
    assert store.has_session(2026, 13, "R") and not store.has_session(2026, 13, "Q")
    assert store.stored_telemetry_laps(2026, 13, "R") == {("VER", 1), ("HAM", 1)}


def test_data_reads_saved_sessions_without_fastf1(monkeypatch):
    save()
    monkeypatch.setattr(data, "_session", lambda *a, **k: pytest.fail("should not call FastF1"))
    monkeypatch.setenv("F1_OFFLINE", "1")
    assert len(data.load_session_laps(2026, 13, "R")) == 10
    assert set(data.load_lap_telemetry(2026, 13, "R", (("VER", 1), ("VER", 2)))) == {"VER|1"}
    assert len(data.load_corners(2026, 13, "R")) == 2
    assert len(data.load_weather(2026, 13, "R")) == 2


def test_offline_unsaved_session_raises_and_degrades(monkeypatch):
    monkeypatch.setattr(data, "_session", lambda *a, **k: pytest.fail("should not call FastF1"))
    monkeypatch.setenv("F1_OFFLINE", "1")
    with pytest.raises(store.NotSaved, match="python -m f1.sync --year 2026 --rounds 5 --sessions Q"):
        data.load_session_laps(2026, 5, "Q")
    assert data.load_lap_telemetry(2026, 5, "Q", (("VER", 1),)) == {}
    assert data.load_corners(2026, 5, "Q").empty and data.load_weather(2026, 5, "Q").empty


def test_offline_flag(monkeypatch):
    monkeypatch.setenv("F1_OFFLINE", "0")
    assert data.offline() is False
    monkeypatch.setenv("F1_OFFLINE", "1")
    assert data.offline() is True
    monkeypatch.delenv("F1_OFFLINE")
    assert data.offline() is False  # a normal checkout is not under /mount/


class FakeSession:
    def __init__(self, laps):
        self.laps = laps
        self.weather_data = pd.DataFrame({"Time": pd.to_timedelta([0], unit="s"), "AirTemp": [20.0]})


def test_sync_session_saves_then_app_reads_it(monkeypatch):
    laps = make_laps()
    monkeypatch.setattr(data, "_session", lambda *a, **k: FakeSession(laps))
    monkeypatch.setattr(data, "corners_frame", lambda s: pd.DataFrame({"Number": [1], "Distance": [1.0], "X": [0.0], "Y": [0.0]}))
    monkeypatch.setattr(data, "fetch_lap_telemetry", lambda s, d, n: make_tel())
    msgs = []
    assert sync.sync_session(2026, 13, "R", "fastest", log=msgs.append)
    assert "saved 10 laps and 2 telemetry laps" in msgs[-1]
    monkeypatch.setattr(data, "_session", lambda *a, **k: pytest.fail("saved data should be used"))
    assert len(data.load_session_laps(2026, 13, "R")) == 10


def test_sync_session_skips_sessions_that_fail_or_are_empty(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("no such session")
    monkeypatch.setattr(data, "_session", boom)
    msgs = []
    assert not sync.sync_session(2026, 13, "FP1", "fastest", log=msgs.append)
    assert "skipped (RuntimeError" in msgs[-1]
    monkeypatch.setattr(data, "_session", lambda *a, **k: FakeSession(pd.DataFrame()))
    assert not sync.sync_session(2026, 13, "FP1", "fastest", log=msgs.append)
    assert not store.saved_sessions()


def test_parse_rounds():
    assert sync.parse_rounds("13") == [13]
    assert sync.parse_rounds("10-13") == [10, 11, 12, 13]
    assert sync.parse_rounds("1, 3,5") == [1, 3, 5]
    assert sync.parse_rounds("all", 4) == [1, 2, 3, 4]
    with pytest.raises(ValueError):
        sync.parse_rounds("all")


def test_main_last_rounds(monkeypatch):
    sched = pd.DataFrame({"round": [1, 2, 3, 4], "name": list("abcd"), "date": ["2026-03-01", "2026-03-08", "2026-03-15", "2999-01-01"]})
    monkeypatch.setattr(data, "season_schedule", lambda y: sched)
    called = []
    monkeypatch.setattr(sync, "sync_session", lambda y, r, k, mode, log=print: called.append((y, r, k, mode)) or True)
    assert sync.main(["--year", "2026", "--last", "2", "--sessions", "R"]) == 0
    assert called == [(2026, 2, "R", "fastest"), (2026, 3, "R", "fastest")]
