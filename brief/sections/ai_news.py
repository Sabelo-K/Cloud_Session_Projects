"""AI updates from RSS feeds listed under [ai_news] in settings.toml.

Same engine as the SA economy headlines (brief/sections/headlines.py): keyword ranking,
near-duplicate collapsing, per-outlet cap, per-feed failure isolation, headline + link only.
"""
from __future__ import annotations

from brief.config import Settings
from brief.runner import Context, SectionResult
from brief.sections import headlines


def run(settings: Settings, ctx: Context) -> SectionResult:
    return headlines.run_feeds(settings, ctx, key="ai_news", title="AI updates")
