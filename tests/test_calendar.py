from datetime import date

from brief.jse_calendar import JSECalendar, SessionCalendar


def test_weekend_and_holiday_reasons():
    cal = JSECalendar()
    assert cal.closed_reason(date(2026, 9, 27)) == "Sunday"
    assert cal.closed_reason(date(2026, 9, 24)) == "Heritage Day"
    assert cal.closed_reason(date(2026, 9, 25)) is None


def test_previous_session_skips_weekend_and_holiday():
    cal = JSECalendar()
    assert cal.previous_session(date(2026, 9, 25)) == date(2026, 9, 23)   # Heritage Day Thu
    assert cal.previous_session(date(2026, 9, 28)) == date(2026, 9, 25)   # Sat/Sun
    assert cal.previous_session(date(2026, 11, 5)) == date(2026, 11, 3)   # election holiday Wed


def test_observed_holiday_when_it_falls_on_a_sunday():
    assert JSECalendar().closed_reason(date(2026, 8, 10)) is not None   # Women's Day observed


def test_extra_closures_are_honoured():
    cal = JSECalendar([date(2026, 9, 28)])
    assert cal.closed_reason(date(2026, 9, 28)) == "market closure"


def test_futures_calendar_only_skips_weekends():
    cal = SessionCalendar()
    assert cal.is_open(date(2026, 9, 24))          # a SA holiday is irrelevant to Brent
    assert cal.previous_session(date(2026, 9, 28)) == date(2026, 9, 25)
