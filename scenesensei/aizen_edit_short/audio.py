"""Audio for the Aizen phonk-edit Short: narration + synthesized phonk beat + SFX, all beat-synced.

Usage: python3 audio.py <assets_dir> <out_dir>   -> out_dir/audio.wav + out_dir/timeline.json
"""
import json, math, os, sys
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt, resample
from kokoro_onnx import Kokoro

A, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
SR, BPM = 24000, 140
BEAT = 60 / BPM; BAR = 4 * BEAT; EIGHTH = BEAT / 2
DROP = 6  # index of the line that lands on the drop ("Sosuke Aizen.")

# (spoken text, scene id)
LINES = [
    ("Yhwach could see every possible future.", "eye_open"),
    ("And he still got played by a man chained to a chair.", "chair_flash"),
    ("After absorbing the Soul King, nothing could touch him.", "eye_king"),
    ("Every attack. Every Bankai. Every plan. Erased before it happened.", "eye_slams"),
    ("So Kyoraku did the unthinkable.", "chains"),
    ("He unsealed the one prisoner Soul Society feared most.", "chair_reveal"),
    ("Sosuke Aizen.", "name"),
    ("His opening move? A full incantation Kurohitsugi.", "coffin"),
    ("Yhwach broke out. But that was never the point.", "coffin_break"),
    ("The Almighty sees the future.", "eye_calm"),
    ("But seeing is perception.", "water_moon"),
    ("And perception belongs to Kyoka Suigetsu.", "mirror_shatter"),
    ("The future Yhwach was reading? Aizen wrote it.", "eye_hypno"),
    ("And while a god stared at a lie, Ichigo cut straight through him.", "slash"),
    ("No reward. No pardon. Aizen went right back to his cell.", "chair_cell"),
    ("Since when were you under the impression he was ever on your side?", "final"),
]

# ---------- narration ----------
kok = Kokoro(os.path.join(A, "k.onnx"), os.path.join(A, "voices.bin"))
PITCH = 0.94  # resample -> slightly deeper, slower voice
def tts(text, speed):
    w, sr = kok.create(text, voice="am_onyx", speed=speed, lang="en-us")
    w = w.astype(np.float32)
    w = resample(w, int(len(w) / PITCH)).astype(np.float32)  # played at SR => pitch down
    nz = np.where(np.abs(w) > 0.01)[0]  # trim silence
    return w[max(0, nz[0] - 200): nz[-1] + 1200] if len(nz) else w

clips, t, timeline = [], 0.12, []
for i, (text, scene) in enumerate(LINES):
    speed = 0.92 if i in (DROP, len(LINES) - 1) else 1.07
    w = tts(text, speed); dur = len(w) / SR
    start = math.ceil(t / EIGHTH) * EIGHTH if i else t
    if i == DROP:  # land the name exactly on a bar line, with a breath of silence + riser before it
        start = math.ceil((t + 0.35) / BAR) * BAR
    clips.append((start, w))
    timeline.append({"i": i, "text": text, "scene": scene, "start": start, "end": start + dur})
    t = start + dur + (0.06 if i < DROP else 0.1)
VOICE_END = t
TOTAL = math.ceil((VOICE_END + 2.6) / BAR) * BAR  # room for the CTA, end on a bar
N = int(TOTAL * SR)
voice = np.zeros(N, np.float32)
for s, w in clips:
    a = int(s * SR); voice[a:a + len(w)] += w[: N - a]

def echo(sig, a, b, delay=0.23, fb=0.35, n=4):
    seg = sig[a:b].copy()
    for k in range(1, n + 1):
        d = int(delay * k * SR); g = fb ** k
        e = min(N, b + d)
        sig[a + d:e] += seg[: e - a - d] * g
for li in (DROP, len(LINES) - 1):  # echo tails on the name + the final line
    e = timeline[li]; echo(voice, int(e["start"] * SR), int(e["end"] * SR))

# ---------- instruments ----------
rng = np.random.default_rng(11)
def env_exp(n, k): return np.exp(-np.arange(n) / SR * k).astype(np.float32)
def bp(x, lo, hi): return sosfilt(butter(2, [lo, hi], "band", fs=SR, output="sos"), x).astype(np.float32)
def hp(x, f): return sosfilt(butter(2, f, "high", fs=SR, output="sos"), x).astype(np.float32)
def lp(x, f): return sosfilt(butter(2, f, "low", fs=SR, output="sos"), x).astype(np.float32)
def place(buf, x, at, g=1.0):
    a = int(at * SR)
    if a >= len(buf): return
    x = x[: len(buf) - a]; buf[a:a + len(x)] += x * g

