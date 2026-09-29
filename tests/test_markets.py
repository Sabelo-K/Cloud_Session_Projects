from datetime import date

import pytest

from brief.runner import FAILED, OK, PARTIAL, Section, run_sections
from brief.sections import markets
from brief.sections.markets import Instrument
from brief.util import DataError
from tests.conftest import make_ctx

D = date.fromisoformat


def bars(*pairs):
    return [(D(d), c) for d, c in pairs]


# Tuesday 29 Sep 2026: the JSE traded on Monday 28th, so lines are 'fresh'.
FRESH = {
    "^J200.JO": bars(("2026-09-25", 100_500.0), ("2026-09-28", 101_317.16)),
    "SBK.JO": bars(("2026-09-25", 28_000.0), ("2026-09-28", 28_540.0)),
    "FSR.JO": bars(("2026-09-25", 9_000.0), ("2026-09-28", 8_910.0)),
    "ABG.JO": bars(("2026-09-25", 22_000.0), ("2026-09-28", 22_000.0)),
    "NED.JO": bars(("2026-09-25", 26_700.0), ("2026-09-28", 26_734.0)),
    "CPI.JO": bars(("2026-09-25", 300_000.0), ("2026-09-28", 303_000.0)),
    "BZ=F": bars(("2026-09-25", 99.6), ("2026-09-28", 97.51), ("2026-09-29", 97.0)),  # today = partial
    "GC=F": bars(("2026-09-25", 4_170.0), ("2026-09-28", 4_150.10)),
}


def stub(monkeypatch, table, fail=()):
    calls = []

    def fake(symbol):
        calls.append(symbol)
        if symbol in fail:
            raise ConnectionError(f"cannot reach {symbol}")
        return table[symbol]

    monkeypatch.setattr(markets, "yahoo_history", fake)
    return calls


def test_normal_day_renders_every_line(monkeypatch, settings):
    stub(monkeypatch, FRESH)
    result = markets.run(settings, make_ctx("2026-09-29"))
    assert result.status == OK
    assert result.render() == [
        "<b>Markets</b> (previous close)",
        "JSE Top 40  101,317  ▲ 0.8%",
        "Standard Bank  R285.40  ▲ 1.9%",
        "FirstRand  R89.10  ▼ 1.0%",
        "Absa  R220.00  ▬ 0.0%",
        "Nedbank  R267.34  ▲ 0.1%",
        "Capitec  R3,030.00  ▲ 1.0%",
        "Brent  $97.51  ▼ 2.1%",
        "Gold  $4,150  ▼ 0.5%",
    ]


def test_todays_partial_bar_is_never_used():
    inst = Instrument("Brent", "BZ=F")
    q = markets.make_quote(inst, bars(("2026-09-25", 99.6), ("2026-09-28", 97.51), ("2026-09-29", 50.0)),
                           D("2026-09-29"))
    assert (q.session, q.close, q.prev_close) == (D("2026-09-28"), 97.51, 99.6)


@pytest.mark.parametrize("history", [[], bars(("2026-09-28", 1.0)),
                                     bars(("2026-09-25", 0.0), ("2026-09-28", 1.0)),
                                     bars(("2026-09-25", float("nan")), ("2026-09-28", 1.0))])
def test_unusable_history_is_a_data_error(history):
    with pytest.raises(DataError):
        markets.make_quote(Instrument("X", "X"), history, D("2026-09-29"))


def test_jse_closed_after_weekend_collapses_to_one_line(monkeypatch, settings):
    monday = {"BZ=F": bars(("2026-09-24", 99.0), ("2026-09-25", 98.0)),   # last Friday's session
              "GC=F": bars(("2026-09-24", 4_100.0), ("2026-09-25", 4_150.0))}
    calls = stub(monkeypatch, monday)
    result = markets.run(settings, make_ctx("2026-09-28"))   # Monday: JSE shut on Sunday
    assert result.lines[0] == "JSE closed yesterday (Sunday); last session Fri 25 Sep"
    assert calls == ["BZ=F", "GC=F"]                          # JSE tickers not even fetched
    assert len(result.lines) == 3
    assert result.status == OK


def test_jse_closed_after_public_holiday(monkeypatch, settings):
    friday = {"BZ=F": bars(("2026-09-23", 99.0), ("2026-09-24", 98.0)),   # futures traded on Heritage Day
              "GC=F": bars(("2026-09-23", 4_100.0), ("2026-09-24", 4_150.0))}
    stub(monkeypatch, friday)
    result = markets.run(settings, make_ctx("2026-09-25"))   # Friday after Heritage Day
    assert result.lines[0] == "JSE closed yesterday (Heritage Day); last session Wed 23 Sep"


