"""Colour helpers. Plain Python: lets tests and scene scripts share one hex-to-linear conversion."""
from __future__ import annotations

Color = tuple[float, float, float]


def srgb_to_linear(c: float) -> float:
    """One sRGB channel (0-1, what you see in a colour picker) to linear light (what Blender computes in)."""
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def parse_color(value: "str | Color") -> Color:
    """'#RRGGBB' / 'RRGGBB' (sRGB, as in a colour picker) or an (r, g, b) tuple that is already linear.

    Returns linear RGB, which is what Blender's colour sockets expect.
    """
    if isinstance(value, str):
        text = value.strip().lstrip("#")
        if len(text) != 6:
            raise ValueError(f"expected a #RRGGBB colour, got {value!r}")
        try:
            r, g, b = (int(text[i:i + 2], 16) / 255 for i in (0, 2, 4))
        except ValueError:
            raise ValueError(f"expected a #RRGGBB colour, got {value!r}") from None
        return (srgb_to_linear(r), srgb_to_linear(g), srgb_to_linear(b))
    r, g, b = value
    return (float(r), float(g), float(b))
