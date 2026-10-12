"""SceneSensei logo reveal: gold 3D title on a dark glossy studio floor, with a light that sweeps
across the letters while the camera drifts in. 6 seconds.

Run:  python -m scenesensei.render logo_reveal --preset draft
Copy this file to start your own scene; everything you would change is in the CONFIG block.
"""
import math
import sys
from pathlib import Path

# Lets the script run both from `python -m scenesensei.render` and when pasted into Blender.
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scenesensei.scene_args import parse_scene_args  # noqa: E402
from scenesensei.studio import camera, lighting, materials, output, stage  # noqa: E402

# ---- CONFIG --------------------------------------------------------------------------------
TITLE = "SCENESENSEI"
TITLE_COLOR = "#e8b84a"        # gold
FLOOR_COLOR = "#14161c"
RIM_COLOR = "#4fd1c5"          # teal edge light
FONT = None                    # e.g. "C:/Windows/Fonts/impact.ttf" for a bolder look
SECONDS = 6
# ---------------------------------------------------------------------------------------------

args = parse_scene_args(Path(__file__).stem)
frames = SECONDS * args.preset.fps

stage.reset_scene()

# Set: a seamless dark studio with a slightly glossy floor that reflects the title.
stage.cyclorama(material=materials.principled("Floor", FLOOR_COLOR, roughness=0.22))
title = stage.text("Title", TITLE, size=0.85, extrude=0.12, bevel=0.014,
                   material=materials.gold(roughness=0.2), font_path=FONT, location=(0, 0, 1.0))
stage.sphere("Chrome", 0.42, (-2.0, -2.3, 0.42), materials.chrome())
stage.sphere("Glass", 0.32, (2.1, -2.7, 0.32), materials.glass(color="#dff3ff"))

# Light: a dark room, a soft key, and a thin strip light that travels across the letters.
hdri_dir = _ROOT / "scenesensei" / "assets" / "hdri"
hdris = sorted([*hdri_dir.glob("*.hdr"), *hdri_dir.glob("*.exr")])
if hdris:
    lighting.hdri(hdris[0], strength=0.6, backdrop=FLOOR_COLOR)
else:
    lighting.ambient("#06070a")
focus = (0, 0, 1.0)
rig = lighting.three_point(focus, distance=9, rim=RIM_COLOR, intensity=0.9, rim_intensity=0.45)
lighting.area_light("Softbox", (0, -17, 2.5), focus, size=12, size_y=5, energy=2000)   # big panel behind the camera: lights the flat faces of the gold
sweep = lighting.area_light("Sweep", (-9, -5, 3.5), focus, size=0.5, size_y=7, energy=1300)
camera.animate(sweep, lambda t: (-9 + 18 * t, -5, 3.5), 1, frames)

# Camera: 70 mm, shallow depth of field, a slow eased drift forward and around.
cam, _ = camera.create(location=(0, -14, 2.2), target=focus, focal_mm=70, fstop=3.2)
camera.orbit(cam, center=focus, radius=14, height=1.0, start_deg=-14, end_deg=6,
             frame_start=1, frame_end=frames)

output.configure(args, frame_start=1, frame_end=frames)
output.render(args)
