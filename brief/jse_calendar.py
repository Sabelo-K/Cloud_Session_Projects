"""Trading-session calendars, used to tell 'no new session' apart from 'stale data'."""
from __future__ import annotations

from datetime import date, timedelta
from typing import Iterable

import holidays

from brief.util import DAYS


class SessionCalendar:
    """Weekdays only. Used for 24h futures, where we don't model exchange holidays."""

    def closed_reason(self, d: date) -> str | None:
        return DAYS[d.weekday()] if d.weekday() >= 5 else None

    def is_open(self, d: date) -> bool:
        return self.closed_reason(d) is None

    def previous_session(self, d: date) -> date:
        """Latest open day strictly before `d`."""
        d -= timedelta(days=1)
        while not self.is_open(d):
            d -= timedelta(days=1)
        return d


class JSECalendar(SessionCalendar):
    """Weekdays minus South African public holidays, plus any user-listed one-off closures."""

    def __init__(self, extra_closed: Iterable[date] = ()) -> None:
        self._extra = set(extra_closed)
        # holidays expands years on demand, so any date can be looked up.
        self._za = holidays.country_holidays("ZA")

    def closed_reason(self, d: date) -> str | None:
        if d.weekday() >= 5:
            return DAYS[d.weekday()]
        if d in self._za:
            return str(self._za.get(d))
        if d in self._extra:
            return "market closure"
        return None
