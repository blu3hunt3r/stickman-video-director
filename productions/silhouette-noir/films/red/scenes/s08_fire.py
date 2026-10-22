"""s08 · FIRE (17.0 s): the fight in the clearing, the basket, the lantern, the burning web.

IN  hard cut on action from s07: the same performance carries on (s08 t = s07 t - 13.0); the
    wolf, mid-leap, crashes into Grandmother's face.
OUT flash (warm white): the fire flares to white.
"""
import math

from engine.timing import Cue
from films.red import sets as S
from films.red.scenes import _lib_s04_s08 as L

C = S.CLEARING_SET
MOOD = L.CL_MOOD
D = L.S08_DT
F8 = L.F8

_CAM = L.CamPath([
    (0.0, 1050.0, 990.0, 0.95),
    (2.4, 1080.0, 1000.0, 0.95),
    (3.6, 1180.0, 1066.0, 1.35),
    (8.6, 1200.0, 1080.0, 1.45),
    (9.8, 1100.0, 1000.0, 0.95),
    (12.66, 1620.0, 1000.0, 0.80),
    (13.3, 1600.0, 980.0, 0.78),
    (16.5, 1150.0, 450.0, 0.42),
    (17.5, 1130.0, 420.0, 0.40),
])


def cam(t):
    return _CAM(t)


def render(f, t, T):
    t7 = t + D
    f.set_camera(cam(t))
    C.draw_back(f, MOOD, era="web", t=t7)
    C.draw_plane(f, MOOD, era="web", t=t7)
    f.haze(MOOD.mist, 0.38, y1=1480.0, feather=260.0, x0=-760.0, x1=1060.0, tex=0.6, tex_scale=0.8,
           scroll=(12.0, -2.0), seed=5)
    sp, g, w = L.cl_spider(), L.cl_girl(), L.cl_wolf()
    with f.layer() as c:
        sp.draw(f, t7, c, eye_scale=1.3)
        w.draw(f, t7, c)
        g.draw(f, t7, c)
    C.draw_front(f, MOOD, era="web", t=t7)


def cues(T):
    return []
