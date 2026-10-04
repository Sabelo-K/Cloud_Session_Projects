#!/usr/bin/env bash
# Mux the silent master render with the synthesized score, normalise loudness for YouTube
# and re-encode video to a sensible delivery size (the master is near-lossless and large
# because of the film grain).
set -euo pipefail
cd "$(dirname "$0")"
IN_V=${1:-build/silent.mp4}
IN_A=${2:-build/score.wav}
OUT=${3:-build/ultra_ego_motion_sketch.mp4}

ffmpeg -y -loglevel error -i "$IN_V" -i "$IN_A" \
  -filter_complex "[1:a]loudnorm=I=-16:TP=-1.5:LRA=11[a]" \
  -map 0:v -map "[a]" \
  -c:v libx264 -preset slow -crf 20 -pix_fmt yuv420p -r 24 \
  -c:a aac -b:a 256k -ar 48000 -movflags +faststart -shortest "$OUT"
echo "wrote $OUT"
