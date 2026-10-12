"""Render a scene with Blender, then (for `final` presets) stitch the frames into an MP4.

    python -m scenesensei.render logo_reveal                  # preview quality
    python -m scenesensei.render logo_reveal --preset draft   # fast check of layout and timing
    python -m scenesensei.render logo_reveal --frame 40       # one still image of frame 40
    python -m scenesensei.render logo_reveal --blend-only     # build the scene, open the .blend yourself
    python -m scenesensei.render logo_reveal --preset final   # upload quality

Blender must be installed (free, blender.org). It is found via --blender, the BLENDER environment
variable, your PATH, or the usual install folders.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from scenesensei.presets import DEFAULT_PRESET, PRESETS, get_preset
from scenesensei.scene_args import PACKAGE_DIR, RENDERS_DIR

SCENES_DIR = PACKAGE_DIR / "scenes"
INFO_FILE = "render_info.json"   # written by the Blender side after configuring the render

_BLENDER_GLOBS = (
    r"C:\Program Files\Blender Foundation\Blender*\blender.exe",
    r"C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe",
    "/Applications/Blender.app/Contents/MacOS/Blender",
    "/snap/bin/blender",
    "/usr/bin/blender",
    "/usr/local/bin/blender",
)


class RenderError(Exception):
    """Something the user can fix; shown as a one-line message, not a traceback."""


def find_blender(explicit: str | None = None) -> str:
    candidates = [explicit, os.environ.get("BLENDER")]
    for c in candidates:
        if c:
            if Path(c).is_file():
                return c
            raise RenderError(f"Blender not found at {c!r}")
    on_path = shutil.which("blender")
    if on_path:
        return on_path
    for pattern in _BLENDER_GLOBS:
        # Newest install first, so "Blender 4.5" wins over "Blender 4.2".
        hits = sorted(glob.glob(pattern), reverse=True)
        if hits:
            return hits[0]
    raise RenderError(
        "Blender not found. Install it from https://www.blender.org/download/ (free), then either add it "
        "to PATH, set the BLENDER environment variable to blender.exe, or pass --blender PATH."
    )


def resolve_scene(name: str) -> Path:
    """'logo_reveal', 'logo_reveal.py' or a path to a scene file."""
    direct = Path(name)
    for candidate in (direct, SCENES_DIR / name, SCENES_DIR / f"{name}.py"):
        if candidate.is_file():
            return candidate.resolve()
    available = sorted(p.stem for p in SCENES_DIR.glob("*.py") if not p.name.startswith("_"))
    raise RenderError(f"scene {name!r} not found. Available: {', '.join(available) or '(none)'}")


def build_command(blender: str, scene: Path, out_dir: Path, args: argparse.Namespace) -> list[str]:
    cmd = [blender, "--background", "--factory-startup", "--python-exit-code", "1",
           "--python", str(scene), "--",
           "--preset", args.preset, "--out", str(out_dir),
           "--scale", str(args.scale)]
    if args.frame is not None:
        cmd += ["--frame", str(args.frame)]
    if args.samples is not None:
        cmd += ["--samples", str(args.samples)]
    if args.blend_only:
        cmd.append("--blend-only")
    if args.save_blend:
        cmd.append("--save-blend")
    if args.resume:
        cmd.append("--resume")
    return cmd


def build_ffmpeg_command(ffmpeg: str, out_dir: Path, info: dict) -> list[str]:
    """Stitch Blender's PNG frames into an H.264 MP4 that YouTube and editors accept."""
    return [
        ffmpeg, "-y", "-loglevel", "error", "-stats",
        "-framerate", str(info["fps"]),
        "-start_number", str(info["frame_start"]),
        "-i", str(out_dir / "frames" / "frame_%04d.png"),
        "-frames:v", str(info["frame_end"] - info["frame_start"] + 1),   # ignore leftovers of an older, longer render
        "-c:v", "libx264", "-preset", "slow", "-crf", "14",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(out_dir / f"{info['name']}_{info['preset']}.mp4"),
    ]


