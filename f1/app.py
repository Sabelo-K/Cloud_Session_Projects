"""Streamlit entry point. Run: python -m streamlit run f1/app.py"""
import sys
from pathlib import Path

import streamlit as st

# Streamlit Cloud puts f1/ (the script folder) on sys.path, not the repo root, so `from f1 import ...` fails there.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

st.set_page_config(page_title="F1 Insights", page_icon="🏁", layout="wide")

from f1 import ui  # noqa: E402  (after set_page_config, which must be the first Streamlit call)
from f1.views import (car_performance, championship, home, lap_replay, practice, race_pace, sectors_maps, season_pace,  # noqa: E402
                      prediction_league, single_lap, strategy_weather, telemetry_analyser, weekend)

ui.inject_css()

PAGES = [
    st.Page(home.render, title="Home", icon="🏁", url_path="home", default=True),
    st.Page(weekend.render, title="Race Weekend Summary", icon="📋", url_path="weekend"),
    st.Page(race_pace.render, title="Race Pace Insights", icon="⏱️", url_path="race-pace"),
    st.Page(telemetry_analyser.render, title="Telemetry Analyser", icon="📈", url_path="telemetry"),
    st.Page(single_lap.render, title="Single Lap Comparison", icon="🗺️", url_path="single-lap"),
    st.Page(lap_replay.render, title="Lap Replay", icon="🎬", url_path="replay"),
    st.Page(practice.render, title="Practice Insights", icon="🛞", url_path="practice"),
    st.Page(sectors_maps.render, title="Sectors & Maps", icon="🧭", url_path="sectors"),
    st.Page(strategy_weather.render, title="Strategy & Weather", icon="⛅", url_path="strategy"),
    st.Page(season_pace.render, title="Season Pace", icon="📊", url_path="season-pace"),
    st.Page(car_performance.render, title="Car Performance", icon="🏎️", url_path="cars"),
    st.Page(prediction_league.render, title="Prediction League", icon="🎯", url_path="league"),
    st.Page(championship.render, title="Championship", icon="🏆", url_path="championship"),
]
st.navigation(PAGES).run()
