"""Lap Replay: watch fast laps being driven on the circuit, with each sector time appearing as the car passes it."""
import pandas as pd
import streamlit as st

from f1 import charts, data, replay, store, style, ui


@st.cache_data(show_spinner="Loading telemetry (slow the first time)...")
def _telemetry(year, rnd, kind, picks):
    return data.load_lap_telemetry(year, rnd, kind, picks)


@st.cache_data(show_spinner=False)
def _corners(year, rnd, kind):
    return data.load_corners(year, rnd, kind)


@st.cache_data(show_spinner=False)
def _timeline(year, rnd, kind, key, picks):
    return replay.timeline(_telemetry(year, rnd, kind, picks)[key])


def render():
    ui.title("Lap Replay", "Press play to watch the picked laps being driven. Each sector time appears as the car passes the sector line.")
    year, rnd, event, kind = ui.session_controls("replay", list(data.SESSION_NAMES), "Q")
    laps = ui.load_laps(year, rnd, kind)
    colours = style.distinct_colours(laps)

    valid = laps.dropna(subset=["LapTime"])
    if "Deleted" in valid.columns:
        valid = valid[~store.as_bool(valid["Deleted"])]
    if data.offline():  # hosted copy: only laps whose telemetry was saved can be replayed
        saved = store.stored_telemetry_laps(year, rnd, kind)
        valid = valid[[(d, int(n)) in saved for d, n in zip(valid["Driver"], valid["LapNumber"])]]
        if valid.empty:
            st.info("No telemetry was saved for this session." + ui.SAVED_ONLY_HINT)
            return
    best = valid.groupby("Driver")["LapTime"].min().sort_values()
    drivers = ui.driver_picker("replay", list(best.index), colours, default_n=2, max_selected=3)
    if not drivers:
        st.info("Pick at least one driver above (up to three).")
        return

    chosen = {}
    cols = st.columns(len(drivers))
    for col, drv in zip(cols, drivers):
        mine = valid[valid["Driver"] == drv].sort_values("LapNumber")
        fast = int(mine.loc[mine["LapTime"].idxmin(), "LapNumber"])
        options = [int(n) for n in mine["LapNumber"]]
        chosen[drv] = col.selectbox(f"{drv} lap", options, index=options.index(fast), key=f"rp_{drv}_{year}_{rnd}_{kind}",
                                    format_func=lambda n, fast=fast: f"Lap {n}" + (" (fastest)" if n == fast else ""))
    picks = tuple((d, int(n)) for d, n in chosen.items())
    c1, c2 = st.columns([2, 3])
    reference = c1.selectbox("Reference driver", drivers, help="The delta is shown from this driver's point of view: green when they are ahead of the others, red when behind.") if len(drivers) > 1 else drivers[0]
    speed = c2.segmented_control("Playback speed", ["0.5x", "1x", "2x", "4x"], default="1x") or "1x"

    tels = _telemetry(year, rnd, kind, picks)
    runs, missing = [], []
    for drv, lap_no in picks:
        key = f"{drv}|{lap_no}"
        if key not in tels:
            missing.append(f"{drv} lap {lap_no}")
            continue
        row = laps[(laps["Driver"] == drv) & (laps["LapNumber"] == lap_no)].iloc[0]
        runs.append(dict(label=drv, colour=colours.get(drv, "#00D5CF"), tl=_timeline(year, rnd, kind, key, picks),
                         splits=replay.splits_from_row(row), lap_time=float(pd.Timedelta(row["LapTime"]).total_seconds()),
                         tyre=row.get("Compound"), lap=lap_no))
    runs.sort(key=lambda r: r["label"] != reference)  # the reference driver leads, the others are measured against them
    replay.attach_deltas(runs)
    if missing:
        st.warning("No telemetry for: " + ", ".join(missing) + ". Showing the rest." + (ui.SAVED_ONLY_HINT if data.offline() else ""))
    if not runs:
        return
    if any(r["splits"] is None for r in runs):
        st.caption("Sector times are not available for some of these laps, so their sector rows stay empty.")

    with ui.card("Replay", f"Dots start together at the line. The dotted line joins {runs[0]['label']} to each other driver: green when {runs[0]['label']} is ahead, "
                           "red when behind, with the gap in seconds in the timing panel. Numbered circles are the corners. Purple is the quickest sector shown. Use the slider to jump anywhere."):
        fig = style.style_fig(charts.lap_replay(runs, float(speed.rstrip("x")), corners=_corners(year, rnd, kind)), 600)
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=120))
        st.plotly_chart(fig, width="stretch", config=style.PLOT_CONFIG)
    with ui.card("Lap summary", "Sector times and lap time for the laps replayed above."):
        st.dataframe(replay.results_table(runs), width="stretch", hide_index=True)
