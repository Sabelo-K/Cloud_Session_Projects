"""Synthesise original SFX and a lo-fi music bed for Money Mechanics.

Everything is generated from scratch (sine waves and noise), so there are no samples,
no licences and no Content ID claims.
Usage: python synth_audio.py OUT_DIR MUSIC_SECONDS
"""
import sys
import wave

import numpy as np

SR = 44100
out = sys.argv[1]
music_len = float(sys.argv[2])
rng = np.random.default_rng(7)


def t(d):
    return np.arange(int(SR * d)) / SR


def env(n, a=0.005, r=0.2):
    e = np.ones(n)
    na = max(1, int(a * SR))
    e[:na] = np.linspace(0, 1, na)
    nr = min(n, int(r * SR))
    e[-nr:] *= np.exp(-np.linspace(0, 6, nr))
    return e


def expdec(d, k):
    return np.exp(-k * t(d))


def norm(x, peak=0.9):
    return x / (np.max(np.abs(x)) + 1e-9) * peak


def lp(x, a=0.15):
    """Cheap low-pass: moving average whose width grows as `a` shrinks."""
    w = max(1, int(1 / a))
    return np.convolve(x, np.ones(w) / w, mode="same")


def save(name, x):
    x = np.clip(x, -1, 1)
    stereo = x.ndim == 2
    data = (x * 32767).astype(np.int16)
    with wave.open(f"{out}/{name}.wav", "wb") as w:
        w.setnchannels(2 if stereo else 1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.reshape(-1).tobytes())


def tone(f, d, k=6, harm=(1,), amps=(1,)):
    tt = t(d)
    return sum(a * np.sin(2 * np.pi * f * h * tt) for h, a in zip(harm, amps)) * expdec(d, k)


def sweep(f0, f1, d):
    return np.sin(2 * np.pi * np.cumsum(np.linspace(f0, f1, int(SR * d))) / SR)


def noise(d):
    return rng.standard_normal(int(SR * d))


def mix(*parts):
    n = max(int(off * SR) + len(p) for p, off in parts)
    y = np.zeros(n)
    for p, off in parts:
        o = int(off * SR)
        y[o : o + len(p)] += p
    return y


def bell(f, d=0.9):
    return tone(f, d, 5, (1, 2.76, 5.4), (1, 0.5, 0.25))


# --- SFX ---------------------------------------------------------------
save("chaching", norm(mix((norm(noise(0.08)) * expdec(0.08, 60) * 0.6, 0), (bell(1568), 0.06), (bell(2093), 0.16))))
save("coin", norm(mix((bell(2637, 0.5) * 0.8, 0), (bell(3136, 0.4) * 0.5, 0.05), (bell(2637, 0.3) * 0.3, 0.14))))
save("pop", norm(sweep(900, 300, 0.09) * expdec(0.09, 40)) * 0.7)
save("whoosh", norm(lp(noise(0.45), 0.25) * np.sin(np.pi * t(0.45) / 0.45) ** 2) * 0.6)
save("stamp", norm(mix((tone(70, 0.35, 14), 0), (lp(noise(0.12), 0.3) * expdec(0.12, 40), 0))))
sc = t(0.5)
save("scratch", norm(np.sin(2 * np.pi * np.cumsum(300 + 900 * np.sin(2 * np.pi * 6 * sc)) / SR) * expdec(0.5, 3)) * 0.7)
save("ding", norm(bell(1760, 1.2)) * 0.7)
save("tick", norm(mix((tone(1200, 0.06, 60), 0), (lp(noise(0.03), 0.6) * 0.3, 0))) * 0.6)
save("beep", norm(np.sin(2 * np.pi * 1950 * t(0.18)) * env(int(SR * 0.18), 0.002, 0.03)) * 0.5)
save("buzzer", norm(np.sign(np.sin(2 * np.pi * 110 * t(0.35))) * env(int(SR * 0.35), 0.005, 0.08)) * 0.35)
save("slap", norm(lp(noise(0.15), 0.5) * expdec(0.15, 35)))
save("bloop", norm(sweep(520, 180, 0.4) * expdec(0.4, 7)) * 0.7)
save("rise", norm(sweep(220, 880, 1.2) * np.linspace(0, 1, int(SR * 1.2)) ** 1.5) * 0.45)
save("flip", norm(np.concatenate([lp(noise(0.05), 0.6) * expdec(0.05, 50), np.zeros(int(SR * 0.05)), lp(noise(0.05), 0.6) * expdec(0.05, 50)])) * 0.7)
save("gasp", norm(lp(noise(0.5), 0.08) * np.sin(np.pi * t(0.5) / 0.5)) * 0.4)
rw = t(0.9)
save("rewind", norm(np.sin(2 * np.pi * np.cumsum(np.linspace(1200, 300, len(rw)) * (1 + 0.3 * np.sign(np.sin(2 * np.pi * 14 * rw)))) / SR) * expdec(0.9, 1.5)) * 0.4)
hm = t(2.5)
save("hum", norm((np.sin(2 * np.pi * 55 * hm) + 0.5 * np.sin(2 * np.pi * 82.4 * hm)) * np.sin(np.pi * hm / 2.5)) * 0.5)
nb = t(1.0)
save("neon", norm((np.sin(2 * np.pi * 120 * nb) + 0.4 * np.sign(np.sin(2 * np.pi * 240 * nb))) * (rng.random(len(nb)) > 0.02)) * 0.25)
wh = t(1.6)
save("whirr", norm(np.sin(2 * np.pi * (90 + 10 * np.sin(2 * np.pi * 3 * wh)) * wh) * (0.6 + 0.4 * np.sign(np.sin(2 * np.pi * 12 * wh))) * np.sin(np.pi * wh / 1.6)) * 0.3)
sp = t(1.0)
save("sputter", norm(lp(noise(1.0), 0.2) * (np.sin(2 * np.pi * 9 * sp) > 0) * expdec(1.0, 1.5)) * 0.7)
save("plink", norm(bell(2349, 0.25)) * 0.35)
clk = np.zeros(int(SR * 3.2))
for i in range(7):
    o = int(i * 0.5 * SR)
    c = tone(2200 if i % 2 else 1800, 0.04, 80)
    clk[o : o + len(c)] += c
