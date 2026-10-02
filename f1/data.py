"""Data access: FastF1 for laps, Jolpica (Ergast successor) for schedule/results."""
from __future__ import annotations

from pathlib import Path

import time

import pandas as pd
import requests

from f1.standings import parse_standings

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


def season_standings(year: int, rounds: list[int]) -> list[pd.DataFrame]:
    """Driver standings after each round (one Jolpica call per round; free tier is rate limited)."""
    frames = []
    for rnd in rounds:
        r = requests.get(f"{JOLPICA}/{year}/{rnd}/driverStandings.json", timeout=20)
        r.raise_for_status()
        frames.append(parse_standings(r.json(), rnd))
        time.sleep(0.3)
    return frames


def _session(year: int, round_no: int, kind: str, telemetry: bool):
    import fastf1

    CACHE_DIR.mkdir(exist_ok=True)
    fastf1.Cache.enable_cache(str(CACHE_DIR))
    session = fastf1.get_session(year, round_no, kind)
    session.load(telemetry=telemetry, weather=False, messages=False)
    return session


def load_session_laps(year: int, round_no: int, kind: str = "Q") -> pd.DataFrame:
    return pd.DataFrame(_session(year, round_no, kind, telemetry=False).laps)


def load_fastest_lap_telemetry(year: int, round_no: int, kind: str, drivers: list[str]) -> dict:
    """Telemetry (with Distance) for each driver's fastest lap in the session."""
    session = _session(year, round_no, kind, telemetry=True)
    out = {}
    for drv in drivers:
        lap = session.laps.pick_drivers(drv).pick_fastest()
        if lap is not None:
            out[drv] = lap.get_car_data().add_distance()
    return out
