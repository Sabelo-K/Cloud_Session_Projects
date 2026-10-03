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


TRACE_BG = "#0A0B0E"
TRACE_GRID = "#262A31"
TRACE_TEXT = "#C9D1D9"


def telemetry_stack(res: dict, colours: dict, dashes: dict, corners: pd.DataFrame | None = None) -> go.Figure:
    """Five linked charts (speed, throttle, brake, gear, RPM) against distance, styled like a pro speed trace:
    near-black canvas, dashed grid, a dashed hover line with one tooltip listing every lap, and a Reset Zoom button."""
    fig = make_subplots(rows=len(CHANNELS), cols=1, shared_xaxes=True, vertical_spacing=0.045,
                        row_heights=[0.34, 0.15, 0.11, 0.15, 0.25], subplot_titles=[c[1] for c in CHANNELS])
    for i, (col, _, shape) in enumerate(CHANNELS, start=1):
        unit = {"Speed": " km/h", "Throttle": "%", "Brake": "", "nGear": "", "RPM": " rpm"}[col]
        for label, df in res.items():
            if col not in df:
                continue
            line = dict(color=colours.get(driver_of(label)), dash=dashes.get(label, "solid"), width=1.8)
            if shape:
                line["shape"] = shape
            y = df[col]
            if col == "Brake":
                text = pd.Series(np.where(y > 0, "On", "Off"), index=df.index)
                hover = "%{fullData.name}: %{text}<extra></extra>"
            else:
                text = None
                hover = "%{fullData.name}: %{y:.0f}" + unit + "<extra></extra>"
            fig.add_trace(go.Scatter(x=df["Distance"], y=y, text=text, name=pretty(label), line=line, legendgroup=label,
                                     showlegend=(i == 1), hovertemplate=hover), row=i, col=1)
    n = len(CHANNELS)
    drivers = [driver_of(l) for l in res]
    if len(set(drivers)) == len(drivers):  # one lap per driver: tooltip reads "LEC: 310 km/h" like a broadcast graphic
        for tr in fig.data:
            tr.name = driver_of(tr.legendgroup)
    axis = dict(gridcolor=TRACE_GRID, griddash="dot", zeroline=False, linecolor=TRACE_GRID, tickfont=dict(color=TRACE_TEXT, size=11))
    fig.update_yaxes(fixedrange=True, **axis)  # dragging zooms along the lap only, and all five charts zoom together
    fig.update_yaxes(tickvals=[0, 1], ticktext=["Off", "On"], range=[-0.1, 1.15], row=3, col=1)
    fig.update_xaxes(ticksuffix="m", hoverformat=".0f", showspikes=True, spikemode="across", spikesnap="cursor",
                     spikethickness=1, spikedash="dot", spikecolor="#B8C0CC", **axis)
    fig.update_xaxes(title_text="Distance", title_font=dict(color=TRACE_TEXT), row=n, col=1)
    for ann in fig.layout.annotations:  # subplot titles
        ann.update(font=dict(size=13, color="#FFFFFF"), x=0, xanchor="left")
    fig.update_layout(
        hovermode="x unified", margin=dict(t=75), paper_bgcolor=TRACE_BG, plot_bgcolor=TRACE_BG,
        font=dict(color=TRACE_TEXT), legend=dict(orientation="h", yanchor="top", y=-0.08, x=0, title_text="", font=dict(color=TRACE_TEXT)),
        hoverlabel=dict(bgcolor="#14171C", bordercolor="#2B3038", font=dict(color="#FFFFFF", size=13)),
        updatemenus=[dict(type="buttons", direction="right", x=1, xanchor="right", y=1.0, yanchor="bottom", pad=dict(t=0, r=0),
                          bgcolor="#14171C", bordercolor="#2B3038", font=dict(color=TRACE_TEXT, size=12), showactive=False,
                          buttons=[dict(label="Reset Zoom", method="relayout",
                                        args=[{f"xaxis{'' if k == 1 else k}.autorange": True for k in range(1, n + 1)}])])],
    )
    add_corner_markers(fig, corners, res)
    return fig


def _lap_text(seconds: float) -> str:
    m, sec = divmod(float(seconds), 60)
    return f"{int(m)}:{sec:06.3f}"


