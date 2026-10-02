"""Streamlit UI. Run: python -m streamlit run f1/app.py"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from f1 import data, pace, standings, telemetry

st.set_page_config(page_title="F1 analysis", layout="wide")
st.title("F1 race analysis")

year = int(st.sidebar.number_input("Season", 2018, 2026, 2024))


@st.cache_data(show_spinner=False)
def schedule_for(y: int):
    return data.season_schedule(y)


@st.cache_data(show_spinner="Loading laps (first load is slow)...")
def laps_for(y: int, r: int, kind: str):
    return data.load_session_laps(y, r, kind)


@st.cache_data(show_spinner="Loading standings...")
def standings_for(y: int, rounds: tuple):
    return standings.progression(data.season_standings(y, list(rounds)))


@st.cache_data(show_spinner="Loading telemetry (slow the first time)...")
def telemetry_for(y: int, r: int, kind: str, drivers: tuple):
    return data.load_fastest_lap_telemetry(y, r, kind, list(drivers))


sched = schedule_for(year)
race = int(st.sidebar.selectbox("Race", sched["round"], format_func=lambda r: sched.set_index("round").loc[r, "name"]))

laps = laps_for(year, race, "R")
all_drivers = sorted(laps["Driver"].unique())
drivers = st.sidebar.multiselect("Drivers", all_drivers, default=all_drivers[:4])
sel = laps[laps["Driver"].isin(drivers)]

t_laps, t_pace, t_stints, t_deg, t_champ, t_quali = st.tabs(
    ["Lap times", "Race pace", "Tyre stints", "Tyre degradation", "Championship", "Qualifying & telemetry"]
)

with t_laps:
    show_all = st.checkbox("Show pit, safety car and slow laps", value=False)
    d = pace.lap_chart_frame(sel, show_all=show_all)
    st.plotly_chart(px.line(d, x="LapNumber", y="LapSeconds", color="Driver"), width="stretch")

with t_pace:
    p = pace.race_pace(laps)
    st.dataframe(p[p["Driver"].isin(drivers)], width="stretch")
    st.plotly_chart(px.bar(p, x="Driver", y="gap_to_best", title="Gap to best median clean lap (s)"), width="stretch")

with t_stints:
    s = pace.stint_summary(sel)
    s["Laps"] = s["EndLap"] - s["StartLap"] + 1
    fig = px.bar(s, x="Laps", base="StartLap", y="Driver", color="Compound", orientation="h",
                 labels={"Laps": "Lap number"})
    st.plotly_chart(fig, width="stretch")
    st.dataframe(s, width="stretch")

with t_deg:
    st.caption("Slope of fuel-corrected clean lap time against tyre age, pooled over all drivers "
               "(assumes ~0.03 s/lap fuel effect). Positive = losing pace.")
    if "TyreLife" in laps.columns:
        deg = pace.compound_degradation(laps)
        st.dataframe(deg, width="stretch")
        if not deg.empty:
            st.plotly_chart(px.bar(deg, x="Compound", y="deg_per_lap", title="Degradation (s per lap of tyre age)"),
                            width="stretch")
    else:
        st.info("This session has no tyre age data.")

with t_champ:
    rounds = tuple(int(r) for r in sched[sched["date"] <= str(pd.Timestamp.today().date())]["round"])
    if not rounds:
        st.info("No completed rounds yet this season.")
    else:
        prog = standings_for(year, rounds)
        top = prog[prog["Round"] == prog["Round"].max()].nlargest(10, "Points")["Driver"]
        st.plotly_chart(px.line(prog[prog["Driver"].isin(top)], x="Round", y="Points", color="Driver", markers=True,
                                title="Championship points after each round (top 10)"), width="stretch")

with t_quali:
    kind = st.radio("Session", ["Q", "R"], format_func=lambda k: {"Q": "Qualifying", "R": "Race"}[k], horizontal=True)
    ql = laps_for(year, race, kind)
    best = telemetry.best_lap_times(ql)
    st.dataframe(best, width="stretch")
    pair = st.multiselect("Compare two drivers' fastest laps", list(best["Driver"]), default=list(best["Driver"][:2]),
                          max_selections=2)
    if len(pair) == 2:
        tel = telemetry_for(year, race, kind, tuple(pair))
        if all(d in tel for d in pair):
            cmp = telemetry.compare_laps(tel[pair[0]], tel[pair[1]])
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.65, 0.35],
                                subplot_titles=("Speed (km/h)", f"Time delta: {pair[1]} vs {pair[0]} (s, + = {pair[1]} behind)"))
            fig.add_trace(go.Scatter(x=cmp["Distance"], y=cmp["SpeedA"], name=pair[0]), row=1, col=1)
            fig.add_trace(go.Scatter(x=cmp["Distance"], y=cmp["SpeedB"], name=pair[1]), row=1, col=1)
            fig.add_trace(go.Scatter(x=cmp["Distance"], y=cmp["Delta"], name="delta", showlegend=False), row=2, col=1)
            fig.update_xaxes(title_text="Distance (m)", row=2, col=1)
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("No fastest-lap telemetry for one of those drivers.")
