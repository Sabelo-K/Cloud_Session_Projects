"""Original dramatic score for the Ultra Ego sketch, synthesized from scratch with numpy.

No samples, no external service: heartbeat, taiko, sub booms, tremolo strings, a
Shepard-style riser, a brass-ish lead in D minor and a bell outro, all placed on the
shared timeline so each hit lands on the matching picture cut.

    python audio.py score.wav
"""
import sys
import wave

import numpy as np

from timeline import (BEATS, BOOM, CHARGE, DUR, HEART, HITS, IMPACT, ROLL, SILENCE, SR, TITLE_SLAM)

N = int(SR * DUR)
rng = np.random.default_rng(3)
DL = np.zeros(N, np.float32)
DR = np.zeros(N, np.float32)
SEND = np.zeros(N, np.float32)
LATE_L = np.zeros(N, np.float32)       # added after the blackout duck
LATE_R = np.zeros(N, np.float32)

_NOTE = {'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'F': 5, 'F#': 6, 'Gb': 6,
         'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11}


def hz(name):
    key, octv = (name[:2], int(name[2:])) if name[1] in '#b' else (name[:1], int(name[1:]))
    return 440.0 * 2 ** ((_NOTE[key] + 12 * (octv + 1) - 69) / 12.0)


def tt(n):
    return np.arange(n, dtype=np.float32) / SR


def add(sig, t0, gain=1.0, pan=0.0, send=0.25, late=False):
    i0 = int(t0 * SR)
    if i0 >= N or i0 + len(sig) <= 0:
        return
    i1 = min(N, i0 + len(sig))
    s = sig[:i1 - i0].astype(np.float32) * gain
    a = (pan + 1) * np.pi / 4
    if late:
        LATE_L[i0:i1] += s * np.cos(a)
        LATE_R[i0:i1] += s * np.sin(a)
    else:
        DL[i0:i1] += s * np.cos(a)
        DR[i0:i1] += s * np.sin(a)
        SEND[i0:i1] += s * send


def box(x, k):
    return np.convolve(x, np.ones(k, np.float32) / k, mode='same')


def lowpass_noise(n, k):
    return box(rng.normal(size=n).astype(np.float32), k)


def highpass_noise(n, k):
    x = rng.normal(size=n).astype(np.float32)
    return x - box(x, k)


def adsr(n, a, r, sustain=1.0):
    e = np.ones(n, np.float32) * sustain
    na = max(1, int(a * SR))
    e[:na] *= np.linspace(0, 1, na, dtype=np.float32) ** 2
    nr = max(1, int(r * SR))
    e[-nr:] *= np.linspace(1, 0, nr, dtype=np.float32) ** 1.5
    return e


def saw(f, dur, a=0.03, r=0.3, vib=0.0, harm=16, p=1.0, detune=(0.0,), vib_delay=0.3):
    n = int((dur + r) * SR)
    t = tt(n)
    out = np.zeros(n, np.float32)
    vramp = np.clip((t - vib_delay) / 0.5, 0, 1)
    for dcents in detune:
        ft = f * 2 ** (dcents / 1200.0) * (1 + vib * vramp * np.sin(2 * np.pi * 5.6 * t))
        ph = 2 * np.pi * np.cumsum(ft) / SR
        hm = max(1, min(harm, int(0.45 * SR / f)))
        for k in range(1, hm + 1):
            out += np.sin(k * ph).astype(np.float32) / (k ** p)
    out /= len(detune)
    return out * adsr(n, a, r)


def taiko(f0=118, f1=62, dur=0.7, decay=0.16, noise=0.4):
    n = int(dur * SR)
    t = tt(n)
    freq = f1 + (f0 - f1) * np.exp(-t / 0.035)
    ph = 2 * np.pi * np.cumsum(freq) / SR
    body = np.sin(ph) * np.exp(-t / decay)
    click = lowpass_noise(n, 5) * np.exp(-t / 0.025) * noise
    skin = np.sin(2 * np.pi * (f1 * 2.6) * t) * np.exp(-t / 0.07) * 0.25
    return (body + click + skin).astype(np.float32)


def thump(f=55, dur=0.35, decay=0.09):
    n = int(dur * SR)
    t = tt(n)
    freq = f * 0.75 + (f * 0.9) * np.exp(-t / 0.03)
    return (np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-t / decay)).astype(np.float32)


