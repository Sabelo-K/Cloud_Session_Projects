"""Sectors & Maps: sector rankings, theoretical best lap and circuit map."""
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from f1 import charts, data, pace, sectors, style, ui


@st.cache_data(show_spinner="Loading telemetry for the fastest lap (slow the first time)...")
def _fastest_tel(year, rnd, kind, driver):
    return data.load_lap_telemetry(year, rnd, kind, ((driver, None),))


def render():
    ui.title("Sectors & Maps", "Where each driver gains and loses, and the lap that could have been.")
    year, rnd, event, kind = ui.session_controls("sectors", list(data.SESSION_NAMES), "Q")
    laps = ui.load_laps(year, rnd, kind)
    colours, _ = style.driver_styles(laps)
    drivers = ui.driver_picker("sectors", sorted(laps["Driver"].unique()), colours, default_n=20)
    if not drivers:
        st.info("Pick at least one driver above.")
        return
    best = sectors.best_sectors(laps[laps["Driver"].isin(drivers)])
    best = best.dropna(subset=["Theoretical"])
    if best.empty:
        st.info("No sector times for this session.")
        return
    ult = sectors.ultimate_lap(best)

    top = st.columns(4)
    top[0].metric("Theoretical best lap", ui.fmt_lap(ult["total"]) if ult["total"] else "n/a")
    for i, n in enumerate(sectors.NAMES, start=1):
        top[i].metric(f'Best {n} · {ult["owners"].get(n, "")}', f'{ult["times"].get(n, float("nan")):.3f}s')
    st.caption("The theoretical lap adds the best sector from any selected driver, so it mixes drivers and may not be achievable in one lap.")

    left, right = st.columns(2)
    with left, ui.card("Gap to theoretical best", "Each driver's best sectors against the best sector overall, summed. Ranked by total deficit."):
        d = sectors.sector_deficits(best)
        long = d.melt(id_vars=["Driver", "Total"], value_vars=sectors.NAMES, var_name="Sector", value_name="Deficit")
        fig = px.bar(long, y="Driver", x="Deficit", color="Sector", orientation="h", labels={"Deficit": "Deficit (s)"},
                     color_discrete_sequence=["#E8002D", "#FFD60A", "#00D5CF"])
        fig.update_layout(yaxis=dict(categoryorder="array", categoryarray=list(d["Driver"])[::-1]))
        ui.show(fig, max(320, 26 * len(d) + 100))
    with right, ui.card("Lap map", "A driver's quickest lap drawn on the circuit: by timing sector, by speed (blue slow, red fast) or by gear."):
        fastest = best.sort_values("BestLap").iloc[0]["Driver"]
        c1, c2 = st.columns(2)
        pick = c1.selectbox("Driver", sorted(best["Driver"]), index=sorted(best["Driver"]).index(fastest), key="map_driver")
        view = c2.segmented_control("Colour by", ["Sector", "Speed", "Gear"], default="Speed", key="map_view") or "Speed"
        if st.toggle("Show circuit map (loads telemetry, slower)", value=False):
            got = _fastest_tel(year, rnd, kind, pick)
            if not got:
                st.info(f"No telemetry saved for {pick}'s fastest lap.")
            else:
                label, frame = next(iter(got.items()))
                row = laps[(laps["Driver"] == pick) & (laps["LapNumber"] == int(label.split("|")[1]))].iloc[0]
                if view == "Sector":
                    s1 = row["Sector1Time"].total_seconds()
                    s2 = row["Sector2Time"].total_seconds()
                    ui.show(charts.sector_map(frame, sectors.sector_regions(frame, s1, s2)), 430)
                else:
                    ui.show(charts.speed_map(frame, "nGear" if view == "Gear" else "Speed", data.load_corners(year, rnd, kind)), 430)
                st.caption(f"{pick}'s fastest lap ({ui.fmt_lap(row['LapTime'].total_seconds())}).")
        else:
            st.caption("Switch the toggle on to draw the circuit.")

    st.subheader("Sector rankings")
    sec = sectors.sector_seconds(laps[laps["Driver"].isin(drivers)])
    team = laps.dropna(subset=["Team"]).groupby("Driver")["Team"].first() if "Team" in laps else {}
    cols = st.columns(3)
    for col, n in zip(cols, sectors.NAMES):
        with col, ui.card(f"{n} ranking", "Each driver's best sector time."):
            r = sec.groupby("Driver")[n].min().dropna().sort_values().reset_index()
            r["Team"] = r["Driver"].map(team)
            fig = px.bar(r, x="Driver", y=n, color="Driver", color_discrete_map=colours, hover_data={"Team": True},
                         labels={n: "Time (s)"})
            fig.update_layout(showlegend=False)
            fig.update_yaxes(range=[r[n].min() - 0.4, r[n].max() + 0.1])
            ui.show(fig, 300)
