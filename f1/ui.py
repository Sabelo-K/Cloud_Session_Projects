"""Shared UI pieces: theme CSS, chart cards, season/event/session controls that persist across pages,
the driver picker, and data-loading helpers with friendly errors."""
from __future__ import annotations

from datetime import date

import streamlit as st

from f1 import data, store, style, tyres

CSS = """
<style>
.block-container {padding-top: 1.2rem; padding-bottom: 2.5rem; max-width: 1280px;}
h1 {font-size: 1.6rem !important; padding-bottom: 0.2rem; letter-spacing: -0.01em;}
h2, h3 {letter-spacing: -0.01em;}
[data-testid="stSidebar"] {background: #14181E; border-right: 1px solid #29313A;}
[data-testid="stSidebarNav"] a[aria-current="page"] {background: rgba(0,213,207,0.14); border-left: 3px solid #00D5CF;}
div[data-testid="stVerticalBlockBorderWrapper"] {border-radius: 12px; background: #14181E;}
div[data-testid="stMetric"] {background: #14181E; border: 1px solid #29313A; border-left: 3px solid #00D5CF;
    border-radius: 10px; padding: 10px 14px;}
div[data-testid="stMetricValue"], .stDataFrame, .tnum {font-variant-numeric: tabular-nums;}
div[data-testid="stMetricValue"] {font-size: 1.5rem;}
.card-title {font-weight: 600; font-size: 1.02rem; margin: 0;}
.card-cap {color: #98A4B3; font-size: 0.85rem; margin: 0 0 0.35rem 0;}
.chip {display:inline-block; padding: 2px 10px; margin: 0 6px 6px 0; border-radius: 999px; font-size: 0.82rem;
    font-weight: 600; background:#1d232b; border: 1px solid #29313A;}
.chip i {display:inline-block; width:9px; height:9px; border-radius:50%; margin-right:6px;}
.tyre {display:inline-block; width:15px; height:15px; line-height:15px; text-align:center; border-radius:50%;
    font-size:.62rem; font-weight:800; margin-right:6px; vertical-align:middle;}
.badge {display:inline-block; padding: 1px 8px; border-radius: 6px; font-size: .78rem; font-weight:600;
    background:#1d232b; border:1px solid #29313A; margin-left: 6px;}
button[data-baseweb="tab"] {padding: 6px 10px;}
@media (max-width: 640px) {
  .block-container {padding-left: 0.7rem; padding-right: 0.7rem;}
  h1 {font-size: 1.3rem !important;}
  /* keep short control rows two-up on a phone instead of one tall stack */
  div[data-testid="stHorizontalBlock"] {flex-direction: row !important; flex-wrap: wrap; gap: 0.5rem;}
  div[data-testid="stColumn"] {flex: 1 1 calc(50% - 0.5rem) !important; min-width: calc(50% - 0.5rem) !important;}
}
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def title(text: str, caption: str | None = None) -> None:
    st.title(text)
    if caption:
        st.caption(caption)


class card:
    """Bordered chart card: title, short explanation, then whatever is drawn inside the `with` block."""

    def __init__(self, heading: str, caption: str | None = None):
        self.box = st.container(border=True)
        self.heading, self.caption = heading, caption

    def __enter__(self):
        self.box.__enter__()
        st.markdown(f'<p class="card-title">{self.heading}</p>', unsafe_allow_html=True)
        if self.caption:
            st.markdown(f'<p class="card-cap">{self.caption}</p>', unsafe_allow_html=True)
        return self

    def __exit__(self, *exc):
        return self.box.__exit__(*exc)


def show(fig, height: int = 380) -> None:
    st.plotly_chart(style.style_fig(fig, height), width="stretch", config=style.PLOT_CONFIG)


SAVED_ONLY_HINT = (" This hosted copy only has the laps saved with `python -m f1.sync`, by default each driver's fastest lap "
                   "(use `--telemetry all` to save every lap).")


def fmt_lap(seconds: float) -> str:
    m, s = divmod(float(seconds), 60)
    return f"{int(m)}:{s:06.3f}"


def _remembered(label, options, page, name, default, fmt=None, container=st):
    """Selectbox whose choice is remembered across pages (each page has its own widget key, seeded from memory)."""
    ss = st.session_state
    key = f"w_{page}_{name}"
    if key not in ss or ss[key] not in options:
        remembered = ss.get(f"mem_{name}", default)
        ss[key] = remembered if remembered in options else default
    value = container.selectbox(label, options, key=key, format_func=fmt or str)
    ss[f"mem_{name}"] = value
    return value


@st.cache_data(show_spinner=False)
def schedule_for(year: int):
    return data.season_schedule(year)


def session_controls(page: str, sessions: list[str], default_session: str):
    """Season / event / session row at the top of a page. Returns (year, round, event name, session code).
    Choices are kept when switching pages (the session falls back to `default_session` if unsupported here)."""
    c1, c2, c3 = st.columns([1, 3, 2])
    year = _remembered("Season", list(range(date.today().year, 2017, -1)), page, "year", date.today().year, container=c1)
    try:
        sched = schedule_for(year)
    except Exception as exc:
        st.error(f"Could not load the {year} calendar ({type(exc).__name__}). Check your connection and reload.")
        st.stop()
    done = sched[sched["date"] <= str(date.today())]
    latest = int(done["round"].iloc[-1]) if len(done) else int(sched["round"].iloc[0])
    saved = [r for r in store.saved_rounds(year) if r in set(sched["round"])]
    if data.offline() and saved:  # hosted app: open on the newest event that has saved data
        latest = saved[-1]
    names = sched.set_index("round")["name"]
    rnd = _remembered("Event", [int(r) for r in sched["round"]], page, "round", latest,
                      fmt=lambda r: f"R{r} · {names.loc[r]}", container=c2)
    kind = _remembered("Session", sessions, page, "session", default_session,
                       fmt=lambda k: data.SESSION_NAMES[k], container=c3)
    return int(year), int(rnd), str(names.loc[rnd]), kind


@st.cache_data(show_spinner="Loading laps (the first load of a session is slow)...")
def _laps(year: int, rnd: int, kind: str):
    return data.load_session_laps(year, rnd, kind)


def load_laps(year: int, rnd: int, kind: str):
    """Laps for a session, or a friendly message and a stop when the session has no data (yet)."""
    try:
        laps = _laps(year, rnd, kind)
    except store.NotSaved as exc:
        have = ", ".join(f"R{r}" for r in store.saved_rounds(year)) or "none yet"
        st.warning(f"{exc}\n\nEvents with saved data for {year}: {have}.")
        st.stop()
    except Exception as exc:
        st.error(f"No {data.SESSION_NAMES[kind].lower()} data for this event ({type(exc).__name__}). "
                 "It may not have happened yet, or this weekend had no such session. Try another event or session.")
        st.caption(f"Details: {str(exc)[:300] or type(exc).__name__}")
        st.stop()
    if laps.empty:
        st.warning("This session has no lap data.")
        st.stop()
    return laps


def driver_picker(page: str, drivers: list[str], colours: dict, default_n: int = 4, max_selected: int | None = None):
    """Chips for choosing drivers (with Select all / Clear) that remember the choice between pages."""
    ss = st.session_state
    key = f"w_{page}_drivers"
    if key not in ss:
        keep = [d for d in ss.get("mem_drivers", []) if d in drivers]
        ss[key] = keep or drivers[:default_n]
    else:
        ss[key] = [d for d in ss[key] if d in drivers]
    c1, c2, c3 = st.columns([1, 1, 6])
    if c1.button("Select all", key=f"{key}_all", disabled=max_selected is not None):
        ss[key] = list(drivers)
    if c2.button("Clear", key=f"{key}_none"):
        ss[key] = []
    chosen = st.pills("Drivers", drivers, selection_mode="multi", key=key, label_visibility="collapsed")
    chosen = list(chosen or [])
    if max_selected and len(chosen) > max_selected:
        st.warning(f"Showing the first {max_selected} of your selection.")
        chosen = chosen[:max_selected]
    ss["mem_drivers"] = chosen
    c3.caption(f"{len(chosen)} of {len(drivers)} drivers selected")
    return chosen


def tyre_dot(compound) -> str:
    """Small round tyre marker (coloured, with the compound's initial) as HTML."""
    return (f'<span class="tyre" style="background:{tyres.colour(compound)};color:{tyres.text_colour(compound)}">'
            f'{tyres.letter(compound)}</span>')


def tyre_legend(laps) -> None:
    """Which tyre colour is which, for the compounds in these laps, plus a note when some laps have no tyre information."""
    if "Compound" not in laps.columns:
        return
    present = sorted({tyres.normalise(c) for c in laps["Compound"]}, key=tyres.rank)
    st.markdown("".join(f'<span class="chip">{tyre_dot(c)}{tyres.name(c)}</span>' for c in present), unsafe_allow_html=True)
    note = tyres.unknown_note(laps)
    if note:
        st.caption(note)


def chips(labels: list[str], colours: dict) -> None:
    from f1 import charts

    html = "".join(f'<span class="chip"><i style="background:{colours.get(charts.driver_of(l), "#00D5CF")}"></i>{charts.pretty(l)}</span>'
                   for l in labels)
    st.markdown(html, unsafe_allow_html=True)
