"""A tiny sound-effects synth (standard library only) so a rendered film is not silent.

    track = [Sound("rumble", 0.0, 10.0, 0.35), Sound("boom", 4.5, 1.8, 1.0), Sound("whoosh", 3.5, 0.6, 0.7, pan=-0.4)]
    write_wav("sfx.wav", mix(track, seconds=10))

Sounds are synthesised, so there is nothing to license. They are simple (think "good placeholder"):
swap in recorded effects or music in your editor for a finished video. Times are in seconds
(`frame / fps`). `pan` runs from -1 (left) to 1 (right).
"""
from __future__ import annotations

import math
import random
import struct
import wave
from dataclasses import dataclass
from pathlib import Path

SAMPLE_RATE = 44100
KINDS = ("boom", "hit", "whoosh", "rise", "rumble", "zap")


@dataclass(frozen=True)
class Sound:
    kind: str
    start: float
    duration: float
    gain: float = 1.0
    pan: float = 0.0

    def __post_init__(self) -> None:
        if self.kind not in KINDS:
            raise ValueError(f"unknown sound {self.kind!r}; choose from {', '.join(KINDS)}")
        if self.duration <= 0 or self.start < 0:
            raise ValueError("a sound needs start >= 0 and duration > 0")


def _lowpass(x: list[float], cutoff: float, rate: int) -> list[float]:
    a = 1 - math.exp(-2 * math.pi * cutoff / rate)
    y, out = 0.0, []
    for v in x:
        y += a * (v - y)
        out.append(y)
    return out


def _noise(n: int, rng: random.Random) -> list[float]:
    return [rng.uniform(-1, 1) for _ in range(n)]


def _synth(s: Sound, rate: int, rng: random.Random) -> list[float]:
    n = int(s.duration * rate)
    t = [i / rate for i in range(n)]
    if s.kind == "boom":                    # deep sine that falls in pitch, plus a rumbling noise burst
        phase, tone = 0.0, []
        for ti in t:
            phase += 2 * math.pi * (35 + 85 * math.exp(-ti * 5)) / rate
            tone.append(math.sin(phase) * math.exp(-ti * 2.2))
        burst = _lowpass(_noise(n, rng), 500, rate)
        return [a + 1.4 * b * math.exp(-ti * 3.5) for a, b, ti in zip(tone, burst, t)]
    if s.kind == "hit":                     # a punchy thump with a crack on top
        crack = _lowpass(_noise(n, rng), 3500, rate)
        return [math.sin(2 * math.pi * (70 + 130 * math.exp(-ti * 40)) * ti) * math.exp(-ti * 14)
                + 0.9 * c * math.exp(-ti * 28) for c, ti in zip(crack, t)]
    if s.kind == "whoosh":                  # filtered noise that swells and fades
        raw = _noise(n, rng)
        low, high = _lowpass(raw, 700, rate), _lowpass(raw, 3200, rate)
        return [(l + (h - l) * math.sin(math.pi * ti / s.duration)) * math.sin(math.pi * ti / s.duration) ** 2 * 1.6
                for l, h, ti in zip(low, high, t)]
    if s.kind == "rise":                    # a tone sweeping upwards and getting louder: tension
        phase, out = 0.0, []
        for ti in t:
            k = ti / s.duration
            phase += 2 * math.pi * (70 + 900 * k * k) / rate
            out.append((math.sin(phase) + 0.4 * math.sin(2.01 * phase)) * k ** 1.5)
        shimmer = _lowpass(_noise(n, rng), 5000, rate)
        return [a + 0.5 * b * (ti / s.duration) ** 2 for a, b, ti in zip(out, shimmer, t)]
    if s.kind == "zap":                     # a short electric sizzle
        buzz = _noise(n, rng)
        return [(math.sin(2 * math.pi * (900 + 400 * math.sin(ti * 60)) * ti) * 0.5 + b * 0.5)
                * math.exp(-ti * 9) for b, ti in zip(buzz, t)]
    # rumble: low brown-ish noise with a slow swell, a bed of power under everything
    low = _lowpass(_lowpass(_noise(n, rng), 140, rate), 140, rate)
    return [v * 9 * (0.75 + 0.25 * math.sin(2 * math.pi * 0.45 * ti)) * min(1, ti / 0.4, (s.duration - ti) / 0.4)
            for v, ti in zip(low, t)]


def mix(sounds: list[Sound], seconds: float, rate: int = SAMPLE_RATE, seed: int = 0
        ) -> tuple[list[float], list[float]]:
    """Mix sounds into (left, right) sample lists, scaled so the loudest moment peaks at 90%."""
    rng = random.Random(seed)
    total = int(seconds * rate)
    left, right = [0.0] * total, [0.0] * total
    for s in sounds:
        first = int(s.start * rate)
        theta = (max(-1.0, min(1.0, s.pan)) + 1) * math.pi / 4          # equal-power pan law
        gl, gr = math.cos(theta) * s.gain, math.sin(theta) * s.gain
        for i, v in enumerate(_synth(s, rate, rng)):
            j = first + i
            if j >= total:
                break
            left[j] += v * gl
            right[j] += v * gr
    peak = max([abs(v) for v in left + right] + [1e-9])
    scale = 0.9 / peak                                                   # loudest moment sits at 90%
    return [v * scale for v in left], [v * scale for v in right]


def write_wav(path: str | Path, channels: tuple[list[float], list[float]], rate: int = SAMPLE_RATE) -> Path:
    left, right = channels
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    frames = bytearray()
    for l, r in zip(left, right):
        frames += struct.pack("<hh", int(max(-1, min(1, l)) * 32767), int(max(-1, min(1, r)) * 32767))
    with wave.open(str(path), "wb") as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(rate)
        f.writeframes(bytes(frames))
    return path
