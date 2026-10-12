"""Action effects: auras, shockwaves, flashes, debris, energy balls and beams, fades.

Everything here keys its own visibility, so an effect exists only between the frames you give it
(it is hidden from the render before and after). Colours are '#RRGGBB'. `fps` is needed only by the
effects that follow physics (debris), so they fall at the right speed.
"""
from __future__ import annotations

import math
import random

import bpy
from mathutils import Vector

from scenesensei.color import parse_color
from scenesensei.studio import materials, shapes

Vec = tuple[float, float, float]


def key(obj, frame: int, **props) -> None:
    """Set properties on `obj` and keyframe them at `frame`: key(rock, 12, location=(0, 0, 1), scale=(2, 2, 2))."""
    for prop, value in props.items():
        setattr(obj, prop, value)
        obj.keyframe_insert(prop, frame=frame)


def visible_between(obj, start: int, end: int | None = None) -> None:
    """Show `obj` from frame `start` (to frame `end`, if given). Hidden at every other frame."""
    key(obj, max(0, start - 1), hide_render=True)
    key(obj, start, hide_render=False)
    if end is not None:
        key(obj, end, hide_render=False)
        key(obj, end + 1, hide_render=True)


def animate_input(mat: bpy.types.Material, node: str, socket: str, values: dict[int, float]) -> None:
    """Keyframe one shader input over time: animate_input(aura, "Glow", "Strength", {1: 3, 40: 12})."""
    sock = mat.node_tree.nodes[node].inputs[socket]
    for frame, value in sorted(values.items()):
        sock.default_value = value
        sock.keyframe_insert("default_value", frame=frame)


def glow_only(obj) -> bpy.types.Object:
    """Stop a glow shell from casting shadows or being seen in reflections' shadows."""
    obj.visible_shadow = False
    return obj


def aura(parent, name: str, color: str, radii: Vec, location: Vec, strength: float = 4.0,
         flicker: tuple[int, int] | None = None, seed: int = 0) -> tuple[bpy.types.Object, bpy.types.Material]:
    """A flaming energy shell around `parent` (e.g. a figure's root). `flicker=(first, last)` makes the
    flames move and keys a ragged pulse on the shell's size between those frames. Returns (shell, material)."""
    mat = materials.aura(f"{name}_mat", color, strength, edge=0.5, flame=True)
    shell = glow_only(shapes.ellipsoid(name, parent, location, radii, mat, segments=24))
    if flicker:
        animate_input(mat, "Flow", "W", {flicker[0]: 0.0, flicker[1]: (flicker[1] - flicker[0]) * 0.22})
        rng = random.Random(seed)
        for frame in range(flicker[0], flicker[1] + 1, 2):
            k = rng.uniform(0.93, 1.08) * (1 + 0.04 * math.sin(frame * 0.9))
            key(shell, frame, scale=tuple(r * k for r in radii))
    return shell, mat


