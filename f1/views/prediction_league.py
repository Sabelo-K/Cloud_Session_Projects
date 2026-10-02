"""Prediction League: pick pole, the podium and the fastest lap before a race, then score against the result."""
import pandas as pd
import plotly.express as px
import streamlit as st

from f1 import data, league, store, style, ui


def _results(year: int, rounds: list[int]) -> dict:
    out = {}
    for r in rounds:
        res = league.result_from_laps(ui.optional_laps(year, r, "Q"), ui.optional_laps(year, r, "R"))
        if res:
            out[r] = res
    return out


def _drivers(year: int, rnd: int) -> list[str]:
    """Drivers to choose from: the event's own sessions if saved, else the newest saved race of the season."""
    for r, kind in [(rnd, k) for k in ("R", "Q", "FP3", "FP2", "FP1")] + [(r, "R") for r in sorted(store.saved_rounds(year), reverse=True)]:
        laps = ui.optional_laps(year, r, kind)
        if laps is not None:
            return sorted(laps["Driver"].dropna().unique())
    return []


def _picks_form(year: int, rnd: int, event: str, lg: dict) -> None:
    drivers = _drivers(year, rnd)
    if not drivers:
        st.info("No saved race yet to take the driver list from. Save a race with `python -m f1.sync` first.")
        return
    with ui.card("Make your picks", f"For {event}. Points: {league.POINTS['exact']} for each driver in the right podium place, "
                                    f"{league.POINTS['on_podium']} if on the podium in another place, {league.POINTS['pole']} for pole, "
                                    f"{league.POINTS['fastest']} for the fastest lap (best possible {league.MAX_POINTS})."):
        with st.form(f"picks_{year}_{rnd}"):
            known = lg["players"]
            c1, c2 = st.columns(2)
            chosen = c1.selectbox("Player", known + ["+ New player"]) if known else "+ New player"
            new = c2.text_input("New player name", disabled=bool(known) and chosen != "+ New player")
            player = new if chosen == "+ New player" else chosen
            c1, c2, c3 = st.columns(3)
            p1 = c1.selectbox("Winner (P1)", drivers, index=None, placeholder="Pick a driver")
            p2 = c2.selectbox("Second (P2)", drivers, index=None, placeholder="Pick a driver")
            p3 = c3.selectbox("Third (P3)", drivers, index=None, placeholder="Pick a driver")
            c1, c2 = st.columns(2)
            pole = c1.selectbox("Pole sitter", drivers, index=None, placeholder="Pick a driver")
            fastest = c2.selectbox("Fastest lap", drivers, index=None, placeholder="Pick a driver")
            if st.form_submit_button("Save picks", type="primary"):
                try:
                    updated = league.add_prediction(lg, rnd, player, pole or "", [p1 or "", p2 or "", p3 or ""], fastest or "")
                except ValueError as exc:
                    st.error(str(exc))
                else:
                    league.save(year, updated)
                    st.success(f"Saved {player}'s picks. To show them on the hosted app run `python -m f1.league --push` on your computer.")
                    st.rerun()


def render():
    ui.title("Prediction League", "Pick pole, the podium and the fastest lap, then see who scores best once the race is saved.")
    year, rnd, event = ui.event_controls("league")
    lg = league.load(year)
    sched = ui.schedule_for(year)
    rounds = [int(r) for r in sched["round"]]
    results = _results(year, sorted(set(int(r) for r in lg["rounds"]) | {rnd}))

    if rnd in results:
        st.info(f"{event} is finished, so picks for it are locked.")
    elif data.offline():
        st.info("Picks are entered on your own computer (`python -m streamlit run f1/app.py`), then published with "
                "`python -m f1.league --push`. This hosted copy shows the saved picks and the leaderboard.")
    else:
        _picks_form(year, rnd, event, lg)

    board = league.leaderboard(lg, results)
    with ui.card("Leaderboard", "Season points from every round that has both picks and a saved result."):
        if board.empty or board["Rounds"].sum() == 0:
            st.info("No scored rounds yet. Picks are scored once the race has been saved.")
        else:
            st.dataframe(board, width="stretch", hide_index=True)
            pts = board.melt(id_vars=["Player", "Points", "Rounds"], var_name="Round", value_name="Pts").dropna(subset=["Pts"])
            pts["Cumulative"] = pts.sort_values("Round", key=lambda s: s.str[1:].astype(int)).groupby("Player")["Pts"].cumsum()
            fig = px.line(pts.sort_values("Round", key=lambda s: s.str[1:].astype(int)), x="Round", y="Cumulative", color="Player",
                          markers=True, labels={"Cumulative": "Points"}, color_discrete_sequence=style.FALLBACK)
            ui.show(fig, 340)

    picks = lg["rounds"].get(str(rnd), {})
    with ui.card(f"Picks for {event}", "Each player's choices and, once the race is saved, the points they earned."):
        if not picks:
            st.info("Nobody has made picks for this event.")
        else:
            res = results.get(rnd)
            rows = []
            for player, p in picks.items():
                row = {"Player": player, "Pole": p["pole"], "P1": p["podium"][0], "P2": p["podium"][1], "P3": p["podium"][2],
                       "Fastest lap": p["fastest"]}
                if res:
                    row["Points"] = league.score(p, res)["total"]
                rows.append(row)
            st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
            if res:
                st.caption(f'Result: pole {res["pole"]}, podium {" · ".join(res["podium"])}, fastest lap {res["fastest"]}.')