def kick():
    n = int(0.35 * SR); tt = np.arange(n) / SR
    f = 48 + 110 * np.exp(-tt * 30)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * env_exp(n, 9) * 1.0).astype(np.float32)
def b808(freq, length):
    n = int(length * SR); tt = np.arange(n) / SR
    f = freq * (1 + 0.6 * np.exp(-tt * 40))  # pitch punch
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_exp(n, 1.6)
    return np.tanh(x * 2.2).astype(np.float32) * 0.6
def clap():
    n = int(0.22 * SR); x = rng.standard_normal(n).astype(np.float32)
    e = env_exp(n, 22); e[: int(.012 * SR)] *= 1.4
    return bp(x * e, 900, 3500) * 1.6
def hat(open_=False):
    n = int((0.18 if open_ else 0.05) * SR)
    return hp(rng.standard_normal(n).astype(np.float32) * env_exp(n, 18 if open_ else 70), 7000) * 0.5
def cowbell(freq):
    n = int(0.22 * SR); tt = np.arange(n) / SR
    x = np.sign(np.sin(2 * np.pi * freq * tt)) * .5 + np.sign(np.sin(2 * np.pi * freq * 1.48 * tt)) * .5
    return bp(x.astype(np.float32) * env_exp(n, 14), freq * .8, freq * 3.2) * 0.55
def boom(length=1.6):
    n = int(length * SR); tt = np.arange(n) / SR
    x = np.sin(2 * np.pi * np.cumsum(30 + 70 * np.exp(-tt * 6)) / SR) * env_exp(n, 2.2)
    x += lp(rng.standard_normal(n).astype(np.float32), 400) * env_exp(n, 8) * .6
    return np.tanh(x * 1.5).astype(np.float32)
def whoosh(length=0.45, up=True):
    n = int(length * SR); x = rng.standard_normal(n).astype(np.float32)
    out = np.zeros(n, np.float32); steps = 12
    for k in range(steps):  # stepped sweeping bandpass
        a, b = k * n // steps, (k + 1) * n // steps
        c = 300 * (18 ** ((k / steps) if up else (1 - k / steps)))
        out[a:b] = bp(x, c * .7, min(c * 1.6, SR / 2 - 100))[a:b]
    return out * np.hanning(n).astype(np.float32) * 1.3
