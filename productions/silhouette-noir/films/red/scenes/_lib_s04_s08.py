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
from engine.motion import Actor, foot_ik, SOLE_U
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


def pchip(xs, ys):
    """Monotone cubic through (xs, ys), at rest at both ends; holds outside."""
    n = len(xs)
    if n == 1:
        return lambda x: ys[0]
    h = [max(xs[i + 1] - xs[i], 1e-9) for i in range(n - 1)]
    dl = [(ys[i + 1] - ys[i]) / h[i] for i in range(n - 1)]
    m = [0.0] * n
    for i in range(1, n - 1):
        if dl[i - 1] * dl[i] > 0:
            w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / dl[i - 1] + w2 / dl[i])

    def f(x):
        if x <= xs[0]:
            return ys[0]
        if x >= xs[-1]:
            return ys[-1]
        i = min(bisect.bisect_right(xs, x) - 1, n - 2)
        u = (x - xs[i]) / h[i]
        u2, u3 = u * u, u * u * u
        return ((2 * u3 - 3 * u2 + 1) * ys[i] + (u3 - 2 * u2 + u) * h[i] * m[i]
                + (-2 * u3 + 3 * u2) * ys[i + 1] + (u3 - u2) * h[i] * m[i + 1])
    return f


def _smax(a, b, k):
    return 0.5 * (a + b + math.sqrt((a - b) ** 2 + k * k))


def reach_y(body, H, x, y, ankles, k=None):
    """Lower the pelvis y (world, y down) so every planted ankle [(ax, ay)] stays in reach."""
    Lmax = (body.thigh + body.shin) * H * 0.985
    for (ax, ay) in ankles:
        dx = ax - x
        if abs(dx) < Lmax:
            y = _smax(y, ay - math.sqrt(Lmax * Lmax - dx * dx), 0.012 * H if k is None else k)
    return y


class Retreat:
    """A free-segment performance (Actor.free(dur, path=R.path, pose=R.pose)): backing away
    on hand-planted steps while facing `d`, a fall onto the bottom, then sitting and scooting
    back on the heels. All times absolute.

        steps     [(t_land, side, x[, swing])] backward steps from feet0 {L: x, R: x}
        fall      (tf0, tf1, x_sit): the fall starts at tf0, the bottom lands at tf1 at x_sit
        sit       [(t_land, side, x)]: the sitting feet's plants (the first two at tf1 put the
                  feet out in front), later ones are the heel pushes of the scoot
        scoot     [(t, x)] pelvis keys while sitting (start with (tf1, x_sit))
        lean      [(t, pitch)] trunk pitch keys (+ forward); crouch while stepping"""

    SIT_H = 0.075

    def __init__(self, A, t0, x0, feet0, d, steps, fall, sit, scoot, lean, crouch=0.03):
        self.A, self.d = A, float(d)
        self.body, self.H, self.g = A.body, A.H, A.g
        self.t0, self.x0 = t0, x0
        self.steps = Steps(A.g, A.H, feet0, steps, facing=d)
        self.tf0, self.tf1, self.x_sit = fall
        self.sitst = Steps(A.g, A.H, dict(L=sit[0][2], R=sit[1][2]), sit[2:], swing=0.28, lift=0.03, facing=d)
        self.sx = pchip([q[0] for q in scoot], [q[1] for q in scoot])
        self.lean = lean
        self.crouch = crouch
        # stepping pelvis x: from the start through the support centre after each landing
        tx, xx = [t0], [x0]
        fx = dict(feet0)
        for st in steps:
            fx[st[1]] = st[2]
            tx.append(st[0] + 0.10)
            xx.append(0.5 * (fx["L"] + fx["R"]) - self.d * 0.03 * self.H)
        self.feet_end = fx
        self.px = pchip(tx, xx)

    # ---------------------------------------------------------------- pieces
    def _step_state(self, t):
        H = self.H
        x = self.px(t)
        feet = {s: self.steps.foot(s, t) for s in ("L", "R")}
        y = self.g(x) - (self.body.hip - 0.006 - self.crouch) * H
        ph = sum(1 for st in self.steps.track["L"][1:] + self.steps.track["R"][1:] if st[0] <= t)
        y = reach_y(self.body, H, x, y, [feet[s][0] for s in feet if feet[s][3]])
        return x, y, feet

    def _sit_feet(self, t):
        out = {}
        for s in ("L", "R"):
            (a, p, toe, planted) = self.sitst.foot(s, t)
            out[s] = (a, 22.0, 0.0, planted)            # heels down, toes up
        return out

    def path(self, t):
        H = self.H
        if t < self.tf0:
            x, y, _ = self._step_state(t)
            return x, y
        xa, ya, _ = self._step_state(self.tf0)
        xs = self.x_sit
        yb = self.g(xs) - self.SIT_H * H
        if t < self.tf1:
            u = (t - self.tf0) / (self.tf1 - self.tf0)
            x = lerp(xa, xs, ease("out", u))
            y = lerp(ya, yb, u * u)
            return x, y
        k_ = t - self.tf1
        x = self.sx(t)
        bounce = -0.035 * H * math.sin(math.pi * clamp(k_ / 0.22)) * (1.0 if k_ < 0.22 else 0.0)
        # a scoot lifts the bottom a little while it slides
        v = (self.sx(t + 0.05) - self.sx(t - 0.05)) / 0.1
        lift = -0.018 * H * clamp(abs(v) / 120.0)
        return x, self.g(x) - self.SIT_H * H + bounce + lift

    def pose(self, t, u):
        H, d = self.H, self.d
        x, y = self.path(t)
        p = F.Pose(x, y, 0.0 if d > 0 else 180.0)
        p.scale = self.A.scale
        if t < self.tf0:
            _, _, feet = self._step_state(t)
            legs = {s: (feet[s][0], feet[s][1], feet[s][2]) for s in feet}
        else:
            sf = self._sit_feet(max(t, self.tf1))
            if t < self.tf1:
                _, _, f0 = self._step_state(self.tf0)
                w = clamp((t - self.tf0) / (self.tf1 - self.tf0))
                e = ease("inout", w)
                legs = {}
                for i, s in enumerate(("L", "R")):
                    a0, a1 = f0[s][0], sf[s][0]
                    kick = 0.10 * H * math.sin(math.pi * clamp(w * 1.15 - 0.1 * i))
                    legs[s] = ((lerp(a0[0], a1[0], e), lerp(a0[1], a1[1], e) - kick),
                               lerp(f0[s][1], sf[s][1], e), 0.0)
            else:
                legs = {s: (sf[s][0], sf[s][1], sf[s][2]) for s in sf}
        for s, (a, pitch, toe) in legs.items():
            p.legs[s] = {"ik": a, "pitch": pitch, "toe": toe, "abd": 3.0}
        p.pitch = keys(t, self.lean)
        br = math.sin(2 * math.pi * t / 1.6)              # fast frightened breathing
        p.spine = [0.8 * br, 0.0, -1.2 * br]
        for s in ("L", "R"):
            p.arms[s].update(sh=4.0, abd=6.0, elbow=20.0, wrist=4.0, grip=0.4)
        return p


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


