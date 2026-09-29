import json
from datetime import date

import pytest

from brief.config import ConfigError
from brief.http import HttpError
from brief.runner import OK, PARTIAL, Section, run_sections, FAILED
from brief.sections import youtube
from brief.util import DataError
from brief.youtube import SOURCES, data_api
from brief.youtube.data_api import DataApiSource
from brief.youtube.history import JsonHistory
from brief.youtube.models import ChannelConfig, ChannelReport, ChannelSnapshot, LatestVideo
from tests.conftest import load_fixture, make_ctx

A, B = "UCaaaaaaaaaaaaaaaaaaaaaa", "UCbbbbbbbbbbbbbbbbbbbbbb"
KEY = "AIzaFAKEKEY"
CHANNELS = [ChannelConfig(A, ""), ChannelConfig(B, "")]


def fake_api(monkeypatch, overrides=None):
    """Route get_json calls to fixtures by API path; `overrides` maps a key to a value/Exception."""
    routes = {"channels": load_fixture("youtube_channels.json"),
              "playlistItems:UUaaaaaaaaaaaaaaaaaaaaaa": load_fixture("youtube_playlist_a.json"),
              "playlistItems:UUbbbbbbbbbbbbbbbbbbbbbb": load_fixture("youtube_playlist_b.json"),
              "videos": load_fixture("youtube_videos.json"), **(overrides or {})}
    calls = []

    def fake(url, params=None, **kwargs):
        path = url.rsplit("/", 1)[-1]
        calls.append({"path": path, "params": params, **kwargs})
        key = f"playlistItems:{params['playlistId']}" if path == "playlistItems" else path
        value = routes[key]
        if isinstance(value, Exception):
            raise value
        return value

    monkeypatch.setattr(data_api, "get_json", fake)
    return calls


def source(tmp_path, **kw):
    return DataApiSource({"state_file": str(tmp_path / "hist.json")}, api_key=KEY, **kw)


# --- API parsing ----------------------------------------------------------------------------------

def test_snapshots_parse_stats_latest_upload_and_view_counts(monkeypatch, tmp_path):
    fake_api(monkeypatch)
    snaps = source(tmp_path).fetch_snapshots(CHANNELS)
    a, b = snaps[A], snaps[B]
    assert (a.name, a.subs, a.views, a.videos) == ("Durban Data Lab", 1230, 45678, 42)
    assert (a.latest.title, a.latest.video_id, a.latest.views) == ("How I track the JSE with Python", "vidAAAAAAA1", 1204)
    assert b.subs is None                                  # hiddenSubscriberCount
    assert b.latest.views == 88 and a.problems == [] and b.problems == []


def test_api_key_travels_in_a_header_never_in_the_url_params(monkeypatch, tmp_path):
    calls = fake_api(monkeypatch)
    source(tmp_path).fetch_snapshots(CHANNELS)
    assert calls and all(c["headers"] == {"X-Goog-Api-Key": KEY} for c in calls)
    assert all("key" not in c["params"] for c in calls)
    assert all(c["redact"] == [KEY] for c in calls)
    assert [c["path"] for c in calls] == ["channels", "playlistItems", "playlistItems", "videos"]  # ~4 quota units


def test_unknown_channel_becomes_a_not_found_report(monkeypatch, tmp_path):
    fake_api(monkeypatch, {"channels": {"items": []}})
    (report,) = source(tmp_path).fetch_reports([ChannelConfig(A, "Mine")], make_ctx("2026-09-29"))
    assert report.snapshot is None and report.name == "Mine" and "not found" in report.problems[0]


def test_failed_latest_upload_lookup_keeps_the_channel_stats(monkeypatch, tmp_path):
    fake_api(monkeypatch, {"playlistItems:UUaaaaaaaaaaaaaaaaaaaaaa": HttpError("HTTP 404: playlistNotFound")})
    snaps = source(tmp_path).fetch_snapshots(CHANNELS)
    assert snaps[A].subs == 1230 and snaps[A].latest is None
    assert "latest upload unavailable" in snaps[A].problems[0]
    assert snaps[B].latest is not None


