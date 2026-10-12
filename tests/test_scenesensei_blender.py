"""SceneSensei's Blender side, run for real through the `bpy` module (tiny, fast renders).

Skipped when `bpy` is not installed (CI): it is a ~400 MB wheel. To run these locally:
    pip install bpy        # use the Python version the wheel supports (3.11 for Blender 4.x, 3.13 for 5.x)
    python -m pytest tests/test_scenesensei_blender.py
"""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

import pytest

bpy = pytest.importorskip("bpy")
from mathutils import Vector  # noqa: E402  (ships with bpy)

from scenesensei.scene_args import PACKAGE_DIR, parse_scene_args  # noqa: E402
from scenesensei.studio import camera, figure, fx, lighting, materials, output, shapes, stage  # noqa: E402
from scenesensei.studio.compat import enum_options, pick_enum  # noqa: E402

TINY = ["--scale", "10", "--samples", "2"]   # ~86x48 px, 2 samples: a render takes about a second


def run_scene(monkeypatch, script: Path, *argv: str) -> None:
    monkeypatch.setattr(sys, "argv", ["blender", "--", *argv])
    runpy.run_path(str(script), run_name="__main__")


def tiny_scene_script(tmp_path: Path, frames: int = 2) -> Path:
    """A two-frame scene built from the public studio API, for the animation/MP4 paths."""
    script = tmp_path / "tiny.py"
    script.write_text(f"""
from pathlib import Path
from scenesensei.scene_args import parse_scene_args
from scenesensei.studio import camera, lighting, materials, output, stage

args = parse_scene_args("tiny")
stage.reset_scene()
stage.cyclorama(material=materials.principled("Floor", "#888888"))
stage.sphere("S", 1.0, (0, 0, 1.0), materials.gold())
lighting.ambient("#555555")
lighting.three_point((0, 0, 1.0))
cam, _ = camera.create((0, -9, 2.0), (0, 0, 1.0))
camera.orbit(cam, (0, 0, 1.0), 9, 1.0, 0, 10, 1, {frames})
output.configure(args, 1, {frames})
output.render(args)
""", encoding="utf-8")
    return script


@pytest.mark.parametrize("scene", ["_template", "logo_reveal", "beerus_vs_goku"])
def test_shipped_scenes_render_a_still(monkeypatch, tmp_path, scene):
    run_scene(monkeypatch, PACKAGE_DIR / "scenes" / f"{scene}.py",
              "--preset", "draft", "--frame", "1", "--out", str(tmp_path), *TINY)
    still = tmp_path / "stills" / f"{scene}_f0001.png"
    assert still.is_file() and still.stat().st_size > 200


def test_blend_only_saves_a_scene_and_renders_nothing(monkeypatch, tmp_path):
    run_scene(monkeypatch, PACKAGE_DIR / "scenes" / "logo_reveal.py",
              "--preset", "draft", "--blend-only", "--out", str(tmp_path))
    assert (tmp_path / "logo_reveal.blend").is_file()
    assert not (tmp_path / "stills").exists() and not list(tmp_path.glob("*.mp4"))


def test_mp4_preset_writes_one_named_file(monkeypatch, tmp_path):
    run_scene(monkeypatch, tiny_scene_script(tmp_path), "--preset", "draft", "--out", str(tmp_path / "o"), *TINY)
    assert (tmp_path / "o" / "tiny_draft.mp4").stat().st_size > 0
    info = (tmp_path / "o" / output.INFO_FILE).read_text()
    assert '"frame_end": 2' in info and '"width": 86' in info


def test_frames_preset_writes_numbered_pngs_and_resume_skips_them(monkeypatch, tmp_path):
    out = tmp_path / "o"
    script = tiny_scene_script(tmp_path)
    run_scene(monkeypatch, script, "--preset", "final", "--out", str(out), *TINY)
    frames = sorted((out / "frames").glob("frame_*.png"))
    assert [f.name for f in frames] == ["frame_0001.png", "frame_0002.png"]
    marker = frames[0].stat().st_mtime_ns
    frames[1].unlink()
    run_scene(monkeypatch, script, "--preset", "final", "--out", str(out), "--resume", *TINY)
    assert frames[0].stat().st_mtime_ns == marker            # untouched
    assert frames[1].is_file()                                 # redone


