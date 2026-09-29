"""Section registry. The order here is the order in the message."""
from brief.runner import Section
from brief.sections import ai_news, fx, headlines, markets, watch, weather, youtube

SECTIONS = [
    Section("weather", "Durban weather", weather.run),
    Section("fx", "Rand", fx.run),
    Section("markets", "Markets", markets.run),          # off by default in settings.toml
    Section("ai_news", "AI updates", ai_news.run),
    Section("youtube", "YouTube", youtube.run),
    Section("headlines", "SA economy", headlines.run),
    Section("watch", "Watch today", watch.run),
]
