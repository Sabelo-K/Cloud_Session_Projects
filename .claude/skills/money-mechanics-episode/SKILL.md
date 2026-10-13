---
name: money-mechanics-episode
description: Produce a complete, upload-ready episode for the Money Mechanics faceless YouTube channel (or any similar faceless explainer channel), covering a fact-checked script, a free Kokoro AI voiceover, hand-drawn-style animation in Remotion + rough.js with the mascot Penny, original synthesised music and sound effects, a 1080p render normalised to -14 LUFS, thumbnail, captions and an upload kit, all at $0. Use this skill whenever the user asks for a new Money Mechanics episode or video ("make the casino episode", "next episode", "Ep 4"), wants a faceless animated explainer, a "how X makes money" video, or wants to re-voice, re-render, re-time or fix an existing episode, even if they don't say "skill" or name every step.
---

# Money Mechanics Episode Production

Money Mechanics explains how the money machines around you actually work, in roughly 4–5 minute hand-drawn-style animated videos. The house format is "How X Actually Makes Money". Everything in this pipeline is free: no subscriptions, no paid credits, no licensed media. Keep it that way. The channel owner has no budget, so never spend money or paid credits without asking first.

The pipeline was battle-tested on three episodes (pawn shops, Costco, credit cards). Follow it in order; each step feeds the next.

## 0. Set up the workspace (once per session)

The animation project lives at `youtube_channel/animation/` in the repo. If it's missing, scaffold it from this skill:

```bash
cp -r <skill>/assets/template youtube_channel/animation
cp <skill>/scripts/*.py youtube_channel/animation/scripts/   # mkdir -p first
cd youtube_channel/animation && npm install
```

Sound effects aren't bundled (they regenerate in seconds):
```bash
python3 -m venv /tmp/venv && /tmp/venv/bin/pip -q install numpy kokoro-onnx soundfile
/tmp/venv/bin/python -I scripts/synth_audio.py public/sfx 270   # 270 = music length (s); make it ≥ episode length
ffmpeg -y -i public/sfx/music_lofi.wav -b:a 160k public/sfx/music_lofi.mp3 && rm public/sfx/music_lofi.wav
```
Rename the music to match what the episode's `<Soundtrack music=...>` references.

Kokoro model files come from GitHub releases (Hugging Face may be blocked by a proxy; GitHub works):
```bash
mkdir -p /tmp/kokoro && cd /tmp/kokoro
curl -sSLO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
curl -sSLO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
```
Start these downloads in the background while you research.

**Cloud container note:** Remotion needs the pre-installed headless shell:
`--browser-executable=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell`. Fonts are bundled locally because the headless browser can't reach Google Fonts.

## 1. Pick the topic and check demand

Check the content calendar in `youtube_channel/LAUNCH_PLAN.md` and the upload order. **Each episode ends by teasing the next one**, so confirm which episode should come next before writing. If the previous episode promised a topic, make that one, or flag the mismatch to the user.

If vidIQ tools are available, `vidiq_keyword_research` (free) on the main keyword gives search volume and competition; prefer high volume and competition under ~40. Don't call paid vidIQ tools without asking.

## 2. Research and fact-check

Use primary sources wherever possible: annual reports and 10-K filings (SEC EDGAR), the Federal Reserve, the New York Fed, the CFPB, state regulators, and official company releases. Run searches in parallel. For every number that will be spoken:
- record the exact figure, the period it covers and the source URL;
- if you calculated something (payoff times, ratios), show the arithmetic in the log and say it's illustrative;
- if a claim can't be verified, cut it or reword it so it doesn't depend on it. Popular "facts" (markup caps, quotes, legends) often turn out to be unverifiable.

Why: the channel's credibility, and YouTube's originality rules, rest on accurate, sourced scripts. Sources also go in the description.

## 3. Write the script

Write to `youtube_channel/episodes/epNN_slug/SCRIPT.md`. See `references/example_script.md` for a complete example. Structure:

