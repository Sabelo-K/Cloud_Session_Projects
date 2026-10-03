"""Driver head-to-head maths: two drivers compared weekend by weekend on qualifying, race result and race pace.
Pure pandas on the per-round frames from f1.summary and f1.pace, so it is unit-testable without Streamlit or the network."""
from __future__ import annotations

import numpy as np
import pandas as pd

from f1 import pace, summary

COLUMNS = ["Round", "QualiA", "QualiB", "QualiGap", "GridA", "GridB", "FinishA", "FinishB", "PaceA", "PaceB", "PaceGap", "PaceGapPct"]


def _pos(table: pd.DataFrame, drv: str, col: str = "Pos"):
    row = table[table["Driver"] == drv]
    return float(row[col].iloc[0]) if not row.empty else np.nan


def weekend_rows(quali: dict, race: dict, a: str, b: str) -> pd.DataFrame:
    """One row per round where either session exists. Gaps are B minus A, so a positive gap means A was quicker.
    Qualifying uses each driver's best lap, race pace the median clean lap; a driver who did not take part is NaN."""
    rows = []
    for rnd in sorted(set(quali) | set(race)):
        row = dict.fromkeys(COLUMNS, np.nan)
        row["Round"] = rnd
        if rnd in quali:
            q = summary.quali_order(quali[rnd])
            row.update(QualiA=_pos(q, a, "Best"), QualiB=_pos(q, b, "Best"), GridA=_pos(q, a), GridB=_pos(q, b))
            row["QualiGap"] = row["QualiB"] - row["QualiA"]
        if rnd in race:
            r = summary.race_classification(race[rnd])
            row.update(FinishA=_pos(r, a), FinishB=_pos(r, b))
            p = pace.race_pace(race[rnd]).set_index("Driver")["median"]
            row.update(PaceA=float(p.get(a, np.nan)), PaceB=float(p.get(b, np.nan)))
            row["PaceGap"] = row["PaceB"] - row["PaceA"]
            row["PaceGapPct"] = row["PaceGap"] / row["PaceA"] * 100
        rows.append(row)
    return pd.DataFrame(rows, columns=COLUMNS)


def scoreboard(rows: pd.DataFrame) -> dict:
    """Wins for A and B (ties go to neither) and the average gap, for each of qualifying, race finish and race pace.
    Gaps are B minus A: positive means A was quicker on average."""
    def count(col_a, col_b, lower_wins):
        both = rows.dropna(subset=[col_a, col_b])
        diff = both[col_b] - both[col_a] if lower_wins else both[col_a] - both[col_b]
        return {"a": int((diff > 0).sum()), "b": int((diff < 0).sum()), "rounds": int(len(both))}

    out = {"quali": count("QualiA", "QualiB", True), "finish": count("FinishA", "FinishB", True), "pace": count("PaceA", "PaceB", True)}
    out["quali"]["avg_gap"] = float(rows["QualiGap"].mean()) if rows["QualiGap"].notna().any() else float("nan")
    out["pace"]["avg_gap_pct"] = float(rows["PaceGapPct"].mean()) if rows["PaceGapPct"].notna().any() else float("nan")
    both = rows.dropna(subset=["FinishA", "FinishB"])
    out["finish"]["avg_places"] = float((both["FinishB"] - both["FinishA"]).mean()) if len(both) else float("nan")
    return out
