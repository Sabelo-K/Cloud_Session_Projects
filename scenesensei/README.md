# SceneSensei: free 3D video pipeline

Make cinematic 3D video for the channel with **Blender** (free, no watermark, you own what you render),
driven by short Python scene scripts. A scene is a text file you can version in Git, tweak, and re-render;
the same lighting rig, camera and render settings are reused for every video.

```
python -m scenesensei.render logo_reveal --preset draft
```

That builds the demo scene (a gold 3D title on a glossy dark studio floor, a light sweeping across it,
a slow camera drift) and writes `scenesensei/renders/logo_reveal/draft/logo_reveal_draft.mp4`.

## One-time setup

1. **Install Blender** from <https://www.blender.org/download/> (free). 4.2 LTS or newer.
2. **Tell the launcher where it is**, only if it isn't found automatically. It looks at `--blender PATH`, the
   `BLENDER` environment variable, your `PATH`, then the standard install folders (Windows, macOS, Linux). In
   PowerShell:
   ```
   $env:BLENDER = "C:\Program Files\Blender Foundation\Blender 4.5\blender.exe"
   ```
3. **Optional: ffmpeg**, only for the `final` presets (it joins the PNG frames into an MP4). Install it from
   <https://ffmpeg.org/download.html> (on Windows: `winget install Gyan.FFmpeg`). Without it you still get
   the frames, which DaVinci Resolve (free) can import as an image sequence.

No Python packages are needed: the launcher uses only the standard library.

## Day-to-day workflow

| Goal | Command |
|---|---|
| Fast look at layout, timing, camera | `python -m scenesensei.render logo_reveal --preset draft` |
| Check one frame's lighting and materials | `python -m scenesensei.render logo_reveal --preset preview --frame 70` |
| Tweak the scene by hand in Blender | `python -m scenesensei.render logo_reveal --blend-only`, then open the `.blend` it prints |
| Upload-quality render | `python -m scenesensei.render logo_reveal --preset final` |
| Continue an interrupted `final` | same command plus `--resume` (only if the scene hasn't changed) |
| Half-size, for a quick test of any preset | add `--scale 50` |

Stills land in `renders/<scene>/<preset>/stills/`. Judge lighting on a single `--frame` first, because a still
takes seconds and a full render takes much longer.

### Presets (`presets.py`)

| Preset | Size | Samples | Output | Use it for |
|---|---|---|---|---|
| `draft` | 854x480 | 12 | MP4 | layout, timing, camera moves |
| `preview` (default) | 1280x720 | 48 | MP4 | lighting and materials |
| `final` | 1920x1080 | 192 | PNG frames, then MP4 | uploading |
| `final4k` | 3840x2160 | 256 | PNG frames, then MP4 | 4K (about 4x the time of `final`) |

All presets use Blender's Cycles renderer with adaptive sampling and AI denoising, so a low sample count
still looks clean. `final` adds motion blur. Render time depends on your hardware, mostly on whether you have a
supported GPU: the pipeline picks one automatically (OptiX, CUDA, HIP, oneAPI or Metal) and falls back to the
CPU, printing which it chose at the top of the render.

## Make your own scene

Copy `scenes/_template.py` to `scenes/my_video.py`, edit it, and run
`python -m scenesensei.render my_video --preset draft`. A scene has four steps: build the set, light it, place
the camera, then `output.configure(...)` and `output.render(...)`. The helpers (`scenesensei/studio/`):

| Module | What it gives you |
|---|---|
| `stage` | `reset_scene`, `cyclorama` (seamless curved studio backdrop), `sphere`, `text` (extruded 3D text), `empty` |
| `materials` | `gold`, `chrome`, `metal`, `glass`, `glossy`, `emissive`, `principled` (everything), `textured` (a Poly Haven texture folder). Colours are `"#RRGGBB"`. |
| `lighting` | `three_point` (key, fill, rim), `area_light`, `hdri` (realistic reflections), `ambient`, `aim` |
| `camera` | `create` (lens, f-stop, depth of field), `orbit`, `dolly`, `animate` (any path), all eased in and out |
| `output` | `configure` (applies the preset), `render`, `save_blend` |

To import a model (a `.glb`/`.fbx` from Sketchfab or your own), use `bpy.ops.import_scene.gltf(filepath=...)`
inside the scene after `stage.reset_scene()`, then give it materials and aim the camera at it.

## What makes it look premium (and costs nothing)

- **Light first.** A soft key, a dim fill and a rim light (`three_point`) beat any expensive model. Use an
  HDRI (below) so metal and glass have something real to reflect.
- **Shallow depth of field.** A 50-85 mm lens at f/2.8-4 (`camera.create`) is the "filmed, not CG" look.
- **Slow, eased moves.** `camera.orbit` and `camera.dolly` start and stop gently. Fast, linear moves look cheap.
- **Real materials.** Slight roughness (0.15-0.3) and a glossy floor for reflections; flat colours look like clip art.
- **Finish in an editor.** Grain, vignette, colour grade, music and sound design in DaVinci Resolve (free).

## Free assets

- **HDRIs** (lighting and reflections): `python -m scenesensei.fetch_hdri <id>` downloads from
  [Poly Haven](https://polyhaven.com/hdris) (CC0: free for commercial use, no credit needed) into `assets/hdri/`.
  The ID is the end of the asset's page address. `logo_reveal` uses the first HDRI found there; without one it
  falls back to a dark studio.
- **Textures:** polyhaven.com/textures, unzipped into `assets/textures/<name>/`, used with `materials.textured`.
- **Fonts for 3D text:** [Google Fonts](https://fonts.google.com) (open licences). Set `FONT` in the scene.
- **Models:** polyhaven.com/models (CC0); Sketchfab downloads need their licence checked per model.

`renders/`, HDRIs and textures are git-ignored because they are large.

## What has and hasn't been verified

Built and tested in a Linux sandbox with no GPU and no Blender executable, using the `bpy` Python module.

- **Verified there, on both Blender 4.2 LTS and Blender 5.2:** every scene renders (stills, MP4 and PNG-frame
  presets, `--blend-only`, `--resume`), the ffmpeg stitching (frame count, size and H.264 output checked), the
  colour management, the camera and lighting maths, and the launcher's command construction. See
  `tests/test_scenesensei_*.py`. The demo's look was checked by eye on rendered frames.
- **Not verified:** the real `blender` executable on Windows (the sandbox used a stand-in that runs the same
  script), GPU auto-detection (no GPU here; the CPU fallback is what ran), and `fetch_hdri` against the live
  Poly Haven API (the sandbox cannot reach it; the logic is tested against a mocked response). If any of these
  misbehave on your machine, the error text will tell you what failed; send it over.

## Tests

```
pytest tests/test_scenesensei_core.py        # plain Python; also runs in CI
pip install bpy && pytest tests/test_scenesensei_blender.py   # real Blender renders, ~5 seconds
```

The Blender tests skip themselves when `bpy` is not installed (it is a ~400 MB package). Use the Python
version the wheel supports (`pip` will say if it doesn't).
