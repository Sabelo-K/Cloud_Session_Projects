"""Plotly figure builders shared by the pages. They take plain DataFrames, so they can be tested without Streamlit."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from f1 import style, tyres

GROUP_DASHES = ["solid", "dash", "dot", "dashdot"]


def driver_of(label: str) -> str:
    return label.split("|")[0]


def pretty(label: str) -> str:
    """'VER|36' -> 'VER · lap 36' (labels are kept as 'DRIVER|LAP' internally)."""
    drv, _, lap = label.partition("|")
    return f"{drv} · lap {lap}" if lap else drv


def track_outline(x, y) -> go.Scatter:
    return go.Scatter(x=x, y=y, mode="lines", line=dict(color="#29313A", width=9), hoverinfo="skip", showlegend=False)


def finish_map(fig: go.Figure, height: int = 460) -> go.Figure:
    fig.update_xaxes(visible=False, scaleanchor="y")
    fig.update_yaxes(visible=False)
    fig.update_layout(height=height, margin=dict(l=0, r=0, t=10, b=0))
    return fig


def _corner_labels(fig: go.Figure, corners: pd.DataFrame | None) -> None:
    if corners is None or corners.empty or "X" not in corners:
        return
    fig.add_trace(go.Scatter(x=corners["X"], y=corners["Y"], mode="text", text=[f"T{int(n)}" for n in corners["Number"]],
                             textfont=dict(size=10, color="#98A4B3"), hoverinfo="skip", showlegend=False))


def dominance_map(dom: pd.DataFrame, colours: dict, corners: pd.DataFrame | None = None) -> go.Figure:
    """Circuit drawn in short segments, each coloured by the lap that was quickest through it."""
    fig = go.Figure()
    fig.add_trace(track_outline(np.append(dom["X0"].to_numpy(), dom["X1"].iloc[-1]),
                                np.append(dom["Y0"].to_numpy(), dom["Y1"].iloc[-1])))
    for label in dom["Winner"].unique():
        seg = dom[dom["Winner"] == label]
        xs, ys, hov = [], [], []
        for r in seg.itertuples():
            xs += [r.X0, r.X1, None]
            ys += [r.Y0, r.Y1, None]
            hov += [f"{pretty(label)}: +{r.Gain:.3f}s on this segment"] * 2 + [None]
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", name=f"{pretty(label)} ({len(seg)})", text=hov, hoverinfo="text",
                                 line=dict(color=colours.get(driver_of(label), "#00D5CF"), width=5)))
    _corner_labels(fig, corners)
    return finish_map(fig)


def sector_map(tel: pd.DataFrame, sector: pd.Series, palette: dict | None = None) -> go.Figure:
    """Circuit coloured by timing sector."""
    palette = palette or {1: "#E8002D", 2: "#FFD60A", 3: "#00D5CF"}
    fig = go.Figure(track_outline(tel["X"], tel["Y"]))
    for n in (1, 2, 3):
        part = tel[sector == n]
        fig.add_trace(go.Scatter(x=part["X"], y=part["Y"], mode="lines", name=f"Sector {n}",
                                 line=dict(color=palette[n], width=5), hoverinfo="skip"))
    return finish_map(fig)


def speed_with_corners(res: dict, colours: dict, dashes: dict, corners: pd.DataFrame | None, ref: str | None = None):
    """Speed traces and, underneath, time delta against `ref` (positive = slower than ref), sharing the distance axis."""
    from f1 import telemetry

    ref = ref or next(iter(res))
    delta = telemetry.delta_vs_reference(res, ref)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.65, 0.35], vertical_spacing=0.08,
                        subplot_titles=("Speed (km/h)", f"Time delta vs {pretty(ref)} (s): above zero = slower"))
    for label, df in res.items():
        line = dict(color=colours.get(driver_of(label)), dash=dashes.get(label, "solid"))
        fig.add_trace(go.Scatter(x=df["Distance"], y=df["Speed"], name=pretty(label), line=line, legendgroup=label), row=1, col=1)
        fig.add_trace(go.Scatter(x=df["Distance"], y=delta[label], name=pretty(label), line=line, legendgroup=label,
                                 showlegend=False), row=2, col=1)
    fig.add_hline(y=0, line=dict(color="#98A4B3", width=1, dash="dot"), row=2, col=1)
    add_corner_markers(fig, corners, res)
    fig.update_xaxes(title_text="Distance (m)", row=2, col=1)
    return fig


def add_corner_markers(fig: go.Figure, corners: pd.DataFrame | None, res: dict) -> None:
    if corners is None or corners.empty:
        return
    lap_len = max(df["Distance"].max() for df in res.values())
    dist = corners["Distance"].astype(float)
    if dist.max() > lap_len * 1.5:
        dist = dist / 10.0
    for n, d in zip(corners["Number"], dist):
        fig.add_vline(x=d, line=dict(color="#29313A", width=1), row="all", col=1)
        fig.add_annotation(x=d, xref="x", y=1.0, yref="paper", text=f"T{int(n)}", showarrow=False,
                           font=dict(size=9, color="#98A4B3"), yshift=34)


CHANNELS = [("Speed", "Speed (km/h)", None), ("Throttle", "Throttle (%)", None),
            ("Brake", "Brake (off/on)", "hv"), ("nGear", "Gear", "hv"), ("RPM", "Engine RPM", None)]


def telemetry_stack(res: dict, colours: dict, dashes: dict, corners: pd.DataFrame | None = None) -> go.Figure:
    """Five linked charts (speed, throttle, brake, gear, RPM) against distance. Brake and gear are drawn as steps."""
    fig = make_subplots(rows=len(CHANNELS), cols=1, shared_xaxes=True, vertical_spacing=0.035,
                        row_heights=[0.28, 0.17, 0.13, 0.17, 0.25], subplot_titles=[c[1] for c in CHANNELS])
    for i, (col, _, shape) in enumerate(CHANNELS, start=1):
        for label, df in res.items():
            if col not in df:
                continue
            line = dict(color=colours.get(driver_of(label)), dash=dashes.get(label, "solid"), width=2)
            if shape:
                line["shape"] = shape
            fig.add_trace(go.Scatter(x=df["Distance"], y=df[col], name=pretty(label), line=line, legendgroup=label,
                                     showlegend=(i == 1)), row=i, col=1)
    fig.update_yaxes(fixedrange=True)  # dragging zooms along the lap only, and all five charts zoom together
    fig.update_yaxes(tickvals=[0, 1], ticktext=["Off", "On"], row=3, col=1)
    fig.update_xaxes(title_text="Distance (m)", row=len(CHANNELS), col=1)
    fig.update_xaxes(showspikes=True, spikemode="across", spikethickness=1, spikecolor="#98A4B3")
    fig.update_layout(hovermode="x unified", margin=dict(t=75))
    add_corner_markers(fig, corners, res)
    return fig


def stint_timeline(laps: pd.DataFrame, order: list[str]) -> go.Figure:
    """One row per driver, one block per stint, coloured by compound and labelled with its initial.
    Hover shows the compound, laps, tyre age at the start and whether the set was new. Unknown tyres are hatched grey."""
    fig = go.Figure()
    shown = set()
    for (drv, stint), g in laps.dropna(subset=["Stint"]).groupby(["Driver", "Stint"]):
        comp = tyres.stint_compound(g["Compound"]) if "Compound" in g else tyres.UNKNOWN
        start, end = int(g["LapNumber"].min()), int(g["LapNumber"].max())
        age = g["TyreLife"].iloc[0] if "TyreLife" in g else float("nan")
        age_text = f"{age:g}" if pd.notna(age) else "not reported"
        fresh = g["FreshTyre"].dropna() if "FreshTyre" in g else []
        set_text = "" if not len(fresh) else ("<br>new set" if bool(fresh.iloc[0]) else "<br>used set")
        fig.add_trace(go.Bar(
            y=[drv], x=[end - start + 1], base=[start - 1], orientation="h", name=tyres.name(comp), legendgroup=comp,
            legendrank=tyres.rank(comp), showlegend=comp not in shown,
            marker=dict(color=tyres.colour(comp), line=dict(color="#090B0E", width=2),
                        pattern=dict(shape="/", fgcolor="#2B323B", size=6) if comp == tyres.UNKNOWN else dict()),
            text=[f"<b>{tyres.letter(comp)}</b>"], textposition="inside", insidetextanchor="middle",
            textangle=0, textfont=dict(color=tyres.text_colour(comp), size=13),
            hovertemplate=(f"{drv} · stint {int(stint)}<br>{tyres.name(comp)}<br>laps {start}-{end}"
                           f"<br>tyre age at start: {age_text}{set_text}<extra></extra>")))
        shown.add(comp)
    fig.update_layout(barmode="overlay", bargap=0.12, yaxis=dict(categoryorder="array", categoryarray=order[::-1]),
                      xaxis_title="Lap")
    return fig
