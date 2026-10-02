"""Save F1 sessions into the repo so the hosted app can read them.

Run on your own computer (FastF1's live-timing server refuses Streamlit Cloud):

    python -m f1.sync --year 2026 --last 3 --push
    python -m f1.sync --year 2026 --rounds 13,15 --sessions R Q --telemetry all
    python -m f1.sync --year 2026 --rounds 15 --sessions R --telemetry all --drivers NOR,PIA   # every lap, for chosen drivers only
    python -m f1.sync --year 2026 --missing --push      # everything finished and not saved yet (what f1/sync_missing.ps1 runs)

Telemetry: `fastest` (default) saves each driver's fastest lap, `all` saves every timed lap (bigger files), `none` skips it.
A whole race of `all` is about 20 MB, so use `--drivers` to limit it to the drivers you care about. Laps saved earlier are kept.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import date

import pandas as pd

from f1 import data, store

DEFAULT_SESSIONS = ["R", "Q"]
BIG_FILE_MB = 50  # GitHub refuses files over 100 MB


def parse_rounds(text: str, last_round: int | None = None) -> list[int]:
    """'13' -> [13], '10-13' -> [10, 11, 12, 13], '1,3,5' -> [1, 3, 5], 'all' -> 1..last_round."""
    text = text.strip().lower()
    if text == "all":
        if not last_round:
            raise ValueError("'all' needs a season with completed rounds")
        return list(range(1, last_round + 1))
    rounds: list[int] = []
    for part in text.split(","):
        part = part.strip()
        if "-" in part:
            lo, hi = part.split("-", 1)
            rounds += list(range(int(lo), int(hi) + 1))
        elif part:
            rounds.append(int(part))
    return sorted(set(rounds))


def completed_rounds(year: int, today: date | None = None, strict: bool = False) -> list[int]:
    """Rounds whose race date has arrived (strict: has passed, i.e. at least a day ago)."""
    sched = data.season_schedule(year)
    day = str(today or date.today())
    done = sched[sched["date"] < day] if strict else sched[sched["date"] <= day]
    return [int(r) for r in done["round"]]


def laps_to_save(laps: pd.DataFrame, mode: str, drivers: list[str] | None = None) -> list[tuple[str, int]]:
    """Which (driver, lap number) pairs get telemetry saved (only for `drivers` when given)."""
    if mode == "none":
        return []
    timed = laps.dropna(subset=["LapTime"])
    if drivers:
        timed = timed[timed["Driver"].isin(drivers)]
    if "Deleted" in timed.columns:
        timed = timed[~store.as_bool(timed["Deleted"])]
    if mode == "all":
        return [(str(d), int(n)) for d, n in zip(timed["Driver"], timed["LapNumber"])]
    best = timed.loc[timed.groupby("Driver")["LapTime"].idxmin()]
    return [(str(d), int(n)) for d, n in zip(best["Driver"], best["LapNumber"])]


def sync_session(year: int, round_no: int, kind: str, mode: str = "fastest", log=print, drivers: list[str] | None = None) -> bool:
    """Download one session with FastF1 and save it. False when the session has no data."""
    label = f"{year} round {round_no} {data.SESSION_NAMES.get(kind, kind)}"
    log(f"{label}: loading from FastF1 (this can take a few minutes)...")
    try:
        session = data._session(year, round_no, kind, mode != "none", True)
        laps = pd.DataFrame(session.laps)
    except Exception as exc:
        log(f"{label}: skipped ({type(exc).__name__}: {str(exc)[:120]})")
        return False
    if laps.empty:
        log(f"{label}: skipped (no lap data)")
        return False
    try:
        weather = pd.DataFrame(session.weather_data)
    except Exception:
        weather = pd.DataFrame()
    corners = data.corners_frame(session) if mode != "none" else pd.DataFrame()
    telemetry = {}
    picks = laps_to_save(laps, mode, drivers)
    for i, (drv, lap_no) in enumerate(picks, 1):
        try:
            tel = data.fetch_lap_telemetry(session, drv, lap_no)
        except Exception:
            continue
        if tel is not None and len(tel):
            telemetry[(drv, lap_no)] = tel
        if mode == "all" and i % 200 == 0:
            log(f"{label}: telemetry {i}/{len(picks)} laps")
    folder = store.write_session(year, round_no, kind, laps, weather, corners, telemetry, mode)
    size = sum(f.stat().st_size for f in folder.iterdir()) / 1e6
    log(f"{label}: saved {len(laps)} laps and {len(telemetry)} telemetry laps ({size:.1f} MB)")
    big = [f.name for f in folder.iterdir() if f.stat().st_size > BIG_FILE_MB * 1e6]
    if big:
        log(f"  warning: {', '.join(big)} is over {BIG_FILE_MB} MB; GitHub rejects files over 100 MB. Re-run with --telemetry fastest.")
    return True


def git_push(message: str, log=print, path: str = "f1/store") -> bool:
    """Commit the saved data (or another folder of the app) and push the current branch."""
    steps = [["git", "add", path], ["git", "commit", "-m", message], ["git", "push"]]
    for step in steps:
        done = subprocess.run(step, capture_output=True, text=True)
        if done.returncode != 0:
            out = (done.stdout + done.stderr).strip()
            if step[1] == "commit" and "nothing to commit" in out:
                log("Nothing new to commit.")
                return True
            log(f"`{' '.join(step)}` failed:\n{out}")
            return False
    log("Pushed. The hosted app updates in a minute or two.")
    return True


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--year", type=int, default=date.today().year)
    pick = ap.add_mutually_exclusive_group()
    pick.add_argument("--rounds", help="e.g. 13, 10-13, 1,3,5 or all")
    pick.add_argument("--last", type=int, help="the last N completed rounds of the season")
    pick.add_argument("--missing", action="store_true",
                      help="every finished round of the season whose sessions are not saved yet (what f1/sync_missing.ps1 runs)")
    ap.add_argument("--sessions", nargs="+", default=DEFAULT_SESSIONS, choices=list(data.SESSION_NAMES))
    ap.add_argument("--telemetry", choices=["fastest", "all", "none"], default="fastest")
    ap.add_argument("--drivers", help="only save telemetry for these drivers, e.g. NOR,PIA (all drivers when left out)")
    ap.add_argument("--push", action="store_true", help="commit and push the saved data with git afterwards")
    args = ap.parse_args(argv)

    if args.missing:
        pairs = [(r, k) for r in completed_rounds(args.year, strict=True) for k in args.sessions
                 if not store.has_session(args.year, r, k)]
        if not pairs:
            print("Everything is already saved.")
            return 0
    else:
        done = completed_rounds(args.year)
        if args.rounds:
            rounds = parse_rounds(args.rounds, done[-1] if done else None)
        elif args.last:
            rounds = done[-args.last:]
        else:
            ap.error("choose --rounds, --last or --missing")
        pairs = [(r, k) for r in rounds for k in args.sessions]
    if not pairs:
        print("No completed rounds to save.")
        return 1

    extra = {"drivers": [d.strip().upper() for d in args.drivers.split(",") if d.strip()]} if args.drivers else {}
    saved = 0
    for rnd, kind in pairs:
        saved += sync_session(args.year, rnd, kind, args.telemetry, **extra)
    print(f"Saved {saved} of {len(pairs)} session(s).")
    if saved and args.push:
        rounds = sorted({r for r, _ in pairs})
        return 0 if git_push(f"Save F1 data: {args.year} rounds {', '.join(map(str, rounds))}") else 1
    if saved:
        print("To publish: git add f1/store && git commit -m \"Save F1 data\" && git push (or re-run with --push).")
    return 0 if saved else 1


if __name__ == "__main__":
    sys.exit(main())
