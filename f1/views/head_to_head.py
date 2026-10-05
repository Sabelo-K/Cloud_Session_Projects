"""Driver Head-to-Head: two drivers across a season, weekend by weekend."""
from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from f1 import data, headtohead, store, style, ui
from f1.views import championship


@st.cache_data(show_spinner="Loading the season...")
def _season(year: int, rounds: tuple):
    quali, race, team_of = {}, {}, {}
    for r in rounds:
        q, rc = ui.optional_laps(year, r, "Q"), ui.optional_laps(year, r, "R")
        for laps, into in ((q, quali), (rc, race)):
            if laps is None:
                continue
            into[r] = laps
            for drv, team in laps.dropna(subset=["Team"]).groupby("Driver")["Team"].last().items():
                team_of[drv] = team
    return quali, race, team_of


def _colours(a: str, b: str, team_of: dict) -> tuple[str, str]:
    ca, cb = style.team_color(team_of.get(a)), style.team_color(team_of.get(b), 1)
    return ca, (style.lighten(cb) if ca == cb else cb)  # team-mates share a colour, so B is drawn lighter


def _tile(col, title: str, a: str, b: str, score: dict, detail: str) -> None:
    col.markdown(f'<p class="card-title">{title}</p>', unsafe_allow_html=True)
    col.markdown(f'<p style="font-size:2rem;font-weight:700;margin:0">{a} {score["a"]} – {score["b"]} {b}</p>', unsafe_allow_html=True)
    col.caption(f'{detail} · {score["rounds"]} weekends')