def s07_hood_targets(t=0.0, cam=None, layers=_S07_RED_LAYERS, girl=True):
    """Screen positions (1080x1920 frame px) of the red hoods in s07's frame at time t:
    [dict(id, layer, x, y, h)] - x, y = the hood's centre, h = its height on screen.
    The s06 Bass grid lands on these (s06 -> s07 is a flatten transition). girl=True adds
    the girl's own red hood and cloak as the first entry (id "girl", layer "girl"; she
    stands still at S07_GIRL_X for t <= 1)."""
    C = S.CLEARING_SET
    cam = cam or S07_CAM0
    by_id = {h["id"]: h for h in C.hoods.items}
    out = []
    if girl:
        # centroid of her red silhouette (hood + cloak), measured on the rendered frame
        gx, gy = S07_GIRL_X - 10.0, float(S.CLEARING.ground_y(S07_GIRL_X)) - 216.0
        out.append(dict(id="girl", layer="girl", x=round((gx - cam.x) * cam.zoom + 540.0, 1),
                        y=round((gy - cam.y) * cam.zoom + 960.0, 1), h=round(253.0 * cam.zoom, 1)))
    for hid, layer, x, y in C.hood_positions(t):
        if layer not in layers:
            continue
        c = cam.parallax(LAYER_PAR[layer])
        sx, sy = (x - c.x) * c.zoom + 540.0, (y - c.y) * c.zoom + 960.0
        h = by_id[hid]["size"] * c.zoom
        if 10 < sx < 1070 and 10 < sy + 0.5 * h < 1910:
            out.append(dict(id=hid, layer=layer, x=round(sx, 1), y=round(sy + 0.5 * h, 1), h=round(h, 1)))
    return out


# ============================================================================= the clearing (s07 + s08)
# One continuous performance on the s07 clock (t7 = s07 time = s08 time + 13.0): the hard cut
# s07 -> s08 is a cut on action, so the spider, the wolf and the girl simply carry on.
S08_DT = 13.0
CL_MOOD = S.mood_mix(S.DUSK, S.NIGHT, 0.55)
CG = S.CLEARING.ground_y

T7 = dict(desc=1.5, back=5.95, drop=6.3, charge=8.3, fall=8.45, sit=8.85, leap=12.6)
SP_X = 1690.0


@lru_cache(maxsize=None)
def cl_spider():
    from engine.creatures import Spider
    sp = Spider(x=SP_X, ground=CG, facing=-1, size=500.0, seed=7)
    sp.at(T7["desc"]).descend(dur=3.9, top=-2600.0, frm=-1700.0, eyes_at=0.86, pitch0=-25.0, hang=1150.0,
                              low=760.0, touch=(0.41, 0.60), unfold=(0.04, 0.42), reach_down=1.0, settle=0.5)
    sp.stand(dur=0.3)
    sp.at(T7["drop"]).drop(dur=0.7)
    sp.stand(dur=0.5)
    sp.creep(to=1630.0)
    sp.at(T7["charge"]).charge(to=1260.0)
    sp.threat(dur=1.6)
    sp.stand(dur=0.5)
    sp.creep(to=1200.0)
    _spider_s08(sp)
    return sp


@lru_cache(maxsize=None)
def cl_wolf():
    from engine.creatures import Wolf
    w = Wolf(x=-200.0, ground=CG, facing=1, size=330.0, seed=1)
    w.at(8.7).stalk(to=250.0, speed=280.0).crouch(dur=0.14).leap(to=1150.0, height=400.0, bite=True, rest=0.15)
    _wolf_s08(w)
    return w


