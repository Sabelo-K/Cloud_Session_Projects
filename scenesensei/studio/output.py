"""Render settings and the render itself: quality, colour, GPU, file format, output folder."""
from __future__ import annotations

import json

import bpy

from scenesensei.presets import scaled_size
from scenesensei.scene_args import SceneArgs
from scenesensei.studio.compat import enum_options, pick_enum

INFO_FILE = "render_info.json"   # read by scenesensei.render to stitch frames into an MP4
_GPU_ORDER = ("OPTIX", "CUDA", "HIP", "ONEAPI", "METAL")   # fastest first; Blender lists only what the OS supports


def use_best_device(scene: bpy.types.Scene) -> str:
    """Render on the GPU if Blender can find a supported one, else on the CPU. Returns what it chose."""
    prefs = bpy.context.preferences.addons["cycles"].preferences
    kinds = enum_options(prefs, "compute_device_type")
    for kind in _GPU_ORDER:
        if kind not in kinds:
            continue
        prefs.compute_device_type = kind
        prefs.get_devices()
        gpus = [d for d in prefs.devices if d.type == kind]
        if gpus:
            for device in prefs.devices:
                device.use = device.type == kind
            scene.cycles.device = "GPU"
            return f"GPU ({kind}): " + ", ".join(d.name for d in gpus)
    prefs.compute_device_type = "NONE"
    scene.cycles.device = "CPU"
    return "CPU (no supported GPU found)"


def _cycles(scene: bpy.types.Scene, args: SceneArgs) -> None:
    scene.render.engine = "CYCLES"
    cy = scene.cycles
    cy.samples = args.samples
    cy.use_adaptive_sampling = True       # stop early on clean areas, spend samples where it's noisy
    cy.adaptive_threshold = 0.01
    cy.use_denoising = True               # Intel Open Image Denoise: cleans a low-sample render
    cy.denoiser = "OPENIMAGEDENOISE"
    cy.max_bounces = args.preset.bounces
    cy.glossy_bounces = args.preset.bounces
    cy.transmission_bounces = args.preset.bounces
    cy.sample_clamp_indirect = 10.0       # tames bright "firefly" specks
    scene.render.use_motion_blur = args.preset.motion_blur
    scene.render.motion_blur_shutter = 0.5
    print(f"[scenesensei] device: {use_best_device(scene)}", flush=True)


def _colour(scene: bpy.types.Scene) -> None:
    """AgX handles bright highlights gracefully (they roll off instead of clipping to flat white)."""
    view = scene.view_settings
    transform = pick_enum(view, "view_transform", "AgX", "Filmic", "Standard")
    if transform:
        view.view_transform = transform
    look = pick_enum(view, "look", "Medium High Contrast")
    if look:
        view.look = look


def _file_format(image_settings, video: bool) -> None:
    """Blender 5 picks image vs video with `media_type` first; Blender 4.2 has only `file_format`."""
    if hasattr(image_settings, "media_type"):
        image_settings.media_type = "VIDEO" if video else "IMAGE"
    image_settings.file_format = "FFMPEG" if video else "PNG"


def _output(scene: bpy.types.Scene, args: SceneArgs) -> None:
    r = scene.render
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    r.use_file_extension = True
    if args.frame is not None:
        _file_format(r.image_settings, video=False)
        r.filepath = str(out / "stills" / f"{args.name}_f{args.frame:04d}")
    elif args.preset.output == "frames":
        _file_format(r.image_settings, video=False)
        r.image_settings.color_mode = "RGB"
        r.use_overwrite = not args.resume  # --resume: skip frames that are already on disk
        r.use_placeholder = False
        r.filepath = str(out / "frames" / "frame_")
    else:
        _file_format(r.image_settings, video=True)
        r.ffmpeg.format = "MPEG4"
        r.ffmpeg.codec = "H264"
        r.ffmpeg.constant_rate_factor = "HIGH"
        r.ffmpeg.ffmpeg_preset = "GOOD"
        r.ffmpeg.audio_codec = "NONE"
        r.use_file_extension = False
        r.filepath = str(out / f"{args.name}_{args.preset.name}.mp4")


def configure(args: SceneArgs, frame_start: int = 1, frame_end: int = 120) -> None:
    """Apply the preset (size, quality, colour, device, output) to the current scene."""
    scene = bpy.context.scene
    r, p = scene.render, args.preset
    width, height = scaled_size(p, args.scale)
    r.resolution_x, r.resolution_y, r.resolution_percentage = width, height, 100
    r.fps, r.fps_base = p.fps, 1.0
    r.film_transparent = False
    scene.frame_start, scene.frame_end = frame_start, frame_end
    _cycles(scene, args)
    _colour(scene)
    _output(scene, args)
    info = {"name": args.name, "preset": p.name, "fps": p.fps, "frame_start": frame_start,
            "frame_end": frame_end, "width": width, "height": height, "output": p.output}
    (args.out_dir / INFO_FILE).write_text(json.dumps(info, indent=2), encoding="utf-8")


def save_blend(args: SceneArgs) -> str:
    """Save the scene as a .blend you can open in Blender to look around and tweak."""
    path = str(args.out_dir / f"{args.name}.blend")
    bpy.ops.wm.save_as_mainfile(filepath=path, copy=True, relative_remap=False)
    print(f"[scenesensei] saved {path}", flush=True)
    return path


def render(args: SceneArgs) -> None:
    """Render what `configure` set up: the whole animation, one still (--frame), or nothing (--blend-only)."""
    if args.blend_only or args.save_blend:
        save_blend(args)
    if args.blend_only:
        return
    scene = bpy.context.scene
    if args.frame is not None:
        scene.frame_set(args.frame)
        bpy.ops.render.render(write_still=True)
    else:
        bpy.ops.render.render(animation=True)
