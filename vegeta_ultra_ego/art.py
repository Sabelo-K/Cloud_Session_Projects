"""Geometry for the motion sketch: Vegeta, the fist, cracks and the ruined city.

Everything is in a 'design space' of 1280x720-ish units; render.py maps it to
pixels.  Character reference (from fan-wiki/news summaries, see README):
  base      black upward flame hair with widow's peak, thick angry brows
  Ultra Ego purple wilder hair, bright purple eyes with pronounced pupils,
            NO eyebrows (swollen brow ridge), sharp cheekbones, ripped physique,
            armor shed, purple flame-like aura (Beerus-style), crazed grin.
"""
import math
import random

CH = (232, 229, 222)        # chalk line
CHD = (150, 146, 155)       # dim chalk
SKIN = (38, 33, 49)
SKIN_UE = (44, 30, 66)
HAIR_BASE = (13, 11, 22)
HAIR_UE = (62, 18, 118)
ARMF = (30, 28, 42)
GLOVE = (176, 172, 186)
BLOOD = (178, 24, 38)
PURP = (170, 70, 255)
LAV = (228, 196, 255)
EYE_UE = (196, 112, 255)


def lerp(a, b, u):
    return a + (b - a) * u


def lc(c1, c2, u):
    u = max(0.0, min(1.0, u))
    return tuple(int(lerp(a, b, u)) for a, b in zip(c1, c2))


def mirror(pts):
    return [(-x, y) for x, y in reversed(pts)]


def chaikin(pts, n=2):
    """Round off a closed polygon (organic limbs instead of ruler-straight edges)."""
    for _ in range(n):
        new = []
        m = len(pts)
        for i in range(m):
            a, b = pts[i], pts[(i + 1) % m]
            new.append((0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]))
            new.append((0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1]))
        pts = new
    return pts


HAIR_L = [(-108, -58), (-132, -112), (-116, -142), (-132, -214), (-94, -188),
          (-104, -292), (-62, -232), (-56, -346), (-22, -268)]
HAIR_TOP = (0, -405)
HAIR_L_W = [(-108, -58), (-150, -80), (-132, -112), (-170, -150), (-122, -148),
            (-144, -232), (-98, -196), (-122, -320), (-64, -240), (-74, -376),
            (-24, -280)]
HAIR_TOP_W = (0, -432)
HAIRLINE = [(95, -100), (45, -86), (0, -62), (-45, -86), (-95, -100)]
FACE = [(-106, -62), (-102, 18), (-74, 100), (-32, 138), (0, 150), (32, 138),
        (74, 100), (102, 18), (106, -62)] + HAIRLINE


def tongue(bx, by, w, h, sway, ph, n=14):
    """A flame tongue polygon rising from (bx, by)."""
    left, right = [], []
    for i in range(n + 1):
        u = i / n
        off = sway * (u ** 2) * h * 0.25 * math.sin(ph + u * 2)
        half = w / 2 * (1 - u) ** 1.3
        left.append((bx - half + off, by - h * u))
        right.append((bx + half + off, by - h * u))
    return left + right[::-1]