# ----------------------------------------------------------------------------- s08: the fight
# s08 times (t8 = t7 - S08_DT). The spider (facing left) is driven back to the right by the
# wolf, then pins it at W_PIN; the girl smashes the lantern on the anchor strand at
# C.smash_point (1426, 1354), just left of them.
F8 = dict(stabA=1.30, dodge=1.37, knock=2.385, fly=2.42, roll=3.95, bread=5.5, wine=6.3, lantern=8.25,
          pin=9.6, smash=12.66, burnt=13.05)
W_PIN = 1700.0              # the wolf's root when pinned (facing right)
SP_PIN = 2060.0             # the spider's body x while it pins the wolf


def _spider_s08(sp):
    D, G = S08_DT, CG
    sp.threat(dur=D - sp.end, settle=False)              # still reared at the cut
    sp.at(D).recoil(dur=0.8, dist=260.0)                  # 0.0: the wolf crashes into its face
    sp.stand(dur=0.3)
    sp.at(D + 3.1).threat(dur=0.9)                        # the wolf jumps at its face: it rears
    sp.creep(to=1700.0)                                   # backs off, the wolf pressing
    sp.at(D + 5.65).threat(dur=0.75)
    sp.walk(to=1880.0)
    sp.at(D + 7.4).threat(dur=0.95)
    sp.walk(to=SP_PIN)
    sp.at(D + F8["pin"]).pin(dur=D + F8["burnt"] - (D + F8["pin"]), target=W_PIN + 120.0, legs=(0, 4),
                             offsets=(-260.0, 120.0), low=0.66, pitch=-18.0)
    # the stabs (overlays, absolute times): the strike lands 0.385 s after t0
    sp.stab(0, target=(1180.0, G(1180.0)), t0=D + F8["stabA"], hold=1.4)     # where the wolf was
    sp.stab(1, target=(880.0, G(880.0)), t0=D + F8["knock"] - 0.385, hold=0.12)   # at the girl
    sp.stab(1, target=(1150.0, G(1150.0)), t0=D + F8["roll"] - 0.385, hold=0.2)   # by the basket
    sp.stab(0, target=lambda t: cl_wolf().head_points(t)["withers"], t0=D + F8["bread"] - 0.385,
            hold=0.25)
    sp.stab(1, target=(1130.0, G(1130.0)), t0=D + F8["wine"] - 0.385, hold=0.2)
    sp.stab(0, target=(1190.0, G(1190.0)), t0=D + F8["lantern"] - 0.385, hold=0.3)
    return sp


def _wolf_s08(w):
    D = S08_DT
    w.overlay("bite", D + 0.25, 0.55, n=2)               # snaps at its face as it lands
    w.at(D + F8["dodge"]).recoil(dur=0.9, dist=200.0)     # dodges stab A
    w.overlay("bite", D + 1.85, 0.75, n=2)               # bites the stuck leg
    w.at(D + 2.35).crouch(dur=0.2)
    w.lunge(to=1250.0, height=200.0, bite=True, rest=0.2)      # up at its face as it rears
    w.trot(to=1420.0)
    w.at(D + F8["bread"]).recoil(dur=0.8, dist=120.0)     # stab D hits it
    w.crouch(dur=0.2)
    w.lunge(to=1560.0, height=180.0, bite=True, rest=0.2)
    w.trot(to=W_PIN)
    w.snarl(dur=0.3)
    w.at(D + F8["pin"] + 0.25).lie(dur=8.0, head_down=0.0, eyes=1.0, breath=2.2, t_in=0.45)
    w.overlay("snarl", D + F8["pin"] + 0.4, 3.2)
    for tb in (10.4, 11.1, 11.7, 12.3):
        w.overlay("bite", D + tb, 0.45, n=1)
    return w


def _cl_girl_actor():
    return Actor(GIRL, look_girl(), x=S07_GIRL_X, ground=CG, facing=1, seed=7, name="red")


@lru_cache(maxsize=None)
def cl_retreat():
    a = _cl_girl_actor()
    GX = S07_GIRL_X
    o = 0.022 * GH
    feet0 = {"L": GX + o, "R": GX - o}
    steps = [(6.25, "R", GX - 70.0), (6.55, "L", GX - 190.0), (6.80, "R", GX - 290.0),
             (7.05, "L", GX - 345.0), (7.60, "R", GX - 430.0), (8.05, "L", GX - 500.0),
             (8.38, "R", GX - 585.0, 0.22)]
    xs = GX - 650.0
    sit = [(T7["sit"], "L", xs + 120.0), (T7["sit"], "R", xs + 95.0),
           (9.7, "L", xs + 70.0), (9.95, "R", xs + 45.0), (10.9, "L", xs + 10.0), (11.15, "R", xs - 15.0)]
    scoot = [(T7["sit"], xs), (9.55, xs), (9.9, xs - 45.0), (10.75, xs - 45.0), (11.1, xs - 90.0)]
    lean = [(T7["back"], 0.0), (6.4, -9.0, "out"), (7.2, -4.0), (8.3, -6.0), (8.6, -38.0, "in"),
            (T7["sit"], -45.0), (9.2, -22.0, "out"), (12.0, -24.0), (12.35, -34.0, "out3")]
    return Retreat(a, T7["back"], GX, feet0, 1.0, steps, (T7["fall"], T7["sit"], xs), sit, scoot, lean)


