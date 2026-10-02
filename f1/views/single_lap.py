"""Single Lap Comparison: up to three drivers on one lap each, with track dominance, corners, speed and delta."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from f1 import charts, data, pace, store, style, telemetry, tyres, ui


@st.cache_data(show_spinner="Loading telemetry (slow the first time)...")
def _telemetry(year, rnd, kind, picks):
    return data.load_lap_telemetry(year, rnd, kind, picks)


@st.cache_data(show_spinner=False)
def _corners(year, rnd, kind):
    return data.load_corners(year, rnd, kind)


def render():
    ui.title("Single Lap Comparison", "Up to three drivers, one lap each. Find where the time was won and lost.")
    year, rnd, event, kind = ui.session_controls("single_lap", list(data.SESSION_NAMES), "Q")
    laps = ui.load_laps(year, rnd, kind)
    colours = style.distinct_colours(laps)
    drivers = ui.driver_picker("single_lap", sorted(laps["Driver"].unique()), colours, default_n=2, max_selected=3)
    if not drivers:
        st.info("Pick at least one driver above (up to three).")
        return

    valid = laps.dropna(subset=["LapTime"])
    if data.offline():  # hosted copy: only laps whose telemetry was saved can be compared
        saved = store.stored_telemetry_laps(year, rnd, kind)
        valid = valid[[(d, int(n)) in saved for d, n in zip(valid["Driver"], valid["LapNumber"])]]
        if valid.empty:
            st.info("No telemetry was saved for this session." + ui.SAVED_ONLY_HINT)
            return
    picks = []
    cols = st.columns(len(drivers))
    for col, drv in zip(cols, drivers):
        mine = valid[valid["Driver"] == drv].sort_values("LapNumber")
        if mine.empty:
            col.warning(f"{drv} has no timed laps.")
            continue
        fast = int(mine.loc[mine["LapTime"].idxmin(), "LapNumber"])
        options = [int(n) for n in mine["LapNumber"]]
        lap_no = col.selectbox(f"{drv} lap", options, index=options.index(fast), key=f"sl_{drv}_{year}_{rnd}_{kind}",
                               format_func=lambda n, fast=fast: f"Lap {n}" + (" (fastest)" if n == fast else ""))
        row = mine[mine["LapNumber"] == lap_no].iloc[0]
        age = f' · {int(row["TyreLife"])} laps old' if "TyreLife" in row and pd.notna(row["TyreLife"]) else ""
        if "FreshTyre" in row and pd.notna(row["FreshTyre"]):
            age += " · new set" if bool(row["FreshTyre"]) else " · used set"
        col.markdown(f'<span class="chip"><i style="background:{colours.get(drv)}"></i>{drv}</span>'
                     f'<span class="badge tnum">{ui.fmt_lap(row["LapTime"].total_seconds())}</span>'
                     f'<span class="badge">{ui.tyre_dot(row.get("Compound"))}{tyres.name(row.get("Compound"))}{age}</span>', unsafe_allow_html=True)
        picks.append((drv, int(lap_no)))
    if not picks:
        return

    tels = _telemetry(year, rnd, kind, tuple(picks))
    missing = [f"{d} lap {n}" for d, n in picks if f"{d}|{n}" not in tels]
    if missing:
        st.warning("No telemetry for: " + ", ".join(missing) + ". Showing the rest." + (ui.SAVED_ONLY_HINT if data.offline() else ""))
    if len(tels) < 2:
        st.info("Pick at least two drivers with telemetry to compare.")
        return
    corners = _corners(year, rnd, kind)
    res = telemetry.resample_all(tels, step=5.0)
    labels = list(res)

    c1, c2, c3 = st.columns(3)
    ref = c1.selectbox("Reference for time delta", labels, index=0, format_func=charts.pretty)
    seg = c2.selectbox("Track segment size", [10, 25, 40, 60], index=1, format_func=lambda m: f"{m} m")
    thr = c3.slider("High-speed corner from (km/h)", 80, 250, 150, 10)

    top, side = st.columns([3, 2])
    with top, ui.card("Track dominance", "Each stretch of track is coloured by who got through it quickest (traversal time, not top speed). Hover to see the time gained."):
        dom = telemetry.track_dominance(res, seg)
        ui.show(charts.dominance_map(dom, colours, corners), 480)
    with side, ui.card("Cornering performance", f"Corners won on apex speed. High speed means an average apex of at least {thr} km/h."):
        if corners.empty:
            st.info("No corner data for this circuit.")
        else:
            cs = telemetry.corner_speeds(res, corners, threshold=thr)
            wins = telemetry.apex_wins(cs)
            fig = px.bar(wins.assign(Name=wins["Lap"].map(charts.pretty)), x="Name", y="Wins", color="Lap", facet_col="Class", hover_data=["Corners"],
                         color_discrete_map={l: colours.get(charts.driver_of(l)) for l in labels},
                         category_orders={"Class": ["High", "Low"]})
            fig.update_layout(showlegend=False)
            fig.for_each_annotation(lambda a: a.update(text=a.text.replace("Class=", "") + " speed"))
            ui.show(fig, 330)
            with st.expander("Apex speeds by corner"):
                st.dataframe(cs.pivot(index="Corner", columns="Lap", values="ApexSpeed").round(0).rename(columns=charts.pretty), width="stretch")

    dashes = {l: charts.GROUP_DASHES[i % 4] if i else "solid" for i, l in enumerate(labels)}
    same_driver = len({charts.driver_of(l) for l in labels}) < len(labels)
    if not same_driver:
        dashes = {l: "solid" for l in labels}
    with ui.card("Speed trace and time delta", f"Zero is {charts.pretty(ref)}. Above zero means slower than {charts.pretty(ref)} at that point on the lap. Drag to zoom, double-click to reset."):
        ui.show(charts.speed_with_corners(res, colours, dashes, corners, ref), 560)

    with ui.card("Raw telemetry", "Throttle, brake, RPM and gear against distance."):
        tabs = st.tabs(["Throttle", "Brake", "RPM", "Gear"])
        for tab, (col, title, shape) in zip(tabs, [("Throttle", "Throttle (%)", None), ("Brake", "Brake (off/on)", "hv"),
                                                    ("RPM", "Engine RPM", None), ("nGear", "Gear", "hv")]):
            with tab:
                fig = go.Figure()
                for l, df in res.items():
                    if col in df:
                        line = dict(color=colours.get(charts.driver_of(l)), dash=dashes.get(l, "solid"))
                        if shape:
                            line["shape"] = shape
                        fig.add_trace(go.Scatter(x=df["Distance"], y=df[col], name=charts.pretty(l), line=line))
                fig.update_layout(xaxis_title="Distance (m)", yaxis_title=title)
                if col == "Brake":
                    fig.update_yaxes(tickvals=[0, 1], ticktext=["Off", "On"])
                ui.show(fig, 340)
