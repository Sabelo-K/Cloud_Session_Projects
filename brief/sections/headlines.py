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
    keyword_only: bool = False   # general-interest feeds: only items with a keyword in the TITLE qualify
    user_agent: str = ""         # per-feed override for sites that block the default one
    split_publisher: bool = False  # aggregator titles end in " - Publisher": show that as the source

    @classmethod
    def from_config(cls, raw: dict) -> "Feed":
        return cls(raw["name"], raw["url"], raw.get("priority", 0), raw.get("keyword_only", False),
                   raw.get("user_agent", ""), raw.get("split_publisher", False))


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


def strip_excluded(text: str, exclude: list[str]) -> str:
    """Blank out phrases that contain a keyword without meaning it ('East Rand' is a place)."""
    for phrase in exclude:
        text = re.sub(re.escape(phrase), " ", text, flags=re.IGNORECASE)
    return text


def score_item(item: FeedItem, patterns: list[re.Pattern], exclude: list[str] = ()) -> int:
    title, summary = strip_excluded(item.title, exclude), strip_excluded(item.summary, exclude)
    return sum(TITLE_WEIGHT if p.search(title) else SUMMARY_WEIGHT if p.search(summary)
               else 0 for p in patterns)


def split_publisher(title: str) -> tuple[str, str | None]:
    """'Rates rise - Business Day' -> ('Rates rise', 'Business Day'). Only splits on a short tail."""
    head, sep, tail = title.rpartition(" - ")
    return (head, tail) if sep and head and 0 < len(tail) <= 40 else (title, None)


def title_matches(item: FeedItem, patterns: list[re.Pattern], exclude: list[str] = ()) -> bool:
    title = strip_excluded(item.title, exclude)
    return any(p.search(title) for p in patterns)


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
    data = get_bytes(feed.url, headers={"User-Agent": feed.user_agent or cfg.get("user_agent", DEFAULT_UA),
                                        "Accept": ACCEPT}, timeout=10, attempts=2)
    return parse_feed(data)


def _shorten(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def render_headline(cand: Candidate) -> str:
    href = html.escape(cand.item.link, quote=True)
    return f'• <a href="{href}">{esc(_shorten(cand.item.title, TITLE_CHARS))}</a> · {esc(cand.source)}'


def _is_web_link(url: str) -> bool:
    return urlparse(url).scheme in ("http", "https")


BRIEFING_INPUT_ITEMS = 12   # how many top-ranked items the briefing is written from


def _maybe_brief(settings: Settings, pool: list[Candidate]) -> tuple[list[str] | None, str]:
    """(briefing lines, problem). Off unless [summary] enabled = true; never raises."""
    cfg = settings.get("summary", {})
    if not cfg.get("enabled", False) or not pool:
        return None, ""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        return None, "briefing enabled but ANTHROPIC_API_KEY is not set"
    try:
        lines = summary.briefing([(c.item.title, c.item.summary) for c in pool], cfg, api_key)
    except Exception as exc:  # noqa: BLE001 - the briefing is a bonus; the headlines still go out
        return None, f"briefing failed ({describe(exc)})"
    return lines, "" if lines else "briefing came back empty"


def run(settings: Settings, ctx: Context) -> SectionResult:
    return run_feeds(settings, ctx, key="headlines", title="SA economy", allow_summary=True)


def run_feeds(settings: Settings, ctx: Context, *, key: str, title: str,
              allow_summary: bool = False) -> SectionResult:
    """Fetch, rank and render a list of RSS feeds configured under settings[key].
    Shared by 'SA economy' headlines and 'AI updates'; only the config and heading differ."""
    cfg = settings[key]
    feeds = [Feed.from_config(f) for f in cfg["feeds"] if f.get("enabled", True)]
    if not feeds:
        raise DataError(f"no enabled feeds in [[{key}.feeds]]")
    patterns = compile_keywords(cfg["keywords"])
    exclude = cfg.get("exclude_phrases", [])
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
            score = score_item(item, patterns, exclude)
            if feed.keyword_only and not title_matches(item, patterns, exclude):
                continue   # a keyword buried in the summary isn't enough for a general-interest feed
            source = feed.name
            if feed.split_publisher:
                new_title, publisher = split_publisher(item.title)
                if publisher:
                    item, source = FeedItem(new_title, item.link, item.published, item.summary), publisher
            candidates.append(Candidate(item, source, score + feed.priority, order))

    if len(failures) == len(feeds):
        raise DataError("all feeds failed: " + "; ".join(f"{k} ({v})" for k, v in failures.items()))

    chosen = select(candidates, max_items=cfg.get("max_items", 4),
                    max_per_source=cfg.get("max_per_source", 2),
                    threshold=cfg.get("similarity", 0.5))
    detail = "; ".join(f"{k} ({v})" for k, v in failures.items())
    briefing_lines, briefing_problem = (None, "")
    if allow_summary:
        pool = select(candidates, max_items=BRIEFING_INPUT_ITEMS, max_per_source=BRIEFING_INPUT_ITEMS,
                      threshold=cfg.get("similarity", 0.5))
        briefing_lines, briefing_problem = _maybe_brief(settings, pool)
    if briefing_problem:
        detail = "; ".join(filter(None, [detail, briefing_problem]))

    if briefing_lines:   # a few plain sentences; optionally the top N source links underneath
        n_links = settings.get("summary", {}).get("links", 0)
        lines = [f"• {esc(line)}" for line in briefing_lines]
        lines += [render_headline(c).replace("• ", "↳ ", 1) for c in chosen[:n_links]]
        trimmable = 0
    else:
        lines = [render_headline(c) for c in chosen] or ["No recent items."]
        trimmable = max(0, len(chosen) - MIN_ITEMS)   # spec: always keep at least 3 if we have them
    result = SectionResult(key, title, lines, status=PARTIAL if detail else OK, detail=detail)
    result.heading = f"<b>{esc(title)}</b>"
    result.trimmable = trimmable
    return result
