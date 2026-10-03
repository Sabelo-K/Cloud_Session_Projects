"""Practice Insights: long-run pace, tyre degradation, consistency and straight-line speed."""
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from f1 import charts, data, pace, style, tyres, ui


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

    ui.tyre_legend(laps[laps["Driver"].isin(drivers)])
    c1, c2 = st.columns(2)
    min_laps = c1.slider("Minimum clean laps for a long run", 3, 12, 5)
    fuel = c2.toggle("Adjust for fuel burn (0.03 s per lap)", value=False)
    runs = pace.long_runs(laps[laps["Driver"].isin(drivers)], min_laps)
    if runs.empty:
        st.info("No long runs found for these drivers. Lower the minimum laps, or pick another session.")
        return
    fuel_effect = pace.FUEL_EFFECT_S_PER_LAP if fuel else 0.0
    summary = pace.run_summary(runs, fuel_effect)
    label = {r.Run: f"{r.Run} {tyres.letter(r.Compound)}" for r in summary.itertuples()}
    runs = runs.assign(Label=runs["Run"].map(label), Adjusted=runs["LapSeconds"] + fuel_effect * runs["LapInRun"])
    mean_of = summary.set_index("Run")["mean"]
    best_mean = summary["mean"].min()

    with ui.card("Long run pace violin plot", "One violin per driver, in the team colour. Each dot is a clean long-run lap in its tyre colour. "
                                              "Under each violin: the driver's average lap and the gap to the quickest driver."):
        ui.show(charts.long_run_violin(runs, colours, f"Long Run Pace Violin Plot: {event} {year} {kind}"), 560)

    with ui.card("Long-run pace distribution", "One violin per run, coloured by tyre (S soft, M medium, H hard, I intermediate, W wet, ? unknown). Hover for the mean lap and gap to the quickest run; the table below lists them all."):
        fig = go.Figure()
        for r in summary.sort_values("mean").itertuples():
            g = runs[runs["Run"] == r.Run]
            col = tyres.colour(r.Compound)
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

    with ui.card("Stint consistency and tyre degradation", "Lap time against lap of the run, in team colours (a driver's later stints dashed), dots in tyre colour. Click a legend entry to hide a run, double-click to show only that run. The table gives each run's degradation in seconds per lap."):
        fig = go.Figure()
        seen: dict[str, int] = {}
        for r in summary.sort_values(["Driver", "Stint"]).itertuples():
            g = runs[runs["Run"] == r.Run].sort_values("LapInRun")
            seen[r.Driver] = seen.get(r.Driver, 0) + 1
            team = colours.get(r.Driver, "#98A4B3")
            fig.add_trace(go.Scatter(
                x=g["LapInRun"], y=g["Adjusted"], mode="lines+markers", name=label[r.Run], legendgroup=r.Run,
                line=dict(color=team, width=2, dash="solid" if seen[r.Driver] == 1 else "dash"),  # a driver's later stints are dashed
                marker=dict(color=[tyres.colour(c) for c in g["Compound"]], size=9, line=dict(color="#0A0B0E", width=1)),
                text=[f"{label[r.Run]} lap {int(n)}<br>{tyres.name(c)}" for n, c in zip(g["LapNumber"], g["Compound"])],
                hovertemplate="%{text}<br>Lap Time: %{y:.3f}s<extra></extra>"))
        fig.update_layout(xaxis_title="Lap Number in Stint", yaxis_title="Lap Time (s)",
                          legend=dict(orientation="v", x=1.01, y=1, title_text="Stints (Click to toggle)", itemclick="toggle", itemdoubleclick="toggleothers"))
        ui.show(fig, 440)
        shown = summary[["Run", "Compound", "laps", "mean", "slope", "std", "resid_std"]].rename(
            columns={"slope": "deg s/lap", "std": "std dev", "resid_std": "std dev after trend"})
        st.dataframe(shown.round(3), width="stretch", hide_index=True)

    left, right = st.columns(2)
    with left, ui.card("Driver consistency", "Standard deviation of lap time within each run, after removing its trend. Lower is better. Bars are in team colours."):
        ordered = summary.sort_values("resid_std")
        fig = px.bar(ordered, x="Run", y="resid_std", color="Driver", color_discrete_map=colours, labels={"resid_std": "Std dev (s)"},
                     category_orders={"Run": list(ordered["Run"])})
        fig.update_layout(showlegend=False, bargap=0.25)
        ui.show(fig, 320)
    with right, ui.card("Straight-line speed", "Average speed-trap speed over each run's laps."):
        if "SpeedST" in runs and runs["SpeedST"].notna().any():
            trap = runs.groupby("Run").agg(speed=("SpeedST", "mean"), laps=("SpeedST", "count"), Compound=("Compound", "first")).reset_index()
            trap = trap.merge(summary[["Run", "Driver"]], on="Run").sort_values("speed", ascending=False)
            fig = px.bar(trap, x="Run", y="speed", color="Driver", color_discrete_map=colours, labels={"speed": "Speed trap (km/h)"},
                         category_orders={"Run": list(trap["Run"])})
            fig.update_layout(showlegend=False, bargap=0.25)
            fig.update_yaxes(range=[trap["speed"].min() - 8, trap["speed"].max() + 3])
            ui.show(fig, 320)
            st.caption("Whether DRS was open on each lap is not available here, so compare runs with care.")
        else:
            st.info("No speed-trap data for this session.")
