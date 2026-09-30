import pytest

from jobs import morning_brief
from brief.runner import Section, SectionResult


@pytest.fixture
def env(monkeypatch, tmp_path):
    marker = tmp_path / "last_sent.txt"
    settings = {"brief": {"last_sent_file": str(marker)}}       # absolute path wins over ROOT
    monkeypatch.setattr(morning_brief, "load_settings", lambda: settings)
    monkeypatch.setattr(morning_brief, "load_dotenv", lambda: None)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "tok")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")
    monkeypatch.setattr(morning_brief, "SECTIONS", [Section("weather", "W", lambda s, c: SectionResult("weather", "W", ["ok"]))])
    sent = []
    monkeypatch.setattr(morning_brief, "send_message", lambda text, token, chat: sent.append(text))
    return marker, sent


def test_a_real_send_records_the_day(env):
    marker, sent = env
    assert morning_brief.main(["--date", "2026-09-30"]) == 0
    assert len(sent) == 1 and marker.read_text().strip() == "2026-09-30"


def test_backup_run_stays_silent_when_today_was_already_sent(env):
    marker, sent = env
    marker.write_text("2026-09-30\n")
    assert morning_brief.main(["--skip-if-sent-today", "--date", "2026-09-30"]) == 0
    assert sent == []


def test_backup_run_sends_when_only_yesterday_was_recorded(env):
    marker, sent = env
    marker.write_text("2026-09-29\n")
    assert morning_brief.main(["--skip-if-sent-today", "--date", "2026-09-30"]) == 0
    assert len(sent) == 1 and marker.read_text().strip() == "2026-09-30"


def test_backup_run_sends_when_there_is_no_marker_at_all(env):
    marker, sent = env
    assert morning_brief.main(["--skip-if-sent-today", "--date", "2026-09-30"]) == 0 and len(sent) == 1


def test_a_manual_run_always_sends_even_if_today_was_recorded(env):
    marker, sent = env
    marker.write_text("2026-09-30\n")
    assert morning_brief.main(["--date", "2026-09-30"]) == 0 and len(sent) == 1


def test_dry_runs_never_touch_the_marker(env, capsys):
    marker, sent = env
    assert morning_brief.main(["--dry-run", "--date", "2026-09-30"]) == 0
    assert not marker.exists() and sent == []


def test_a_failed_send_does_not_record_the_day(env, monkeypatch):
    marker, _ = env
    from brief.telegram import TelegramError

    def boom(text, token, chat):
        raise TelegramError("down")

    monkeypatch.setattr(morning_brief, "send_message", boom)
    assert morning_brief.main(["--date", "2026-09-30"]) == 1 and not marker.exists()
