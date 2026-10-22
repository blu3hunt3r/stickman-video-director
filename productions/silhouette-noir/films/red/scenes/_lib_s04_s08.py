"""Shared code for RED s04 THE WOLF, s07 GRANDMOTHER and s08 FIRE.

    CamPath           camera keys [(t, x, y, zoom), ...]: monotone cubic per channel (zoom in
                      log space), eased at the first and last key, holds outside them
    look_girl()       the girl in her hood (the same look as s02-s06: cast.red(), bob hair)
    draw_basket()     the basket with its cloth (as s02/s03 carry it)
    Steps             hand-planted footsteps for moves the gait engine does not do (backing
                      away, stumbles): feet plant exactly, the pelvis rides between them
    snow()            falling snow in the mood's light

Everything is a pure function of t; Actors and creatures are built once per process.
"""
import bisect
import math
from functools import lru_cache

import numpy as np

from engine import atmos, draw
from engine import figure as F
from engine.core import clamp, ease, lerp, smoothstep, hash01, noise1
from engine.frame import Camera
from engine.motion import foot_ik, SOLE_U
from films.red import cast
from films.red import sets as S

GIRL = cast.RED_GIRL
GH = GIRL.height                       # 380 px
RED = S.HOOD_RED
D2R = math.pi / 180.0


# ----------------------------------------------------------------------------- small math
def k(t, t0, dur, e="inout"):
    """Eased 0..1 progress of a move that starts at t0 and lasts dur."""
    if dur <= 0:
        return 1.0 if t >= t0 else 0.0
    return ease(e, clamp((t - t0) / dur))


def ss(e0, e1, x):
    return smoothstep(e0, e1, x)


def bump(t, t0, t1, fin=0.25, fout=0.25):
    """0..1 envelope: up over fin before t0, down over fout after t1."""
    if t <= t0 - fin or t >= t1 + fout:
        return 0.0
    a = ss(t0 - fin, t0, t) if fin > 0 else 1.0
    b = 1.0 - ss(t1, t1 + fout, t) if fout > 0 else 1.0
    return min(a, b)


def keys(t, ks):
    """Piecewise eased value: ks = [(t, v), (t, v, ease), ...] (ease applies to the segment
    arriving at that key). Holds outside."""
    if t <= ks[0][0]:
        return ks[0][1]
    for i in range(1, len(ks)):
        if t <= ks[i][0]:
            a, b = ks[i - 1], ks[i]
            e = b[2] if len(b) > 2 else "inout"
            return lerp(a[1], b[1], ease(e, (t - a[0]) / max(b[0] - a[0], 1e-9)))
    return ks[-1][1]


# ----------------------------------------------------------------------------- camera
class CamPath:
    """Camera keys [(t, x, y, zoom), ...] -> Camera(t). Monotone cubic (Fritsch-Carlson) per
    channel (x, y, log zoom): no overshoot, continuous velocity, at rest at the first and
    last key. Holds outside the keys."""

    def __init__(self, keys_):
        ks = sorted(keys_, key=lambda q: q[0])
        self.t = np.array([q[0] for q in ks], float)
        self.v = [np.array([q[1] for q in ks], float), np.array([q[2] for q in ks], float),
                  np.log(np.array([q[3] for q in ks], float))]
        self.m = [self._tangents(self.t, v) for v in self.v]

    @staticmethod
    def _tangents(t, v):
        n = len(t)
        m = np.zeros(n)
        if n < 3:
            return m
        d = np.diff(v) / np.maximum(np.diff(t), 1e-9)
        for i in range(1, n - 1):
            if d[i - 1] * d[i] > 0:
                h0, h1 = t[i] - t[i - 1], t[i + 1] - t[i]
                w1, w2 = 2 * h1 + h0, h1 + 2 * h0
                m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
        return m

    def _eval(self, j, t):
        T, V, M = self.t, self.v[j], self.m[j]
        if t <= T[0]:
            return float(V[0])
        if t >= T[-1]:
            return float(V[-1])
        i = int(np.searchsorted(T, t) - 1)
        h = T[i + 1] - T[i]
        u = (t - T[i]) / h
        h00 = 2 * u ** 3 - 3 * u ** 2 + 1
        h10 = u ** 3 - 2 * u ** 2 + u
        h01 = -2 * u ** 3 + 3 * u ** 2
        h11 = u ** 3 - u ** 2
        return float(h00 * V[i] + h10 * h * M[i] + h01 * V[i + 1] + h11 * h * M[i + 1])

    def __call__(self, t):
        return Camera(self._eval(0, t), self._eval(1, t), math.exp(self._eval(2, t)))


def cam_for(point, screen, zoom):
    """Camera (zoom) that puts world `point` at screen position `screen` (frame px)."""
    return Camera(point[0] - (screen[0] - 540.0) / zoom, point[1] - (screen[1] - 960.0) / zoom, zoom)


def to_screen(cam, p, par=1.0):
    """World (layer) point -> frame px through the parallax camera (no rotation)."""
    c = cam.parallax(par) if par != 1.0 else cam
    return ((p[0] - c.x) * c.zoom + 540.0, (p[1] - c.y) * c.zoom + 960.0)


# ----------------------------------------------------------------------------- the girl
def look_girl(**opts):
    """The girl in her hood (cast.red(); a bob under the hood), as in s02-s06."""
    lk = cast.red()
    lk.hair = "bob"
    lk.opts.update(opts)
    return lk


BASKET_SIZE = 0.82


