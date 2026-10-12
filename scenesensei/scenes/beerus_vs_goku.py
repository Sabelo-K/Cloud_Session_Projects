"""Beerus vs Goku: a 10-second stylised clash. Stand-off, close-ups, a charge, a shock-wave collision,
a flurry of blows, then a beam struggle that whites out into a title card.

An unofficial fan homage. The characters are low-poly stand-ins made from primitives in this file
(no ripped models or artwork). Dragon Ball belongs to its rights holders: a channel that monetises
videos like this can get Content ID claims, so check the platform's rules before publishing.

Run:  python -m scenesensei.render beerus_vs_goku --preset draft
Look at one moment:  python -m scenesensei.render beerus_vs_goku --preset preview --frame 110
Times below are in seconds; T(seconds) turns them into frame numbers.
"""
import math
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

from scenesensei import audio  # noqa: E402
from scenesensei.scene_args import parse_scene_args  # noqa: E402
from scenesensei.studio import camera, figure, fx, lighting, materials, output, shapes, stage  # noqa: E402

# ---- CONFIG --------------------------------------------------------------------------------
SECONDS = 10
GOKU_AURA = "#3aa0ff"
BEERUS_AURA = "#d04bff"
STAND = 5.5                    # how far each fighter starts from the centre (metres)
TITLE = "BEERUS vs GOKU"
SUBTITLE = "A SCENESENSEI DEMO"
# ---------------------------------------------------------------------------------------------

args = parse_scene_args(Path(__file__).stem)
FPS = args.preset.fps
frames = SECONDS * FPS


def T(seconds: float) -> int:
    return 1 + round(seconds * FPS)


def lerp(a, b):
    return lambda u: tuple(x + (y - x) * u for x, y in zip(a, b))


stage.reset_scene()
P = materials.principled

# ======================================================================== the arena ============
lighting.sky(sun_elevation_deg=2.5, sun_rotation_deg=20, strength=0.1, dust=5.0)
stage.ground(material=P("Ground", "#16101a", roughness=0.95), radius=4000)
rock = P("Rock", "#241b27", roughness=0.9)
stage.scatter("Spire", 26, "spire", 70, 220, (6, 16), seed=4, material=rock)
stage.scatter("Boulder", 36, "boulder", 9, 60, (0.4, 1.8), seed=9, material=rock, keep_clear=(0, 0, 8))
lighting.area_light("Key", (-4, -15, 8), (0, 0, 1.3), size=8, size_y=4, energy=11000, color="#ffe3c4")
lighting.area_light("GokuRim", (-11, 7, 3.5), (-4, 0, 1.4), size=4, size_y=6, energy=5000, color="#59b0ff")
lighting.area_light("BeerusRim", (11, 7, 3.5), (4, 0, 1.4), size=4, size_y=6, energy=5000, color="#e060ff")


# ======================================================================== the fighters =========
def spike(parent, name, center, radii, az_deg, el_deg, length, radius, mat):
    az, el = math.radians(az_deg), math.radians(el_deg)
    d = Vector((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)))
    base = Vector(center) + Vector((d.x * radii[0], d.y * radii[1], d.z * radii[2])) * 0.85
    rot = tuple(math.degrees(a) for a in Vector((0, 0, 1)).rotation_difference(d).to_euler())
    return shapes.cone(name, parent, tuple(base), radius, length, mat, rotation=rot, segments=8)


def eyes(head, name, white, pupil, spread=0.043, y=0.14, size=(0.02, 0.025, 0.017), slit=False):
    for side in (1, -1):
        shapes.ellipsoid(f"{name}_eye{side}", head, (0.118, spread * side, y), size, white, segments=12)
        radii = (0.01, 0.0035, 0.016) if slit else (0.01, 0.0105, 0.0105)
        shapes.ellipsoid(f"{name}_pupil{side}", head, (0.133, spread * side, y), radii, pupil, segments=10)