def long_run_violin(runs: pd.DataFrame, colours: dict, title: str = "Long Run Pace Violin Plot") -> go.Figure:
    """One violin per driver (all their long-run laps), filled in the team colour, with a dot per lap in its tyre colour
    and the average and gap to the quickest driver printed under it. `runs` needs Driver, Adjusted (s) and Compound."""
    stats = runs.groupby("Driver")["Adjusted"].agg(["mean", "count"]).sort_values("mean")
    best = stats["mean"].min()
    pos = {d: i for i, d in enumerate(stats.index)}
    rng = np.random.default_rng(1)  # fixed seed: the dots do not shuffle on every rerun
    fig = go.Figure()
    for drv, row in stats.iterrows():
        g = runs[runs["Driver"] == drv]
        col = colours.get(drv, "#98A4B3")
        fig.add_trace(go.Violin(
            x=[pos[drv]] * len(g), y=g["Adjusted"], name=drv, points=False, spanmode="hard", line=dict(color=col, width=1),
            fillcolor=col, opacity=0.85, width=0.8, meanline_visible=True, meanline=dict(color="rgba(255,255,255,0.7)", width=1),
            showlegend=False, hoverinfo="skip"))
        fig.add_annotation(x=pos[drv], y=g["Adjusted"].min(), yshift=-26 - 30 * (pos[drv] % 2), showarrow=False, align="center",  # staggered so neighbours do not collide
                           text=f"<b>Avg: {_lap_text(row['mean'])}</b><br>{row['mean'] - best:+.3f}s",
                           font=dict(size=11, color="#E6EBF1"))
    comp = runs["Compound"].map(tyres.normalise)
    for c in [c for c in tyres.ORDER if (comp == c).any()]:  # one dot series per tyre, so the legend doubles as a filter
        g = runs[comp == c]
        fig.add_trace(go.Scatter(
            x=[pos[d] + j for d, j in zip(g["Driver"], rng.uniform(-0.12, 0.12, len(g)))], y=g["Adjusted"], mode="markers",
            name=tyres.name(c).upper(), marker=dict(color=tyres.colour(c), size=6, line=dict(color="#111418", width=1)),
            text=[f"{d} lap {int(n)}<br>{tyres.name(c)}" for d, n in zip(g["Driver"], g["LapNumber"])],
            hovertemplate="%{text}<br>Lap Time: %{y:.3f}s<extra></extra>"))
    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", x=0.5, xanchor="center", font=dict(size=17, color="#FFFFFF")), violingap=0.12, violinmode="overlay",
        paper_bgcolor=TRACE_BG, plot_bgcolor=TRACE_BG, font=dict(color=TRACE_TEXT), margin=dict(t=70, b=30),
        legend=dict(orientation="v", x=1, xanchor="right", y=1, title_text="Tire Compound"),
        yaxis=dict(title="Lap Time (seconds)", gridcolor=TRACE_GRID, zeroline=False), xaxis=dict(showgrid=False, tickmode="array", tickvals=list(pos.values()), ticktext=list(pos), range=[-0.6, len(pos) - 0.4]),
        hoverlabel=dict(bgcolor="#FFD60A", font=dict(color="#000000")))
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


