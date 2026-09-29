"""Small shared helpers: SAST time, HTML escaping, number/date formatting."""
from __future__ import annotations

import html
from datetime import date, datetime, timedelta, timezone

# South Africa has no DST, so a fixed offset is exact and needs no tzdata package.
SAST = timezone(timedelta(hours=2), "SAST")

DAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
MONTHS = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)


class DataError(Exception):
    """A source responded, but not with usable data."""


def now_sast() -> datetime:
    return datetime.now(SAST)


def describe(exc: BaseException, limit: int = 140) -> str:
    """One-line, length-capped 'ExcType: message' for logs and Actions annotations."""
    first = (str(exc).strip().splitlines() or [""])[0]
    text = f"{type(exc).__name__}: {first}" if first else type(exc).__name__
    return text if len(text) <= limit else text[: limit - 1] + "…"


def esc(text: object) -> str:
    """Escape for Telegram HTML. Apply to every dynamic string (headlines, names, errors)."""
    return html.escape(str(text), quote=False)


def fmt_num(value: float, decimals: int = 0) -> str:
    return f"{value:,.{decimals}f}"


def pct_change(new: float, old: float) -> float:
    if old == 0:
        raise DataError("previous value is zero; cannot compute % change")
    return (new - old) / old * 100


def fmt_change(pct: float) -> str:
    """'▲ 0.3%' / '▼ 0.1%' / '▬ 0.0%'. Rounds first so a tiny negative never shows as '-0.0'."""
    rounded = round(pct, 1)
    if rounded == 0:
        return "▬ 0.0%"
    return f"{'▲' if rounded > 0 else '▼'} {abs(rounded):.1f}%"


def fmt_day(d: date) -> str:
    """'Tue 29 Sep'. Hand-rolled so output never depends on the machine's locale."""
    return f"{DAYS[d.weekday()][:3]} {d.day} {MONTHS[d.month - 1][:3]}"


def fmt_date_long(d: date) -> str:
    """'Tuesday 29 September 2026'."""
    return f"{DAYS[d.weekday()]} {d.day} {MONTHS[d.month - 1]} {d.year}"
