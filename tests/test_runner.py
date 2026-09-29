from brief import runner
from brief.runner import FAILED, OK, PARTIAL, Section, SectionResult, assemble, run_sections, warning_line
from tests.conftest import make_ctx


def ok(key):
    return lambda settings, ctx: SectionResult(key, key.title(), [f"{key} body"])


def boom(settings, ctx):
    raise RuntimeError("source exploded\nwith a second line")


def test_a_failing_section_never_stops_the_others():
    sections = [Section("a", "A", ok("a")), Section("b", "B", boom), Section("c", "C", ok("c"))]
    results = run_sections(sections, {}, make_ctx("2026-09-29"))
    assert [r.status for r in results] == [OK, FAILED, OK]
    assert results[1].render() == ["<b>B</b>", "unavailable"]
    assert results[1].detail == "RuntimeError: source exploded"      # one line, no traceback
    assert results[2].lines == ["c body"]


def test_disabled_sections_are_skipped_and_not_counted():
    sections = [Section("a", "A", ok("a")), Section("b", "B", boom)]
    results = run_sections(sections, {"b": {"enabled": False}}, make_ctx("2026-09-29"))
    assert [r.key for r in results] == ["a"]


def test_warning_only_when_more_than_half_failed():
    def res(*statuses):
        return [SectionResult(str(i), "T", [], status=s) for i, s in enumerate(statuses)]

    assert warning_line(res(OK, OK, FAILED)) is None
    assert warning_line(res(OK, FAILED)) is None                      # exactly half
    assert warning_line(res(PARTIAL, FAILED, FAILED)) == "⚠️ 2 of 3 sections failed; check the workflow log."
    assert warning_line([]) is None


def test_message_still_assembles_when_everything_fails():
    results = run_sections([Section(k, k, boom) for k in "abc"], {}, make_ctx("2026-09-29"))
    text = assemble("<b>Tue</b>", results)
    assert text.startswith("<b>Tue</b>")
    assert text.count("unavailable") == 3
    assert text.splitlines()[-1].startswith("⚠️ 3 of 3 sections failed")


def test_blank_separators_are_dropped_only_when_over_the_line_budget():
    results = [SectionResult("a", "A", ["x", "y"]), SectionResult("b", "B", ["z"])]
    roomy = assemble("H", results, max_lines=30)
    assert roomy == "H\n\n<b>A</b>\nx\ny\n\n<b>B</b>\nz"
    tight = assemble("H", results, max_lines=6)
    assert tight == "H\n<b>A</b>\nx\ny\n<b>B</b>\nz"


def test_step_summary_is_written_when_github_provides_a_path(tmp_path, monkeypatch):
    path = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(path))
    runner.write_step_summary([SectionResult("fx", "Rand", [], status=FAILED, detail="a|b")])
    assert "| Rand | failed |" in path.read_text() and "a/b" in path.read_text()
