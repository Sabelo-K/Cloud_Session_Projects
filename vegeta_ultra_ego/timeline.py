"""Shared timing for the Ultra Ego motion sketch (60 s).

Both the visuals (render.py) and the score (audio.py) read these event times so
every camera punch, flash and drum hit lands on the same frame.  The whole piece
sits on a 120 bpm grid (one beat = 0.5 s, one bar = 2 s).

Story, by act
  A   0 - 9   wide shot, battered Vegeta is drawn into a ruined city
  B   9 - 17  close-up, head lifts, eyes open
  C  17 - 27  pain becomes power: every hit he absorbs makes the aura grow
  D  27 - 35  build-up: accelerating drum roll, quick cuts, then a blackout
  E  35 - 49  ULTRA EGO: reveal, title slam, wide shot, close-ups, the charge
  F  49 - 60  impact, pull-back, end card, fade
"""

FPS = 24
DUR = 60.0
SR = 44100


def _heartbeats():
    out, t = [], 2.0
    while t < 17.0:
        out.append(t)
        k = (t - 2.0) / 15.0
        t += 1.3 + (0.6 - 1.3) * k          # heart speeds up as the power builds
    return out


def _roll():
    out, t, iv = [], 27.0, 0.5
    while t < 34.5:
        out.append(t)
        t += iv
        iv = max(0.085, iv * 0.94)           # accelerating taiko roll
    return out


HEART = _heartbeats()                                   # lub-dub, 2 s - 17 s
HITS = [17.5, 19.5, 21.0, 22.2, 23.0, 23.5, 24.0, 24.5, 24.75, 25.0, 25.25, 25.5, 25.75]
HIT_DIR = [1 if i % 2 == 0 else -1 for i in range(len(HITS))]   # which side the blow lands
ROLL = _roll()                                          # build-up roll, 27 s - 34.5 s
SILENCE = 34.55                                         # everything drops out
BOOM = 35.0                                             # the transformation
BEATS = [35.0 + 0.5 * k for k in range(28)]             # driving section, 35 s - 48.5 s
TITLE_SLAM = 37.0                                       # "ULTRA EGO"
CHARGE = 47.0                                           # he charges the camera
IMPACT = 49.0                                           # blow lands, resolve begins
END_CARD = 51.0                                         # "VEGETA" appears
FADE_START = 58.0                                       # fade to black
