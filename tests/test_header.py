from datetime import date

from brief import header
from brief.header import build_header


def test_plain_day():
    assert build_header(date(2026, 9, 29)) == "<b>Tuesday 29 September 2026</b>"


def test_public_holiday_is_named():
    assert build_header(date(2026, 9, 24)) == \
        "<b>Thursday 24 September 2026</b> · Public holiday: Heritage Day"


def test_observed_holiday_and_election_day():
    assert "Public holiday: National Women's Day (observed)" in build_header(date(2026, 8, 10))
    assert "Local Government Elections" in build_header(date(2026, 11, 4))


def test_a_lookup_failure_never_breaks_the_header(monkeypatch):
    def boom(_d):
        raise RuntimeError("holidays package broke")

    monkeypatch.setattr(header, "za_holiday_name", boom)
    assert build_header(date(2026, 9, 24)) == "<b>Thursday 24 September 2026</b>"