class Floor:
    """The girl's floor work in s08, after the Retreat (sitting): knocked flat on her back by
    a blow at tk (the legs kick up, she slides back to x_lie), propped on her hands to watch,
    then getting up (tu0 -> tu1: sit up, tuck the feet, rise over them) to stand at x_up
    facing right. path(t) / pose(t, u) for an Actor.free segment (before tk: the Retreat's)."""

    LIE_H = 0.07

    def __init__(self, R, tk, x_lie, tu0, tu1, x_up, knock=0.5):
        self.R, self.A = R, R.A
        self.H, self.g, self.body, self.d = R.H, R.g, R.body, R.d
        self.tk, self.tl, self.x_lie, self.tu0, self.tu1, self.x_up = tk, tk + knock, x_lie, tu0, tu1, x_up
        H = self.H
        self.xk, self.yk = R.path(tk)
        o = 0.022 * H
        self.f_sit = {s: R.sitst.planted_x(s, tk) for s in ("L", "R")}
        self.f_lie = {"L": x_lie + 0.36 * H, "R": x_lie + 0.31 * H}
        self.f_up = {"L": x_up + o, "R": x_up - o}
        self.y_lie = self.g(x_lie) - self.LIE_H * H
        self.y_stand = self.g(x_up) - (self.body.hip - 0.006) * H
        Tu = tu1 - tu0
        l0 = keys(tk, R.lean)
        self.lean = [(tk, l0), (tk + 0.12, -62.0, "out"), (tk + 0.36, -84.0, "out"), (tk + 0.95, -84.0),
                     (tk + 1.6, -58.0), (tu0, -58.0), (tu0 + 0.30 * Tu, -16.0), (tu0 + 0.55 * Tu, 30.0),
                     (tu0 + 0.8 * Tu, 32.0), (tu1, 5.0)]
        self.curl = [(tk, 0.0), (tk + 0.36, -4.0), (tk + 0.95, -4.0), (tk + 1.6, 7.0), (tu0, 7.0),
                     (tu0 + 0.3 * Tu, 3.0), (tu1, 0.0)]

    def path(self, t):
        if t < self.tk:
            return self.R.path(t)
        H = self.H
        if t < self.tl:
            u = (t - self.tk) / (self.tl - self.tk)
            x = lerp(self.xk, self.x_lie, ease("out", u))
            y = lerp(self.yk, self.y_lie, u) - 0.07 * H * math.sin(math.pi * clamp(u * 1.3))
            return x, y
        if t < self.tu0:
            return self.x_lie, self.y_lie + 0.004 * H * math.sin(2 * math.pi * t / 1.5)
        v = clamp((t - self.tu0) / (self.tu1 - self.tu0))
        x = lerp(self.x_lie, self.x_lie + 0.05 * H, ss(0.3, 0.55, v))
        x = lerp(x, self.x_up, ss(0.5, 0.85, v))
        y = lerp(self.y_lie, self.y_stand, ss(0.58, 1.0, v))
        return x, y

    def pose(self, t, u):
        if t < self.tk:
            return self.R.pose(t, u)
        H, d, g = self.H, self.d, self.g
        x, y = self.path(t)
        p = F.Pose(x, y, 0.0 if d > 0 else 180.0)
        p.scale = self.A.scale
        legs = {}
        if t < self.tl:
            w = clamp((t - self.tk) / (self.tl - self.tk))
            for i, s in enumerate(("L", "R")):
                wi = clamp(w * 1.1 - 0.06 * i)
                fx = lerp(self.f_sit[s], self.f_lie[s], ease("inout", wi))
                (a, pch) = foot_ik(fx, 22.0, "heel", d, H, g)
                kick = 0.20 * H * math.sin(math.pi * clamp(wi * 1.25)) * (1.0 - 0.15 * i)
                legs[s] = ((a[0], a[1] - kick), pch + 20.0 * math.sin(math.pi * wi), 0.0)
        elif t < self.tu0:
            for s in ("L", "R"):
                (a, pch) = foot_ik(self.f_lie[s], 18.0, "heel", d, H, g)
                legs[s] = (a, pch, 0.0)
        else:
            v = clamp((t - self.tu0) / (self.tu1 - self.tu0))
            for i, s in enumerate(("L", "R")):
                a0, a1 = 0.30 + 0.09 * i, 0.44 + 0.09 * i
                w = clamp((v - a0) / (a1 - a0))
                e = w - math.sin(2 * math.pi * w) / (2 * math.pi)
                fx = lerp(self.f_lie[s], self.f_up[s], e)
                th = lerp(18.0, 0.0, w)
                (a, pch) = foot_ik(fx, th, "heel" if th > 0.5 else "flat", d, H, g)
                lift = 0.05 * H * math.sin(math.pi * w)
                legs[s] = ((a[0], a[1] - lift), pch, 6.0 * math.sin(math.pi * w))
        for s, (a, pch, toe) in legs.items():
            p.legs[s] = {"ik": a, "pitch": pch, "toe": toe, "abd": 3.0}
        p.pitch = keys(t, self.lean)
        c = keys(t, self.curl)
        br = math.sin(2 * math.pi * t / 1.5)
        p.spine = [0.4 * c + 0.8 * br, c, c - 1.2 * br]
        for s in ("L", "R"):
            p.arms[s].update(sh=4.0, abd=6.0, elbow=20.0, wrist=4.0, grip=0.4)
        return p


