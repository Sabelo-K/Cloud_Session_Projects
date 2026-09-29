"""Source-neutral data shapes for the YouTube section.

The renderer only ever sees `ChannelReport`. Any data source (public Data API now, Supabase
later) just has to produce a list of them, so switching is a config change, not a rewrite.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:  # avoid a runtime import cycle with the runner
    from brief.runner import Context


@dataclass(frozen=True)
class ChannelConfig:
    id: str
    name: str = ""


@dataclass
class LatestVideo:
    title: str
    video_id: str
    views: int | None
    published: datetime | None


@dataclass
class ChannelSnapshot:
    channel_id: str
    name: str
    subs: int | None          # None when the channel hides its subscriber count
    views: int | None
    videos: int | None
    latest: LatestVideo | None = None
    problems: list[str] = field(default_factory=list)   # non-fatal issues, e.g. latest upload


@dataclass
class ChannelReport:
    channel_id: str
    name: str
    snapshot: ChannelSnapshot | None        # None: the channel could not be fetched
    prev_date: date | None = None           # date the deltas are measured against
    d_subs: int | None = None
    d_views: int | None = None
    d_videos: int | None = None
    problems: list[str] = field(default_factory=list)


class YouTubeSource(Protocol):
    #: Short text for the section heading, describing what the numbers are.
    label: str

    def fetch_reports(self, channels: list[ChannelConfig], ctx: "Context") -> list[ChannelReport]:
        ...