def test_render_settings_follow_the_preset(monkeypatch, tmp_path):
    args = parse_scene_args("t", ["--", "--preset", "final", "--samples", "7", "--out", str(tmp_path)])
    stage.reset_scene()
    output.configure(args, 5, 20)
    scene = bpy.context.scene
    assert scene.render.engine == "CYCLES" and scene.cycles.samples == 7
    assert (scene.render.resolution_x, scene.render.resolution_y) == (1920, 1080)
    assert (scene.frame_start, scene.frame_end, scene.render.fps) == (5, 20, 24)
    assert scene.render.use_motion_blur and scene.cycles.use_denoising
    assert scene.view_settings.view_transform == "AgX" and "Medium High Contrast" in scene.view_settings.look
    assert scene.cycles.device in ("CPU", "GPU")


def test_compat_enum_discovery():
    scene = bpy.context.scene
    assert "CYCLES" in enum_options(scene.render, "engine")        # a dynamic list bl_rna does not show
    assert pick_enum(scene.view_settings, "view_transform", "agx") == "AgX"
    assert pick_enum(scene.render, "engine", "no-such-engine") is None
    assert scene.render.engine != "__probe__"                       # probing never changes anything


def test_cyclorama_is_a_floor_that_curves_into_a_wall_facing_the_camera():
    stage.reset_scene()
    obj = stage.cyclorama(height=30.0)
    zs = [v.co.z for v in obj.data.vertices]
    assert min(zs) == 0 and max(zs) == pytest.approx(30.0)
    assert obj.data.polygons[0].normal.z > 0.99                    # floor faces up
    assert obj.data.polygons[-1].normal.y < -0.99                  # wall faces the camera at -y


def test_text_stands_upright_facing_the_camera():
    stage.reset_scene()
    obj = stage.text("T", "HI", location=(0, 0, 1))
    bpy.context.view_layer.update()
    assert (obj.matrix_world.to_3x3() @ Vector((0, 0, 1))).y < -0.99     # the front of the letters faces -y
    assert (obj.matrix_world.to_3x3() @ Vector((0, 1, 0))).z > 0.99      # and "up" on the page is up


def test_camera_aims_focuses_and_eases():
    stage.reset_scene()
    cam, target = camera.create((0, -10, 2), (0, 0, 1), focal_mm=70, fstop=2.0)
    assert bpy.context.scene.camera == cam
    assert cam.data.dof.use_dof and cam.data.dof.focus_object == target and cam.data.lens == 70
    camera.dolly(cam, (0, -10, 2), (0, -6, 2), 1, 11)
    bpy.context.scene.frame_set(1)
    start = cam.matrix_world.translation.y
    bpy.context.scene.frame_set(11)
    end = cam.matrix_world.translation.y
    bpy.context.scene.frame_set(2)
    early = cam.matrix_world.translation.y
    assert start == pytest.approx(-10) and end == pytest.approx(-6)
    assert early - start < 0.1 * (end - start)                    # eased: barely moved after one frame
    assert camera.smootherstep(0) == 0 and camera.smootherstep(1) == 1 and camera.smootherstep(0.5) == 0.5


def test_three_point_keeps_exposure_when_distance_changes():
    stage.reset_scene()
    near = lighting.three_point((0, 0, 0), distance=5)
    far = lighting.three_point((0, 0, 0), distance=10)
    assert far["key"].data.energy == pytest.approx(near["key"].data.energy * 4)
    assert near["key"].location.x < 0 and near["fill"].location.x > 0 and near["rim"].location.y > 0


