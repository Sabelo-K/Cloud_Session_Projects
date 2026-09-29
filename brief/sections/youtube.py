"""My YouTube channels, in at most MAX_LINES lines (heading included).

Rendering is source-independent: it only sees ChannelReport objects (see brief/youtube).
"""
from __future__ import annotations

import html
import re
from datetime import datetime

from brief.config import Settings
from brief.runner import OK, PARTIAL, Context, SectionResult
from brief.util import DataError, esc, fmt_day, fmt_num
from brief.youtube import get_source
from brief.youtube.models import ChannelConfig, ChannelReport

MAX_LINES = 7                                   # spec: under 8 lines for the whole section
CHANNEL_ID = re.compile(r"^UC[\w-]{22}$")
VIDEO_ID = re.compile(r"^[\w-]{6,20}$")
TITLE_CHARS = 60


def fmt_delta(n: int | None) -> str:
    if n is None:
        return ""
    return f" (+{n:,})" if n > 0 else f" ({n:,})" if n < 0 else " (0)"


def fmt_age(now: datetime, published: datetime | None) -> str:
    if published is None:
        return ""
    hours = int((now - published).total_seconds() // 3600)
    return "today" if hours < 1 else f"{hours}h ago" if hours < 24 else f"{hours // 24}d ago"


def _stats_line(r: ChannelReport, today) -> str:
    s = r.snapshot
    subs = "subs hidden" if s.subs is None else f"{fmt_num(s.subs)} subs{fmt_delta(r.d_subs)}"
    parts = [subs]
    if s.views is not None:
        parts.append(f"{fmt_num(s.views)} views{fmt_delta(r.d_views)}")
    if s.videos is not None:
        parts.append(f"{fmt_num(s.videos)} videos{fmt_delta(r.d_videos)}")
    line = f"<b>{esc(r.name)}</b>: " + " · ".join(parts)
    if r.prev_date is None:
        line += " (first snapshot)"
    elif (today - r.prev_date).days > 1:
        line += f" (vs {esc(fmt_day(r.prev_date))})"
    return line


def _latest_line(r: ChannelReport, now: datetime) -> str | None:
    latest = r.snapshot.latest if r.snapshot else None
    if latest is None:
        return None
    title = latest.title if len(latest.title) <= TITLE_CHARS else latest.title[:TITLE_CHARS - 1].rstrip() + "…"
    label = esc(title)
    if VIDEO_ID.match(latest.video_id):
        label = f'<a href="{html.escape(f"https://youtu.be/{latest.video_id}", quote=True)}">{label}</a>'
    bits = [label]
    if latest.views is not None:
        bits.append(f"{fmt_num(latest.views)} views")
    age = fmt_age(now, latest.published)
    if age:
        bits.append(age)
    return "↳ " + " · ".join(bits)


def render_reports(reports: list[ChannelReport], ctx: Context, max_lines: int = MAX_LINES) -> list[str]:
    """Body lines only; the heading takes one of `max_lines`. Two lines per channel while that
    fits, then one line per channel, then the first few plus a '+N more' line."""
    budget = max_lines - 1
    with_latest = len(reports) * 2 <= budget
    shown = reports if len(reports) <= budget else reports[: budget - 1]
    lines: list[str] = []
    for r in shown:
        if r.snapshot is None:
            lines.append(f"<b>{esc(r.name)}</b>: unavailable")
            continue
        lines.append(_stats_line(r, ctx.today))
        latest = _latest_line(r, ctx.now) if with_latest else None
        if latest:
            lines.append(latest)
    if len(shown) < len(reports):
        lines.append(f"+{len(reports) - len(shown)} more channels not shown")
    return lines


def _channel_configs(cfg: dict) -> tuple[list[ChannelConfig], list[str]]:
    channels, problems = [], []
    for raw in cfg.get("channels", []):
        channel_id = str(raw.get("id", "")).strip()
        if not CHANNEL_ID.match(channel_id):
            problems.append(f"{channel_id!r} is not a channel ID (they start with UC and are 24 "
                            f"characters; an @handle won't work)")
            continue
        channels.append(ChannelConfig(channel_id, str(raw.get("name", "")).strip()))
    return channels, problems


def run(settings: Settings, ctx: Context) -> SectionResult:
    cfg = settings["youtube"]
    channels, problems = _channel_configs(cfg)
    if not channels:
        detail = "; ".join(problems) or "no channels listed under [[youtube.channels]] in settings.toml"
        return SectionResult("youtube", "YouTube", [], status=PARTIAL, detail=detail, hidden=True)

    source = get_source(cfg.get("source", "data_api"), cfg)
    reports = source.fetch_reports(channels, ctx)
    if not any(r.snapshot for r in reports):
        raise DataError("no channel could be fetched: " + "; ".join(
            f"{r.name}: {'; '.join(r.problems)}" for r in reports))

    for r in reports:
        problems += [f"{r.name}: {p}" for p in r.problems]
    result = SectionResult("youtube", "YouTube", render_reports(reports, ctx),
                           status=PARTIAL if problems else OK, detail="; ".join(problems))
    result.heading = f"<b>YouTube</b> ({esc(source.label)})"
    return result
