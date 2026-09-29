"""Section registry. The order here is the order in the message."""
from brief.runner import Section
from brief.sections import fx, headlines, markets, watch, weather, youtube

SECTIONS = [
    Section("weather", "Durban weather", weather.run),
    Section("fx", "Rand", fx.run),
    Section("markets", "Markets", markets.run),
    Section("youtube", "YouTube", youtube.run),
    Section("headlines", "SA economy", headlines.run),
    Section("watch", "Watch today", watch.run),
]
