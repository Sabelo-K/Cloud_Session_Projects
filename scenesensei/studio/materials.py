"""Materials. Colours can be '#RRGGBB' (as in a colour picker) and are converted for Blender."""
from __future__ import annotations

from pathlib import Path

import bpy

from scenesensei.color import parse_color
from scenesensei.studio.compat import ensure_nodes, set_socket

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".exr", ".webp"}


def _new(name: str):
    mat = bpy.data.materials.new(name)
    ensure_nodes(mat)
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf is None:
        bsdf = nodes.new("ShaderNodeBsdfPrincipled")
        out = nodes.get("Material Output") or nodes.new("ShaderNodeOutputMaterial")
        mat.node_tree.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat, bsdf


def principled(name: str, color="#cccccc", metallic: float = 0.0, roughness: float = 0.5,
               ior: float = 1.45, coat: float = 0.0, coat_roughness: float = 0.03,
               transmission: float = 0.0, emission=None, emission_strength: float = 0.0,
               anisotropic: float = 0.0) -> bpy.types.Material:
    """The all-purpose physically based material. Roughness is the one to play with: 0 is a mirror."""
    mat, bsdf = _new(name)
    rgba = (*parse_color(color), 1.0)
    set_socket(bsdf, ("Base Color",), rgba)
    set_socket(bsdf, ("Metallic",), metallic)
    set_socket(bsdf, ("Roughness",), roughness)
    set_socket(bsdf, ("IOR",), ior)
    set_socket(bsdf, ("Coat Weight", "Clearcoat"), coat)
    set_socket(bsdf, ("Coat Roughness", "Clearcoat Roughness"), coat_roughness)
    set_socket(bsdf, ("Transmission Weight", "Transmission"), transmission)
    set_socket(bsdf, ("Anisotropic",), anisotropic)
    if emission is not None:
        set_socket(bsdf, ("Emission Color", "Emission"), (*parse_color(emission), 1.0))
        set_socket(bsdf, ("Emission Strength",), emission_strength)
    return mat


def metal(name: str, color="#d4af37", roughness: float = 0.25, anisotropic: float = 0.0):
    """Polished metal. Lower roughness = sharper reflections. Try anisotropic 0.5 for brushed metal."""
    return principled(name, color, metallic=1.0, roughness=roughness, anisotropic=anisotropic)


def gold(name: str = "Gold", roughness: float = 0.22):
    return metal(name, "#e8b84a", roughness)


def chrome(name: str = "Chrome", roughness: float = 0.04):
    return metal(name, "#e6e6ea", roughness)


def glass(name: str = "Glass", color="#ffffff", roughness: float = 0.0, ior: float = 1.5):
    return principled(name, color, roughness=roughness, ior=ior, transmission=1.0)


def glossy(name: str, color="#3366ff", roughness: float = 0.15):
    """Painted / plastic surface with a clear glossy coat on top."""
    return principled(name, color, roughness=0.5, coat=1.0, coat_roughness=roughness)


def emissive(name: str, color="#ffffff", strength: float = 10.0):
    """Glows, and lights nearby surfaces. Good for neon, screens and light strips."""
    return principled(name, "#000000", roughness=1.0, emission=color, emission_strength=strength)


def _find_map(folder: Path, *keys: str, avoid: tuple[str, ...] = ()) -> Path | None:
    files = sorted(p for p in folder.iterdir() if p.suffix.lower() in IMAGE_EXTENSIONS)
    for key in keys:
        for p in files:
            stem = p.stem.lower()
            if key in stem and not any(a in stem for a in avoid):
                return p
    return None


def textured(name: str, folder: str | Path, tile_m: float = 2.0, normal_strength: float = 1.0):
    """A PBR material from a texture folder, e.g. one downloaded from polyhaven.com/textures.

    Looks for colour (diff/albedo/color), roughness, metal and normal (OpenGL, `nor_gl`) maps by file
    name; whichever are missing are skipped. Needs UVs (primitives, `stage.cyclorama`, imported
    models). `tile_m` is how many metres one copy of the texture covers.
    """
    folder = Path(folder)
    if not folder.is_dir():
        raise FileNotFoundError(f"texture folder not found: {folder}")
    maps = {
        "Base Color": (_find_map(folder, "diff", "albedo", "basecolor", "base_color", "color"), True),
        "Roughness": (_find_map(folder, "rough"), False),
        "Metallic": (_find_map(folder, "metal"), False),
        "Normal": (_find_map(folder, "nor_gl", "normal_gl", "normal", avoid=("nor_dx", "normal_dx")), False),
    }
    if not any(path for path, _ in maps.values()):
        raise FileNotFoundError(f"no texture images (png/jpg/exr...) found in {folder}")

    mat, bsdf = _new(name)
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    coord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (1 / tile_m, 1 / tile_m, 1 / tile_m)
    links.new(coord.outputs["UV"], mapping.inputs["Vector"])
    for socket, (path, is_color) in maps.items():
        if path is None:
            continue
        tex = nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(str(path), check_existing=True)
        tex.image.colorspace_settings.name = "sRGB" if is_color else "Non-Color"
        links.new(mapping.outputs["Vector"], tex.inputs["Vector"])
        if socket == "Normal":
            nmap = nodes.new("ShaderNodeNormalMap")
            nmap.inputs["Strength"].default_value = normal_strength
            links.new(tex.outputs["Color"], nmap.inputs["Color"])
            links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
        else:
            links.new(tex.outputs["Color"], bsdf.inputs[socket])
    return mat


