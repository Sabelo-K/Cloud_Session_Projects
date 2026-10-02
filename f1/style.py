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
    fig.update_layout(
        height=height, margin=dict(l=8, r=8, t=fig.layout.margin.t or 40, b=8),
        legend=dict(orientation="h", yanchor="top", y=-0.18, x=0, title_text=""),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        title=dict(font=dict(size=15), x=0),
    )
    return fig


PLOT_CONFIG = {"displayModeBar": False}
