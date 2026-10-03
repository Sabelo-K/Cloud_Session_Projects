"""Team/compound colours and chart styling shared by the app. Pure helpers are unit-tested."""
from __future__ import annotations

import pandas as pd

from f1 import tyres

# Matched by lower-case substring of FastF1's Team name, first hit wins.
TEAM_COLORS = [
    ("red bull", "#3671C6"), ("racing bulls", "#6692FF"), ("alphatauri", "#5E8FAA"),
    ("mercedes", "#27F4D2"), ("ferrari", "#E8002D"), ("mclaren", "#FF8000"),
    ("aston", "#229971"), ("alpine", "#FF87BC"), ("williams", "#64C4FF"),
    ("sauber", "#52E252"), ("alfa", "#B12039"), ("haas", "#B6BABD"),
    ("audi", "#F50537"), ("cadillac", "#9AA0A6"), ("renault", "#FFF500"), ("racing point", "#F596C8"),
]
FALLBACK = ["#E10600", "#FFD60A", "#30D158", "#BF5AF2", "#FF9F0A", "#64D2FF"]

COMPOUND_COLORS = tyres.COLOURS


def team_color(team: str | None, fallback_index: int = 0) -> str:
    name = (team or "").lower()
    if name in ("rb", "visa cash app rb"):
        return "#6692FF"
    for key, colour in TEAM_COLORS:
        if key in name:
            return colour
    return FALLBACK[fallback_index % len(FALLBACK)]


def driver_styles(laps: pd.DataFrame) -> tuple[dict, dict]:
    """(colour map, dash map) per driver: team colour, with a team's second driver dashed."""
    colours, dashes = {}, {}
    if "Team" not in laps.columns:
        return colours, dashes
    teams = laps.dropna(subset=["Team"]).groupby("Driver")["Team"].first()
    seen: dict[str, int] = {}
    for i, (drv, team) in enumerate(sorted(teams.items())):
        colours[drv] = team_color(team, i)
        seen[team] = seen.get(team, 0) + 1
        dashes[drv] = "solid" if seen[team] == 1 else "dash"
    return colours, dashes


def lighten(hex_colour: str, amount: float = 0.45) -> str:
    h = hex_colour.lstrip("#")
    rgb = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
    return "#" + "".join(f"{round(c + (255 - c) * amount):02X}" for c in rgb)


def distinct_colours(laps: pd.DataFrame) -> dict:
    """Like driver_styles' colours, but a team's second driver gets a lighter shade of the team colour, for charts
    where line style is already used for something else (e.g. which comparison group a lap belongs to)."""
    colours, dashes = driver_styles(laps)
    return {d: (lighten(c) if dashes.get(d) == "dash" else c) for d, c in colours.items()}


def style_fig(fig, height: int = 380):
    """Compact, phone-friendly layout: legend underneath, tight margins, transparent background."""
    legend = dict(orientation="h", yanchor="top", y=-0.18, x=0, title_text="")
    if fig.layout.legend.orientation:  # a chart that placed its own legend (e.g. above tilted labels) keeps it
        legend = dict(title_text="")
    fig.update_layout(
        height=height, margin=dict(l=8, r=8, t=fig.layout.margin.t or 40, b=8),
        legend=legend,
        title=dict(font=dict(size=15), x=0),
    )
    return dark_theme(fig)


CHART_BG = "#0A0B0E"
CHART_GRID = "#262A31"
CHART_TEXT = "#C9D1D9"


def dark_theme(fig):
    """The broadcast-graphic look shared by every chart: near-black canvas, dotted grid, light text, dark tooltips.
    Only fills in what a chart has not set itself."""
    fig.update_layout(
        paper_bgcolor=fig.layout.paper_bgcolor or CHART_BG, plot_bgcolor=fig.layout.plot_bgcolor or CHART_BG,
        font=dict(color=CHART_TEXT),
        hoverlabel=dict(bgcolor=fig.layout.hoverlabel.bgcolor or "#14171C", bordercolor="#2B3038",
                        font=dict(color=fig.layout.hoverlabel.font.color or "#FFFFFF")),
    )
    fig.update_xaxes(gridcolor=CHART_GRID, griddash="dot", zeroline=False, linecolor=CHART_GRID)
    fig.update_yaxes(gridcolor=CHART_GRID, griddash="dot", zeroline=False, linecolor=CHART_GRID)
    return fig


def fmt_lap(seconds: float) -> str:
    """101.5 -> '1:41.500'."""
    m, s = divmod(float(seconds), 60)
    return f"{int(m)}:{s:06.3f}"


_LAP_STEPS = [0.1, 0.2, 0.5, 1, 2, 5, 10, 15, 30, 60, 120, 300]


def lap_time_axis(fig, axis: str = "y"):
    """Show a lap-time axis as m:ss instead of raw seconds, and every hover that printed '%{y:.3f}s' as m:ss.sss.
    Call once the traces are added; the ticks are fixed, so very deep zooms show only the coarse marks."""
    vals = [v for t in fig.data if getattr(t, axis, None) is not None
            for v in pd.to_numeric(pd.Series(list(getattr(t, axis))), errors="coerce").dropna()]
    if not vals:
        return fig
    lo, hi = min(vals), max(vals)
    step = next((s for s in _LAP_STEPS if (hi - lo) / s <= 12), _LAP_STEPS[-1])
    first = int(lo // step) * step
    ticks = [round(first + i * step, 3) for i in range(int((hi - first) // step) + 2)]
    ticks = [t for t in ticks if t >= lo - step and t <= hi + step]
    text = [fmt_lap(t)[:-2] if step < 1 else fmt_lap(t)[:-4] for t in ticks]
    (fig.update_yaxes if axis == "y" else fig.update_xaxes)(tickmode="array", tickvals=ticks, ticktext=text)
    if axis == "y":
        for t in fig.data:
            tpl = getattr(t, "hovertemplate", None)
            if isinstance(tpl, str) and "%{y:.3f}s" in tpl:
                t.hovertext = [fmt_lap(v) if v == v else "" for v in pd.to_numeric(pd.Series(list(t.y)), errors="coerce")]
                t.hovertemplate = tpl.replace("%{y:.3f}s", "%{hovertext}")
    return fig


PLOT_CONFIG = {"displayModeBar": False}