def build_vegeta(P, t):
    """Return (items, anchors) in local coordinates."""
    tilt = P.get('tilt', 0.0)
    drop = P.get('drop', 0.0)
    eo = P.get('eye_open', 1.0)
    glow = P.get('glow', 0.0)
    grin = P.get('grin', 0.0)
    bat = P.get('battered', 0.0)
    hu = P.get('hair_up', 0.0)
    bf = P.get('furrow', 0.5)
    ue = P.get('ue', 0.0)
    hpur = P.get('hp', 0.0)
    armor = P.get('armor', 1.0)
    sway = P.get('sway', 0.0)
    splay = P.get('splay', 0.0)
    full = P.get('full', False)
    sq = P.get('squint', 0.0)

    lcol = lc(CH, LAV, ue)
    items = []
    nid = [0]

    def add(kind, pts, fill=None, col=None, w=3, closed=True, **kw):
        nid[0] += 1
        d = dict(kind=kind, pts=pts, fill=fill, col=col or lcol, w=w,
                 closed=closed, id=nid[0])
        d.update(kw)
        items.append(d)

    ct, st = math.cos(tilt), math.sin(tilt)

    def hp(pt):
        x, y = pt[0], pt[1] - 175
        return (x * ct - y * st, x * st + y * ct + 175 + drop)

    def HP(pts):
        return [hp(p) for p in pts]

    skin = lc(SKIN, SKIN_UE, ue)
    armf = ARMF

    # ---------------------------------------------------------------- body
    if full:
        sp = 1 + 0.30 * splay
        # legs
        legL = [(-108, 520), (-6, 520), (-12, 610), (-20, 700), (-24, 770), (-22, 850), (-34, 882),
                (-120, 882), (-118, 820), (-124, 760), (-130, 680), (-124, 600)]
        add('poly', chaikin(legL), fill=armf, col=lcol, w=3)
        add('poly', chaikin(mirror(legL)), fill=armf, col=lcol, w=3)
        add('line', [(-60, 700), (-70, 740), (-66, 770)], col=lcol, w=2, closed=False)   # knee
        add('line', [(60, 700), (70, 740), (66, 770)], col=lcol, w=2, closed=False)
        bootL = [(-140, 840), (-22, 840), (-12, 896), (-152, 908)]
        add('poly', bootL, fill=(24, 22, 34), col=lcol, w=3)
        add('poly', mirror(bootL), fill=(24, 22, 34), col=lcol, w=3)
        add('line', [(-140, 858), (-22, 858)], col=GLOVE, w=3, closed=False)             # white boot trim
        add('line', [(22, 858), (140, 858)], col=GLOVE, w=3, closed=False)
        # arms: shoulder -> bicep -> elbow -> forearm -> wrist (flare outward when splay)
        armL = [(-150, 240), (-205, 258), (-232, 335), (-234, 385), (-222, 445), (-216, 478), (-224, 530),
                (-216, 596), (-178, 604), (-142, 590), (-144, 520), (-148, 462), (-152, 402), (-150, 334),
                (-140, 296)]
        armL = [(x * sp, y) for x, y in armL]
        afill = skin if armor < 1 else armf
        add('poly', chaikin(armL), fill=afill, col=lcol, w=3)
        add('poly', chaikin(mirror(armL)), fill=afill, col=lcol, w=3)
        add('line', [(-206 * sp, 340), (-214 * sp, 392), (-206 * sp, 430)], col=lcol, w=2, closed=False)  # bicep
        add('line', [(206 * sp, 340), (214 * sp, 392), (206 * sp, 430)], col=lcol, w=2, closed=False)
        fistL = [(-226 * sp, 590), (-150 * sp, 590), (-144 * sp, 632), (-158 * sp, 656), (-214 * sp, 656),
                 (-230 * sp, 630)]
        add('poly', chaikin(fistL, 1), fill=GLOVE, col=lcol, w=3)
        add('poly', chaikin(mirror(fistL), 1), fill=GLOVE, col=lcol, w=3)
        add('poly', chaikin([(-152, 240), (-146, 400), (-106, 520), (106, 520), (146, 400), (152, 240)]),
            fill=skin if armor < 1 else armf, col=lcol, w=3)
        if armor < 1:
            for k in range(3):                       # ab lines
                y = 400 + 36 * k
                add('line', [(-34, y), (34, y)], col=lcol, w=2, closed=False)
            add('line', [(0, 330), (0, 500)], col=lcol, w=2, closed=False)
    else:
        add('poly', [(-150, 240), (-60, 258), (60, 258), (150, 240), (172, 600), (-172, 600)],
            fill=skin if armor < 1 else armf, col=lcol, w=3)

    # armor / bare torso
    padL = [(-140, 238), (-232, 214), (-292, 250), (-304, 324), (-214, 342), (-152, 300)]
    if armor >= 0.5:
        add('poly', padL, fill=armf, col=lcol, w=4)
        if armor >= 1:
            add('poly', mirror(padL), fill=armf, col=lcol, w=4)
            add('poly', [(-140, 250), (0, 288), (140, 250), (122, 430), (0, 452), (-122, 430)],
                fill=(34, 32, 46), col=lcol, w=3)
        else:
            add('line', [(-232, 214), (-250, 262), (-228, 290), (-250, 330)], col=lcol, w=3, closed=False)
            add('line', [(-150, 300), (-110, 330), (-70, 322), (-40, 368)], col=lcol, w=3, closed=False)
    if armor < 1:
        # ripped physique: traps, collarbones, pecs
        add('line', [(-50, 232), (-130, 262), (-196, 304)], col=lcol, w=3, closed=False)
        add('line', [(50, 232), (130, 262), (196, 304)], col=lcol, w=3, closed=False)
        add('line', [(-34, 262), (-112, 272)], col=lcol, w=2, closed=False)
        add('line', [(34, 262), (112, 272)], col=lcol, w=2, closed=False)
        add('line', [(-150, 336), (-92, 360), (-20, 342)], col=lcol, w=3, closed=False)
        add('line', [(150, 336), (92, 360), (20, 342)], col=lcol, w=3, closed=False)
        add('line', [(0, 268), (0, 420)], col=lcol, w=2, closed=False)
        add('hatch', [(-150, 300), (-20, 330), (-20, 560), (-170, 560)], angle=-0.9, spacing=11, col=CHD)

    # neck
    add('poly', [(-46, 110), (-54, 250), (54, 250), (46, 110)], fill=skin, col=lcol, w=3)
    add('hatch', [(-48, 120), (48, 120), (54, 250), (-54, 250)], angle=0.6, spacing=9, col=CHD)

    # ---------------------------------------------------------------- hair
    wild = hu >= 0.5
    hl, ht = (HAIR_L_W, HAIR_TOP_W) if wild else (HAIR_L, HAIR_TOP)

    def hair_pt(pt):
        x, y = pt
        if y < -90:
            kk = (-90 - y)
            y = -90 - kk * (1 + 0.30 * hu)
            x = x * 1.12 * (1 + 0.10 * hu) + sway * ((kk / 320.0) ** 2) * math.sin(t * 9 + x * 0.04) * 18
        return (x, y)

    hair = hl + [ht] + mirror(hl)
    hair = [hair_pt(p) for p in hair] + [(95, -100), (45, -86), (0, -62), (-45, -86), (-95, -100)]
    hcol = lc(HAIR_BASE, HAIR_UE, hpur)
    add('poly', HP(hair), fill=hcol, col=lcol, w=4)
    for xs in (-60, 0, 60):                                   # flow lines in the hair
        tipy = -330 - 40 * hu
        add('line', HP([hair_pt((xs * 0.8, -96)), hair_pt((xs * 1.1, -200)), hair_pt((xs * 0.6, tipy))]),
            col=lc(CHD, LAV, hpur), w=2, closed=False)

    # ---------------------------------------------------------------- face
    wid = 1 + 0.07 * ue
    face = [(x * (wid if 0 < y < 110 else 1), y) for x, y in FACE]
    add('poly', HP(face), fill=skin, col=lcol, w=4)
    add('hatch', HP([(-104, -30), (-60, -10), (-40, 60), (-30, 138), (-74, 100), (-100, 18)]),
        angle=0.95, spacing=9, col=CHD)
    add('hatch', HP([(-95, -100), (-45, -86), (0, -62), (45, -86), (95, -100), (95, -58), (0, -40), (-95, -58)]),
        angle=0.35, spacing=8, col=CHD)
    if ue > 0.3:                                             # hollow, sharp cheekbones
        add('hatch', HP([(-100, 20), (-56, 44), (-44, 92), (-74, 100)]), angle=-0.9, spacing=7, col=lcol)
        add('hatch', HP([(100, 20), (56, 44), (44, 92), (74, 100)]), angle=0.9, spacing=7, col=lcol)
        add('line', HP([(-98, 14), (-62, 40), (-46, 84)]), col=lcol, w=3, closed=False)
        add('line', HP([(98, 14), (62, 40), (46, 84)]), col=lcol, w=3, closed=False)
    else:
        add('line', HP([(-70, 40), (-58, 74)]), col=lcol, w=2, closed=False)
        add('line', HP([(70, 40), (58, 74)]), col=lcol, w=2, closed=False)

    # eyes (+ brows or brow ridge)
    eye_open = max(0.0, eo * (1.0 - 0.55 * sq))
    for sign in (1, -1):
        pts = [(-86, -12), (-54, -28 - 2 * ue), (-18, -8), (-50, 0)]
        mid = -12
        epts = [(sign * x, mid + (y - mid) * eye_open) for x, y in pts]
        if eye_open < 0.15:
            add('line', HP([(sign * -86, -12), (sign * -50, -7), (sign * -18, -7)]), col=lcol, w=3, closed=False)
        else:
            ef = lc((236, 232, 226), EYE_UE, max(ue, glow * 0.9))
            add('poly', HP(epts), fill=ef, col=lcol, w=3)
            if eye_open > 0.5:
                pcol = (28, 0, 56) if ue > 0.4 or glow > 0.5 else (14, 12, 20)
                prad = 8 if ue < 0.4 else 11
                cxp, cyp = sign * -48, -14
                circ = [(cxp + prad * math.cos(a * math.pi / 4), cyp + prad * math.sin(a * math.pi / 4))
                        for a in range(8)]
                add('poly', HP(circ), fill=pcol, col=pcol, w=1)
        if ue < 0.5:
            iy = -18 + 9 * bf
            add('line', HP([(sign * -94, -38), (sign * -54, -48 + 4 * bf), (sign * -10, iy)]),
                col=lcol, w=9 * (1 - ue) + 3, closed=False)
        else:   # no eyebrows: a swollen brow ridge instead
            add('poly', HP([(sign * -100, -30), (sign * -56, -48), (sign * -8, -24), (sign * -10, -8),
                            (sign * -56, -34), (sign * -98, -16)]), fill=lc(skin, (22, 12, 40), 0.7), col=lcol, w=2)
            add('hatch', HP([(sign * -100, -30), (sign * -56, -48), (sign * -8, -24), (sign * -10, -8),
                             (sign * -56, -34), (sign * -98, -16)]), angle=0.2, spacing=5, col=lcol)

    # nose
    add('line', HP([(-3, 8), (-10, 50), (6, 56)]), col=lcol, w=3, closed=False)

    # mouth: smirk -> wide grin
    if grin < 0.05:
        add('line', HP([(-36, 96), (-8, 100), (24, 96), (48, 78), (54, 72)]), col=lcol, w=3, closed=False)
    else:
        gy = 14 * grin
        up = [(-56, 82), (-28, 90), (0, 93), (28, 90), (56, 82)]
        lo = [(56, 82), (44, 100 + gy), (0, 112 + gy * 1.6), (-44, 100 + gy), (-56, 82)]
        add('poly', HP(up + lo[1:-1]), fill=(236, 232, 226), col=lcol, w=3)
        for xt in (-34, -17, 0, 17, 34):
            add('line', HP([(xt, 91), (xt, 100 + gy * 0.8)]), col=(90, 84, 96), w=1, closed=False)
        add('line', HP([(-60, 76), (-56, 82)]), col=lcol, w=3, closed=False)
        add('line', HP([(60, 76), (56, 82)]), col=lcol, w=3, closed=False)

    # damage
    if bat > 0.2:
        add('line', HP([(-88, 8), (-62, 30)]), col=lcol, w=2, closed=False)
        add('line', HP([(-84, 22), (-60, 40)]), col=lcol, w=2, closed=False)
        add('line', HP([(30, -50), (54, -28)]), col=lcol, w=2, closed=False)
        blood = [(-72, -88), (-64, -88), (-62, -22 * bat), (-58, 30 * bat), (-62, 64 * bat),
                 (-68, 30 * bat), (-70, -20 * bat)]
        add('poly', HP(blood), fill=BLOOD, col=BLOOD, w=2)
        add('poly', HP([(48, 70), (54, 70), (52, 110), (47, 100)]), fill=BLOOD, col=BLOOD, w=2)

    anchors = dict(eyeL=hp((-50, -14)), eyeR=hp((50, -14)), mouth=hp((0, 100)),
                   head=hp((0, 20)), chest=(0, 330), feet=(0, 905), hair=hp((0, -300)))
    return items, anchors