def shockwave(center: Vec, start: int, color: str = "#ffffff", radius: float = 10.0, duration: int = 16,
              strength: float = 14.0, name: str = "Shock", dome: bool = False) -> list[bpy.types.Object]:
    """A ring racing outwards along the ground, plus (with `dome=True`, for big blasts) a glowing dome
    that blooms and fades."""
    ring_mat = materials.emissive(f"{name}_ring_mat", color, strength)
    ring = shapes.torus(f"{name}_ring", None, (center[0], center[1], 0.12), 1.0, 0.045, ring_mat,
                        major_segments=64, minor_segments=8)
    parts = [(ring, ring_mat, "Principled BSDF", "Emission Strength", lambda r: (r, r, 1.0))]   # flat ribbon
    if dome:
        dome_mat = materials.aura(f"{name}_dome_mat", color, strength * 0.12, edge=0.35)
        shell = glow_only(shapes.ellipsoid(f"{name}_dome", None, (center[0], center[1], 0.0), (1, 1, 1),
                                           dome_mat, segments=32))
        parts.append((shell, dome_mat, "Glow", "Strength", lambda r: (r, r, r * 0.55)))
    end = start + duration
    for obj, mat, node, socket, scale_at in parts:
        for frame, frac in ((start, 0.04), (start + max(1, duration // 3), 0.7), (end, 1.0)):
            key(obj, frame, scale=scale_at(radius * frac))
        visible_between(obj, start, end - 1)       # at its last frame the ring is dark: drop it a frame early
        top = mat.node_tree.nodes[node].inputs[socket].default_value
        animate_input(mat, node, socket, {start: top, start + duration // 2: top * 0.5, end: 0.0})
    return [obj for obj, *_ in parts]


def flash(center: Vec, frame: int, duration: int = 8, radius: float = 2.5, color: str = "#ffffff",
          power: float = 60000.0, name: str = "Flash") -> bpy.types.Object:
    """A burst of light: a hot sphere that swells and vanishes, with a lamp that lights the neighbours."""
    mat = materials.emissive(f"{name}_mat", color, 30.0)
    ball = shapes.ellipsoid(name, None, center, (1, 1, 1), mat, segments=24)
    end = frame + duration
    key(ball, frame, scale=(0.05, 0.05, 0.05))
    key(ball, frame + 2, scale=(radius, radius, radius))
    key(ball, end, scale=(0.01, 0.01, 0.01))                       # shrinks away as it dims
    animate_input(mat, "Principled BSDF", "Emission Strength", {frame: 30.0, end - 1: 10.0, end: 0.0})
    visible_between(ball, frame, end)

    light = bpy.data.lights.new(f"{name}_light", "POINT")
    light.color = parse_color(color)
    light.shadow_soft_size = radius
    lamp = bpy.data.objects.new(f"{name}_light", light)
    lamp.location = center
    bpy.context.scene.collection.objects.link(lamp)
    for f, p in ((max(0, frame - 1), 0.0), (frame, power), (frame + duration, 0.0)):
        light.energy = p
        light.keyframe_insert("energy", frame=f)
    return ball


def debris(center: Vec, start: int, count: int = 40, speed: float = 11.0, size: tuple[float, float] = (0.06, 0.3),
           seed: int = 0, fps: int = 24, duration: int = 48, gravity: float = 16.0, material=None,
           name: str = "Debris") -> list[bpy.types.Object]:
    """Rocks thrown out of `center` that arc through the air and land. Pure ballistics, keyed every frame."""
    rng = random.Random(seed)
    material = material or materials.principled(f"{name}_mat", "#2b2530", roughness=0.9)
    rocks = []
    for i in range(count):
        r = rng.uniform(*size)
        rock = shapes.ellipsoid(f"{name}{i}", None, center, (r, r * rng.uniform(0.6, 1.1), r * rng.uniform(0.5, 0.9)),
                                material, segments=8)
        az, el = rng.uniform(0, 2 * math.pi), math.radians(rng.uniform(30, 75))
        v = rng.uniform(0.45, 1.0) * speed
        vel = Vector((v * math.cos(el) * math.cos(az), v * math.cos(el) * math.sin(az), v * math.sin(el)))
        spin = Vector((rng.uniform(-9, 9), rng.uniform(-9, 9), rng.uniform(-9, 9)))
        floor = r * 0.5
        for step in range(duration + 1):
            t = step / fps
            pos = Vector(center) + vel * t
            pos.z = center[2] + vel.z * t - 0.5 * gravity * t * t
            landed = pos.z <= floor
            pos.z = max(pos.z, floor)
            key(rock, start + step, location=tuple(pos), rotation_euler=tuple(s * t for s in spin))
            if landed:                                  # stays where it fell
                break
        visible_between(rock, start, start + duration)
        rocks.append(rock)
    return rocks


def ball(name: str, location: Vec, color: str, radii: dict[int, float], parent=None,
         strength: float = 14.0) -> bpy.types.Object:
    """A glowing energy sphere (a hot core inside a soft shell). `radii` maps frame -> radius, e.g.
    {185: 0.0, 200: 0.7}: it grows, holds, and is hidden outside the first and last frames."""
    core_mat = materials.emissive(f"{name}_core_mat", "#ffffff", strength)
    shell_mat = materials.aura(f"{name}_shell_mat", color, strength * 0.5, edge=0.6)
    core = shapes.ellipsoid(name, parent, location, (1, 1, 1), core_mat, segments=24)
    shell = glow_only(shapes.ellipsoid(f"{name}_shell", core, (0, 0, 0), (1.7, 1.7, 1.7), shell_mat,
                                       segments=24))
    for frame, radius in sorted(radii.items()):
        key(core, frame, scale=(max(radius, 0.001),) * 3)
    for obj in (core, shell):                       # hiding a parent does not hide its children
        visible_between(obj, min(radii), max(radii))
    return core


def beam(name: str, start: Vec, end: Vec, color: str, frames: tuple[int, int, int], radius: float = 0.35,
         strength: float = 18.0) -> bpy.types.Object:
    """A beam that shoots from `start` towards `end`: it grows over frames[0]..frames[1], holds, and
    disappears after frames[2]."""
    a, b = Vector(start), Vector(end)
    direction = b - a
    core_mat = materials.emissive(f"{name}_core_mat", "#ffffff", strength)
    glow_mat = materials.aura(f"{name}_glow_mat", color, strength * 0.4, edge=0.5)
    core = shapes.cone(name, None, start, radius * 0.6, 1.0, core_mat, tip_radius=radius * 0.6, segments=16)
    glow = glow_only(shapes.cone(f"{name}_glow", core, (0, 0, 0), radius * 1.9, 1.0, glow_mat,
                                 tip_radius=radius * 1.9, segments=16))
    core.rotation_mode = "QUATERNION"
    core.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(direction)
    first, full, last = frames
    key(core, first, scale=(1, 1, 0.01))
    key(core, full, scale=(1, 1, direction.length))
    key(core, last, scale=(1, 1, direction.length))
    for obj in (core, glow):
        visible_between(obj, first, last)
    return core


def fade_sheet(name: str, center: Vec, color: str, frames: dict[int, float], radius: float = 4.0,
               strength: float = 8.0) -> bpy.types.Object:
    """A glowing sphere that surrounds a camera at `center` and fades in or out: a whiteout (color
    "#ffffff") or a fade from/to black ("#000000"). `frames` maps frame -> opacity (0 clear, 1 solid)."""
    mat = materials.fade(f"{name}_mat", color, strength, opacity=0.0)
    sheet = shapes.ellipsoid(name, None, center, (radius,) * 3, mat, segments=24)
    glow_only(sheet)
    animate_input(mat, "Fade", "Fac", frames)
    visible_between(sheet, min(frames), max(frames))
    return sheet