def lap_replay(runs: list[dict], speed: float = 1.0, tail: int = 25, corners: pd.DataFrame | None = None) -> go.Figure:
    """Animated track map: one dot per run driving its lap, a short tail behind it and a timing panel that fills in each
    sector time as the dot passes the sector line. Play / pause buttons and a time slider are part of the figure,
    so playback runs in the browser. `runs` are dicts from the replay page: label, colour, tl (replay.timeline), splits,
    lap_time, tyre. `speed` is the playback speed (1 = real time). `corners` (Number, X, Y) adds numbered corner signs."""
    from f1 import replay

    ref = runs[0]
    fig = go.Figure()
    fig.add_trace(track_outline(ref["tl"]["X"], ref["tl"]["Y"]))
    marks = [("S/F", 0.0)]
    if ref.get("splits"):
        s1, s2, _ = ref["splits"]
        marks += [("S2", s1), ("S3", s1 + s2)]
    mx, my, mt = [], [], []
    for text, at in marks:
        i = int(np.clip(round(at / replay.STEP), 0, len(ref["tl"]) - 1))
        mx.append(float(ref["tl"]["X"].iloc[i]))
        my.append(float(ref["tl"]["Y"].iloc[i]))
        mt.append(text)
    fig.add_trace(go.Scatter(x=mx, y=my, mode="markers+text", text=mt, textposition="top center", hoverinfo="skip", showlegend=False,
                             marker=dict(symbol="line-ns", size=16, color="#F2F3F5", line=dict(width=2, color="#F2F3F5")),
                             textfont=dict(size=11, color="#98A4B3")))
    if corners is not None and not corners.empty and "X" in corners:
        fig.add_trace(go.Scatter(x=corners["X"], y=corners["Y"], mode="markers+text", text=[str(int(n)) for n in corners["Number"]],
                                 textposition="middle center", hoverinfo="skip", showlegend=False, textfont=dict(size=9, color="#F2F3F5"),
                                 marker=dict(size=17, color="#14181E", line=dict(
                                     width=1, color="#E3B341" if "Estimated" in corners and corners["Estimated"].any() else "#6B7683"))))
    first_dynamic = len(fig.data)
    label_at = ["top center", "bottom center", "middle right"]  # different sides, so close cars keep readable names
    for k, r in enumerate(runs):
        tl = r["tl"]
        fig.add_trace(go.Scatter(x=tl["X"].iloc[:1], y=tl["Y"].iloc[:1], mode="lines", line=dict(color=r["colour"], width=5),
                                 hoverinfo="skip", showlegend=False))
        fig.add_trace(go.Scatter(x=tl["X"].iloc[:1], y=tl["Y"].iloc[:1], mode="markers+text", text=[r["label"]], textposition=label_at[k % 3],
                                 textfont=dict(size=12, color="#F2F3F5"), hoverinfo="skip", name=r["label"],
                                 marker=dict(size=15, color=r["colour"], line=dict(color="#F2F3F5", width=2))))
    gaps = [k for k, r in enumerate(runs) if k and r.get("delta") is not None]  # lines from the reference to each other car
    for k in gaps:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines", line=dict(color=replay.WHITE, width=3, dash="dot"),
                                 hoverinfo="skip", showlegend=False))
    n = max(len(r["tl"]) for r in runs)
    traces = list(range(first_dynamic, first_dynamic + 2 * len(runs) + len(gaps)))
    frames = []
    for i in range(n):
        data = []
        for r in runs:
            tl = r["tl"]
            j = min(i, len(tl) - 1)
            lo = max(0, j - tail)
            data.append(go.Scatter(x=np.round(tl["X"].iloc[lo:j + 1].to_numpy(), 0), y=np.round(tl["Y"].iloc[lo:j + 1].to_numpy(), 0)))
            data.append(go.Scatter(x=[round(float(tl["X"].iloc[j]))], y=[round(float(tl["Y"].iloc[j]))]))
        ref_tl = runs[0]["tl"]
        rj = min(i, len(ref_tl) - 1)
        for k in gaps:
            tl = runs[k]["tl"]
            j = min(i, len(tl) - 1)
            ahead = runs[k]["delta"][min(i, len(runs[k]["delta"]) - 1)] >= 0  # reference ahead: green, behind: red
            data.append(go.Scatter(x=[round(float(ref_tl["X"].iloc[rj])), round(float(tl["X"].iloc[j]))],
                                   y=[round(float(ref_tl["Y"].iloc[rj])), round(float(tl["Y"].iloc[j]))],
                                   line=dict(color=replay.GREEN if ahead else replay.RED, width=3, dash="dot")))
        frames.append(go.Frame(data=data, traces=traces, name=str(i),
                               layout=dict(annotations=[_panel(replay.panel_html(runs, i * replay.STEP))])))
    fig.frames = frames
    duration = max(16, int(replay.STEP * 1000 / speed))
    play = dict(frame=dict(duration=duration, redraw=True), transition=dict(duration=0), fromcurrent=True, mode="immediate")
    ticks = sorted({int(v) for v in np.linspace(0, n - 1, 21)})
    fig.update_layout(
        annotations=[_panel(replay.panel_html(runs, 0.0))],
        updatemenus=[dict(type="buttons", direction="left", bgcolor="#C9D1DA", bordercolor="#29313A", font=dict(color="#090B0E"), active=-1, x=0, y=-0.02, xanchor="left", yanchor="top", pad=dict(t=4, r=8),
                          buttons=[dict(label="▶ Play", method="animate", args=[None, play]),
                                   dict(label="⏸ Pause", method="animate",
                                        args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate", transition=dict(duration=0))]),
                                   dict(label="↺ Reset", method="animate",
                                        args=[["0"], dict(frame=dict(duration=0, redraw=True), mode="immediate", transition=dict(duration=0))])])],
        sliders=[dict(active=0, bgcolor="#29313A", bordercolor="#29313A", font=dict(color="#98A4B3", size=10),
                      tickcolor="#29313A", x=0.0, y=-0.11, len=1.0, xanchor="left", yanchor="top", pad=dict(t=0, b=0),
                      currentvalue=dict(prefix="Lap time ", font=dict(size=12, color="#98A4B3")),
                      steps=[dict(method="animate", label=replay.fmt_time(i * replay.STEP),
                                  args=[[str(i)], dict(mode="immediate", frame=dict(duration=0, redraw=True), transition=dict(duration=0))])
                             for i in ticks])],
    )
    fig.update_layout(showlegend=False)  # the dots carry their own names
    return finish_map(fig, 520)


def _panel(html: str) -> dict:
    return dict(xref="paper", yref="paper", x=0.0, y=1.0, xanchor="left", yanchor="top", align="left", showarrow=False, text=html,
                font=dict(size=13, color="#F2F3F5"), bgcolor="rgba(20,24,30,0.88)", bordercolor="#29313A", borderwidth=1, borderpad=8)
