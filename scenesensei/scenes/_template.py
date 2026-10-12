"""Starting point for a new scene: copy this file, rename it, and edit.

Run:  python -m scenesensei.render my_scene --preset draft
"""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scenesensei.scene_args import parse_scene_args  # noqa: E402
from scenesensei.studio import camera, lighting, materials, output, stage  # noqa: E402

SECONDS = 4

args = parse_scene_args(Path(__file__).stem)
frames = SECONDS * args.preset.fps

stage.reset_scene()

# 1. The set and the subject (replace the sphere with your own objects or an imported model).
stage.cyclorama(material=materials.principled("Floor", "#d9dce3", roughness=0.4))
stage.sphere("Subject", 1.0, (0, 0, 1.0), materials.glossy("Paint", "#2b6cff"))

# 2. Light: dark room + studio rig. Swap `ambient` for `lighting.hdri(path)` for realistic reflections.
lighting.ambient("#8a8f9c", strength=0.35)
lighting.three_point((0, 0, 1.0), distance=8)

# 3. Camera: long lens, shallow depth of field, slow eased orbit.
cam, _ = camera.create(location=(0, -10, 2.0), target=(0, 0, 1.0), focal_mm=60, fstop=2.8)
camera.orbit(cam, center=(0, 0, 1.0), radius=10, height=1.0, start_deg=-18, end_deg=18,
             frame_start=1, frame_end=frames)

output.configure(args, frame_start=1, frame_end=frames)
output.render(args)
