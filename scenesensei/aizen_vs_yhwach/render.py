"""Render the SceneSensei video: Kokoro narration + synth score + motion-graphics visuals.

Usage: python3 render.py <assets_dir> <out_dir>
assets_dir must contain k.onnx, voices.bin (kokoro-onnx v1.0), Anton.ttf, Mincho.ttf, Oswald.ttf
"""
import math, os, re, subprocess, sys
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import imageio_ffmpeg
from kokoro_onnx import Kokoro
from script import SEGMENTS

A, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
W, H, FPS, SR = 1920, 1080, 24, 24000
VOICE, SPEED = "am_michael", 0.98
THEMES = {  # bg inner, bg outer, accent, particle
    "aizen": ((58, 20, 92), (6, 2, 12), (190, 140, 255), (215, 180, 255)),
    "yhwach": ((70, 8, 12), (4, 2, 3), (255, 70, 60), (255, 120, 60)),
    "ichigo": ((12, 40, 80), (2, 4, 10), (120, 200, 255), (200, 235, 255)),
    "neutral": ((34, 34, 42), (4, 4, 6), (235, 235, 240), (200, 200, 210)),
}
font = lambda n, s: ImageFont.truetype(os.path.join(A, n), s)
F_HEAD, F_CAP, F_KANJI, F_BRAND = font("Anton.ttf", 118), font("Oswald.ttf", 50), font("Mincho.ttf", 560), font("Oswald.ttf", 30)

# ---------- narration ----------
kok = Kokoro(os.path.join(A, "k.onnx"), os.path.join(A, "voices.bin"))
audio, captions, seg_bounds, t = [], [], [], 0.0
def silence(s): return np.zeros(int(s * SR), dtype=np.float32)
for i, (_, _, _, text) in enumerate(SEGMENTS):
    start = t
    lead = silence(0.9 if i else 0.4); audio.append(lead); t += len(lead) / SR
    for sent in re.split(r"(?<=[.?!])\s+", text.strip()):
        wav, _ = kok.create(sent, voice=VOICE, speed=SPEED, lang="en-us")
        wav = wav.astype(np.float32); dur = len(wav) / SR
        words = sent.split(); n = math.ceil(len(words) / 7)  # balanced <=7-word chunks
        chunks = [" ".join(c) for c in np.array_split(np.array(words, dtype=object), n)]
        total = sum(len(c) for c in chunks); ct = t
        for c in chunks:
            d = dur * len(c) / total; captions.append((ct, ct + d, c)); ct += d
        audio.append(wav); t += dur
        gap = silence(0.28); audio.append(gap); t += len(gap) / SR
    seg_bounds.append((start, t))
tail = silence(1.5); audio.append(tail); t += 1.5
seg_bounds[-1] = (seg_bounds[-1][0], t)
voice = np.concatenate(audio); N = len(voice)

# ---------- score: dark drone + impact at each segment ----------
tt = np.arange(N) / SR
roots = {"aizen": 55.0, "yhwach": 49.0, "ichigo": 61.7, "neutral": 55.0}
music = np.zeros(N, dtype=np.float32)
rng = np.random.default_rng(7)
for (s, e), seg in zip(seg_bounds, SEGMENTS):
    a, b = int(s * SR), min(int(e * SR), N); x = tt[a:b] - s; f = roots[seg[2]]
    env = np.minimum(1, x / 1.5) * np.minimum(1, (e - s - x) / 1.0)
    pad = sum(np.sin(2 * np.pi * f * m * x + m) * g for m, g in ((1, .5), (1.5, .25), (2, .2), (3, .06)))
    pad *= 0.6 + 0.4 * np.sin(2 * np.pi * 0.08 * x)
    music[a:b] += (pad * env * 0.22).astype(np.float32)
    hl = min(int(2.2 * SR), b - a); hx = np.arange(hl) / SR  # boom
    boom = np.sin(2 * np.pi * (38 + 60 * np.exp(-hx * 8)) * hx) * np.exp(-hx * 2.2)
    boom += rng.standard_normal(hl) * np.exp(-hx * 14) * 0.25
    music[a:a + hl] += (boom * 0.55).astype(np.float32)
mix = voice * 0.95 + music * 0.35
mix /= max(1e-6, np.abs(mix).max()) / 0.95
sf.write(os.path.join(OUT, "audio.wav"), mix, SR)
DUR = N / SR

def ts(x): return f"{int(x//3600):02}:{int(x%3600//60):02}:{int(x%60):02},{int(x*1000%1000):03}"
with open(os.path.join(OUT, "captions.srt"), "w") as fh:
    for k, (s, e, c) in enumerate(captions, 1): fh.write(f"{k}\n{ts(s)} --> {ts(e)}\n{c}\n\n")
with open(os.path.join(OUT, "chapters.txt"), "w") as fh:
    for (s, _), seg in zip(seg_bounds, SEGMENTS):
        fh.write(f"{int(s//60)}:{int(s%60):02} {seg[0].replace(chr(10), ' ').title()}\n")