def brows(head, name, mat, tilt_deg, y=0.168):
    for side in (1, -1):    # inner ends lower = angry
        shapes.box(f"{name}_brow{side}", head, (0.118, 0.052 * side, y), (0.022, 0.07, 0.02), mat,
                   rotation=(tilt_deg * side, 0, 0))


def build_goku(x):
    skin = P("GokuSkin", "#f1b48b", roughness=0.55)
    orange = P("GokuGi", "#f26b10", roughness=0.8)
    blue = P("GokuBlue", "#1d52d4", roughness=0.7)
    hair = P("GokuHair", "#2f9bff", roughness=0.35, emission="#2f9bff", emission_strength=1.6)
    dark = P("Dark", "#101015", roughness=0.4)
    white = P("EyeWhite", "#f4f4f4", roughness=0.3)
    fig = figure.humanoid("Goku", skin, orange, orange, blue, blue, blue, location=(x, 0, 0))
    head = fig.joints["head"]
    c, r = (0.01, 0, 0.12), (0.125, 0.11, 0.145)
    for i, (az, el, ln, rad) in enumerate((
            (0, 62, 0.30, 0.06), (28, 66, 0.36, 0.065), (-28, 66, 0.36, 0.065), (62, 56, 0.33, 0.065),
            (-62, 56, 0.33, 0.065), (100, 48, 0.32, 0.065), (-100, 48, 0.32, 0.065), (140, 40, 0.34, 0.06),
            (-140, 40, 0.34, 0.06), (180, 52, 0.36, 0.06), (0, 88, 0.42, 0.07), (45, 82, 0.4, 0.065),
            (-45, 82, 0.4, 0.065), (135, 76, 0.38, 0.06), (-135, 76, 0.38, 0.06))):
        spike(head, f"GokuHair{i}", c, r, az, el, ln, rad, hair)
    eyes(head, "Goku", white, dark)
    brows(head, "Goku", dark, 24)
    for side in (1, -1):
        shapes.ellipsoid(f"GokuEar{side}", head, (0.0, 0.112 * side, 0.115), (0.02, 0.018, 0.04), skin, segments=10)
    shapes.ellipsoid("GokuChestV", fig.joints["chest"], (0.115, 0, 0.3), (0.1, 0.17, 0.2), blue, segments=16)
    shapes.ellipsoid("GokuGiChest", fig.joints["chest"], (0.135, 0, 0.24), (0.08, 0.2, 0.26), orange, segments=16)
    return fig


def build_beerus(x):
    skin = P("BeerusSkin", "#8f80b4", roughness=0.5)
    robe = P("BeerusRobe", "#3b2070", roughness=0.6)
    sash = P("BeerusSash", "#5a2fa0", roughness=0.6)
    gold = materials.gold("BeerusGold", roughness=0.25)
    boots = P("BeerusBoots", "#22123f", roughness=0.5)
    dark = P("Dark2", "#0e0b16", roughness=0.4)
    eye = P("BeerusEye", "#e9e26a", roughness=0.25, emission="#e9e26a", emission_strength=0.6)
    inner = P("EarInner", "#4a3a78", roughness=0.6)
    fig = figure.humanoid("Beerus", skin, robe, sash, boots, gold, gold, location=(x, 0, 0))
    fig.root.rotation_euler[2] = math.pi
    head, chest = fig.joints["head"], fig.joints["chest"]
    for side in (1, -1):    # tall cat ears
        shapes.cone(f"BeerusEar{side}", head, (-0.01, 0.075 * side, 0.2), 0.062, 0.26, skin,
                    rotation=(-14 * side, -6, 0), tip_radius=0.004, segments=10)
        shapes.cone(f"BeerusEarIn{side}", head, (0.012, 0.075 * side, 0.205), 0.036, 0.2, inner,
                    rotation=(-14 * side, -6, 0), tip_radius=0.003, segments=8)
        for k, tilt in enumerate((-18, 0, 18)):                       # whiskers
            shapes.cone(f"BeerusWhisker{side}{k}", head, (0.1, 0.075 * side, 0.075), 0.004, 0.2, dark,
                        rotation=(-90 * side + tilt * side, 0, -35 * side), tip_radius=0.001, segments=5)
    eyes(head, "Beerus", eye, dark, spread=0.048, y=0.145, size=(0.024, 0.034, 0.014), slit=True)
    brows(head, "Beerus", dark, 14, y=0.172)
    shapes.ellipsoid("BeerusNose", head, (0.128, 0, 0.1), (0.014, 0.022, 0.012), dark, segments=8)
    shapes.torus("BeerusCollar", chest, (0, 0, 0.5), 0.12, 0.028, gold, major_segments=36, minor_segments=8)
    shapes.ellipsoid("BeerusPectoral", chest, (0.135, 0, 0.32), (0.05, 0.19, 0.16), gold, segments=16)
    shapes.ellipsoid("BeerusSashFront", fig.joints["hips"], (0.13, 0, -0.02), (0.1, 0.16, 0.26), sash, segments=14)
    return fig


