"""Visuals for the Aizen phonk-edit Short (1080x1920, 30fps). Every frame is drawn procedurally.

Usage: [WORKERS=n] [STILLS=0.5] python3 video.py <assets_dir> <out_dir>   (reads out_dir/timeline.json + audio.wav)
"""
import json, math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops
import imageio_ffmpeg

A, OUT = sys.argv[1], sys.argv[2]
TL = json.load(open(os.path.join(OUT, "timeline.json")))
W, H, FPS = 1080, 1920, 30
BEAT = 60 / TL["bpm"]; TOTAL, DROP, VEND = TL["total"], TL["drop"], TL["voice_end"]
LINES = TL["lines"]
rng = np.random.default_rng(5)
F = lambda n, s: ImageFont.truetype(os.path.join(A, n), s)
PURPLE, RED, GOLD, YEL = (170, 90, 255), (255, 40, 40), (255, 200, 80), (255, 214, 0)

# ---------------- helpers ----------------
import functools
@functools.lru_cache(maxsize=32)
def radial_bg(inner, outer, cx=.5, cy=.42, r=.8):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.clip(np.sqrt(((xx - W * cx) / W) ** 2 + ((yy - H * cy) / W) ** 2) / r, 0, 1)[..., None]
    return Image.fromarray((np.array(inner) * (1 - d) + np.array(outer) * d).astype(np.uint8))
def glow_add(base, layer, radius, strength=1.0):
    g = layer.filter(ImageFilter.GaussianBlur(radius))
    if strength != 1.0: g = Image.eval(g, lambda v: min(255, int(v * strength)))
    return ImageChops.add(base, g.convert("RGB"))
def over(base, rgba, xy=(0, 0)):
    b = base.convert("RGBA"); b.alpha_composite(rgba, xy); return b.convert("RGB")
def ease(x): x = min(1, max(0, x)); return 1 - (1 - x) ** 3
def scaled(img, s, center=None):
    """zoom an image by s around center (fx, fy fractions)"""
    cx, cy = center or (.5, .5); w, h = img.size
    cw, ch = w / s, h / s; x0, y0 = cx * w - cw / 2, cy * h - ch / 2
    x0 = min(max(0, x0), w - cw); y0 = min(max(0, y0), h - ch)
    return img.resize((w, h), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))

VIGN = None
def vignette():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W / 2) / (W * .75)) ** 2 + ((yy - H / 2) / (H * .62)) ** 2)
    return np.clip(1.15 - d * .75, .25, 1)[..., None]
