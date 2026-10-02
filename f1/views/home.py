"""Home: a quick read of one session, plus a guide to the modules."""
import plotly.express as px
import streamlit as st

from f1 import data, pace, style, telemetry, ui


def render():
    ui.title("🏁 F1 Insights", "Pick a season, event and session. Your choice follows you to every module in the sidebar.")
    year, rnd, event, kind = ui.session_controls("home", list(data.SESSION_NAMES), "R")
    laps = ui.load_laps(year, rnd, kind)
    colours, _ = style.driver_styles(laps)

    race_pace = pace.race_pace(laps)
    best = telemetry.best_lap_times(laps)
    gaps = pace.teammate_gaps(laps)
    m1, m2, m3 = st.columns(3)
    if not best.empty:
        m1.metric(f'Fastest lap · {best["Driver"].iloc[0]}', ui.fmt_lap(best["LapSeconds"].iloc[0]))
    if not race_pace.empty:
        m2.metric(f'Best median pace · {race_pace["Driver"].iloc[0]}', ui.fmt_lap(race_pace["median"].iloc[0]))
    if not gaps.empty:
        top = gaps.iloc[-1]
        m3.metric(f'Biggest teammate gap · {top["Faster"]} v {top["Slower"]}', f'{top["gap"]:.2f}s')

    if not race_pace.empty:
        with ui.card("Pace", "Gap to the fastest median clean lap (pit, non-green and slow laps excluded)."):
            fig = px.bar(race_pace, x="Driver", y="gap_to_best", color="Driver", color_discrete_map=colours,
                         labels={"gap_to_best": "Gap (s)"})
            fig.update_layout(showlegend=False)
            ui.show(fig)
    if not gaps.empty:
        with ui.card("Teammate battles", "Median clean-lap gap between a team's two drivers."):
            plot = gaps.assign(Pair=gaps["Faster"] + " vs " + gaps["Slower"])
            fig = px.bar(plot, x="gap", y="Pair", orientation="h", color="Team",
                         color_discrete_map={t: style.team_color(t, i) for i, t in enumerate(gaps["Team"])},
                         labels={"gap": "Gap (s)", "Pair": ""})
            fig.update_layout(showlegend=False, yaxis=dict(autorange="reversed"))
            ui.show(fig, height=max(260, 34 * len(gaps) + 90))

    with ui.card("Modules"):
        st.markdown(
            "- **Race Weekend Summary**: qualifying, race result, places gained, strategy and top speeds\n"
            "- **Race Pace Insights**: box plots, raw laps, gap to leader, consistency, traffic\n"
            "- **Telemetry Analyser**: overlay any drivers and laps on speed, throttle, brake, gear, RPM\n"
            "- **Single Lap Comparison**: track dominance map, corner speeds, speed trace, time delta\n"
            "- **Lap Replay**: watch fast laps being driven, with sector times, a green/red delta to a reference driver and numbered corners\n"
            "- **Practice Insights**: long runs, degradation, consistency, speed traps\n"
            "- **Sectors & Maps**: sector rankings, theoretical best lap, circuit map\n"
            "- **Strategy & Weather**: tyre stints, pit stops, session conditions\n"
            "- **Season Pace**: race pace deficit round by round\n"
            "- **Car Performance**: team qualifying gap, race pace and top speed over the season\n"
            "- **Prediction League**: pick pole, the podium and the fastest lap, then score against the result\n"
            "- **Championship**: points after each round"
        )
