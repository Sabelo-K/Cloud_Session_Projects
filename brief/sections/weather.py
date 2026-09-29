"""Durban weather from Open-Meteo (no API key)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from brief.config import Settings
from brief.http import get_json
from brief.runner import OK, PARTIAL, Context, SectionResult
from brief.util import DataError, esc

DAILY_VARS = (
    "temperature_2m_max,temperature_2m_min,precipitation_probability_max,"
    "precipitation_sum,wind_speed_10m_max,wind_gusts_10m_max,wind_direction_10m_dominant"
)
COMPASS = ("N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
           "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW")


@dataclass
class Weather:
    day: date
    t_min: float
    t_max: float
    rain_prob: float | None
    rain_mm: float | None
    wind_kmh: float
    gust_kmh: float | None
    wind_dir_deg: float | None


def compass(deg: float) -> str:
    """Wind direction = where the wind blows FROM, as Open-Meteo reports it."""
    return COMPASS[int((deg % 360) / 22.5 + 0.5) % 16]


def fetch_forecast(cfg: dict) -> dict:
    return get_json(cfg["base_url"], {
        "latitude": cfg["latitude"],
        "longitude": cfg["longitude"],
        "daily": DAILY_VARS,
        "timezone": cfg["timezone"],
        "wind_speed_unit": "kmh",
        "forecast_days": 1,
    })


def parse_forecast(payload: dict, today: date) -> Weather:
    try:
        daily = payload["daily"]
        day = date.fromisoformat(daily["time"][0])
        first = lambda name: daily[name][0]  # noqa: E731 - tiny local accessor
        weather = Weather(
            day=day,
            t_min=first("temperature_2m_min"),
            t_max=first("temperature_2m_max"),
            rain_prob=daily.get("precipitation_probability_max", [None])[0],
            rain_mm=daily.get("precipitation_sum", [None])[0],
            wind_kmh=first("wind_speed_10m_max"),
            gust_kmh=daily.get("wind_gusts_10m_max", [None])[0],
            wind_dir_deg=daily.get("wind_direction_10m_dominant", [None])[0],
        )
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise DataError(f"unexpected Open-Meteo response shape: {exc!r}") from exc
    if weather.day != today:
        raise DataError(f"forecast is for {weather.day}, expected {today}")
    if None in (weather.t_min, weather.t_max, weather.wind_kmh):
        raise DataError("temperature or wind missing from forecast")
    return weather


def render_weather(w: Weather) -> str:
    rain = "rain n/a" if w.rain_prob is None else f"rain {w.rain_prob:.0f}%"
    if w.rain_mm is not None and w.rain_mm >= 1:
        rain += f" ({w.rain_mm:.0f} mm)"
    wind = f"wind {w.wind_kmh:.0f} km/h"
    if w.wind_dir_deg is not None:
        wind = f"wind {compass(w.wind_dir_deg)} {w.wind_kmh:.0f} km/h"
    if w.gust_kmh is not None:
        wind += f", gusts {w.gust_kmh:.0f}"
    return f"{w.t_min:.0f}–{w.t_max:.0f}°C · {rain} · {wind}"


def run(settings: Settings, ctx: Context) -> SectionResult:
    cfg = settings["weather"]
    weather = parse_forecast(fetch_forecast(cfg), ctx.today)
    result = SectionResult("weather", cfg["name"], [render_weather(weather)], status=OK)
    result.heading = f"<b>{esc(cfg['name'])}</b> today"
    if weather.rain_prob is None:
        result.status, result.detail = PARTIAL, "rain probability missing"
    return result
