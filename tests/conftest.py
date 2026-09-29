"""Shared test setup. Tests never touch the network: sockets are blocked and yfinance is stubbed.

NOTE: the JSON fixtures were written by hand from the Open-Meteo and Frankfurter documentation,
not recorded from live responses (the build sandbox had no access to those hosts). After the
first successful dry run on GitHub Actions, compare a DEBUG log against them.
"""
from __future__ import annotations

import json
import socket
from datetime import date, datetime, time
from pathlib import Path

import pytest

from brief.config import load_settings
from brief.runner import Context
from brief.util import SAST

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def make_ctx(day: str) -> Context:
    return Context(now=datetime.combine(date.fromisoformat(day), time(7, 0), tzinfo=SAST))


@pytest.fixture
def settings() -> dict:
    return load_settings()  # the real config/settings.toml, so a typo in it fails the tests


@pytest.fixture(autouse=True)
def no_network_no_sleep(monkeypatch):
    def refuse(*_a, **_k):
        raise AssertionError("test attempted a real network connection")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr("brief.http.time.sleep", lambda _s: None)
    monkeypatch.setattr("brief.telegram.time.sleep", lambda _s: None)
    monkeypatch.setattr(
        "brief.sections.markets.yahoo_history",
        lambda symbol: (_ for _ in ()).throw(AssertionError(f"unstubbed yfinance call: {symbol}")),
    )


def load_text(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()

# The youtube_error_*.json fixtures ARE recorded live responses (real API, fake key). The other
# youtube_*.json and feed_* fixtures are hand-written from the API/RSS docs.
