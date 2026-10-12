"""Small helpers that keep the studio code working across Blender versions (4.2 LTS and newer).

Blender renames things between releases (render engine ids, colour-look names, Principled BSDF
sockets). Instead of hard-coding one version's names, look up what this Blender calls them.
"""
from __future__ import annotations

import re


def enum_options(owner, prop: str) -> list[str]:
    """Every value `owner.prop` accepts right now.

    Blender builds some lists on demand (render engines, colour looks, compute devices), and they
    are not visible through `bl_rna`. Setting an impossible value makes Blender name the valid ones.
    """
    try:
        setattr(owner, prop, "__probe__")
    except TypeError as exc:
        return re.findall(r"'([^']*)'", str(exc).split("not found in", 1)[-1])
    return []


def pick_enum(owner, prop: str, *wanted: str) -> str | None:
    """The first valid value of `owner.prop` containing one of `wanted` (in order, case-insensitive)."""
    options = enum_options(owner, prop)
    for w in wanted:
        for option in options:
            if w.lower() in option.lower():
                return option
    return None


def set_socket(node, names: tuple[str, ...], value) -> bool:
    """Set the first input socket of `node` that exists under any of `names`. False if none do."""
    for name in names:
        sock = node.inputs.get(name)
        if sock is not None:
            sock.default_value = value
            return True
    return False


def shade_smooth(obj) -> None:
    mesh = obj.data
    if hasattr(mesh, "shade_smooth"):      # Blender 4.1+
        mesh.shade_smooth()
    else:
        for poly in mesh.polygons:
            poly.use_smooth = True


def ensure_nodes(datablock) -> None:
    """Make sure a material or world has a node tree. Blender 4.x needs `use_nodes`; Blender 5 always has one
    (and warns that `use_nodes` is going away), so only set it when there is no tree yet."""
    if datablock.node_tree is None:
        datablock.use_nodes = True
