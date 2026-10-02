"""Championship: driver points after each completed round."""
from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from f1 import data, standings, style, ui


@st.cache_data(show_spinner="Loading standings...")
def _standings(year: int, rounds: tuple):
    return standings.progression(data.season_standings(year, list(rounds)))


def render():
    ui.title("Championship", "Driver points after each completed round.")
    year = ui._remembered("Season", list(range(date.today().year, 2017, -1)), "championship", "year", date.today().year)
    sched = ui.schedule_for(year)
    rounds = tuple(int(r) for r in sched[sched["date"] <= str(pd.Timestamp.today().date())]["round"])
    if not rounds:
        st.info("No completed rounds yet this season.")
        return
    prog = _standings(year, rounds)
    top = prog[prog["Round"] == prog["Round"].max()].nlargest(10, "Points")["Driver"]
    with ui.card("Points progression", "Top ten drivers."):
        fig = px.line(prog[prog["Driver"].isin(top)], x="Round", y="Points", color="Driver", markers=True)
        ui.show(fig, 460)