goku = build_goku(-STAND)
beerus = build_beerus(STAND)
goku_aura, goku_aura_mat = fx.aura(goku.root, "GokuAura", GOKU_AURA, (0.75, 0.75, 1.2), (0, 0, 0.95),
                                   strength=1.2, flicker=(1, T(9.1)), seed=1)
beerus_aura, beerus_aura_mat = fx.aura(beerus.root, "BeerusAura", BEERUS_AURA, (0.75, 0.75, 1.2), (0, 0, 0.95),
                                       strength=1.2, flicker=(1, T(9.1)), seed=2)
for shell in (goku_aura, beerus_aura):
    fx.visible_between(shell, 1, T(9.1))

# ======================================================================== poses ================
# Joint angles in degrees: arms/legs hang down, so negative ry swings them forward. See figure.py.
Z3 = (0, 0, 0)
POSES = {
    "guard": dict(chest=(0, 8, 0), head=(0, -5, 0), shoulder_l=(10, -50, 0), elbow_l=(0, -100, 0),
                  shoulder_r=(-10, -35, 0), elbow_r=(0, -110, 0), hip_l=(0, -28, 0), knee_l=(0, 45, 0),
                  hip_r=(0, 18, 0), knee_r=(0, 12, 0)),
    "dash": dict(chest=(0, 36, 0), head=(0, -22, 0), shoulder_l=(0, 55, 0), elbow_l=(0, 10, 0),
                 shoulder_r=(0, 55, 0), elbow_r=(0, 10, 0), hip_l=(0, -50, 0), knee_l=(0, 80, 0),
                 hip_r=(0, 40, 0), knee_r=(0, 30, 0)),
    "punch_r": dict(chest=(0, 10, 25), head=(0, -5, -15), shoulder_r=(0, -85, 0), elbow_r=(0, -8, 0),
                    shoulder_l=(10, -45, 0), elbow_l=(0, -105, 0), hip_l=(0, -35, 0), knee_l=(0, 55, 0),
                    hip_r=(0, 25, 0), knee_r=(0, 10, 0)),
    "punch_l": dict(chest=(0, 10, -25), head=(0, -5, 15), shoulder_l=(0, -85, 0), elbow_l=(0, -8, 0),
                    shoulder_r=(-10, -45, 0), elbow_r=(0, -105, 0), hip_r=(0, -35, 0), knee_r=(0, 55, 0),
                    hip_l=(0, 25, 0), knee_l=(0, 10, 0)),
    "kick_r": dict(chest=(0, -15, 0), head=(0, 5, 0), shoulder_l=(60, -10, 0), elbow_l=(0, -30, 0),
                   shoulder_r=(-50, -30, 0), elbow_r=(0, -60, 0), hip_r=(0, -85, 0), knee_r=(0, 15, 0),
                   hip_l=(0, 5, 0), knee_l=(0, 10, 0)),
    "kick_l": dict(chest=(0, -15, 0), head=(0, 5, 0), shoulder_r=(-60, -10, 0), elbow_r=(0, -30, 0),
                   shoulder_l=(50, -30, 0), elbow_l=(0, -60, 0), hip_l=(0, -85, 0), knee_l=(0, 15, 0),
                   hip_r=(0, 5, 0), knee_r=(0, 10, 0)),
    "block": dict(chest=(0, 5, 0), head=(0, 0, 0), shoulder_l=(-20, -70, 0), elbow_l=(0, -120, 0),
                  shoulder_r=(20, -70, 0), elbow_r=(0, -120, 0), hip_l=(0, -20, 0), knee_l=(0, 30, 0),
                  hip_r=(0, 25, 0), knee_r=(0, 20, 0)),
    "recoil": dict(chest=(0, -18, 0), head=(0, -10, 0), shoulder_l=(35, 20, 0), elbow_l=(0, -40, 0),
                   shoulder_r=(-35, 20, 0), elbow_r=(0, -40, 0), hip_l=(0, 10, 0), knee_l=(0, 15, 0),
                   hip_r=(0, -5, 0), knee_r=(0, 30, 0)),
    "ball": dict(chest=(0, 12, 0), head=(0, -8, 0), shoulder_l=(-18, -60, 0), elbow_l=(0, -62, 0),
                 shoulder_r=(18, -60, 0), elbow_r=(0, -62, 0), hip_l=(0, -30, 0), knee_l=(0, 42, 0),
                 hip_r=(0, 28, 0), knee_r=(0, 18, 0)),
    "fire": dict(chest=(0, 6, 0), head=(0, -4, 0), shoulder_l=(-8, -88, 0), elbow_l=(0, -5, 0),
                 shoulder_r=(8, -88, 0), elbow_r=(0, -5, 0), hip_l=(0, -30, 0), knee_l=(0, 40, 0),
                 hip_r=(0, 25, 0), knee_r=(0, 15, 0)),
}


