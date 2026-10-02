import json

import pandas as pd
import pytest

from f1 import league


@pytest.fixture(autouse=True)
def _tmp_league(tmp_path, monkeypatch):
    monkeypatch.setattr(league, "ROOT", tmp_path / "league")


RESULT = {"pole": "NOR", "podium": ["VER", "NOR", "PIA"], "fastest": "HAM"}


def test_score_exact_wrong_place_and_bonuses():
    exact = {"pole": "NOR", "podium": ["VER", "NOR", "PIA"], "fastest": "HAM"}
    assert league.score(exact, RESULT)["total"] == league.MAX_POINTS == 21
    shuffled = {"pole": "VER", "podium": ["NOR", "VER", "PIA"], "fastest": "LEC"}
    s = league.score(shuffled, RESULT)
    assert (s["podium"], s["pole"], s["fastest"]) == (2 + 2 + 5, 0, 0)
    miss = {"pole": "RUS", "podium": ["LEC", "RUS", "HAM"], "fastest": "HAM"}
    assert league.score(miss, RESULT)["total"] == 3  # only the fastest lap


def test_add_prediction_validates_and_replaces():
    lg = {"players": [], "rounds": {}}
    with pytest.raises(ValueError):
        league.add_prediction(lg, 3, " ", "NOR", ["A", "B", "C"], "NOR")
    with pytest.raises(ValueError):
        league.add_prediction(lg, 3, "Sabelo", "NOR", ["A", "A", "C"], "NOR")
    with pytest.raises(ValueError):
        league.add_prediction(lg, 3, "Sabelo", "", ["A", "B", "C"], "NOR")
    one = league.add_prediction(lg, 3, "Sabelo", "NOR", ["A", "B", "C"], "NOR")
    two = league.add_prediction(one, 3, "Sabelo", "VER", ["C", "B", "A"], "VER")
    assert lg == {"players": [], "rounds": {}}  # input untouched
    assert two["players"] == ["Sabelo"] and two["rounds"]["3"]["Sabelo"]["pole"] == "VER"


def test_save_and_load_round_trip_and_bad_file():
    assert league.load(2026) == {"players": [], "rounds": {}}
    lg = league.add_prediction({"players": [], "rounds": {}}, 13, "Sabelo", "NOR", ["VER", "NOR", "PIA"], "HAM")
    league.save(2026, lg)
    assert league.load(2026) == lg
    league.path_for(2026).write_text("{not json")
    assert league.load(2026) == {"players": [], "rounds": {}}


def test_leaderboard_orders_by_points_and_skips_unscored_rounds():
    lg = {"players": ["A", "B"], "rounds": {
        "1": {"A": {"pole": "NOR", "podium": ["VER", "NOR", "PIA"], "fastest": "HAM"},
              "B": {"pole": "VER", "podium": ["LEC", "RUS", "HAM"], "fastest": "VER"}},
        "2": {"B": {"pole": "VER", "podium": ["VER", "NOR", "PIA"], "fastest": "HAM"}}}}   # round 2 has no result
    board = league.leaderboard(lg, {1: RESULT})
    assert list(board["Player"]) == ["A", "B"] and list(board["Points"]) == [21, 0]
    assert list(board["Rounds"]) == [1, 1] and "R2" not in board.columns
    assert league.leaderboard({"players": [], "rounds": {}}, {}).empty


def test_result_from_laps_needs_a_saved_race():
    def laps(order):
        rows = []
        for i, d in enumerate(order):
            for n in (1, 2):
                rows.append(dict(Driver=d, Team="T", LapNumber=n, LapTime=pd.Timedelta(seconds=90 + i + n * 0.1),
                                 Time=pd.Timedelta(seconds=n * 90 + i), Stint=1, Compound="SOFT", TyreLife=float(n)))
        return pd.DataFrame(rows)
    assert league.result_from_laps(None, None) is None
    assert league.result_from_laps(None, laps(["A", "B"])) is None  # fewer than three finishers
    res = league.result_from_laps(laps(["Q", "R", "S"]), laps(["A", "B", "C", "D"]))
    assert res == {"pole": "Q", "podium": ["A", "B", "C"], "fastest": "A"}


def test_main_pushes_league_folder(monkeypatch):
    from f1 import sync
    seen = []
    monkeypatch.setattr(sync, "git_push", lambda message, log=print, path="f1/store": seen.append(path) or True)
    assert league.main(["--push"]) == 0 and seen == ["f1/league"]