class Stepper:
    """Standing / stepping on hand-planted feet while facing d (forward or backward steps):
    the pelvis rides over the support, trunk lean keys, crouch keys. path(t) / pose(t, u)
    for an Actor.free segment."""

    def __init__(self, A, t0, x0, feet0, d, steps, lean, crouch=None):
        self.A, self.d = A, float(d)
        self.body, self.H, self.g = A.body, A.H, A.g
        self.t0, self.x0 = t0, x0
        self.steps = Steps(A.g, A.H, feet0, steps, facing=d)
        self.lean = lean
        self.crouch = crouch or [(t0, 0.012)]
        tx, xx = [t0], [x0]
        fx = dict(feet0)
        for st in steps:
            fx[st[1]] = st[2]
            tx.append(st[0] + 0.08)
            xx.append(0.5 * (fx["L"] + fx["R"]))
        self.px = pchip(tx, xx)
        self.feet_end = fx

    def _state(self, t):
        H = self.H
        x = self.px(t)
        feet = {s: self.steps.foot(s, t) for s in ("L", "R")}
        y = self.g(x) - (self.body.hip - 0.006 - keys(t, self.crouch)) * H
        y = reach_y(self.body, H, x, y, [feet[s][0] for s in feet if feet[s][3]])
        return x, y, feet

    def path(self, t):
        x, y, _ = self._state(t)
        return x, y

    def pose(self, t, u):
        x, y, feet = self._state(t)
        p = F.Pose(x, y, 0.0 if self.d > 0 else 180.0)
        p.scale = self.A.scale
        for s in feet:
            a, pch, toe, _ = feet[s]
            p.legs[s] = {"ik": a, "pitch": pch, "toe": toe, "abd": 3.0}
        p.pitch = keys(t, self.lean)
        br = math.sin(2 * math.pi * t / 1.4)
        p.spine = [0.8 * br, 0.0, -1.2 * br]
        for s in ("L", "R"):
            p.arms[s].update(sh=4.0, abd=6.0, elbow=20.0, wrist=4.0, grip=0.4)
        return p


# where things are in s08 (world x)
X_LIE = 720.0                     # her pelvis, knocked flat
X_UP = X_LIE + 0.19 * GH          # standing up (and squatting for the lantern)
LANTERN_X = 952.0                 # where the lantern comes to rest (its centre)
X_SMASH = 1328.0                  # her pelvis when she smashes it on the strand
SMASH_HAND = (1392.0, 1334.0)     # her hand at the impact (the lantern hits C.smash_point)
RUN_SPEED = 2.4                   # body heights per second
G8 = dict(up0=9.2, up1=10.15, grab=10.62, smash=12.66)


@lru_cache(maxsize=None)
def cl_floor():
    D = S08_DT
    return Floor(cl_retreat(), D + F8["knock"], X_LIE, D + G8["up0"], D + G8["up1"], X_UP)


@lru_cache(maxsize=None)
def cl_girl():
    a = _cl_girl_actor()
    Fl = cl_floor()
    D = S08_DT
    a.stand(until=T7["back"], at=-1.0)
    a.free(dur=Fl.tu1 - T7["back"], path=Fl.path, pose=Fl.pose, at=T7["back"], blend=0.3, end_x=X_UP)
    a.stand(until=D + G8["grab"] + 0.2, crouch=0.30, blend=0.3)
    a.run(to=X_SMASH, gait="child_run", speed=RUN_SPEED, blend=0.2)
    t_r = a.cursor
    o = 0.022 * GH
    feet0 = dict(a.state["feet"])
    ts = D + G8["smash"]
    steps = [(ts - 0.16, "L", X_SMASH + 0.10 * GH, 0.2),                    # into the swing
             (ts + 0.22, "L", X_SMASH - 0.10 * GH, 0.16), (ts + 0.42, "R", X_SMASH - 0.32 * GH, 0.2),
             (ts + 0.66, "L", X_SMASH - 0.50 * GH, 0.22), (ts + 0.95, "R", X_SMASH - 0.62 * GH),
             (ts + 2.1, "L", X_SMASH - 0.80 * GH, 0.4), (ts + 2.9, "R", X_SMASH - 0.96 * GH, 0.4),
             (ts + 3.9, "L", X_SMASH - 1.08 * GH, 0.4)]
    steps = [st for st in steps if st[0] - (st[3] if len(st) > 3 else 0.32) > t_r]
    lean = [(t_r, 6.0), (ts - 0.3, 2.0), (ts - 0.12, -10.0, "out"), (ts, 24.0, "in"), (ts + 0.12, 14.0),
            (ts + 0.3, -16.0, "out"), (ts + 1.0, -8.0), (ts + 2.0, -10.0), (ts + 5.0, -8.0)]
    St = Stepper(a, t_r, a.state["x"], feet0, 1.0, steps, lean)
    a.free(dur=D + 18.0 - t_r, path=St.path, pose=St.pose, at=t_r, blend=0.15)
    _girl_channels(a)
    return a


