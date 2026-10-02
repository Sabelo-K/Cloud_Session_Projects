"""Data access: FastF1 for laps/telemetry/weather, Jolpica (Ergast successor) for schedule and standings.
The app calls only these functions, so tests and demos can swap them out."""
from __future__ import annotations

import time
from functools import lru_cache
from pathlib import Path

import pandas as pd
import requests

from f1.standings import parse_standings

JOLPICA = "https://api.jolpi.ca/ergast/f1"
CACHE_DIR = Path(".fastf1-cache")

SESSION_NAMES = {"FP1": "Practice 1", "FP2": "Practice 2", "FP3": "Practice 3",
                 "SQ": "Sprint qualifying", "S": "Sprint", "Q": "Qualifying", "R": "Race"}


def season_schedule(year: int) -> pd.DataFrame:
    r = requests.get(f"{JOLPICA}/{year}.json", timeout=20)
    r.raise_for_status()
    races = r.json()["MRData"]["RaceTable"]["Races"]
    return pd.DataFrame(
        [{"round": int(x["round"]), "name": x["raceName"], "date": x["date"]} for x in races]
    )


def season_standings(year: int, rounds: list[int]) -> list[pd.DataFrame]:
    """Driver standings after each round (one Jolpica call per round; the free tier is rate limited)."""
    frames = []
    for rnd in rounds:
        r = requests.get(f"{JOLPICA}/{year}/{rnd}/driverStandings.json", timeout=20)
        r.raise_for_status()
        frames.append(parse_standings(r.json(), rnd))
        time.sleep(0.3)
    return frames


@lru_cache(maxsize=3)
def _session(year: int, round_no: int, kind: str, telemetry: bool, weather: bool):
    import fastf1  # imported lazily: heavy, and not needed for the maths or tests

    CACHE_DIR.mkdir(exist_ok=True)
    fastf1.Cache.enable_cache(str(CACHE_DIR))
    session = fastf1.get_session(year, round_no, kind)
    session.load(laps=True, telemetry=telemetry, weather=weather, messages=False)
    return session


def load_session_laps(year: int, round_no: int, kind: str = "R") -> pd.DataFrame:
    return pd.DataFrame(_session(year, round_no, kind, False, False).laps)


def load_lap_telemetry(year: int, round_no: int, kind: str, picks: tuple) -> dict:
    """Telemetry for each (driver, lap) pick; lap None means that driver's fastest lap. Returns
    {'VER|36': frame} where the frame has Distance, Time, Speed, Throttle, Brake, nGear, RPM, DRS, X, Y.
    Picks without usable telemetry are left out."""
    session = _session(year, round_no, kind, True, False)
    out = {}
    for drv, lap_no in picks:
        try:
            laps = session.laps.pick_drivers(drv)
            lap = laps.pick_fastest() if lap_no is None else laps.pick_laps(int(lap_no)).iloc[0]
            if lap is None:
                continue
            tel = lap.get_telemetry()
            number = int(lap["LapNumber"])
            out[f"{drv}|{number}"] = pd.DataFrame(tel)
        except Exception:  # lap without telemetry, deleted lap, etc.
            continue
    return out


def load_corners(year: int, round_no: int, kind: str) -> pd.DataFrame:
    """Corner numbers with their distance along the lap and position (empty if unavailable)."""
    try:
        info = _session(year, round_no, kind, True, False).get_circuit_info()
        return pd.DataFrame(info.corners)[["Number", "Distance", "X", "Y"]]
    except Exception:
        return pd.DataFrame(columns=["Number", "Distance", "X", "Y"])


def load_weather(year: int, round_no: int, kind: str) -> pd.DataFrame:
    """Weather samples (Time, AirTemp, TrackTemp, Humidity, WindSpeed, Rainfall); empty if unavailable."""
    try:
        return pd.DataFrame(_session(year, round_no, kind, False, True).weather_data)
    except Exception:
        return pd.DataFrame()