def test_user_listed_extra_closure(monkeypatch, settings):
    settings["markets"]["extra_jse_closed_dates"] = ["2026-09-28"]
    stub(monkeypatch, FRESH)
    result = markets.run(settings, make_ctx("2026-09-29"))
    assert result.lines[0].startswith("JSE closed yesterday (market closure)")


def test_stale_data_is_labelled_not_presented_as_new(monkeypatch, settings):
    table = dict(FRESH)
    table["SBK.JO"] = bars(("2026-09-23", 28_000.0), ("2026-09-25", 28_540.0))  # Monday missing
    stub(monkeypatch, table)
    result = markets.run(settings, make_ctx("2026-09-29"))
    line = next(l for l in result.lines if l.startswith("Standard Bank"))
    assert line == "Standard Bank  R285.40 (last close Fri 25 Sep, not updated)"
    assert "▲" not in line and "%" not in line


def test_one_failed_ticker_shows_unavailable_and_the_rest_still_render(monkeypatch, settings):
    stub(monkeypatch, FRESH, fail={"NED.JO"})
    result = markets.run(settings, make_ctx("2026-09-29"))
    assert result.status == PARTIAL
    assert "Nedbank  unavailable" in result.lines
    assert len(result.lines) == 8
    assert "Standard Bank  R285.40  ▲ 1.9%" in result.lines
    assert "NED.JO ConnectionError" in result.detail


def test_every_ticker_failing_fails_the_section_via_the_runner(monkeypatch, settings):
    stub(monkeypatch, FRESH, fail=set(FRESH))
    (result,) = run_sections([Section("markets", "Markets", markets.run)], settings,
                             make_ctx("2026-09-29"))
    assert result.status == FAILED
    assert result.render() == ["<b>Markets</b>", "unavailable"]
    assert "all 8 instruments failed" in result.detail


def test_labels_are_html_escaped():
    inst = Instrument("A&B <Co>", "AB.JO", "JSE")
    q = markets.Quote(inst, D("2026-09-28"), 100.0, 99.0)
    assert markets.render_quote(q, D("2026-09-28")).startswith("A&amp;B &lt;Co&gt;  100.00")


# --- the yfinance adapter (real function; Ticker stubbed, no network) -----------------------

REAL_YAHOO_HISTORY = markets.yahoo_history   # captured at import, before conftest stubs it


class FakeTicker:
    frames: list = []
    calls: list = []

    def __init__(self, symbol):
        self.symbol = symbol

    def history(self, **kwargs):
        FakeTicker.calls.append(kwargs)
        item = FakeTicker.frames.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def test_yahoo_history_uses_exchange_dates_drops_nan_and_raises_errors(monkeypatch):
    import pandas as pd
    import yfinance

    idx = pd.DatetimeIndex(["2026-09-25", "2026-09-26", "2026-09-28"], tz="Africa/Johannesburg")
    FakeTicker.calls = []
    FakeTicker.frames = [pd.DataFrame({"Close": [28_000.0, float("nan"), 28_540.0]}, index=idx)]
    monkeypatch.setattr(yfinance, "Ticker", FakeTicker)

    assert REAL_YAHOO_HISTORY("SBK.JO") == [(D("2026-09-25"), 28_000.0), (D("2026-09-28"), 28_540.0)]
    assert FakeTicker.calls[0]["raise_errors"] is True and FakeTicker.calls[0]["auto_adjust"] is False


def test_yahoo_history_retries_once_then_succeeds(monkeypatch):
    import pandas as pd
    import yfinance

    idx = pd.DatetimeIndex(["2026-09-28"], tz="America/New_York")
    FakeTicker.calls = []
    FakeTicker.frames = [RuntimeError("rate limited"), pd.DataFrame({"Close": [97.5]}, index=idx)]
    monkeypatch.setattr(yfinance, "Ticker", FakeTicker)
    monkeypatch.setattr(markets.time, "sleep", lambda _s: None)

    assert REAL_YAHOO_HISTORY("BZ=F") == [(D("2026-09-28"), 97.5)]
    assert len(FakeTicker.calls) == 2


def test_yahoo_history_gives_up_after_the_second_failure(monkeypatch):
    import yfinance

    FakeTicker.calls = []
    FakeTicker.frames = [RuntimeError("one"), RuntimeError("two")]
    monkeypatch.setattr(yfinance, "Ticker", FakeTicker)
    monkeypatch.setattr(markets.time, "sleep", lambda _s: None)
    with pytest.raises(RuntimeError, match="two"):
        REAL_YAHOO_HISTORY("BZ=F")