def _girl_channels(a):
    D = S08_DT
    sp, w = cl_spider(), cl_wolf()
    eye = lambda t: sp.eye_pos(t)[0]
    a.look_at(-1.0, 1.95, (1720.0, 420.0), fade=0.1, amount=0.8)
    a.look_at(2.15, 3.45, eye, fade=0.3, amount=0.9)
    a.look_at(3.55, 3.95, (900.0, 1540.0), fade=0.2)
    a.look_at(4.1, 4.5, (2150.0, 1540.0), fade=0.2)
    a.look_at(4.7, D - 0.15, eye, fade=0.3)
    # s08: the wolf, the fight, the lantern, the strand, the fire
    wolf_head = lambda t: w.head_points(t)["eye"]
    a.look_at(D - 0.15, D + 2.3, wolf_head, fade=0.15)
    a.look_at(D + 3.0, D + 8.3, wolf_head, fade=0.4, amount=0.85)
    lant = lambda t: lantern_state(min(t - D, LANTERN_GRAB_T - 1e-3))["pos"]     # (never the hand)
    a.look_at(D + 8.4, D + G8["grab"] + 0.1, lant, fade=0.3)
    a.look_at(D + 11.35, D + G8["smash"], C_SMASH, fade=0.2)
    a.look_at(D + 13.6, D + 18.0, lambda t: (1500.0 - 60.0 * (t - D - 13.6), 900.0 - 260.0 * (t - D - 13.6)),
              fade=0.5)
    # the basket: carried on the far (left) arm, then clutched to her chest; knocked away
    a.arm("L", -1.0, 3.55, fade=0.3, sh=18.0, elbow=62.0, abd=9.0, wrist=-8.0, grip=0.9)
    a.arm("L", 3.75, D + F8["knock"], fade=0.3, sh=34.0, elbow=112.0, abd=12.0, wrist=-20.0, grip=0.95)
    a.arm("R", 3.85, T7["fall"], fade=0.3, sh=40.0, elbow=95.0, abd=14.0, wrist=-10.0, grip=0.8)
    a.reach("R", T7["fall"] + 0.15, 11.95, lambda t: (a.root(t)[0] - 0.17 * GH, CG(a.root(t)[0]) - 6.0), fade=0.2)
    a.arm("R", 12.15, D + 0.9, fade=0.18, sh=128.0, elbow=70.0, abd=10.0, wrist=20.0, grip=0.2)
    a.reach("R", D + 1.25, D + F8["knock"] - 0.05, lambda t: (a.root(t)[0] - 0.19 * GH, CG(a.root(t)[0]) - 6.0),
            fade=0.3)
    # knocked flat: the arms fly up, then she props herself on her hands
    kt = D + F8["knock"]
    for s_, k_ in (("L", 1.0), ("R", 0.85)):
        a.key("arm.%s.sh" % s_, [(kt - 0.02, 40.0), (kt + 0.15, 165.0 * k_, "out"), (kt + 0.45, 150.0 * k_),
                                 (kt + 0.8, 100.0)], fade=0.06, fade_out=0.3)
        a.key("arm.%s.elbow" % s_, [(kt - 0.02, 60.0), (kt + 0.15, 25.0, "out"), (kt + 0.8, 40.0)],
              fade=0.06, fade_out=0.3)
    for s_, dx in (("L", -0.24), ("R", -0.21)):
        a.reach(s_, kt + 1.1, D + G8["up0"] + 0.45,
                (lambda dx_: (lambda t: (a.root(t)[0] + dx_ * GH, CG(a.root(t)[0]) - 5.0)))(dx), fade=0.45)
    # getting up: the arms come forward for balance
    a.arm("L", D + G8["up0"] + 0.55, D + G8["up1"] - 0.1, fade=0.25, sh=40.0, elbow=35.0, abd=12.0)
    a.arm("R", D + G8["up0"] + 0.55, D + G8["up1"] - 0.1, fade=0.25, sh=50.0, elbow=30.0, abd=12.0)
    # the grab: squat, lean in, the near hand takes the lantern's ring
    tg = D + G8["grab"]
    a.key("pitch", [(tg - 0.42, 5.0), (tg - 0.1, 52.0, "out"), (tg + 0.08, 50.0), (tg + 0.3, 12.0)],
          fade=0.15, fade_out=0.15)
    a.reach("R", tg - 0.3, tg, lambda t: lantern_state(LANTERN_GRAB_T)["ring"], fade=0.18, grip=0.95)
    a.arm("L", tg - 0.4, tg + 0.3, fade=0.2, sh=-20.0, elbow=30.0, abd=18.0)
    # running with it, then the swing into the strand
    ts = D + G8["smash"]
    a.arm("R", tg + 0.2, ts - 0.36, fade=0.18, sh=12.0, elbow=38.0, abd=14.0, wrist=-12.0, grip=0.95)
    a.key("arm.R.sh", [(ts - 0.36, 12.0), (ts - 0.12, 172.0, "out"), (ts - 0.03, 120.0, "in")],
          fade=0.08, fade_out=0.06)
    a.key("arm.R.elbow", [(ts - 0.36, 38.0), (ts - 0.12, 60.0), (ts - 0.03, 20.0)], fade=0.08, fade_out=0.06)
    a.reach("R", ts - 0.03, ts + 0.06, SMASH_HAND, fade=0.04, grip=0.95)
    a.arm("L", ts - 0.36, ts + 0.06, fade=0.1, sh=-35.0, elbow=25.0, abd=20.0)
    # the fire bursts: she flinches away, arms up over her face, then lowers them
    for s_, sh_, el_ in (("R", 112.0, 118.0), ("L", 100.0, 125.0)):
        a.key("arm.%s.sh" % s_, [(ts + 0.06, 90.0 if s_ == "R" else -35.0), (ts + 0.2, sh_, "out"),
                                 (ts + 1.1, sh_), (ts + 1.8, 45.0)], fade=0.06, fade_out=0.6)
        a.key("arm.%s.elbow" % s_, [(ts + 0.06, 20.0), (ts + 0.2, el_, "out"), (ts + 1.1, el_),
                                    (ts + 1.8, 50.0)], fade=0.06, fade_out=0.6)
    a.key("head", [(ts + 0.04, 0.0), (ts + 0.18, 22.0, "out"), (ts + 1.0, 18.0), (ts + 1.5, 0.0)], mode="add")
    a.key("head", [(5.0, 0.0), (5.3, -8.0, "out"), (8.4, -8.0), (8.7, 6.0, "out"), (9.2, -4.0)], mode="add")
    return a


