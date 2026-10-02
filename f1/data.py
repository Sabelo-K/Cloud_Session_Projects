"""Data access: FastF1 for laps, Jolpica (Ergast successor) for schedule/results."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import requests

JOLPICA = "https://api.jolpi.ca/ergast/f1"
CACHE_DIR = Path(".fastf1-cache")


def season_schedule(year: int) -> pd.DataFrame:
    r = requests.get(f"{JOLPICA}/{year}.json", timeout=20)
    r.raise_for_status()
    races = r.json()["MRData"]["RaceTable"]["Races"]
    return pd.DataFrame(
        [{"round": int(x["round"]), "name": x["raceName"], "date": x["date"]} for x in races]
    )


def load_race_laps(year: int, round_no: int) -> pd.DataFrame:
    import fastf1  # imported lazily: heavy, and not needed for pace tests

    CACHE_DIR.mkdir(exist_ok=True)
    fastf1.Cache.enable_cache(str(CACHE_DIR))
    session = fastf1.get_session(year, round_no, "R")
    session.load(telemetry=False, weather=False, messages=False)
    return pd.DataFrame(session.laps)
