"""s07 · GRANDMOTHER (13.0 s): the clearing at night (CLEARING_SET, era "web"). The spider
comes down around the girl, drops, charges; she backs away and falls; the wolf leaps.

IN (flatten from s06's Bass hood grid): static wide Camera(1180, 560, 0.45) for t <= 1.0;
    she stands under the hood tree at x 1480 facing right, looking up at the hoods.
"""
import math
from functools import lru_cache

from engine.core import clamp, lerp
from engine.creatures import Spider, Wolf
from engine.motion import Actor
from engine.timing import Cue
from films.red import sets as S
from films.red.scenes import _lib_s04_s08 as L

C = S.CLEARING_SET
G = S.CLEARING.ground_y
MOOD = S.mood_mix(S.DUSK, S.NIGHT, 0.55)
GX = L.S07_GIRL_X

# beats (scene seconds; narration: Grandmother 1.86, child 3.61, alone 5.69)
T_DESC = 1.5            # the spider starts down out of the canopy
T_BACK = 5.95           # she starts to back away
T_DROP = 6.3            # it lets go and drops
T_CHARGE = 8.3
T_FALL = 8.45           # she falls (bottom down at T_SIT)
T_SIT = 8.85
T_LEAP = 12.6           # the wolf flies over her
SP_X = 1690.0


@lru_cache(maxsize=None)
def spider():
    sp = Spider(x=SP_X, ground=G, facing=-1, size=500.0, seed=7)
    sp.at(T_DESC).descend(dur=3.9, top=-2600.0, frm=-1700.0, eyes_at=0.86, pitch0=-25.0, hang=1150.0,
                          low=760.0, touch=(0.41, 0.60), unfold=(0.04, 0.42), reach_down=1.0, settle=0.5)
    sp.stand(dur=0.3)
    sp.at(T_DROP).drop(dur=0.7)
    sp.stand(dur=0.3)
    sp.creep(to=1580.0)
    sp.at(T_CHARGE).charge(to=1330.0)
    sp.threat(dur=4.6)
    return sp


@lru_cache(maxsize=None)
def wolf():
    w = Wolf(x=-150.0, ground=G, facing=1, size=330.0, seed=1)
    w.at(10.6).trot(to=330.0).stalk(to=560.0).crouch(dur=0.25).leap(to=1450.0, height=470.0)
    return w


@lru_cache(maxsize=None)
def retreat():
    a = _girl_base()
    o = 0.022 * L.GH
    feet0 = {"L": GX + o, "R": GX - o}
    steps = [(6.25, "R", GX - 70.0), (6.55, "L", GX - 190.0), (6.80, "R", GX - 290.0),
             (7.05, "L", GX - 345.0), (7.60, "R", GX - 430.0), (8.05, "L", GX - 500.0),
             (8.38, "R", GX - 585.0, 0.22)]
    xs = GX - 650.0
    sit = [(T_SIT, "L", xs + 120.0), (T_SIT, "R", xs + 95.0),
           (9.7, "L", xs + 70.0), (9.95, "R", xs + 45.0), (10.9, "L", xs + 10.0), (11.15, "R", xs - 15.0)]
    scoot = [(T_SIT, xs), (9.55, xs), (9.9, xs - 45.0), (10.75, xs - 45.0), (11.1, xs - 90.0)]
    lean = [(T_BACK, 0.0), (6.4, -9.0, "out"), (7.2, -4.0), (8.3, -6.0), (8.6, -38.0, "in"), (T_SIT, -45.0),
            (9.2, -22.0, "out"), (12.0, -24.0), (12.35, -34.0, "out3")]
    return L.Retreat(a, T_BACK, GX, feet0, 1.0, steps, (T_FALL, T_SIT, xs), sit, scoot, lean)


def _girl_base():
    return Actor(L.GIRL, L.look_girl(), x=GX, ground=G, facing=1, seed=7, name="red")


@lru_cache(maxsize=None)
def girl():
    a = _girl_base()
    R = retreat()
    a.stand(until=T_BACK, at=-1.0)
    a.free(dur=14.0 - T_BACK, path=R.path, pose=R.pose, at=T_BACK, blend=0.3)
    sp = spider()
    eye = lambda t: sp.eye_pos(t)[0]
    a.look_at(-1.0, 1.95, (1720.0, 420.0), fade=0.1, amount=0.8)
    a.look_at(2.15, 3.45, eye, fade=0.3, amount=0.9)
    a.look_at(3.55, 3.95, (900.0, 1540.0), fade=0.2)
    a.look_at(4.1, 4.5, (2150.0, 1540.0), fade=0.2)
    a.look_at(4.7, 14.0, eye, fade=0.3)
    # the basket: carried on the far (left) arm, then clutched to her chest
    a.arm("L", -1.0, 3.55, fade=0.3, sh=18.0, elbow=62.0, abd=9.0, wrist=-8.0, grip=0.9)
    a.arm("L", 3.75, 14.0, fade=0.3, sh=34.0, elbow=112.0, abd=12.0, wrist=-20.0, grip=0.95)
    a.arm("R", 3.85, T_FALL, fade=0.3, sh=40.0, elbow=95.0, abd=14.0, wrist=-10.0, grip=0.8)
    # falling: the near hand goes back to the snow
    a.reach("R", T_FALL + 0.15, 11.95, lambda t: (a.root(t)[0] - 0.17 * L.GH, G(a.root(t)[0]) - 6.0), fade=0.2)
    # the shield: near arm up in front of her face as it rears to strike
    a.arm("R", 12.15, 14.0, fade=0.18, sh=128.0, elbow=70.0, abd=10.0, wrist=20.0, grip=0.2)
    a.key("head", [(5.0, 0.0), (5.3, -8.0, "out"), (8.4, -8.0), (8.7, 6.0, "out"), (9.2, -4.0)], mode="add")
    return a


def basket_pose(a, t):
    """(grip, angle, in_front) of the basket at t."""
    sk = a.skeleton(t)
    grip = L.basket_hand(sk, "L")
    w = clamp((t - 3.55) / 0.5)
    ang = lerp(4.0 * math.sin(t * 2.1), -28.0, w)
    return grip, ang, w > 0.5


_CAM = L.CamPath([
    (-0.5, 1180.0, 560.0, 0.45),
    (1.0, 1180.0, 560.0, 0.45),
    (3.9, 1330.0, 560.0, 0.50),
    (5.8, 1450.0, 820.0, 0.66),
    (6.6, 1420.0, 860.0, 0.62),
    (9.3, 1180.0, 860.0, 0.55),
    (13.0, 1150.0, 900.0, 0.60),
])


def cam(t):
    return _CAM(t)


def render(f, t, T):
    f.set_camera(cam(t))
    C.draw_back(f, MOOD, era="web", t=t)
    C.draw_plane(f, MOOD, era="web", t=t)
    sp, g, w = spider(), girl(), wolf()
    grip, ang, front = basket_pose(g, t)
    with f.layer() as c:
        if t >= T_DESC:
            sp.draw(f, t, c, eye_scale=1.6)
        if t >= 10.5:
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
        Cue(T_DROP + 0.25, "heavy drop thud, snow burst", gain_db=-2),
        Cue(T_CHARGE, "spider charge: rattling legs, hiss", gain_db=-1, dur=0.8),
        Cue(T_SIT, "girl falls in snow", gain_db=-6),
        Cue(T_LEAP - 0.25, "wolf snarl and leap", gain_db=0, pan=-0.4),
    ]
