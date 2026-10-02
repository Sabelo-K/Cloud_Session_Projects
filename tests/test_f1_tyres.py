import numpy as np
import pandas as pd

from f1 import charts, pace, tyres


def _stint(driver, stint, compounds, first_lap=1, life=None, fresh=True):
    rows = []
    for i, comp in enumerate(compounds):
        rows.append(dict(Driver=driver, Stint=stint, LapNumber=first_lap + i, Compound=comp,
                         TyreLife=(i + 1 if life is None else life[i]), FreshTyre=fresh,
                         LapTime=pd.Timedelta(seconds=90 + i * 0.1), PitInTime=pd.NaT, PitOutTime=pd.NaT,
                         TrackStatus="1"))
    return pd.DataFrame(rows)


def test_normalise_maps_missing_values_to_unknown():
    for bad in [None, np.nan, pd.NA, "", "None", "nan", "UNKNOWN", "TEST_UNKNOWN", " unknown "]:
        assert tyres.normalise(bad) == tyres.UNKNOWN
    assert tyres.normalise("soft") == "SOFT"
    assert tyres.normalise("Inter") == "INTERMEDIATE"


def test_letters_colours_names():
    assert [tyres.letter(c) for c in ["SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET", "None"]] == list("SMHIW?")
    assert tyres.name("None") == "Unknown" and tyres.name("HARD") == "Hard"
    assert len({tyres.colour(c) for c in tyres.ORDER}) == len(tyres.ORDER)
    assert tyres.rank("SOFT") < tyres.rank("HARD") < tyres.rank("UNKNOWN")


def test_repair_fills_gaps_inside_a_stint_only():
    laps = pd.concat([
        _stint("VER", 1, ["MEDIUM", "UNKNOWN", "MEDIUM", None]),
        _stint("VER", 2, ["None"] * 3, first_lap=5),          # nothing known: stays unknown
        _stint("HAM", 1, ["HARD", "HARD"], life=[3, np.nan]),
    ], ignore_index=True)
    out = tyres.repair(laps)
    assert list(out[(out.Driver == "VER") & (out.Stint == 1)]["Compound"]) == ["MEDIUM"] * 4
    assert set(out[(out.Driver == "VER") & (out.Stint == 2)]["Compound"]) == {"UNKNOWN"}
    assert list(out[out.Driver == "HAM"]["TyreLife"]) == [3, 4]  # age counted on from the known lap
    assert laps["Compound"].iloc[1] == "UNKNOWN"  # input untouched
    assert pd.isna(laps[laps.Driver == "HAM"]["TyreLife"].iloc[1])


def test_repair_leaves_age_unknown_when_no_lap_has_one():
    laps = _stint("PER", 2, ["None"] * 3, life=[np.nan] * 3)
    assert tyres.repair(laps)["TyreLife"].isna().all()


def test_repair_without_compound_column_is_a_no_op():
    laps = pd.DataFrame({"Driver": ["A"], "LapNumber": [1]})
    assert tyres.repair(laps) is laps


def test_unknown_note():
    laps = _stint("VER", 1, ["SOFT", "UNKNOWN", "None"])
    assert "2 laps" in tyres.unknown_note(laps)
    assert tyres.unknown_note(_stint("VER", 1, ["SOFT"] * 2)) is None


def test_stint_compound_uses_majority_not_first_lap():
    assert tyres.stint_compound(pd.Series(["UNKNOWN", "HARD", "HARD", "MEDIUM"])) == "HARD"
    assert tyres.stint_compound(pd.Series(["None", None])) == "UNKNOWN"


def test_degradation_ignores_unknown_tyres():
    known = _stint("VER", 1, ["SOFT"] * 8)
    unknown = _stint("HAM", 1, ["UNKNOWN"] * 8)
    deg = pace.compound_degradation(pd.concat([known, unknown], ignore_index=True))
    assert list(deg["Compound"]) == ["SOFT"]


def test_stint_summary_and_pit_stops_use_the_stint_compound():
    laps = pd.concat([_stint("VER", 1, ["UNKNOWN", "SOFT", "SOFT", "SOFT"]),
                      _stint("VER", 2, ["HARD"] * 4, first_lap=5, life=[1, 2, 3, 4])], ignore_index=True)
    summary = pace.stint_summary(laps)
    assert list(summary["Compound"]) == ["SOFT", "HARD"]
    stops = pace.pit_stops(laps)
    assert stops.iloc[0][["From", "To", "NewTyreAge"]].tolist() == ["SOFT", "HARD", 1]


def test_stint_timeline_labels_colours_and_unknown_hatching():
    laps = pd.concat([_stint("VER", 1, ["SOFT"] * 3, fresh=True),
                      _stint("VER", 2, ["None"] * 3, first_lap=4, fresh=False)], ignore_index=True)
    fig = charts.stint_timeline(tyres.repair(laps), ["VER"])
    soft, unknown = fig.data
    assert soft.marker.color == tyres.colour("SOFT") and soft.text[0] == "<b>S</b>"
    assert "new set" in soft.hovertemplate
    assert unknown.marker.color == tyres.colour("UNKNOWN") and unknown.text[0] == "<b>?</b>"
    assert unknown.marker.pattern.shape == "/" and "used set" in unknown.hovertemplate
    assert unknown.name == "Unknown" and soft.legendrank < unknown.legendrank
