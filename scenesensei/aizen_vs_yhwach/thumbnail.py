"""Thumbnail: 'HE BLINDED A GOD' + cracked all-seeing eye (The Almighty vs Kyoka Suigetsu)."""
import sys, os, math, numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
A, OUT = sys.argv[1], sys.argv[2]; W, H = 1280, 720; rng = np.random.default_rng(3)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
t = np.clip(xx / W * 1.3 - .2, 0, 1)[..., None]
img = np.array([40, 10, 70]) * (1 - t) + np.array([90, 5, 10]) * t
d = np.sqrt(((xx - 930) / 500) ** 2 + ((yy - 360) / 400) ** 2)[..., None]
img = img * np.clip(1.3 - d * .8, .25, 1.3) + rng.normal(0, 5, (H, W, 1))
im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert("RGBA")
# eye
eye = Image.new("RGBA", (W, H)); de = ImageDraw.Draw(eye); cx, cy = 940, 360
pts = [(cx + 330 * math.cos(a), cy + 170 * math.sin(a) * abs(math.sin(a)) ** .3) for a in np.linspace(0, 2 * math.pi, 120)]
de.polygon(pts, fill=(245, 230, 225, 255))
for r, c in ((150, (120, 0, 0)), (130, (220, 30, 30)), (95, (255, 90, 40)), (48, (10, 0, 0))):
    de.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c + (255,))
for dx in (-70, 70): de.ellipse([cx + dx - 16, cy - 16, cx + dx + 16, cy + 16], fill=(10, 0, 0, 255))  # extra pupils
mask = Image.new("L", (W, H)); ImageDraw.Draw(mask).polygon(pts, fill=255)
eye.putalpha(mask)
glow = Image.new("RGBA", (W, H), (255, 40, 30, 0)); glow.putalpha(mask.filter(ImageFilter.GaussianBlur(40)))
im.alpha_composite(glow); im.alpha_composite(glow); im.alpha_composite(eye)
# purple cracks (Kyoka Suigetsu shattering the vision)
dc = ImageDraw.Draw(im)
for k in range(9):
    a = rng.uniform(0, 2 * math.pi); x, y = cx + rng.normal(0, 30), cy + rng.normal(0, 20); p = [(x, y)]
    for _ in range(6):
        a += rng.normal(0, .5); step = rng.uniform(30, 70); x += step * math.cos(a); y += step * math.sin(a); p.append((x, y))
    dc.line(p, fill=(200, 150, 255, 255), width=7); dc.line(p, fill=(255, 255, 255, 255), width=2)
# text
F = lambda s: ImageFont.truetype(os.path.join(A, "Anton.ttf"), s)
tl = Image.new("RGBA", (W, H)); dt = ImageDraw.Draw(tl)
dt.text((50, 70), "HE BLINDED", font=F(150), fill=(255, 255, 255, 255), stroke_width=8, stroke_fill=(0, 0, 0, 255))
dt.text((50, 260), "A GOD", font=F(270), fill=(205, 160, 255, 255), stroke_width=10, stroke_fill=(0, 0, 0, 255))
dt.text((56, 590), "AIZEN vs YHWACH", font=F(70), fill=(255, 220, 90, 255), stroke_width=6, stroke_fill=(0, 0, 0, 255))
sh = tl.filter(ImageFilter.GaussianBlur(12)); im.alpha_composite(Image.eval(sh, lambda v: v)); im.alpha_composite(tl)
im.convert("RGB").save(os.path.join(OUT, "thumbnail.jpg"), quality=92)