def boom(dur=5.0, decay=1.4):
    n = int(dur * SR)
    t = tt(n)
    freq = 26 + (120 - 26) * np.exp(-t / 0.28)
    body = np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-t / decay)
    rumble = lowpass_noise(n, 9) * np.exp(-t / 0.9) * 1.6
    crack = rng.normal(size=n).astype(np.float32) * np.exp(-t / 0.05) * 0.5
    return (body + rumble + crack).astype(np.float32)


def crash(dur=3.0, decay=0.9):
    n = int(dur * SR)
    t = tt(n)
    nz = highpass_noise(n, 3) * np.exp(-t / decay)
    return nz * np.minimum(1.0, t / 0.01)


def whoosh(dur, rise=3.0):
    n = int(dur * SR)
    t = tt(n)
    u = t / dur
    nz = highpass_noise(n, 6) + 0.6 * lowpass_noise(n, 3)
    return (nz * (u ** rise)).astype(np.float32)


def bell(f, dur=3.0):
    n = int(dur * SR)
    t = tt(n)
    s = np.zeros(n, np.float32)
    for h, g, d in ((1, 1.0, 1.8), (2.0, 0.5, 1.2), (2.76, 0.35, 0.8), (4.1, 0.2, 0.5), (5.4, 0.1, 0.35)):
        s += g * np.sin(2 * np.pi * f * h * t) * np.exp(-t / d)
    return s * np.minimum(1.0, t / 0.004)


def curve(points, n=N):
    xs = [p[0] * SR for p in points]
    ys = [p[1] for p in points]
    return np.interp(np.arange(n), xs, ys).astype(np.float32)


# =========================================================================== layers
# ---- sub drone + wind, whole piece ------------------------------------------------
t_all = tt(N)
drone = (np.sin(2 * np.pi * hz('D1') * t_all) + 0.5 * np.sin(2 * np.pi * hz('D2') * t_all + 0.4)
         + 0.18 * np.sin(2 * np.pi * hz('A2') * t_all)).astype(np.float32)
drone *= curve([(0, 0), (3, 0.25), (9, 0.35), (17, 0.45), (27, 0.6), (34.5, 0.9), (34.55, 0.0),
                (35.0, 0.0), (35.05, 0.9), (49, 0.9), (49.05, 1.0), (56, 0.55), (60, 0)])
add(drone, 0, 0.55, send=0.1)

wind = lowpass_noise(N, 14) - lowpass_noise(N, 90)
wind *= (0.6 + 0.4 * np.sin(2 * np.pi * 0.11 * t_all + 1.0)) * curve([(0, 0), (2, 0.5), (9, 0.55), (17, 0.3),
                                                                         (27, 0.1), (60, 0.05)])
add(wind, 0, 0.55, pan=0.0, send=0.35)

# ---- heartbeat (A-C), gets stronger / faster ------------------------------------------
for i, te in enumerate(HEART):
    g = 0.35 + 0.5 * min(1.0, te / 17.0)
    add(thump(52, 0.4, 0.10), te, g * 1.2, send=0.2)
    add(thump(46, 0.3, 0.07), te + 0.2, g * 0.8, send=0.2)

# ---- strings pad: dark cluster (B onward) -------------------------------------------------
def string_pad(freqs, t0, dur, gain, trem=0.0, bright=1.6, send=0.5):
    for i, f in enumerate(freqs):
        s = saw(f, dur, a=min(2.0, dur * 0.4), r=1.0, vib=0.004, harm=14, p=bright, detune=(-9, 0, 9))
        if trem:
            s = s * (1 - 0.35 + 0.35 * np.sin(2 * np.pi * trem * tt(len(s))))
        add(s, t0, gain, pan=(-0.5 + i * 0.35) if len(freqs) > 1 else 0, send=send)