def cl_basket(t7):
    """(grip, angle, in_front) of the basket while she holds it (s07, s08 until it flies)."""
    a = cl_girl()
    sk = a.skeleton(t7)
    grip = basket_hand(sk, "L")
    w = clamp((t7 - 3.55) / 0.5)
    ang = lerp(4.0 * math.sin(t7 * 2.1), -28.0, w)
    return grip, ang, w > 0.5


# ----------------------------------------------------------------------------- s08: basket, bread, wine, lantern
C_SMASH = (1426.4955282228193, 1354.232922537315)       # == CLEARING_SET.smash_point (lazy there)
LANTERN_SIZE = 0.8
_BK = S.Basket(BASKET_SIZE)
_BODY = _BK._body()[0]
BASKET_REST = -74.4               # lying on its side, mouth to the left
B_FLY = dict(v=(430.0, -650.0), spin=-380.0)
B_LAND_X = 1075.0                 # where it settles upright after the bounce
LANTERN_GRAB_T = 10.62            # (s08 t) her hand closes on the ring


def _rot(p, ang):
    a = math.radians(ang)
    c, s_ = math.cos(a), math.sin(a)
    return (p[0] * c - p[1] * s_, p[0] * s_ + p[1] * c)


def _rest_grip(cx, ang, sink=3.0):
    """Grip (handle top) of the basket at angle `ang` whose body centre is at x cx and whose
    lowest point rests on the snow."""
    cl = _rot((0.0, 78.0 * BASKET_SIZE), ang)
    low = max(_rot(p, ang)[1] for p in _BODY) - cl[1]
    cy = CG(cx) + sink - low
    return (cx - cl[0], cy - cl[1])


@lru_cache(maxsize=None)
def _fly0():
    g0, a0, _ = cl_basket(S08_DT + F8["fly"])
    c0 = _rot((0.0, 78.0 * BASKET_SIZE), a0)
    return (g0[0] + c0[0], g0[1] + c0[1]), a0


def basket_state(t):
    """s08 t -> dict(grip, angle, held, mouth (world point at the rim centre)), the basket's
    flight (knocked out of her arms), bounce, tipping over on [basket] and rest."""
    if t < F8["fly"]:
        g, a_, _ = cl_basket(t + S08_DT)
        return dict(grip=g, angle=a_, held=True)
    (cx0, cy0), a0 = _fly0()
    vx, vy = B_FLY["v"]
    tau = t - F8["fly"]
    # flight until the body centre comes down to the snow
    y_rest = _rest_grip(cx0, 0.0)[1] + 78.0 * BASKET_SIZE
    A_, B_, C_ = 0.5 * S.G_PX, vy, cy0 - y_rest
    tl = (-B_ + math.sqrt(max(B_ * B_ - 4 * A_ * C_, 0.0))) / (2 * A_)
    if tau < tl:
        cx, cy = cx0 + vx * tau, cy0 + vy * tau + 0.5 * S.G_PX * tau * tau
        ang = a0 + B_FLY["spin"] * tau
        cl = _rot((0.0, 78.0 * BASKET_SIZE), ang)
        return dict(grip=(cx - cl[0], cy - cl[1]), angle=ang, held=False)
    xl = cx0 + vx * tl
    a_l = a0 + B_FLY["spin"] * tl
    k_ = tau - tl
    t_tip = F8["roll"] + 0.05
    if t < t_tip:
        # the bounce: a hop and a wobble that dies out, sliding to B_LAND_X
        x = lerp(xl, B_LAND_X, ss(0.0, 0.45, k_))
        da = ((a_l + 180.0) % 360.0) - 180.0
        ang = da * math.exp(-k_ / 0.12) * math.cos(2 * math.pi * k_ / 0.42)
        g = _rest_grip(x, ang)
        hop = 22.0 * math.sin(math.pi * clamp(k_ / 0.24)) * (1.0 if k_ < 0.24 else 0.0)
        return dict(grip=(g[0], g[1] - hop), angle=ang, held=False)
    # tipped over by the blow next to it: falls onto its side and rolls a little left
    u = t - t_tip
    fall = clamp(u / 0.3) ** 2
    rock = 7.0 * math.exp(-max(u - 0.3, 0.0) / 0.25) * math.sin(2 * math.pi * max(u - 0.3, 0.0) / 0.3) \
        if u > 0.3 else 0.0
    ang = BASKET_REST * fall + rock
    x = B_LAND_X - 38.0 * ss(0.05, 0.8, u)
    return dict(grip=_rest_grip(x, ang), angle=ang, held=False)