def test_failed_view_count_lookup_is_reported_but_title_still_shown(monkeypatch, tmp_path):
    fake_api(monkeypatch, {"videos": HttpError("HTTP 500")})
    snaps = source(tmp_path).fetch_snapshots(CHANNELS)
    assert snaps[A].latest.title and snaps[A].latest.views is None
    assert any("views unavailable" in p for p in snaps[A].problems)


def test_channels_call_failure_propagates_so_the_section_fails(monkeypatch, tmp_path):
    fake_api(monkeypatch, {"channels": HttpError("HTTP 403: quotaExceeded")})
    with pytest.raises(HttpError, match="quotaExceeded"):
        source(tmp_path).fetch_reports(CHANNELS, make_ctx("2026-09-29"))


def test_missing_api_key_is_a_clear_config_error(monkeypatch, tmp_path):
    monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
    with pytest.raises(ConfigError, match="YOUTUBE_API_KEY"):
        DataApiSource({"state_file": str(tmp_path / "h.json")})


# --- history and deltas ---------------------------------------------------------------------------

def seed(tmp_path, day, subs, views, videos, channel=A):
    h = JsonHistory(tmp_path / "hist.json")
    h.record(channel, date.fromisoformat(day), subs, views, videos)
    h.save(date.fromisoformat("2026-09-29"))


def test_first_run_has_no_deltas_and_writes_the_baseline(monkeypatch, tmp_path):
    fake_api(monkeypatch)
    reports = source(tmp_path).fetch_reports(CHANNELS, make_ctx("2026-09-29"))
    assert reports[0].prev_date is None and reports[0].d_subs is None
    saved = json.loads((tmp_path / "hist.json").read_text())
    assert saved["channels"][A]["2026-09-29"] == {"subs": 1230, "views": 45678, "videos": 42}
    assert saved["channels"][B]["2026-09-29"]["subs"] is None


def test_deltas_are_measured_against_the_previous_snapshot(monkeypatch, tmp_path):
    seed(tmp_path, "2026-09-28", 1200, 45000, 41)
    fake_api(monkeypatch)
    ra = source(tmp_path).fetch_reports(CHANNELS, make_ctx("2026-09-29"))[0]
    assert (ra.prev_date, ra.d_subs, ra.d_views, ra.d_videos) == (date(2026, 9, 28), 30, 678, 1)


def test_a_rerun_on_the_same_day_compares_to_yesterday_not_itself(monkeypatch, tmp_path):
    seed(tmp_path, "2026-09-28", 1200, 45000, 41)
    fake_api(monkeypatch)
    for _ in range(2):
        ra = source(tmp_path).fetch_reports(CHANNELS, make_ctx("2026-09-29"))[0]
        assert ra.d_subs == 30
    assert list(json.loads((tmp_path / "hist.json").read_text())["channels"][A]) == ["2026-09-28", "2026-09-29"]


def test_hidden_subscriber_count_gives_no_subscriber_delta(monkeypatch, tmp_path):
    seed(tmp_path, "2026-09-28", 5000, 8_000_000, 300, channel=B)
    fake_api(monkeypatch)
    rb = source(tmp_path).fetch_reports(CHANNELS, make_ctx("2026-09-29"))[1]
    assert rb.d_subs is None and rb.d_views == 1_000_000 and rb.d_videos == 10


def test_dry_run_never_writes_the_history_file(monkeypatch, tmp_path):
    fake_api(monkeypatch)
    ctx = make_ctx("2026-09-29")
    ctx.dry_run = True
    source(tmp_path).fetch_reports(CHANNELS, ctx)
    assert not (tmp_path / "hist.json").exists()