def build_fist(P, t):
    ue = P.get('ue', 0.0)
    lcol = lc(CH, LAV, ue)
    items = []
    nid = [100]

    def add(kind, pts, fill=None, col=None, w=3, closed=True, **kw):
        nid[0] += 1
        d = dict(kind=kind, pts=pts, fill=fill, col=col or lcol, w=w, closed=closed, id=nid[0])
        d.update(kw)
        items.append(d)

    skin = lc((62, 52, 74), (70, 48, 100), ue)
    # forearm with tendons, then the white glove cuff
    add('poly', chaikin([(-82, 230), (82, 230), (96, 400), (88, 570), (-88, 570), (-96, 400)]),
        fill=skin, w=3)
    for dx in (-40, 4, 46):
        add('line', [(dx, 270), (dx + 8, 350), (dx - 6, 440), (dx + 4, 540)], col=lcol, w=2, closed=False)
    add('poly', chaikin([(-104, 206), (104, 206), (110, 268), (-110, 268)], 1), fill=(160, 156, 172), w=3)
    add('line', [(-106, 226), (106, 226)], col=(96, 90, 112), w=2, closed=False)
    add('line', [(-108, 248), (108, 248)], col=(96, 90, 112), w=2, closed=False)
    # clenched hand: back of hand, four curled fingers, thumb wrapped across
    add('poly', chaikin([(-130, -20), (130, -20), (142, 100), (104, 208), (-104, 208), (-142, 100)]),
        fill=(150, 146, 162), w=3)
    for i in range(4):
        x0 = -130 + 65 * i
        x1 = x0 + 62
        add('poly', chaikin([(x0, -8), (x0 - 2, -82), (x0 + 8, -108), (x1 - 8, -108), (x1 + 2, -82), (x1, -8)]),
            fill=(176, 172, 188), w=3)
        add('line', [(x0 + 6, -64), ((x0 + x1) / 2, -56), (x1 - 6, -64)], col=(96, 90, 112), w=2, closed=False)
        add('line', [(x0 + 6, -26), ((x0 + x1) / 2, -18), (x1 - 6, -26)], col=(96, 90, 112), w=2, closed=False)
        add('line', [(x0 + 16, -98), (x1 - 16, -98)], col=(246, 244, 250), w=3, closed=False)   # knuckle shine
    add('poly', chaikin([(-134, 92), (60, 62), (96, 106), (62, 152), (-112, 172)]), fill=(190, 186, 202), w=3)
    add('hatch', [(-142, 100), (-30, 100), (-30, 208), (-104, 208)], angle=0.8, spacing=8, col=(104, 98, 120))
    add('hatch', [(40, 110), (140, 100), (104, 208), (40, 208)], angle=-0.8, spacing=8, col=(104, 98, 120))
    return items, {}


