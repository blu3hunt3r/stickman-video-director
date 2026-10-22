"""Shared code for RED s02 THE HOOD, s03 THE PATH, s05 DEEP SNOW and s06 RED HOODS.

    camera paths      CamPath([(t, x, y, zoom), ...]): C1-smooth, eased ends, zoom in log space
    the girl          looks (hood up / down + the hood being pulled up), the basket in her
                      hand, the walk that s02 hands to s03 (one Actor definition, offset in
                      time and space, so the dissolve between them is a perfect match)
    weather           falling snow in the mood's colours

Everything is a pure function of t (Actors and pendulums are cached per process).
"""
import math
from functools import lru_cache

import numpy as np

from engine import atmos, costume, draw
from engine import figure as F
from engine.core import clamp, ease, lerp, smoothstep
from engine.frame import Camera
from engine.motion import Actor, GAITS
from films.red import cast
from films.red import sets as S

GIRL = cast.RED_GIRL
GH = GIRL.height                       # 380 px
RED = S.HOOD_RED


# ----------------------------------------------------------------------------- small math
def k(t, t0, dur, e="inout"):
    """Eased 0..1 progress of a move that starts at t0 and lasts dur."""
    if dur <= 0:
        return 1.0 if t >= t0 else 0.0
    return ease(e, (t - t0) / dur)


def ss(e0, e1, x):
    return smoothstep(e0, e1, x)


def bump(t, t0, t1, fin=0.25, fout=0.25):
    """0..1 envelope: up over fin after t0, down over fout before t1."""
    if t <= t0 - fin or t >= t1 + fout:
        return 0.0
    a = ss(t0 - fin, t0, t) if fin > 0 else 1.0
    b = 1.0 - ss(t1, t1 + fout, t) if fout > 0 else 1.0
    return min(a, b)


# ----------------------------------------------------------------------------- camera
class CamPath:
    """Camera keys [(t, x, y, zoom), ...] -> Camera(t). Monotone cubic (Fritsch-Carlson)
    through the keys per channel (x, y, log zoom): no overshoot, continuous velocity, zero
    velocity at the first and last key (eased start and stop). Holds outside the keys."""

    def __init__(self, keys):
        ks = sorted(keys, key=lambda q: q[0])
        self.t = np.array([q[0] for q in ks], float)
        self.v = [np.array([q[1] for q in ks], float), np.array([q[2] for q in ks], float),
                  np.log(np.array([q[3] for q in ks], float))]
        self.m = [self._tangents(self.t, v) for v in self.v]

    @staticmethod
    def _tangents(t, v):
        n = len(t)
        if n < 2:
            return np.zeros(n)
        d = np.diff(v) / np.maximum(np.diff(t), 1e-9)
        m = np.zeros(n)
        for i in range(1, n - 1):
            if d[i - 1] * d[i] <= 0:
                m[i] = 0.0
            else:
                h0, h1 = t[i] - t[i - 1], t[i + 1] - t[i]
                w1, w2 = 2 * h1 + h0, h1 + 2 * h0
                m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
        return m

    def _eval(self, j, t):
        T, V, M = self.t, self.v[j], self.m[j]
        if t <= T[0]:
            return V[0]
        if t >= T[-1]:
            return V[-1]
        i = int(np.searchsorted(T, t) - 1)
        h = T[i + 1] - T[i]
        u = (t - T[i]) / h
        h00 = 2 * u ** 3 - 3 * u ** 2 + 1
        h10 = u ** 3 - 2 * u ** 2 + u
        h01 = -2 * u ** 3 + 3 * u ** 2
        h11 = u ** 3 - u ** 2
        return h00 * V[i] + h10 * h * M[i] + h01 * V[i + 1] + h11 * h * M[i + 1]

    def __call__(self, t):
        return Camera(self._eval(0, t), self._eval(1, t), math.exp(self._eval(2, t)))

    def x(self, t):
        return self._eval(0, t)


def cam_mix(a, b, w):
    """Blend two cameras (zoom geometric)."""
    w = clamp(w)
    return Camera(lerp(a.x, b.x, w), lerp(a.y, b.y, w), a.zoom * (b.zoom / a.zoom) ** w)


def cam_for(point, screen, zoom):
    """Camera (zoom) that puts world `point` at screen position `screen` (frame px)."""
    return Camera(point[0] - (screen[0] - 540.0) / zoom, point[1] - (screen[1] - 960.0) / zoom, zoom)


# ----------------------------------------------------------------------------- the girl's looks
def look_up(**opts):
    """The girl in her hood (cast.red(); a bob under the hood)."""
    lk = cast.red()
    lk.hair = "bob"
    lk.opts.update(opts)
    return lk


