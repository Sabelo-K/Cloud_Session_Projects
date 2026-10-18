"""Kokoro voiceover generated a whole paragraph at a time (more natural prosody than per-sentence).
Exact paragraph start/end times; sentence times inside a paragraph are split by character share.
Usage: python kokoro_vo_para.py VOICEOVER.txt out.wav timing.json [voice] [speed] [lang]
"""
import json, os, re, sys
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
txt, wav, tjson = sys.argv[1:4]
voice = sys.argv[4] if len(sys.argv) > 4 else "am_michael"
speed = float(sys.argv[5]) if len(sys.argv) > 5 else 0.95
lang = sys.argv[6] if len(sys.argv) > 6 else "en-us"
d = os.environ.get("KOKORO_DIR", ".")
k = Kokoro(os.path.join(d, "kokoro-v1.0.onnx"), os.path.join(d, "voices-v1.0.bin"))
paras = [p.strip() for p in open(txt, encoding="utf-8").read().split("\n") if p.strip()]
GAP = 0.7; audio = []; timing = []; t = 0.0; sr = 24000
for p in paras:
    s, sr = k.create(p, voice=voice, speed=speed, lang=lang)
    dur = len(s) / sr
    sents = [x.strip() for x in re.split(r"(?<=[.?!:])\s+", p) if x.strip()]
    tot = sum(len(x) + 6 for x in sents); c = 0
    for x in sents:
        a = t + dur * c / tot; c += len(x) + 6; b = t + dur * c / tot
        timing.append({"i": len(timing), "text": x, "start": round(a, 2), "end": round(b - 0.15, 2)})
    audio += [s, np.zeros(int(sr * GAP), dtype=np.float32)]; t += dur + GAP
sf.write(wav, np.concatenate(audio), sr)
json.dump(timing, open(tjson, "w"), indent=1)
print(len(timing), "sentences", round(t, 2), "s")
