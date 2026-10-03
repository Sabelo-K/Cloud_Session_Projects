import math

from f1 import headtohead
from tests.test_f1_summary_cars import quali, race


def test_weekend_rows_gaps_are_b_minus_a():
    rows = headtohead.weekend_rows({1: quali()}, {1: race()}, "VER", "NOR")
    r = rows.iloc[0]
    assert (r["GridA"], r["GridB"]) == (1, 3)
    assert round(r["QualiGap"], 3) == 1.0  # NOR 81.0 vs VER 80.0: positive means A (VER) was quicker
    assert (r["FinishA"], r["FinishB"]) == (2, 1)
    assert r["PaceGap"] < 0  # NOR's clean laps are quicker in the race


def test_scoreboard_counts_weekends_and_averages():
    rows = headtohead.weekend_rows({1: quali(), 2: quali()}, {1: race()}, "VER", "NOR")
    board = headtohead.scoreboard(rows)
    assert board["quali"] == {"a": 2, "b": 0, "rounds": 2, "avg_gap": 1.0}
    assert (board["finish"]["a"], board["finish"]["b"], board["finish"]["rounds"]) == (0, 1, 1)
    assert board["finish"]["avg_places"] == -1.0  # NOR finished one place ahead of VER
    assert board["pace"]["rounds"] == 1


def test_driver_missing_from_a_session_is_skipped_not_counted():
    rows = headtohead.weekend_rows({1: quali()}, {1: race()}, "VER", "ZZZ")
    assert math.isnan(rows.iloc[0]["QualiGap"])
    board = headtohead.scoreboard(rows)
    assert board["quali"]["rounds"] == 0 and math.isnan(board["quali"]["avg_gap"])
