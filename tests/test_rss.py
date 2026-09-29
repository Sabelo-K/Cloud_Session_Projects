from datetime import datetime, timezone

import pytest

from brief.rss import MAX_BYTES, parse_feed
from brief.util import DataError
from tests.conftest import load_text


def test_rss_items_titles_links_dates_and_summaries():
    items = {i.title: i for i in parse_feed(load_text("feed_rss.xml"))}
    assert len(items) == 4                       # the item without a link is skipped
    repo = items["Sarb ups repo rate to 7.25%"]
    assert repo.link == "https://example.co.za/news/economy/sarb-ups-repo-rate/"
    assert repo.published == datetime(2026, 9, 28, 13, 0, tzinfo=timezone.utc)
    assert repo.summary == "The Reserve Bank raised rates by 25 basis points & warned on inflation."


def test_full_article_text_is_never_extracted():
    everything = " ".join(i.summary + i.title for i in parse_feed(load_text("feed_rss.xml")))
    assert "FULL ARTICLE TEXT" not in everything


def test_double_encoded_wordpress_entities_are_decoded():
    titles = [i.title for i in parse_feed(load_text("feed_rss.xml"))]
    assert "Eskom’s winter: no load shedding in sight" in titles


def test_missing_and_bad_dates_become_none_and_naive_dates_are_utc():
    items = {i.title: i for i in parse_feed(load_text("feed_rss.xml"))}
    assert items["Undated item"].published is None
    assert items["Bad date item"].published is None
    naive = b"<rss><channel><item><title>T</title><link>https://x.co.za/</link>" \
            b"<pubDate>2026-09-28T10:00:00</pubDate></item></channel></rss>"
    assert parse_feed(naive)[0].published.tzinfo is not None


def test_atom_uses_the_alternate_link_and_updated_date():
    (item,) = parse_feed(load_text("feed_atom.xml"))
    assert item.link == "https://example.co.za/fuel-price-october/"
    assert item.published == datetime(2026, 9, 28, 13, 0, tzinfo=timezone.utc)
    assert item.summary == "Petrol and diesel fall ."


@pytest.mark.parametrize("bad, match", [
    (b"<html><body>Not a feed</body></html>", "unsupported feed root"),
    (b"this is not xml at all", "not valid"),
    (b"", "not valid"),
    (b'<!DOCTYPE r [<!ENTITY a "aaaa">]><rss><channel/></rss>', "XML entities"),
    (b"<rss>" + b"x" * MAX_BYTES + b"</rss>", "too large"),
])
def test_bad_feeds_raise_a_data_error(bad, match):
    with pytest.raises(DataError, match=match):
        parse_feed(bad)