VIGN = vignette()
GRAIN = [rng.integers(-12, 13, (H // 2, W // 2, 1)).astype(np.int16).repeat(2, 0).repeat(2, 1) for _ in range(4)]

def speed_lines(seed, col=(255, 255, 255), alpha=150, inner=420):
    r = np.random.default_rng(seed); lay = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(lay)
    cx, cy = W / 2, H * .42
    for _ in range(170):
        a = r.uniform(0, 2 * math.pi); w_ = r.uniform(.004, .014); r0 = inner + r.uniform(0, 260)
        p = [(cx + math.cos(a) * r0, cy + math.sin(a) * r0),
             (cx + math.cos(a - w_) * 2400, cy + math.sin(a - w_) * 2400),
             (cx + math.cos(a + w_) * 2400, cy + math.sin(a + w_) * 2400)]
        d.polygon(p, fill=col + (int(alpha * r.uniform(.4, 1)),))
    return lay
SPEED = [speed_lines(s) for s in range(4)]
SPEED_P = [speed_lines(10 + s, (200, 150, 255), 170) for s in range(4)]
SPEED_R = [speed_lines(20 + s, (255, 90, 70), 150) for s in range(4)]

# ---------------- assets ----------------
def make_eye(iris=((120, 0, 0), (255, 50, 30), (255, 150, 60)), hypno=False):
    ew, eh = 1000, 600; cx, cy = ew / 2, eh / 2
    def almond(open_=1.0):
        xs = np.linspace(-1, 1, 90)
        top = [(cx + x * 480, cy - 250 * open_ * (1 - x * x) ** .85 * (1 + .15 * x)) for x in xs]
        bot = [(cx + x * 480, cy + 200 * open_ * (1 - x * x) ** .9) for x in xs[::-1]]
        return top + bot
    im = Image.new("RGBA", (ew, eh)); d = ImageDraw.Draw(im)
    d.polygon(almond(), fill=(232, 222, 215, 255))
    r = np.random.default_rng(3)
    for _ in range(26):  # veins
        x, y = (cx - 470, cy + r.uniform(-60, 60)) if r.random() < .5 else (cx + 470, cy + r.uniform(-60, 60))
        pts = [(x, y)]
        for _ in range(7): x += (1 if x < cx else -1) * r.uniform(15, 40); y += r.uniform(-18, 18); pts.append((x, y))
        d.line(pts, fill=(190, 40, 40, 170), width=int(r.integers(1, 4)))
    yy, xx = np.mgrid[0:eh, 0:ew].astype(np.float32)
    rr = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / 205
    c0, c1, c2 = [np.array(c, np.float32) for c in iris]
    ir = np.where(rr[..., None] < .55, c2 * (1 - rr[..., None] / .55) + c1 * (rr[..., None] / .55),
                  c1 * (1 - (rr[..., None] - .55) / .45) + c0 * ((rr[..., None] - .55) / .45))
    streak = (np.sin(np.arctan2(yy - cy, xx - cx) * 40) * 18)[..., None]  # iris fibres
    ir = np.clip(ir + streak, 0, 255)
    irisimg = Image.fromarray(ir.astype(np.uint8)).convert("RGBA")
    m = Image.new("L", (ew, eh)); ImageDraw.Draw(m).ellipse([cx - 205, cy - 205, cx + 205, cy + 205], fill=255)
    im.paste(irisimg, (0, 0), m)
    d = ImageDraw.Draw(im)
    if hypno:  # spiral pupil
        for k in range(260):
            a = k * .19; rad = 8 + k * .55
            d.ellipse([cx + math.cos(a) * rad - 6, cy + math.sin(a) * rad - 6, cx + math.cos(a) * rad + 6, cy + math.sin(a) * rad + 6], fill=(20, 0, 30, 255))
    else:  # The Almighty: many pupils
        d.ellipse([cx - 58, cy - 58, cx + 58, cy + 58], fill=(8, 0, 0, 255))
        for a in range(5):
            ang = a * 2 * math.pi / 5 - math.pi / 2; px, py = cx + math.cos(ang) * 128, cy + math.sin(ang) * 128
            d.ellipse([px - 24, py - 24, px + 24, py + 24], fill=(8, 0, 0, 255))
    d.ellipse([cx - 120, cy - 120, cx - 70, cy - 85], fill=(255, 255, 255, 220))
    mask = Image.new("L", (ew, eh)); ImageDraw.Draw(mask).polygon(almond(), fill=255)
    im.putalpha(ImageChops.multiply(im.getchannel("A"), mask))
    return im, almond
EYE, ALMOND = make_eye()
EYE_H, _ = make_eye(((40, 0, 70), (150, 60, 255), (230, 170, 255)), hypno=True)

def eye_frame(eye, open_=1.0, scale=1.0, glow_col=RED, bg=None, look=0.0):
    base = bg.copy() if bg else radial_bg((60, 0, 0), (0, 0, 0))
    e = eye
    if look: e = e.transform(e.size, Image.AFFINE, (1, 0, -look, 0, 1, 0))
    if open_ < 1:
        m = Image.new("L", e.size); ImageDraw.Draw(m).polygon(ALMOND(max(.001, open_)), fill=255)
        e = e.copy(); e.putalpha(ImageChops.multiply(e.getchannel("A"), m))
    ew, eh = int(e.width * scale), int(e.height * scale); e = e.resize((ew, eh), Image.BILINEAR)
    pos = ((W - ew) // 2, int(H * .42 - eh / 2))
    gl = Image.new("RGBA", (W, H)); gl.paste(Image.new("RGBA", (ew, eh), glow_col + (255,)), pos, e.getchannel("A"))
    base = glow_add(base, gl, 60, 1.2)
    base = over(base, Image.new("RGBA", (W, H)), (0, 0))
    b = base.convert("RGBA"); b.alpha_composite(e, pos)
    d = ImageDraw.Draw(b)  # heavy lid line
    lid = [(pos[0] + (x - 0) * scale, pos[1] + y * scale) for x, y in ALMOND(max(.001, open_))[:90]]
    d.line(lid, fill=(0, 0, 0, 255), width=int(16 * scale))
    return b.convert("RGB")

def _shade(mask, top, bottom, side=.45):
    """fill a mask with a top-lit, cylindrically shaded colour"""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    bb = mask.getbbox(); x0, y0, x1, y1 = bb
    v = np.clip((yy - y0) / max(1, y1 - y0), 0, 1)[..., None]
    col = np.array(top, np.float32) * (1 - v) + np.array(bottom, np.float32) * v
    cx = (x0 + x1) / 2; hx = np.clip(np.abs(xx - cx) / max(1, (x1 - x0) / 2), 0, 1)[..., None]
    col *= 1 - side * hx ** 2
    im = Image.fromarray(np.clip(col, 0, 255).astype(np.uint8)).convert("RGBA"); im.putalpha(mask); return im
def _rim(mask, col, shift=7):
    top = ImageChops.subtract(mask, ImageChops.offset(mask, 0, shift)).filter(ImageFilter.GaussianBlur(2))
    r = Image.new("RGBA", (W, H), col + (255,)); r.putalpha(top); return r

def make_chair():
    out = Image.new("RGBA", (W, H))
    # chair: gothic high back
    cm = Image.new("L", (W, H)); d = ImageDraw.Draw(cm)
    d.polygon([(290, 1500), (290, 660), (540, 360), (790, 660), (790, 1500)], fill=255)
    d.rectangle([255, 1075, 825, 1125], fill=255); d.rectangle([265, 1125, 305, 1640], fill=255); d.rectangle([775, 1125, 815, 1640], fill=255)
    d.rectangle([285, 1290, 795, 1370], fill=255); d.rectangle([300, 1370, 340, 1660], fill=255); d.rectangle([740, 1370, 780, 1660], fill=255)
    chair = _shade(cm, (34, 26, 44), (8, 6, 12)); edge = ImageChops.subtract(cm.filter(ImageFilter.MaxFilter(7)), cm)
    ec = Image.new("RGBA", (W, H), (120, 70, 190, 255)); ec.putalpha(edge)
    out.alpha_composite(ec); out.alpha_composite(chair); out.alpha_composite(_rim(cm, (150, 110, 220), 5))
    # body in white prison wrap
    bm = Image.new("L", (W, H)); d = ImageDraw.Draw(bm)
    d.rectangle([510, 850, 570, 930], fill=255)                                       # neck
    d.polygon([(385, 935), (695, 935), (668, 1300), (412, 1300)], fill=255)           # torso
    d.polygon([(385, 945), (330, 1080), (392, 1098), (440, 985)], fill=255)            # arms to armrests
    d.polygon([(695, 945), (750, 1080), (688, 1098), (640, 985)], fill=255)
    d.rounded_rectangle([318, 1070, 402, 1105], 12, fill=255); d.rounded_rectangle([678, 1070, 762, 1105], 12, fill=255)  # hands
    d.polygon([(420, 1290), (535, 1290), (530, 1620), (455, 1620)], fill=255)          # legs
    d.polygon([(545, 1290), (660, 1290), (625, 1620), (550, 1620)], fill=255)
    d.ellipse([440, 1600, 540, 1650], fill=255); d.ellipse([540, 1600, 640, 1650], fill=255)
    out.alpha_composite(_shade(bm, (236, 228, 240), (120, 110, 135)))
    folds = Image.new("RGBA", (W, H)); df = ImageDraw.Draw(folds)
    for x0_, x1_ in ((470, 440), (540, 540), (610, 640)): df.line([(x0_, 960), (x1_, 1290)], fill=(140, 130, 160, 140), width=4)
    df.line([(470, 935), (540, 1060), (610, 935)], fill=(130, 120, 150, 200), width=5)      # collar V
    out.alpha_composite(folds); out.alpha_composite(_rim(bm, (255, 245, 255)))
    # face
    fm = Image.new("L", (W, H)); ImageDraw.Draw(fm).ellipse([465, 665, 615, 870], fill=255)
    out.alpha_composite(_shade(fm, (232, 196, 170), (170, 130, 110), .6))
    dd = ImageDraw.Draw(out)
    dd.line([(525, 835), (540, 842), (556, 835)], fill=(120, 70, 70, 255), width=4)      # faint smirk
    dd.line([(556, 835), (562, 829)], fill=(120, 70, 70, 255), width=4)
    # hair: swept back, brown, with the single strand
    hm = Image.new("L", (W, H)); d = ImageDraw.Draw(hm)
    d.polygon([(458, 770), (452, 700), (472, 648), (515, 618), (570, 612), (615, 635), (640, 680), (648, 740), (660, 790),
               (628, 760), (612, 700), (575, 668), (520, 672), (482, 705), (470, 770)], fill=255)
    for sx, sy in ((500, 632), (548, 618), (596, 628), (632, 660)):
        d.polygon([(sx - 30, sy + 8), (sx + 38, sy - 30), (sx + 22, sy + 16)], fill=255)
    d.line([(520, 668), (500, 720), (487, 790), (478, 860)], fill=255, width=13)            # the strand
    out.alpha_composite(_shade(hm, (120, 72, 45), (50, 28, 18), .3)); out.alpha_composite(_rim(hm, (200, 150, 110), 5))
    # restraints + blindfold + seal tags
    straps = Image.new("RGBA", (W, H)); ds = ImageDraw.Draw(straps)
    for box in ([380, 1000, 700, 1028], [395, 1180, 685, 1208], [315, 1060, 405, 1082], [675, 1060, 765, 1082],
                [430, 1450, 650, 1478], [458, 745, 622, 776]):
        ds.rectangle(box, fill=(195, 160, 255, 255))
    for x in (440, 523, 606):
        ds.rectangle([x, 1028, x + 34, 1098], fill=(240, 232, 205, 255)); ds.line([(x + 17, 1038), (x + 17, 1088)], fill=(160, 0, 0, 255), width=4)
    return out, straps
CHAIR, STRAPS = make_chair()

@functools.lru_cache(maxsize=1)
def _chair_bg():
    bg = radial_bg((26, 12, 40), (0, 0, 0), cy=.55)
    cone = Image.new("RGBA", (W, H)); dc = ImageDraw.Draw(cone)
    dc.polygon([(470, 0), (610, 0), (900, 1650), (180, 1650)], fill=(200, 180, 255, 55))
    dc.ellipse([160, 1560, 920, 1700], fill=(170, 130, 255, 70))
    return over(bg, cone.filter(ImageFilter.GaussianBlur(30)))
@functools.lru_cache(maxsize=8)
def _strap_glow(g):
    return Image.eval(STRAPS, lambda v: int(v * g)).filter(ImageFilter.GaussianBlur(14))
def chair_frame(bright=1.0, tint=None, strap_glow=1.0, eyes=0.0, dust_t=0.0):
    bg = _chair_bg().copy()
    dd = ImageDraw.Draw(bg); r = np.random.default_rng(1)
    for _ in range(60):  # dust in the light
        x = r.uniform(250, 830); y = (r.uniform(0, 1600) + dust_t * r.uniform(10, 40)) % 1600
        a = int(r.uniform(60, 200) * bright); dd.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(a, a, a))
    bg = over(bg, CHAIR)
    s = STRAPS
    bg = ImageChops.add(bg, Image.eval(_strap_glow(round(strap_glow, 1)).convert("RGB"), lambda v: min(255, int(v * 1.3)))); bg = over(bg, s)
    if eyes > 0:  # eyes glowing through the blindfold
        e = Image.new("RGBA", (W, H)); de = ImageDraw.Draw(e)
        for x in (510, 572): de.ellipse([x - 18, 754, x + 18, 767], fill=(255, 240, 255, int(255 * eyes)))
        bg = glow_add(bg, e, 16, 2.0); bg = over(bg, e)
    if bright < 1: bg = Image.eval(bg, lambda v: int(v * bright))
    if tint: bg = Image.blend(bg, Image.new("RGB", (W, H), tint), .25)
    return bg

def petals(t, n=40, col=(255, 150, 200), seed=2, lay=None):
    lay = lay or Image.new("RGBA", (W, H)); d = ImageDraw.Draw(lay); r = np.random.default_rng(seed)
    for _ in range(n):
        x0, y0, v, ph = r.uniform(0, W), r.uniform(-H, H), r.uniform(120, 260), r.uniform(0, 6)
        y = (y0 + t * v) % (H + 100) - 50; x = x0 + math.sin(t * 1.5 + ph) * 60
        w_ = 14 + 8 * math.sin(t * 3 + ph)
        d.ellipse([x - w_, y - 7, x + w_, y + 7], fill=col + (220,))
    return lay

def chains_frame(lt, d, snap_at):
    bg = radial_bg((80, 0, 10), (5, 0, 0))
    lay = Image.new("RGBA", (W, H)); dl = ImageDraw.Draw(lay)
    for k, (y0, ang) in enumerate(((600, .35), (1000, -.3), (1400, .25))):
        slide = (1 - ease(lt / .35)) * 900 * (1 if k % 2 else -1)
        ca, sa = math.cos(ang), math.sin(ang)
        for j in range(-14, 15):
            off = 0
            if lt > snap_at:  # snap in the middle
                off = (1 if j > 0 else -1) * ease((lt - snap_at) / .4) * 240
            cx = W / 2 + (j * 78 + slide + off) * ca; cy = y0 + (j * 78 + off) * sa
            if j == 0 and lt > snap_at: continue
            if j % 2: dl.ellipse([cx - 50, cy - 30, cx + 50, cy + 30], outline=(195, 195, 210, 255), width=12)
            else: dl.line([(cx - 44 * ca, cy - 44 * sa), (cx + 44 * ca, cy + 44 * sa)], fill=(150, 150, 165, 255), width=16)
    bg = glow_add(bg, lay, 8, .6); bg = over(bg, lay)
    return over(bg, petals(lt, 45))

def coffin_frame(lt, d):
    bg = radial_bg((40, 0, 70), (2, 0, 6), cy=.45)
    lay = Image.new("RGBA", (W, H)); dl = ImageDraw.Draw(lay)
    x0, y0, x1, y1 = 300, 480, 780, 1330
    p = ease(lt / .5)
    # walls slam in from four sides
    dl.rectangle([x0 - (1 - p) * 600, y0, x0 + (x1 - x0) / 2 * p + 1 if p < 1 else x1, y1], fill=(0, 0, 0, 255))
    if p >= 1:
        for k in range(14):  # purple sigil lines on the surface
            yy = y0 + 40 + k * 58; dl.line([(x0 + 30, yy), (x1 - 30, yy + (20 if k % 2 else -20))], fill=(120, 60, 200, 255), width=3)
        dl.rectangle([x0, y0, x1, y1], outline=(180, 110, 255, 255), width=8)
    ns = 22; r = np.random.default_rng(9)
    for k in range(ns):  # spears pierce inward
        ts = .45 + k * (max(.2, d - .9) / ns)
        if lt < ts: continue
        q = ease((lt - ts) / .12); side = k % 4
        if side == 0: tip, base_ = (r.uniform(x0, x1), y0 + 40), (0, -1)
        elif side == 1: tip, base_ = (r.uniform(x0, x1), y1 - 40), (0, 1)
        elif side == 2: tip, base_ = (x0 + 40, r.uniform(y0, y1)), (-1, 0)
        else: tip, base_ = (x1 - 40, r.uniform(y0, y1)), (1, 0)
        L = 520 * q; bx, by = tip[0] + base_[0] * L, tip[1] + base_[1] * L
        wv = 30; nx, ny = -base_[1] * wv, base_[0] * wv
        dl.polygon([tip, (bx + nx, by + ny), (bx - nx, by - ny)], fill=(25, 5, 45, 255), outline=(200, 140, 255, 255), width=4)
    bg = glow_add(bg, Image.eval(lay, lambda v: v), 26, 1.4); bg = over(bg, lay)
    return bg

def make_shards(cx, cy, seed=4):
    r = np.random.default_rng(seed)
    angs = np.sort(r.uniform(0, 2 * np.pi, 15)); angs = np.append(angs, angs[0] + 2 * np.pi)
    rings = [0, 150, 380, 700, 2400]
    pts = {}
    def P(i, j):
        if (i % 15, j) not in pts:
            a = angs[i % 15] + (2 * np.pi if i >= 15 else 0); rr = rings[j] * (1 + r.uniform(-.18, .18) if 0 < j < 4 else 1)
            pts[(i % 15, j)] = (cx + math.cos(a) * rr, cy + math.sin(a) * rr)
        return pts[(i % 15, j)]
    shards = []
    for i in range(15):
        for j in range(4):
            poly = [P(i, j), P(i + 1, j), P(i + 1, j + 1), P(i, j + 1)] if j else [P(i, 0), P(i + 1, 1), P(i, 1)]
            xs, ys = [p[0] for p in poly], [p[1] for p in poly]
            bb = [int(max(0, min(xs))), int(max(0, min(ys))), int(min(W, max(xs))), int(min(H, max(ys)))]
            if bb[2] - bb[0] < 2 or bb[3] - bb[1] < 2: continue
            m = Image.new("L", (bb[2] - bb[0], bb[3] - bb[1]))
            ImageDraw.Draw(m).polygon([(x - bb[0], y - bb[1]) for x, y in poly], fill=255)
            c = (sum(xs) / len(xs) - cx, sum(ys) / len(ys) - cy); n = math.hypot(*c) or 1
            shards.append((poly, bb, m, (c[0] / n, c[1] / n), r.uniform(.6, 1.6)))
    return shards
SHARDS = make_shards(W / 2, H * .42)

def shatter(src, back, p, crack=1.0):
    """p=0: intact with cracks; p>0: shards fly outward"""
    if p <= 0:
        out = src.copy(); d = ImageDraw.Draw(out)
        for poly, *_ in SHARDS[: int(len(SHARDS) * crack)]:
            d.line(poly + [poly[0]], fill=(255, 255, 255), width=3)
        return out
    out = back.copy()
    for poly, bb, m, (dx, dy), sp in SHARDS:
        dist = p * p * 1400 * sp
        piece = src.crop(bb); piece = Image.eval(piece, lambda v: min(255, int(v * 1.15)))
        out.paste(piece, (int(bb[0] + dx * dist), int(bb[1] + dy * dist + p * p * 500)), m)
        ImageDraw.Draw(out).line([(x + dx * dist, y + dy * dist + p * p * 500) for x, y in poly] + [(poly[0][0] + dx * dist, poly[0][1] + dy * dist + p * p * 500)], fill=(230, 210, 255), width=2)
    return out

def water_moon(lt):
    img = radial_bg((20, 18, 60), (0, 0, 8), cy=.25)
    d = ImageDraw.Draw(img); mx, my = W / 2, 560
    moon = Image.new("RGBA", (W, H)); ImageDraw.Draw(moon).ellipse([mx - 170, my - 170, mx + 170, my + 170], fill=(235, 230, 255, 255))
    img = glow_add(img, moon, 60, 1.2); img = over(img, moon)
    arr = np.array(img); horizon = 1000
    refl = arr[horizon - (np.arange(H - horizon) * .9).astype(int) - 1][:, :, :].astype(np.float32)  # mirrored
    refl *= np.linspace(.8, .25, H - horizon)[:, None, None]
    rows = np.arange(H - horizon)
    shift = (np.sin(rows * .06 + lt * 5) * (6 + rows * .03)).astype(int)
    for i in range(0, H - horizon, 2): refl[i:i + 2] = np.roll(refl[i:i + 2], shift[i], axis=1)
    arr[horizon:] = np.clip(refl * np.array([.8, .8, 1.2]), 0, 255).astype(np.uint8)
    img = Image.fromarray(arr); d = ImageDraw.Draw(img)
    for k in range(4):  # ripples
        rr = ((lt * 260 + k * 170) % 700); a = int(200 * (1 - rr / 700))
        d.ellipse([mx - rr, 1250 - rr * .18, mx + rr, 1250 + rr * .18], outline=(a, a, min(255, a + 40)), width=3)
    d.line([(0, horizon), (W, horizon)], fill=(120, 110, 200), width=2)
    return over(img, petals(lt, 35, (200, 150, 255), seed=7))

def crescent(angle, scale=1.0):
    s = int(1400 * scale); m = Image.new("L", (s, s)); d = ImageDraw.Draw(m)
    d.ellipse([0, 0, s, s], fill=255); d.ellipse([s * .12, s * .06, s * 1.02, s * .96], fill=0)
    rim = ImageChops.subtract(m.filter(ImageFilter.MaxFilter(15)), m)
    im = Image.new("RGBA", (s, s), (5, 0, 0, 255)); im.putalpha(m)
    rc = Image.new("RGBA", (s, s), (255, 30, 20, 255)); rc.putalpha(rim)
    out = Image.new("RGBA", (s, s)); out.alpha_composite(rc.filter(ImageFilter.GaussianBlur(6))); out.alpha_composite(rc); out.alpha_composite(im)
    return out.rotate(angle, expand=True)
CRES = crescent(-40)

# ---------------- captions ----------------
HOT = {"FUTURE", "CHAIR", "NOTHING", "ERASED", "UNTHINKABLE", "FEARED", "KUROHITSUGI", "NEVER", "PERCEPTION", "KYOKA",
       "SUIGETSU", "WROTE", "LIE", "ICHIGO", "CELL", "SIDE", "PLAYED", "ALMIGHTY", "GOD", "SEEING"}
FCAP = F("Anton.ttf", 124)
def chunks_for(line):
    words = line["text"].upper().replace("?", "?").split(); out, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) == 3 or w[-1] in ".,?" or (len(cur) == 2 and len(" ".join(cur)) > 13):
            out.append(cur); cur = []
    if cur: out.append(cur)
    total = sum(len(" ".join(c)) + 2 for c in out); t = line["start"]; dur = line["end"] - line["start"]; res = []
    for c in out:
        dd = dur * (len(" ".join(c)) + 2) / total; res.append((t, t + dd, c)); t += dd
    return res
CAPS = [c for l in LINES if l["scene"] != "name" for c in chunks_for(l)]
_cap_cache = {}
def caption(words):
    key = " ".join(words)
    if key in _cap_cache: return _cap_cache[key]
    tmp = Image.new("RGBA", (2400, 260)); d = ImageDraw.Draw(tmp); x = 20
    for w in words:
        clean = w.strip(".,?!")
        col = YEL if clean in HOT else (255, 255, 255)
        d.text((x, 130), w, font=FCAP, fill=col + (255,), anchor="lm", stroke_width=11, stroke_fill=(0, 0, 0, 255))
        x += d.textlength(w + " ", font=FCAP)
    img = tmp.crop(tmp.getbbox())
    if img.width > 1000: img = img.resize((1000, int(img.height * 1000 / img.width)), Image.LANCZOS)
    _cap_cache[key] = img; return img

def big_text(lines_, fonts, cols, y0, gap=10, glow=PURPLE):
    lay = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(lay); y = y0
    for t_, f, c in zip(lines_, fonts, cols):
        d.text((W / 2, y), t_, font=f, fill=c + (255,), anchor="mt", stroke_width=10, stroke_fill=(0, 0, 0, 255))
        y += f.size + gap
    g = Image.new("RGBA", (W, H), glow + (0,)); g.putalpha(lay.getchannel("A"))
    return g.filter(ImageFilter.GaussianBlur(22)), lay

# ---------------- scenes ----------------
BG_RED = radial_bg((70, 0, 0), (0, 0, 0))
BG_GOLD = radial_bg((90, 60, 10), (5, 2, 0))
BG_PURP = radial_bg((50, 10, 80), (2, 0, 6))
NAME_BIG = big_text(["SOSUKE", "AIZEN"], [F("Anton.ttf", 200), F("Anton.ttf", 340)], [(255, 255, 255), (205, 165, 255)], 520)
KANJI = Image.new("RGBA", (W, H)); dk = ImageDraw.Draw(KANJI); fk = F("Mincho.ttf", 150)
for i, ch in enumerate("藍染惣右介"): dk.text((955, 170 + i * 165), ch, font=fk, fill=(180, 120, 255, 90), anchor="mm")
CTA = big_text(["WAS AIZEN", "THE REAL MVP?"], [F("Anton.ttf", 170), F("Anton.ttf", 150)], [(255, 255, 255), YEL], 560)
HOOK = big_text(["HOW AIZEN", "FOOLED A GOD"], [F("Anton.ttf", 96), F("Anton.ttf", 96)], [(255, 255, 255), (205, 165, 255)], 150, 0)

def rays(t, col, n=18, alpha=60):
    lay = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(lay); cx, cy = W / 2, H * .42
    for k in range(n):
        a = k * 2 * math.pi / n + t * .4
        d.polygon([(cx, cy), (cx + math.cos(a - .06) * 2500, cy + math.sin(a - .06) * 2500), (cx + math.cos(a + .06) * 2500, cy + math.sin(a + .06) * 2500)], fill=col + (alpha,))
    return lay.filter(ImageFilter.GaussianBlur(8))

def render_scene(sc, lt, d, gt, fi):
    if sc == "eye_open":
        img = eye_frame(EYE, open_=ease(lt / .9), scale=.9 + .06 * lt / d, bg=BG_RED)
        if lt < 2.5: img = over(img, HOOK[0]); img = over(img, HOOK[1])
        return img
    if sc == "chair_flash":
        img = scaled(chair_frame(eyes=min(1, lt / .6)), 1.25 - .12 * ease(lt / d), (.5, .45))
        return img
    if sc == "eye_king":
        bg = over(BG_GOLD, rays(gt, GOLD, 20, 70))
        return eye_frame(EYE, scale=.95 + .05 * lt / d, glow_col=GOLD, bg=bg)
    if sc == "eye_slams":
        img = eye_frame(EYE, scale=1.0, bg=over(BG_RED, SPEED_R[fi % 4]), look=30 * math.sin(lt * 9))
        hits = [d * f for f in (0, .2, .4)]
        for k, h in enumerate(hits):
            if 0 <= lt - h < .35:  # an attack streak that gets erased
                p = (lt - h) / .35; lay = Image.new("RGBA", (W, H)); dl = ImageDraw.Draw(lay)
                y = 500 + k * 260; a = int(255 * (1 - p))
                dl.line([(-50, y + 300), (W + 50, y - 300)], fill=(255, 255, 255, a), width=int(28 * (1 - p)) + 2)
                img = glow_add(img, lay, 20); img = over(img, lay)
        if lt > d * .6: img = Image.blend(img, img.convert("L").convert("RGB"), min(1, (lt - d * .6) / .3) * .8)
        return img
    if sc == "chains": return chains_frame(lt, d, d * .55)
    if sc == "chair_reveal":
        flick = 1 if lt > .5 else (0.2 if int(lt * 20) % 3 == 0 else .9)
        img = chair_frame(bright=min(1, .15 + lt / 1.2) * flick, eyes=0, dust_t=lt)
        return scaled(img, 1.0 + .18 * lt / d, (.5, .42))
    if sc == "name":
        bg = over(BG_PURP, rays(gt, PURPLE, 22, 90)); bg = over(bg, SPEED_P[fi % 4]); bg = over(bg, KANJI)
        s = 1 + .5 * (1 - ease(lt / .18)); g, t_ = NAME_BIG
        bg = over(bg, g); bg = over(bg, t_)
        return scaled(bg, s) if s > 1.001 else bg
    if sc == "coffin": return coffin_frame(lt, d)
    if sc == "coffin_break":
        src = coffin_frame(99, 2.0); back = over(radial_bg((120, 10, 10), (5, 0, 0)), SPEED_R[fi % 4])
        return shatter(src, back, max(0, (lt - .15) / 2.2))
    if sc == "eye_calm": return eye_frame(EYE, scale=.9 + .08 * lt / d, bg=BG_RED, look=40 * math.sin(lt * 1.5))
    if sc == "water_moon": return water_moon(gt)
    if sc == "mirror_shatter":
        src = eye_frame(EYE, scale=1.0, bg=BG_RED); back = water_moon(gt)
        crack = min(1, lt / .35)
        return shatter(src, back, max(0, (lt - .45) / 1.6), crack)
    if sc == "eye_hypno":
        bg = over(BG_PURP, rays(gt, PURPLE, 16, 50)); img = eye_frame(EYE_H, scale=.95, glow_col=PURPLE, bg=bg)
        ghosts = Image.blend(img, ImageChops.offset(img, int(60 * math.sin(lt * 3)), 0), .35)
        return Image.blend(ghosts, ImageChops.offset(img, -int(60 * math.sin(lt * 3)), 0), .25)
    if sc == "slash":
        bg = over(BG_PURP, rays(gt, PURPLE, 16, 40)); img = eye_frame(EYE_H, scale=.95, glow_col=PURPLE, bg=bg)
        cut = d * .55
        if lt < cut: return img
        u = lt - cut
        if u < .2:  # crescent sweep
            p = u / .2; cx, cy = W + 300 - p * (W + 900), -300 + p * (H * .9)
            return over(img, CRES, (int(cx - CRES.width / 2), int(cy - CRES.height / 2)))
        # split along the diagonal
        off = int(ease((u - .2) / .5) * 70)
        m = Image.new("L", (W, H)); ImageDraw.Draw(m).polygon([(0, 0), (W, 0), (W, H * .15), (0, H * .75)], fill=255)
        out = Image.new("RGB", (W, H)); out.paste(ImageChops.offset(img, -off, -off), (0, 0))
        top = ImageChops.offset(img, off, -off // 2); out.paste(top, (0, 0), m)
        line = Image.new("RGBA", (W, H)); ImageDraw.Draw(line).line([(0, H * .75), (W, H * .15)], fill=(255, 40, 30, 255), width=10)
        out = glow_add(out, line, 18, 1.5); return over(out, line)
    if sc == "chair_cell":
        img = chair_frame(bright=.75, tint=(20, 30, 60), strap_glow=.6, dust_t=lt)
        lay = Image.new("RGBA", (W, H)); dl = ImageDraw.Draw(lay); p = ease(lt / (d * .8))
        for k in range(8):  # bars close in from both sides
            x = (k * 70 + 30) * p if k < 4 else W - ((k - 4) * 70 + 30) * p
            dl.rectangle([x - 12, 0, x + 12, H], fill=(25, 25, 30, 255), outline=(90, 90, 110, 255), width=3)
        return over(img, lay)
    if sc == "final":
        img = chair_frame(eyes=min(1, lt / .8), strap_glow=1.4)
        img = scaled(img, 1.6 + .5 * ease(lt / d), (.5, .42))
        return Image.blend(img, over(img, SPEED_P[fi % 4]), min(1, lt / 1.5) * .6)
    if sc == "cta":
        bg = over(BG_PURP, rays(gt, PURPLE, 18, 60)); g, t_ = CTA
        bg = over(bg, g); bg = over(bg, t_); d_ = ImageDraw.Draw(bg)
        by = 1150 + 25 * math.sin(lt * 8)
        d_.text((W / 2, by), "COMMENT BELOW", font=F("Anton.ttf", 90), fill=(255, 255, 255), anchor="mt", stroke_width=8, stroke_fill=(0, 0, 0))
        d_.polygon([(W / 2 - 70, by + 130), (W / 2 + 70, by + 130), (W / 2, by + 230)], fill=YEL, outline=(0, 0, 0), width=6)
        return bg
    raise ValueError(sc)

# ---------------- timeline -> frames ----------------
segs = []
for i, l in enumerate(LINES):
    end = LINES[i + 1]["start"] if i + 1 < len(LINES) else VEND + .1
    segs.append((l["start"] if i else 0.0, end, l["scene"]))
segs.append((VEND + .1, TOTAL, "cta"))
hits = [(s, 1.0) for s, _, _ in segs]
hits += [(LINES[3]["start"] + (LINES[3]["end"] - LINES[3]["start"]) * f, .9) for f in (.2, .4)]
sl = next(l for l in LINES if l["scene"] == "slash"); hits.append((sl["start"] + (sl["end"] - sl["start"]) * .55 + .2, 1.4))
breakdown = next(l for l in LINES if l["scene"] == "chair_cell")["start"]
final_t = next(l for l in LINES if l["scene"] == "final")["start"]
bt = DROP
while bt < TOTAL:
    if bt < breakdown - .01 or bt >= final_t: hits.append((bt, .35))
    bt += BEAT
HARD = {"chair_flash", "name", "chains", "coffin", "eye_king", "final", "cta", "slash"}

if os.environ.get("STILLS"):  # contact sheet: one still per scene at 70% through
    tiles = []
    for s_, e_, sc in segs:
        lt = (e_ - s_) * float(os.environ["STILLS"]); tiles.append(render_scene(sc, lt, e_ - s_, s_ + lt, 0).resize((270, 480)))
    sheet = Image.new("RGB", (270 * 6, 480 * math.ceil(len(tiles) / 6)))
    for k, t_ in enumerate(tiles): sheet.paste(t_, (270 * (k % 6), 480 * (k // 6)))
    sheet.save(os.path.join(OUT, "sheet.png")); sys.exit()
out_path = os.path.join(OUT, "SceneSensei_Aizen_Edit.mp4")
NF = int(round(TOTAL * FPS))
def seg_at(fi):
    gt = fi / FPS
    for s_, e_, sc in segs:
        if s_ <= gt < e_: return s_, e_, sc
    return segs[-1]

def render_frame(fi):
    s, e, sc = seg_at(fi); gt = fi / FPS; lt = gt - s
    fr_rng = np.random.default_rng(fi)
    img = render_scene(sc, lt, e - s, gt, fi)
    amp = sum(st * math.exp(-(gt - h) * 12) for h, st in hits if 0 <= gt - h < .5)
    z = 1.04 + .08 * amp
    ox, oy = fr_rng.uniform(-1, 1) * 28 * amp, fr_rng.uniform(-1, 1) * 28 * amp
    img = scaled(img, z, (.5 + ox / W, .5 + oy / H))
    arr = np.asarray(img).astype(np.int16)
    ca = int(14 * amp)
    if ca:  # chromatic aberration
        arr[..., 0] = np.roll(arr[..., 0], ca, 1); arr[..., 2] = np.roll(arr[..., 2], -ca, 1)
    if amp > .8:  # glitch slices
        for _ in range(5):
            y = fr_rng.integers(0, H - 80); hgt = fr_rng.integers(10, 80)
            arr[y:y + hgt] = np.roll(arr[y:y + hgt], int(fr_rng.integers(-60, 60)), 1)
    arr = arr * VIGN + GRAIN[fi % 4]
    if sc in HARD and lt < .1: arr = arr + (255 - arr) * (.7 * (1 - lt / .1))  # impact flash
    frame = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    cap = next((c for c in CAPS if c[0] <= gt < c[1]), None)
    if cap and sc != "cta":
        ci = caption(cap[2]); pop = 1 + .3 * max(0, 1 - (gt - cap[0]) / .09)
        if pop > 1: ci = ci.resize((int(ci.width * pop), int(ci.height * pop)), Image.BILINEAR)
        frame = over(frame, ci, ((W - ci.width) // 2, 1390 - ci.height // 2))
    if gt > TOTAL - .35: frame = Image.eval(frame, lambda v, k=(TOTAL - gt) / .35: int(v * k))  # fade to black for the loop
    return frame

def worker(k, n):
    a_, b_ = NF * k // n, NF * (k + 1) // n
    ff = subprocess.Popen([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
        os.path.join(OUT, f"chunk{k}.mp4")], stdin=subprocess.PIPE)
    for fi in range(a_, b_): ff.stdin.write(render_frame(fi).tobytes())
    ff.stdin.close(); ff.wait()

if __name__ == "__main__":
    import multiprocessing as mp
    n = int(os.environ.get("WORKERS", os.cpu_count() or 4))
    ps = [mp.Process(target=worker, args=(k, n)) for k in range(n)]
    for p_ in ps: p_.start()
    for p_ in ps: p_.join()
    lst = os.path.join(OUT, "chunks.txt")
    open(lst, "w").write("".join(f"file 'chunk{k}.mp4'\n" for k in range(n)))
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                    "-i", os.path.join(OUT, "audio.wav"), "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                    "-movflags", "+faststart", out_path], check=True)
    for k in range(n): os.remove(os.path.join(OUT, f"chunk{k}.mp4"))
    print("done", out_path)
