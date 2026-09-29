"""Section registry. The order here is the order in the message."""
from brief.runner import Section
from brief.sections import fx, markets, weather

SECTIONS = [
    Section("weather", "Durban weather", weather.run),
    Section("fx", "Rand", fx.run),
    Section("markets", "Markets", markets.run),
    # Phase 2: youtube, headlines, watch-today
]
