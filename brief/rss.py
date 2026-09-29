"""Minimal, dependency-free RSS 2.0 / RSS 1.0 / Atom parsing.

Feeds are untrusted input, so: size-capped, and any feed declaring XML entities is refused
(stdlib parsers can be blown up by entity-expansion tricks). Only headline, link, date and a
short plain-text summary (used for keyword matching, never sent) are extracted.
"""
from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from brief.util import DataError

MAX_BYTES = 3_000_000
SUMMARY_CHARS = 500


@dataclass(frozen=True)
class FeedItem:
    title: str
    link: str
    published: datetime | None   # timezone-aware when present
    summary: str                 # plain text, truncated; for matching only


def _local(tag: object) -> str:
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def _child_text(el: ET.Element, *names: str) -> str:
    for child in el:
        if _local(child.tag) in names and (child.text or "").strip():
            return child.text.strip()
    return ""


def _atom_link(entry: ET.Element) -> str:
    for child in entry:
        if _local(child.tag) == "link" and child.get("rel", "alternate") == "alternate":
            if child.get("href"):
                return child.get("href", "").strip()
    return ""


def _parse_date(text: str) -> datetime | None:
    if not text:
        return None
    parsed: datetime | None = None
    try:
        parsed = parsedate_to_datetime(text)          # RSS: "Tue, 29 Sep 2026 05:00:00 +0200"
    except (TypeError, ValueError):
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))   # Atom / dc:date
        except ValueError:
            return None
    if parsed is None:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _plain(text: str, limit: int) -> str:
    text = html.unescape(re.sub(r"<[^>]*>", " ", text))
    return " ".join(text.split())[:limit]


def parse_feed(data: bytes) -> list[FeedItem]:
    if len(data) > MAX_BYTES:
        raise DataError(f"feed too large ({len(data)} bytes)")
    if b"<!ENTITY" in data:
        raise DataError("refusing feed that declares XML entities")
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise DataError(f"not valid RSS/Atom XML ({exc})") from exc

    kind = _local(root.tag)
    if kind not in ("rss", "RDF", "feed"):
        raise DataError(f"unsupported feed root <{kind}>")
    entries = [el for el in root.iter() if _local(el.tag) == ("entry" if kind == "feed" else "item")]

    items: list[FeedItem] = []
    for el in entries:
        title = " ".join(html.unescape(_child_text(el, "title")).split())
        link = _atom_link(el) if kind == "feed" else _child_text(el, "link")
        if not title or not link:
            continue
        items.append(FeedItem(
            title=title,
            link=link,
            published=_parse_date(_child_text(el, "pubDate", "published", "updated", "date")),
            summary=_plain(_child_text(el, "description", "summary", "encoded", "content"),
                           SUMMARY_CHARS),
        ))
    return items
