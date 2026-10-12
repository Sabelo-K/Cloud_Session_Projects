"""Arguments a scene script receives from `python -m scenesensei.render` (after Blender's `--`).

Plain Python so it can be tested without Blender. When a script is run by hand from Blender's
Scripting tab there is no `--`, and the defaults apply (preview preset, renders/<name>/preview).
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

from scenesensei.presets import DEFAULT_PRESET, PRESETS, Preset, get_preset

PACKAGE_DIR = Path(__file__).resolve().parent
RENDERS_DIR = PACKAGE_DIR / "renders"


@dataclass(frozen=True)
class SceneArgs:
    name: str
    preset: Preset
    out_dir: Path
    frame: int | None        # render just this frame as a still image
    samples: int             # preset.samples unless overridden
    scale: int               # resolution percentage (100 = the preset's size)
    blend_only: bool         # build the scene and save a .blend, no rendering
    save_blend: bool         # also save the .blend next to the render
    resume: bool             # frame presets: keep frames already rendered instead of redoing them


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="scene", add_help=False)
    p.add_argument("--preset", default=DEFAULT_PRESET, choices=list(PRESETS))
    p.add_argument("--out", type=Path, default=None)
    p.add_argument("--frame", type=int, default=None)
    p.add_argument("--samples", type=int, default=None)
    p.add_argument("--scale", type=int, default=100)
    p.add_argument("--blend-only", action="store_true")
    p.add_argument("--save-blend", action="store_true")
    p.add_argument("--resume", action="store_true")
    return p


def split_blender_argv(argv: list[str]) -> list[str]:
    """Blender passes its own flags first; ours come after a lone `--`."""
    return argv[argv.index("--") + 1:] if "--" in argv else []


def parse_scene_args(name: str, argv: list[str] | None = None) -> SceneArgs:
    ns = build_parser().parse_args(split_blender_argv(sys.argv if argv is None else argv))
    preset = get_preset(ns.preset)
    if ns.scale < 1 or ns.scale > 200:
        raise SystemExit("--scale must be between 1 and 200 (percent)")
    return SceneArgs(
        name=name,
        preset=preset,
        out_dir=ns.out or RENDERS_DIR / name / preset.name,
        frame=ns.frame,
        samples=ns.samples or preset.samples,
        scale=ns.scale,
        blend_only=ns.blend_only,
        save_blend=ns.save_blend,
        resume=ns.resume,
    )
