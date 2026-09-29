"""USD/ZAR, EUR/ZAR, GBP/ZAR from Frankfurter (ECB reference rates, no API key).

ECB rates are published once per business day, so on weekends and Mondays the 'latest' rate
is Friday's. The section heading always states the date the rates are for.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from brief.config import Settings
from brief.http import get_json
from brief.runner import OK, PARTIAL, Context, SectionResult
from brief.util import DataError, describe, esc, fmt_change, fmt_day, fmt_num, pct_change

LOOKBACK_DAYS = 10  # wide enough to always span two ECB publication days, even over holidays


@dataclass
class Rate:
    base: str
    quote: str
    latest_date: date
    latest: float
    prev_date: date
    prev: float

    @property
    def change_pct(self) -> float:
        return pct_change(self.latest, self.prev)


def fetch_series(cfg: dict, base: str, today: date) -> dict:
    start = today - timedelta(days=LOOKBACK_DAYS)
    return get_json(f"{cfg['base_url']}/{start.isoformat()}..{today.isoformat()}",
                    {"base": base, "symbols": cfg["quote"]})


def parse_series(payload: dict, base: str, quote: str) -> Rate:
    try:
        series = {date.fromisoformat(d): float(v[quote]) for d, v in payload["rates"].items()}
    except (KeyError, AttributeError, TypeError, ValueError) as exc:
        raise DataError(f"unexpected Frankfurter response shape: {exc!r}") from exc
    days = sorted(series)
    if len(days) < 2:
        raise DataError(f"need two published days for {base}/{quote}, got {len(days)}")
    (d_prev, d_last) = days[-2], days[-1]
    return Rate(base, quote, d_last, series[d_last], d_prev, series[d_prev])


def render_rate(rate: Rate, heading_date: date) -> str:
    line = f"{rate.base}/{rate.quote}  {fmt_num(rate.latest, 2)}  {fmt_change(rate.change_pct)}"
    if rate.latest_date != heading_date:
        line += f" (as of {fmt_day(rate.latest_date)})"
    return line


def run(settings: Settings, ctx: Context) -> SectionResult:
    cfg = settings["fx"]
    rates: list[Rate] = []
    failures: dict[str, str] = {}
    for base in cfg["bases"]:
        try:
            rates.append(parse_series(fetch_series(cfg, base, ctx.today), base, cfg["quote"]))
        except Exception as exc:  # noqa: BLE001 - one pair failing must not drop the others
            failures[base] = describe(exc)

    if not rates:
        raise DataError("; ".join(f"{b}: {m}" for b, m in failures.items()))

    heading_date = max(r.latest_date for r in rates)
    by_base = {r.base: r for r in rates}
    lines = [render_rate(by_base[b], heading_date) if b in by_base
             else f"{esc(b)}/{esc(cfg['quote'])}  unavailable" for b in cfg["bases"]]
    result = SectionResult("fx", "Rand", lines, status=OK if not failures else PARTIAL)
    result.heading = f"<b>Rand</b> · ECB {fmt_day(heading_date)}"
    if failures:
        result.detail = "; ".join(f"{b}: {m}" for b, m in failures.items())
    return result