def _bare(name: str):
    """A material with an empty node tree, to build custom shaders from scratch."""
    mat = bpy.data.materials.new(name)
    ensure_nodes(mat)
    mat.node_tree.nodes.clear()
    return mat, mat.node_tree.nodes, mat.node_tree.links


def aura(name: str, color="#4fa3ff", strength: float = 4.0, edge: float = 0.35, flame: bool = False):
    """A see-through glowing shell: bright at the silhouette, clear in the middle (like a force field).
    Put it on a slightly oversized copy of the subject. Animate "Strength" on the node named "Glow"
    (`fx.animate_input`) to make it flare, and turn off the shell's shadows (`fx.glow_only`).
    With `flame=True` the glow breaks up into licking flames; animate "W" on the node named "Flow"
    to make them move."""
    mat, nodes, links = _bare(name)
    weight = nodes.new("ShaderNodeLayerWeight")
    weight.inputs["Blend"].default_value = edge
    glow = nodes.new("ShaderNodeEmission")
    glow.name = "Glow"
    glow.inputs["Color"].default_value = (*parse_color(color), 1.0)
    glow.inputs["Strength"].default_value = strength
    clear = nodes.new("ShaderNodeBsdfTransparent")
    mix = nodes.new("ShaderNodeMixShader")
    out = nodes.new("ShaderNodeOutputMaterial")
    mask = weight.outputs["Facing"]
    if flame:
        coord = nodes.new("ShaderNodeTexCoord")
        mapping = nodes.new("ShaderNodeMapping")
        mapping.inputs["Scale"].default_value = (2.6, 2.6, 1.5)    # stretched vertically, like flames
        noise = nodes.new("ShaderNodeTexNoise")
        noise.name = "Flow"
        noise.noise_dimensions = "4D"
        noise.inputs["Scale"].default_value = 1.4
        noise.inputs["Detail"].default_value = 6.0
        noise.inputs["Roughness"].default_value = 0.62
        ramp = nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.47
        ramp.color_ramp.elements[1].position = 0.6
        lift = nodes.new("ShaderNodeMath")
        lift.operation = "ADD"
        lift.inputs[1].default_value = 0.05
        gate = nodes.new("ShaderNodeMath")
        gate.operation = "MULTIPLY"
        links.new(coord.outputs["Object"], mapping.inputs["Vector"])
        links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
        links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
        links.new(ramp.outputs["Color"], lift.inputs[0])
        links.new(lift.outputs["Value"], gate.inputs[0])
        links.new(mask, gate.inputs[1])
        mask = gate.outputs["Value"]
    links.new(mask, mix.inputs["Fac"])
    links.new(clear.outputs["BSDF"], mix.inputs[1])
    links.new(glow.outputs["Emission"], mix.inputs[2])
    links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return mat


def fade(name: str, color="#ffffff", strength: float = 8.0, opacity: float = 1.0):
    """A uniform glowing sheet whose opacity ("Opacity" on the node named "Fade") you can animate: a
    flash, a whiteout, a fade to black (use color "#000000"). Opacity 0 is invisible, 1 solid."""
    mat, nodes, links = _bare(name)
    glow = nodes.new("ShaderNodeEmission")
    glow.inputs["Color"].default_value = (*parse_color(color), 1.0)
    glow.inputs["Strength"].default_value = strength
    clear = nodes.new("ShaderNodeBsdfTransparent")
    mix = nodes.new("ShaderNodeMixShader")
    mix.name = "Fade"
    mix.inputs["Fac"].default_value = opacity
    out = nodes.new("ShaderNodeOutputMaterial")
    links.new(clear.outputs["BSDF"], mix.inputs[1])
    links.new(glow.outputs["Emission"], mix.inputs[2])
    links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return mat
