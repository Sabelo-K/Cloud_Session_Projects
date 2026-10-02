"""Streamlit entry point. Run: python -m streamlit run f1/app.py"""
import streamlit as st

st.set_page_config(page_title="F1 Insights", page_icon="🏁", layout="wide")

from f1 import ui  # noqa: E402  (after set_page_config, which must be the first Streamlit call)
from f1.views import (championship, home, practice, race_pace, sectors_maps, season_pace,  # noqa: E402
                      single_lap, strategy_weather, telemetry_analyser)

ui.inject_css()

PAGES = [
    st.Page(home.render, title="Home", icon="🏁", url_path="home", default=True),
    st.Page(race_pace.render, title="Race Pace Insights", icon="⏱️", url_path="race-pace"),
    st.Page(telemetry_analyser.render, title="Telemetry Analyser", icon="📈", url_path="telemetry"),
    st.Page(single_lap.render, title="Single Lap Comparison", icon="🗺️", url_path="single-lap"),
    st.Page(practice.render, title="Practice Insights", icon="🛞", url_path="practice"),
    st.Page(sectors_maps.render, title="Sectors & Maps", icon="🧭", url_path="sectors"),
    st.Page(strategy_weather.render, title="Strategy & Weather", icon="⛅", url_path="strategy"),
    st.Page(season_pace.render, title="Season Pace", icon="📊", url_path="season-pace"),
    st.Page(championship.render, title="Championship", icon="🏆", url_path="championship"),
]
st.navigation(PAGES).run()