def test_hdri_world_hides_the_photo_from_the_camera(tmp_path):
    stage.reset_scene()
    img = bpy.data.images.new("probe", 4, 2, float_buffer=True)
    img.filepath_raw = str(tmp_path / "probe.hdr")
    img.file_format = "HDR"
    img.save()
    lighting.hdri(tmp_path / "probe.hdr", strength=0.5)
    types = {n.bl_idname for n in bpy.context.scene.world.node_tree.nodes}
    assert {"ShaderNodeTexEnvironment", "ShaderNodeLightPath", "ShaderNodeMixShader"} <= types
    lighting.hdri(tmp_path / "probe.hdr", camera_visible=True)
    assert "ShaderNodeMixShader" not in {n.bl_idname for n in bpy.context.scene.world.node_tree.nodes}


def test_textured_material_picks_maps_by_name(tmp_path):
    stage.reset_scene()
    for name in ("rock_diff_1k.png", "rock_rough_1k.png", "rock_nor_gl_1k.png", "rock_nor_dx_1k.png"):
        img = bpy.data.images.new(name, 4, 4)
        img.filepath_raw = str(tmp_path / name)
        img.file_format = "PNG"
        img.save()
    mat = materials.textured("Rock", tmp_path, tile_m=2.0)
    nodes = mat.node_tree.nodes
    loaded = sorted(Path(n.image.filepath).name for n in nodes if n.bl_idname == "ShaderNodeTexImage")
    assert loaded == ["rock_diff_1k.png", "rock_nor_gl_1k.png", "rock_rough_1k.png"]   # not the DirectX normal map
    colour = next(n for n in nodes if n.bl_idname == "ShaderNodeTexImage" and "diff" in n.image.filepath)
    assert colour.image.colorspace_settings.name == "sRGB"
    rough = next(n for n in nodes if n.bl_idname == "ShaderNodeTexImage" and "rough" in n.image.filepath)
    assert rough.image.colorspace_settings.name == "Non-Color"
    assert "ShaderNodeNormalMap" in {n.bl_idname for n in nodes}
    with pytest.raises(FileNotFoundError):
        materials.textured("x", tmp_path / "missing")
    (tmp_path / "empty").mkdir()
    with pytest.raises(FileNotFoundError, match="no texture images"):
        materials.textured("x", tmp_path / "empty")


def test_material_helpers_accept_hex_and_set_the_right_values():
    stage.reset_scene()
    gold = materials.gold()
    bsdf = gold.node_tree.nodes["Principled BSDF"]
    assert bsdf.inputs["Metallic"].default_value == 1.0
    r, g, b, _ = bsdf.inputs["Base Color"].default_value
    assert r > g > b                                              # gold is warm
    glass = materials.glass()
    key = "Transmission Weight" if "Transmission Weight" in glass.node_tree.nodes["Principled BSDF"].inputs else "Transmission"
    assert glass.node_tree.nodes["Principled BSDF"].inputs[key].default_value == 1.0


def test_beerus_vs_goku_renders_mid_impact_and_in_the_title(monkeypatch, tmp_path):
    script = PACKAGE_DIR / "scenes" / "beerus_vs_goku.py"
    for frame in (112, 239):                                      # just after the first impact; the title card
        run_scene(monkeypatch, script, "--preset", "draft", "--frame", str(frame), "--out", str(tmp_path), *TINY)
        assert (tmp_path / "stills" / f"beerus_vs_goku_f{frame:04d}.png").is_file()
    info = (tmp_path / output.INFO_FILE).read_text()
    assert '"frame_end": 240' in info and "sfx.wav" in info


def stance_feet_height(name: str, pose: dict) -> float:
    """Lowest point of either foot, in metres above the ground, for a posed figure."""
    stage.reset_scene()
    skin = materials.principled("s")
    fig = figure.humanoid(name, skin, skin, skin, skin, skin, skin)
    fig.pose(1, **pose)
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    lows = []
    for side in ("l", "r"):
        foot = bpy.data.objects[f"{name}_foot_{side}"]
        lows.append(min((foot.matrix_world @ Vector(c)).z for c in foot.bound_box))
    return min(lows)


