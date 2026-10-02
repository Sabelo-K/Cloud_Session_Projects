"""Streamlit UI. Run: streamlit run f1/app.py"""
import plotly.express as px
import streamlit as st

from f1 import data, pace

st.set_page_config(page_title="F1 analysis", layout="wide")
st.title("F1 race analysis")

year = st.sidebar.number_input("Season", 2018, 2026, 2024)
sched = data.season_schedule(int(year))
race = st.sidebar.selectbox("Race", sched["round"], format_func=lambda r: sched.set_index("round").loc[r, "name"])


@st.cache_data(show_spinner="Loading laps (first load is slow)...")
def laps_for(y: int, r: int):
    return data.load_race_laps(y, r)


laps = laps_for(int(year), int(race))
drivers = st.sidebar.multiselect("Drivers", sorted(laps["Driver"].unique()), default=sorted(laps["Driver"].unique())[:4])
sel = laps[laps["Driver"].isin(drivers)]

t1, t2, t3 = st.tabs(["Lap times", "Race pace", "Tyre stints"])
with t1:
    d = pace.with_seconds(sel).dropna(subset=["LapSeconds"])
    st.plotly_chart(px.line(d, x="LapNumber", y="LapSeconds", color="Driver"), use_container_width=True)
with t2:
    p = pace.race_pace(laps)
    st.dataframe(p[p["Driver"].isin(drivers)], use_container_width=True)
    st.plotly_chart(px.bar(p, x="Driver", y="gap_to_best", title="Gap to best median clean lap (s)"), use_container_width=True)
with t3:
    s = pace.stint_summary(sel)
    s["Laps"] = s["EndLap"] - s["StartLap"] + 1
    fig = px.bar(s, x="Laps", base="StartLap", y="Driver", color="Compound", orientation="h",
                 labels={"Laps": "Lap number"})
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(s, use_container_width=True)
