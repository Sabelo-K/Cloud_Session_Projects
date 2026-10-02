"""Streamlit UI. Run: python -m streamlit run f1/app.py"""
from datetime import date

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from f1 import data, pace, standings, style, telemetry

st.set_page_config(page_title="F1 analysis", page_icon="🏁", layout="wide", initial_sidebar_state="collapsed")

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1200px;}
    h1 {font-size: 1.7rem !important; padding-bottom: 0;}
    div[data-testid="stMetric"] {background: #171A22; border: 1px solid #262A35; border-left: 3px solid #E10600;
        border-radius: 8px; padding: 10px 14px;}
    div[data-testid="stMetricValue"] {font-size: 1.5rem;}
    button[data-baseweb="tab"] {padding: 6px 10px;}
    @media (max-width: 640px) {
      .block-container {padding-left: 0.7rem; padding-right: 0.7rem;}
      h1 {font-size: 1.35rem !important;}
    }
    </style>
    """,
    unsafe_allow_html=True,
)


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


def fmt_lap(seconds: float) -> str:
    m, s = divmod(seconds, 60)
    return f"{int(m)}:{s:06.3f}"


def show(fig, height: int = 380):
    st.plotly_chart(style.style_fig(fig, height), width="stretch", config=style.PLOT_CONFIG)


st.title("🏁 F1 race analysis")

# Filters sit at the top (not in a sidebar) so they are reachable on a phone.
c_year, c_race = st.columns([1, 3])
year = int(c_year.selectbox("Season", list(range(date.today().year, 2017, -1))))
sched = schedule_for(year)
done = sched[sched["date"] <= str(date.today())]
race = int(c_race.selectbox("Race", sched["round"], index=max(len(done) - 1, 0),
                            format_func=lambda r: f'R{r} · {sched.set_index("round").loc[r, "name"]}'))

try:
    laps = laps_for(year, race, "R")
except Exception as exc:  # FastF1 raises for races with no data yet
    st.error(f"No lap data for this race yet ({type(exc).__name__}). Try an earlier race.")
    st.stop()
all_drivers = sorted(laps["Driver"].unique())
colours, dashes = style.driver_styles(laps)
drivers = st.multiselect("Drivers", all_drivers, default=all_drivers[:4], placeholder="Pick drivers to compare")
sel = laps[laps["Driver"].isin(drivers)]
NEED_DRIVERS = "Pick at least one driver above."

t_over, t_pace, t_tyres, t_champ, t_quali = st.tabs(["Overview", "Pace", "Tyres", "Championship", "Qualifying"])

with t_over:
    race_pace = pace.race_pace(laps)
    best = telemetry.best_lap_times(laps)
    gaps = pace.teammate_gaps(laps)
    m1, m2, m3 = st.columns(3)
    if not best.empty:
        m1.metric(f'Fastest lap · {best["Driver"].iloc[0]}', fmt_lap(best["LapSeconds"].iloc[0]))
    if not race_pace.empty:
        m2.metric(f'Best race pace · {race_pace["Driver"].iloc[0]}', fmt_lap(race_pace["median"].iloc[0]))
    if not gaps.empty:
        top = gaps.iloc[-1]
        m3.metric(f'Biggest teammate gap · {top["Faster"]} v {top["Slower"]}', f'{top["gap"]:.2f}s')
    if not race_pace.empty:
        fig = px.bar(race_pace, x="Driver", y="gap_to_best", color="Driver", color_discrete_map=colours,
                     labels={"gap_to_best": "Gap (s)"}, title="Race pace: gap to fastest median clean lap (s)")
        fig.update_layout(showlegend=False)
        show(fig)
    if not gaps.empty:
        st.subheader("Teammate battles")
        gaps_plot = gaps.assign(Pair=gaps["Faster"] + " vs " + gaps["Slower"])
        fig = px.bar(gaps_plot, x="gap", y="Pair", orientation="h", color="Team",
                     color_discrete_map={t: style.team_color(t, i) for i, t in enumerate(gaps["Team"])},
                     labels={"gap": "Gap (s)", "Pair": ""}, title="Median clean-lap gap between teammates (s)")
        fig.update_layout(showlegend=False, yaxis=dict(autorange="reversed"))
        show(fig, height=max(260, 34 * len(gaps) + 90))

with t_pace:
    if not drivers:
        st.info(NEED_DRIVERS)
    else:
        show_all = st.toggle("Show pit, safety car and slow laps", value=False)
        d = pace.lap_chart_frame(sel, show_all=show_all)
        fig = px.line(d, x="LapNumber", y="LapSeconds", color="Driver", line_dash="Driver",
                      color_discrete_map=colours, line_dash_map=dashes, labels={"LapSeconds": "Lap time (s)", "LapNumber": "Lap"}, title="Lap times")
        show(fig, 420)
        st.dataframe(race_pace[race_pace["Driver"].isin(drivers)].round(3), width="stretch", hide_index=True)

with t_tyres:
    s = pace.stint_summary(sel)
    if s.empty:
        st.info(NEED_DRIVERS)
    else:
        s["Laps"] = s["EndLap"] - s["StartLap"] + 1
        fig = px.bar(s, x="Laps", base="StartLap", y="Driver", color="Compound", orientation="h",
                     color_discrete_map=style.COMPOUND_COLORS, labels={"Laps": "Lap number"},
                     title="Tyre stints")
        fig.update_traces(marker_line_color="#0B0D12", marker_line_width=2)
        show(fig, height=max(240, 60 * s["Driver"].nunique() + 120))
        with st.expander("Stint table"):
            st.dataframe(s.round(3), width="stretch", hide_index=True)
    st.subheader("Tyre degradation")
    st.caption("Slope of fuel-corrected clean lap time against tyre age, all drivers pooled "
               "(assumes about 0.03 s/lap fuel effect). Positive means losing pace.")
    if "TyreLife" in laps.columns:
        deg = pace.compound_degradation(laps)
        if not deg.empty:
            fig = px.bar(deg, x="Compound", y="deg_per_lap", color="Compound",
                         color_discrete_map=style.COMPOUND_COLORS, title="Degradation (s per lap of tyre age)")
            fig.update_layout(showlegend=False)
            show(fig, 300)
            st.dataframe(deg.round(4), width="stretch", hide_index=True)
    else:
        st.info("This session has no tyre age data.")

with t_champ:
    rounds = tuple(int(r) for r in sched[sched["date"] <= str(pd.Timestamp.today().date())]["round"])
    if not rounds:
        st.info("No completed rounds yet this season.")
    else:
        prog = standings_for(year, rounds)
        top = prog[prog["Round"] == prog["Round"].max()].nlargest(10, "Points")["Driver"]
        fig = px.line(prog[prog["Driver"].isin(top)], x="Round", y="Points", color="Driver", markers=True,
                      color_discrete_map=colours, title="Championship points after each round (top 10)")
        show(fig, 440)

with t_quali:
    kind = st.radio("Session", ["Q", "R"], format_func=lambda k: {"Q": "Qualifying", "R": "Race"}[k], horizontal=True)
    ql = laps_for(year, race, kind)
    best = telemetry.best_lap_times(ql)
    q_colours, q_dashes = style.driver_styles(ql)
    if not best.empty:
        fig = px.bar(best, x="Driver", y="gap_to_pole", color="Driver", color_discrete_map=q_colours,
                     labels={"gap_to_pole": "Gap (s)"}, title="Fastest lap: gap to the quickest (s)")
        fig.update_layout(showlegend=False)
        show(fig)
    with st.expander("Fastest lap table"):
        st.dataframe(best.round(3), width="stretch", hide_index=True)
    pair = st.multiselect("Compare two drivers' fastest laps", list(best["Driver"]), default=list(best["Driver"][:2]),
                          max_selections=2)
    if len(pair) == 2:
        tel = telemetry_for(year, race, kind, tuple(pair))
        if all(d in tel for d in pair):
            cmp = telemetry.compare_laps(tel[pair[0]], tel[pair[1]])
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.65, 0.35], vertical_spacing=0.08,
                                subplot_titles=("Speed (km/h)", f"Time delta: {pair[1]} vs {pair[0]} (s, + = {pair[1]} behind)"))
            for col, drv in (("SpeedA", pair[0]), ("SpeedB", pair[1])):
                fig.add_trace(go.Scatter(x=cmp["Distance"], y=cmp[col], name=drv,
                                         line=dict(color=q_colours.get(drv), dash=q_dashes.get(drv, "solid"))), row=1, col=1)
            fig.add_trace(go.Scatter(x=cmp["Distance"], y=cmp["Delta"], name="delta", showlegend=False,
                                     line=dict(color="#E10600")), row=2, col=1)
            fig.update_xaxes(title_text="Distance (m)", row=2, col=1)
            show(fig, 560)
        else:
            st.info("No fastest-lap telemetry for one of those drivers.")