def pose(fig, seconds, name, x=None, z=None):
    fig.pose(T(seconds), **POSES[name])
    if x is not None or z is not None:
        fig.root.location = (x if x is not None else fig.root.location[0], 0, z or 0)
        fig.root.keyframe_insert("location", frame=T(seconds))


def breathe(fig, t0, t1, base="guard"):
    """Stand-off: the guard pose with a slow rise and fall of the chest."""
    for i, t in enumerate([t0 + k * 0.5 for k in range(int((t1 - t0) / 0.5) + 1)]):
        p = {j: tuple(a) for j, a in POSES[base].items()}
        p["chest"] = (0, 8 + (3 if i % 2 else 0), 0)
        fig.pose(T(t), **p)


# ---- act 1: stand-off (0 - 3.5 s) ----
breathe(goku, 0, 3.0)
breathe(beerus, 0, 3.0)
for fig, x in ((goku, -STAND), (beerus, STAND)):
    fig.root.location = (x, 0, 0)
    fig.root.keyframe_insert("location", frame=1)
    fig.root.keyframe_insert("location", frame=T(3.5))

# ---- act 2: the charge (3.5 - 4.5 s) ----
DASH0, DASH1 = 3.5, 4.5
pose(goku, 3.4, "guard")
pose(beerus, 3.4, "guard")
pose(goku, DASH0 + 0.1, "dash")
pose(beerus, DASH0 + 0.1, "dash")
pose(goku, DASH1 - 0.1, "dash")
pose(beerus, DASH1 - 0.1, "dash")
for fig, x0, x1 in ((goku, -STAND, -0.78), (beerus, STAND, 0.78)):
    camera.animate(fig.root, lambda u, x0=x0, x1=x1: (x0 + (x1 - x0) * u ** 2.6, 0, 0),
                   T(DASH0), T(DASH1), ease=False)

