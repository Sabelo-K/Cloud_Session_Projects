"""Saved session data: parquet files under f1/store/<year>/<round>_<session>/ that the app reads before it calls FastF1.

Why: FastF1's live-timing server refuses requests from Streamlit Cloud, so `python -m f1.sync` (run on a normal
internet connection) saves the data into the repo and the hosted app reads it from there. Pure pandas, no network."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent / "store"
TELEMETRY_COLUMNS = ["Distance", "Time", "Speed", "Throttle", "Brake", "nGear", "RPM", "DRS", "X", "Y"]
_BOOL_LIKE = {True, False}


class NotSaved(Exception):
    """The session has not been saved with `python -m f1.sync`."""


def session_dir(year: int, round_no: int, kind: str) -> Path:
    return ROOT / str(int(year)) / f"{int(round_no):02d}_{kind}"


def as_bool(series: pd.Series) -> pd.Series:
    """Booleans with missing values counted as False (avoids the pandas downcasting warning of fillna)."""
    return pd.Series([bool(v) if pd.notna(v) else False for v in series], index=series.index, dtype=bool)


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    """Make a frame parquet-safe: object columns become real booleans or strings."""
    df = df.copy()
    for col in df.columns[df.dtypes == object]:
        values = set(df[col].dropna().unique())
        if values <= _BOOL_LIKE:
            df[col] = as_bool(df[col])
        else:
            df[col] = df[col].astype("string")
    return df


def _slim_telemetry(df: pd.DataFrame) -> pd.DataFrame:
    keep = df[[c for c in TELEMETRY_COLUMNS if c in df.columns]].copy()
    for col in keep.columns:
        if keep[col].dtype == "float64":
            keep[col] = keep[col].astype("float32")
    return keep


def write_session(year: int, round_no: int, kind: str, laps: pd.DataFrame, weather: pd.DataFrame,
                  corners: pd.DataFrame, telemetry: dict[tuple[str, int], pd.DataFrame], mode: str) -> Path:
    """Save one session. `telemetry` maps (driver, lap number) to that lap's telemetry frame."""
    folder = session_dir(year, round_no, kind)
    folder.mkdir(parents=True, exist_ok=True)
    _clean(laps).to_parquet(folder / "laps.parquet", index=False, compression="zstd")
    for name, frame in (("weather", weather), ("corners", corners)):
        path = folder / f"{name}.parquet"
        if frame is not None and len(frame):
            _clean(frame).to_parquet(path, index=False, compression="zstd")
        elif path.exists():
            path.unlink()
    tel_path = folder / "telemetry.parquet"
    parts = [_slim_telemetry(frame).assign(Driver=drv, LapNumber=int(n)) for (drv, n), frame in telemetry.items()]
    if parts:
        new = pd.concat(parts, ignore_index=True)
        if tel_path.exists():  # keep laps saved earlier (e.g. every lap of one driver) that this run did not touch
            old = pd.read_parquet(tel_path)
            fresh = set(zip(new["Driver"], new["LapNumber"]))
            keep = old[[(d, n) not in fresh for d, n in zip(old["Driver"], old["LapNumber"])]]
            new = pd.concat([keep, new], ignore_index=True)
        new.to_parquet(tel_path, index=False, compression="zstd")
    elif tel_path.exists() and mode == "none":
        tel_path.unlink()
    saved_laps = len(stored_telemetry_laps(year, round_no, kind)) if tel_path.exists() else 0
    meta = {"saved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "telemetry": mode,
            "telemetry_laps": saved_laps}
    (folder / "meta.json").write_text(json.dumps(meta))
    return folder


def has_session(year: int, round_no: int, kind: str) -> bool:
    return (session_dir(year, round_no, kind) / "laps.parquet").exists()


def _read(year: int, round_no: int, kind: str, name: str, **kwargs):
    path = session_dir(year, round_no, kind) / f"{name}.parquet"
    return pd.read_parquet(path, **kwargs) if path.exists() else None


def read_laps(year: int, round_no: int, kind: str) -> pd.DataFrame | None:
    return _read(year, round_no, kind, "laps")


def read_weather(year: int, round_no: int, kind: str) -> pd.DataFrame | None:
    return _read(year, round_no, kind, "weather")


def read_corners(year: int, round_no: int, kind: str) -> pd.DataFrame | None:
    return _read(year, round_no, kind, "corners")


def stored_telemetry_laps(year: int, round_no: int, kind: str) -> set[tuple[str, int]]:
    """(driver, lap number) pairs whose telemetry was saved."""
    tel = _read(year, round_no, kind, "telemetry", columns=["Driver", "LapNumber"])
    if tel is None:
        return set()
    return {(str(d), int(n)) for d, n in tel.drop_duplicates().itertuples(index=False)}


def read_telemetry(year: int, round_no: int, kind: str, picks) -> dict[str, pd.DataFrame] | None:
    """{'VER|36': frame} for the saved picks, or None when this session has no saved telemetry.
    A pick with lap None means that driver's fastest saved lap."""
    drivers = sorted({d for d, _ in picks})
    tel = _read(year, round_no, kind, "telemetry", filters=[("Driver", "in", drivers)])
    if tel is None:
        return None
    laps = read_laps(year, round_no, kind)
    out = {}
    for drv, lap_no in picks:
        mine = tel[tel["Driver"] == drv]
        if lap_no is None:
            if laps is None or mine.empty:
                continue
            timed = laps[(laps["Driver"] == drv) & laps["LapNumber"].isin(mine["LapNumber"].unique())].dropna(subset=["LapTime"])
            if timed.empty:
                continue
            lap_no = int(timed.loc[timed["LapTime"].idxmin(), "LapNumber"])
        frame = mine[mine["LapNumber"] == int(lap_no)]
        if frame.empty:
            continue
        frame = frame.drop(columns=["Driver", "LapNumber"]).reset_index(drop=True)
        frame = frame.astype({c: "float64" for c in frame.columns if frame[c].dtype == "float32"})
        out[f"{drv}|{int(lap_no)}"] = frame
    return out


def saved_sessions() -> list[dict]:
    """Everything saved: [{'year', 'round', 'kind', 'telemetry', 'saved_at'}], oldest first."""
    found = []
    if not ROOT.exists():
        return found
    for folder in sorted(ROOT.glob("*/*_*")):
        if not (folder / "laps.parquet").exists():
            continue
        try:
            rnd, kind = folder.name.split("_", 1)
            meta = json.loads((folder / "meta.json").read_text()) if (folder / "meta.json").exists() else {}
            found.append({"year": int(folder.parent.name), "round": int(rnd), "kind": kind,
                          "telemetry": meta.get("telemetry", "none"), "saved_at": meta.get("saved_at", "")})
        except ValueError:
            continue
    return found


def saved_rounds(year: int) -> list[int]:
    return sorted({s["round"] for s in saved_sessions() if s["year"] == int(year)})
