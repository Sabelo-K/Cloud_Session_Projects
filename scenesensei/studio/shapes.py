"""Primitive shapes, built with bmesh, for dressing a set and building figures.

Every function takes an optional `parent` (an object, or None for the scene root), a location, and a
material, and returns the new object. Rotations are in degrees.
"""
from __future__ import annotations

import math

import bmesh
import bpy

from scenesensei.studio.compat import shade_smooth

Vec = tuple[float, float, float]


def link(obj: bpy.types.Object, parent: bpy.types.Object | None) -> bpy.types.Object:
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = parent
    return obj


def _mesh(name: str, bm: bmesh.types.BMesh, parent, location: Vec, material, scale: Vec = (1, 1, 1),
          rotation: Vec = (0, 0, 0)) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    obj.scale = scale
    obj.rotation_euler = tuple(math.radians(a) for a in rotation)
    if material is not None:
        mesh.materials.append(material)
    link(obj, parent)
    shade_smooth(obj)
    return obj


def ellipsoid(name: str, parent, location: Vec, radii: Vec, material, rotation: Vec = (0, 0, 0),
              segments: int = 24) -> bpy.types.Object:
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=segments // 2, radius=1.0)
    return _mesh(name, bm, parent, location, material, radii, rotation)


def cone(name: str, parent, location: Vec, radius: float, height: float, material,
         rotation: Vec = (0, 0, 0), tip_radius: float = 0.0, segments: int = 12) -> bpy.types.Object:
    """A spike (or a tapered cylinder with `tip_radius`), base at `location`, pointing up its local z."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments, radius1=radius,
                          radius2=tip_radius, depth=height)
    bmesh.ops.translate(bm, vec=(0, 0, height / 2), verts=bm.verts)   # base at the origin
    return _mesh(name, bm, parent, location, material, rotation=rotation)


def box(name: str, parent, location: Vec, size: Vec, material, rotation: Vec = (0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    return _mesh(name, bm, parent, location, material, size, rotation)


def torus(name: str, parent, location: Vec, major: float, minor: float, material,
          rotation: Vec = (0, 0, 0), major_segments: int = 48, minor_segments: int = 12):
    bm = bmesh.new()
    rings = []
    for i in range(major_segments):
        a = 2 * math.pi * i / major_segments
        ring = []
        for j in range(minor_segments):
            b = 2 * math.pi * j / minor_segments
            r = major + minor * math.cos(b)
            ring.append(bm.verts.new((r * math.cos(a), r * math.sin(a), minor * math.sin(b))))
        rings.append(ring)
    for i in range(major_segments):
        for j in range(minor_segments):
            bm.faces.new((rings[i][j], rings[(i + 1) % major_segments][j],
                          rings[(i + 1) % major_segments][(j + 1) % minor_segments],
                          rings[i][(j + 1) % minor_segments]))
    return _mesh(name, bm, parent, location, material, rotation=rotation)
