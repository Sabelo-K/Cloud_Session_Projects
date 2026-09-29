from datetime import timedelta

import pytest

from brief.rss import FeedItem
from brief.runner import OK, PARTIAL
from brief.sections import headlines
from brief.sections.headlines import Candidate, compile_keywords, score_item, select, similar
from brief.util import DataError
from tests.conftest import make_ctx

NOW = make_ctx("2026-09-29").now


def item(title, hours_ago=5, summary="", link=None):
    return FeedItem(title, link or f"https://x.co.za/{abs(hash(title))}/",
                    None if hours_ago is None else NOW - timedelta(hours=hours_ago), summary)


def settings_with(feeds, **overrides):
    cfg = {"keywords": ["repo rate", "inflation", "fuel price", "rand", "bank", "load shedding"],
           "max_items": 4, "max_per_source": 2, "max_age_hours": 48, "similarity": 0.5,
           "feeds": feeds, **overrides}
    return {"headlines": cfg}


def stub_feeds(monkeypatch, by_name):
    def fake(feed, cfg):
        value = by_name[feed.name]
        if isinstance(value, Exception):
            raise value
        return value

    monkeypatch.setattr(headlines, "fetch_feed", fake)


FEED_A = {"name": "A", "url": "https://a.example/feed"}
FEED_B = {"name": "B", "url": "https://b.example/feed"}


# --- keywords ---------------------------------------------------------------------------------

@pytest.mark.parametrize("keyword, text, expected", [
    ("load shedding", "Stage 2 load-shedding tonight", True),
    ("load shedding", "Load Shedding returns", True),
    ("bank", "Banks post record profits", True),
    ("bank", "Nedbank results", False),          # whole words only
    ("rand", "Rand firms against the dollar", True),
    ("rand", "Randburg road closures", False),
    ("cpi", "CPI slows to 4.4%", True),
])
def test_keyword_matching(keyword, text, expected):
    (pattern,) = compile_keywords([keyword])
    assert bool(pattern.search(text)) is expected


def test_title_hits_outweigh_summary_hits():
    pats = compile_keywords(["repo rate", "inflation"])
    assert score_item(item("Repo rate decision"), pats) == 3
    assert score_item(item("Markets wrap", summary="talk of inflation"), pats) == 1
    assert score_item(item("Repo rate and inflation", summary="inflation"), pats) == 6


# --- duplicates ---------------------------------------------------------------------------------

def test_same_story_from_two_outlets_is_a_duplicate():
    assert similar("Sarb ups repo rate to 7.25%", "SARB raises repo rate to 7.25%", 0.5)


def test_different_stories_are_not_duplicates():
    assert not similar("Sarb ups repo rate to 7.25%", "Rand firms as Sarb hikes", 0.5)
    assert not similar("Fuel price to rise in October", "Fuel price to fall in December", 0.5)


# --- selection ----------------------------------------------------------------------------------

def cands(*specs):
    return [Candidate(item(t, h), src, score, i) for i, (t, src, score, h) in enumerate(specs)]


def test_higher_score_wins_then_newer():
    chosen = select(cands(("Old but relevant", "A", 6, 30), ("New but bland", "A", 0, 1),
                          ("Fresh and relevant", "B", 6, 2)),
                    max_items=3, max_per_source=5, threshold=0.5)
    assert [c.item.title for c in chosen] == ["Fresh and relevant", "Old but relevant", "New but bland"]


def test_duplicates_collapse_to_the_best_ranked():
    chosen = select(cands(("Sarb ups repo rate to 7.25%", "A", 3, 5),
                          ("SARB raises repo rate to 7.25%", "B", 9, 5)),
                    max_items=4, max_per_source=2, threshold=0.5)
    assert [c.source for c in chosen] == ["B"]


def test_one_outlet_cannot_fill_the_list():
    chosen = select(cands(*[(f"Distinct story number {n} {'xyz'*n}", "A", 3, n) for n in range(1, 6)],
                          ("Another outlet story about mining", "B", 0, 40)),
                    max_items=4, max_per_source=2, threshold=0.5)
    assert [c.source for c in chosen].count("A") == 2 and "B" in [c.source for c in chosen]


# --- the section ----------------------------------------------------------------------------------

def test_run_renders_headline_and_link_only(monkeypatch):
    stub_feeds(monkeypatch, {"A": [item("Repo rate held at 7.25%", link="https://a.example/x?a=1&b=2",
                                        summary="SECRET BODY TEXT")]})
    result = headlines.run(settings_with([FEED_A]), make_ctx("2026-09-29"))
    assert result.status == OK
    assert result.render() == ["<b>SA economy</b>",
                               '• <a href="https://a.example/x?a=1&amp;b=2">Repo rate held at 7.25%</a> · A']
    assert "SECRET" not in "".join(result.render())


def test_titles_are_html_escaped_and_long_ones_shortened(monkeypatch):
    stub_feeds(monkeypatch, {"A": [item('Rand <script>alert(1)</script> & "co" ' + "x" * 200)]})
    (line,) = headlines.run(settings_with([FEED_A]), make_ctx("2026-09-29")).lines
    assert "<script>" not in line and "&lt;script&gt;" in line and "&amp;" in line
    assert "…</a>" in line


def test_old_items_dropped_undated_kept_and_bad_links_ignored(monkeypatch):
    stub_feeds(monkeypatch, {"A": [item("Ancient bank news", hours_ago=100),
                                   item("Undated bank news", hours_ago=None),
                                   item("Bank news with bad link", link="javascript:alert(1)"),
                                   item("Bank news with ftp link", link="ftp://x/y")]})
    result = headlines.run(settings_with([FEED_A]), make_ctx("2026-09-29"))
    assert [l for l in result.lines if "Undated" in l] and len(result.lines) == 1


