"""Camera: lens, depth of field, and smooth, eased moves."""
from __future__ import annotations

import math
import random
from collections.abc import Callable

import bpy

from scenesensei.studio import lighting, stage

Vec = tuple[float, float, float]


def create(location: Vec, target: "Vec | bpy.types.Object", focal_mm: float = 50.0, fstop: float = 2.8,
           name: str = "Camera") -> tuple[bpy.types.Object, bpy.types.Object]:
    """Add the scene camera, always aimed at `target`, focused on it, with a shallow depth of field.

    A longer lens (50-85 mm) and a low f-stop (1.8-4) give the soft, blurred background that reads
    as "filmed", not "computer generated". Returns (camera, target) so you can animate either.
    """
    if not isinstance(target, bpy.types.Object):
        target = stage.empty(f"{name}Target", target)
    data = bpy.data.cameras.new(name)
    data.lens = focal_mm
    data.clip_end = 500.0
    data.dof.use_dof = True
    data.dof.focus_object = target
    data.dof.aperture_fstop = fstop
    cam = bpy.data.objects.new(name, data)
    cam.location = location
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    lighting.aim(cam, target)
    return cam, target


def smootherstep(t: float) -> float:
    """0 to 1 with zero speed at both ends: moves ease in and out instead of starting abruptly."""
    t = min(1.0, max(0.0, t))
    return t * t * t * (t * (t * 6 - 15) + 10)


def animate(obj: bpy.types.Object, position: Callable[[float], Vec], frame_start: int, frame_end: int,
            ease: bool = True) -> None:
    """Move `obj` along `position(t)` (t runs 0 to 1) over the frame range, one keyframe per frame."""
    span = max(1, frame_end - frame_start)
    for frame in range(frame_start, frame_end + 1):
        t = (frame - frame_start) / span
        obj.location = position(smootherstep(t) if ease else t)
        obj.keyframe_insert("location", frame=frame)


def orbit(cam: bpy.types.Object, center: Vec, radius: float, height: float, start_deg: float,
          end_deg: float, frame_start: int, frame_end: int) -> None:
    """Swing the camera around `center`. 0 deg = straight in front (-y), positive = towards +x."""
    def position(t: float) -> Vec:
        a = math.radians(start_deg + (end_deg - start_deg) * t)
        return (center[0] + radius * math.sin(a), center[1] - radius * math.cos(a), center[2] + height)
    animate(cam, position, frame_start, frame_end)


def dolly(obj: bpy.types.Object, start: Vec, end: Vec, frame_start: int, frame_end: int) -> None:
    """Glide in a straight line from `start` to `end`."""
    def position(t: float) -> Vec:
        return tuple(a + (b - a) * t for a, b in zip(start, end))  # type: ignore[return-value]
    animate(obj, position, frame_start, frame_end)


def cut_to(cam: bpy.types.Object, frame: int) -> None:
    """Make `cam` the active camera from `frame` on (a hard cut). Add one for every shot, including the
    first, in any order. Works by binding the camera to a timeline marker."""
    marker = bpy.context.scene.timeline_markers.new(f"cut_{cam.name}_{frame}", frame=frame)
    marker.camera = cam


def shake(cam: bpy.types.Object, frame_start: int, frame_end: int, amplitude: float = 0.15,
          seed: int = 0, decay: bool = True) -> None:
    """Jolt the camera (an impact, an explosion). `amplitude` is in metres; with `decay` it dies away
    over the range. It is added on top of any move already keyed on the camera."""
    rng = random.Random(seed)
    span = max(1, frame_end - frame_start)
    for frame in range(frame_start, frame_end + 1):
        k = amplitude * ((1 - (frame - frame_start) / span) if decay else 1.0)
        cam.delta_location = (rng.uniform(-k, k), rng.uniform(-k, k), rng.uniform(-k, k))
        cam.keyframe_insert("delta_location", frame=frame)
    cam.delta_location = (0.0, 0.0, 0.0)
    cam.keyframe_insert("delta_location", frame=frame_end + 1)
