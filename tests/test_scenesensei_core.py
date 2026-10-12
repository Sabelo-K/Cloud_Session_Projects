"""SceneSensei's plain-Python side: presets, args, the render launcher, the HDRI downloader.

None of this needs Blender (the Blender side is covered by test_scenesensei_blender.py).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

import wave

from scenesensei import audio, fetch_hdri, render
from scenesensei.color import parse_color, srgb_to_linear
from scenesensei.presets import PRESETS, get_preset, scaled_size
from scenesensei.scene_args import RENDERS_DIR, parse_scene_args


# ---- presets / colour -----------------------------------------------------------------------

def test_every_preset_is_encodable():
    for preset in PRESETS.values():
        assert preset.width % 2 == 0 and preset.height % 2 == 0, preset.name
        assert preset.output in ("mp4", "frames")


def test_unknown_preset_lists_choices():
    with pytest.raises(ValueError, match="draft.*preview.*final"):
        get_preset("ultra")


@pytest.mark.parametrize("scale, expected", [(100, (854, 480)), (50, (428, 240)), (10, (86, 48)), (1, (8, 4))])
def test_scaled_size_is_always_even(scale, expected):
    size = scaled_size(get_preset("draft"), scale)
    assert size == expected
    assert size[0] % 2 == 0 and size[1] % 2 == 0


def test_parse_color():
    assert parse_color("#ffffff") == pytest.approx((1, 1, 1))
    assert parse_color("000000") == (0, 0, 0)
    assert parse_color("#808080")[0] == pytest.approx(0.2158, abs=1e-3)   # sRGB mid-grey is ~22% linear
    assert parse_color((0.1, 0.2, 0.3)) == (0.1, 0.2, 0.3)                # tuples are already linear
    assert srgb_to_linear(0.02) == pytest.approx(0.02 / 12.92)


@pytest.mark.parametrize("bad", ["#fff", "#gggggg", "", "12345"])
def test_parse_color_rejects_bad_hex(bad):
    with pytest.raises(ValueError):
        parse_color(bad)


# ---- scene args -------------------------------------------------------------------------------

def test_scene_args_defaults_when_run_by_hand():
    args = parse_scene_args("demo", ["blender", "--background"])           # no `--`: Blender GUI case
    assert args.preset.name == "preview"
    assert args.out_dir == RENDERS_DIR / "demo" / "preview"
    assert (args.frame, args.scale, args.samples) == (None, 100, args.preset.samples)
    assert not (args.blend_only or args.save_blend or args.resume)


def test_scene_args_after_double_dash():
    argv = ["blender", "-b", "--python", "x.py", "--", "--preset", "final", "--frame", "40", "--samples", "9",
            "--scale", "50", "--out", "somewhere", "--resume", "--blend-only"]
    args = parse_scene_args("demo", argv)
    assert args.preset.name == "final"
    assert (args.frame, args.samples, args.scale) == (40, 9, 50)
    assert args.out_dir == Path("somewhere")
    assert args.resume and args.blend_only


def test_scene_args_reject_silly_scale():
    with pytest.raises(SystemExit):
        parse_scene_args("demo", ["--", "--scale", "0"])


# ---- render launcher ------------------------------------------------------------------------

def test_find_blender_precedence(tmp_path, monkeypatch):
    exe = tmp_path / "blender"
    exe.write_text("")
    other = tmp_path / "other"
    other.write_text("")
    monkeypatch.setenv("BLENDER", str(other))
    assert render.find_blender(str(exe)) == str(exe)          # --blender beats the environment
    assert render.find_blender() == str(other)                # environment beats PATH
    monkeypatch.delenv("BLENDER")
    monkeypatch.setattr(render.shutil, "which", lambda name: "/usr/bin/blender")
    assert render.find_blender() == "/usr/bin/blender"


def test_find_blender_explains_how_to_install(monkeypatch):
    monkeypatch.delenv("BLENDER", raising=False)
    monkeypatch.setattr(render.shutil, "which", lambda name: None)
    monkeypatch.setattr(render, "_BLENDER_GLOBS", ())
    with pytest.raises(render.RenderError, match="blender.org"):
        render.find_blender()
    with pytest.raises(render.RenderError, match="not found at"):
        render.find_blender("/nope/blender")


def test_resolve_scene_by_name_and_hides_template():
    assert render.resolve_scene("logo_reveal").name == "logo_reveal.py"
    assert render.resolve_scene("logo_reveal.py").name == "logo_reveal.py"
    with pytest.raises(render.RenderError) as exc:
        render.resolve_scene("nope")
    assert "logo_reveal" in str(exc.value) and "_template" not in str(exc.value)
    assert render.resolve_scene("_template").name == "_template.py"   # still runnable by name


def test_build_command():
    args = render.parse_args(["logo_reveal", "--preset", "final", "--frame", "7", "--samples", "5",
                              "--scale", "50", "--resume", "--save-blend"])
    cmd = render.build_command("/b/blender", Path("/s/scene.py"), Path("/o"), args)
    sep = cmd.index("--")
    assert cmd[:sep] == ["/b/blender", "--background", "--factory-startup", "--python-exit-code", "1",
                         "--python", str(Path("/s/scene.py"))]
    assert cmd[sep + 1:] == ["--preset", "final", "--out", str(Path("/o")), "--scale", "50",
                             "--frame", "7", "--samples", "5", "--save-blend", "--resume"]


def test_ffmpeg_command_matches_blender_output_names():
    info = {"name": "demo", "preset": "final", "fps": 24, "frame_start": 3, "frame_end": 12}
    cmd = render.build_ffmpeg_command("ffmpeg", Path("/o"), info)
    assert cmd[cmd.index("-start_number") + 1] == "3"
    assert cmd[cmd.index("-frames:v") + 1] == "10"
    assert cmd[cmd.index("-i") + 1] == str(Path("/o/frames/frame_%04d.png"))
    assert cmd[-1] == str(Path("/o/demo_final.mp4"))
    assert "yuv420p" in cmd


@pytest.fixture
def fake_run(tmp_path, monkeypatch):
    """Replace Blender and ffmpeg with recorders; 'Blender' writes the info file the real one would."""
    calls: list[list[str]] = []
    exe = tmp_path / "blender"
    exe.write_text("")

    def call(cmd):
        calls.append(cmd)
        if cmd[0] == str(exe):
            out = Path(cmd[cmd.index("--out") + 1])
            out.mkdir(parents=True, exist_ok=True)
            (out / render.INFO_FILE).write_text(json.dumps(
                {"name": "logo_reveal", "preset": "final", "fps": 24, "frame_start": 1, "frame_end": 4}))
        return 0

    monkeypatch.setattr(render.subprocess, "call", call)
    return calls, exe, tmp_path / "out"


def test_final_preset_stitches_with_ffmpeg(fake_run, monkeypatch):
    calls, exe, out = fake_run
    monkeypatch.setattr(render.shutil, "which", lambda name: "/usr/bin/ffmpeg")
    assert render.main(["logo_reveal", "--preset", "final", "--blender", str(exe), "--out", str(out)]) == 0
    assert [Path(c[0]).name for c in calls] == ["blender", "ffmpeg"]


def test_missing_ffmpeg_is_explained_not_fatal(fake_run, monkeypatch, capsys):
    calls, exe, out = fake_run
    monkeypatch.setattr(render.shutil, "which", lambda name: None)
    assert render.main(["logo_reveal", "--preset", "final", "--blender", str(exe), "--out", str(out)]) == 0
    assert len(calls) == 1
    assert "ffmpeg is not installed" in capsys.readouterr().out


def test_mp4_preset_and_stills_never_call_ffmpeg(fake_run):
    calls, exe, out = fake_run
    assert render.main(["logo_reveal", "--preset", "draft", "--blender", str(exe), "--out", str(out)]) == 0
    assert render.main(["logo_reveal", "--preset", "final", "--frame", "3", "--blender", str(exe),
                        "--out", str(out)]) == 0
    assert all(Path(c[0]).name == "blender" for c in calls)


def test_blender_failure_is_a_clean_error(fake_run, monkeypatch, capsys):
    calls, exe, out = fake_run
    monkeypatch.setattr(render.subprocess, "call", lambda cmd: 1)
    assert render.main(["logo_reveal", "--blender", str(exe), "--out", str(out)]) == 1
    assert "Blender exited with code 1" in capsys.readouterr().err


def test_main_reports_missing_blender_without_traceback(monkeypatch, capsys):
    monkeypatch.delenv("BLENDER", raising=False)
    monkeypatch.setattr(render.shutil, "which", lambda name: None)
    monkeypatch.setattr(render, "_BLENDER_GLOBS", ())
    assert render.main(["logo_reveal"]) == 1
    assert capsys.readouterr().err.startswith("error: Blender not found")


# ---- HDRI downloader (network mocked) ---------------------------------------------------------

FILES = {"hdri": {"1k": {"hdr": {"url": "https://x/a_1k.hdr", "md5": "m1"}},
                  "2k": {"exr": {"url": "https://x/a_2k.exr", "md5": "m2"},
                         "hdr": {"url": "https://x/a_2k.hdr", "md5": "m3"}}}}


def test_pick_file_prefers_hdr_and_explains_gaps():
    res, entry, ext = fetch_hdri.pick_file(FILES, "2k")
    assert (res, ext, entry["url"]) == ("2k", "hdr", "https://x/a_2k.hdr")
    with pytest.raises(fetch_hdri.FetchError, match="available: 1k, 2k"):
        fetch_hdri.pick_file(FILES, "8k")
    with pytest.raises(fetch_hdri.FetchError, match="no HDRI"):
        fetch_hdri.pick_file({"blend": {}}, "2k")


def test_fetch_saves_and_verifies_checksum(tmp_path, monkeypatch):
    payload = b"fake-hdr-bytes"
    files = {"hdri": {"2k": {"hdr": {"url": "https://x/a.hdr", "md5": hashlib.md5(payload).hexdigest()}}}}
    monkeypatch.setattr(fetch_hdri, "_get_json", lambda url: files)

    def download(url, dest):
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(payload)
        return payload

    monkeypatch.setattr(fetch_hdri, "_download", download)
    path = fetch_hdri.fetch("studio_x", "2k", tmp_path)
    assert path == tmp_path / "studio_x_2k.hdr" and path.read_bytes() == payload


def test_fetch_deletes_corrupt_download(tmp_path, monkeypatch):
    files = {"hdri": {"2k": {"hdr": {"url": "https://x/a.hdr", "md5": "0" * 32}}}}
    monkeypatch.setattr(fetch_hdri, "_get_json", lambda url: files)
    monkeypatch.setattr(fetch_hdri, "_download",
                        lambda url, dest: (dest.write_bytes(b"junk"), b"junk")[1])
    with pytest.raises(fetch_hdri.FetchError, match="corrupt"):
        fetch_hdri.fetch("studio_x", "2k", tmp_path)
    assert not list(tmp_path.glob("*"))


def test_fetch_cli_reports_errors(monkeypatch, capsys):
    def boom(url):
        raise fetch_hdri.FetchError("no such asset; check the ID on polyhaven.com")
    monkeypatch.setattr(fetch_hdri, "_get_json", boom)
    assert fetch_hdri.main(["nonsense"]) == 1
    assert "no such asset" in capsys.readouterr().err


# ---- sound effects ----------------------------------------------------------------------------

def test_sound_validates_its_arguments():
    with pytest.raises(ValueError, match="unknown sound"):
        audio.Sound("kazoo", 0, 1)
    with pytest.raises(ValueError):
        audio.Sound("boom", -1, 1)
    with pytest.raises(ValueError):
        audio.Sound("boom", 0, 0)


def test_every_sound_kind_synthesises_and_the_mix_is_normalised():
    rate = 4000                                                   # tiny sample rate: fast test
    sounds = [audio.Sound(kind, 0.1 * i, 0.5, 1.0, pan=-1 + 0.4 * i) for i, kind in enumerate(audio.KINDS)]
    left, right = audio.mix(sounds, seconds=2, rate=rate, seed=1)
    assert len(left) == len(right) == 2 * rate
    peak = max(abs(v) for v in left + right)
    assert peak == pytest.approx(0.9)
    assert any(abs(v) > 0.05 for v in left) and any(abs(v) > 0.05 for v in right)


def test_pan_places_a_sound_in_one_ear():
    left, right = audio.mix([audio.Sound("hit", 0, 0.3, 1, pan=-1)], seconds=0.5, rate=4000)
    assert max(abs(v) for v in right) < 1e-6 < max(abs(v) for v in left)


def test_mix_clips_sounds_that_run_past_the_end():
    left, _ = audio.mix([audio.Sound("boom", 0.9, 2.0)], seconds=1.0, rate=4000)
    assert len(left) == 4000


def test_write_wav_roundtrip(tmp_path):
    channels = audio.mix([audio.Sound("hit", 0, 0.2)], seconds=0.5, rate=8000)
    path = audio.write_wav(tmp_path / "sub" / "x.wav", channels, rate=8000)
    with wave.open(str(path)) as f:
        assert (f.getnchannels(), f.getsampwidth(), f.getframerate(), f.getnframes()) == (2, 2, 8000, 4000)


def test_mux_command_copies_the_picture_and_encodes_aac():
    cmd = render.build_mux_command("ffmpeg", Path("/o/v.mp4"), "/o/sfx.wav", Path("/o/v_with_audio.mp4"))
    assert cmd[cmd.index("-c:v") + 1] == "copy" and cmd[cmd.index("-c:a") + 1] == "aac"
    assert "-shortest" in cmd and cmd[-1] == str(Path("/o/v_with_audio.mp4"))


@pytest.fixture
def run_with_audio(tmp_path, monkeypatch):
    """Like fake_run, but the scene recorded a sound track and Blender 'wrote' the MP4."""
    calls: list[list[str]] = []
    exe = tmp_path / "blender"
    exe.write_text("")

    def call(cmd):
        calls.append(cmd)
        if cmd[0] == str(exe):
            out = Path(cmd[cmd.index("--out") + 1])
            out.mkdir(parents=True, exist_ok=True)
            (out / "logo_reveal_draft.mp4").write_bytes(b"video")
            (out / render.INFO_FILE).write_text(json.dumps(
                {"name": "logo_reveal", "preset": "draft", "fps": 24, "frame_start": 1, "frame_end": 4,
                 "audio": str(out / "sfx.wav")}))
        return 0

    monkeypatch.setattr(render.subprocess, "call", call)
    return calls, exe, tmp_path / "out"


def test_sound_is_added_to_the_finished_video(run_with_audio, monkeypatch, capsys):
    calls, exe, out = run_with_audio
    monkeypatch.setattr(render.shutil, "which", lambda name: "/usr/bin/ffmpeg")
    assert render.main(["logo_reveal", "--preset", "draft", "--blender", str(exe), "--out", str(out)]) == 0
    assert [Path(c[0]).name for c in calls] == ["blender", "ffmpeg"]
    assert calls[1][-1].endswith("logo_reveal_draft_with_audio.mp4")
    assert "With sound" in capsys.readouterr().out


def test_missing_ffmpeg_leaves_a_silent_video_and_says_so(run_with_audio, monkeypatch, capsys):
    calls, exe, out = run_with_audio
    monkeypatch.setattr(render.shutil, "which", lambda name: None)
    assert render.main(["logo_reveal", "--preset", "draft", "--blender", str(exe), "--out", str(out)]) == 0
    assert len(calls) == 1 and "video is silent" in capsys.readouterr().out