def test_history_is_pruned_and_written_deterministically(tmp_path):
    h = JsonHistory(tmp_path / "h.json", keep_days=10)
    h.record(A, date(2026, 8, 1), 1, 1, 1)
    h.record(A, date(2026, 9, 28), 2, 2, 2)
    h.save(date(2026, 9, 29))
    text = (tmp_path / "h.json").read_text()
    assert list(json.loads(text)["channels"][A]) == ["2026-09-28"] and text.endswith("}\n")
    assert not list(tmp_path.glob("*.tmp"))


def test_a_corrupt_history_file_is_reported_and_never_overwritten(monkeypatch, tmp_path):
    (tmp_path / "hist.json").write_text("<<<<<<< HEAD\nnot json")
    fake_api(monkeypatch)
    reports = source(tmp_path).fetch_reports(CHANNELS, make_ctx("2026-09-29"))
    assert reports[0].snapshot.subs == 1230 and reports[0].d_subs is None
    assert "history file unreadable" in reports[0].problems[0]
    assert (tmp_path / "hist.json").read_text().startswith("<<<<<<<")


# --- rendering ------------------------------------------------------------------------------------

def snap(name="Durban Data Lab", subs=1230, views=45678, videos=42, latest=True, cid=A):
    lv = LatestVideo("How I track the JSE with Python", "vidAAAAAAA1", 1204,
                     make_ctx("2026-09-27").now) if latest else None
    return ChannelSnapshot(cid, name, subs, views, videos, lv)


def report(**kw):
    prev = kw.pop("prev", date(2026, 9, 28))
    return ChannelReport(A, kw.get("name", "Durban Data Lab"), snap(**kw), prev_date=prev,
                         d_subs=12, d_views=-3, d_videos=0)


def test_channel_rendering_two_lines_with_deltas_and_link():
    ctx = make_ctx("2026-09-29")
    lines = youtube.render_reports([report()], ctx)
    assert lines == [
        "<b>Durban Data Lab</b>: 1,230 subs (+12) · 45,678 views (-3) · 42 videos (0)",
        '↳ <a href="https://youtu.be/vidAAAAAAA1">How I track the JSE with Python</a> · 1,204 views · 2d ago',
    ]


def test_first_snapshot_gap_hidden_subs_and_unavailable_variants():
    ctx = make_ctx("2026-09-29")
    assert youtube.render_reports([report(prev=None, latest=False)], ctx)[0].endswith("(first snapshot)")
    assert youtube.render_reports([report(prev=date(2026, 9, 25), latest=False)], ctx)[0].endswith("(vs Fri 25 Sep)")
    assert "subs hidden" in youtube.render_reports([report(subs=None, latest=False)], ctx)[0]
    assert youtube.render_reports([ChannelReport(A, "Gone", None)], ctx) == ["<b>Gone</b>: unavailable"]


def test_titles_and_names_are_escaped_and_long_titles_shortened():
    r = report(name="A&B <Lab>")
    r.snapshot.latest.title = "<b>Bold</b> " + "long " * 30
    lines = youtube.render_reports([r], make_ctx("2026-09-29"))
    assert lines[0].startswith("<b>A&amp;B &lt;Lab&gt;</b>") and "&lt;b&gt;Bold" in lines[1] and "…</a>" in lines[1]


def test_a_bad_video_id_is_shown_without_a_link():
    r = report()
    r.snapshot.latest.video_id = 'x"><script>'
    assert "<a " not in youtube.render_reports([r], make_ctx("2026-09-29"))[1]


@pytest.mark.parametrize("n, expected_body", [(1, 2), (3, 6), (4, 4), (6, 6), (9, 6)])
def test_section_never_exceeds_seven_lines_including_heading(n, expected_body):
    reports = [report(name=f"Channel {i}") for i in range(n)]
    body = youtube.render_reports(reports, make_ctx("2026-09-29"))
    assert len(body) == expected_body and len(body) + 1 <= youtube.MAX_LINES
    if n > 6:
        assert body[-1] == "+4 more channels not shown"


# --- the section ----------------------------------------------------------------------------------