| Beat | Purpose |
|---|---|
| Cold open hook (~15s) | A surprising number or situation with Penny. Never open with an intro. |
| Promise (~15s) | What they'll understand by the end, then the MONEY MECHANICS title card. |
| Setup | Penny's relatable situation. |
| 2–3 reveals ("engines", "tricks") | Each gets one visual metaphor and one number, with a re-hook every ~45s. |
| So-what | How it affects the viewer's own money, plus 3 practical rules. |
| Payoff + bridge | A one-line takeaway, then tease the next episode by name. |

Format: `**VISUAL:**` lines for the animator and `> ` blockquotes for narration, with ` / ` marking pauses. End with a fact-check log table and a source list. Write numbers the way they should be spoken ("one point two six trillion").

**Length:** aim for **~620–650 narration words**, which Kokoro reads in about 4:10–4:20. Count with `scripts/extract_vo.sh SCRIPT.md | wc -w` and extend with *verified* material if you're short. Both earlier first drafts came in ~150 words short.

Mark the script `Status: LOCKED` once every claim is checked.

## 4. Voiceover (free Kokoro)

```bash
scripts/extract_vo.sh episodes/epNN/SCRIPT.md > episodes/epNN/VOICEOVER.txt
KOKORO_DIR=/tmp/kokoro /tmp/venv/bin/python -I animation/scripts/kokoro_vo.py \
  episodes/epNN/VOICEOVER.txt /tmp/epNN.wav animation/timing_epNN.json bm_george 1.0
ffmpeg -y -i /tmp/epNN.wav -af loudnorm=I=-16:TP=-1.5 -ar 44100 -b:a 128k animation/public/epNN_vo.mp3
```
The channel voice is **`bm_george`**; keep it consistent across episodes. The script generates sentence by sentence, so `timing_epNN.json` holds **exact** start and end times for every sentence. Print it; every animation cue comes from it.

(For an externally produced voiceover, use `scripts/align_timing.py VOICEOVER.txt vo.mp3 timing.json` instead. It estimates sentence timings from pauses and is accurate to roughly ±1s.)

## 5. Animate

Create `src/epNN/EpNN.tsx`, modelled on `references/example_episode.tsx`, and register it in `src/Root.tsx`.

**The look** (see `assets/template/src/lib/`):
- `rough.tsx` contains `R` (any hand-drawn shape with draw-on animation and line boil), `T` (hand-lettered text), `G` (group with transform), `useP()` (eased progress and pop helpers), and the palette `C`.
- `characters.tsx` contains **Penny** (moods: neutral, happy, worried, shocked, thinking, confident; plus `walk`, `wave`, `holdGuitar`), the Broker/shopkeeper and the guitar.
- `props.tsx` and `props2.tsx` hold about 30 reusable props (cash, coin, jar, card, gear, tick, cross, price tag, bubble, pawn shop, warehouse, cart, receipt, calculator, casino sign…).
- `sound.tsx` contains `<Soundtrack music sfx voEnd dips>`, a music bed at 0.14 that dips before key lines and swells on the end screen.

**Build pattern:**
- One component per script beat. Scene boundaries are the sentence start times from the timing file, and a `useCue(sceneStart)` helper lets cues use *global* seconds copied straight from the timing.
- Inside a scene, switch sub-parts with `t < X ? … : …` at sentence boundaries, and pop elements in on the sentence where they're mentioned.
- Each reveal gets a header ("ENGINE #1: THE SWIPE"), one strong visual and its number counting up (`countUp`).
- Reuse props first. Draw new ones as small components (in the episode file, or `props2.tsx` if reusable).
- Add a 12s end screen with dashed placeholders for YouTube's "watch next" and subscribe elements, and Penny waving.
- Build an SFX table that matches each visual beat: pop for text, cha-ching for money, coin for fees, stamp, whoosh, tick for checklists, sting for the title and reveals. Use volumes of 0.3–0.6.

