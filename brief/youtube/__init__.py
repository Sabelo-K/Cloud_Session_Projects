"""YouTube data sources. Select one with `source = "..."` in [youtube] of settings.toml."""
from __future__ import annotations

from brief.util import DataError
from brief.youtube.data_api import DataApiSource
from brief.youtube.models import YouTubeSource

# To add the Command Centre's Supabase source later: write a class with a `label` and
# `fetch_reports(channels, ctx) -> list[ChannelReport]`, register it here, and set
# `source = "supabase"` in settings.toml. Nothing else changes.
SOURCES: dict[str, type] = {"data_api": DataApiSource}


def get_source(name: str, cfg: dict) -> YouTubeSource:
    try:
        cls = SOURCES[name]
    except KeyError:
        raise DataError(f"unknown youtube source {name!r}; available: {', '.join(SOURCES)}") from None
    return cls(cfg)
