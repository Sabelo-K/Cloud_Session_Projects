"""3-5 SA economy headlines from RSS feeds listed in settings.toml.

Headline + link only (never article text). Feeds are fetched independently, so a dead feed just
means fewer candidates. Ranking: keyword hits (title counts more than summary), then recency.
Near-duplicate stories are collapsed and one outlet can't fill the whole list.
"""
from __future__ import annotations

import difflib
import html
import logging
import os
import re
from dataclasses import dataclass
from datetime import timedelta
from urllib.parse import urlparse

from brief.config import Settings
from brief.http import get_bytes
from brief import summary
from brief.rss import FeedItem, parse_feed
from brief.runner import OK, PARTIAL, Context, SectionResult
from brief.util import DataError, describe, esc

log = logging.getLogger(__name__)

DEFAULT_UA = "Mozilla/5.0 (compatible; SA-Morning-Brief/1.0)"
ACCEPT = "application/rss+xml, application/atom+xml, application/xml;q=0.9, text/xml;q=0.8, */*;q=0.5"
STOPWORDS = frozenset("a an the of to in on at for and as by is are was with from after says say "
                      "said over into its it be will new".split())
TITLE_WEIGHT, SUMMARY_WEIGHT = 3, 1
TITLE_CHARS = 100
MIN_ITEMS = 3


@dataclass(frozen=True)
class Feed:
    name: str
    url: str
    priority: int = 0            # added to the score of every item from this feed
    keyword_only: bool = False   # general-interest feeds: only items matching a keyword qualify

    @classmethod
    def from_config(cls, raw: dict) -> "Feed":
        return cls(raw["name"], raw["url"], raw.get("priority", 0), raw.get("keyword_only", False))


@dataclass
class Candidate:
    item: FeedItem
    source: str
    score: int
    order: int                   # position in config; final tiebreak


def compile_keywords(keywords: list[str]) -> list[re.Pattern]:
    """'load shedding' also matches 'load-shedding'; a trailing plural 's' is allowed."""
    patterns = []
    for kw in keywords:
        body = r"[\s-]+".join(re.escape(part) for part in kw.split())
        patterns.append(re.compile(rf"(?<!\w){body}s?(?!\w)", re.IGNORECASE))
    return patterns


def score_item(item: FeedItem, patterns: list[re.Pattern]) -> int:
    return sum(TITLE_WEIGHT if p.search(item.title) else SUMMARY_WEIGHT if p.search(item.summary)
               else 0 for p in patterns)


def _tokens(title: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+(?:\.[0-9]+)?", title.lower())
    return [w for w in words if w not in STOPWORDS]


def similar(a: str, b: str, threshold: float) -> bool:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return a.strip().lower() == b.strip().lower()
    sa, sb = set(ta), set(tb)
    if len(sa & sb) / len(sa | sb) >= threshold:
        return True
    return difflib.SequenceMatcher(None, " ".join(ta), " ".join(tb)).ratio() >= 0.85


def select(candidates: list[Candidate], *, max_items: int, max_per_source: int,
           threshold: float) -> list[Candidate]:
    ranked = sorted(candidates, key=lambda c: (
        -c.score, -(c.item.published.timestamp() if c.item.published else 0), c.order))
    chosen: list[Candidate] = []
    per_source: dict[str, int] = {}
    for cand in ranked:
        if len(chosen) >= max_items:
            break
        if per_source.get(cand.source, 0) >= max_per_source:
            continue
        if any(cand.item.link == c.item.link or similar(cand.item.title, c.item.title, threshold)
               for c in chosen):
            continue
        chosen.append(cand)
        per_source[cand.source] = per_source.get(cand.source, 0) + 1
    return chosen


def fetch_feed(feed: Feed, cfg: dict) -> list[FeedItem]:
    data = get_bytes(feed.url, headers={"User-Agent": cfg.get("user_agent", DEFAULT_UA),
                                        "Accept": ACCEPT}, timeout=10, attempts=2)
    return parse_feed(data)


def _shorten(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def render_headline(cand: Candidate) -> str:
    href = html.escape(cand.item.link, quote=True)
    return f'• <a href="{href}">{esc(_shorten(cand.item.title, TITLE_CHARS))}</a> · {esc(cand.source)}'


def _is_web_link(url: str) -> bool:
    return urlparse(url).scheme in ("http", "https")


def _maybe_summarise(settings: Settings, titles: list[str]) -> tuple[str | None, str]:
    """(sentence, problem). Feature is off unless [summary] enabled = true; never raises."""
    cfg = settings.get("summary", {})
    if not cfg.get("enabled", False) or not titles:
        return None, ""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        return None, "summary enabled but ANTHROPIC_API_KEY is not set"
    try:
        sentence = summary.summarise(titles, cfg, api_key)
    except Exception as exc:  # noqa: BLE001 - the summary is a garnish; the headlines still go out
        return None, f"summary failed ({describe(exc)})"
    return sentence, "" if sentence else "summary came back empty"


def run(settings: Settings, ctx: Context) -> SectionResult:
    cfg = settings["headlines"]
    feeds = [Feed.from_config(f) for f in cfg["feeds"] if f.get("enabled", True)]
    if not feeds:
        raise DataError("no enabled feeds in [[headlines.feeds]]")
    patterns = compile_keywords(cfg["keywords"])
    max_age = timedelta(hours=cfg.get("max_age_hours", 48))

    candidates: list[Candidate] = []
    failures: dict[str, str] = {}
    for order, feed in enumerate(feeds):
        try:
            items = fetch_feed(feed, cfg)
        except Exception as exc:  # noqa: BLE001 - a dead feed must not stop the others
            failures[feed.name] = describe(exc)
            log.warning("feed=%s FAILED %s", feed.name, failures[feed.name])
            continue
        dated = [i.published for i in items if i.published]
        log.info("feed=%s ok items=%d newest=%s", feed.name, len(items),
                 max(dated).isoformat() if dated else "n/a")
        for item in items:
            if not _is_web_link(item.link):
                continue
            if item.published and ctx.now - item.published > max_age:
                continue
            score = score_item(item, patterns)
            if feed.keyword_only and score == 0:
                continue
            candidates.append(Candidate(item, feed.name, score + feed.priority, order))

    if len(failures) == len(feeds):
        raise DataError("all feeds failed: " + "; ".join(f"{k} ({v})" for k, v in failures.items()))

    chosen = select(candidates, max_items=cfg.get("max_items", 4),
                    max_per_source=cfg.get("max_per_source", 2),
                    threshold=cfg.get("similarity", 0.5))
    lines = [render_headline(c) for c in chosen] or ["No recent headlines."]
    detail = "; ".join(f"{k} ({v})" for k, v in failures.items())
    sentence, summary_problem = _maybe_summarise(settings, [c.item.title for c in chosen])
    if sentence:
        lines.insert(0, f"<i>{esc(sentence)}</i>")
    if summary_problem:
        detail = "; ".join(filter(None, [detail, summary_problem]))
    result = SectionResult("headlines", "SA economy", lines,
                           status=PARTIAL if detail else OK, detail=detail)
    result.heading = "<b>SA economy</b>"
    result.trimmable = max(0, len(chosen) - MIN_ITEMS)   # spec: always keep at least 3 if we have them
    return result
