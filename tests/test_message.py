"""End-to-end assembly with every source stubbed by fixture data: order, budget, isolation."""
from datetime import timedelta

import pytest

from brief.rss import FeedItem
from brief.sections import fx, headlines, markets, watch, weather
from brief.youtube import SOURCES
from jobs import morning_brief
from tests.conftest import load_fixture, make_ctx
from tests.test_fx import payload, series_for
from tests.test_markets import FRESH
from tests.test_youtube import FakeSource, report

TODAY = "2026-09-29"                     # a normal Tuesday: JSE open yesterday
ORDER = ["Tuesday 29 September 2026", "<b>Durban</b>", "<b>Rand</b>", "<b>AI updates</b>",
         "<b>YouTube</b>", "<b>SA economy</b>", "<b>Watch today:</b>"]      # markets are off by default


class ThreeChannels(FakeSource):
    def fetch_reports(self, channels, ctx):
        return [report(name=f"Channel {i}") for i in range(3)]      # worst case: 2 lines each


def stub_everything(monkeypatch, settings, tmp_path, *, markets_on=False, dead_feeds=()):
    """Every source returns fixture data. Feeds are told apart by name: 'SAFeed' for the SA economy
    headlines, 'AIFeed' for AI updates; names in `dead_feeds` raise instead."""
    monkeypatch.setattr(weather, "fetch_forecast", lambda cfg: load_fixture("open_meteo_durban.json"))
    monkeypatch.setattr(fx, "fetch_series", lambda cfg, base, today: payload(base, series_for(base)))
    monkeypatch.setattr(markets, "yahoo_history", lambda symbol: FRESH[symbol])
    now = make_ctx(TODAY).now
    sa = [FeedItem(f"Distinct economy story {n} about {topic}", f"https://x.co.za/sa{n}/", now - timedelta(hours=n), "")
          for n, topic in enumerate(["repo rate", "inflation", "fuel price", "the rand", "load shedding", "banks"], 1)]
    ai_titles = ["OpenAI ships a faster reasoning model", "Google DeepMind unveils protein design system",
                 "Nvidia announces new datacentre chips for AI", "Anthropic details agent safety research",
                 "Hugging Face open-sources speech recognition weights", "Meta trains Llama on robotics data"]
    ai = [FeedItem(t, f"https://x.co.za/ai{n}/", now - timedelta(hours=n), "") for n, t in enumerate(ai_titles, 1)]

    def fake_fetch(feed, cfg):
        if feed.name in dead_feeds:
            raise ConnectionError("feed down")
        return sa if feed.name == "SAFeed" else ai

    monkeypatch.setattr(headlines, "fetch_feed", fake_fetch)
    monkeypatch.setitem(SOURCES, "three", ThreeChannels)
    events = tmp_path / "events.toml"
    events.write_text(f'[[event]]\ndate = "{TODAY}"\ntext = "CPI inflation release"\n', encoding="utf-8")
    settings["youtube"].update(source="three", channels=[{"id": "UC" + "a" * 22}])
    settings["headlines"].update(max_items=5, max_per_source=5, feeds=[{"name": "SAFeed", "url": "https://x.co.za/f"}])
    settings["ai_news"].update(max_items=5, max_per_source=5, feeds=[{"name": "AIFeed", "url": "https://x.co.za/a"}])
    settings["markets"]["enabled"] = markets_on
    settings["watch"]["file"] = str(events)


def test_default_config_replaces_markets_with_ai_updates(settings):
    assert settings["markets"]["enabled"] is False and settings["ai_news"]["enabled"] is True


def test_full_message_has_every_section_in_order_within_the_line_budget(monkeypatch, settings, tmp_path):
    stub_everything(monkeypatch, settings, tmp_path)
    message, results = morning_brief.build_message(settings, make_ctx(TODAY).now)
    lines = message.splitlines()
    positions = [next(i for i, l in enumerate(lines) if marker in l) for marker in ORDER]
    assert positions == sorted(positions)
    assert len(lines) <= 30, f"{len(lines)} lines:\n{message}"
    assert len(message) < 4096 and "Markets" not in message and "Brent" not in message
    assert all(r.status == "ok" for r in results), [(r.key, r.detail) for r in results]


