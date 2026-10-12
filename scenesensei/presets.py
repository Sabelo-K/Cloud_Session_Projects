"""Render presets: how much quality to buy with render time. Plain Python (no Blender needed)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Preset:
    name: str
    width: int
    height: int
    fps: int
    samples: int           # Cycles samples per pixel (adaptive sampling stops early on clean areas)
    bounces: int           # max light bounces: more = more realistic glass/reflections, slower
    motion_blur: bool
    output: str            # "mp4": Blender writes one H.264 file. "frames": PNG per frame, then ffmpeg
    note: str

    def __post_init__(self) -> None:
        # H.264 (yuv420p) cannot encode odd dimensions.
        if self.width % 2 or self.height % 2:
            raise ValueError(f"preset {self.name}: width and height must be even")
        if self.output not in ("mp4", "frames"):
            raise ValueError(f"preset {self.name}: output must be 'mp4' or 'frames'")


PRESETS: dict[str, Preset] = {p.name: p for p in (
    Preset("draft", 854, 480, 24, 12, 4, False, "mp4",
           "Seconds per frame. Check layout, timing and camera moves."),
    Preset("preview", 1280, 720, 24, 48, 6, False, "mp4",
           "Check lighting and materials before committing to a long render."),
    Preset("final", 1920, 1080, 24, 192, 8, True, "frames",
           "Upload quality. Writes PNG frames (resumable), then stitches an MP4 if ffmpeg is installed."),
    Preset("final4k", 3840, 2160, 24, 256, 8, True, "frames",
           "4K. Roughly 4x the render time of final."),
)}

DEFAULT_PRESET = "preview"


def scaled_size(preset: Preset, scale: int) -> tuple[int, int]:
    """The preset's size at `scale` percent, kept even (H.264 refuses odd widths and heights)."""
    def even(n: float) -> int:
        return max(2, round(n / 2) * 2)
    return even(preset.width * scale / 100), even(preset.height * scale / 100)


def get_preset(name: str) -> Preset:
    try:
        return PRESETS[name]
    except KeyError:
        raise ValueError(f"unknown preset {name!r}; choose from: {', '.join(PRESETS)}") from None
