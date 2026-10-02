"""Race Pace Insights: distribution, raw laps, gap to leader, consistency and traffic."""
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from f1 import data, pace, style, ui


def _box(tagged, stats, colours, show_excluded):
    fig = go.Figure()
    labels = {r.Driver: f"{r.Driver}<br>+{r.delta_to_best:.2f}" for r in stats.itertuples()}
    for r in stats.itertuples():
        g = tagged[(tagged["Driver"] == r.Driver) & ~tagged["Excluded"]]
        fig.add_trace(go.Box(y=g["LapSeconds"], name=labels[r.Driver], boxmean=True, boxpoints=False,
                             marker_color=colours.get(r.Driver), line=dict(color=colours.get(r.Driver)),
                             legendgroup=r.Driver, showlegend=False))
    if show_excluded:
        ex = tagged[tagged["Excluded"] & tagged["LapSeconds"].notna() & tagged["Driver"].isin(labels)]
        fig.add_trace(go.Scatter(x=[labels[d] for d in ex["Driver"]], y=ex["LapSeconds"], mode="markers", name="Excluded laps",
                                 marker=dict(symbol="x", color="#98A4B3", size=7), text=ex["Reason"],
                                 hovertemplate="%{y:.3f}s<br>%{text}<extra>Excluded</extra>"))
    fig.update_layout(yaxis_title="Lap time (s)", xaxis_title="Driver and median gap to the best (s)",
                      showlegend=show_excluded)
    return fig


def _raw(tagged, colours, dashes, show_excluded):
    fig = go.Figure()
    hover = ("%{customdata[0]} · %{customdata[1]}<br>Lap %{x} · %{y:.3f}s<br>%{customdata[2]} · tyre age %{customdata[3]}"
             "<br>Stint %{customdata[4]} · track status %{customdata[5]} · P%{customdata[6]}<extra></extra>")
    cols = ["Driver", "Team", "Compound", "TyreLife", "Stint", "TrackStatus", "Position"]
    for drv, g in tagged.groupby("Driver"):
        keep = g[~g["Excluded"]].sort_values("LapNumber")
        fig.add_trace(go.Scatter(x=keep["LapNumber"], y=keep["LapSeconds"], mode="lines+markers", name=drv,
                                 line=dict(color=colours.get(drv), dash=dashes.get(drv, "solid"), width=1.5),
                                 marker=dict(size=4), customdata=keep.reindex(columns=cols).to_numpy(), hovertemplate=hover))
    if show_excluded:
        ex = tagged[tagged["Excluded"] & tagged["LapSeconds"].notna()]
        fig.add_trace(go.Scatter(x=ex["LapNumber"], y=ex["LapSeconds"], mode="markers", name="Excluded laps",
                                 marker=dict(symbol="x", color="#98A4B3", size=7), text=ex["Reason"] + " · " + ex["Driver"],
                                 hovertemplate="Lap %{x} · %{y:.3f}s<br>%{text}<extra></extra>"))
    fig.update_layout(xaxis_title="Lap", yaxis_title="Lap time (s)", dragmode="zoom")
    return fig


def render():
    ui.title("Race Pace Insights", "How fast, how consistent and how free of traffic each car really was.")
    year, rnd, event, kind = ui.session_controls("race_pace", ["R", "S"], "R")
    laps = ui.load_laps(year, rnd, kind)
    colours, dashes = style.driver_styles(laps)
    drivers = ui.driver_picker("race_pace", sorted(laps["Driver"].unique()), colours)
    if not drivers:
        st.info("Pick at least one driver above.")
        return
    sel = laps[laps["Driver"].isin(drivers)]
    tagged = pace.tag_laps(sel)

    c1, c2 = st.columns([2, 1])
    view = c1.segmented_control("Pace view", ["Box plot", "Raw laps"], default="Box plot", label_visibility="collapsed") or "Box plot"
    show_excluded = c2.toggle("Show excluded laps", value=False)

    stats = pace.distribution_stats(sel)
    with ui.card("Pace distribution" if view == "Box plot" else "Raw lap times",
                 "Each box spans the middle half of a driver's clean laps; the dashed line is the mean. Drivers are ordered by median."
                 if view == "Box plot" else "Every lap. Hover for tyre, stint, track status and position. Drag to zoom, double-click to reset."):
        ui.show(_box(tagged, stats, colours, show_excluded) if view == "Box plot" else _raw(tagged, colours, dashes, show_excluded), 430)
        st.caption(f"Clean laps used: {', '.join(f'{r.Driver} {r.laps}' for r in stats.itertuples())}. "
                   "Excluded: laps without a time, pit in/out laps, non-green laps and laps over 107% of the driver's median.")
    with st.expander("Distribution table and excluded laps"):
        st.dataframe(stats.round(3), width="stretch", hide_index=True)
        ex = tagged[tagged["Excluded"]]
        st.write(ex["Reason"].str.replace(r"\(.*\)", "", regex=True).value_counts().rename("laps").to_frame())

    with ui.card("Gap to leader", "Seconds behind the race leader at the end of each lap. Zero is the leader; below zero means behind."):
        if "Time" in laps:
            gap = pace.gap_to_leader(laps)
            gap = gap[gap["Driver"].isin(drivers)]
            fig = go.Figure()
            for drv, g in gap.groupby("Driver"):
                fig.add_trace(go.Scatter(x=g["LapNumber"], y=g["GapToLeader"], name=drv,
                                         line=dict(color=colours.get(drv), dash=dashes.get(drv, "solid"))))
            fig.update_layout(xaxis_title="Lap", yaxis_title="Gap to leader (s)", hovermode="x unified")
            ui.show(fig, 400)
        else:
            st.info("This session has no cumulative lap timing.")

    left, right = st.columns(2)
    with left, ui.card("Driver consistency", "Lap-time standard deviation of clean laps. Lower is more consistent."):
        detrend = st.toggle("Remove tyre wear and fuel trend within each stint", value=True)
        cons = pace.consistency(sel, detrend=detrend)
        if cons.empty:
            st.info("Not enough clean laps.")
        else:
            fig = px.bar(cons, x="Driver", y="std", color="Driver", color_discrete_map=colours,
                         labels={"std": "Std dev (s)"})
            fig.update_layout(showlegend=False)
            ui.show(fig, 320)
    with right, ui.card("Traffic", "Laps finished close to the car ahead. It is an indicator, not proof of lost pace."):
        thr = st.slider("Counts as traffic within (s)", 0.5, 3.0, 1.5, 0.1)
        if "Position" in laps:
            tr = pace.traffic(laps, thr)
            tr = tr[tr["Driver"].isin(drivers)]
            fig = px.bar(tr, x="Driver", y="in_traffic", color="Driver", color_discrete_map=colours,
                         labels={"in_traffic": "Laps in traffic"})
            fig.update_layout(showlegend=False)
            ui.show(fig, 320)
        else:
            st.info("No position data for this session.")