@pytest.mark.parametrize("pose", [
    {},                                                                       # standing straight
    dict(hip_l=(0, -28, 0), knee_l=(0, 45, 0), hip_r=(0, 18, 0), knee_r=(0, 12, 0)),    # fighting stance
    dict(hip_l=(0, -50, 0), knee_l=(0, 80, 0), hip_r=(0, 40, 0), knee_r=(0, 30, 0)),    # sprint
    dict(hip_r=(0, -85, 0), knee_r=(0, 15, 0), hip_l=(0, 5, 0), knee_l=(0, 10, 0)),     # a high kick
])
def test_posed_figures_keep_their_feet_on_the_ground(pose):
    assert stance_feet_height("T", pose) == pytest.approx(0.0, abs=0.03)


def test_pose_rejects_unknown_joints():
    stage.reset_scene()
    skin = materials.principled("s")
    fig = figure.humanoid("T", skin, skin, skin, skin, skin, skin)
    with pytest.raises(KeyError, match="elbow_x"):
        fig.pose(1, elbow_x=(0, 0, 0))


def test_a_pose_resets_joints_it_does_not_mention():
    stage.reset_scene()
    skin = materials.principled("s")
    fig = figure.humanoid("T", skin, skin, skin, skin, skin, skin)
    fig.pose(1, shoulder_r=(0, -80, 0))
    fig.pose(10)
    bpy.context.scene.frame_set(10)
    assert fig.joints["shoulder_r"].rotation_euler[1] == pytest.approx(0)
    bpy.context.scene.frame_set(1)
    assert fig.joints["shoulder_r"].rotation_euler[1] == pytest.approx(-80 * 3.14159265 / 180, abs=1e-4)


def test_effects_exist_only_between_their_frames():
    stage.reset_scene()
    ball = fx.flash((0, 0, 1), 10, duration=5)
    ring, = fx.shockwave((0, 0, 0), 30, radius=5, duration=10)
    scene = bpy.context.scene
    seen = {}
    for frame in (5, 10, 14, 16, 29, 35, 41):
        scene.frame_set(frame)
        seen[frame] = (ball.hide_render, ring.hide_render)
    assert seen[5] == (True, True) and seen[10][0] is False and seen[14][0] is False
    assert seen[16][0] is True and seen[29][1] is True and seen[35][1] is False and seen[41][1] is True


def test_flash_does_not_leave_a_dark_ball_behind():
    stage.reset_scene()
    ball = fx.flash((0, 0, 1), 10, duration=5)
    scene = bpy.context.scene
    scene.frame_set(15)
    assert max(ball.scale) <= 0.011


def test_debris_lands_and_stays():
    stage.reset_scene()
    rocks = fx.debris((0, 0, 1.2), 5, count=6, seed=1, fps=24, duration=60)
    assert len(rocks) == 6
    scene = bpy.context.scene
    scene.frame_set(5 + 60)
    heights = [r.location.z for r in rocks]
    assert max(heights) < 0.3                                   # everything has come down
    scene.frame_set(5 + 3)
    assert max(r.location.z for r in rocks) > 1.2                # and was thrown upwards first


def test_beam_grows_from_its_start_towards_its_end():
    stage.reset_scene()
    beam = fx.beam("B", (-5, 0, 1), (0, 0, 1), "#3aa0ff", (10, 20, 40))
    scene = bpy.context.scene
    scene.frame_set(20)
    bpy.context.view_layer.update()
    tip = beam.matrix_world @ Vector((0, 0, 1))                  # the cylinder is 1 m tall before scaling
    assert (tip.x, tip.y, tip.z) == pytest.approx((0, 0, 1), abs=1e-4)
    assert (beam.matrix_world @ Vector((0, 0, 0))).x == pytest.approx(-5)


def test_camera_cuts_follow_the_markers():
    stage.reset_scene()
    a, _ = camera.create((0, -5, 1), (0, 0, 1), name="CamA")
    b, _ = camera.create((5, 0, 1), (0, 0, 1), name="CamB")
    camera.cut_to(a, 1)
    camera.cut_to(b, 20)
    scene = bpy.context.scene
    scene.frame_set(10)
    assert scene.camera == a
    scene.frame_set(25)
    assert scene.camera == b
    scene.frame_set(3)
    assert scene.camera == a


