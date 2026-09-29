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
ORDER = ["Tuesday 29 September 2026", "<b>Durban</b>", "<b>Rand</b>", "<b>Markets</b>",
         "<b>YouTube</b>", "<b>SA economy</b>", "<b>Watch today:</b>"]


class ThreeChannels(FakeSource):
    def fetch_reports(self, channels, ctx):
        return [report(name=f"Channel {i}") for i in range(3)]      # worst case: 2 lines each


def stub_everything(monkeypatch, settings, tmp_path):
    monkeypatch.setattr(weather, "fetch_forecast", lambda cfg: load_fixture("open_meteo_durban.json"))
    monkeypatch.setattr(fx, "fetch_series", lambda cfg, base, today: payload(base, series_for(base)))
    monkeypatch.setattr(markets, "yahoo_history", lambda symbol: FRESH[symbol])
    now = make_ctx(TODAY).now
    items = [FeedItem(f"Distinct economy story {n} about {topic}", f"https://x.co.za/{n}/", now - timedelta(hours=n), "")
             for n, topic in enumerate(["repo rate", "inflation", "fuel price", "the rand", "load shedding", "banks"], 1)]
    monkeypatch.setattr(headlines, "fetch_feed", lambda feed, cfg: items)
    monkeypatch.setitem(SOURCES, "three", ThreeChannels)
    events = tmp_path / "events.toml"
    events.write_text(f'[[event]]\ndate = "{TODAY}"\ntext = "CPI inflation release"\n', encoding="utf-8")
    settings["youtube"].update(source="three", channels=[{"id": "UC" + "a" * 22}])
    settings["headlines"].update(max_items=5, max_per_source=5)
    settings["headlines"]["feeds"] = [{"name": "Feed", "url": "https://x.co.za/feed"}]
    settings["watch"]["file"] = str(events)


def test_full_message_has_every_section_in_spec_order_within_the_line_budget(monkeypatch, settings, tmp_path):
    stub_everything(monkeypatch, settings, tmp_path)
    message, results = morning_brief.build_message(settings, make_ctx(TODAY).now)
    lines = message.splitlines()
    positions = [next(i for i, l in enumerate(lines) if marker in l) for marker in ORDER]
    assert positions == sorted(positions)
    assert len(lines) <= 30, f"{len(lines)} lines:\n{message}"
    assert len(message) < 4096
    assert all(r.status == "ok" for r in results), [(r.key, r.detail) for r in results]


def test_youtube_block_stays_under_eight_lines_in_the_full_message(monkeypatch, settings, tmp_path):
    stub_everything(monkeypatch, settings, tmp_path)
    message, _ = morning_brief.build_message(settings, make_ctx(TODAY).now)
    lines = [l for l in message.splitlines()]
    start = next(i for i, l in enumerate(lines) if "<b>YouTube</b>" in l)
    end = next(i for i, l in enumerate(lines) if "<b>SA economy</b>" in l)
    assert len([l for l in lines[start:end] if l]) <= 7


@pytest.mark.parametrize("dead", ["weather", "fx", "markets", "youtube", "headlines", "watch"])
def test_any_single_source_failing_still_sends_the_other_five(monkeypatch, settings, tmp_path, dead):
    stub_everything(monkeypatch, settings, tmp_path)

    def boom(*_a, **_k):
        raise ConnectionError("source down")

    target = {"weather": (weather, "fetch_forecast"), "fx": (fx, "fetch_series"),
              "markets": (markets, "yahoo_history"), "headlines": (headlines, "fetch_feed"),
              "youtube": (ThreeChannels, "fetch_reports"), "watch": (watch, "load_events")}[dead]
    monkeypatch.setattr(*target, boom)
    message, results = morning_brief.build_message(settings, make_ctx(TODAY).now)
    failed = [r for r in results if r.status == "failed"]
    assert [r.key for r in failed] == [dead]
    assert message.count("unavailable") == 1
    assert "sections failed" not in message              # 1 of 6 is well under half
    assert len([r for r in results if r.status == "ok"]) == 5
