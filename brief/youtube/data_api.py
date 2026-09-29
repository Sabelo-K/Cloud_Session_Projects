"""Public channel stats from the YouTube Data API v3 (API key only, no OAuth).

Quota: about 2 + N units per run for N channels, against a free 10,000 per day.
The key is sent in the `X-Goog-Api-Key` header, never in the URL, so it can't leak through
request-error messages.

Public subscriber counts are rounded by YouTube (to 3 significant figures), so small
day-over-day changes can be invisible on larger channels. Counts under 1,000 are exact.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Iterator

from brief.config import ROOT, require_env
from brief.http import get_json
from brief.runner import Context
from brief.util import describe
from brief.youtube.history import JsonHistory
from brief.youtube.models import (ChannelConfig, ChannelReport, ChannelSnapshot, LatestVideo)

log = logging.getLogger(__name__)

API = "https://www.googleapis.com/youtube/v3"
BATCH = 50                                        # max ids per channels.list / videos.list call
UNAVAILABLE_TITLES = {"Private video", "Deleted video"}


def _int(value: object) -> int | None:
    try:
        return int(value)  # type: ignore[arg-type]  # the API sends counts as strings
    except (TypeError, ValueError):
        return None


def _chunks(items: list[str], size: int) -> Iterator[list[str]]:
    for i in range(0, len(items), size):
        yield items[i:i + size]


def _parse_time(text: object) -> datetime | None:
    try:
        return datetime.fromisoformat(str(text).replace("Z", "+00:00"))
    except ValueError:
        return None


class DataApiSource:
    label = "public stats, subs rounded"

    def __init__(self, cfg: dict, api_key: str | None = None,
                 history: JsonHistory | None = None) -> None:
        self.api_key = api_key or require_env("YOUTUBE_API_KEY")
        self.history = history or JsonHistory(ROOT / cfg.get("state_file", "data/youtube_history.json"),
                                              cfg.get("history_days", 120))

    def _get(self, path: str, params: dict) -> dict:
        return get_json(f"{API}/{path}", params, headers={"X-Goog-Api-Key": self.api_key},
                        redact=[self.api_key], timeout=15)

    # -- fetching --------------------------------------------------------------------------

    def fetch_snapshots(self, channels: list[ChannelConfig]) -> dict[str, ChannelSnapshot]:
        snapshots: dict[str, ChannelSnapshot] = {}
        uploads: dict[str, str] = {}
        for chunk in _chunks([c.id for c in channels], BATCH):
            data = self._get("channels", {"part": "snippet,statistics,contentDetails",
                                          "id": ",".join(chunk), "maxResults": BATCH})
            for item in data.get("items", []):
                stats = item.get("statistics", {})
                subs = None if stats.get("hiddenSubscriberCount") else _int(stats.get("subscriberCount"))
                snapshots[item["id"]] = ChannelSnapshot(
                    channel_id=item["id"], name=item.get("snippet", {}).get("title", item["id"]),
                    subs=subs, views=_int(stats.get("viewCount")), videos=_int(stats.get("videoCount")))
                playlist = item.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads")
                if playlist:
                    uploads[item["id"]] = playlist

        for channel_id, playlist in uploads.items():
            snap = snapshots[channel_id]
            try:
                snap.latest = self._latest_upload(playlist)
            except Exception as exc:  # noqa: BLE001 - the channel's stats are still worth showing
                snap.problems.append(f"latest upload unavailable ({describe(exc)})")
        self._attach_view_counts([s.latest for s in snapshots.values() if s.latest], snapshots)
        return snapshots

    def _latest_upload(self, playlist_id: str) -> LatestVideo | None:
        data = self._get("playlistItems", {"part": "snippet,contentDetails",
                                           "playlistId": playlist_id, "maxResults": 3})
        for item in data.get("items", []):   # newest first; skip private/deleted placeholders
            snippet, details = item.get("snippet", {}), item.get("contentDetails", {})
            title = snippet.get("title", "")
            video_id = details.get("videoId") or snippet.get("resourceId", {}).get("videoId")
            if title and video_id and title not in UNAVAILABLE_TITLES:
                return LatestVideo(title, video_id, None, _parse_time(
                    details.get("videoPublishedAt") or snippet.get("publishedAt")))
        return None

    def _attach_view_counts(self, videos: list[LatestVideo], snapshots: dict) -> None:
        if not videos:
            return
        by_id = {v.video_id: v for v in videos}
        try:
            for chunk in _chunks(list(by_id), BATCH):
                data = self._get("videos", {"part": "statistics", "id": ",".join(chunk),
                                            "maxResults": BATCH})
                for item in data.get("items", []):
                    if item.get("id") in by_id:
                        by_id[item["id"]].views = _int(item.get("statistics", {}).get("viewCount"))
        except Exception as exc:  # noqa: BLE001
            for snap in snapshots.values():
                if snap.latest:
                    snap.problems.append(f"latest upload views unavailable ({describe(exc)})")

    # -- history + deltas ------------------------------------------------------------------

    def fetch_reports(self, channels: list[ChannelConfig], ctx: Context) -> list[ChannelReport]:
        snapshots = self.fetch_snapshots(channels)
        reports: list[ChannelReport] = []
        for channel in channels:
            snap = snapshots.get(channel.id)
            if snap is None:
                reports.append(ChannelReport(channel.id, channel.name or channel.id, None,
                                             problems=["channel not found (check the ID)"]))
                continue
            if channel.name:
                snap.name = channel.name
            report = ChannelReport(channel.id, snap.name, snap, problems=list(snap.problems))
            previous = self.history.previous(channel.id, ctx.today)
            if previous:
                report.prev_date, old = previous
                for attr, key in (("d_subs", "subs"), ("d_views", "views"), ("d_videos", "videos")):
                    now_value, old_value = getattr(snap, key), old.get(key)
                    if now_value is not None and old_value is not None:
                        setattr(report, attr, now_value - old_value)
            if self.history.load_error:
                report.problems.append(self.history.load_error)
            self.history.record(channel.id, ctx.today, snap.subs, snap.views, snap.videos)
            reports.append(report)
        if not ctx.dry_run:
            self.history.save(ctx.today)
        return reports
