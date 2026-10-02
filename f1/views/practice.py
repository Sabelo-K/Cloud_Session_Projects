"""Practice Insights: long-run pace, tyre degradation, consistency and straight-line speed."""
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from f1 import data, pace, style, ui


def _hex_rgba(hex_colour: str, alpha: float) -> str:
    h = hex_colour.lstrip("#")
    return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{alpha})"


def render():
    ui.title("Practice Insights", "Long runs, tyre degradation and consistency. Practice pace is an estimate: fuel, traffic and run plans vary.")
    year, rnd, event, kind = ui.session_controls("practice", ["FP1", "FP2", "FP3", "SQ", "Q"], "FP2")
    laps = ui.load_laps(year, rnd, kind)
    colours, _ = style.driver_styles(laps)
    drivers = ui.driver_picker("practice", sorted(laps["Driver"].unique()), colours, default_n=6)
    if not drivers:
        st.info("Pick at least one driver above.")
        return

    c1, c2 = st.columns(2)
    min_laps = c1.slider("Minimum clean laps for a long run", 3, 12, 5)
    fuel = c2.toggle("Adjust for fuel burn (0.03 s per lap)", value=False)
    runs = pace.long_runs(laps[laps["Driver"].isin(drivers)], min_laps)
    if runs.empty:
        st.info("No long runs found for these drivers. Lower the minimum laps, or pick another session.")
        return
    fuel_effect = pace.FUEL_EFFECT_S_PER_LAP if fuel else 0.0
    summary = pace.run_summary(runs, fuel_effect)
    label = {r.Run: f"{r.Run} {r.Compound[:1]}" for r in summary.itertuples()}
    runs = runs.assign(Label=runs["Run"].map(label), Adjusted=runs["LapSeconds"] + fuel_effect * runs["LapInRun"])
    mean_of = summary.set_index("Run")["mean"]
    best_mean = summary["mean"].min()

    with ui.card("Long-run pace distribution", "One violin per run, coloured by tyre (S soft, M medium, H hard). Hover for the mean lap and gap to the quickest run; the table below lists them all."):
        fig = go.Figure()
        for r in summary.sort_values("mean").itertuples():
            g = runs[runs["Run"] == r.Run]
            col = style.COMPOUND_COLORS.get(r.Compound, "#98A4B3")
            fig.add_trace(go.Violin(y=g["Adjusted"], name=label[r.Run],
                                    hovertemplate=f"{label[r.Run]}: mean {ui.fmt_lap(r.mean)} (+{r.mean - best_mean:.2f}s)<br>%{{y:.3f}}s<extra></extra>",
                                    points="all", pointpos=0, jitter=0.4, meanline_visible=True, line_color=col,
                                    fillcolor=_hex_rgba(col, 0.25), marker=dict(color=col, size=4), spanmode="hard",
                                    showlegend=False, width=0.9))
        fig.update_layout(yaxis_title="Lap time (s)" + (" (fuel adjusted)" if fuel else ""), violingap=0.1)
        fig.update_xaxes(tickangle=-60)
        ui.show(fig, 460)
        st.caption(f"Laps per run: {', '.join(f'{r.Run} {r.laps}' for r in summary.itertuples())}. "
                   "Only clean laps (no pit, non-green or >107% laps) are used.")

    with ui.card("Stint consistency and tyre degradation", "Lap time against lap of the run with a trend line. The slope is the degradation in seconds per lap. Click a legend entry to hide a run."):
        fig = go.Figure()
        for r in summary.itertuples():
            g = runs[runs["Run"] == r.Run]
            col = style.COMPOUND_COLORS.get(r.Compound, "#98A4B3")
            fig.add_trace(go.Scatter(x=g["LapInRun"], y=g["Adjusted"], mode="markers", name=label[r.Run], legendgroup=r.Run,
                                     marker=dict(color=col, size=6, line=dict(color="#090B0E", width=1))))
            xs = [g["LapInRun"].min(), g["LapInRun"].max()]
            fig.add_trace(go.Scatter(x=xs, y=[r.intercept + r.slope * x for x in xs], mode="lines", legendgroup=r.Run,
                                     showlegend=False, line=dict(color=col, width=2),
                                     hovertemplate=f"{label[r.Run]}: {r.slope:+.3f} s/lap<extra></extra>"))
        fig.update_layout(xaxis_title="Lap of run", yaxis_title="Lap time (s)")
        ui.show(fig, 440)
        shown = summary[["Run", "Compound", "laps", "mean", "slope", "std", "resid_std"]].rename(
            columns={"slope": "deg s/lap", "std": "std dev", "resid_std": "std dev after trend"})
        st.dataframe(shown.round(3), width="stretch", hide_index=True)

    left, right = st.columns(2)
    with left, ui.card("Driver consistency", "Standard deviation of lap time within each run, after removing its trend. Lower is better."):
        fig = px.bar(summary.sort_values("resid_std"), x="Run", y="resid_std", color="Compound",
                     color_discrete_map=style.COMPOUND_COLORS, labels={"resid_std": "Std dev (s)"})
        ui.show(fig, 320)
    with right, ui.card("Straight-line speed", "Average speed-trap speed over each run's laps."):
        if "SpeedST" in runs and runs["SpeedST"].notna().any():
            trap = runs.groupby("Run").agg(speed=("SpeedST", "mean"), laps=("SpeedST", "count"), Compound=("Compound", "first")).reset_index()
            fig = px.bar(trap.sort_values("speed", ascending=False), x="Run", y="speed", color="Compound",
                         color_discrete_map=style.COMPOUND_COLORS, labels={"speed": "Speed trap (km/h)"})
            fig.update_yaxes(range=[trap["speed"].min() - 8, trap["speed"].max() + 3])
            ui.show(fig, 320)
            st.caption("Whether DRS was open on each lap is not available here, so compare runs with care.")
        else:
            st.info("No speed-trap data for this session.")
