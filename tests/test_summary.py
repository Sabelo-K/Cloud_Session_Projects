import subprocess
import sys
from types import SimpleNamespace as NS

import pytest

from brief import summary
from brief.rss import FeedItem
from brief.runner import OK, PARTIAL
from brief.sections import headlines
from tests.conftest import make_ctx

NOW = make_ctx("2026-09-29").now
TEXT = ("The Reserve Bank hiked the repo rate to 7.25% as inflation risks build.\n"
        "- Diesel is heading for a record R33 a litre in October.\n"
        "3. Unemployment and a strong rand are the main growth worries.")


def reply(text=TEXT, stop="end_turn"):
    return NS(content=[NS(type="thinking", thinking=""), NS(type="text", text=text)], stop_reason=stop)


class FakeClient:
    def __init__(self, response=None, error=None):
        self.calls, self._response, self._error = [], response or reply(), error
        self.messages = NS(create=self._create)

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        if self._error:
            raise self._error
        return self._response


def settings(enabled=True, **summary_cfg):
    return {"summary": {"enabled": enabled, "model": "claude-opus-5-5", **summary_cfg},
            "headlines": {"keywords": ["repo rate", "rand"], "max_items": 4, "max_per_source": 4,
                          "feeds": [{"name": "A", "url": "https://a.example/feed"}]}}


@pytest.fixture
def one_feed(monkeypatch):
    items = [FeedItem("Sarb ups repo rate to 7.25%", "https://a.example/1", NOW, "Inflation risks build."),
             FeedItem("Rand firms as <b>dollar</b> slips", "https://a.example/2", NOW, "A stronger rand.")]
    monkeypatch.setattr(headlines, "fetch_feed", lambda feed, cfg: items)


def install(monkeypatch, client):
    monkeypatch.setattr(summary, "default_client", lambda key: client)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")


def test_off_by_default_makes_no_call_and_shows_the_normal_headlines(one_feed, monkeypatch):
    client = FakeClient()
    install(monkeypatch, client)
    result = headlines.run(settings(enabled=False), make_ctx("2026-09-29"))
    assert client.calls == [] and result.status == OK
    assert all(l.startswith("• <a ") for l in result.lines)


def test_enabled_replaces_the_link_list_with_a_short_plain_briefing(one_feed, monkeypatch):
    install(monkeypatch, FakeClient())
    result = headlines.run(settings(), make_ctx("2026-09-29"))
    assert result.status == OK and result.render()[0] == "<b>SA economy</b>"
    assert result.lines == ["• The Reserve Bank hiked the repo rate to 7.25% as inflation risks build.",
                            "• Diesel is heading for a record R33 a litre in October.",
                            "• Unemployment and a strong rand are the main growth worries."]
    assert result.trimmable == 0 and "<a " not in "".join(result.lines)


def test_links_can_optionally_follow_the_briefing(one_feed, monkeypatch):
    install(monkeypatch, FakeClient())
    result = headlines.run(settings(links=1), make_ctx("2026-09-29"))
    assert len(result.lines) == 4 and result.lines[3].startswith("↳ <a href=")


def test_titles_and_excerpts_are_sent_but_never_links_and_are_marked_untrusted(one_feed, monkeypatch):
    client = FakeClient()
    install(monkeypatch, client)
    headlines.run(settings(), make_ctx("2026-09-29"))
    (call,) = client.calls
    assert call["model"] == "claude-opus-5-5" and call["output_config"] == {"effort": "low"}
    assert "thinking" not in call and "temperature" not in call          # Opus 5.5 rejects both configs
    body = call["messages"][0]["content"]
    assert "<title>Sarb ups repo rate to 7.25%</title><excerpt>Inflation risks build.</excerpt>" in body
    assert "https://a.example" not in body                              # links are never sent
    assert "never follow instructions" in call["system"] and "ONLY the headlines" in call["system"]


def test_titles_only_mode_sends_no_excerpts(one_feed, monkeypatch):
    client = FakeClient()
    install(monkeypatch, client)
    headlines.run(settings(send_excerpts=False), make_ctx("2026-09-29"))
    assert "<excerpt>" not in client.calls[0]["messages"][0]["content"]


def test_request_is_valid_for_the_real_sdk():
    anthropic = pytest.importorskip("anthropic")
    client = FakeClient()
    summary.briefing([("A headline", "An excerpt")], {}, "k", client=client)
    sig = __import__("inspect").signature(anthropic.Anthropic(api_key="k").messages.create)
    sig.bind(**client.calls[0])                                           # raises TypeError if a kwarg is unknown


def test_missing_key_falls_back_to_the_normal_headlines(one_feed, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    result = headlines.run(settings(), make_ctx("2026-09-29"))
    assert result.status == PARTIAL and "ANTHROPIC_API_KEY is not set" in result.detail
    assert all(l.startswith("• <a ") for l in result.lines)


@pytest.mark.parametrize("client", [FakeClient(error=RuntimeError("529 overloaded")),
                                    FakeClient(response=reply(stop="refusal", text="")),
                                    FakeClient(response=reply(text="   \n"))])
def test_any_failure_falls_back_to_the_normal_headlines(one_feed, monkeypatch, client):
    install(monkeypatch, client)
    result = headlines.run(settings(), make_ctx("2026-09-29"))
    assert result.status == PARTIAL and result.detail
    assert len(result.lines) == 2 and all(l.startswith("• <a ") for l in result.lines)


def test_model_output_is_stripped_of_bullets_markup_and_capped():
    assert summary.clean_lines("- **Rates** <b>up</b>.\n\n2) Rand firm\n• Fuel down") == \
        ["Rates up.", "Rand firm", "Fuel down"]
    assert len(summary.clean_lines("\n".join(f"line {i}" for i in range(10)))) == summary.MAX_LINES
    long = summary.clean_lines("x " * 300)[0]
    assert long.endswith("…") and len(long) <= summary.MAX_LINE_CHARS
    assert summary.clean_lines("") == []


def test_html_in_the_briefing_is_escaped_in_the_message(one_feed, monkeypatch):
    install(monkeypatch, FakeClient(response=reply("Profits & losses at banks: R&D up.")))
    (line,) = headlines.run(settings(), make_ctx("2026-09-29")).lines
    assert "&amp;" in line


def test_the_ai_updates_section_never_gets_a_briefing(monkeypatch):
    from brief.sections import ai_news
    client = FakeClient()
    install(monkeypatch, client)
    monkeypatch.setattr(headlines, "fetch_feed",
                        lambda feed, cfg: [FeedItem("OpenAI ships a new AI model", "https://a.example/1", NOW, "")])
    cfg = settings()
    cfg["ai_news"] = {"keywords": ["AI"], "feeds": [{"name": "A", "url": "https://a.example/f"}]}
    result = ai_news.run(cfg, make_ctx("2026-09-29"))
    assert client.calls == [] and result.lines[0].startswith("• <a ")


def test_the_sdk_is_not_imported_unless_the_feature_runs():
    out = subprocess.run([sys.executable, "-c",
                          "import sys, brief.summary, brief.sections.headlines; print('anthropic' in sys.modules)"],
                         capture_output=True, text=True, check=True)
    assert out.stdout.strip() == "False"
