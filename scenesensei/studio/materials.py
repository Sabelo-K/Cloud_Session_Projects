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
