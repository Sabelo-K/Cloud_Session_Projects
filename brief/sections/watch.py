"""One-line 'watch today' item from an editable TOML file (config/events.toml).

Silent on days with no event. A malformed entry is skipped and reported in the run log rather
than breaking the brief; an unreadable file fails only this section.
"""
from __future__ import annotations

import logging
import tomllib
from dataclasses import dataclass
from datetime import date

from brief.config import ROOT, Settings
from brief.runner import OK, PARTIAL, Context, SectionResult
from brief.util import esc

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Event:
    day: date
    text: str


def load_events(path) -> tuple[list[Event], list[str]]:
    """Returns (valid events, problems). Raises only if the file can't be read/parsed at all."""
    with open(path, "rb") as fh:
        raw = tomllib.load(fh)
    events: list[Event] = []
    problems: list[str] = []
    for i, entry in enumerate(raw.get("event", []), start=1):
        try:
            day = date.fromisoformat(str(entry["date"]))
            text = str(entry["text"]).strip()
            if not text:
                raise ValueError("empty text")
        except (KeyError, ValueError) as exc:
            problems.append(f"event #{i} skipped ({exc!r}); needs date=YYYY-MM-DD and text")
            continue
        events.append(Event(day, text))
    return events, problems


def run(settings: Settings, ctx: Context) -> SectionResult:
    cfg = settings["watch"]
    events, problems = load_events(ROOT / cfg["file"])
    today_texts = [e.text for e in events if e.day == ctx.today]
    status, detail = (PARTIAL, "; ".join(problems)) if problems else (OK, "")
    if not today_texts:
        return SectionResult("watch", "Watch today", [], status=status, detail=detail, hidden=True)
    result = SectionResult("watch", "Watch today", [], status=status, detail=detail)
    result.heading = f"<b>Watch today:</b> {' · '.join(esc(t) for t in today_texts)}"
    return result