def test_keyword_only_feed_drops_unrelated_items(monkeypatch):
    stub_feeds(monkeypatch, {"A": [item("Celebrity wedding"), item("Inflation slows")]})
    result = headlines.run(settings_with([{**FEED_A, "keyword_only": True}]), make_ctx("2026-09-29"))
    assert len(result.lines) == 1 and "Inflation slows" in result.lines[0]


def test_keyword_only_feed_needs_the_keyword_in_the_title_not_just_the_summary(monkeypatch):
    stub_feeds(monkeypatch, {"A": [item("Woman murdered in Ekurhuleni", summary="police at the bank"),
                                   item("Bank profits jump")]})
    result = headlines.run(settings_with([{**FEED_A, "keyword_only": True}]), make_ctx("2026-09-29"))
    assert len(result.lines) == 1 and "Bank profits" in result.lines[0]


def test_per_feed_user_agent_overrides_the_default(monkeypatch):
    seen = {}
    monkeypatch.setattr(headlines, "get_bytes", lambda url, headers, **kw: seen.update(headers) or b"<rss/>")
    monkeypatch.setattr(headlines, "parse_feed", lambda data: [])
    headlines.fetch_feed(headlines.Feed("A", "https://a.example/f", user_agent="Custom/1"), {"user_agent": "Default/1"})
    assert seen["User-Agent"] == "Custom/1"
    headlines.fetch_feed(headlines.Feed("A", "https://a.example/f"), {"user_agent": "Default/1"})
    assert seen["User-Agent"] == "Default/1"


def test_place_names_containing_a_keyword_are_excluded(monkeypatch):
    stub_feeds(monkeypatch, {"A": [item("EAST RAND murders: what we know"), item("Rand firms against the dollar")]})
    cfg = settings_with([{**FEED_A, "keyword_only": True}])
    cfg["headlines"]["exclude_phrases"] = ["east rand"]
    result = headlines.run(cfg, make_ctx("2026-09-29"))
    assert len(result.lines) == 1 and "Rand firms" in result.lines[0]


def test_aggregator_publisher_suffix_becomes_the_source(monkeypatch):
    stub_feeds(monkeypatch, {"A": [item("Sarb ups repo rate to 7.25% - Business Day"),
                                   item("Rand firms - a very long tail that is clearly not a publisher name at all")]})
    result = headlines.run(settings_with([{**FEED_A, "split_publisher": True}]), make_ctx("2026-09-29"))
    assert any("Sarb ups repo rate to 7.25%</a> · Business Day" in l for l in result.lines)
    assert any("Rand firms - a very long tail" in l and l.endswith("· A") for l in result.lines)


def test_business_feed_fills_with_unmatched_items_after_matched(monkeypatch):
    stub_feeds(monkeypatch, {"A": [item("Mining output edges up", hours_ago=1), item("Bank profits jump", hours_ago=9)]})
    result = headlines.run(settings_with([FEED_A]), make_ctx("2026-09-29"))
    assert ["Bank profits" in result.lines[0], "Mining" in result.lines[1]] == [True, True]


def test_priority_boosts_a_feed(monkeypatch):
    stub_feeds(monkeypatch, {"A": [item("Bank profits jump")], "B": [item("Mining output edges up")]})
    result = headlines.run(settings_with([FEED_A, {**FEED_B, "priority": 10}]), make_ctx("2026-09-29"))
    assert "Mining" in result.lines[0]


def test_a_dead_feed_only_costs_its_own_items(monkeypatch):
    stub_feeds(monkeypatch, {"A": ConnectionError("dns failure"), "B": [item("Bank profits jump")]})
    result = headlines.run(settings_with([FEED_A, FEED_B]), make_ctx("2026-09-29"))
    assert result.status == PARTIAL and len(result.lines) == 1
    assert "A (ConnectionError: dns failure)" in result.detail


def test_all_feeds_failing_raises(monkeypatch):
    stub_feeds(monkeypatch, {"A": ConnectionError("x"), "B": DataError("not valid RSS/Atom XML")})
    with pytest.raises(DataError, match="all feeds failed"):
        headlines.run(settings_with([FEED_A, FEED_B]), make_ctx("2026-09-29"))


def test_disabled_feeds_are_not_fetched(monkeypatch):
    stub_feeds(monkeypatch, {"B": [item("Bank profits jump")]})   # "A" would KeyError if fetched
    result = headlines.run(settings_with([{**FEED_A, "enabled": False}, FEED_B]), make_ctx("2026-09-29"))
    assert result.status == OK and len(result.lines) == 1


def test_no_enabled_feeds_is_an_error(monkeypatch):
    with pytest.raises(DataError, match="no enabled feeds"):
        headlines.run(settings_with([{**FEED_A, "enabled": False}]), make_ctx("2026-09-29"))


def test_nothing_recent_says_so_instead_of_an_empty_section(monkeypatch):
    stub_feeds(monkeypatch, {"A": [item("Ancient", hours_ago=500)]})
    result = headlines.run(settings_with([FEED_A]), make_ctx("2026-09-29"))
    assert result.status == OK and result.lines == ["No recent items."]


def test_the_shipped_config_only_enables_feeds_with_real_urls(settings):
    for feed in settings["headlines"]["feeds"]:
        if feed.get("enabled", True):
            assert feed["url"].startswith("https://") and "rss-feeds" not in feed["url"]
