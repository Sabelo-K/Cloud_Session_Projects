"""Lap replay maths: turn one lap's telemetry into a fixed-step timeline and describe what a timing screen would show
at any moment (clock, sector times as they are passed, speed, gear). Pure pandas/numpy, no Streamlit or Plotly."""
from __future__ import annotations

import numpy as np
import pandas as pd

from f1 import telemetry, tyres

STEP = 0.1                  # seconds between animation frames
PURPLE, WHITE, DIM = "#BF5AF2", "#F2F3F5", "#6B7683"
GREEN, RED = "#30D158", "#FF453A"   # reference driver ahead / behind


def timeline(tel: pd.DataFrame, step: float = STEP) -> pd.DataFrame:
    """One lap on a regular time grid (seconds from the start of the lap): T, Distance, X, Y, Speed, Throttle, nGear, Brake.
    The last row is the end of the lap."""
    df = telemetry.prepare_lap(tel)
    t = np.maximum.accumulate(df["TimeS"].to_numpy(float))
    end = float(t[-1])
    grid = np.append(np.arange(0.0, end, step), end)
    out = {"T": grid, "Distance": np.interp(grid, t, np.maximum.accumulate(df["Distance"].to_numpy(float)))}
    for col in ("X", "Y", "Speed", "Throttle"):
        out[col] = np.interp(grid, t, df[col].to_numpy(float)) if col in df else np.zeros(len(grid))
    idx = np.clip(np.searchsorted(t, grid, side="right") - 1, 0, len(t) - 1)
    for col in ("nGear", "Brake"):
        out[col] = df[col].to_numpy()[idx] if col in df else np.zeros(len(grid))
    return pd.DataFrame(out)


def splits_from_row(row) -> tuple[float, float, float] | None:
    """(S1, S2, S3) in seconds from a laps row, or None when any sector time is missing."""
    vals = []
    for col in ("Sector1Time", "Sector2Time", "Sector3Time"):
        v = row.get(col) if hasattr(row, "get") else None
        if v is None or pd.isna(v):
            return None
        vals.append(float(pd.Timedelta(v).total_seconds()))
    return tuple(vals)


def attach_deltas(runs: list[dict]) -> list[dict]:
    """Give every run after the first (the reference) a `delta` array, one value per animation frame: how many seconds
    later than the reference it reaches the point on track where the reference is at that moment. Positive means the
    reference is ahead, negative means it is behind. Once the reference has finished, the last value is held."""
    if len(runs) < 2:
        return runs
    ref = runs[0]["tl"]
    n = max(len(r["tl"]) for r in runs)
    j = np.minimum(np.arange(n), len(ref) - 1)
    ref_dist, ref_time = ref["Distance"].to_numpy()[j], ref["T"].to_numpy()[j]
    for r in runs[1:]:
        other = r["tl"]
        reach = np.interp(ref_dist, np.maximum.accumulate(other["Distance"].to_numpy()), other["T"].to_numpy())
        r["delta"] = reach - ref_time
    return runs


def delta_text(runs: list[dict], k: int, i: int) -> str:
    """Panel line for run k at frame i: how far the reference (runs[0]) is ahead (green) or behind (red) of it."""
    d = runs[k].get("delta")
    if d is None:
        return ""
    v = float(d[min(i, len(d) - 1)])
    ref = runs[0]["label"]
    if abs(v) < 0.0005:
        return f'<span style="color:{WHITE}">level with {ref}</span>'
    colour, word = (GREEN, "ahead") if v > 0 else (RED, "behind")
    return f'<span style="color:{colour}">{ref} {word} {abs(v):.3f}s</span>'


def fmt_time(seconds: float) -> str:
    m, s = divmod(float(seconds), 60)
    return f"{int(m)}:{s:06.3f}" if m else f"{s:.3f}"


def sector_colours(runs: list[dict]) -> list[list[str]]:
    """Per run and sector: purple for the quickest sector among the runs shown (only when there are two or more), else white."""
    out = [[WHITE] * 3 for _ in runs]
    if len(runs) < 2:
        return out
    for s in range(3):
        times = [r["splits"][s] if r.get("splits") else None for r in runs]
        known = [t for t in times if t is not None]
        if len(known) < 2:
            continue
        best = min(known)
        for i, t in enumerate(times):
            if t is not None and t == best:
                out[i][s] = PURPLE
    return out


def state_at(run: dict, t: float) -> dict:
    """What a driver's row on the timing screen shows at animation time `t` (seconds from the start of the lap)."""
    tl = run["tl"]
    end = float(tl["T"].iloc[-1])
    clock = min(t, end)
    i = int(np.clip(round(clock / STEP), 0, len(tl) - 1))
    splits = run.get("splits")
    shown: list[float | None] = [None, None, None]
    finished = t >= end
    if splits:
        passed = np.cumsum(splits)
        for s in range(3):
            if t >= passed[s] - 1e-9:
                shown[s] = splits[s]
    return {"frame": int(round(t / STEP)), "clock": clock, "finished": finished, "sectors": shown, "speed": float(tl["Speed"].iloc[i]),
            "gear": int(tl["nGear"].iloc[i]), "i": i, "x": float(tl["X"].iloc[i]), "y": float(tl["Y"].iloc[i]),
            "lap_time": run.get("lap_time") or end}


def panel_html(runs: list[dict], t: float) -> str:
    """The timing panel text (HTML for a Plotly annotation) at animation time `t`."""
    colours = sector_colours(runs)
    lines = []
    for run, cols in zip(runs, colours):
        st = state_at(run, t)
        head = f'<b style="color:{run["colour"]}">{run["label"]}</b>'
        if run.get("tyre"):
            head += f' <span style="color:{tyres.colour(run["tyre"])}">●</span> {tyres.name(run["tyre"])}'
        head += f'  {fmt_time(st["lap_time"]) if st["finished"] else fmt_time(st["clock"])}'
        secs = "   ".join(
            f'S{n + 1} <span style="color:{cols[n]}">{fmt_time(v) if v is not None else "–"}</span>' for n, v in enumerate(st["sectors"]))
        live = "finished" if st["finished"] else f'{st["speed"]:.0f} km/h · gear {st["gear"]}'
        extra = delta_text(runs, len(lines), st["frame"]) if len(lines) else ""
        lines.append(f"{head}<br>{secs}<br><span style=\"color:{DIM}\">{live}</span>" + (f"<br>{extra}" if extra else ""))
    return "<br>".join(lines)


def results_table(runs: list[dict]) -> pd.DataFrame:
    """Final times per run for a static table: Driver, Lap, Tyre, S1, S2, S3, Lap time, Gap (lap time minus the reference's,
    shown for every run after the first) and Top speed."""
    rows = []
    for r in runs:
        sp = r.get("splits")
        gap = r["lap_time"] - runs[0]["lap_time"]
        rows.append({"Driver": r["label"], "Lap": r.get("lap"), "Tyre": tyres.name(r["tyre"]) if r.get("tyre") else "",
                     "S1": fmt_time(sp[0]) if sp else "", "S2": fmt_time(sp[1]) if sp else "", "S3": fmt_time(sp[2]) if sp else "",
                     "Lap time": fmt_time(r["lap_time"]), "Gap": "" if r is runs[0] else f"{gap:+.3f}",
                     "Top speed": f'{r["tl"]["Speed"].max():.0f} km/h'})
    return pd.DataFrame(rows)
