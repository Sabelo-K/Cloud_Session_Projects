"""Generate a voiceover with Kokoro TTS (free, Apache-2.0) plus exact sentence timings.

Usage: python kokoro_vo.py VOICEOVER.txt out.wav timing.json [voice] [speed]
Model files (kokoro-v1.0.onnx, voices-v1.0.bin) come from
https://github.com/thewh1teagle/kokoro-onnx/releases ; set KOKORO_DIR to their folder.
"""
import json, os, re, sys
import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

txt_path, wav_path, timing_path = sys.argv[1:4]
voice = sys.argv[4] if len(sys.argv) > 4 else "bm_george"
speed = float(sys.argv[5]) if len(sys.argv) > 5 else 1.0
d = os.environ.get("KOKORO_DIR", ".")
k = Kokoro(os.path.join(d, "kokoro-v1.0.onnx"), os.path.join(d, "voices-v1.0.bin"))

paras = [p.strip() for p in open(txt_path).read().split("\n") if p.strip()]
SENT_GAP, PARA_GAP = 0.32, 0.65
audio, timing, t, sr = [], [], 0.0, 24000
for pi, para in enumerate(paras):
    sents = [s.strip() for s in re.split(r"(?<=[.?!:])\s+", para) if s.strip()]
    for si, s in enumerate(sents):
        samples, sr = k.create(s, voice=voice, speed=speed, lang="en-us" if voice.startswith("a") else "en-gb")
        dur = len(samples) / sr
        timing.append({"i": len(timing), "text": s, "start": round(t, 2), "end": round(t + dur, 2)})
        audio.append(samples)
        t += dur
        gap = PARA_GAP if si == len(sents) - 1 else SENT_GAP
        audio.append(np.zeros(int(sr * gap), dtype=np.float32))
        t += gap
out = np.concatenate(audio)
sf.write(wav_path, out, sr)
json.dump(timing, open(timing_path, "w"), indent=1)
print(f"{len(timing)} sentences, {t:.2f}s")