class FakeSource:
    label = "fake source"

    def __init__(self, cfg):
        pass

    def fetch_reports(self, channels, ctx):
        return [report(name=c.id[-4:], latest=False, prev=None) for c in channels]


def yt_settings(**overrides):
    return {"youtube": {"enabled": True, "source": "data_api", "channels": [{"id": A, "name": "Mine"}],
                        **overrides}}


def test_switching_source_is_a_config_change_only(monkeypatch):
    monkeypatch.setitem(SOURCES, "fake", FakeSource)
    result = youtube.run(yt_settings(source="fake"), make_ctx("2026-09-29"))
    assert result.status == OK and result.heading == "<b>YouTube</b> (fake source)"
    assert result.lines[0].startswith("<b>aaaa</b>")


def test_unknown_source_lists_the_valid_ones():
    with pytest.raises(DataError, match="unknown youtube source 'supabase'.*data_api"):
        youtube.run(yt_settings(source="supabase"), make_ctx("2026-09-29"))


def test_no_channels_configured_hides_the_section_but_flags_the_run():
    result = youtube.run(yt_settings(channels=[]), make_ctx("2026-09-29"))
    assert result.hidden and result.status == PARTIAL and "[[youtube.channels]]" in result.detail


def test_a_handle_instead_of_a_channel_id_is_rejected_with_advice(monkeypatch):
    monkeypatch.setitem(SOURCES, "fake", FakeSource)
    result = youtube.run(yt_settings(source="fake", channels=[{"id": "@MyChannel"}, {"id": A}]),
                         make_ctx("2026-09-29"))
    assert result.status == PARTIAL and "@handle won't work" in result.detail and len(result.lines) == 1


def test_every_channel_failing_fails_the_section(monkeypatch):
    class Dead(FakeSource):
        def fetch_reports(self, channels, ctx):
            return [ChannelReport(c.id, "X", None, problems=["channel not found"]) for c in channels]

    monkeypatch.setitem(SOURCES, "dead", Dead)
    with pytest.raises(DataError, match="no channel could be fetched"):
        youtube.run(yt_settings(source="dead"), make_ctx("2026-09-29"))


def test_missing_api_key_fails_only_this_section_via_the_runner(monkeypatch):
    monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
    (result,) = run_sections([Section("youtube", "YouTube", youtube.run)], yt_settings(), make_ctx("2026-09-29"))
    assert result.status == FAILED and "YOUTUBE_API_KEY" in result.detail
    assert result.render() == ["<b>YouTube</b>", "unavailable"]


def test_partial_problems_do_not_hide_the_numbers(monkeypatch):
    class Flaky(FakeSource):
        def fetch_reports(self, channels, ctx):
            r = report(latest=False)
            r.problems.append("latest upload unavailable (HttpError: HTTP 404)")
            return [r]

    monkeypatch.setitem(SOURCES, "flaky", Flaky)
    result = youtube.run(yt_settings(source="flaky"), make_ctx("2026-09-29"))
    assert result.status == PARTIAL and "1,230 subs" in result.lines[0] and "HTTP 404" in result.detail


def test_real_source_end_to_end_through_the_section(monkeypatch, tmp_path):
    monkeypatch.setenv("YOUTUBE_API_KEY", KEY)
    fake_api(monkeypatch)
    cfg = {"enabled": True, "source": "data_api", "state_file": str(tmp_path / "h.json"),
           "channels": [{"id": A, "name": "Mine"}, {"id": B}]}
    result = youtube.run({"youtube": cfg}, make_ctx("2026-09-29"))
    assert result.status == OK
    assert result.render()[0] == "<b>YouTube</b> (public stats, subs rounded)"
    assert result.render()[1] == "<b>Mine</b>: 1,230 subs · 45,678 views · 42 videos (first snapshot)"
    assert result.render()[3].startswith("<b>Rand Shorts</b>: subs hidden")
    assert (tmp_path / "h.json").exists()
