from datetime import date

import pytest

from brief.runner import OK, PARTIAL
from brief.sections import fx
from brief.util import DataError
from tests.conftest import load_fixture, make_ctx


def payload(base, series):
    return {"base": base, "rates": {d: {"ZAR": v} for d, v in series.items()}}


def test_parse_usd_fixture_uses_last_two_published_days():
    rate = fx.parse_series(load_fixture("frankfurter_usd_zar.json"), "USD", "ZAR")
    assert (rate.latest_date, rate.latest) == (date(2026, 9, 28), 17.85)
    assert (rate.prev_date, rate.prev) == (date(2026, 9, 25), 17.80)
    assert round(rate.change_pct, 2) == 0.28
    assert fx.render_rate(rate, date(2026, 9, 28)) == "USD/ZAR  17.85  ▲ 0.3%"


def test_line_is_labelled_when_its_date_differs_from_heading():
    rate = fx.parse_series(load_fixture("frankfurter_usd_zar.json"), "USD", "ZAR")
    assert fx.render_rate(rate, date(2026, 9, 29)).endswith("(as of Mon 28 Sep)")


def test_single_published_day_is_a_data_error():
    with pytest.raises(DataError, match="two published days"):
        fx.parse_series(payload("USD", {"2026-09-28": 17.85}), "USD", "ZAR")


@pytest.mark.parametrize("bad", [{}, {"rates": None}, {"rates": {"2026-09-28": {"EUR": 1}}}])
def test_unexpected_shape_is_a_data_error(bad):
    with pytest.raises(DataError):
        fx.parse_series(bad, "USD", "ZAR")


def series_for(base):
    return {"USD": {"2026-09-25": 17.80, "2026-09-28": 17.85},
            "EUR": {"2026-09-25": 20.90, "2026-09-28": 20.88},
            "GBP": {"2026-09-25": 24.00, "2026-09-28": 24.00}}[base]


def test_run_all_pairs(monkeypatch, settings):
    monkeypatch.setattr(fx, "fetch_series", lambda cfg, base, today: payload(base, series_for(base)))
    result = fx.run(settings, make_ctx("2026-09-29"))
    assert result.status == OK
    assert result.render() == [
        "<b>Rand</b> · ECB Mon 28 Sep",
        "USD/ZAR  17.85  ▲ 0.3%",
        "EUR/ZAR  20.88  ▼ 0.1%",
        "GBP/ZAR  24.00  ▬ 0.0%",
    ]


def test_one_failing_pair_leaves_the_others(monkeypatch, settings):
    def fetch(cfg, base, today):
        if base == "EUR":
            raise ConnectionError("boom")
        return payload(base, series_for(base))

    monkeypatch.setattr(fx, "fetch_series", fetch)
    result = fx.run(settings, make_ctx("2026-09-29"))
    assert result.status == PARTIAL
    assert "EUR/ZAR  unavailable" in result.lines
    assert result.lines[0].startswith("USD/ZAR  17.85")
    assert "EUR: ConnectionError: boom" in result.detail


def test_all_pairs_failing_raises(monkeypatch, settings):
    def fetch(cfg, base, today):
        raise ConnectionError("down")

    monkeypatch.setattr(fx, "fetch_series", fetch)
    with pytest.raises(DataError):
        fx.run(settings, make_ctx("2026-09-29"))
