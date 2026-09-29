"""JSE Top 40, five SA banks, Brent and gold from Yahoo Finance via yfinance.

yfinance scrapes an unofficial endpoint and can break or be rate-limited, so every instrument is
fetched and rendered independently: a failure shows 'unavailable' for that line only.

Rules that keep the numbers honest:
* Only completed sessions are used (today's partial bar is dropped), so the figure is always the
  previous close and its % change vs the session before.
* If the JSE did not trade yesterday (weekend / public holiday), its instruments collapse into
  one 'JSE closed yesterday' line instead of presenting an old change as new.
* If data for a session that should exist is missing, the line is labelled with its real date.

Yahoo failures tend to be all-or-nothing (rate limit, block), so after `max_consecutive_failures`
failures in a row the rest are skipped, and `budget_seconds` caps total time. Either way the
section returns promptly instead of retrying every ticker.
"""
from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass
from datetime import date, timedelta

from brief.config import Settings
from brief.jse_calendar import JSECalendar, SessionCalendar
from brief.runner import OK, PARTIAL, Context, SectionResult
from brief.util import DataError, describe, esc, fmt_change, fmt_day, fmt_num, pct_change

log = logging.getLogger(__name__)

History = list[tuple[date, float]]  # (session date in the exchange's own timezone, close)


@dataclass(frozen=True)
class Instrument:
    label: str
    symbol: str
    market: str = "24H"      # "JSE" uses the JSE calendar; anything else is weekdays-only
    prefix: str = ""
    decimals: int = 2
    divisor: float = 1.0     # 100 for JSE equities: Yahoo quotes them in cents (ZAc)

    @classmethod
    def from_config(cls, raw: dict) -> "Instrument":
        return cls(raw["label"], raw["symbol"], raw.get("market", "24H"), raw.get("prefix", ""),
                   raw.get("decimals", 2), raw.get("divisor", 1))


@dataclass
class Quote:
    instrument: Instrument
    session: date
    close: float
    prev_close: float

    @property
    def change_pct(self) -> float:
        return pct_change(self.close, self.prev_close)


def yahoo_history(symbol: str, attempts: int = 2) -> History:
    """Recent daily closes. Imported lazily so tests (and other sections) never load yfinance."""
    import yfinance as yf

    for attempt in range(1, attempts + 1):
        try:
            frame = yf.Ticker(symbol).history(period="1mo", interval="1d", auto_adjust=False,
                                              actions=False, timeout=15, raise_errors=True)
            break
        except Exception:  # noqa: BLE001 - rate limits, timeouts, missing ticker all surface here
            if attempt == attempts:
                raise
            time.sleep(3)
    closes = frame["Close"].dropna()
    return [(ts.date(), float(value)) for ts, value in closes.items()]


def make_quote(inst: Instrument, history: History, today: date) -> Quote:
    completed = sorted((d, c) for d, c in history if d < today)  # drop today's partial bar
    if len(completed) < 2:
        raise DataError(f"need 2 completed sessions, got {len(completed)}")
    (_, prev), (session, close) = completed[-2], completed[-1]
    if not all(math.isfinite(v) and v > 0 for v in (prev, close)):
        raise DataError(f"non-positive or non-finite close ({prev}, {close})")
    return Quote(inst, session, close, prev)


def fmt_price(inst: Instrument, raw_value: float) -> str:
    return f"{inst.prefix}{fmt_num(raw_value / inst.divisor, inst.decimals)}"


def render_quote(q: Quote, expected_session: date) -> str:
    inst = q.instrument
    price = fmt_price(inst, q.close)
    if q.session >= expected_session:
        return f"{esc(inst.label)}  {price}  {fmt_change(q.change_pct)}"
    return f"{esc(inst.label)}  {price} (last close {fmt_day(q.session)}, not updated)"


def run(settings: Settings, ctx: Context) -> SectionResult:
    cfg = settings["markets"]
    today = ctx.today
    instruments = [Instrument.from_config(raw) for raw in cfg["instruments"]]
    jse = JSECalendar(date.fromisoformat(d) for d in cfg.get("extra_jse_closed_dates", []))
    futures = SessionCalendar()

    jse_closed_reason = jse.closed_reason(today - timedelta(days=1))
    lines: list[str] = []
    failures: dict[str, str] = {}
    attempted = 0
    jse_note_written = False
    started = time.monotonic()
    budget = cfg.get("budget_seconds", 60)
    max_streak = cfg.get("max_consecutive_failures", 3)
    streak = 0
    skip_reason = ""

    for inst in instruments:
        if inst.market == "JSE" and jse_closed_reason:
            if not jse_note_written:
                lines.append(f"JSE closed yesterday ({esc(jse_closed_reason)}); "
                             f"last session {fmt_day(jse.previous_session(today))}")
                jse_note_written = True
            continue
        attempted += 1
        if not skip_reason and streak >= max_streak:
            skip_reason = f"skipped after {streak} consecutive failures (Yahoo looks down)"
        elif not skip_reason and time.monotonic() - started >= budget:
            skip_reason = f"skipped: {budget:g}s time budget used up"
        if skip_reason:
            failures[inst.label] = f"{inst.symbol} {skip_reason}"
            lines.append(f"{esc(inst.label)}  unavailable")
            continue
        calendar = jse if inst.market == "JSE" else futures
        try:
            quote = make_quote(inst, yahoo_history(inst.symbol), today)
            log.debug("markets %s (%s): close=%s prev=%s session=%s", inst.label, inst.symbol,
                      quote.close, quote.prev_close, quote.session)
            lines.append(render_quote(quote, calendar.previous_session(today)))
            streak = 0
        except Exception as exc:  # noqa: BLE001 - one bad ticker must not drop the others
            failures[inst.label] = f"{inst.symbol} {describe(exc)}"
            lines.append(f"{esc(inst.label)}  unavailable")
            streak += 1

    detail = "; ".join(f"{k} ({v})" for k, v in failures.items())
    if attempted and len(failures) == attempted:
        raise DataError(f"all {attempted} instruments failed: {detail}")
    result = SectionResult("markets", "Markets", lines,
                           status=OK if not failures else PARTIAL, detail=detail)
    result.heading = "<b>Markets</b> (previous close)"
    return result