# the hood lying bunched on her back (head-local profile/front points; same count and order
# as costume._HOOD so it morphs straight into it: 0..3 the crown/opening edge, 4 the point,
# 8..10 the lower edge, 11..13 the face edge)
_HOOD_DOWN = (
    [(-0.10, 0.12), (-0.34, 0.14), (-0.56, 0.04), (-0.70, -0.16), (-0.76, -0.60), (-0.62, -0.52),
     (-0.52, -0.44), (-0.42, -0.42), (-0.30, -0.40), (-0.12, -0.32), (0.10, -0.22), (0.14, -0.12),
     (0.03, -0.02), (-0.05, 0.07)],
    [(0.0, 0.10), (0.34, 0.06), (0.52, -0.04), (0.56, -0.20), (0.58, -0.40), (0.56, -0.46),
     (0.40, -0.48), (0.0, -0.50), (-0.40, -0.48), (-0.56, -0.46), (-0.58, -0.40), (-0.56, -0.20),
     (-0.52, -0.04), (-0.34, 0.06)])


def _hood_pts(sk, u, flow=0.0):
    """Hood outline (world) at raise u (0 = bunched on the back, 1 = up: costume's hood)."""
    up_p, up_f = costume._HOOD
    dn_p, dn_f = _HOOD_DOWN
    # the crown points travel over the head on an arc (not through the face)
    prof, front = [], []
    for i, ((ax, ay), (bx, by)) in enumerate(zip(dn_p, up_p)):
        e = clamp(u * 1.25 - 0.25 * (i in (10, 11, 12, 13)) * (1 - u))
        x, y = lerp(ax, bx, e), lerp(ay, by, e)
        y += 0.28 * math.sin(math.pi * e) * (1.0 if i <= 7 else 0.3)
        prof.append((x, y))
    for (ax, ay), (bx, by) in zip(dn_f, up_f):
        e = clamp(u)
        front.append((lerp(ax, bx, e), lerp(ay, by, e) + 0.2 * math.sin(math.pi * e)))
    return costume._hm(sk, prof, front, flow=flow)


def look_hood(u, **opts):
    """The girl while her hood goes up (s02): u = 0 down .. 1 up (then use look_up())."""
    if u >= 1.0:
        return look_up(**opts)
    lk = cast.red()
    lk.hood = False
    lk.hair = "bob"
    lk.opts.update(opts)

    def hood(ctx, sk, f, look, u=u):
        pts = _hood_pts(sk, u)
        draw.smooth(ctx, pts, close=True, tension=0.42)
        draw.fill(ctx, RED)
        if u > 0.55 and sk.front > -0.25:      # the face stays ink inside the hood's opening
            face = costume._hm(sk, *costume._FACE)
            draw.smooth(ctx, face, close=True, tension=0.45)
            draw.fill(ctx, look.ink or (f.pal.ink if f is not None else (0, 0, 0)))
    lk.extras = [hood]
    return lk


# ----------------------------------------------------------------------------- the basket
BASKET = S.Basket(0.82)


def draw_basket(ctx, grip, angle, ink, size=0.82, cloth=True):
    """The basket hanging from `grip` (world), rotated `angle` degrees, with a cloth over it
    (the lantern's ring just peeking out at the back). One ink silhouette."""
    b = S.Basket(size)
    b.draw(ctx, grip, angle, items=("lantern",), ink=ink)
    if cloth:
        s = size
        a = math.radians(angle)
        ca, sa = math.cos(a), math.sin(a)

        def T(p):
            return (grip[0] + p[0] * ca - p[1] * sa, grip[1] + p[0] * sa + p[1] * ca)
        # a cloth dome over the rim, one corner hanging over the side
        pts = [(-44 * s, 58 * s), (-30 * s, 42 * s), (-8 * s, 36 * s), (14 * s, 38 * s), (34 * s, 44 * s),
               (45 * s, 56 * s), (40 * s, 60 * s), (24 * s, 56 * s), (-20 * s, 57 * s), (-38 * s, 74 * s),
               (-46 * s, 70 * s)]
        draw.smooth(ctx, [T(p) for p in pts], close=True, tension=0.3)
        draw.fill(ctx, ink)


def basket_hand(sk, side):
    """Where the basket's handle hangs in a hand: a little below the palm."""
    hx, hy = sk.j["hand_" + side]
    fx, fy = sk.j["fingers_" + side]
    return (lerp(hx, fx, 0.35), lerp(hy, fy, 0.35) + 4.0)


# ----------------------------------------------------------------------------- the walk s02 -> s03
WALK = GAITS["child_walk"].but(speed=0.9)
WALK_PX = 0.9 * GH                      # 342 px/s
S02_X0 = S.VILLAGE.door_x + 10.0        # she stands in her mother's doorway
S02_TURN = 9.42                         # turns to the street (0.5 s) ...
S02_GO = 9.92                           # ... and walks to the gate
S03_DT = 15.0                           # s03 time = s02 time - 15
S03_DX = 800.0                          # s03 trail x = s02 street x + 800


def girl_base(dt=0.0, dx=0.0, look=None, ground=None):
    """The girl's base timeline shared by s02 and s03 (times shifted by -dt, x by +dx): she
    stands in the doorway facing left, turns to the street, and walks right for good."""
    g = ground or S.PATH.ground_y
    a = Actor(GIRL, look or look_up(), x=S02_X0 + dx, ground=g, facing=-1, seed=7, name="red")
    a.stand(until=S02_TURN - dt, at=-40.0 - dt)
    a.turn(0.0, dur=0.5, at=S02_TURN - dt, via=90.0)
    a.walk(to=S02_X0 + dx + 9600.0, gait=WALK, at=S02_GO - dt)
    return a