def build_mux_command(ffmpeg: str, video: Path, audio: str, out: Path) -> list[str]:
    """Add a sound track to a finished video without re-encoding the picture."""
    return [ffmpeg, "-y", "-loglevel", "error", "-i", str(video), "-i", audio,
            "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(out)]


def read_info(out_dir: Path) -> dict:
    try:
        return json.loads((out_dir / INFO_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise RenderError(f"Blender finished but {INFO_FILE} is missing in {out_dir}; "
                          "check the Blender output above for errors.") from None


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="python -m scenesensei.render", description=__doc__.split("\n\n")[0])
    p.add_argument("scene", help="scene name (see scenesensei/scenes/) or path to a .py file")
    p.add_argument("--preset", default=DEFAULT_PRESET, choices=list(PRESETS),
                   help="; ".join(f"{n}: {pr.width}x{pr.height}, {pr.samples} samples" for n, pr in PRESETS.items()))
    p.add_argument("--frame", type=int, help="render only this frame, as a still image")
    p.add_argument("--samples", type=int, help="override the preset's samples per pixel")
    p.add_argument("--scale", type=int, default=100, help="resolution percentage, e.g. 50 for half size")
    p.add_argument("--blend-only", action="store_true", help="build the scene and save a .blend; no render")
    p.add_argument("--save-blend", action="store_true", help="also save the .blend next to the render")
    p.add_argument("--resume", action="store_true",
                   help="for frame presets: continue an interrupted render, skipping frames already done "
                        "(only use this if the scene has not changed since)")
    p.add_argument("--no-mp4", action="store_true", help="for frame presets: leave the PNG frames, skip ffmpeg")
    p.add_argument("--out", type=Path, help="output folder (default: scenesensei/renders/<scene>/<preset>)")
    p.add_argument("--blender", help="path to the Blender executable")
    p.add_argument("--dry-run", action="store_true", help="print the Blender command and stop")
    return p.parse_args(argv)


def run(args: argparse.Namespace) -> int:
    scene = resolve_scene(args.scene)
    out_dir = (args.out or RENDERS_DIR / scene.stem / args.preset).resolve()
    cmd = build_command(find_blender(args.blender), scene, out_dir, args)
    if args.dry_run:
        print(subprocess.list2cmdline(cmd))
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Rendering {scene.stem} [{args.preset}] -> {out_dir}", flush=True)
    code = subprocess.call(cmd)
    if code != 0:
        raise RenderError(f"Blender exited with code {code}; see its output above.")

    if args.blend_only or args.frame is not None:
        print(f"Done: {out_dir}")
        return 0

    preset = get_preset(args.preset)
    try:
        info = read_info(out_dir)
    except RenderError:
        if preset.output == "frames":      # needed to stitch; an MP4 preset is already finished
            raise
        print(f"Done: {out_dir}")
        return 0
    ffmpeg = shutil.which("ffmpeg")
    video = out_dir / f"{info['name']}_{info['preset']}.mp4"
    if preset.output == "frames" and not args.no_mp4:
        if not ffmpeg:
            print(f"Frames are in {out_dir / 'frames'}. ffmpeg is not installed, so no MP4 was made: "
                  "install ffmpeg (free) and re-run, or drag the frames into DaVinci Resolve as an "
                  "image sequence.")
            return 0
        code = subprocess.call(build_ffmpeg_command(ffmpeg, out_dir, info))
        if code != 0:
            raise RenderError(f"ffmpeg exited with code {code}; the frames are intact in {out_dir / 'frames'}.")

    audio = info.get("audio")
    if audio:
        if not ffmpeg:
            print(f"This scene has sound ({audio}) but ffmpeg is not installed, so the video is silent. "
                  "Install ffmpeg (free) and re-run, or add the sound in your editor.")
        elif video.is_file():
            with_audio = video.with_name(video.stem + "_with_audio.mp4")
            code = subprocess.call(build_mux_command(ffmpeg, video, audio, with_audio))
            if code != 0:
                raise RenderError(f"ffmpeg could not add the sound (exit code {code}); the silent video is {video}.")
            print(f"With sound: {with_audio}")
    print(f"Done: {out_dir}")
    return 0


def main(argv: list[str] | None = None) -> int:
    try:
        return run(parse_args(argv))
    except RenderError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
