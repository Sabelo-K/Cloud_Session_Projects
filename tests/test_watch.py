import pytest

from brief.config import ROOT
from brief.runner import OK, PARTIAL
from brief.sections import watch
from tests.conftest import make_ctx


def settings_for(tmp_path, body):
    path = tmp_path / "events.toml"
    path.write_text(body, encoding="utf-8")
    return {"watch": {"enabled": True, "file": str(path)}}   # absolute path wins over ROOT


TWO_ON_ONE_DAY = '''
[[event]]
date = "2026-10-07"
text = "Fuel price adjustment"
[[event]]
date = "2026-10-07"
text = "CPI & PPI <release>"
[[event]]
date = "2026-11-19"
text = "SARB MPC decision"
'''


def test_event_today_is_one_line_and_escaped(tmp_path):
    result = watch.run(settings_for(tmp_path, TWO_ON_ONE_DAY), make_ctx("2026-10-07"))
    assert result.status == OK and not result.hidden
    assert result.render() == ["<b>Watch today:</b> Fuel price adjustment · CPI &amp; PPI &lt;release&gt;"]


def test_no_event_today_is_silent(tmp_path):
    result = watch.run(settings_for(tmp_path, TWO_ON_ONE_DAY), make_ctx("2026-10-08"))
    assert result.hidden and result.render() == []


def test_bad_entries_are_skipped_and_reported_but_good_ones_still_work(tmp_path):
    body = '''
[[event]]
date = "07/10/2026"
text = "wrong date format"
[[event]]
date = "2026-10-07"
[[event]]
date = "2026-10-07"
text = "Good one"
'''
    result = watch.run(settings_for(tmp_path, body), make_ctx("2026-10-07"))
    assert result.status == PARTIAL
    assert result.render() == ["<b>Watch today:</b> Good one"]
    assert "event #1 skipped" in result.detail and "event #2 skipped" in result.detail


def test_unparseable_file_raises_so_the_runner_marks_only_this_section_failed(tmp_path):
    with pytest.raises(Exception):
        watch.run(settings_for(tmp_path, "[[event]\nnot toml"), make_ctx("2026-10-07"))


def test_the_shipped_events_file_is_valid_and_has_the_november_mpc_date():
    events, problems = watch.load_events(ROOT / "config" / "events.toml")
    assert problems == []
    assert any(str(e.day) == "2026-11-19" and "MPC" in e.text for e in events)
