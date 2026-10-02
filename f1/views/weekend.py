"""Race Weekend Summary: qualifying, race result, places gained, tyre strategy and top speeds on one page."""
import plotly.express as px
import streamlit as st

from f1 import charts, data, style, summary, tyres, ui


def _lap(seconds) -> str:
    return "" if seconds != seconds else ui.fmt_lap(seconds)


def render():
    ui.title("Race Weekend Summary", "Qualifying, the race, places gained, tyre strategy and top speeds for one event.")
    year, rnd, event = ui.event_controls("weekend")
    quali_laps = ui.optional_laps(year, rnd, "Q")
    race_laps = ui.optional_laps(year, rnd, "R")
    if quali_laps is None and race_laps is None:
        st.warning("Neither qualifying nor the race is available for this event yet." + (
            f"\n\nOn your computer run: `python -m f1.sync --year {year} --rounds {rnd} --push`" if data.offline() else ""))
        return

    quali = summary.quali_order(quali_laps) if quali_laps is not None else None
    race = summary.race_classification(race_laps) if race_laps is not None else None
    colours = style.driver_styles(race_laps if race_laps is not None else quali_laps)[0]

    m = st.columns(4)
    if quali is not None and not quali.empty:
        m[0].metric(f'Pole · {quali["Driver"].iloc[0]}', ui.fmt_lap(quali["Best"].iloc[0]))
    if race is not None and not race.empty:
        m[1].metric(f'Winner · {race["Laps"].iloc[0]} laps', race["Driver"].iloc[0])
        fast = summary.fastest_lap(race)
        if fast:
            m[2].metric(f"Fastest race lap · {fast[0]}", ui.fmt_lap(fast[1]))
    speeds = summary.top_speeds(race_laps if race_laps is not None else quali_laps)
    if not speeds.empty:
        m[3].metric(f'Top speed · {speeds["Driver"].iloc[0]}', f'{speeds["TopSpeed"].iloc[0]:.0f} km/h')

    if race is not None and not race.empty:
        with ui.card("Race result", "Finishing order from the lap data: most laps first, then who crossed the line first. "
                                    "Strategy letters are the tyres in stint order (S soft, M medium, H hard, I intermediate, W wet, ? unknown)."):
            table = race.assign(Fastest=race["Fastest"].map(_lap), Median=race["Median"].map(_lap))
            st.dataframe(table, width="stretch", hide_index=True, height=38 + 35 * len(table))
    if quali is not None and not quali.empty:
        with ui.card("Qualifying", "Best valid lap per driver, the tyre it was set on and the gap to pole. Top speed is the highest speed-trap reading in the session."):
            table = quali.assign(Best=quali["Best"].map(_lap), Gap=quali["Gap"].map(lambda g: "" if g == 0 else f"+{g:.3f}"),
                                 Tyre=quali["Tyre"].map(tyres.name))
            st.dataframe(table, width="stretch", hide_index=True, height=38 + 35 * len(table))
    if quali is not None and race is not None and not quali.empty and not race.empty:
        moves = summary.places_gained(quali, race)
        if not moves.empty:
            with ui.card("Places gained", "Race finish against qualifying position. Positive means they finished ahead of where they qualified."):
                fig = px.bar(moves, x="Driver", y="Gained", color="Driver", color_discrete_map=colours,
                             labels={"Gained": "Places gained"}, hover_data=["Qualified", "Finished"])
                fig.update_layout(showlegend=False)
                ui.show(fig, 340)
    if race_laps is not None:
        with ui.card("Tyre strategy", "Finishing order, one block per stint."):
            ui.tyre_legend(race_laps)
            order = list(race["Driver"])
            ui.show(charts.stint_timeline(race_laps, order), max(300, 32 * len(order) + 110))
    if not speeds.empty:
        with ui.card("Top speeds", "Highest speed-trap reading per driver (race, or qualifying when there is no race)."):
            fig = px.bar(speeds, x="Driver", y="TopSpeed", color="Driver", color_discrete_map=colours, labels={"TopSpeed": "km/h"})
            fig.update_layout(showlegend=False)
            fig.update_yaxes(range=[speeds["TopSpeed"].min() - 10, speeds["TopSpeed"].max() + 4])
            ui.show(fig, 320)
