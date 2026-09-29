"""Failure handling: hangs, cascading failures, budgets, and every combination of dead sources."""
import itertools
import threading
from html.parser import HTMLParser

import pytest

from brief.runner import FAILED, OK, PARTIAL, Section, SectionResult, assemble, run_sections
from brief.sections import fx, headlines, markets, watch, weather
from jobs import morning_brief
from tests.conftest import make_ctx
from tests.test_fx import payload
from tests.test_markets import FRESH, stub
from tests.test_message import ThreeChannels, TODAY, stub_everything  # noqa: F401 (registers "three")


def bars_for(last_day):
    from datetime import date, timedelta
    end = date.fromisoformat(last_day)
    return [(end - timedelta(days=3), 4100.0), (end, 4150.0)]


# --- hung sources ---------------------------------------------------------------------------------

def test_a_hung_section_is_abandoned_and_the_rest_still_run():
    release = threading.Event()

    def hangs(settings, ctx):
        release.wait(30)                       # simulates a source that never answers
        return SectionResult("slow", "Slow", ["never shown"])

    sections = [Section("a", "A", lambda s, c: SectionResult("a", "A", ["a ok"])),
                Section("slow", "Slow", hangs),
                Section("c", "C", lambda s, c: SectionResult("c", "C", ["c ok"]))]
    try:
        results = run_sections(sections, {"brief": {"section_timeout_seconds": 0.2}}, make_ctx(TODAY))
    finally:
        release.set()
    assert [r.status for r in results] == [OK, FAILED, OK]
    assert "timed out after 0.2s" in results[1].detail and results[1].render()[-1] == "unavailable"


def test_exceptions_still_propagate_through_the_timeout_wrapper():
    def boom(settings, ctx):
        raise KeyError("missing setting")

    (result,) = run_sections([Section("x", "X", boom)], {}, make_ctx(TODAY))
    assert result.status == FAILED and "KeyError" in result.detail


# --- Yahoo cascading failure -------------------------------------------------------------------------

def test_three_consecutive_failures_skip_the_rest_quickly(monkeypatch, settings):
    calls = stub(monkeypatch, FRESH, fail=set(FRESH))
    with pytest.raises(Exception, match="all 8 instruments failed"):
        markets.run(settings, make_ctx(TODAY))
    assert len(calls) == 3                     # not 8: the breaker tripped


def test_a_success_resets_the_failure_streak(monkeypatch, settings):
    fail = {"^J200.JO", "SBK.JO", "ABG.JO", "NED.JO"}      # never 3 in a row
    calls = stub(monkeypatch, FRESH, fail=fail)
    result = markets.run(settings, make_ctx(TODAY))
    assert len(calls) == 8 and result.status == PARTIAL
    assert sum(l.endswith("unavailable") for l in result.lines) == 4


def test_skipped_tickers_say_why_in_the_log_detail(monkeypatch, settings):
    stub(monkeypatch, FRESH, fail={"^J200.JO", "SBK.JO", "FSR.JO"})
    with pytest.raises(Exception) as err:                       # all Yahoo, so the section fails
        markets.run(settings, make_ctx(TODAY))
    assert "ABG.JO skipped after 3 consecutive failures (Yahoo looks down)" in str(err.value)


def test_time_budget_stops_further_fetches(monkeypatch, settings):
    settings["markets"]["budget_seconds"] = 10
    ticks = iter([0, 0, 11, 11, 11, 11, 11, 11, 11, 11, 11])   # clock jumps past the budget
    monkeypatch.setattr(markets.time, "monotonic", lambda: next(ticks))
    calls = stub(monkeypatch, FRESH)
    result = markets.run(settings, make_ctx(TODAY))
    assert len(calls) == 1 and result.status == PARTIAL and "time budget" in result.detail


