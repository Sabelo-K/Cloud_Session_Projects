"""Season Pace Comparison: race pace deficit round by round."""
from datetime import date

import plotly.express as px
import streamlit as st

from f1 import data, pace, style, ui


@st.cache_data(show_spinner="Loading races...")
def _deficits(year: int, rounds: tuple):
    frames = {}
    for r in rounds:
        try:
            frames[r] = ui._laps(year, r, "R")
        except Exception:
            pass  # sprint-only or cancelled rounds, or data not published yet
    return pace.season_deficit(frames)


def render():
    ui.title("Season Pace Comparison", "Race pace deficit to the fastest car, round by round. Loads every completed race, so it takes a while the first time.")
    year = ui._remembered("Season", list(range(date.today().year, 2017, -1)), "season_pace", "year", date.today().year)
    sched = ui.schedule_for(year)
    rounds = [int(r) for r in sched[sched["date"] <= str(date.today())]["round"]]
    if not rounds:
        st.info("No completed rounds yet this season.")
        return

    if not data.offline() and not st.session_state.get(f"season_pace_{year}"):  # saved data loads in seconds; live data does not
        if not st.button(f"Load {len(rounds)} races", type="primary"):
            return
        st.session_state[f"season_pace_{year}"] = True
    out = _deficits(year, tuple(rounds))
    if out.empty:
        st.warning("No race data could be loaded.")
        return
    names = sched.set_index("round")["name"]
    out = out.assign(Event=out["Round"].map(lambda r: f"R{r} {names.loc[r].replace(' Grand Prix', '')}"))
    unit = st.radio("Deficit as", ["Percent of the fastest median lap", "Seconds"], horizontal=True)
    col = "deficit_pct" if unit.startswith("Percent") else "deficit_s"
    by = st.radio("Group by", ["Driver", "Team"], horizontal=True)
    if by == "Team":
        out = out.dropna(subset=["Team"]).groupby(["Round", "Event", "Team"], as_index=False)[col].mean().rename(columns={"Team": "Name"})
        colours = {t: style.team_color(t, i) for i, t in enumerate(out["Name"].unique())}
    else:
        out = out.rename(columns={"Driver": "Name"})
        colours, _ = style.driver_styles(ui._laps(year, int(out["Round"].max()), "R"))
    names_all = sorted(out["Name"].unique())
    mean_rank = out.groupby("Name")[col].mean().sort_values().index.tolist()
    pick = st.multiselect(by + "s", names_all, default=mean_rank[:6])
    sel = out[out["Name"].isin(pick)]
    with ui.card("Pace deficit by round", "Lower is faster. Percent lets short and long circuits be compared. Pace is the median clean lap."):
        fig = px.line(sel, x="Event", y=col, color="Name", markers=True, color_discrete_map=colours,
                      labels={col: "Deficit (%)" if col == "deficit_pct" else "Deficit (s)", "Event": ""})
        fig.update_xaxes(tickangle=-45)
        fig.update_layout(legend=dict(orientation="h", y=1.04, yanchor="bottom", x=0))  # clear of the tilted round names
        ui.show(fig, 460)
    with ui.card("Heatmap", "Same data as a grid, for every driver or team."):
        grid = out.pivot(index="Name", columns="Event", values=col).reindex(mean_rank)
        fig = px.imshow(grid, aspect="auto", color_continuous_scale=["#00D5CF", "#14181E", "#E8002D"], labels=dict(color="Deficit"))
        fig.update_xaxes(tickangle=-45)
        ui.show(fig, max(320, 22 * len(grid) + 140))
