"""Tiny JSON store of each channel's daily public stats, so the brief can show day-over-day change.

The GitHub Actions workflow commits this file after each real run. Layout:
    {"version": 1, "channels": {"UC...": {"2026-09-28": {"subs": 1230, "views": 45000, "videos": 42}}}}
"""
from __future__ import annotations

import json
import logging
import os
import tempfile
from datetime import date, timedelta
from pathlib import Path

log = logging.getLogger(__name__)


class JsonHistory:
    def __init__(self, path: Path, keep_days: int = 120) -> None:
        self.path = Path(path)
        self.keep_days = keep_days
        self.load_error: str | None = None
        self._channels: dict[str, dict[str, dict]] = self._load()

    def _load(self) -> dict[str, dict[str, dict]]:
        if not self.path.is_file():
            return {}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            channels = data["channels"]
            if not isinstance(channels, dict):
                raise TypeError("'channels' is not an object")
            return channels
        except (ValueError, KeyError, TypeError) as exc:
            # Never overwrite a file we couldn't read: that would destroy the history.
            self.load_error = f"history file unreadable ({exc!r}); day-over-day change unavailable"
            log.warning("%s: %s", self.path, self.load_error)
            return {}

    def previous(self, channel_id: str, today: date) -> tuple[date, dict] | None:
        """The most recent entry strictly before `today` (so a same-day rerun compares to
        yesterday, not to itself)."""
        days = self._channels.get(channel_id, {})
        earlier = sorted(d for d in days if date.fromisoformat(d) < today)
        return (date.fromisoformat(earlier[-1]), days[earlier[-1]]) if earlier else None

    def record(self, channel_id: str, day: date, subs: int | None, views: int | None,
               videos: int | None) -> None:
        self._channels.setdefault(channel_id, {})[day.isoformat()] = {
            "subs": subs, "views": views, "videos": videos}

    def save(self, today: date) -> None:
        if self.load_error:
            return
        cutoff = (today - timedelta(days=self.keep_days)).isoformat()
        pruned = {cid: {d: v for d, v in sorted(days.items()) if d >= cutoff}
                  for cid, days in sorted(self._channels.items())}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps({"version": 1, "channels": pruned}, indent=1, ensure_ascii=False)
        fd, tmp = tempfile.mkstemp(dir=self.path.parent, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(payload + "\n")
            os.replace(tmp, self.path)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