save("clock", norm(clk) * 0.5)
save("sting", norm(mix(*[(bell(f, 0.8) * 0.8, i * 0.09) for i, f in enumerate([523, 659, 784, 1047])])) * 0.8)
save("sting_dark", norm(mix(*[(tone(f, 1.2, 3, (1, 2), (1, 0.3)), i * 0.12) for i, f in enumerate([220, 261.6, 311.1])])) * 0.7)

# --- Music: lo-fi loop, 84 bpm, Fmaj7 / Em7 / Dm7 / Cmaj7 ----------------
bpm = 84
beat = 60 / bpm
bar = 4 * beat
chords = [[174.6, 220, 261.6, 329.6], [164.8, 196, 246.9, 293.7], [146.8, 174.6, 220, 261.6], [130.8, 164.8, 196, 246.9]]
n = int(SR * music_len)
L = np.zeros(n)
Rr = np.zeros(n)


def add(buf, x, at):
    o = int(at * SR)
    if o >= n:
        return
    seg = x[: n - o]
    buf[o : o + len(seg)] += seg


def keys(f, d):
    tt = t(d)
    x = np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(2 * np.pi * 2 * f * tt) + 0.1 * np.sin(2 * np.pi * 3 * f * tt)
    return x * (1 + 0.15 * np.sin(2 * np.pi * 5 * tt)) * env(len(tt), 0.02, d * 0.6)


kick = tone(55, 0.35, 12, (1, 2), (1, 0.2)) * 1.4
hat = lp(noise(0.05), 0.9) * expdec(0.05, 90) * 0.25
snare = lp(noise(0.18), 0.5) * expdec(0.18, 22) * 0.45
chord_cache = {}
for b in range(int(music_len / bar) + 1):
    ci = b % 4
    c = chords[ci]
    t0 = b * bar
    for i, f in enumerate(c):
        key = (ci, i)
        if key not in chord_cache:
            chord_cache[key] = keys(f, bar * 0.98) * 0.18
        x = chord_cache[key]
        add(L, x * (1 - i * 0.1), t0 + i * 0.015)
        add(Rr, x * (0.7 + i * 0.1), t0 + i * 0.015)
    bass = tone(c[0] / 2, bar * 0.9, 1.2, (1, 2), (1, 0.25)) * 0.5
    add(L, bass, t0)
    add(Rr, bass, t0)
    for q in range(4):
        hit = kick if q in (0, 2) else snare
        add(L, hit, t0 + q * beat)
        add(Rr, hit, t0 + q * beat)
    for e in range(8):
        sw = 0.06 * beat if e % 2 else 0
        add(L, hat * (1 if e % 2 else 0.6), t0 + e * beat / 2 + sw)
        add(Rr, hat * (0.6 if e % 2 else 1), t0 + e * beat / 2 + sw)
crackle = (rng.random(n) > 0.9993) * rng.standard_normal(n) * 0.15
L = lp(L + crackle, 0.35)
Rr = lp(Rr + crackle, 0.35)
fade = int(SR * 2)
for ch in (L, Rr):
    ch[:fade] *= np.linspace(0, 1, fade)
    ch[-fade:] *= np.linspace(1, 0, fade)
pk = max(np.abs(L).max(), np.abs(Rr).max()) / 0.8
save("music_lofi", np.stack([L / pk, Rr / pk], axis=1))
print("ok")
