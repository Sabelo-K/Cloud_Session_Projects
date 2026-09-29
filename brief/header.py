"""First line of the message: date, weekday, and whether today is a SA public holiday."""
from __future__ import annotations

import logging
from datetime import date

from brief.jse_calendar import za_holiday_name
from brief.util import esc, fmt_date_long

log = logging.getLogger(__name__)


def build_header(today: date) -> str:
    text = f"<b>{esc(fmt_date_long(today))}</b>"
    try:
        holiday = za_holiday_name(today)
    except Exception:  # noqa: BLE001 - the header must never stop the brief
        log.exception("holiday lookup failed")
        return text
    return f"{text} · Public holiday: {esc(holiday)}" if holiday else text