def test_camera_shake_decays_and_settles():
    stage.reset_scene()
    cam, _ = camera.create((0, -5, 1), (0, 0, 1))
    camera.shake(cam, 10, 20, amplitude=0.5, seed=3)
    scene = bpy.context.scene
    early = max(abs(c) for f in range(10, 13) for c in (scene.frame_set(f) or tuple(cam.delta_location)))
    late = max(abs(c) for f in range(18, 21) for c in (scene.frame_set(f) or tuple(cam.delta_location)))
    scene.frame_set(25)
    assert early > late and tuple(cam.delta_location) == (0.0, 0.0, 0.0)


def test_aura_and_fade_materials_expose_their_animatable_nodes():
    stage.reset_scene()
    flames = materials.aura("A", "#3aa0ff", flame=True)
    assert {"Glow", "Flow"} <= set(flames.node_tree.nodes.keys())
    assert "Flow" not in materials.aura("B").node_tree.nodes.keys()
    sheet = materials.fade("F", opacity=0.25)
    assert sheet.node_tree.nodes["Fade"].inputs["Fac"].default_value == pytest.approx(0.25)
    fx.animate_input(flames, "Glow", "Strength", {1: 1.0, 11: 5.0})
    bpy.context.scene.frame_set(11)
    assert flames.node_tree.nodes["Glow"].inputs["Strength"].default_value == pytest.approx(5.0)


def test_ground_faces_up_and_scatter_keeps_the_fighting_area_clear():
    stage.reset_scene()
    ground = stage.ground(radius=100)
    assert ground.data.polygons[0].normal.z > 0.99
    rocks = stage.scatter("R", 25, "boulder", 2, 40, (0.3, 1.0), seed=2, keep_clear=(0, 0, 8))
    spires = stage.scatter("S", 5, "spire", 50, 90, (3, 6), seed=2)
    assert len(rocks) == 25 and len(spires) == 5
    assert all((r.location.x ** 2 + r.location.y ** 2) ** 0.5 >= 8 for r in rocks)
    assert all(s.dimensions.z > s.dimensions.x * 2 for s in spires)             # tall and thin


def test_sky_world_uses_a_sky_texture_with_a_valid_model():
    stage.reset_scene()
    lighting.sky(sun_elevation_deg=4, strength=0.3)
    nodes = bpy.context.scene.world.node_tree.nodes
    sky = next(n for n in nodes if n.bl_idname == "ShaderNodeTexSky")
    assert sky.sky_type in ("NISHITA", "SINGLE_SCATTERING", "MULTIPLE_SCATTERING")
    assert sky.sun_elevation == pytest.approx(4 * 3.14159265 / 180, abs=1e-4)


def test_shapes_have_the_dimensions_asked_for():
    stage.reset_scene()
    spike = shapes.cone("C", None, (0, 0, 0), 0.5, 2.0, None)
    bpy.context.view_layer.update()
    assert spike.dimensions.z == pytest.approx(2.0) and min(v.co.z for v in spike.data.vertices) == pytest.approx(0)
    ring = shapes.torus("T", None, (0, 0, 0), 2.0, 0.25, None)
    bpy.context.view_layer.update()
    assert ring.dimensions.x == pytest.approx(4.5, abs=0.05) and ring.dimensions.z == pytest.approx(0.5, abs=0.02)
    pebble = shapes.ellipsoid("E", None, (0, 0, 0), (1, 2, 3), None)
    slab = shapes.box("B", None, (0, 0, 0), (1, 2, 3), None)
    bpy.context.view_layer.update()                       # dimensions are read from the evaluated object
    assert pebble.dimensions[:] == pytest.approx((2, 4, 6), abs=0.1)
    assert slab.dimensions[:] == pytest.approx((1, 2, 3))
