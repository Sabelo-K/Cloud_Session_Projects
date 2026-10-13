"""Build YouTube captions (.srt) from a timing.json produced by kokoro_vo.py or align_timing.py.
Very short fragments (e.g. "One:") are merged into the next line.
Usage: python make_srt.py timing.json out.srt
"""
import json, sys

t = json.load(open(sys.argv[1]))


def ts(x):
    h, m, s = int(x // 3600), int(x % 3600 // 60), x % 60
    return f"{h:02}:{m:02}:{int(s):02},{int((s % 1) * 1000):03}"


out, buf = [], None
for r in t:
    buf = {"start": buf["start"], "end": r["end"], "text": buf["text"] + " " + r["text"]} if buf else dict(r)
    if buf["end"] - buf["start"] >= 1.2 or r is t[-1]:
        out.append(buf)
        buf = None
with open(sys.argv[2], "w") as f:
    for i, r in enumerate(out, 1):
        f.write(f"{i}\n{ts(r['start'])} --> {ts(max(r['end'], r['start'] + 1))}\n{r['text']}\n\n")
print(f"{len(out)} captions")