# ---- act 3: impact and the flurry (4.5 - 7.5 s) ----
HITS = [   # time, goku pose + x, beerus pose + x, impact point, size
    (4.50, "punch_r", -0.62, "punch_l", 0.62, (0.0, 0, 1.45), 3.0),
    (5.00, "punch_l", -0.50, "block", 0.80, (0.35, 0, 1.5), 1.0),
    (5.30, "block", -0.85, "kick_r", 0.35, (-0.25, 0, 1.15), 1.0),
    (5.60, "punch_r", -0.40, "punch_l", 0.40, (0.0, 0, 1.5), 1.6),
    (5.90, "kick_r", -0.30, "recoil", 0.95, (0.3, 0, 1.3), 1.0),
    (6.20, "recoil", -1.00, "punch_r", 0.30, (-0.3, 0, 1.5), 1.0),
    (6.50, "punch_l", -0.30, "block", 0.75, (0.3, 0, 1.5), 1.0),
    (6.80, "block", -0.95, "kick_l", 0.28, (-0.3, 0, 1.2), 1.0),
    (7.10, "punch_r", -0.40, "punch_r", 0.40, (0.0, 0, 1.5), 1.8),
]
for t, gp, gx, bp, bx, _point, _size in HITS:
    pose(goku, t, gp, x=gx)
    pose(beerus, t, bp, x=bx)

# ---- act 4: knocked apart, charge, beams (7.5 - 9.2 s) ----
pose(goku, 7.45, "recoil", x=-0.4)
pose(beerus, 7.45, "recoil", x=0.4)
pose(goku, 7.62, "recoil", x=-4.5)
pose(beerus, 7.62, "recoil", x=4.5)
pose(goku, 7.85, "ball", x=-6.0)
pose(beerus, 7.85, "ball", x=6.0)
pose(goku, 8.25, "ball", x=-6.0)
pose(beerus, 8.25, "ball", x=6.0)
pose(goku, 8.4, "fire", x=-6.0)
pose(beerus, 8.4, "fire", x=6.0)
pose(goku, 9.3, "fire", x=-6.4)
pose(beerus, 9.3, "fire", x=6.4)

# ======================================================================== effects ==============
fx.animate_input(goku_aura_mat, "Glow", "Strength", {
    1: 1.2, T(3.4): 2.0, T(4.5): 12, T(5.2): 3.5, T(7.0): 7, T(7.6): 2.0, T(8.2): 8, T(9.0): 14})
fx.animate_input(beerus_aura_mat, "Glow", "Strength", {
    1: 1.2, T(3.4): 2.0, T(4.5): 12, T(5.2): 3.5, T(7.0): 7, T(7.6): 2.0, T(8.2): 8, T(9.0): 14})

fps = FPS
for i, (t, _gp, _gx, _bp, _bx, point, size) in enumerate(HITS):
    frame = T(t)
    big = size >= 2
    colour = "#ffffff" if big else ("#ffd9a0" if i % 2 else "#cfe6ff")
    fx.flash(point, frame, duration=5 if big else 5, radius=0.9 if big else 0.7 * size ** 0.5,
             power=90000 if big else 14000 * size, color=colour, name=f"Flash{i}")
    fx.shockwave((point[0], point[1], 0), frame, colour, radius=17 if big else 5.5 * size ** 0.5,
                 duration=24 if big else 11, strength=10 if big else 7, name=f"Shock{i}", dome=big)
fx.debris((0, 0, 1.2), T(4.5), count=46, speed=13, size=(0.07, 0.34), seed=3, fps=fps, duration=60)
fx.debris((0, 0, 1.2), T(5.6), count=14, speed=8, size=(0.05, 0.2), seed=8, fps=fps, duration=36, name="DebrisB")
fx.debris((0, 0, 1.2), T(7.1), count=22, speed=10, size=(0.05, 0.25), seed=12, fps=fps, duration=44, name="DebrisC")

