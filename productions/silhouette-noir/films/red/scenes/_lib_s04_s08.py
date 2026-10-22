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


@lru_cache(maxsize=None)
def cl_girl():
    a = _cl_girl_actor()
    R = cl_retreat()
    a.stand(until=T7["back"], at=-1.0)
    a.free(dur=40.0 - T7["back"], path=R.path, pose=R.pose, at=T7["back"], blend=0.3)
    sp = cl_spider()
    eye = lambda t: sp.eye_pos(t)[0]
    a.look_at(-1.0, 1.95, (1720.0, 420.0), fade=0.1, amount=0.8)
    a.look_at(2.15, 3.45, eye, fade=0.3, amount=0.9)
    a.look_at(3.55, 3.95, (900.0, 1540.0), fade=0.2)
    a.look_at(4.1, 4.5, (2150.0, 1540.0), fade=0.2)
    a.look_at(4.7, 40.0, eye, fade=0.3)
    # the basket: carried on the far (left) arm, then clutched to her chest
    a.arm("L", -1.0, 3.55, fade=0.3, sh=18.0, elbow=62.0, abd=9.0, wrist=-8.0, grip=0.9)
    a.arm("L", 3.75, 40.0, fade=0.3, sh=34.0, elbow=112.0, abd=12.0, wrist=-20.0, grip=0.95)
    a.arm("R", 3.85, T7["fall"], fade=0.3, sh=40.0, elbow=95.0, abd=14.0, wrist=-10.0, grip=0.8)
    # falling: the near hand goes back to the snow
    a.reach("R", T7["fall"] + 0.15, 11.95, lambda t: (a.root(t)[0] - 0.17 * GH, CG(a.root(t)[0]) - 6.0), fade=0.2)
    # the shield: near arm up in front of her face as it rears to strike
    a.arm("R", 12.15, 40.0, fade=0.18, sh=128.0, elbow=70.0, abd=10.0, wrist=20.0, grip=0.2)
    a.key("head", [(5.0, 0.0), (5.3, -8.0, "out"), (8.4, -8.0), (8.7, 6.0, "out"), (9.2, -4.0)], mode="add")
    return a


def cl_basket(t7):
    """(grip, angle, in_front) of the basket while she holds it."""
    a = cl_girl()
    sk = a.skeleton(t7)
    grip = basket_hand(sk, "L")
    w = clamp((t7 - 3.55) / 0.5)
    ang = lerp(4.0 * math.sin(t7 * 2.1), -28.0, w)
    return grip, ang, w > 0.5