def render():
    ui.title("Driver Head-to-Head", "Two drivers, one season: who was quicker in qualifying, who finished ahead, and who had the better race pace.")
    year = ui._remembered("Season", list(range(date.today().year, 2017, -1)), "h2h", "year", date.today().year)
    sched = ui.schedule_for(year)
    names = {int(r): f"R{r} {n.replace(' Grand Prix', '')}" for r, n in zip(sched["round"], sched["name"])}
    done = [int(r) for r in sched[sched["date"] <= str(date.today())]["round"]]
    rounds = [r for r in done if r in set(store.saved_rounds(year))] if data.offline() else done
    if not rounds:
        st.info("No saved rounds for this season yet.")
        return
    if not ui.confirm_load(f"h2h_{year}", year, rounds):
        return
    quali, race, team_of = _season(year, tuple(rounds))
    drivers = sorted(team_of)
    if len(drivers) < 2:
        st.warning("Not enough qualifying or race data could be loaded.")
        return

    c1, c2 = st.columns(2)
    a = c1.selectbox("Driver A", drivers, index=0, key="h2h_a")
    b = c2.selectbox("Driver B", [d for d in drivers if d != a], index=0, key="h2h_b")
    ca, cb = _colours(a, b, team_of)
    rows = headtohead.weekend_rows(quali, race, a, b)
    if rows[["QualiA", "QualiB", "FinishA", "FinishB", "PaceA", "PaceB"]].dropna(how="all").empty:
        st.info(f"{a} and {b} have no sessions in this season's saved data.")
        return
    board = headtohead.scoreboard(rows)
    rows = rows.assign(Event=rows["Round"].map(lambda r: names.get(int(r), f"R{int(r)}")))

    with ui.card("Scoreboard", "Weekends won by each driver. Qualifying is the best lap, race result the finishing order, race pace the median clean lap."):
        t1, t2, t3 = st.columns(3)
        gap = board["quali"]["avg_gap"]
        _tile(t1, "Qualifying", a, b, board["quali"], f"{a if gap >= 0 else b} ahead by {abs(gap):.3f}s on average" if gap == gap else "no common sessions")
        places = board["finish"]["avg_places"]
        _tile(t2, "Race result", a, b, board["finish"], f"{a if places >= 0 else b} ahead by {abs(places):.1f} places on average" if places == places else "no common races")
        pct = board["pace"]["avg_gap_pct"]
        _tile(t3, "Race pace", a, b, board["pace"], f"{a if pct >= 0 else b} quicker by {abs(pct):.2f}% on average" if pct == pct else "no common races")

    def bars(col, title, unit):
        d = rows.dropna(subset=[col])
        if d.empty:
            st.info("No weekends with both drivers.")
            return
        fig = go.Figure(go.Bar(x=d["Event"], y=d[col], marker_color=[ca if v >= 0 else cb for v in d[col]],
                               hovertemplate="%{x}<br>%{customdata}<extra></extra>",
                               customdata=[f"{a if v >= 0 else b} quicker by {abs(v):.3f}{unit}" for v in d[col]]))
        fig.update_layout(yaxis_title=f"{title} (above zero = {a} quicker, below = {b} quicker)", showlegend=False)
        fig.update_xaxes(tickangle=-45)
        ui.show(fig, 380)

    with ui.card("Championship points", "Points after each completed round, from the official standings (sprints included)."):
        try:
            pts = headtohead.points_rows(championship._standings(year, tuple(done)), a, b)
        except Exception as exc:  # Jolpica is a separate service and rate limited
            pts = None
            st.info(f"Championship points could not be loaded right now ({type(exc).__name__}). Try again in a minute.")
        if pts is not None and not pts.empty:
            last = pts.iloc[-1]
            lead = a if last["PointsGap"] >= 0 else b
            st.markdown(f'<p style="font-size:2rem;font-weight:700;margin:0">{a} {last["PointsA"]:g} – {last["PointsB"]:g} {b}</p>', unsafe_allow_html=True)
            st.caption("Level on points." if last["PointsGap"] == 0 else f'{lead} leads by {abs(last["PointsGap"]):g} points after round {int(last["Round"])}.')
            pts = pts.assign(Event=pts["Round"].map(lambda r: names.get(int(r), f"R{int(r)}")))
            fig = go.Figure()
            for drv, colour, col in ((a, ca, "PointsA"), (b, cb, "PointsB")):
                fig.add_trace(go.Scatter(x=pts["Event"], y=pts[col], mode="lines+markers", name=drv, line=dict(color=colour, width=2)))
            fig.update_layout(yaxis_title="Championship points", hovermode="x unified")
            fig.update_xaxes(tickangle=-45)
            ui.show(fig, 380)
            gap_fig = go.Figure(go.Bar(x=pts["Event"], y=pts["PointsGap"], marker_color=[ca if v >= 0 else cb for v in pts["PointsGap"]],
                                       hovertemplate="%{x}<br>%{customdata}<extra></extra>",
                                       customdata=[f"{a if v >= 0 else b} ahead by {abs(v):g}" for v in pts["PointsGap"]]))
            gap_fig.update_layout(yaxis_title=f"Points gap (above zero = {a} ahead, below = {b} ahead)", showlegend=False)
            gap_fig.update_xaxes(tickangle=-45)
            ui.show(gap_fig, 300)

    with ui.card("Qualifying gap", f"Best lap difference by weekend. Bars above zero are {a}, below zero are {b}."):
        bars("QualiGap", "Gap (s)", "s")
    with ui.card("Race pace gap", f"Median clean-lap difference by weekend, in seconds."):
        bars("PaceGap", "Gap (s)", "s")
    with ui.card("Qualifying and race positions", "Lower is better. Solid line is the finishing position, dotted line the grid position (qualifying rank)."):
        fig = go.Figure()
        for drv, colour, grid, fin in ((a, ca, "GridA", "FinishA"), (b, cb, "GridB", "FinishB")):
            fig.add_trace(go.Scatter(x=rows["Event"], y=rows[fin], mode="lines+markers", name=f"{drv} finish", line=dict(color=colour, width=2)))
            fig.add_trace(go.Scatter(x=rows["Event"], y=rows[grid], mode="lines+markers", name=f"{drv} grid", line=dict(color=colour, width=1.5, dash="dot")))
        fig.update_yaxes(autorange="reversed", title="Position")
        fig.update_xaxes(tickangle=-45)
        ui.show(fig, 420)
    with ui.card("Weekend by weekend"):
        shown = rows[["Event", "GridA", "GridB", "FinishA", "FinishB", "QualiGap", "PaceGap"]].rename(columns={
            "GridA": f"{a} grid", "GridB": f"{b} grid", "FinishA": f"{a} finish", "FinishB": f"{b} finish",
            "QualiGap": f"Quali gap (s, + = {a} quicker)", "PaceGap": f"Pace gap (s, + = {a} quicker)"})
        st.dataframe(shown.round(3), width="stretch", hide_index=True)
