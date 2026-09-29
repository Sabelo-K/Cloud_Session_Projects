"""Runs each section in isolation, then assembles the message.

A section that raises never stops the others: it becomes an 'unavailable' block and is logged.
"""
from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Callable

from brief.config import Settings
from brief.util import describe, esc

log = logging.getLogger(__name__)

OK, PARTIAL, FAILED = "ok", "partial", "failed"


@dataclass
class Context:
    now: datetime  # timezone-aware, SAST
    dry_run: bool = False  # sections must not write state (e.g. history files) on a dry run

    @property
    def today(self) -> date:
        return self.now.date()


@dataclass
class SectionResult:
    key: str
    title: str                       # plain name, used in logs and in the failure block
    lines: list[str]                 # body lines, already Telegram-HTML-safe
    heading: str | None = None       # HTML title line; defaults to bold `title`
    status: str = OK
    detail: str = ""                 # what failed, for the log (never sent to Telegram)
    duration: float = 0.0
    hidden: bool = False             # nothing to show today (still logged and counted)
    extra: dict = field(default_factory=dict)

    def render(self) -> list[str]:
        if self.hidden:
            return []
        return [self.heading or f"<b>{esc(self.title)}</b>", *self.lines]


@dataclass(frozen=True)
class Section:
    key: str                         # also the settings.toml table name
    title: str
    run: Callable[[Settings, Context], SectionResult]


def run_sections(sections: list[Section], settings: Settings, ctx: Context) -> list[SectionResult]:
    results: list[SectionResult] = []
    for section in sections:
        if not settings.get(section.key, {}).get("enabled", True):
            log.info("section=%s skipped (disabled in settings)", section.key)
            continue
        started = time.monotonic()
        try:
            result = section.run(settings, ctx)
        except Exception as exc:  # noqa: BLE001 - isolation is the whole point
            log.debug("section %s traceback", section.key, exc_info=True)
            result = SectionResult(section.key, section.title, ["unavailable"], status=FAILED,
                                   detail=describe(exc))
        result.duration = time.monotonic() - started
        results.append(result)
        log.log(logging.INFO if result.status == OK else logging.WARNING,
                "section=%s status=%s duration=%.1fs%s", result.key, result.status,
                result.duration, f" detail={result.detail}" if result.detail else "")
    return results


def warning_line(results: list[SectionResult]) -> str | None:
    """A short bottom-of-message warning when more than half of the sections failed."""
    failed = sum(r.status == FAILED for r in results)
    if results and failed * 2 > len(results):
        return f"⚠️ {failed} of {len(results)} sections failed; check the workflow log."
    return None


def assemble(header: str, results: list[SectionResult], max_lines: int = 30) -> str:
    """Header, then each section, then the optional warning. Sections are separated by a blank
    line for readability; if that would exceed `max_lines`, the blank lines are dropped."""
    blocks = [[header], *(block for r in results if (block := r.render()))]
    warn = warning_line(results)
    if warn:
        blocks.append([warn])
    spaced = [line for i, block in enumerate(blocks) for line in ([""] if i else []) + block]
    if len(spaced) <= max_lines:
        return "\n".join(spaced)
    return "\n".join(line for block in blocks for line in block)


def write_step_summary(results: list[SectionResult]) -> None:
    """Show per-section outcomes on the GitHub Actions run page (no-op elsewhere)."""
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not path:
        return
    rows = ["| Section | Status | Time | Detail |", "|---|---|---|---|"]
    for r in results:
        rows.append(f"| {r.title} | {r.status} | {r.duration:.1f}s | {r.detail.replace('|', '/')} |")
    with open(path, "a", encoding="utf-8") as fh:
        fh.write("\n".join(rows) + "\n")


def annotate_failures(results: list[SectionResult]) -> None:
    """Surface failures as GitHub Actions warning annotations (no-op elsewhere)."""
    if os.environ.get("GITHUB_ACTIONS") != "true":
        return
    for r in results:
        if r.status != OK:
            print(f"::warning title=Section {r.key} {r.status}::{r.detail}")
