"""Tyre names, colours and clean-up shared by every page. Pure pandas, no network.

The timing feed is patchy: some laps arrive with the compound missing, 'UNKNOWN' or the text 'None', and the tyre age
(TyreLife) can be blank. `repair` fixes what can be proven from the rest of the stint and labels everything else
'UNKNOWN' so it is shown as unknown instead of being drawn as a made-up compound."""
from __future__ import annotations

import pandas as pd

UNKNOWN = "UNKNOWN"
ORDER = ["SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET", UNKNOWN]
COLOURS = {"SOFT": "#E8002D", "MEDIUM": "#FFD60A", "HARD": "#F2F3F5",
           "INTERMEDIATE": "#30D158", "WET": "#3E7BFA", UNKNOWN: "#6B7683"}
LETTERS = {"SOFT": "S", "MEDIUM": "M", "HARD": "H", "INTERMEDIATE": "I", "WET": "W", UNKNOWN: "?"}
_ALIASES = {"INTER": "INTERMEDIATE", "INTERMEDIATES": "INTERMEDIATE", "WETS": "WET"}
_MISSING = {"", "NAN", "NONE", "NULL", "<NA>", "UNKNOWN", "TEST_UNKNOWN", "TEST-UNKNOWN", "N/A"}


def normalise(value) -> str:
    """One of SOFT / MEDIUM / HARD / INTERMEDIATE / WET / UNKNOWN (anything else the feed sends is kept upper-case)."""
    if value is None or (not isinstance(value, str) and pd.isna(value)):
        return UNKNOWN
    text = str(value).strip().upper()
    if text in _MISSING:
        return UNKNOWN
    return _ALIASES.get(text, text)


def letter(compound) -> str:
    c = normalise(compound)
    return LETTERS.get(c, c[:1])


def colour(compound) -> str:
    return COLOURS.get(normalise(compound), COLOURS[UNKNOWN])


def text_colour(compound) -> str:
    """Readable label colour on top of the compound's colour."""
    return "#FFFFFF" if normalise(compound) in ("SOFT", "WET", UNKNOWN) else "#090B0E"


def name(compound) -> str:
    c = normalise(compound)
    return "Unknown" if c == UNKNOWN else c.capitalize()


def rank(compound) -> int:
    c = normalise(compound)
    return ORDER.index(c) if c in ORDER else len(ORDER)


def stint_compound(compounds: pd.Series) -> str:
    """The compound of a stint: the most common known one (a stint is one set of tyres), UNKNOWN if none is known."""
    known = compounds.map(normalise)
    known = known[known != UNKNOWN]
    return known.mode().iloc[0] if len(known) else UNKNOWN


def _fill_age(g: pd.DataFrame) -> pd.Series:
    """TyreLife for a stint with gaps: count on from the nearest lap whose age is known (age grows by one per lap)."""
    age = g["TyreLife"]
    known = age.dropna()
    if known.empty or len(known) == len(age):
        return age
    laps = g["LapNumber"].astype(float)
    anchor = (age - laps).dropna().median()  # age - lap number is constant within a stint
    return age.fillna(laps + anchor)


def repair(laps: pd.DataFrame) -> pd.DataFrame:
    """Laps with a clean `Compound` column (names normalised, gaps inside a stint filled from the rest of the stint)
    and gaps in `TyreLife` filled inside stints whose age is known on other laps. Stints with no compound
    information stay UNKNOWN. Other columns are untouched."""
    if "Compound" not in laps.columns:
        return laps
    df = laps.copy()
    df["Compound"] = df["Compound"].map(normalise)
    if "Stint" not in df.columns:
        return df
    has_stint = df["Stint"].notna()
    for _, idx in df[has_stint].groupby(["Driver", "Stint"]).groups.items():
        g = df.loc[idx]
        if (g["Compound"] == UNKNOWN).any():
            df.loc[idx, "Compound"] = g["Compound"].where(g["Compound"] != UNKNOWN, stint_compound(g["Compound"]))
        if "TyreLife" in df.columns and "LapNumber" in df.columns and g["TyreLife"].isna().any():
            df.loc[idx, "TyreLife"] = _fill_age(g)
    return df


def unknown_note(laps: pd.DataFrame) -> str | None:
    """A sentence telling the user how many laps have no tyre information, or None when all are known."""
    if "Compound" not in laps.columns:
        return None
    n = int((laps["Compound"].map(normalise) == UNKNOWN).sum())
    if not n:
        return None
    return (f"{n} lap{'s' if n != 1 else ''} in this session ha{'ve' if n != 1 else 's'} no tyre information from the "
            "timing feed. They are shown as Unknown and left out of tyre-degradation figures.")
