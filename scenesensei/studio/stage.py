"""Build the set: reset the scene, then add a curved studio backdrop, primitives and 3D text."""
from __future__ import annotations

import math
from pathlib import Path

import bmesh
import bpy

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