def basket_mouth(t):
    """World point at the middle of the basket's rim (where things come out)."""
    b = basket_state(t)
    m = _rot((0.0, 55.0 * BASKET_SIZE), b["angle"])
    return (b["grip"][0] + m[0], b["grip"][1] + m[1])


# the spill: (start, end) of each item's way out; rest x of its centre
SPILL = dict(bread=(5.62, 6.05, LANTERN_X + 22.0), bottle=(6.38, 7.2, LANTERN_X - 48.0),
             lantern=(8.3, 8.95, LANTERN_X))


def item_state(name, t):
    """s08 t -> (x, y, angle) of a spilled item, or None while it is still in the basket."""
    t0, t1, xr = SPILL[name]
    if t < t0:
        return None
    s_ = BASKET_SIZE
    half = {"bread": 12.0, "bottle": 7.5}[name] * s_ if name != "lantern" else 17.0 * LANTERN_SIZE
    m = basket_mouth(t0)
    u = clamp((t - t0) / (t1 - t0))
    gy = CG(xr)
    if name == "bread":
        x = lerp(m[0] + 8.0, xr, ease("out", u))
        y = lerp(m[1], gy - half, ss(0.0, 0.45, u)) - 16.0 * math.sin(math.pi * clamp(u / 0.45))
        ang = -230.0 * ease("out", u) - 14.0
        return x, y, ang
    if name == "bottle":
        x = lerp(m[0] + 20.0, xr, ease("out", u))
        y = lerp(m[1], gy - half, ss(0.0, 0.25, u))
        ang = lerp(-60.0, -270.0, ease("out", u))            # neck first, tumbling to rest on its side
        return x, y, ang
    # the lantern: rolls out on its side (ring toward her), glowing
    x = lerp(m[0] + 10.0, xr, ease("out", u))
    y = lerp(m[1], gy - half, ss(0.0, 0.3, u))
    ang = lerp(-160.0, -90.0, ease("out", u)) + 6.0 * math.sin(math.pi * u)
    return x, y, ang


def lantern_state(t):
    """s08 t -> dict(pos (flame / centre), anchor (handle top), angle, lit, shown, ring).
    In the basket -> rolls out glowing -> lying in the snow -> in her hand -> smashed."""
    s_ = LANTERN_SIZE
    L_ = S.Lantern(s_)
    tg, ts = LANTERN_GRAB_T, G8["smash"]
    lit = 0.0
    if t >= SPILL["lantern"][0]:
        lit = ss(SPILL["lantern"][0] + 0.05, SPILL["lantern"][0] + 0.4, t) * (0.85 + 0.15 * noise1(t * 3.0, 41))
    if t < SPILL["lantern"][0]:
        return dict(shown=False, pos=basket_mouth(t), anchor=None, angle=0.0, lit=0.0, ring=None)
    if t < tg - 0.02 or True:
        x, y, ang = item_state("lantern", min(t, tg))
        # centre -> anchor (handle top) for the drawing: the centre is 37 s below the anchor
        c = _rot((0.0, 37.0 * s_), ang)
        anchor = (x - c[0], y - c[1])
        ring = _rot((0.0, 8.0 * s_), ang)
        ring = (anchor[0] + ring[0], anchor[1] + ring[1])
        st = dict(shown=True, pos=(x, y), anchor=anchor, angle=ang, lit=lit, ring=ring)
        if t < tg:
            return st
    if t >= ts:
        return dict(shown=False, pos=C_SMASH, anchor=None, angle=0.0, lit=0.0, ring=None)
    # in her hand: hangs from the ring, swings with her; the swing throws it along the arm
    a = cl_girl()
    t7 = t + S08_DT
    sk = a.skeleton(t7)
    hand = basket_hand(sk, "R")
    w = ss(tg, tg + 0.25, t)
    if w < 1.0:
        hand = (lerp(st["anchor"][0], hand[0], w), lerp(st["anchor"][1], hand[1], w))
    h = 1.0 / 48.0
    v0 = basket_hand(a.skeleton(t7 - h), "R")
    v1 = basket_hand(a.skeleton(t7 + h), "R")
    vx = (v1[0] - v0[0]) / (2 * h)
    hang = clamp(-0.035 * vx, -40.0, 40.0) + 8.0 * math.sin(2 * math.pi * 1.7 * t) * math.exp(-max(t - tg, 0.0) / 0.6)
    ang = lerp(st["angle"], hang, w)
    sw = ss(ts - 0.36, ts - 0.12, t)
    if sw > 0.0:
        shp = sk.j["shoulder_R"]
        dx, dy = hand[0] - shp[0], hand[1] - shp[1]
        along = math.degrees(math.atan2(-dx, dy))         # the lantern's 'down' axis along the arm
        ang = lerp(ang, along, sw)
    c = _rot((0.0, 37.0 * s_), ang)
    return dict(shown=True, pos=(hand[0] + c[0], hand[1] + c[1]), anchor=hand, angle=ang, lit=lit,
                ring=hand)
