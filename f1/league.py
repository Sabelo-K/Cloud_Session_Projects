"""Prediction League: players predict pole, the podium and the fastest lap before a race and score points against the result.
Picks live in one small JSON file per season (f1/league/<year>.json) so they travel with the repo.

    python -m f1.league --push        # commit and push picks entered on your own computer so the hosted app shows them
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

from f1 import summary

ROOT = Path(__file__).resolve().parent / "league"
POINTS = {"exact": 5, "on_podium": 2, "pole": 3, "fastest": 3}  # per correct podium place / wrong place / pole / fastest lap
MAX_POINTS = 3 * POINTS["exact"] + POINTS["pole"] + POINTS["fastest"]


def path_for(year: int) -> Path:
    return ROOT / f"{int(year)}.json"


def load(year: int) -> dict:
    """{'players': [...], 'rounds': {'13': {'Sabelo': {'pole': 'NOR', 'podium': [...], 'fastest': 'PIA'}}}} (empty when none yet)."""
    path = path_for(year)
    if not path.exists():
        return {"players": [], "rounds": {}}
    try:
        data = json.loads(path.read_text())
    except ValueError:
        return {"players": [], "rounds": {}}
    data.setdefault("players", [])
    data.setdefault("rounds", {})
    return data


def save(year: int, league: dict) -> Path:
    path = path_for(year)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(league, indent=2, sort_keys=True) + "\n")
    return path


def add_prediction(league: dict, rnd: int, player: str, pole: str, podium: list[str], fastest: str) -> dict:
    """Return a new league with this player's picks for the round (replacing earlier ones). Raises ValueError on bad picks."""
    player = player.strip()
    if not player:
        raise ValueError("Enter a player name.")
    if len(podium) != 3 or len(set(podium)) != 3 or not all(podium):
        raise ValueError("Pick three different drivers for the podium.")
    if not pole or not fastest:
        raise ValueError("Pick a pole sitter and a fastest-lap driver.")
    out = json.loads(json.dumps(league))
    if player not in out["players"]:
        out["players"].append(player)
    out["rounds"].setdefault(str(int(rnd)), {})[player] = {"pole": pole, "podium": list(podium), "fastest": fastest}
    return out


def result_from_laps(quali_laps: pd.DataFrame | None, race_laps: pd.DataFrame | None) -> dict | None:
    """The real outcome for scoring: {'pole', 'podium', 'fastest'}, or None until the race has been saved."""
    if race_laps is None or race_laps.empty:
        return None
    race = summary.race_classification(race_laps)
    if len(race) < 3:
        return None
    fast = summary.fastest_lap(race)
    pole = None
    if quali_laps is not None and not quali_laps.empty:
        order = summary.quali_order(quali_laps)
        pole = str(order["Driver"].iloc[0]) if not order.empty else None
    return {"pole": pole, "podium": [str(d) for d in race["Driver"].head(3)], "fastest": fast[0] if fast else None}


def score(pred: dict, result: dict) -> dict:
    """Points for one prediction against a result, with the parts: podium, pole, fastest, total."""
    podium = 0
    for i, driver in enumerate(pred["podium"]):
        if i < len(result["podium"]) and driver == result["podium"][i]:
            podium += POINTS["exact"]
        elif driver in result["podium"]:
            podium += POINTS["on_podium"]
    pole = POINTS["pole"] if result.get("pole") and pred["pole"] == result["pole"] else 0
    fastest = POINTS["fastest"] if result.get("fastest") and pred["fastest"] == result["fastest"] else 0
    return {"podium": podium, "pole": pole, "fastest": fastest, "total": podium + pole + fastest}


def leaderboard(league: dict, results: dict[int, dict]) -> pd.DataFrame:
    """One row per player: Points, Rounds played and points per scored round (columns 'R13' ...). Best first."""
    rows = []
    for player in league["players"]:
        row, total, played = {"Player": player}, 0, 0
        for rnd in sorted(int(r) for r in league["rounds"]):
            pred = league["rounds"][str(rnd)].get(player)
            if pred is None or rnd not in results:
                continue
            pts = score(pred, results[rnd])["total"]
            row[f"R{rnd}"] = pts
            total, played = total + pts, played + 1
        row.update(Points=total, Rounds=played)
        rows.append(row)
    cols = ["Player", "Points", "Rounds"]
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=cols)
    rounds = sorted((c for c in df.columns if c.startswith("R") and c[1:].isdigit()), key=lambda c: int(c[1:]))
    df = df[cols + rounds].astype({c: "Int64" for c in rounds})  # whole points, blank where a player skipped a round
    return df.sort_values(["Points", "Rounds"], ascending=[False, True]).reset_index(drop=True)


def main(argv: list[str] | None = None) -> int:
    from f1 import sync

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--push", action="store_true", required=True, help="commit and push the league files with git")
    ap.parse_args(argv)
    return 0 if sync.git_push("Update F1 prediction league", path="f1/league") else 1


if __name__ == "__main__":
    sys.exit(main())