def test_news_is_plain_text_by_default_with_the_source_name(monkeypatch, settings, tmp_path):
    stub_everything(monkeypatch, settings, tmp_path)
    message, _ = morning_brief.build_message(settings, make_ctx(TODAY).now)
    news = [l for l in message.splitlines() if l.endswith(("· AIFeed", "· SAFeed"))]
    assert news and not any("<a " in l or "http" in l for l in news)   # nothing to tap or click (YouTube's own-video link is separate)
    ai_lines = [l for l in message.splitlines() if l.endswith("· AIFeed")]
    assert len(ai_lines) == 5 and all(l.startswith("• ") for l in ai_lines)
    assert any(l.endswith("· SAFeed") for l in message.splitlines())


def test_links_can_be_switched_back_on(monkeypatch, settings, tmp_path):
    stub_everything(monkeypatch, settings, tmp_path)
    settings["ai_news"]["show_links"] = True
    message, _ = morning_brief.build_message(settings, make_ctx(TODAY).now)
    assert any(l.startswith("• <a href=") and l.endswith("· AIFeed") for l in message.splitlines())


def test_markets_can_be_switched_back_on_in_the_same_spot(monkeypatch, settings, tmp_path):
    stub_everything(monkeypatch, settings, tmp_path, markets_on=True)
    message, results = morning_brief.build_message(settings, make_ctx(TODAY).now)
    lines = message.splitlines()
    rand = next(i for i, l in enumerate(lines) if "<b>Rand</b>" in l)
    mk = next(i for i, l in enumerate(lines) if "<b>Markets</b>" in l)
    ai = next(i for i, l in enumerate(lines) if "<b>AI updates</b>" in l)
    assert rand < mk < ai and any(l.startswith("Brent") for l in lines)
    assert len(lines) <= 33   # worst case (3 channels, everything on): both news lists trimmed to their 3-item floor; ~30 is soft


def test_youtube_block_stays_under_eight_lines_in_the_full_message(monkeypatch, settings, tmp_path):
    stub_everything(monkeypatch, settings, tmp_path)
    message, _ = morning_brief.build_message(settings, make_ctx(TODAY).now)
    lines = message.splitlines()
    start = next(i for i, l in enumerate(lines) if "<b>YouTube</b>" in l)
    end = next(i for i, l in enumerate(lines) if "<b>SA economy</b>" in l)
    assert len([l for l in lines[start:end] if l]) <= 7


KILLERS = {"weather": (weather, "fetch_forecast"), "fx": (fx, "fetch_series"),
           "youtube": (ThreeChannels, "fetch_reports"), "watch": (watch, "load_events")}
FEED_KILLERS = {"headlines": "SAFeed", "ai_news": "AIFeed"}


@pytest.mark.parametrize("dead", ["weather", "fx", "youtube", "headlines", "ai_news", "watch"])
def test_any_single_source_failing_still_sends_the_other_five(monkeypatch, settings, tmp_path, dead):
    stub_everything(monkeypatch, settings, tmp_path, dead_feeds=(FEED_KILLERS.get(dead),))

    def boom(*_a, **_k):
        raise ConnectionError("source down")

    if dead in KILLERS:
        monkeypatch.setattr(*KILLERS[dead], boom)
    message, results = morning_brief.build_message(settings, make_ctx(TODAY).now)
    failed = [r for r in results if r.status == "failed"]
    assert [r.key for r in failed] == [dead]
    assert message.count("unavailable") == 1
    assert "sections failed" not in message              # 1 of 6 is well under half
    assert len([r for r in results if r.status == "ok"]) == 5
