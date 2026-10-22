"""s07 · GRANDMOTHER (13.0 s): the clearing at night (CLEARING_SET, era "web"). The spider
comes down around the girl, drops, charges; she backs away and falls; the wolf leaps.

IN (flatten from s06's Bass hood grid): static wide Camera(1180, 560, 0.45) for t <= 1.0;
    she stands under the hood tree at x 1480 facing right, looking up at the hoods.
OUT (hard cut on action into s08, which continues the same performance on this clock).
"""
import math

from engine.timing import Cue
from films.red import sets as S
from films.red.scenes import _lib_s04_s08 as L

C = S.CLEARING_SET
MOOD = L.CL_MOOD
T7 = L.T7

_CAM = L.CamPath([
    (-0.5, 1180.0, 560.0, 0.45),
    (1.0, 1180.0, 560.0, 0.45),
    (3.9, 1330.0, 600.0, 0.50),
    (5.8, 1440.0, 860.0, 0.68),
    (6.3, 1440.0, 870.0, 0.68),
    (7.2, 1380.0, 880.0, 0.62),
    (9.3, 1150.0, 880.0, 0.60),
    (13.0, 960.0, 880.0, 0.75),
])
T_IMPACT = 6.645            # the spider's body lands (drop)


def cam(t):
    c = _CAM(t)
    k = t - T_IMPACT
    if 0.0 <= k < 1.2:
        amp = 4.0 * math.exp(-k / 0.22)
        c = c.shaken(t, amp=amp, rot_amp=0.0, freq=9.0, seed=7)
    return c


def haze(t):
    """Mist rolling in between the cottage and the action (lifts the black cottage off the
    wolf and the girl); none at the opening, for the flatten handoff."""
    return 0.38 * L.ss(2.5, 7.0, t)


def render(f, t, T):
    f.set_camera(cam(t))
    C.draw_back(f, MOOD, era="web", t=t)
    C.draw_plane(f, MOOD, era="web", t=t)
    hz = haze(t)
    if hz > 0.0:
        f.haze(MOOD.mist, hz, y1=1480.0, feather=260.0, x0=-760.0, x1=1060.0, tex=0.6, tex_scale=0.8,
               scroll=(12.0, -2.0), seed=5)
    sp, g, w = L.cl_spider(), L.cl_girl(), L.cl_wolf()
    grip, ang, front = L.cl_basket(t)
    with f.layer() as c:
        if t >= T7["desc"]:
            sp.draw(f, t, c, eye_scale=1.6)
        if t >= 10.0:
            w.draw(f, t, c)
        if not front:
            L.draw_basket(c, grip, ang, f.pal.ink)
        g.draw(f, t, c)
        if front:
            L.draw_basket(c, grip, ang, f.pal.ink)
    C.draw_front(f, MOOD, era="web", t=t)


def cues(T):
    return [
        Cue(T.at("Grandmother"), "silk thread creak, high", gain_db=-6),
        Cue(T.at("child") - 0.3, "spider leg tips touching down in snow, one by one", gain_db=-4, dur=0.9),
        Cue(T7["drop"] + 0.25, "heavy drop thud, snow burst", gain_db=-2),
        Cue(T7["charge"], "spider charge: rattling legs, hiss", gain_db=-1, dur=0.8),
        Cue(T7["sit"], "girl falls in snow", gain_db=-6),
        Cue(T7["leap"] - 0.25, "wolf snarl and leap", gain_db=0, pan=-0.4),
    ]