def make_cracks(seed, n=16):
    rng = random.Random(seed)
    cracks = []
    for i in range(n):
        ang = 2 * math.pi * i / n + rng.uniform(-0.15, 0.15)
        L = rng.uniform(380, 760)
        x = y = 0.0
        a = ang
        pts = [(0.0, 0.0)]
        for _ in range(14):
            a += rng.uniform(-0.35, 0.35)
            x += math.cos(a) * L / 14
            y += math.sin(a) * L / 14
            pts.append((x, y))
        cracks.append(pts)
        for _b in range(2):
            kk = rng.randint(3, 9)
            bx, by = pts[kk]
            ba = ang + rng.choice([-1, 1]) * rng.uniform(0.5, 0.9)
            bp = [(bx, by)]
            for _ in range(6):
                ba += rng.uniform(-0.4, 0.4)
                bx += math.cos(ba) * L / 20
                by += math.sin(ba) * L / 20
                bp.append((bx, by))
            cracks.append(bp)
    return cracks


def build_city(seed=7):
    """World-space ruined skyline: far layer, near layer, rubble, ground line."""
    rng = random.Random(seed)
    far, near, rubble = [], [], []
    x = -1900
    while x < 1900:
        w = rng.uniform(70, 150)
        h = rng.uniform(140, 420)
        n = rng.randint(3, 6)
        top = [(x, 905), (x, 905 - h)]
        for i in range(1, n + 1):
            top.append((x + w * i / n, 905 - h + rng.uniform(-60, 40)))
        top.append((x + w, 905))
        far.append(top)
        x += w + rng.uniform(-20, 60)
    for side in (-1, 1):
        x = 430
        while x < 1900:
            w = rng.uniform(110, 220)
            h = rng.uniform(300, 760)
            n = rng.randint(3, 7)
            xs0, xs1 = (side * x, side * (x + w))
            top = [(xs0, 905), (xs0, 905 - h)]
            for i in range(1, n + 1):
                top.append((xs0 + (xs1 - xs0) * i / n, 905 - h + rng.uniform(-90, 70)))
            top.append((xs1, 905))
            floors = [[(xs0, 905 - h * f), (xs1, 905 - h * f + rng.uniform(-14, 14))]
                      for f in (0.25, 0.45, 0.65) if h * f > 0]
            near.append((top, floors))
            x += w + rng.uniform(10, 90)
    for _ in range(26):
        cx = rng.uniform(-900, 900)
        r = rng.uniform(14, 56)
        rubble.append([(cx - r, 905), (cx - r * 0.5, 905 - r * 0.9), (cx + r * 0.3, 905 - r * 1.1),
                       (cx + r, 905)])
    return far, near, rubble
