"""Stylised action-figure characters built from primitives, with joints you can pose and keyframe.

A figure is a hierarchy of empties (joints) with ellipsoid limbs hung off them, so animating means
keying a few rotation angles. Every figure faces +x. In degrees, for the joint rotations:

* arms and legs hang down (-z); a NEGATIVE `ry` swings them forward (+x), positive swings back
* the chest and head rise up (+z); a POSITIVE `ry` leans them forward
* `rx` lifts a limb sideways: positive moves it towards the figure's left (+y)
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import bpy
from mathutils import Vector

from scenesensei.studio.shapes import ellipsoid, link

JOINTS = ("hips", "chest", "head", "shoulder_l", "elbow_l", "shoulder_r", "elbow_r",
          "hip_l", "knee_l", "ankle_l", "hip_r", "knee_r", "ankle_r")
Vec = tuple[float, float, float]
THIGH, SHIN, FOOT, HIP_DROP = 0.45, 0.43, 0.055, 0.02   # thigh, shin-to-ankle, foot half-height; hip joint hangs HIP_DROP below the hips


def hips_height(angles: dict[str, Vec]) -> float:
    """How high the hips must be for the lower foot to just touch the ground, given the leg angles.
    Ankles stay level (see `Figure.pose`), so only the thigh and shin angles matter."""
    def drop(side: str) -> float:
        hip = math.radians(angles.get(f"hip_{side}", (0, 0, 0))[1])
        knee = hip + math.radians(angles.get(f"knee_{side}", (0, 0, 0))[1])
        return THIGH * math.cos(hip) + SHIN * math.cos(knee) + FOOT
    return HIP_DROP + max(drop("l"), drop("r"))


STAND_HIPS_Z = hips_height({})   # hip height (m) that puts the feet on the ground when standing straight


def joint(name: str, parent: bpy.types.Object | None, location: Vec = (0, 0, 0)) -> bpy.types.Object:
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_size = 0.05
    obj.location = location
    return link(obj, parent)


@dataclass
class Figure:
    name: str
    root: bpy.types.Object                    # stands on the ground; move/rotate this to place the figure
    joints: dict[str, bpy.types.Object]
    height: float                             # head-top height in metres, for aiming cameras

    def place(self, frame: int, location: Vec | None = None, yaw_deg: float | None = None) -> None:
        if location is not None:
            self.root.location = location
            self.root.keyframe_insert("location", frame=frame)
        if yaw_deg is not None:
            self.root.rotation_euler[2] = math.radians(yaw_deg)
            self.root.keyframe_insert("rotation_euler", frame=frame, index=2)

    def pose(self, frame: int, hips_z: float | None = None, **angles: Vec) -> None:
        """Key every joint at `frame`. Joints you leave out return to straight (0, 0, 0), so a pose
        always means the same thing no matter what came before. Angles are (rx, ry, rz) in degrees.
        The ankles keep the feet level and the hips are lowered so the lower foot stays on the
        ground; pass `hips_z` (metres) to override the height, e.g. for a jump."""
        unknown = set(angles) - set(JOINTS)
        if unknown:
            raise KeyError(f"unknown joint(s) {sorted(unknown)}; choose from {JOINTS}")
        for side in ("l", "r"):          # ankles level the feet unless a pose says otherwise
            if f"ankle_{side}" not in angles:
                lean = angles.get(f"hip_{side}", (0, 0, 0))[1] + angles.get(f"knee_{side}", (0, 0, 0))[1]
                angles[f"ankle_{side}"] = (0.0, -lean, 0.0)
        for name in JOINTS:
            rx, ry, rz = angles.get(name, (0.0, 0.0, 0.0))
            j = self.joints[name]
            j.rotation_euler = (math.radians(rx), math.radians(ry), math.radians(rz))
            j.keyframe_insert("rotation_euler", frame=frame)
        hips = self.joints["hips"]
        hips.location[2] = hips_height(angles) if hips_z is None else hips_z
        hips.keyframe_insert("location", frame=frame, index=2)

    def point(self, joint_name: str, local: Vec = (0, 0, 0)) -> Vec:
        """World position of a spot on a joint at the scene's current frame: call `scene.frame_set(f)`
        first. Handy for aiming an energy blast at a hand."""
        bpy.context.view_layer.update()
        p = self.joints[joint_name].matrix_world @ Vector(local)
        return (p.x, p.y, p.z)


def humanoid(name: str, skin, top, pants, boots, belt, wrist, location: Vec = (0, 0, 0),
             scale: float = 1.0) -> Figure:
    """Build a posable figure about 1.75 m tall (times `scale`) from the given materials.

    `top` covers torso and upper arms, `wrist` the cuffs, `belt` the waist band, `boots` the feet and
    lower legs, `pants` the thighs. Hair, ears, faces and outfit details are added by the caller with
    `ellipsoid` / `cone` / `box` / `torus`, parented to `fig.joints["head"]` etc.
    """
    root = joint(f"{name}", None, location)
    root.scale = (scale, scale, scale)
    hips = joint(f"{name}_hips", root, (0, 0, STAND_HIPS_Z))
    chest = joint(f"{name}_chest", hips, (0, 0, 0.12))
    head = joint(f"{name}_head", chest, (0, 0, 0.6))
    j = {"hips": hips, "chest": chest, "head": head}

    # torso: a pelvis, a ribcage and a waist band
    ellipsoid(f"{name}_pelvis", hips, (0, 0, 0.0), (0.17, 0.2, 0.15), pants)
    ellipsoid(f"{name}_torso", chest, (0, 0, 0.22), (0.19, 0.29, 0.33), top)
    ellipsoid(f"{name}_belt", hips, (0, 0, 0.1), (0.2, 0.23, 0.07), belt)
    ellipsoid(f"{name}_neck", chest, (0, 0, 0.52), (0.07, 0.07, 0.1), skin)
    ellipsoid(f"{name}_head_mesh", head, (0.01, 0, 0.12), (0.125, 0.11, 0.145), skin)

    for side, sy in (("l", 1), ("r", -1)):
        shoulder = joint(f"{name}_shoulder_{side}", chest, (0, 0.33 * sy, 0.42))
        elbow = joint(f"{name}_elbow_{side}", shoulder, (0, 0, -0.3))
        ellipsoid(f"{name}_deltoid_{side}", shoulder, (0, 0, 0.0), (0.1, 0.1, 0.1), top)
        ellipsoid(f"{name}_upper_arm_{side}", shoulder, (0, 0, -0.15), (0.075, 0.075, 0.19), top)
        ellipsoid(f"{name}_forearm_{side}", elbow, (0, 0, -0.14), (0.065, 0.065, 0.18), skin)
        ellipsoid(f"{name}_cuff_{side}", elbow, (0, 0, -0.24), (0.075, 0.075, 0.07), wrist)
        ellipsoid(f"{name}_fist_{side}", elbow, (0, 0, -0.33), (0.07, 0.065, 0.075), skin)
        hip = joint(f"{name}_hip_{side}", hips, (0, 0.11 * sy, -0.02))
        knee = joint(f"{name}_knee_{side}", hip, (0, 0, -0.45))
        ellipsoid(f"{name}_thigh_{side}", hip, (0, 0, -0.22), (0.105, 0.105, 0.26), pants)
        ellipsoid(f"{name}_shin_{side}", knee, (0, 0, -0.22), (0.08, 0.08, 0.25), boots)
        ankle = joint(f"{name}_ankle_{side}", knee, (0, 0, -SHIN))
        ellipsoid(f"{name}_foot_{side}", ankle, (0.07, 0, 0), (0.15, 0.075, FOOT), boots)
        j.update({f"shoulder_{side}": shoulder, f"elbow_{side}": elbow,
                  f"hip_{side}": hip, f"knee_{side}": knee, f"ankle_{side}": ankle})
    fig = Figure(name, root, j, height=1.75 * scale)
    fig.pose(1)
    return fig
