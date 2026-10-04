"""Procedural 'motion sketch' renderer: ink-on-charcoal line animation with boiling
lines, hatching, purple Hakai-style aura glow, lightning, and beat-synced camera work.

    python render.py preview 2 12 36        # PNG stills into ./previews
    python render.py sheet  2 12 36 ...     # one contact sheet PNG
    python render.py render silent.mp4      # full 60 s video (no audio)
"""
import math
import os
import random
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

import art
from art import (BLOOD, CH, CHD, LAV, PURP, build_city, build_fist, build_vegeta,
                 lc, lerp, make_cracks, tongue)
from timeline import (BEATS, BOOM, CHARGE, DUR, END_CARD, FADE_START, FPS, HEART, HIT_DIR,
                      HITS, IMPACT, ROLL, TITLE_SLAM)

W, H = 1920, 1080
K = W / 1280.0                 # design space is 1280x720
HW, HH = W // 2, H // 2        # half-res buffer for glows
NFRAMES = int(round(DUR * FPS))

FONT_SANS = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
FONT_MONO = "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"
_fonts = {}


def font(path, size):
    key = (path, int(size))
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(path, int(size))
    return _fonts[key]


# ------------------------------------------------------------------ helpers
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def seg(t, a, b):
    return clamp((t - a) / (b - a))


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def pulse(t, times, decay=0.13):
    best = 0.0
    for te in times:
        if te <= t:
            v = math.exp(-(t - te) / decay)
            if v > best:
                best = v
    return best


def hit_state(t):
    idx = -1
    for i, h in enumerate(HITS):
        if h <= t:
            idx = i
    if idx < 0:
        return None
    return idx, t - HITS[idx], HIT_DIR[idx]


def n_hits(t):
    return sum(1 for h in HITS if h <= t)


NZ = None


