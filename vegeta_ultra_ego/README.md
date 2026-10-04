# Vegeta — Ultra Ego (motion sketch tribute)

A 60-second, 1080p/24fps hand-drawn-style animation of Vegeta's first Ultra Ego
transformation, with an original dramatic score. Everything is generated locally from
code (Pillow + numpy + ffmpeg): **no paid service, no stock footage, no samples**.

## Rebuild

```bash
pip install -r requirements.txt          # pillow, numpy (ffmpeg must be on PATH)
python audio.py build/score.wav          # ~7 s   – synthesize the score
python render.py render build/silent.mp4 # ~4 min – 1440 frames, 4 processes
./build.sh                               # mux + loudness-normalise -> ultra_ego_motion_sketch.mp4
python render.py sheet 4 12 36 52        # contact sheet of chosen timestamps (SHEET_OUT=... to choose path)
```

`timeline.py` holds every event time (hits, drum roll, boom, title slam, charge, impact);
both `render.py` and `audio.py` read it, so picture and sound stay locked.

## Story beats (60 s, 120 bpm grid)

| Time | Act | What happens |
|------|-----|--------------|
| 0–9 | A | Ruined city. Battered Vegeta is drawn on, line by line. "BEATEN. BLOODIED. BUT NOT BROKEN." |
| 9–17 | B | Close-up. Head lifts, eyes open. He trained with a God of Destruction... |
| 17–27 | C | Pain becomes power: each blow he absorbs grows the aura (armor is shredded off). |
| 27–35 | D | Accelerating taiko roll, fist, cracking ground, eye close-ups, rapid cuts, blackout. |
| 35–49 | E | **ULTRA EGO**: reveal, title slam, wide shot, close-ups, the charge. |
| 49–60 | F | Impact, pull-back, end card, fade. |

## Character reference used

Collected from web search summaries (the fan-wiki pages themselves were blocked by this
environment's network proxy, so I only kept details that several independent summaries agreed on):

* **Ultra Ego look:** hair turns purple and wilder, eyes bright purple with pronounced pupils,
  **no eyebrows** (swollen brow ridge, a nod to Beerus' cat-like face), sharper cheekbones,
  ripped physique, sinister/crazed grin, purple flame-like aura like a God of Destruction's.
  The armor is shed during the fight.
* **Base look:** upward black flame hair with a widow's peak, thick angry brows, Saiyan armor,
  white gloves and boots.
* **Story:** first shown in the *Dragon Ball Super* manga's Granolah arc against Granolah, after
  training with Beerus; Vegeta absorbs punishment instead of dodging and the more damage he takes,
  the stronger he gets.

Sources: [Ultra Ego (Dragon Ball Universe wiki)](https://dragonballuniverse.fandom.com/wiki/Ultra_Ego),
[Jump Festa '22 colour reveal (Sportskeeda)](https://sportskeeda.com/anime/dragon-ball-super-vegeta-ultra-ego-color-finally-revealed-jump-festa-22),
[Design inspiration (FandomWire)](https://fandomwire.com/i-was-trying-to-capture-beerus-appearance-vegetas-strongest-form-isnt-one-of-akira-toriyamas-super-saiyan-creations-the-artist-was-trying-to-copy-the-god-of-destruction/),
[Debut recap (Legião dos Heróis)](https://www.legiaodosherois.com.br/2021/dragon-ball-super-nova-forma-vegeta-tudo-sobre.html).

## Rights note

Vegeta and Dragon Ball belong to Akira Toriyama / Shueisha / Toei Animation / Bandai Namco.
This is an original, from-scratch fan tribute: the artwork is procedurally drawn here and the
music is synthesized here, so no third-party footage or music is used. Fan content can still draw
a claim on a platform; label it clearly as a fan work.
