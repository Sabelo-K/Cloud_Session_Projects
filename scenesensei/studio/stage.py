"""Build the set: reset the scene, then add a curved studio backdrop, primitives and 3D text."""
from __future__ import annotations

import math
import random
from pathlib import Path

import bmesh
import bpy

from scenesensei.studio import shapes
from scenesensei.studio.compat import shade_smooth


def reset_scene() -> bpy.types.Scene:
    """Start from an empty scene so a script always builds the same thing, however it is run."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene


def _add(obj: bpy.types.Object, material=None) -> bpy.types.Object:
    bpy.context.scene.collection.objects.link(obj)
    if material is not None and hasattr(obj.data, "materials"):
        obj.data.materials.append(material)
    return obj


def _mesh_object(name: str, bm: bmesh.types.BMesh, material=None, smooth: bool = True):
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = _add(bpy.data.objects.new(name, mesh), material)
    if smooth:
        shade_smooth(obj)
    return obj


def empty(name: str, location=(0.0, 0.0, 0.0)) -> bpy.types.Object:
    """An invisible marker: something for the camera or a light to aim at."""
    obj = bpy.data.objects.new(name, None)
    obj.location = location
    bpy.context.scene.collection.objects.link(obj)
    return obj


def sphere(name: str, radius: float, location, material=None, segments: int = 64):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=segments // 2, radius=radius,
                              calc_uvs=True)
    obj = _mesh_object(name, bm, material)
    obj.location = location
    return obj


def cyclorama(name: str = "Cyclorama", width: float = 60.0, front: float = 20.0, back: float = 12.0,
              radius: float = 6.0, height: float = 30.0, steps: int = 32, material=None):
    """A seamless studio backdrop: a floor that curves up into a wall, with no horizon line.

    The floor is the z=0 plane. `back` is where the wall stands (y), `front` how far the floor runs
    towards the camera (at -y). UVs are in metres, so a texture tiles at a predictable size.
    """
    y0 = back - radius
    profile = [(-front, 0.0), (y0, 0.0)]
    for i in range(1, steps + 1):
        a = math.pi / 2 * i / steps
        profile.append((y0 + radius * math.sin(a), radius - radius * math.cos(a)))
    profile.append((back, height))

    run = [0.0]                        # distance along the profile, for the V coordinate
    for (ya, za), (yb, zb) in zip(profile, profile[1:]):
        run.append(run[-1] + math.hypot(yb - ya, zb - za))

    bm = bmesh.new()
    left = [bm.verts.new((-width / 2, y, z)) for y, z in profile]
    right = [bm.verts.new((width / 2, y, z)) for y, z in profile]
    uv = bm.loops.layers.uv.new("UVMap")
    for i in range(len(profile) - 1):
        face = bm.faces.new((left[i], right[i], right[i + 1], left[i + 1]))
        for loop, (u, v) in zip(face.loops, ((0, run[i]), (width, run[i]),
                                             (width, run[i + 1]), (0, run[i + 1]))):
            loop[uv].uv = (u, v)
    return _mesh_object(name, bm, material)


def text(name: str, body: str, size: float = 1.0, extrude: float = 0.1, bevel: float = 0.01,
         material=None, font_path: str | Path | None = None, location=(0.0, 0.0, 1.0)):
    """Extruded 3D text, standing upright and facing the camera (which sits at -y).

    Blender's built-in font is plain. For a branded look, pass `font_path` to any .ttf/.otf you
    are licensed to use (Google Fonts are free).
    """
    curve = bpy.data.curves.new(name, "FONT")
    curve.body = body
    curve.size = size
    curve.extrude = extrude
    curve.bevel_depth = bevel
    curve.bevel_resolution = 4
    curve.align_x = "CENTER"
    curve.align_y = "CENTER"
    if font_path:
        curve.font = bpy.data.fonts.load(str(font_path))
    obj = _add(bpy.data.objects.new(name, curve), material)
    obj.rotation_euler = (math.pi / 2, 0.0, 0.0)
    obj.location = location
    return obj


def ground(name: str = "Ground", radius: float = 400.0, material=None, segments: int = 96):
    """A huge flat disc at z=0 that reaches the horizon, for outdoor scenes. UVs are in metres."""
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=True, radius=radius, segments=segments)
    uv = bm.loops.layers.uv.new("UVMap")
    for face in bm.faces:
        if face.normal.z < 0:
            face.normal_flip()
        for loop in face.loops:
            loop[uv].uv = (loop.vert.co.x, loop.vert.co.y)
    return _mesh_object(name, bm, material)


def scatter(name: str, count: int, kind: str, inner: float, outer: float, size: tuple[float, float],
            seed: int = 0, material=None, keep_clear: tuple[float, float, float] | None = None):
    """Scatter rocks around the origin between radii `inner` and `outer` (metres): `kind` "boulder"
    for rounded stones or "spire" for tall jagged pillars. `size` is the (min, max) base radius; spires
    are 4-9 times taller than wide. `keep_clear` = (x, y, radius) leaves a circle empty."""
    rng = random.Random(seed)
    made = []
    while len(made) < count:
        angle, dist = rng.uniform(0, 2 * math.pi), rng.uniform(inner, outer)
        x, y = dist * math.cos(angle), dist * math.sin(angle)
        if keep_clear and math.hypot(x - keep_clear[0], y - keep_clear[1]) < keep_clear[2]:
            continue
        r = rng.uniform(*size)
        if kind == "spire":
            made.append(shapes.cone(f"{name}{len(made)}", None, (x, y, -0.5), r, r * rng.uniform(4, 9),
                                    material, rotation=(rng.uniform(-6, 6), rng.uniform(-6, 6),
                                                        rng.uniform(0, 360)),
                                    tip_radius=r * rng.uniform(0.0, 0.25), segments=rng.choice((5, 6, 7))))
        else:
            made.append(shapes.ellipsoid(f"{name}{len(made)}", None, (x, y, r * 0.3),
                                         (r, r * rng.uniform(0.7, 1.2), r * rng.uniform(0.5, 0.9)), material,
                                         rotation=(0, 0, rng.uniform(0, 360)), segments=10))
    return made