# energy balls charge in each fighter's hands, then fire as beams that meet in the middle
fire_frame = T(8.4)
bpy_scene = bpy.context.scene
bpy_scene.frame_set(T(8.2))
goku_hands = Vector(goku.point("elbow_l", (0, 0, -0.33))).lerp(Vector(goku.point("elbow_r", (0, 0, -0.33))), 0.5)
beerus_hands = Vector(beerus.point("elbow_l", (0, 0, -0.33))).lerp(Vector(beerus.point("elbow_r", (0, 0, -0.33))), 0.5)
bpy_scene.frame_set(1)
fx.ball("GokuBall", tuple(goku_hands), GOKU_AURA, {T(7.85): 0.0, T(8.2): 0.5, fire_frame: 0.62, T(8.5): 0.0})
fx.ball("BeerusBall", tuple(beerus_hands), BEERUS_AURA, {T(7.85): 0.0, T(8.2): 0.5, fire_frame: 0.62, T(8.5): 0.0})
CLASH = (0.0, 0.0, goku_hands.z)
fx.beam("GokuBeam", tuple(goku_hands), CLASH, GOKU_AURA, (fire_frame, T(8.62), T(9.45)), radius=0.3)
fx.beam("BeerusBeam", tuple(beerus_hands), CLASH, BEERUS_AURA, (fire_frame, T(8.62), T(9.45)), radius=0.3)
fx.ball("ClashCore", CLASH, "#ffffff", {T(8.6): 0.0, T(8.85): 1.0, T(9.2): 3.6, T(9.45): 4.5}, strength=20)
fx.flash(CLASH, T(8.6), duration=6, radius=1.6, power=50000, color="#fff2d0", name="ClashFlash")

# ======================================================================== the title set ========
TX = 300.0
floor = stage.cyclorama(material=P("TitleFloor", "#0d0b12", roughness=0.18))
floor.location = (TX, 0, -0.02)
gold = materials.gold(roughness=0.2)
stage.text("Title", TITLE, size=0.62, extrude=0.1, bevel=0.012, material=gold, location=(TX, 0, 1.1))
stage.text("Subtitle", SUBTITLE, size=0.14, extrude=0.025, bevel=0.003, material=materials.chrome(roughness=0.12),
           location=(TX, 0, 0.55))
lighting.area_light("TitleKey", (TX - 3, -12, 6), (TX, 0, 1.1), size=9, size_y=4, energy=3500, color="#ffe9cf")
lighting.area_light("TitleRim", (TX + 6, 7, 3), (TX, 0, 1.1), size=4, size_y=6, energy=2500, color="#e060ff")
lighting.area_light("TitleRim2", (TX - 6, 7, 3), (TX, 0, 1.1), size=4, size_y=6, energy=2500, color="#59b0ff")

# ======================================================================== cameras ==============
SHOTS = []


def shot(name, t0, t1, loc0, loc1, tgt0, tgt1, lens, fstop):
    cam, target = camera.create(loc0, tgt0, focal_mm=lens, fstop=fstop, name=name)
    camera.animate(cam, lerp(loc0, loc1), T(t0), T(t1) - 1)
    camera.animate(target, lerp(tgt0, tgt1), T(t0), T(t1) - 1)
    camera.cut_to(cam, T(t0))
    SHOTS.append((cam, t0, t1))
    return cam


