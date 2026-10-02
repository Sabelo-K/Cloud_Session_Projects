"""Telemetry Analyser: overlay any drivers and laps on five linked channels."""
import streamlit as st

from f1 import charts, data, style, telemetry, ui


@st.cache_data(show_spinner="Loading telemetry (slow the first time)...")
def _telemetry(year, rnd, kind, picks):
    return data.load_lap_telemetry(year, rnd, kind, picks)


@st.cache_data(show_spinner=False)
def _corners(year, rnd, kind):
    return data.load_corners(year, rnd, kind)


def render():
    ui.title("Telemetry Analyser", "Compare any drivers on any laps. Add a second group to compare the same drivers on a different lap.")
    year, rnd, event, kind = ui.session_controls("telemetry", list(data.SESSION_NAMES), "Q")
    laps = ui.load_laps(year, rnd, kind)
    colours = style.distinct_colours(laps)
    all_drivers = sorted(laps["Driver"].unique())
    valid = laps.dropna(subset=["LapTime"])
    max_lap = int(valid["LapNumber"].max())
    fastest_lap = int(valid.loc[valid["LapTime"].idxmin(), "LapNumber"])

    ss = st.session_state
    sig = (year, rnd, kind)
    if ss.get("ta_sig") != sig:  # new session: old lap choices may not exist here
        ss["ta_sig"] = sig
        quickest = valid.groupby("Driver")["LapTime"].min().nsmallest(2).index
        ss["ta_groups"] = [{"id": 0, "lap": fastest_lap, "drivers": list(quickest)}]
        ss["ta_next"] = 1
    groups = ss["ta_groups"]

    for i, grp in enumerate(groups):
        with st.container(border=True):
            h1, h2 = st.columns([5, 1])
            h1.markdown(f'<p class="card-title">Comparison Group {i + 1}</p>', unsafe_allow_html=True)
            if len(groups) > 1 and h2.button("Remove", key=f"ta_rm_{grp['id']}"):
                groups.pop(i)
                st.rerun()
            c1, c2 = st.columns([1, 3])
            grp["lap"] = c1.number_input("Lap", 1, max_lap, min(grp["lap"], max_lap), key=f"ta_lap_{grp['id']}")
            grp["drivers"] = c2.multiselect("Drivers to plot", all_drivers, default=[d for d in grp["drivers"] if d in all_drivers],
                                            key=f"ta_drv_{grp['id']}", max_selections=4)
    if len(groups) < 4 and st.button("Add lap group"):
        groups.append({"id": ss["ta_next"], "lap": fastest_lap, "drivers": list(groups[-1]["drivers"])})
        ss["ta_next"] += 1
        st.rerun()

    picks = []
    for grp in groups:
        picks += [(d, int(grp["lap"])) for d in grp["drivers"]]
    picks = tuple(dict.fromkeys(picks))
    if not picks:
        st.info("Pick at least one driver in a group.")
        return
    tels = _telemetry(year, rnd, kind, picks)
    missing = [f"{d} lap {n}" for d, n in picks if f"{d}|{n}" not in tels]
    if missing:
        st.warning("No telemetry for: " + ", ".join(missing) + ". Those laps may be deleted, or the car was in the pits.")
    if not tels:
        return

    res = telemetry.resample_all(tels, step=5.0)
    dash = {}
    for gi, grp in enumerate(groups):
        for d in grp["drivers"]:
            dash.setdefault(f"{d}|{int(grp['lap'])}", charts.GROUP_DASHES[gi % 4])
    ui.chips(list(res), colours)
    with ui.card("Telemetry", "Drag across a chart to zoom into that part of the lap, double-click to reset. All five charts zoom together. "
                              "Solid, dashed and dotted lines mark the group a lap belongs to."):
        ui.show(charts.telemetry_stack(res, colours, dash, _corners(year, rnd, kind)), 900)