def test_a_missing_newest_bar_is_retried_once_and_the_fresh_one_used(monkeypatch, settings):
    monday = bars_for("2026-09-28")
    stale = bars_for("2026-09-25")
    answers = {"GC=F": [stale, monday]}
    calls = []

    def fake(symbol):
        calls.append(symbol)
        return answers[symbol].pop(0) if symbol in answers and answers[symbol] else FRESH[symbol]

    monkeypatch.setattr(markets, "yahoo_history", fake)
    monkeypatch.setattr(markets.time, "sleep", lambda _s: None)
    result = markets.run(settings, make_ctx(TODAY))
    assert calls.count("GC=F") == 2
    assert not any("not updated" in l for l in result.lines)


def test_a_bar_that_stays_missing_is_labelled_stale_after_the_retry(monkeypatch, settings):
    stale = bars_for("2026-09-25")
    monkeypatch.setattr(markets, "yahoo_history", lambda s: stale if s == "GC=F" else FRESH[s])
    monkeypatch.setattr(markets.time, "sleep", lambda _s: None)
    result = markets.run(settings, make_ctx(TODAY))
    assert any(l.startswith("Gold") and "not updated" in l for l in result.lines)


# --- stale ECB data ------------------------------------------------------------------------------------

def test_stuck_ecb_feed_is_flagged_as_stale(monkeypatch, settings):
    old = {"2026-09-18": 17.0, "2026-09-21": 17.1}
    monkeypatch.setattr(fx, "fetch_series", lambda cfg, base, today: payload(base, old))
    result = fx.run(settings, make_ctx(TODAY))
    assert result.status == PARTIAL and "(stale: 8 days old)" in result.heading


def test_a_normal_weekend_gap_is_not_stale(monkeypatch, settings):
    fresh = {"2026-09-24": 17.0, "2026-09-25": 17.1}          # Friday rates, read on Monday
    monkeypatch.setattr(fx, "fetch_series", lambda cfg, base, today: payload(base, fresh))
    result = fx.run(settings, make_ctx("2026-09-28"))
    assert result.status == OK and "stale" not in result.heading


# --- line budget -------------------------------------------------------------------------------------

def sect(key, n, trimmable=0):
    return SectionResult(key, key, [f"{key} line {i}" for i in range(n)], trimmable=trimmable)


def test_over_budget_trims_headlines_but_never_below_three():
    results = [sect("a", 20), sect("news", 5, trimmable=2)]      # 1 + 21 + 6 = 28 without blanks
    assert len(assemble("H", results, max_lines=26).splitlines()) == 26
    text = assemble("H", results, max_lines=10)
    assert text.count("news line") == 3                         # floor of 3 respected, even if still long


def test_blank_lines_and_trimming_are_not_used_when_everything_fits():
    results = [sect("a", 2), sect("news", 5, trimmable=2)]
    assert assemble("H", results, max_lines=30).count("\n\n") == 2


def test_warning_line_survives_trimming():
    dead = [SectionResult(k, k, ["unavailable"], status=FAILED) for k in ("x", "y")]
    text = assemble("H", [*dead, sect("news", 5, trimmable=2)], max_lines=11)
    assert text.splitlines()[-1] == "⚠️ 2 of 3 sections failed; check the workflow log."
    assert text.count("news line") == 4 and len(text.splitlines()) == 11   # 12 untrimmed, one dropped


# --- entrypoint last resorts ----------------------------------------------------------------------------

def test_a_crash_while_building_still_sends_a_short_notice(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "tok")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")
    sent = {}
    monkeypatch.setattr(morning_brief, "send_message", lambda text, token, chat: sent.update(text=text))
    monkeypatch.setattr(morning_brief, "build_message", lambda *a, **k: 1 / 0)
    assert morning_brief.main(["--date", TODAY]) == 0
    assert "could not be built" in sent["text"] and "ZeroDivisionError" in sent["text"]


def test_broken_reporting_never_blocks_the_send(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "tok")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")
    sent = {}
    monkeypatch.setattr(morning_brief, "send_message", lambda text, token, chat: sent.update(text=text))
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", "/nonexistent-dir/summary.md")
    monkeypatch.setattr(morning_brief, "SECTIONS", [Section("weather", "W", lambda s, c: SectionResult("weather", "W", ["ok"]))])
    assert morning_brief.main(["--date", TODAY]) == 0 and "ok" in sent["text"]


