# Money Mechanics Animation Pipeline ($0)

Episodes are hand-drawn-style animations rendered from code:
- **[Remotion](https://github.com/remotion-dev/remotion)** turns React components into MP4 video. Free for individuals and companies of up to 3 people; see the [licence](https://www.remotion.dev/license).
- **[rough.js](https://github.com/rough-stuff/rough)** (MIT) gives every shape a sketchy, hand-drawn line.

On top of those, the code adds:
- **draw-on strokes:** lines animate as if being drawn
- **line boil:** each shape is re-sketched every 5 frames, the classic hand-animated wobble
- **hachure fills:** shading made of hand-drawn hatching lines

Fonts (bundled in `public/fonts`, SIL Open Font License): Patrick Hand and Permanent Marker.

## Layout
```
src/lib/rough.tsx       hand-drawn primitives (R shape, T text, G group), palette, timing helpers
src/lib/characters.tsx  Penny (mascot), the shopkeeper/broker, guitar
src/lib/props.tsx       reusable props: pawn shop, cash, coin, jar, car, phone, cards, gears, ticks, price tags, bubbles
src/ep01/Ep01.tsx       Episode 1 scenes, cued to voiceover timings
src/ep01/Thumb.tsx      Episode 1 thumbnail
timing.json             sentence-level voiceover timings (auto-aligned from audio pauses)
public/ep01_vo.mp3      Episode 1 voiceover
```

## Commands
```bash
npm install
npx remotion studio                                  # live preview / scrub in the browser
npx remotion render Ep01 out/ep01.mp4                # full episode
npx remotion still Ep01Thumb out/ep01_thumbnail.png  # thumbnail
```
In the cloud container, Chrome must be pointed at the pre-installed headless shell:
`--browser-executable=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell`

## Making a new episode
1. Final script → voiceover MP3 into `public/`.
2. Generate `timing.json` for it. The alignment script in the session notes matches sentence ends to pauses in the audio. If Whisper is available, word-level timings are even better.
3. Copy `src/ep01/` to `src/epNN/` and rewrite the scenes. Reuse Penny, the props and the palette, and add only the new props the story needs.
4. Register the composition in `src/Root.tsx`, preview in Studio, then render.

## Sound design (original, $0)
`scripts/synth_audio.py` generates every sound from scratch with sine waves and noise, so there are no samples, no licences and no Content ID claims:
- **Music:** `music_lofi.mp3`, an 84 bpm lo-fi loop (Fmaj7 / Em7 / Dm7 / Cmaj7) with soft drums and vinyl crackle.
- **25 sound effects:** cha-ching, coin, pop, whoosh, stamp, record scratch, ding, tick, beep, buzzer, paper slap, bloop, riser, card flip, gasp, rewind, hum, neon buzz, gear whirr, car sputter, plink, clock, and two stings.

```bash
python scripts/synth_audio.py public/sfx 257   # needs numpy; last arg = music length in seconds
```
Cues live in the `SFX` table in `src/ep01/Ep01.tsx`. The music bed sits at 0.14 volume, drops out for the beat before "the house wins", and swells on the end screen.

**Final loudness:** normalise the render to YouTube's −14 LUFS:
```bash
ffmpeg -i out/ep01_raw.mp4 -c:v copy -af loudnorm=I=-14:TP=-1:LRA=11 -c:a aac -b:a 192k -ar 48000 out/ep01.mp4
```
