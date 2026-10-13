#!/usr/bin/env bash
# Render an episode, normalise loudness to YouTube's -14 LUFS, and make a GitHub-friendly
# 1080p file (<100 MB) plus a 720p preview (<30 MB, small enough to send in chat).
# Usage (from the animation project dir): finish_video.sh Ep04 ../episodes/ep04_slug ep04
set -euo pipefail
COMP=$1; OUTDIR=$2; NAME=$3
BROWSER=${REMOTION_BROWSER:-/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell}
mkdir -p out "$OUTDIR"
ARGS=(); [ -x "$BROWSER" ] && ARGS=(--browser-executable="$BROWSER")
npx remotion render "$COMP" "out/${NAME}_raw.mp4" "${ARGS[@]}" --concurrency=100% --log=error
ffmpeg -hide_banner -loglevel error -y -i "out/${NAME}_raw.mp4" -c:v libx264 -preset slow -crf 24 -pix_fmt yuv420p \
  -movflags +faststart -af loudnorm=I=-14:TP=-1:LRA=11 -c:a aac -b:a 192k -ar 48000 "$OUTDIR/${NAME}_1080p.mp4"
ffmpeg -hide_banner -loglevel error -y -i "$OUTDIR/${NAME}_1080p.mp4" -c:v libx264 -preset medium -crf 30 \
  -vf scale=1280:-2 -c:a aac -b:a 128k "$OUTDIR/${NAME}_preview_720p.mp4"
ls -la "$OUTDIR"/*.mp4
