"""Car Performance: how each team's car compares over the season in qualifying, race pace and straight-line speed."""
from datetime import date

import plotly.express as px
import streamlit as st

from f1 import cars, data, store, style, ui


@st.cache_data(show_spinner="Loading the season...")
def _season(year: int, rounds: tuple):
    quali, race = {}, {}
    for r in rounds:
        q, rc = ui.optional_laps(year, r, "Q"), ui.optional_laps(year, r, "R")
        if q is not None:
            quali[r] = q
        if rc is not None:
            race[r] = rc
    return cars.team_rounds(quali, race)


def _lines(df, col, label, colours, names):
    df = df.dropna(subset=[col]).assign(Event=df["Round"].map(names))
    fig = px.line(df, x="Event", y=col, color="Team", markers=True, color_discrete_map=colours, labels={col: label, "Event": ""})
    fig.update_xaxes(tickangle=-45)
    fig.update_layout(legend=dict(orientation="h", y=1.04, yanchor="bottom", x=0))  # keeps it clear of the tilted round names
    return fig


def render():
    ui.title("Car Performance", "How each team's car stacks up: one-lap pace, race pace and straight-line speed, round by round.")
    year = ui._remembered("Season", list(range(date.today().year, 2017, -1)), "cars", "year", date.today().year)
    sched = ui.schedule_for(year)
    names = {int(r): f"R{r} {n.replace(' Grand Prix', '')}" for r, n in zip(sched["round"], sched["name"])}
    done = [int(r) for r in sched[sched["date"] <= str(date.today())]["round"]]
    rounds = [r for r in done if r in set(store.saved_rounds(year))] if data.offline() else done
    if not rounds:
        st.info("No saved rounds for this season yet.")
        return
    if not data.offline() and f"cars_{year}" not in st.session_state:
        if not st.button(f"Load {len(rounds)} rounds", type="primary"):
            st.caption("Loading a whole season from F1 takes a while the first time.")
            return
        st.session_state[f"cars_{year}"] = True
    table = _season(year, tuple(rounds))
    if table.empty:
        st.warning("No qualifying or race data could be loaded.")
        return
    teams = sorted(table["Team"].unique())
    colours = {t: style.team_color(t, i) for i, t in enumerate(teams)}
    profile = cars.season_profile(table)
    pick = st.multiselect("Teams", teams, default=list(profile["Team"].head(6)))
    sel = table[table["Team"].isin(pick)]
    if sel.empty:
        st.info("Pick at least one team.")
        return

    with ui.card("Season profile", "Each dot is a team's season average. Left is faster in a straight line, lower is faster over one lap, "
                                   "bigger is slower in the race. Teams in the bottom-left have the quickest car."):
        prof = profile[profile["Team"].isin(pick)].dropna(subset=["TopSpeedGap", "QualiGapPct"])
        fig = px.scatter(prof, x="TopSpeedGap", y="QualiGapPct", size=prof["RacePaceGapPct"].fillna(0) + 0.6, color="Team",
                         color_discrete_map=colours, hover_data={"RacePaceGapPct": ":.2f", "Rounds": True},
                         labels={"TopSpeedGap": "Top speed below the fastest team (km/h)", "QualiGapPct": "Qualifying gap to pole team (%)"})
        ui.show(fig, 420)
    with ui.card("Qualifying gap", "Each team's best lap against the pole team's, in percent. Lower is faster."):
        ui.show(_lines(sel, "QualiGapPct", "Gap (%)", colours, names), 400)
    with ui.card("Race pace gap", "Average median clean lap of a team's drivers against the fastest team, in percent."):
        ui.show(_lines(sel, "RacePaceGapPct", "Gap (%)", colours, names), 400)
    with ui.card("Top speed", "Best speed-trap reading by team in qualifying or the race."):
        ui.show(_lines(sel, "TopSpeed", "km/h", colours, names), 400)
    with st.expander("Season table"):
        st.dataframe(profile.round(2), width="stretch", hide_index=True)