string_pad([hz('D3'), hz('A3'), hz('F4')], 9.0, 8.5, 0.10)
string_pad([hz('D3'), hz('A3'), hz('Eb4')], 17.0, 10.5, 0.11, trem=6.0)       # Eb = unease
string_pad([hz('D3'), hz('F3'), hz('Ab3'), hz('D4')], 27.0, 7.6, 0.13, trem=9.0)

# ---- C: every blow he absorbs ------------------------------------------------------------------
for i, th in enumerate(HITS):
    g = 0.55 + 0.4 * (i / len(HITS))
    add(boom(2.2, 0.5), th, 0.55 * g, send=0.5)
    add(taiko(130, 70, 0.8, 0.2, 0.5), th, 0.8 * g, pan=0.15 * (1 if i % 2 else -1), send=0.4)
    add(crash(0.5, 0.08) * 0.7, th, 0.5 * g, pan=-0.2 * (1 if i % 2 else -1), send=0.3)
# low pulsing ostinato 17-35 (builds)
for k in range(int((35 - 17) / 0.5)):
    t0 = 17.0 + 0.5 * k
    g = 0.05 + 0.12 * ((t0 - 17) / 18.0)
    add(saw(hz('D2'), 0.25, a=0.005, r=0.12, harm=10, p=1.2), t0, g, send=0.1)
    add(saw(hz('D2'), 0.2, a=0.005, r=0.1, harm=10, p=1.2), t0 + 0.25, g * 0.6, send=0.1)

# ---- D: riser + accelerating taiko roll + tremolo violins ---------------------------------------
rn = int(7.5 * SR)
u = np.linspace(0, 1, rn, dtype=np.float32)
fsweep = 150 * (12.0 ** u)
ph = 2 * np.pi * np.cumsum(fsweep) / SR
rs = np.zeros(rn, np.float32)
for k in range(1, 7):
    rs += np.sin(k * ph) / (k ** 1.1)
rs += 0.6 * np.sin(ph * 1.005)
rs *= (u ** 2.0) * np.minimum(1, (1 - u) * 40)
add(rs, 27.0, 0.28, send=0.35)
add(highpass_noise(rn, 5) * (u ** 2.6), 27.0, 0.45, send=0.5)
for i, tr in enumerate(ROLL):
    g = 0.25 + 0.75 * ((tr - 27) / 7.5)
    add(taiko(110, 60, 0.5, 0.14, 0.45), tr, 0.95 * g, pan=0.35 * (1 if i % 2 else -1), send=0.4)
vn = int(5.5 * SR)
tv = tt(vn)
viol = (saw(hz('D5'), 5.0, a=2.0, r=0.5, harm=8, p=1.4, detune=(-8, 8))
        + saw(hz('Eb5'), 5.0, a=2.5, r=0.5, harm=8, p=1.4, detune=(-8, 8)))
viol = viol[:vn] * (0.55 + 0.45 * np.sin(2 * np.pi * 14 * tv[:len(viol)][:vn]))
add(viol, 29.0, 0.16, send=0.5)

# ---- blackout: two unducked heartbeats -----------------------------------------------------------
add(thump(48, 0.6, 0.16), 34.62, 1.4, late=True)
add(thump(42, 0.5, 0.12), 34.84, 1.0, late=True)

# ---- E: ULTRA EGO ---------------------------------------------------------------------------------
add(boom(6.0, 1.7), BOOM, 1.3, send=0.6)
add(crash(3.5, 1.1), BOOM, 0.9, send=0.6)
add(taiko(110, 56, 1.0, 0.3, 0.5), BOOM, 1.1)

CH_E = [['D3', 'F3', 'A3', 'D4'], ['Bb2', 'D3', 'F3', 'Bb3'], ['C3', 'E3', 'G3', 'C4'], ['D3', 'F3', 'A3', 'D4'],
        ['Bb2', 'D3', 'F3', 'Bb3'], ['G2', 'Bb2', 'D3', 'G3'], ['A2', 'C#3', 'E3', 'A3']]