def set_boil(f):
    """Line wobble re-rolls every 2nd frame (12 fps 'boil')."""
    global NZ
    NZ = np.random.default_rng(5000 + f // 2).normal(size=(8192, 2)).astype(np.float32)


class Cam:
    def __init__(self, fx, fy, z, roll=0.0, sx=0.0, sy=0.0):
        self.fx, self.fy, self.z = fx, fy, z
        self.c, self.s = math.cos(roll), math.sin(roll)
        self.sx, self.sy = sx * K, sy * K

    def p(self, pt):
        x = (pt[0] - self.fx) * self.z * K
        y = (pt[1] - self.fy) * self.z * K
        return (W / 2 + self.sx + x * self.c - y * self.s, H / 2 + self.sy + x * self.s + y * self.c)

    def pts(self, pts):
        return [self.p(p) for p in pts]


def wob(pts, ident, amp, closed=False, step=38.0):
    seq = list(pts) + ([pts[0]] if closed else [])
    out = []
    base = ident * 977
    k = 0
    for a, b in zip(seq[:-1], seq[1:]):
        d = math.hypot(b[0] - a[0], b[1] - a[1])
        m = max(1, int(d // (step * K)))
        for j in range(m):
            u = j / m
            nz = NZ[(base + k) % 8192]
            k += 1
            out.append((a[0] + (b[0] - a[0]) * u + nz[0] * amp, a[1] + (b[1] - a[1]) * u + nz[1] * amp))
    nz = NZ[(base + k) % 8192]
    out.append((seq[-1][0] + nz[0] * amp, seq[-1][1] + nz[1] * amp))
    return out


def trim(pts, p):
    if p >= 1:
        return pts
    if p <= 0 or len(pts) < 2:
        return []
    L = [0.0]
    for a, b in zip(pts[:-1], pts[1:]):
        L.append(L[-1] + math.dist(a, b))
    tgt = L[-1] * p
    out = [pts[0]]
    for i in range(1, len(pts)):
        if L[i] <= tgt:
            out.append(pts[i])
        else:
            u = (tgt - L[i - 1]) / (L[i] - L[i - 1] + 1e-9)
            a, b = pts[i - 1], pts[i]
            out.append((a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u))
            break
    return out


def stroke(d, pts, col, w, ident, amp=1.5, closed=False, alpha=255, p=1.0):
    wp = wob(pts, ident, amp * K, closed)
    if closed:
        wp = wp + [wp[0]]
    wp = trim(wp, p)
    if len(wp) > 1:
        d.line(wp, fill=tuple(col) + (alpha,), width=max(1, int(w)), joint='curve')
    return wp


def draw_hatch(layer, pts, it, z):
    xs = [q[0] for q in pts]
    ys = [q[1] for q in pts]
    x0, x1 = int(max(0, min(xs))), int(min(W, max(xs)) + 1)
    y0, y1 = int(max(0, min(ys))), int(min(H, max(ys)) + 1)
    if x1 - x0 < 4 or y1 - y0 < 4:
        return
    bw, bh = x1 - x0, y1 - y0
    mask = Image.new('L', (bw, bh), 0)
    ImageDraw.Draw(mask).polygon([(x - x0, y - y0) for x, y in pts], fill=255)
    hat = Image.new('L', (bw, bh), 0)
    hd = ImageDraw.Draw(hat)
    ang = it['angle']
    sp = max(4.0, it['spacing'] * z * K)
    D = math.hypot(bw, bh)
    ca, sa = math.cos(ang), math.sin(ang)
    o = -D / 2
    i = 0
    while o < D / 2:
        j = NZ[(it['id'] * 31 + i) % 8192][0] * 1.2
        cx = bw / 2 - sa * (o + j)
        cy = bh / 2 + ca * (o + j)
        hd.line((cx - ca * D, cy - sa * D, cx + ca * D, cy + sa * D), fill=255, width=max(1, int(1.4 * K)))
        o += sp
        i += 1
    comb = ImageChops.multiply(mask, hat)
    layer.paste(tuple(it['col']) + (235,), (x0, y0), comb)


def draw_items(layer, items, cam, p_draw=1.0, amp=1.4):
    d = ImageDraw.Draw(layer)
    n = len(items)
    for k_, it in enumerate(items):
        pk = 1.0 if p_draw >= 1 else clamp(p_draw * n - k_)
        if pk <= 0:
            continue
        pts = cam.pts(it['pts'])
        if it['kind'] == 'hatch':
            if pk >= 1:
                draw_hatch(layer, pts, it, cam.z)
            continue
        wpx = max(1.0, it['w'] * (0.5 + 0.5 * cam.z) * K)
        closed = it['closed']
        wp = wob(pts, it['id'], amp * K, closed)
        if it['fill'] is not None and pk >= 1:
            d.polygon(wp, fill=tuple(it['fill']) + (255,))
        full = wp + [wp[0]] if closed else wp
        full = trim(full, pk)
        if len(full) > 1:
            d.line(full, fill=tuple(it['col']) + (255,), width=int(round(wpx)), joint='curve')
        if pk >= 1 and wpx >= 2:     # pencil double-stroke
            w2 = wob(pts, it['id'] + 5000, amp * 1.8 * K, closed)
            if closed:
                w2 = w2 + [w2[0]]
            dim = lc(it['col'], (40, 36, 50), 0.45)
            d.line(w2, fill=dim + (200,), width=max(1, int(wpx // 2)), joint='curve')


# ------------------------------------------------------------------ static art
CITY = build_city()
CRACKS_FLAT = make_cracks(11, 16)
CRACKS_WORLD = make_cracks(23, 12)
_yy = np.linspace(0, 1, H, dtype=np.float32)[:, None]
_xx = np.linspace(-1, 1, W, dtype=np.float32)[None, :]
_top = np.array([8, 7, 16], np.float32)
_bot = np.array([30, 20, 46], np.float32)
BG_ARR = np.clip(_top + (_bot - _top) * (_yy ** 1.6)[..., None] + 0 * _xx[..., None], 0, 255).astype(np.uint8)
_r = np.sqrt((_xx * 0.85) ** 2 + ((_yy - 0.5) * 2 * 0.85) ** 2)
VIG = (1 - 0.55 * np.clip((_r - 0.55) / 0.75, 0, 1) ** 1.4)[..., None].astype(np.float32)
_grng = np.random.default_rng(7)
GRAIN = [(_grng.normal(0, 5.0, (H, W)).astype(np.float32))[..., None] for _ in range(3)]
GX, GY = np.meshgrid(np.arange(HW, dtype=np.float32), np.arange(HH, dtype=np.float32))

_prng = np.random.default_rng(42)
PN = 170
P_X = _prng.uniform(0, 1, PN)
P_PH = _prng.uniform(0, 1, PN)
P_SP = _prng.uniform(0.3, 1.0, PN)
P_SZ = _prng.uniform(0.6, 2.2, PN)


# ------------------------------------------------------------------ fx
def draw_particles(d, t, amount, mode):
    for i in range(int(PN * amount)):
        if mode == 'ash':
            x = (P_X[i] * W + 30 * K * math.sin(t * 0.7 + i)) % W
            y = (P_PH[i] * H + 40 * K * P_SP[i] * t) % (H + 20)
            r = P_SZ[i] * K
            d.ellipse((x - r, y - r, x + r, y + r), fill=(170, 165, 180, 150))
        else:
            sp = (120 + 260 * P_SP[i]) * K
            span = H + 60 * K
            y = H + 30 * K - ((P_PH[i] * span + sp * t) % span)
            x = P_X[i] * W + 40 * K * math.sin(t * 2.2 + i * 1.3)
            ln = (6 + 16 * P_SP[i]) * K
            col = (236, 190, 255, 220) if i % 3 else (255, 120, 220, 220)
            d.line((x, y, x + math.sin(t + i) * 2 * K, y + ln), fill=col,
                   width=max(1, int(P_SZ[i] * K * 0.9)))


def bolt(p0, p1, rng, depth=5, disp=0.22):
    pts = [p0, p1]
    for _ in range(depth):
        new = [pts[0]]
        for a, b in zip(pts[:-1], pts[1:]):
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            L = math.hypot(b[0] - a[0], b[1] - a[1]) + 1e-6
            nx, ny = -(b[1] - a[1]) / L, (b[0] - a[0]) / L
            o = rng.uniform(-1, 1) * L * disp
            new.append((mx + nx * o, my + ny * o))
            new.append(b)
        pts = new
    return pts


def draw_lightning(d, gd, amount, cx, cy, spread, f):
    n = int(1 + 6 * amount)
    for i in range(n):
        rng = random.Random(f * 31 + i)
        a = rng.uniform(0, 2 * math.pi)
        r0 = spread * rng.uniform(0.35, 0.8)
        r1 = r0 + spread * rng.uniform(0.35, 0.9)
        p0 = (cx + math.cos(a) * r0, cy + math.sin(a) * r0 * 0.8)
        p1 = (cx + math.cos(a + rng.uniform(-0.5, 0.5)) * r1, cy + math.sin(a + rng.uniform(-0.5, 0.5)) * r1 * 0.8)
        pts = bolt(p0, p1, rng)
        gd.line([(x / 2, y / 2) for x, y in pts], fill=(150, 70, 255), width=max(2, int(6 * K / 2)))
        d.line(pts, fill=(240, 225, 255, 255), width=max(1, int(2.2 * K)))
        if rng.random() < 0.6:
            mid = pts[len(pts) // 2]
            br = bolt(mid, (mid[0] + rng.uniform(-1, 1) * spread * 0.4, mid[1] + rng.uniform(-1, 1) * spread * 0.4),
                      rng, depth=4)
            d.line(br, fill=(220, 180, 255, 220), width=max(1, int(1.4 * K)))


def draw_speed(d, cx, cy, amount, f, rmin=300):
    rng = random.Random(f * 17 + 5)
    for _ in range(int(80 * amount)):
        a = rng.uniform(0, 2 * math.pi)
        r0 = rng.uniform(rmin, rmin + 380) * K
        r1 = r0 + rng.uniform(250, 800) * K
        w = rng.choice([1, 1, 2, 3])
        al = rng.randint(100, 230)
        d.line((cx + math.cos(a) * r0, cy + math.sin(a) * r0 * 0.78,
                cx + math.cos(a) * r1, cy + math.sin(a) * r1 * 0.78),
               fill=(235, 225, 255, al), width=max(1, int(w * K)))


def draw_rings(d, cx, cy, t, births, scale=1.0, col=LAV, ident=300, maxage=1.3):
    for bi, tb in enumerate(births):
        age = t - tb
        if 0 <= age < maxage:
            u = age / maxage
            r = (170 + 1000 * (u ** 0.6)) * K * scale
            a = int(220 * (1 - u) ** 1.2)
            wd = max(1, int((7 * (1 - u) + 1) * K))
            pts = [(cx + math.cos(2 * math.pi * i / 48) * r, cy + math.sin(2 * math.pi * i / 48) * r * 0.62)
                   for i in range(48)]
            stroke(d, pts, col, wd, ident + bi, amp=3, closed=True, alpha=a)


def draw_hit_fx(d, cam, t):
    hs = hit_state(t)
    if hs is None:
        return
    idx, age, dr = hs
    if age > 1.1:
        return
    px, py = cam.p((dr * 100, 5))
    if age < 0.24:
        u = age / 0.24
        r = (30 + 230 * u ** 0.5) * K * max(0.8, cam.z)
        n = 14
        pts = []
        for i in range(2 * n):
            a = math.pi * i / n + idx
            rr = r * (1.0 if i % 2 == 0 else 0.45)
            pts.append((px + math.cos(a) * rr, py + math.sin(a) * rr))
        d.polygon(wob(pts, 700 + idx, 2 * K, True), fill=(255, 250, 255, int(255 * (1 - u))))
        for i in range(10):
            a = i * math.pi / 5 + idx
            d.line((px + math.cos(a) * r * 1.1, py + math.sin(a) * r * 1.1,
                    px + math.cos(a) * r * 1.9, py + math.sin(a) * r * 1.9),
                   fill=(255, 255, 255, int(220 * (1 - u))), width=max(1, int(3 * K)))
    rng = random.Random(idx * 7 + 3)
    base = 0.0 if -dr > 0 else math.pi
    fade = 1.0 if age < 0.6 else max(0.0, 1 - (age - 0.6) / 0.5)
    for _ in range(18):
        ang = base + rng.uniform(-0.9, 0.9)
        v = rng.uniform(300, 950) * K
        vx, vy = math.cos(ang) * v, math.sin(ang) * v - 220 * K
        x = px + vx * age
        y = py + vy * age + 0.5 * 1800 * K * age * age
        r = rng.uniform(2.5, 6) * K
        d.ellipse((x - r, y - r, x + r * 1.4, y + r), fill=BLOOD + (int(235 * fade),))


# ------------------------------------------------------------------ glow
def aura_img(t, x0, x1, by, hmax):
    img = Image.new('RGB', (HW, HH), (0, 0, 0))
    d = ImageDraw.Draw(img)
    N = 15
    layers = [((72, 12, 150), 1.0, 1.0), ((140, 48, 240), 0.78, 0.8),
              ((212, 150, 255), 0.55, 0.6), ((255, 236, 255), 0.32, 0.4)]
    for col, hs, ws in layers:
        for i in range(N):
            u = i / (N - 1)
            env = 0.35 + 0.65 * math.sin(math.pi * u) ** 0.9
            ph = i * 1.9
            h = hmax * hs * env * (0.72 + 0.28 * math.sin(t * 8.0 + ph)) * (0.85 + 0.3 * ((i * 37) % 11) / 11)
            w = (x1 - x0) / N * 3.0 * ws
            bx = x0 + (x1 - x0) * u + 12 * math.sin(t * 3 + ph) * K
            pts = tongue(bx, by, w, h, math.sin(t * 5 + ph) * 0.6, ph)
            d.polygon([(px / 2, py / 2) for px, py in pts], fill=col)
    return img


def radial(cx, cy, sigma, col, k):
    g = np.exp(-(((GX - cx / 2) ** 2 + (GY - cy / 2) ** 2) / (2 * (sigma / 2) ** 2))) * k
    return g[..., None] * np.array(col, np.float32)


# ------------------------------------------------------------------ text
def draw_text(layer, text, cx, cy, size, col, alpha=1.0, fpath=FONT_MONO, spacing=0.0,
              stroke_w=3, stroke_col=(0, 0, 0), align='center', jitter=0.0, rng=None):
    f = font(fpath, size * K)
    d = ImageDraw.Draw(layer)
    widths = [f.getlength(ch) + spacing * K for ch in text]
    total = sum(widths)
    x = cx * K - (total / 2 if align == 'center' else 0)
    y = cy * K
    a = int(255 * clamp(alpha))
    for ch, wd in zip(text, widths):
        jx = jy = 0.0
        if jitter and rng is not None:
            jx, jy = rng.uniform(-jitter, jitter) * K, rng.uniform(-jitter, jitter) * K
        d.text((x + jx, y + jy), ch, font=f, fill=tuple(col) + (a,), anchor='lm',
               stroke_width=int(stroke_w * K), stroke_fill=tuple(stroke_col) + (a,))
        x += wd


def type_alpha(t, a, b, fi=0.3, fo=0.35):
    return clamp(min((t - a) / fi, (b - t) / fo))


def draw_texts(layer, t, f, gd):
    def typed(s, a, b):
        n = int(len(s) * seg(t, a, a + 0.7))
        return s[:max(1, n)]

    cap = [
        (1.2, 3.0, "BEATEN.", 90, 110, 56, CH, 'left'),
        (3.0, 4.9, "BLOODIED.", 90, 110, 56, CH, 'left'),
        (5.2, 8.6, "BUT NOT BROKEN.", 90, 110, 64, LAV, 'left'),
        (9.5, 13.0, "HE TRAINED WITH A GOD OF DESTRUCTION...", 640, 655, 38, CH, 'center'),
        (13.2, 16.8, "...AND LEARNED TO TURN PAIN INTO POWER.", 640, 655, 38, LAV, 'center'),
        (17.2, 20.4, "THE MORE HE BLEEDS...", 640, 655, 46, CH, 'center'),
        (20.8, 25.9, "...THE STRONGER HE GROWS.", 640, 655, 46, LAV, 'center'),
    ]
    for a, b, s, x, y, sz, col, al in cap:
        if a <= t < b:
            draw_text(layer, typed(s, a, b), x, y, sz, col, alpha=type_alpha(t, a, b), spacing=4, align=al)
    # ULTRA EGO slam
    ta, tb = TITLE_SLAM, TITLE_SLAM + 4.0
    if ta <= t < tb:
        age = t - ta
        sc = 1 + 1.4 * math.exp(-age / 0.09)
        rng = random.Random(f)
        sh = 14 * math.exp(-age / 0.25)
        al = clamp(min(age / 0.05, (tb - t) / 0.5))
        draw_text(layer, "ULTRA EGO", 640, 610, 150 * sc, (244, 230, 255), alpha=al, fpath=FONT_SANS,
                  spacing=10, stroke_w=7, stroke_col=(92, 22, 176), jitter=sh, rng=rng)
        if gd is not None:
            draw_text(gd, "ULTRA EGO", 640 / 2 * 1.0, 610 / 2, 150 * sc / 2, (150, 70, 255), alpha=al * 0.9,
                      fpath=FONT_SANS, spacing=10 / 2, stroke_w=12, stroke_col=(150, 70, 255))
    # end card
    if END_CARD <= t < FADE_START + 2:
        age = t - END_CARD
        ex = 905
        draw_text(layer, "VEGETA", ex, 300, 106, CH, alpha=smooth(age / 0.9), fpath=FONT_SANS, spacing=22,
                  stroke_w=5, stroke_col=(12, 10, 20))
        if t >= END_CARD + 1.4:
            draw_text(layer, "ULTRA EGO", ex, 395, 52, LAV, alpha=smooth((t - END_CARD - 1.4) / 0.9),
                      fpath=FONT_SANS, spacing=28, stroke_w=3, stroke_col=(40, 10, 80))
        if t >= END_CARD + 3.6:
            draw_text(layer, "A MOTION SKETCH TRIBUTE", ex, 458, 22, CHD, alpha=smooth((t - END_CARD - 3.6) / 0.9),
                      spacing=7, stroke_w=2)


# ------------------------------------------------------------------ shots
BLUR_VIEWS = [(0, 30, 1.1, 0.04), (-40, -5, 1.8, -0.06), (30, 50, 1.3, 0.08), (0, 95, 2.1, -0.03),
              (45, -10, 1.9, 0.05)]
RAPID = [(50, -12, 3.0, 0.06), (0, 95, 2.2, -0.05), (-45, -12, 3.2, -0.08), (0, 40, 1.5, 0.1),
         (0, -150, 1.3, -0.04), (30, 60, 2.6, 0.07)]


def shot(t):
    P = dict(tilt=0.0, drop=0.0, eye_open=1.0, glow=0.0, grin=0.0, battered=0.0, hair_up=0.0,
             furrow=0.4, ue=0.0, hp=0.0, armor=1.0, sway=0.0, splay=0.0, full=False, squint=0.0)
    S = dict(mode='bust', P=P, view=(0, 60, 0.8, 0.0), shake=0.0, kick=(0.0, 0.0), bg='dark',
             aura=0.0, abase='chest', ash=0.0, embers=0.0, lightning=0.0, speed=0.0, glyph=0.0,
             rings=[], ring_scale=1.0, flash=0.0, fade=0.0, draw_p=1.0, cracks=0.0, blackout=False,
             hitfx=False, rl=0.0, glint=0.0)
    hb = pulse(t, HEART, 0.2)
    beat = pulse(t, BEATS, 0.14)

    if t < 9:                                                         # ---- A wide, battered
        u = smooth(t / 9)
        S.update(mode='full', bg='city', view=(0, lerp(300, 255, u), lerp(0.50, 0.57, u) + 0.004 * hb, 0.0))
        P.update(full=True, tilt=0.2, drop=26, eye_open=0, battered=1, armor=0.5, furrow=0.7)
        S.update(draw_p=smooth(seg(t, 0.6, 5.2)), aura=seg(t, 6.5, 9.0) * 0.22, abase='feet', ash=0.6,
                 fade=max(1 - smooth(seg(t, 0, 1.3)), smooth(seg(t, 8.82, 9.0))))
    elif t < 17:                                                      # ---- B head lifts
        u = smooth(seg(t, 9, 17))
        hr = smooth(seg(t, 13.4, 15.0))
        S.update(mode='bust', view=(0, lerp(60, 40, u), lerp(0.80, 0.98, u) + 0.012 * hb, 0.0),
                 aura=lerp(0.2, 0.35, u), ash=0.4,
                 fade=max(smooth(1 - (t - 9) / 0.4), smooth(seg(t, 16.82, 17.0))))
        P.update(tilt=0.12 * (1 - hr), drop=18 * (1 - hr), eye_open=smooth(seg(t, 14.6, 15.4)), battered=1,
                 armor=0.5, furrow=0.6 + 0.3 * seg(t, 15, 17), glow=0.12 * seg(t, 15.4, 17))
    elif t < 27:                                                      # ---- C pain becomes power
        nh = n_hits(t)
        S.update(aura=min(0.85, 0.38 + 0.05 * nh), ash=0.2, embers=0.1 * nh / 13, hitfx=True,
                 fade=smooth(1 - (t - 17) / 0.3))
        P.update(battered=1, armor=0.5 if t < 21.0 else 0.0, glow=min(0.7, 0.12 + 0.06 * nh), furrow=0.9)
        hs = hit_state(t)
        if hs and hs[1] < 0.6:
            idx, age, dr = hs
            P['tilt'] += dr * 0.14 * math.exp(-age / 0.12)
            P['squint'] = 0.8 * math.exp(-age / 0.15)
            S['kick'] = (-dr * 45 * math.exp(-age / 0.10), 0.0)
            S['flash'] = 0.2 * math.exp(-age / 0.05)
            S['speed'] = 0.8 * math.exp(-age / 0.1)
            S['shake'] = 8 * math.exp(-age / 0.2)
        if t < 21.5:
            S['view'] = (0, 40, 0.92 + 0.01 * seg(t, 17, 21.5), 0.0)
        elif t < 22.1:
            S.update(mode='fist', view=(0, 150, 1.5, 0.0), lightning=0.2, shake=2.5)
        elif t < 22.9:
            S['view'] = (0, 30, 1.25, 0.0)
        elif t < 25.9:
            hi = hs[0] if hs else 0
            v = BLUR_VIEWS[hi % len(BLUR_VIEWS)]
            S['view'] = (v[0], v[1], v[2], v[3])
        else:
            u = seg(t, 25.9, 27)
            S['view'] = (0, 40, 0.95 + 0.04 * u, 0.0)
            P.update(tilt=0.0, grin=0.5 * smooth(seg(t, 26.4, 27)), glow=0.75)
    elif t < 35:                                                      # ---- D build-up
        rl = pulse(t, ROLL, 0.08)
        b = seg(t, 27, 34.5)
        S.update(aura=0.85, embers=0.3 + 0.7 * b, shake=1.5 + 9 * b, rl=rl, fade=smooth(1 - (t - 27) / 0.25))
        P.update(battered=1, armor=0.0, glow=0.5 + 0.5 * b, furrow=1.0, hair_up=0.45 * seg(t, 30.5, 34.5),
                 hp=0.4 * seg(t, 31.4, 34.5), grin=0.5)
        z_k = 1 + 0.03 * rl
        if t < 29.0:
            S['view'] = (0, 40, lerp(0.95, 1.08, seg(t, 27, 29)) * z_k, 0.0)
            S['lightning'] = 0.3 * seg(t, 27, 29)
        elif t < 30.2:
            S.update(mode='fist', view=(0, 150, 1.5 * z_k, 0.0), lightning=0.7, shake=5 + 4 * b)
        elif t < 31.4:
            S.update(mode='ground', cracks=seg(t, 30.2, 31.2), lightning=0.4)
        elif t < 32.4:
            S.update(view=(0, 40, 1.0 * z_k, 0.03 * math.sin(t * 6)), lightning=0.7)
        elif t < 33.2:
            S.update(view=(50, -12, 3.0 * z_k, 0.0), lightning=0.8)
        elif t < 34.2:
            v = RAPID[int((t - 33.2) / 0.125) % len(RAPID)]
            S.update(view=(v[0], v[1], v[2] * z_k, v[3]), lightning=0.9, shake=10)
        else:
            S.update(mode='bust', blackout=True, aura=0.0, embers=0.0, lightning=0.0, shake=0.0)
            S['glint'] = smooth(seg(t, 34.2, 34.98))
    elif t < 49:                                                      # ---- E ULTRA EGO
        age = t - BOOM
        P.update(ue=1, hp=1, hair_up=1, glow=1, grin=smooth(seg(t, 35, 35.7)), battered=0.5, armor=0.0,
                 furrow=0.9, sway=1)
        S.update(aura=1.0, embers=1.0, lightning=0.9, glyph=1.0, rings=BEATS,
                 flash=math.exp(-age / 0.3), shake=3 + 22 * math.exp(-age / 0.5))
        if t < 41:
            u = smooth(seg(t, 35, 41))
            S.update(view=(0, 30, lerp(0.86, 1.0, u) * (1 + 0.04 * beat), 0.045 * math.sin(age * 0.9)),
                     speed=0.25 + 0.65 * (1 - seg(t, 35, 39)))
        elif t < 44.2:
            u = smooth(seg(t, 41, 44.2))
            S.update(mode='full', bg='city', abase='feet', cracks=1.0, flash=0.0, shake=3 * beat,
                     view=(0, lerp(335, 350, u), lerp(0.55, 0.60, u) * (1 + 0.03 * beat), 0.0))
            P.update(full=True, splay=1.0)
        elif t < 45.2:
            S.update(view=(0, -10, lerp(2.4, 2.7, seg(t, 44.2, 45.2)) * (1 + 0.04 * beat), 0.0), flash=0.0,
                     shake=3 * beat)
        elif t < 46.2:
            S.update(view=(0, 95, lerp(2.1, 2.4, seg(t, 45.2, 46.2)) * (1 + 0.04 * beat), 0.0), flash=0.0,
                     shake=3 * beat)
        elif t < CHARGE:
            S.update(mode='fist', view=(0, 150, 1.5 * (1 + 0.05 * beat), 0.0), lightning=1.0, flash=0.0)
        else:
            u = seg(t, CHARGE, IMPACT)
            S.update(view=(0, 30, lerp(0.9, 3.6, u ** 2.2), 0.03 * math.sin(t * 9)), speed=1.0, flash=0.0,
                     shake=4 + 14 * u, rings=[])
            S['flash'] = 0.65 * seg(t, 48.8, 49.0)
    else:                                                             # ---- F impact, resolve
        age = t - IMPACT
        u = smooth(seg(t, 49, 60))
        S.update(mode='full', bg='city', abase='feet', cracks=1.0, aura=lerp(1.0, 0.7, u), embers=0.8,
                 glyph=0.0, rings=[IMPACT, IMPACT + 0.45], ring_scale=1.5,
                 flash=math.exp(-age / 0.45), shake=18 * math.exp(-age / 0.6),
                 view=(330 * smooth(seg(t, 50.2, 52.2)), lerp(330, 385, u), lerp(0.62, 0.46, u), 0.0),
                 fade=smooth(seg(t, FADE_START, 60.0)))
        P.update(ue=1, hp=1, hair_up=1, glow=1, grin=lerp(0.9, 0.3, u), battered=0.5, armor=0.0,
                 furrow=0.9, sway=0.7, full=True, splay=0.7 * (1 - u))
    return S


# ------------------------------------------------------------------ compositing
def draw_city_layer(layer, cam, crack_p, ue):
    d = ImageDraw.Draw(layer)
    mx, my = cam.p((-520, -90))
    r = 200 * cam.z * K
    stroke(d, [(mx + math.cos(a * math.pi / 24) * r, my + math.sin(a * math.pi / 24) * r) for a in range(48)],
           (70, 66, 90), max(1, int(2 * K)), 900, amp=2, closed=True)
    gy = cam.p((0, 905))[1]
    for poly in CITY[0]:
        wp = wob(cam.pts(poly), 910, 1.6 * K, True)
        d.polygon(wp, fill=(15, 13, 26, 255))
        d.line(wp, fill=(90, 86, 112, 255), width=max(1, int(1.5 * K)))
    for top, floors in CITY[1]:
        wp = wob(cam.pts(top), 920 + len(top), 1.6 * K, True)
        d.polygon(wp, fill=(10, 9, 18, 255))
        d.line(wp, fill=CHD + (255,), width=max(1, int(2 * K)), joint='curve')
        for fl in floors:
            d.line(wob(cam.pts(fl), 930, 1.5 * K), fill=(90, 86, 108, 200), width=max(1, int(1.5 * K)))
    if gy < H:
        d.rectangle((0, max(0, gy), W, H), fill=(12, 10, 18, 255))
    stroke(d, cam.pts([(-2300, 905), (2300, 905)]), CHD, max(1, int(3 * K)), 940, amp=2)
    for rb in CITY[2]:
        wp = wob(cam.pts(rb), 950 + int(rb[0][0]), 1.4 * K, True)
        d.polygon(wp, fill=(20, 18, 30, 255))
        d.line(wp + [wp[0]], fill=CHD + (255,), width=max(1, int(1.5 * K)))
    if crack_p > 0:
        ccol = lc(CHD, LAV, ue)
        for i, c in enumerate(CRACKS_WORLD):
            pts = cam.pts([(x * 2.2, 915 + y * 0.16) for x, y in c])
            stroke(d, pts, ccol, max(1, int(2.2 * K)), 960 + i, amp=1.2, p=clamp(crack_p * 1.6 - 0.04 * (i % 7)))


def draw_ground_layer(layer, t, p, ue):
    d = ImageDraw.Draw(layer)
    cx, cy = W / 2, H * 0.58
    for i, c in enumerate(CRACKS_FLAT):
        pts = [(cx + x * 1.15 * K, cy + y * 1.15 * K) for x, y in c]
        stroke(d, pts, CH, max(2, int(3 * K)), 1000 + i, amp=1.5, p=clamp(p * 1.5 - 0.03 * (i % 9)))
    rng = random.Random(77)
    for i in range(46):
        ang = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(60, 700) * K * seg(p, 0.1, 1.0)
        x = cx + math.cos(ang) * rr
        y = cy + math.sin(ang) * rr * 0.8 - 90 * K * seg(p, 0.3, 1.0) * rng.uniform(0.4, 1.2) \
            - (t * 20 * K * rng.uniform(0.2, 1))
        s_ = rng.uniform(5, 16) * K
        d.polygon([(x, y), (x + s_, y - s_ * 0.4), (x + s_ * 0.8, y + s_ * 0.6), (x - s_ * 0.2, y + s_ * 0.5)],
                  fill=(26, 22, 36, 255), outline=CHD + (255,))


def draw_glyph(d, cx, cy, t, z, amount):
    R = 330 * z * K * (0.9 + 0.1 * math.sin(t * 3))
    a = int(190 * amount)
    for rr, wd in ((R, 3), (R * 0.82, 2), (R * 1.08, 1)):
        pts = [(cx + math.cos(i * math.pi / 32) * rr, cy + math.sin(i * math.pi / 32) * rr * 0.9) for i in range(64)]
        stroke(d, pts, LAV, max(1, int(wd * K)), 1100 + int(rr), amp=1.8, closed=True, alpha=a)
    rot = t * 0.6
    for i in range(24):
        ang = rot + i * math.pi / 12
        r0, r1 = R * 0.82, R * (1.0 if i % 2 else 0.93)
        d.line((cx + math.cos(ang) * r0, cy + math.sin(ang) * r0 * 0.9,
                cx + math.cos(ang) * r1, cy + math.sin(ang) * r1 * 0.9),
               fill=LAV + (a,), width=max(1, int(2 * K)))
    for off in (0, math.pi / 3):
        tri = [(cx + math.cos(rot * -1.4 + off + k * 2 * math.pi / 3) * R * 0.78,
                cy + math.sin(rot * -1.4 + off + k * 2 * math.pi / 3) * R * 0.78 * 0.9) for k in range(3)]
        stroke(d, tri, PURP, max(1, int(2 * K)), 1200 + int(off * 10), amp=1.5, closed=True, alpha=a)


def render_frame(f):
    t = f / FPS
    set_boil(f)
    S = shot(t)
    P = S['P']
    fx, fy, z, roll = S['view']
    rng = np.random.default_rng(9000 + f)
    sh = S['shake']
    sx = (rng.uniform(-1, 1) * sh) + S['kick'][0]
    sy = (rng.uniform(-1, 1) * sh) + S['kick'][1]
    cam = Cam(fx, fy, z, roll, sx, sy)
    mode = S['mode']

    img = Image.fromarray(BG_ARR) if not S['blackout'] else Image.new('RGB', (W, H), (4, 3, 8))

    def paste(layer):
        img.paste(layer, (0, 0), layer)

    anchors = {}
    items = None
    if mode in ('bust', 'full') and not S['blackout']:
        items, anchors = build_vegeta(P, t)
    elif mode == 'fist':
        items, anchors = build_fist(P, t)

    # --- world background
    if mode == 'ground':
        bl = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        draw_ground_layer(bl, t, S['cracks'], P['ue'])
        paste(bl)
    elif S['bg'] == 'city' and not S['blackout']:
        bl = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        draw_city_layer(bl, cam, S['cracks'], P['ue'])
        paste(bl)

    # --- glow behind
    back = np.zeros((HH, HW, 3), np.float32)
    head_scr = cam.p(anchors['head']) if 'head' in anchors else (W / 2, H * 0.45)
    if S['aura'] > 0.01 and mode != 'ground':
        if S['abase'] == 'chest':
            x0 = cam.p((-260, 330))[0]
            x1, by = cam.p((260, 330))
            hmax = 900 * cam.z * K
        else:
            x0 = cam.p((-300, 905))[0]
            x1, by = cam.p((300, 905))
            hmax = 1500 * cam.z * K
        if mode == 'fist':
            x0, x1, by, hmax = W * 0.25, W * 0.75, H * 1.02, 700 * K
        ai = aura_img(t, x0, x1, by, hmax).filter(ImageFilter.GaussianBlur(6))
        back += np.asarray(ai, np.float32) * S['aura']
        back += radial(head_scr[0], head_scr[1], 260 * cam.z * K, (110, 40, 200), 0.5 * S['aura'])
    if mode == 'ground' and S['cracks'] > 0:
        back += radial(W / 2, H * 0.58, 420 * K, (120, 40, 210), 0.5 * S['cracks'])
    if S['glint'] > 0:
        for sgn in (-1, 1):
            back += radial(W / 2 + sgn * 130 * K, H / 2, 40 * K * (0.4 + S['glint']), (235, 170, 255), 0.9 * S['glint'])

    # aura sits BEHIND the figure so his face stays readable (screen-blend onto the backdrop now)
    gl = np.clip(back, 0, 255).astype(np.uint8)
    img = ImageChops.screen(img, Image.fromarray(gl).resize((W, H), Image.BILINEAR))

    # --- mid layer (sketch lines behind figure)
    ml = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    md = ImageDraw.Draw(ml)
    if S['aura'] > 0.3 and mode in ('bust', 'full'):
        by = cam.p((0, 330))[1] if S['abase'] == 'chest' else cam.p((0, 905))[1]
        spread = (520 if S['abase'] == 'chest' else 600) * cam.z * K
        cxm = cam.p((0, 0))[0]
        for i in range(9):
            rr = random.Random(f // 2 * 9 + i)
            bx = cxm + (i - 4) * spread / 4.6
            h_ = (700 if S['abase'] == 'chest' else 1100) * cam.z * K * S['aura'] * (0.6 + 0.5 * rr.random())
            pts = tongue(bx, by, spread / 4.2, h_, math.sin(t * 4 + i) * 0.5, i * 1.3)
            stroke(md, pts, LAV, max(1, int(2 * K)), 1300 + i, amp=2.2, alpha=int(150 * S['aura']))
    if S['glyph'] > 0:
        draw_glyph(md, head_scr[0], head_scr[1], t, cam.z, S['glyph'])
    if S['speed'] > 0.02:
        draw_speed(md, W / 2, H * 0.45, S['speed'], f)
    if S['rings']:      # shockwaves emerge from BEHIND him
        ccx, ccy = (head_scr if mode == 'bust' else cam.p((0, 330 if mode == 'full' else 150)))
        draw_rings(md, ccx, ccy, t, S['rings'], S['ring_scale'])
    paste(ml)

    # --- figure
    if items is not None:
        fl = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        draw_items(fl, items, cam, S['draw_p'])
        paste(fl)

    # --- front fx
    fl2 = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fl2)
    front_img = Image.new('RGB', (HW, HH), (0, 0, 0))
    gd = ImageDraw.Draw(front_img)
    front = np.zeros((HH, HW, 3), np.float32)
    if P['glow'] > 0.02 and 'eyeL' in anchors and P['eye_open'] > 0.3:
        for key in ('eyeL', 'eyeR'):
            ex, ey = cam.p(anchors[key])
            front += radial(ex, ey, 30 * cam.z * K, (236, 170, 255), 0.75 * P['glow'])
            if P['ue'] > 0.5:   # lens flare streak
                fd.line((ex - 140 * cam.z * K, ey, ex + 140 * cam.z * K, ey), fill=(255, 230, 255, 190),
                        width=max(1, int(2 * K)))
    if S['ash'] > 0:
        draw_particles(fd, t, S['ash'], 'ash')
    if S['embers'] > 0:
        draw_particles(fd, t, S['embers'], 'embers')
    if S['lightning'] > 0.02:
        draw_lightning(fd, gd, S['lightning'], head_scr[0], head_scr[1], 380 * cam.z * K + 160 * K, f)
    if S['hitfx'] and mode == 'bust':
        draw_hit_fx(fd, cam, t)
    paste(fl2)

    # --- text
    tl = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    tgd = ImageDraw.Draw(front_img)
    draw_texts(tl, t, f, front_img)

    # --- combine glows (screen)
    fb = np.asarray(front_img, np.float32) + front
    fb = Image.fromarray(np.clip(fb, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(5))
    img = ImageChops.screen(img, fb.resize((W, H), Image.BILINEAR))
    img.paste(tl, (0, 0), tl)

    # --- post: vignette, grain, flash, fade
    arr = np.asarray(img, np.float32) * VIG + GRAIN[(f // 2) % 3]
    if S['flash'] > 0.003:
        arr = arr + (255 - arr) * min(1.0, S['flash'])
    if S['fade'] > 0.003:
        arr = arr * (1 - min(1.0, S['fade']))
    return np.clip(arr, 0, 255).astype(np.uint8)


def _frame_bytes(f):
    return render_frame(f).tobytes()


def main():
    cmd = sys.argv[1]
    here = os.path.dirname(os.path.abspath(__file__))
    if cmd == 'preview':
        os.makedirs(os.path.join(here, 'previews'), exist_ok=True)
        for tt in sys.argv[2:]:
            Image.fromarray(render_frame(int(float(tt) * FPS))).save(os.path.join(here, 'previews', f'p_{tt}.png'))
    elif cmd == 'sheet':
        out = os.environ.get('SHEET_OUT', os.path.join(here, 'previews', 'sheet.png'))
        os.makedirs(os.path.dirname(out), exist_ok=True)
        times = [float(x) for x in sys.argv[2:]]
        cols = 3
        rows = (len(times) + cols - 1) // cols
        tw, th = 640, 360
        sheet = Image.new('RGB', (cols * tw, rows * th), (0, 0, 0))
        for i, tt in enumerate(times):
            fr = Image.fromarray(render_frame(int(tt * FPS))).resize((tw, th), Image.LANCZOS)
            sheet.paste(fr, ((i % cols) * tw, (i // cols) * th))
        sheet.save(out)
    elif cmd == 'render':
        out = sys.argv[2]
        ff = subprocess.Popen(
            ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
             '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'slow', '-crf', '15',
             '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
        with Pool(4) as pool:
            for i, b in enumerate(pool.imap(_frame_bytes, range(NFRAMES), chunksize=2)):
                ff.stdin.write(b)
                if i % 48 == 0:
                    print(f'frame {i}/{NFRAMES}', flush=True)
        ff.stdin.close()
        ff.wait()


if __name__ == '__main__':
    main()