def shatter():
    n = int(1.1 * SR); x = hp(rng.standard_normal(n).astype(np.float32), 3000) * env_exp(n, 7) * .8
    for _ in range(26):  # glass pings
        f = rng.uniform(2500, 7000); a = rng.integers(0, n // 2); m = int(.25 * SR)
        tt = np.arange(m) / SR
        x[a:a + m] += (np.sin(2 * np.pi * f * tt) * np.exp(-tt * rng.uniform(15, 40)) * .25).astype(np.float32)[: n - a]
    return x
def slash():
    n = int(0.5 * SR); x = rng.standard_normal(n).astype(np.float32)
    s = whoosh(0.18, up=True) * 1.2; out = np.zeros(n, np.float32); out[: len(s)] += s
    out += hp(x, 4000) * env_exp(n, 14) * .7
    return out
def heartbeat():
    k = kick() * .8; out = np.zeros(int(.6 * SR), np.float32)
    out[: len(k)] += k; out[int(.22 * SR): int(.22 * SR) + len(k)] += k * .7
    return lp(out, 180)
def riser(length):
    n = int(length * SR); tt = np.arange(n) / SR
    x = whoosh(length, up=True) * np.linspace(.2, 1.2, n).astype(np.float32)
    x += (np.sin(2 * np.pi * np.cumsum(200 + 1400 * (tt / length) ** 2) / SR) * .12 * (tt / length)).astype(np.float32)
    return x

music, sfx = np.zeros(N, np.float32), np.zeros(N, np.float32)
drop_t = timeline[DROP]["start"]
cell_t, final_t = timeline[14]["start"], timeline[15]["start"]
D, F, G, A_, Bb, C = 36.71, 43.65, 49.0, 55.0, 58.27, 65.41  # D minor 808 roots
prog = [D, D, Bb, A_]
cow_mel = [587, 0, 698, 587, 0, 523, 587, 0, 880, 0, 784, 698, 0, 659, 587, 0]  # 16th cowbell riff (D minor)
nbars = int(TOTAL / BAR)
for b in range(nbars):
    t0 = b * BAR; root = prog[b % 4]
    intro, outro_break = t0 < drop_t - 1e-6, cell_t - BAR < t0 < final_t - 0.01
    full = not intro and not outro_break
    if intro:
        # tense intro: sub drone, heartbeat, sparse cowbell
        n = int(BAR * SR); tt = np.arange(n) / SR
        place(music, (np.sin(2 * np.pi * root * 2 * tt) * .18 * np.minimum(1, tt * 4)).astype(np.float32), t0)
        place(music, heartbeat(), t0, .9)
        if b % 2: place(music, heartbeat(), t0 + 2 * BEAT, .7)
        for s16 in (0, 6, 10):
            if cow_mel[s16]: place(music, cowbell(cow_mel[s16]), t0 + s16 * BEAT / 4, .35)
    if full:
        place(music, b808(root, BAR * .55), t0, 1.0)
        place(music, b808(root, BAR * .4), t0 + 2.5 * BEAT, .9)
        for bt in range(4):
            place(music, kick(), t0 + bt * BEAT, .75 if bt in (0, 2) else .0)
            if bt in (1, 3): place(music, clap(), t0 + bt * BEAT, .8)
        place(music, kick(), t0 + 2.75 * BEAT, .55)
        for s16 in range(16):
            if cow_mel[s16]: place(music, cowbell(cow_mel[s16] * (1.12 if b % 4 == 3 else 1)), t0 + s16 * BEAT / 4, .55)
            if s16 % 2 == 0 or (b % 2 and s16 > 11): place(music, hat(), t0 + s16 * BEAT / 4, .6)
        place(music, hat(True), t0 + 3.5 * BEAT, .5)
    if outro_break and t0 >= cell_t - BAR:  # breakdown: filtered 808 + slow cowbell
        place(music, lp(b808(root, BAR * .9), 120), t0, .9)
        place(music, cowbell(587), t0, .25); place(music, cowbell(523), t0 + 2 * BEAT, .2)
    if t0 >= final_t - 0.01:  # final line: back in, heavy
        place(music, b808(D, BAR * .9), t0, 1.1); place(music, kick(), t0, .9)
        for bt in (1, 3): place(music, clap(), t0 + bt * BEAT, .8)
        for s16 in range(0, 16, 2): place(music, hat(), t0 + s16 * BEAT / 4, .5)
        for s16 in range(16):
            if cow_mel[s16]: place(music, cowbell(cow_mel[s16]), t0 + s16 * BEAT / 4, .5)

# riser into the drop + drop impact
place(sfx, riser(BAR), drop_t - BAR, .55); place(sfx, boom(2.2), drop_t, 1.1)
# scene SFX
for e in timeline:
    s, sc = e["start"], e["scene"]
    if sc in ("chair_flash", "chains", "coffin", "slash", "final", "eye_king"): place(sfx, boom(1.2), s, .6)
    if sc in ("eye_slams",):
        for k, frac in enumerate((0, .2, .4)): place(sfx, boom(.6), s + (e["end"] - s) * frac, .5)
    if sc in ("coffin_break", "mirror_shatter"): place(sfx, shatter(), s + .15, .9)
    if sc == "slash": place(sfx, slash(), s + (e["end"] - s) * .55, 1.1)
    if sc in ("chair_reveal", "eye_calm", "water_moon", "eye_hypno", "coffin"): place(sfx, whoosh(.4), max(0, s - .3), .55)
place(sfx, boom(2.0), VOICE_END + .1, .8)  # CTA hit

# ---------- mix: sidechain duck music under voice ----------
ve = np.abs(voice); k = int(.08 * SR)
ve = np.convolve(ve, np.ones(k) / k, mode="same")
duck = 1 - np.clip(ve * 5, 0, .55)
mix = voice * 1.0 + music * duck * .5 + sfx * .45
mix = np.tanh(mix * 1.1) * .92  # glue / soft limit
fade = int(.4 * SR); mix[-fade:] *= np.linspace(1, 0, fade)
sf.write(os.path.join(OUT, "audio.wav"), mix.astype(np.float32), SR)
json.dump({"total": TOTAL, "bpm": BPM, "drop": drop_t, "voice_end": VOICE_END, "lines": timeline},
          open(os.path.join(OUT, "timeline.json"), "w"), indent=1)
print("total", round(TOTAL, 2), "drop", round(drop_t, 2), "voice_end", round(VOICE_END, 2))
