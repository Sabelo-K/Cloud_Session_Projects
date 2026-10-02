"""Strategy & Weather: tyre stints, pit stops and session conditions."""
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from f1 import charts, data, pace, style, ui


@st.cache_data(show_spinner="Loading weather...")
def _weather(year, rnd, kind):
    return data.load_weather(year, rnd, kind)


def render():
    ui.title("Strategy & Weather", "Tyre stints, pit stops and the conditions they were run in.")
    year, rnd, event, kind = ui.session_controls("strategy", list(data.SESSION_NAMES), "R")
    laps = ui.load_laps(year, rnd, kind)
    colours, _ = style.driver_styles(laps)
    drivers = ui.driver_picker("strategy", sorted(laps["Driver"].unique()), colours, default_n=20)
    if not drivers:
        st.info("Pick at least one driver above.")
        return
    sel = laps[laps["Driver"].isin(drivers)]

    if "Position" in sel and sel["Position"].notna().any():
        last = sel.sort_values("LapNumber").groupby("Driver").tail(1).sort_values("Position")
        order = list(last["Driver"])
    else:
        order = sorted(drivers)
    with ui.card("Tyre strategy", "One row per driver (finishing order in a race). Each block is a stint; hover for laps and starting tyre age."):
        ui.show(charts.stint_timeline(sel, order), max(300, 26 * len(order) + 110))
    with st.expander("Pit stops"):
        stops = pace.pit_stops(sel)
        st.dataframe(stops, width="stretch", hide_index=True)
        st.caption("Stationary time and total pit-lane time loss are not available here; this lists the lap, tyres and new tyre age.")

    with ui.card("Weather", "Conditions during the session."):
        w = _weather(year, rnd, kind)
        if w.empty:
            st.info("Weather data is not available for this session.")
            return
        t = w["Time"].dt.total_seconds() / 60
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                            subplot_titles=("Temperature (°C)", "Humidity (%) and rain", "Wind (m/s)"))
        fig.add_trace(go.Scatter(x=t, y=w["AirTemp"], name="Air", line=dict(color="#00D5CF")), row=1, col=1)
        fig.add_trace(go.Scatter(x=t, y=w["TrackTemp"], name="Track", line=dict(color="#FF8000")), row=1, col=1)
        fig.add_trace(go.Scatter(x=t, y=w["Humidity"], name="Humidity", line=dict(color="#64C4FF")), row=2, col=1)
        if "Rainfall" in w and w["Rainfall"].any():
            fig.add_trace(go.Scatter(x=t, y=w["Rainfall"].astype(int) * 100, name="Raining", fill="tozeroy",
                                     line=dict(color="#3E7BFA", width=0), opacity=0.4), row=2, col=1)
        fig.add_trace(go.Scatter(x=t, y=w["WindSpeed"], name="Wind", line=dict(color="#FFD60A")), row=3, col=1)
        fig.update_xaxes(title_text="Minutes into session", row=3, col=1)
        ui.show(fig, 560)
