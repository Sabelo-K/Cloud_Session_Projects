from brief.runner import Section, SectionResult
from jobs import morning_brief


def fake_sections(monkeypatch, *, fail=False):
    def run(settings, ctx):
        if fail:
            raise RuntimeError("down")
        return SectionResult("weather", "Durban", ["sunny"])

    monkeypatch.setattr(morning_brief, "SECTIONS", [Section("weather", "Durban", run)])


def test_dry_run_prints_and_needs_no_credentials(monkeypatch, capsys):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    fake_sections(monkeypatch)
    assert morning_brief.main(["--dry-run", "--date", "2026-09-29"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("<b>Tuesday 29 September 2026</b>") and "sunny" in out


def test_send_uses_secrets_from_the_environment(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "tok")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")
    sent = {}
    monkeypatch.setattr(morning_brief, "send_message",
                        lambda text, token, chat: sent.update(text=text, token=token, chat=chat))
    fake_sections(monkeypatch)
    assert morning_brief.main(["--date", "2026-09-29"]) == 0
    assert (sent["token"], sent["chat"]) == ("tok", "42")


def test_message_is_sent_even_when_every_section_fails(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "tok")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")
    sent = {}
    monkeypatch.setattr(morning_brief, "send_message", lambda text, token, chat: sent.update(text=text))
    fake_sections(monkeypatch, fail=True)
    assert morning_brief.main(["--date", "2026-09-29"]) == 0
    assert "unavailable" in sent["text"] and "1 of 1 sections failed" in sent["text"]


def test_missing_credentials_exit_nonzero_so_the_workflow_goes_red(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    monkeypatch.setattr(morning_brief, "load_dotenv", lambda: None)
    fake_sections(monkeypatch)
    assert morning_brief.main(["--date", "2026-09-29"]) == 1