def draw_basket(ctx, grip, angle, ink, size=BASKET_SIZE, cloth=True, items=("lantern",)):
    """The basket hanging from `grip` (world), rotated `angle` degrees, with a cloth over it
    (the lantern's ring peeking out at the back). One ink silhouette (as in s02/s03)."""
    b = S.Basket(size)
    b.draw(ctx, grip, angle, items=items, ink=ink)
    if cloth:
        s = size
        a = math.radians(angle)
        ca, sa = math.cos(a), math.sin(a)

        def T(p):
            return (grip[0] + p[0] * ca - p[1] * sa, grip[1] + p[0] * sa + p[1] * ca)
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


def near_side(sk):
    """'L' or 'R': the limb nearer the camera for this skeleton's facing."""
    return "R" if math.cos(sk.pose.yaw * D2R) >= 0 else "L"


# ----------------------------------------------------------------------------- hand-planted steps
class Steps:
    """Footsteps planted by hand: plants = [(t_land, side, x), ...] in time order, plus the
    starting feet {L: x, R: x}. Each foot lifts `swing` seconds before it lands (heel/toe
    roll kept simple: flat plants, toe-led swing). Used for backing away (the body faces
    one way while the feet step the other), stumbles and shuffles - things the gait engine
    does not plan. Returns per-foot (ankle, pitch, toe, planted) like motion._Walk.foot."""

    def __init__(self, ground, H, feet0, plants, swing=0.32, lift=0.05, facing=1.0):
        self.g = ground
        self.H = H
        self.d = 1.0 if facing >= 0 else -1.0
        self.swing = swing
        self.lift = lift
        self.track = {s: [(-1e9, feet0[s], None)] for s in ("L", "R")}
        for p in plants:
            t, s, x = p[0], p[1], p[2]
            sw = p[3] if len(p) > 3 else swing
            self.track[s].append((t, x, sw))
        self.ts = {s: [q[0] for q in self.track[s]] for s in ("L", "R")}

    def foot(self, s, t):
        tr = self.track[s]
        i = bisect.bisect_right(self.ts[s], t) - 1
        # is the next plant's swing under way?
        if i + 1 < len(tr):
            tn, xn, sw = tr[i + 1]
            if t > tn - sw:
                x0 = tr[i][1]
                u = clamp((t - (tn - sw)) / sw)
                e = u - math.sin(2 * math.pi * u) / (2 * math.pi)
                x = lerp(x0, xn, e)
                (a0, p0) = foot_ik(x, 0.0, "flat", self.d, self.H, self.g)
                h = self.lift * self.H * math.sin(math.pi * u) * clamp(abs(xn - x0) / (0.12 * self.H), 0.35, 1.0)
                return (a0[0], a0[1] - h), p0 - 10.0 * math.sin(math.pi * u), 8.0 * math.sin(math.pi * u), False
        x = tr[i][1]
        (a, p) = foot_ik(x, 0.0, "flat", self.d, self.H, self.g)
        return a, p, 0.0, True

    def planted_x(self, s, t):
        """x of foot s's current (or last) plant at time t."""
        i = bisect.bisect_right(self.ts[s], t) - 1
        return self.track[s][i][1]


def snow(f, mood, density=1.0, wind=22.0, gust=10.0, t=None, seed=0, lit=None, alpha=1.0, size=1.0):
    """Falling snow in the mood's light (three depth bands, near flakes blurred)."""
    if density <= 0.003:
        return 0
    col = S.mix(mood.snow, S.SNOW, 0.55) if mood.night > 0.5 else S.mix(mood.snow, S.SNOW, 0.85)
    return atmos.snow(f, density=density, wind=wind, gust=gust, t=t, seed=seed, color=col, alpha=alpha,
                      lit=lit, lit_color=mood.lamp, size=size)


# ----------------------------------------------------------------------------- s07 opening (s06 handoff)
S07_CAM0 = Camera(1180.0, 560.0, 0.45)          # s07's camera for t <= 1.0 (static)
S07_GIRL_X = 1480.0                             # where she stands at s07 t = 0 (facing right)
LAYER_PAR = {"plane": 1.0, "web": 1.0, "near": 0.76, "mid": 0.56, "far": 0.38, "ghost": 0.22}
# hoods that survive the Bass flatten as red at s07 t = 0 (checked on the flattened frame):
# every plane/web hood and most near ones; mid hoods are mostly fogged pink-grey (7 of 34
# stay red), far/ghost hoods never
_S07_RED_LAYERS = ("plane", "web", "near")


def s07_hood_targets(t=0.0, cam=None, layers=_S07_RED_LAYERS):
    """Screen positions (1080x1920 frame px) of the red hoods in s07's frame at time t:
    [dict(id, layer, x, y, h)] - x, y = the hood's centre, h = its height on screen.
    The s06 Bass grid lands on these (s06 -> s07 is a flatten transition)."""
    C = S.CLEARING_SET
    cam = cam or S07_CAM0
    by_id = {h["id"]: h for h in C.hoods.items}
    out = []
    for hid, layer, x, y in C.hood_positions(t):
        if layer not in layers:
            continue
        c = cam.parallax(LAYER_PAR[layer])
        sx, sy = (x - c.x) * c.zoom + 540.0, (y - c.y) * c.zoom + 960.0
        h = by_id[hid]["size"] * c.zoom
        if 10 < sx < 1070 and 10 < sy + 0.5 * h < 1910:
            out.append(dict(id=hid, layer=layer, x=round(sx, 1), y=round(sy + 0.5 * h, 1), h=round(h, 1)))
    return out
