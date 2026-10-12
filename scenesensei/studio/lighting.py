"""Lighting: the single biggest difference between a "3D render" and a premium-looking one."""
from __future__ import annotations

import math

import bpy

from scenesensei.color import parse_color
from scenesensei.studio.compat import ensure_nodes, pick_enum
from scenesensei.studio import stage


def _fresh_world(name: str = "World") -> bpy.types.NodeTree:
    scene = bpy.context.scene
    world = bpy.data.worlds.new(name)
    scene.world = world
    ensure_nodes(world)
    world.node_tree.nodes.clear()
    return world.node_tree


def ambient(color="#0b0d12", strength: float = 1.0) -> None:
    """A flat-colour world: a dark studio. Light then comes only from the lamps you add."""
    nt = _fresh_world()
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Color"].default_value = (*parse_color(color), 1.0)
    bg.inputs["Strength"].default_value = strength
    out = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])


def sky(sun_elevation_deg: float = 8.0, sun_rotation_deg: float = 0.0, strength: float = 1.0,
        dust: float = 2.0, sun_size_deg: float = 0.6) -> None:
    """A physically based sky with a sun. A low sun (3-10 degrees) gives a long golden-hour glow; raise
    it for daylight. `sun_rotation_deg` turns the sun around the horizon, `dust` hazes the air."""
    nt = _fresh_world()
    node = nt.nodes.new("ShaderNodeTexSky")
    # Blender 4.x calls the model "Nishita"; 5.x calls it single/multiple scattering.
    kind = pick_enum(node, "sky_type", "NISHITA", "MULTIPLE_SCATTERING", "SINGLE_SCATTERING")
    if kind:
        node.sky_type = kind
    for attr, value in (("sun_elevation", math.radians(sun_elevation_deg)),
                        ("sun_rotation", math.radians(sun_rotation_deg)),
                        ("sun_size", math.radians(sun_size_deg)), ("dust_density", dust),
                        ("sun_disc", True)):
        if hasattr(node, attr):
            setattr(node, attr, value)
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = strength
    out = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(node.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])


def hdri(path, strength: float = 1.0, rotation_deg: float = 0.0, camera_visible: bool = False,
         backdrop="#0b0d12") -> None:
    """Light the scene with a photographed environment (a free HDRI from polyhaven.com).

    Reflections on glossy and metal surfaces come from this image, which is most of what makes a
    product shot look real. By default the camera sees a plain `backdrop` colour instead of the
    photo, so your own backdrop stays clean while the HDRI still lights and reflects.
    """
    nt = _fresh_world()
    nodes, links = nt.nodes, nt.links
    coord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    mapping.inputs["Rotation"].default_value[2] = math.radians(rotation_deg)
    env = nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(str(path), check_existing=True)
    bg = nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = strength
    out = nodes.new("ShaderNodeOutputWorld")
    links.new(coord.outputs["Generated"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], env.inputs["Vector"])
    links.new(env.outputs["Color"], bg.inputs["Color"])
    if camera_visible:
        links.new(bg.outputs["Background"], out.inputs["Surface"])
        return
    flat = nodes.new("ShaderNodeBackground")
    flat.inputs["Color"].default_value = (*parse_color(backdrop), 1.0)
    is_camera = nodes.new("ShaderNodeLightPath")
    mix = nodes.new("ShaderNodeMixShader")
    links.new(is_camera.outputs["Is Camera Ray"], mix.inputs["Fac"])
    links.new(bg.outputs["Background"], mix.inputs[1])
    links.new(flat.outputs["Background"], mix.inputs[2])
    links.new(mix.outputs["Shader"], out.inputs["Surface"])


def aim(obj: bpy.types.Object, target) -> None:
    """Point `obj` at an object or an (x, y, z) location; it keeps pointing there if either moves."""
    if not isinstance(target, bpy.types.Object):
        target = stage.empty(f"{obj.name}_Target", target)
    con = obj.constraints.new("TRACK_TO")
    con.target = target
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"


def area_light(name: str, location, target, size: float = 3.0, size_y: float | None = None,
               energy: float = 500.0, color="#ffffff") -> bpy.types.Object:
    """A soft rectangular lamp aimed at `target`. Bigger = softer shadows and broader reflections."""
    light = bpy.data.lights.new(name, "AREA")
    light.shape = "SQUARE" if size_y is None else "RECTANGLE"
    light.size = size
    if size_y is not None:
        light.size_y = size_y
    light.energy = energy
    light.color = parse_color(color)
    obj = bpy.data.objects.new(name, light)
    obj.location = location
    bpy.context.scene.collection.objects.link(obj)
    aim(obj, target)
    return obj


def _polar(center, distance: float, azimuth_deg: float, elevation_deg: float):
    """A point `distance` from `center`. Azimuth 0 = towards the camera (-y), +90 = camera's right."""
    az, el = math.radians(azimuth_deg), math.radians(elevation_deg)
    return (center[0] + distance * math.sin(az) * math.cos(el),
            center[1] - distance * math.cos(az) * math.cos(el),
            center[2] + distance * math.sin(el))


def three_point(target, distance: float = 8.0, key="#fff1e0", fill="#cfe0ff", rim="#ffffff",
                intensity: float = 1.0, rim_intensity: float = 1.0) -> dict[str, bpy.types.Object]:
    """The classic studio rig: a bright warm key, a dim cool fill, and a rim light from behind that
    traces the edges of the subject and separates it from the background.

    `target` is an (x, y, z) point. Power is scaled with distance squared, so the exposure stays
    the same whatever `distance` you pick. `intensity` scales all three lamps, `rim_intensity` only
    the rim (a strong coloured rim also washes the backdrop and floor, so turn it down if so).
    """
    k = intensity * (distance / 5.0) ** 2
    return {
        "key": area_light("Key", _polar(target, distance, -40, 35), target, size=distance * 0.5,
                          energy=900 * k, color=key),
        "fill": area_light("Fill", _polar(target, distance, 55, 10), target, size=distance * 0.8,
                           energy=220 * k, color=fill),
        "rim": area_light("Rim", _polar(target, distance, 160, 30), target, size=distance * 0.4,
                          energy=1200 * k * rim_intensity, color=rim),
    }
