import copy
from datetime import date

import pytest

from brief.runner import OK, PARTIAL
from brief.sections import weather
from brief.util import DataError
from tests.conftest import load_fixture, make_ctx


def test_parse_and_render_fixture():
    w = weather.parse_forecast(load_fixture("open_meteo_durban.json"), date(2026, 9, 29))
    assert weather.render_weather(w) == "17–24°C · rain 40% (3 mm) · wind SW 22 km/h, gusts 41"


@pytest.mark.parametrize("deg,expected", [(0, "N"), (90, "E"), (225, "SW"), (348.75, "N"), (360, "N")])
def test_compass(deg, expected):
    assert weather.compass(deg) == expected


def test_light_rain_amount_is_hidden():
    payload = load_fixture("open_meteo_durban.json")
    payload["daily"]["precipitation_sum"] = [0.2]
    w = weather.parse_forecast(payload, date(2026, 9, 29))
    assert "mm" not in weather.render_weather(w)


def test_forecast_for_wrong_day_is_rejected():
    with pytest.raises(DataError, match="expected 2026-09-30"):
        weather.parse_forecast(load_fixture("open_meteo_durban.json"), date(2026, 9, 30))


def test_missing_required_field_is_a_data_error():
    payload = load_fixture("open_meteo_durban.json")
    del payload["daily"]["wind_speed_10m_max"]
    with pytest.raises(DataError):
        weather.parse_forecast(payload, date(2026, 9, 29))


def test_null_temperature_is_a_data_error():
    payload = load_fixture("open_meteo_durban.json")
    payload["daily"]["temperature_2m_max"] = [None]
    with pytest.raises(DataError):
        weather.parse_forecast(payload, date(2026, 9, 29))


def test_run_ok(monkeypatch, settings):
    monkeypatch.setattr(weather, "fetch_forecast", lambda cfg: load_fixture("open_meteo_durban.json"))
    result = weather.run(settings, make_ctx("2026-09-29"))
    assert result.status == OK
    assert result.render()[0] == "<b>Durban</b> today"
    assert len(result.lines) == 1


def test_missing_rain_probability_degrades_but_still_reports(monkeypatch, settings):
    payload = copy.deepcopy(load_fixture("open_meteo_durban.json"))
    payload["daily"]["precipitation_probability_max"] = [None]
    monkeypatch.setattr(weather, "fetch_forecast", lambda cfg: payload)
    result = weather.run(settings, make_ctx("2026-09-29"))
    assert result.status == PARTIAL
    assert "rain n/a" in result.lines[0]