# --- shipped configuration -----------------------------------------------------------------------------------

def test_shipped_tickers_are_sane(settings):
    inst = settings["markets"]["instruments"]
    symbols = [i["symbol"] for i in inst]
    assert len(symbols) == len(set(symbols)) and "CPIP.JO" not in symbols
    for i in inst:
        if i["market"] == "JSE" and i["symbol"] != "^J200.JO":
            assert i["symbol"].endswith(".JO") and i["divisor"] == 100 and i["prefix"] == "R"   # cents -> Rand
        else:
            assert i.get("divisor", 1) == 1
    assert {i["label"] for i in inst} >= {"JSE Top 40", "Standard Bank", "FirstRand", "Absa", "Nedbank",
                                          "Capitec", "Brent", "Gold"}


def test_every_section_has_a_settings_table_with_an_enabled_flag(settings):
    for key in ("weather", "fx", "markets", "youtube", "headlines", "watch"):
        assert settings[key]["enabled"] in (True, False)


def test_optional_llm_summary_is_off_by_default(settings):
    assert settings["summary"]["enabled"] is False


# --- Telegram-valid HTML, and the full failure matrix -------------------------------------------------------

class TagAudit(HTMLParser):
    ALLOWED = {"b", "a"}

    def __init__(self):
        super().__init__()
        self.stack, self.problems = [], []

    def handle_starttag(self, tag, attrs):
        if tag not in self.ALLOWED:
            self.problems.append(f"disallowed <{tag}>")
        if tag == "a":
            href = dict(attrs).get("href", "")
            if not href.startswith(("http://", "https://")):
                self.problems.append(f"bad href {href!r}")
        self.stack.append(tag)

    def handle_endtag(self, tag):
        if not self.stack or self.stack.pop() != tag:
            self.problems.append(f"unbalanced </{tag}>")


def audit(message):
    parser = TagAudit()
    parser.feed(message)
    parser.close()
    return parser.problems + ([f"unclosed {parser.stack}"] if parser.stack else [])


KILLERS = {"weather": (weather, "fetch_forecast"), "fx": (fx, "fetch_series"),
           "markets": (markets, "yahoo_history"), "headlines": (headlines, "fetch_feed"),
           "youtube": (ThreeChannels, "fetch_reports"), "watch": (watch, "load_events")}


def test_message_with_hostile_text_is_valid_telegram_html(monkeypatch, settings, tmp_path):
    stub_everything(monkeypatch, settings, tmp_path)
    from brief.rss import FeedItem
    evil = FeedItem('<script>x</script> & "quotes" <b>', 'https://x.co.za/?a=1&b="2"<', make_ctx(TODAY).now, "")
    monkeypatch.setattr(headlines, "fetch_feed", lambda feed, cfg: [evil])
    message, _ = morning_brief.build_message(settings, make_ctx(TODAY).now)
    assert audit(message) == []


@pytest.mark.parametrize("dead", [c for n in range(7) for c in itertools.combinations(KILLERS, n)],
                         ids=lambda c: "+".join(c) or "none-dead")
def test_every_combination_of_dead_sources_yields_a_valid_message(monkeypatch, settings, tmp_path, dead):
    stub_everything(monkeypatch, settings, tmp_path)

    def boom(*_a, **_k):
        raise ConnectionError("source down")

    for name in dead:
        monkeypatch.setattr(*KILLERS[name], boom)
    message, results = morning_brief.build_message(settings, make_ctx(TODAY).now)
    failed = [r.key for r in results if r.status == FAILED]
    assert set(failed) == set(dead)
    assert len(message.splitlines()) <= 30 and len(message) < 4096
    assert message.startswith("<b>Tuesday 29 September 2026</b>")
    assert ("sections failed" in message) == (len(dead) * 2 > 6)      # more than half of six
    assert audit(message) == []