ROOT_E = ['D2', 'Bb1', 'C2', 'D2', 'Bb1', 'G1', 'A1']
MELODY = [  # (bar, beat, note, beats)
    (0, 0, 'D5', 2), (0, 2, 'F5', 1), (0, 3, 'A5', 1),
    (1, 0, 'G5', 1.5), (1, 1.5, 'F5', 0.5), (1, 2, 'D5', 2),
    (2, 0, 'E5', 1), (2, 1, 'G5', 1), (2, 2, 'C6', 2),
    (3, 0, 'A5', 1.5), (3, 1.5, 'G5', 0.5), (3, 2, 'F5', 1), (3, 3, 'E5', 1),
    (4, 0, 'D5', 2), (4, 2, 'F5', 1), (4, 3, 'A5', 1),
    (5, 0, 'Bb5', 1.5), (5, 1.5, 'A5', 0.5), (5, 2, 'G5', 2),
    (6, 0, 'A5', 1), (6, 1, 'C#6', 1), (6, 2, 'E6', 2),
]
BEAT = 0.5
for bar, (chord, root) in enumerate(zip(CH_E, ROOT_E)):
    tb = BOOM + bar * 2.0
    inten = 0.85 + 0.15 * (bar / 6.0)
    # sustained chord (strings/brass) with a beat-pump
    for i, nm in enumerate(chord):
        s = saw(hz(nm), 2.0, a=0.05, r=0.45, vib=0.003, harm=18, p=1.15, detune=(-7, 0, 7))
        pump = 1 - 0.38 * np.exp(-((tt(len(s)) % BEAT)) / 0.10)
        add(s * pump, tb, 0.085 * inten, pan=-0.45 + 0.3 * i, send=0.45)
    # choir-ish octave shimmer
    for nm in chord[1:3]:
        f = hz(nm) * 2
        s = saw(f, 2.0, a=0.35, r=0.5, vib=0.005, harm=9, p=1.5, detune=(-12, 12))
        add(s, tb, 0.05 * inten, send=0.7)
    # driving 8th-note bass
    for k in range(8):
        add(saw(hz(root), 0.22, a=0.004, r=0.1, harm=14, p=1.0), tb + k * 0.25, 0.20 * inten, send=0.08)
    # taiko on every beat, accent on 1 & 3, crash on bar start
    for b in range(4):
        tb2 = tb + b * BEAT
        strong = b in (0, 2)
        add(taiko(122 if strong else 140, 64 if strong else 78, 0.7, 0.18, 0.5), tb2,
            (0.9 if strong else 0.55) * inten, pan=-0.15 if strong else 0.2, send=0.35)
        if strong:
            add(thump(48, 0.5, 0.12), tb2, 0.9 * inten, send=0.15)
        add(taiko(150, 90, 0.4, 0.09, 0.4), tb2 + BEAT / 2, 0.30 * inten, pan=0.3, send=0.3)
    add(crash(2.6, 0.8), tb, 0.55 * inten, pan=0.1, send=0.6)
for bar, beat, nm, d in MELODY:
    t0 = BOOM + bar * 2.0 + beat * BEAT
    dur = d * BEAT
    s = saw(hz(nm), dur, a=0.03, r=0.25, vib=0.008, harm=16, p=1.05, detune=(-6, 6))
    s += 0.45 * saw(hz(nm) / 2, dur, a=0.03, r=0.25, vib=0.008, harm=10, p=1.2)
    add(s, t0, 0.17, pan=0.05, send=0.55)
# title-slam accent
add(crash(3.0, 1.0), TITLE_SLAM, 0.8, send=0.6)
add(boom(2.5, 0.6), TITLE_SLAM, 0.8, send=0.4)

# ---- the charge: accelerating hits, swell, then a 0.12 s gasp before the impact ----------------
tc = CHARGE
while tc < 48.0:
    add(taiko(130, 70, 0.4, 0.12, 0.5), tc, 0.9, send=0.3)
    tc += 0.25
while tc < IMPACT - 0.12:
    add(taiko(150, 80, 0.3, 0.09, 0.5), tc, 1.0, pan=0.3 * (1 if int(tc * 8) % 2 else -1), send=0.3)
    tc += 0.125
add(whoosh(2.0, 3.0), CHARGE, 0.9, send=0.5)
add(saw(hz('A4'), 2.0, a=1.6, r=0.1, harm=12, p=1.1, detune=(-9, 0, 9)), CHARGE, 0.18, send=0.4)