BASKET_SIDE = "R"                       # her right hand: the near hand while she walks right
S02_TAKE = 5.70                         # s02 time the basket is hers (carry from here on)


def carry(a, t0, t1, side=BASKET_SIDE, fade=0.35):
    """Basket carry: the arm bent at the elbow, forearm forward, a firm grip."""
    a.arm(side, t0, t1, fade=fade, sh=18.0, elbow=62.0, abd=9.0, wrist=-8.0, grip=0.9)
    return a


@lru_cache(maxsize=None)
def walk_fit():
    """(x_at(t), v): the girl's mean walking position in s02 time (a line fitted to her
    pelvis over the steady walk): the camera tracks this, not the stride surges."""
    a = girl_base()
    ts = np.linspace(12.0, 24.0, 97)
    xs = np.array([a.root(t)[0] for t in ts])
    v, c = np.polyfit(ts, xs, 1)
    return float(c), float(v)


def walk_x(t):
    """Mean walking x of the girl at s02 time t (steady part only)."""
    c, v = walk_fit()
    return c + v * t


class HandSwing:
    """A pendulum hanging from pivot(t) (a hand): the pivot is sampled at `rate` Hz (one
    skeleton solve per sample), splined for its acceleration and integrated at 240 Hz. Much
    cheaper than physics.Pendulum on a skeleton (which solves 3x per 1/240 s step).
    angle(t): radians from straight down, + swings toward +x (draw a basket at
    -degrees(angle)). Holds 0 before t0 and the last value after t1."""

    def __init__(self, pivot, length, t0, t1, damping=2.2, gravity=900.0, rate=60.0):
        from scipy.interpolate import CubicSpline
        n = int(math.ceil((t1 - t0) * rate)) + 1
        ts = t0 + np.arange(n) / rate
        P = np.array([pivot(float(t)) for t in ts], float)
        sx, sy = CubicSpline(ts, P[:, 0]), CubicSpline(ts, P[:, 1])
        self.dt = 1.0 / 240.0
        m = int(math.ceil((t1 - t0) / self.dt)) + 2
        tt = t0 + np.arange(m) * self.dt
        ax, ay = sx(np.minimum(tt, ts[-1]), 2), sy(np.minimum(tt, ts[-1]), 2)
        th, om = 0.0, 0.0
        out = np.empty(m)
        for i in range(m):
            al = -(gravity * math.sin(th) + ax[i] * math.cos(th) - ay[i] * math.sin(th)) / length - damping * om
            om += al * self.dt
            th += om * self.dt
            out[i] = th
        self.t0, self.t1, self._th = t0, t1, out

    def angle(self, t):
        f = (min(max(t, self.t0), self.t1) - self.t0) / self.dt
        i = min(max(int(f), 0), len(self._th) - 2)
        u = f - i
        return float(self._th[i] * (1 - u) + self._th[i + 1] * u)


@lru_cache(maxsize=None)
def basket_pendulum(dt=0.0, dx=0.0):
    """Basket swing for the s02/s03 walk (pivot: the carrying hand), from the turn to the
    street (s02 9.42) for 26 s. angle(t) in radians (+ toward +x)."""
    a = girl_base(dt, dx)
    carry(a, S02_TAKE - dt, 60.0 - dt, fade=0.0)

    def pivot(t):
        return basket_hand(a.skeleton(t), BASKET_SIDE)
    return HandSwing(pivot, length=60.0, t0=S02_GO - dt - 0.5, t1=S02_GO - dt + 26.0, damping=2.2, gravity=900.0)


# ----------------------------------------------------------------------------- weather
def snow(f, mood, density=1.0, wind=22.0, gust=10.0, t=None, seed=0, lit=None, alpha=1.0, size=1.0):
    """Falling snow in the mood's light (three depth bands, near flakes blurred)."""
    if density <= 0.003:
        return 0
    col = S.mix(mood.snow, S.SNOW, 0.55) if mood.night > 0.5 else S.mix(mood.snow, S.SNOW, 0.85)
    return atmos.snow(f, density=density, wind=wind, gust=gust, t=t, seed=seed, color=col, alpha=alpha,
                      lit=lit, lit_color=mood.lamp, size=size)


# ----------------------------------------------------------------------------- figure pieces
def draw_arm(ctx, sk, side, look, ink):
    """Re-draw one arm and hand of a solved figure (to put a near hand over another
    figure drawn after it)."""
    F._arm_path(ctx, sk, side, look)
    draw.fill(ctx, ink)
    F._hand(ctx, sk, side, look, sk.pose.arms[side].get("grip", 0.3))
    draw.fill(ctx, ink)


def near_side(sk):
    """'L' or 'R': the arm/leg nearer the camera for this skeleton's facing."""
    return "R" if math.cos(sk.pose.yaw * math.pi / 180.0) >= 0 else "L"