**Gotchas (each one has already caused a bug):**
- Fonts lack some glyphs (→ ÷ ≈ ✓ ◀). Use plain text or drawn `Tick`/`Cross` instead.
- Apostrophes inside single-quoted JS strings break compilation, so use double quotes. Write `&apos;` inside JSX text, and `{"<<"}` for angle brackets.
- Text overflowing cards is the most common layout bug. Big numbers at size 84+ need cards 700px+ wide.
- Don't put same-coloured items on same-coloured backgrounds (a red cup on a red panel, a yellow hoodie on yellow).
- `pkill -f "remotion render"` can kill your own shell, because the pattern matches the command. Find PIDs another way.

**Verify before rendering:** run `npx tsc -p .`, then render ~15–19 stills across the episode (`npx remotion still EpNN out/s.png --frame=N`), tile them into a contact sheet with PIL, and **look at it**. Fix overlaps and overflow, then re-check only the fixed frames.

## 6. Thumbnail

Add `src/epNN/Thumb.tsx` (1280×720), modelled on `references/example_thumb.tsx`:
- a split background (paper on one side, ink or red on the other);
- a shocked Penny about 1.7× scale on the left;
- the key object on the right;
- a 2–3 word headline in Permanent Marker (yellow with an ink stroke), at a size that fits inside 1280px.

Render with `npx remotion still EpNNThumb …png`, view it, and fix overflow and contrast.

## 7. Render and deliver

```bash
cd youtube_channel/animation && <skill>/scripts/finish_video.sh EpNN ../episodes/epNN_slug epNN
```
Run it in the background, since the render takes several minutes. It produces `epNN_1080p.mp4` (normalised to −14 LUFS, usually 45–55 MB, under GitHub's 100 MB limit) and `epNN_preview_720p.mp4` (under the 30 MB chat-upload limit).

Then verify: run `ffprobe` for duration and streams, `ffmpeg -af ebur128` for integrated loudness (≈ −14 LUFS), and grab 3 frames to view. Send the 720p preview to the user with the file-sending tool, and give them a GitHub link to the 1080p file. Be honest that you've spot-checked rather than watched the whole video.

## 8. Captions and upload kit

```bash
python3 <skill>/scripts/make_srt.py animation/timing_epNN.json episodes/epNN/epNN_captions.srt
```
Write `UPLOAD_KIT.md` following `references/example_upload_kit.md`. It should include:
- the title plus 2 backups to test;
- a description with chapters taken from the scene start times (the first must be 0:00, with at least 3 chapters of 10s or more), a sources list, a "not financial advice" line and hashtags;
- tags, settings (Education, not made for kids, upload the captions, AI-voice disclosure note), a pinned comment, and 3 Shorts with timestamps;
- which position the episode takes in the upload order.

## 9. Commit

Commit everything to the working branch: script, voiceover, timing, code, thumbnail, captions, kit and both MP4s. Push with retries. `out/` and raw renders stay gitignored. Tell the user what's done, what you verified, and the decisions still open (upload order, anything unverifiable you cut).

## Bundled files

- `scripts/kokoro_vo.py`: free TTS plus exact sentence timings.
- `scripts/align_timing.py`: timings for an external voiceover, estimated from pauses.
- `scripts/synth_audio.py`: 25 original SFX plus a lo-fi music bed, made with numpy only.
- `scripts/extract_vo.sh`: pulls the narration out of SCRIPT.md.
- `scripts/make_srt.py`: builds captions from the timing file.
- `scripts/finish_video.sh`: render, loudness, 1080p and 720p outputs.
- `assets/template/`: Remotion project (package.json pinned to remotion 4.0.535 and roughjs 4.6.6), the lib, fonts and an empty Root.
- `references/example_episode.tsx`, `example_thumb.tsx`, `example_script.md`, `example_upload_kit.md`: the full credit-card episode as a worked example.