# ---- F: impact + resolve --------------------------------------------------------------------------
add(boom(6.5, 2.0), IMPACT, 1.4, send=0.7)
add(crash(4.0, 1.5), IMPACT, 1.0, send=0.7)
add(taiko(110, 54, 1.2, 0.35, 0.5), IMPACT, 1.2)
for i, nm in enumerate(['D3', 'A3', 'D4', 'F4']):
    s = saw(hz(nm), 10.0, a=1.8, r=2.5, vib=0.004, harm=14, p=1.4, detune=(-8, 0, 8))
    add(s, IMPACT + 0.2, 0.12, pan=-0.5 + 0.33 * i, send=0.6)
add(saw(hz('D5'), 9.0, a=2.5, r=2.0, vib=0.004, harm=8, p=1.5, detune=(-10, 10)), IMPACT + 0.5, 0.07, send=0.8)
for t0, nm, g in ((51.0, 'D5', 0.30), (52.0, 'F5', 0.26), (53.0, 'A5', 0.26), (54.0, 'G5', 0.24),
                  (55.0, 'F5', 0.24), (56.0, 'D5', 0.30), (57.5, 'A4', 0.2)):
    add(bell(hz(nm), 3.5), t0, g, pan=0.2 if nm in ('F5', 'G5') else -0.1, send=0.7)
for t0 in (51.0, 53.0, 55.0, 57.0):                     # slow, fading heart-drum
    add(thump(48, 0.6, 0.14), t0, 0.6 * (1 - (t0 - 51) / 8.0), send=0.3)

# =========================================================================== mixdown
def reverb_ir(seconds=3.4, seed=11):
    r = np.random.default_rng(seed)
    n = int(seconds * SR)
    t = np.arange(n) / SR
    ir = r.normal(size=n).astype(np.float32) * np.exp(-t / 0.95)
    ir = box(ir, 5) * 1.5 + 0.0
    ir[: int(0.025 * SR)] = 0
    return ir


def fft_conv(x, h):
    n = 1
    while n < len(x) + len(h):
        n *= 2
    X = np.fft.rfft(x, n)
    H = np.fft.rfft(h, n)
    return np.fft.irfft(X * H, n)[:len(x)].astype(np.float32)


wetL = fft_conv(SEND, reverb_ir(seed=11))
wetR = fft_conv(SEND, reverb_ir(seed=12))
wetL *= 0.0045
wetR *= 0.0045
outL = DL + wetL
outR = DR + wetR

# blackout duck: everything drops out for the beat before the transformation
duck = curve([(0, 1), (SILENCE - 0.04, 1), (SILENCE, 0.0), (BOOM - 0.005, 0.0), (BOOM, 1.0), (DUR, 1)])
outL = outL * duck + LATE_L
outR = outR * duck + LATE_R

# the 0.12 s gasp before the final impact
gasp = curve([(0, 1), (IMPACT - 0.12, 1), (IMPACT - 0.10, 0.05), (IMPACT - 0.005, 0.05), (IMPACT, 1), (DUR, 1)])
outL *= gasp
outR *= gasp

master = curve([(0, 0), (0.6, 1), (58.0, 1), (60.0, 0)])
outL *= master
outR *= master
peak = max(np.abs(outL).max(), np.abs(outR).max())
outL, outR = outL / peak * 1.05, outR / peak * 1.05
outL, outR = np.tanh(1.25 * outL) / np.tanh(1.25), np.tanh(1.25 * outR) / np.tanh(1.25)
outL, outR = outL * 0.93, outR * 0.93


def write_wav(path):
    st = np.stack([outL, outR], axis=1)
    pcm = (np.clip(st, -1, 1) * 32767).astype('<i2')
    with wave.open(path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


if __name__ == '__main__':
    write_wav(sys.argv[1] if len(sys.argv) > 1 else 'score.wav')
    print('wrote', sys.argv[1] if len(sys.argv) > 1 else 'score.wav',
          'peak', float(np.abs(np.stack([outL, outR])).max()))