shot("A_Wide", 0.0, 2.5, (-1.5, -14.5, 0.8), (0.8, -11.8, 1.2), (0, 0, 1.6), (0, 0, 1.6), 35, 6.3)
shot("B_Goku", 2.5, 3.0, (-STAND + 2.1, -1.9, 1.72), (-STAND + 1.7, -1.6, 1.72), (-STAND, 0, 1.68), (-STAND, 0, 1.68), 85, 2.0)
shot("C_Beerus", 3.0, 3.5, (STAND - 2.1, -1.9, 1.72), (STAND - 1.7, -1.6, 1.72), (STAND, 0, 1.7), (STAND, 0, 1.7), 85, 2.0)
shot("D_Dash", 3.5, 4.5, (0, -12.5, 1.3), (0, -9.0, 1.2), (0, 0, 1.3), (0, 0, 1.3), 35, 5.0)
shot("E_Impact", 4.5, 5.0, (1.6, -5.6, 1.4), (0.9, -4.5, 1.45), (0, 0, 1.5), (0, 0, 1.5), 50, 4.0)
orbit_cam = shot("F_Orbit", 5.0, 5.9, (0, -6.5, 1.6), (0, -6.5, 1.6), (0, 0, 1.5), (0, 0, 1.5), 40, 4.0)
camera.orbit(orbit_cam, (0, 0, 1.5), 6.5, 0.1, -38, 26, T(5.0), T(5.9) - 1)
shot("G_Low", 5.9, 6.7, (-4.6, -3.6, 0.35), (-3.3, -3.0, 0.45), (0.8, 0, 1.6), (0.3, 0, 1.6), 28, 4.0)
shot("H_High", 6.7, 7.5, (4.0, -7.0, 6.0), (2.2, -5.4, 5.0), (0, 0, 1.0), (0, 0, 1.2), 35, 4.0)
shot("I_Charge", 7.5, 8.4, (0, -14, 1.6), (0, -11.5, 1.5), (0, 0, 1.7), (0, 0, 1.7), 30, 6.3)
shot("J_Clash", 8.4, 9.2, (0, -8.5, 1.7), (0, -5.5, 1.7), (0, 0, 1.6), (0, 0, 1.6), 38, 5.0)
shot("L_Title", 9.2, 10.0, (TX, -9.5, 1.5), (TX, -7.4, 1.4), (TX, 0, 1.05), (TX, 0, 1.05), 50, 3.2)

for cam, t0, t1 in SHOTS:
    for t, _gp, _gx, _bp, _bx, _pt, size in HITS:
        if t0 <= t < t1:
            camera.shake(cam, T(t), T(t) + (14 if size >= 2 else 5), amplitude=0.55 if size >= 2 else 0.12, seed=int(t * 10))
camera.shake(SHOTS[-2][0], T(8.6), T(9.19), amplitude=0.18, seed=77, decay=False)

# ---- transitions: whiteout into the title card ----
fx.fade_sheet("Whiteout", (0, -5.5, 1.7), "#ffffff", {T(8.95): 0.0, T(9.15): 1.0}, radius=7, strength=9)
fx.fade_sheet("TitleFadeIn", (TX, -7.4, 1.4), "#ffffff", {T(9.2): 1.0, T(9.75): 0.0}, radius=3, strength=9)
fx.fade_sheet("OpenFade", (-2, -22, 0.7), "#000000", {1: 1.0, T(0.7): 0.0}, radius=3, strength=1)

# ======================================================================== sound ================
SFX = [
    audio.Sound("rumble", 0.0, 10.0, 0.35),
    audio.Sound("rise", 2.0, 1.5, 0.55),
    audio.Sound("whoosh", 3.45, 1.0, 0.7, pan=-0.6),
    audio.Sound("whoosh", 3.5, 1.0, 0.7, pan=0.6),
    audio.Sound("boom", 4.5, 2.0, 1.0),
    audio.Sound("hit", 4.5, 0.4, 1.0),
]
for t, *_rest, size in HITS[1:]:
    SFX.append(audio.Sound("hit", t, 0.35, 0.65 + 0.12 * size, pan=-0.2 if int(t * 10) % 2 else 0.2))
    if size > 1.2:
        SFX.append(audio.Sound("boom", t, 1.0, 0.45 * size))
SFX += [
    audio.Sound("rise", 7.6, 1.0, 0.6),
    audio.Sound("zap", 8.4, 0.5, 0.6, pan=-0.5),
    audio.Sound("zap", 8.4, 0.5, 0.6, pan=0.5),
    audio.Sound("rumble", 8.4, 1.6, 0.9),
    audio.Sound("boom", 9.05, 0.95, 1.0),
]
sfx_path = args.out_dir / "sfx.wav"

output.configure(args, frame_start=1, frame_end=frames, audio=sfx_path)
bpy_scene.render.use_motion_blur = True     # fast dashes and punches look faster with blur
if not (args.blend_only or args.frame is not None):
    audio.write_wav(sfx_path, audio.mix(SFX, SECONDS, seed=7))
output.render(args)