# ---------- visuals ----------
BW, BH = int(W * 1.12), int(H * 1.12)
def make_bg(theme, kanji):
    inner, outer, accent, _ = THEMES[theme]
    yy, xx = np.mgrid[0:BH, 0:BW].astype(np.float32)
    d = np.sqrt(((xx - BW * .62) / BW) ** 2 + ((yy - BH * .45) / BH) ** 2) / .75
    d = np.clip(d, 0, 1)[..., None]
    img = np.array(inner) * (1 - d) + np.array(outer) * d
    img += rng.normal(0, 4, img.shape[:2])[..., None]  # film grain
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    if kanji:
        layer = Image.new("L", (BW, BH), 0); dr = ImageDraw.Draw(layer)
        size = 560 if len(kanji) <= 2 else 330
        fk = F_KANJI if size == 560 else font("Mincho.ttf", size)
        if len(kanji) <= 2:
            dr.text((BW * .68, BH * .56), kanji, font=fk, fill=70, anchor="mm")
        else:  # vertical stack for 4-char terms
            for j, ch in enumerate(kanji):
                dr.text((BW * (.72 if j < 2 else .56), BH * (.3 + .38 * (j % 2))), ch, font=fk, fill=60, anchor="mm")
        glow = layer.filter(ImageFilter.GaussianBlur(18))
        col = Image.new("RGB", (BW, BH), accent)
        im = Image.composite(col, im, Image.eval(glow, lambda v: v // 2))
        im = Image.composite(col, im, Image.eval(layer, lambda v: v // 2))
    # slash lines
    dr = ImageDraw.Draw(im)
    for _ in range(3):
        y0 = rng.uniform(0, BH); dr.line([(0, y0), (BW, y0 - rng.uniform(200, 500))], fill=tuple(int(c * .35) for c in accent), width=2)
    return im

def headline_layer(text, accent):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(lay)
    lines = text.split("\n"); y = H * .30 - (len(lines) - 1) * 62
    for ln in lines:
        dr.text((128, y + 6), ln, font=F_HEAD, fill=(0, 0, 0, 200), anchor="lm")
        dr.text((122, y), ln, font=F_HEAD, fill=(255, 255, 255, 255), anchor="lm"); y += 128
    dr.rectangle([122, y - 40, 122 + 180, y - 30], fill=accent + (255,))
    return lay

def caption_img(text):
    lay = Image.new("RGBA", (W, 160), (0, 0, 0, 0)); dr = ImageDraw.Draw(lay)
    dr.text((W / 2, 80), text.upper(), font=F_CAP, fill=(255, 255, 255, 255), anchor="mm", stroke_width=5, stroke_fill=(0, 0, 0, 255))
    return lay

cap_cache = {}
ff = subprocess.Popen([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
    "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", os.path.join(OUT, "audio.wav"),
    "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
    "-shortest", "-movflags", "+faststart", os.path.join(OUT, "SceneSensei_Aizen_vs_Yhwach.mp4")], stdin=subprocess.PIPE)
vign = None
for (s, e), (head, kanji, theme, _) in zip(seg_bounds, SEGMENTS):
    bg = make_bg(theme, kanji); accent, pcol = THEMES[theme][2], THEMES[theme][3]
    head_l = headline_layer(head, accent)
    P = 70; px, py = rng.uniform(0, W, P), rng.uniform(0, H, P)
    pv, ps = rng.uniform(.4, 1.6, P), rng.uniform(2, 6, P)
    f0, f1 = int(s * FPS), int(e * FPS)
    for f in range(f0, f1):
        lt, T = f / FPS - s, max(.1, e - s)
        z = 1.0 + .10 * (lt / T)  # slow push-in
        cw, ch = int(BW / z / 1.12 * 1.0), int(BH / z / 1.12)
        ox, oy = (BW - cw) // 2 + int(20 * math.sin(lt * .2)), (BH - ch) // 2
        fr = bg.crop((ox, oy, ox + cw, oy + ch)).resize((W, H), Image.BILINEAR).convert("RGBA")
        dr = ImageDraw.Draw(fr)
        yy = (py - lt * 30 * pv) % H; xx = (px + 12 * np.sin(lt * pv + px)) % W
        for x_, y_, r_, v_ in zip(xx, yy, ps, pv):
            a = int(90 + 80 * math.sin(lt * v_ * 2 + x_))
            dr.ellipse([x_ - r_, y_ - r_, x_ + r_, y_ + r_], fill=pcol + (a,))
        # headline: slide+fade in, hold 5.5s, fade out
        ha = min(1, lt / .6) * min(1, max(0, (6.5 - lt) / .8)) if lt < 6.5 else 0
        if ha > 0:
            h2 = head_l if ha >= 1 else Image.eval(head_l, lambda v: v)  # alpha scaled below
            if ha < 1:
                r, g, b, al = h2.split(); al = al.point(lambda v: int(v * ha)); h2 = Image.merge("RGBA", (r, g, b, al))
            fr.alpha_composite(h2, (int(-60 * (1 - min(1, lt / .6))), 0))
        # caption
        now = f / FPS
        cap = next((c for c in captions if c[0] <= now < c[1]), None)
        if cap:
            if cap[2] not in cap_cache: cap_cache = {cap[2]: caption_img(cap[2])}
            fr.alpha_composite(cap_cache[cap[2]], (0, H - 230))
        ImageDraw.Draw(fr).text((W - 50, 50), "SCENESENSEI", font=F_BRAND, fill=(255, 255, 255, 150), anchor="rt")
        out = fr.convert("RGB")
        if lt < .16:  # impact flash
            out = Image.blend(out, Image.new("RGB", (W, H), accent), .6 * (1 - lt / .16))
        ff.stdin.write(out.tobytes())
ff.stdin.close(); ff.wait()
print("done", round(DUR, 1), "s")
