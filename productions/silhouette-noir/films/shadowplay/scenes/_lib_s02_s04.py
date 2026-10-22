"""Shared code for SHADOW PLAY s02 THE WATCHER, s03 WINDOW NINE and s04 NOTHING.

THE STREET SECTION RIG. s02 and s03 are one camera journey through one world: the facade
across the street, the street, her window 20 m away. `Rig` is a pinhole camera in that
section (metres): F = lens (px), c = distance from the facade plane, (X, Y) its position
(Y up from the sidewalk), (u, v) the facade-world point it looks at. Every plane of the
world (facade, her window wall, her chair, the sky at infinity) gets its own engine Camera
from the rig (`Rig.cam(z, k, u0, v0)`), so a dolly through her window is real perspective
and a tilt (aim change) moves every plane together.

WINDOW PEOPLE (facade scale, inside the lit windows; `interiors` callbacks):
    4  the dancer twirls alone      12  the cat lady talks to her cat (creatures.Cat)
    30 the woman who cries on Sundays
HER (s02, inside): curled in an armchair at her window, binoculars in her lap; `her_inside`.
THE SEAM s02 -> s03: `END_RIG` + `bino_shake(tw)` (tw = s02 time; s03 passes t + 15).
"""
import math
from functools import lru_cache

import cairo

from engine import atmos, bass, draw
from engine import figure as FIG
from engine.core import W, H, clamp, lerp, ease, smoothstep, hash01, noise1, fbm1, pulse
from engine.creatures import Cat
from engine.frame import Camera
from engine.motion import Actor
from engine.palette import SHADOWPLAY as PAL, RED, PAPER
from films.shadowplay import cast, sets

INK = PAL.ink
AMBER = PAL.light
HOT = PAL.lamp_hot
COOL = PAL.fog_at(1.0)

# =========================================================================== the world
K_F = 400.0 / 3.0                 # facade world units per metre (one storey = 3 m = 400)
FAC = sets.Facade(origin=(540.0, 3940.0), scale=1.0)
BLOCKS = sets.neighbours(FAC)
STREET_W = 20.0                   # facade plane -> her building's wall (m)
SHOPS = (0.0, 0.6)                # the late diner (right shopfront) is lit, as in s01
LOCK = FAC.camera_lock()          # Camera(540, 1796.7, 0.375)
LOCK_F = 900.0                    # lens of the lock (px): the lock camera stands 18 m out
LOCK_C = LOCK_F / (LOCK.zoom * K_F)
LOCK_Y = (3940.0 - LOCK.y) / K_F  # 16.07 m

# her room (s02 reveal): the window wall at z = STREET_W, in HerRoom world units
ROOM_K = 343.0                    # HerRoom scale 1: 1 m = 343 px
ROOM_O = (540.0, 1800.0)          # HerRoom origin (floor under the window centre)
HER_FLOOR = 18.9                  # her floor above the street (m): her eye ~ row 3
ROOM = sets.HerRoom(ROOM_O, 1.0)
ROOM_V0 = ROOM_O[1] + ROOM_K * HER_FLOOR


def fac_xy(X, Y):
    """Metres (X right of the facade centre, Y up from the sidewalk) -> facade world."""
    return 540.0 + K_F * X, 3940.0 - K_F * Y


def fac_XY(u, v):
    return (u - 540.0) / K_F, (3940.0 - v) / K_F


def room_xy(X, Y):
    """Metres -> HerRoom world (any plane of her room)."""
    return ROOM_O[0] + ROOM_K * X, ROOM_V0 - ROOM_K * Y


class Rig:
    """Pinhole camera in the street section (see module doc)."""

    __slots__ = ("F", "c", "X", "Y", "u", "v", "shake")

    def __init__(self, F, c, X, Y, u, v, shake=(0.0, 0.0)):
        self.F, self.c, self.X, self.Y, self.u, self.v = F, c, X, Y, u, v
        self.shake = shake               # extra screen offset (px), e.g. a handheld drift

    @property
    def zf(self):
        """Facade zoom (screen px per facade unit)."""
        return self.F / (self.c * K_F)

    def offsets(self):
        """(tx, ty): screen shift of the whole view from aiming (pan / tilt) + shake."""
        z = self.zf
        return (z * (540.0 + K_F * self.X - self.u) + self.shake[0],
                z * (3940.0 - K_F * self.Y - self.v) + self.shake[1])

    def cam(self, z=0.0, k=K_F, u0=540.0, v0=3940.0):
        """Engine Camera for a plane at depth z (m from the facade toward the camera) whose
        world coords map metres as u = u0 + k X, v = v0 - k Y. None behind the camera."""
        d = self.c - z
        if d <= 1e-3:
            return None
        zoom = self.F / (d * k)
        tx, ty = self.offsets()
        return Camera(u0 + k * self.X - tx / zoom, v0 - k * self.Y - ty / zoom, zoom)

    def facade(self):
        return self.cam(0.0)

    def room(self, z=STREET_W):
        """Camera for a plane in her room (HerRoom units) at depth z (>= STREET_W)."""
        return self.cam(z, ROOM_K, ROOM_O[0], ROOM_V0)

    def sky(self):
        """Camera for the sky at infinity: sky world = the lock's screen, shifted by the
        aim and magnified by the lens."""
        z = self.F / LOCK_F
        tx, ty = self.offsets()
        tx0 = LOCK.zoom * (540.0 - LOCK.x)
        ty0 = LOCK.zoom * (3940.0 - K_F * LOCK_Y - LOCK.y)
        return Camera(540.0 - (tx - tx0) / z, 960.0 - (ty - ty0) / z, z)

    def ahead(self):
        """The rig aimed straight ahead (no pan / tilt)."""
        u, v = fac_xy(self.X, self.Y)
        return Rig(self.F, self.c, self.X, self.Y, u, v, self.shake)


LOCK_RIG = Rig(LOCK_F, LOCK_C, 0.0, LOCK_Y, LOCK.x, LOCK.y)

# the end of s02 / start of s03: her binocular view on window 9 (dark, ~200 px wide)
W9C = FAC.window_center(9)                    # (953.3, 810)
END_ZF = 0.78
END_C, END_X, END_Y = 19.5, 0.36, 20.92       # just outside her window, upper-right pane
END_F = END_ZF * END_C * K_F
END_RIG = Rig(END_F, END_C, END_X, END_Y, W9C[0], W9C[1])


def bino_shake(tw, t_on=13.9):
    """Handheld drift of her binoculars (screen px, 3 px), as Camera.shaken(amp=3) would
    move the image; tw is s02 time (s03 passes t + 15) so the seam is exact."""
    e = smoothstep(t_on, t_on + 0.7, tw)
    return (-3.0 * e * fbm1(tw * 1.3, 61), -3.0 * e * fbm1(tw * 1.3, 78))


# =========================================================================== splines
class Spline:
    """Smooth keyframe curve through [(t, value), ...] (floats or tuples): monotone cubic
    Hermite (no overshoot), zero slope at the first and last key and at keys marked with
    a third item 'hold'. Holds outside the keys."""

    def __init__(self, keys):
        self.keys = sorted(keys, key=lambda k: k[0])
        self.ts = [k[0] for k in self.keys]
        vals = [k[1] for k in self.keys]
        self.vec = isinstance(vals[0], (tuple, list))
        self.vals = [tuple(v) if self.vec else (float(v),) for v in vals]
        self.hold = [len(k) > 2 and k[2] == "hold" for k in self.keys]
        n = len(self.ts)
        dim = len(self.vals[0])
        self.m = [[0.0] * dim for _ in range(n)]
        for d in range(dim):
            ys = [v[d] for v in self.vals]
            delta = [(ys[i + 1] - ys[i]) / max(self.ts[i + 1] - self.ts[i], 1e-9) for i in range(n - 1)]
            for i in range(1, n - 1):
                if self.hold[i] or delta[i - 1] * delta[i] <= 0:
                    continue
                h0 = self.ts[i] - self.ts[i - 1]
                h1 = self.ts[i + 1] - self.ts[i]
                w1, w2 = 2 * h1 + h0, h1 + 2 * h0
                self.m[i][d] = (w1 + w2) / (w1 / delta[i - 1] + w2 / delta[i])

    def __call__(self, t):
        ts = self.ts
        if t <= ts[0]:
            v = self.vals[0]
        elif t >= ts[-1]:
            v = self.vals[-1]
        else:
            i = 0
            while ts[i + 1] < t:
                i += 1
            h = ts[i + 1] - ts[i]
            s = (t - ts[i]) / h
            h00 = 2 * s ** 3 - 3 * s ** 2 + 1
            h10 = s ** 3 - 2 * s ** 2 + s
            h01 = -2 * s ** 3 + 3 * s ** 2
            h11 = s ** 3 - s ** 2
            a, b = self.vals[i], self.vals[i + 1]
            ma, mb = self.m[i], self.m[i + 1]
            v = tuple(h00 * a[d] + h10 * h * ma[d] + h01 * b[d] + h11 * h * mb[d] for d in range(len(a)))
        return v if self.vec else v[0]


def kseg(t, t0, t1, e="inout"):
    """Eased 0..1 progress of t through [t0, t1]."""
    if t <= t0:
        return 0.0
    if t >= t1:
        return 1.0
    return ease(e, (t - t0) / (t1 - t0))


# =========================================================================== sky + rain
def night_sky(f, t, rig, horizon=430.0, spread=420.0, glow=1.0, clouds=0.7):
    """sets.night_sky, but anchored to the rig's sky at infinity (it tilts and magnifies
    with the camera). horizon: sky-world y of the city glow (the lock's screen px)."""
    cam = rig.sky()
    hz = cam.to_screen((540.0, horizon))[1]
    z = cam.zoom
    sp = spread * z
    f.sky(PAL.sky_top, sets.mix(PAL.sky_top, PAL.sky_bottom, 0.7), mid=sets.mix(PAL.sky_top, PAL.sky_bottom, 0.25),
          mid_at=0.4, y0=hz - 1100.0 * z, y1=hz + 700.0 * z)
    old = f.cam
    f.set_camera(cam)
    try:
        if glow > 0:
            f.haze(PAL.fog_at(1.0), 0.80 * glow, y0=horizon - spread * 0.15, y1=horizon + 4000, feather=spread * 1.2)
            f.haze(sets.mix(PAL.fog_at(1.0), AMBER, 0.16), 0.30 * glow, y0=horizon + spread * 0.05, y1=horizon + 4000,
                   feather=spread * 0.6)
        if clouds > 0:
            f.haze(sets.mix(PAL.fog_at(1.0), PAL.rain, 0.25), 0.50 * clouds, y0=horizon - spread * 2.2,
                   y1=horizon + spread * 0.2, feather=spread * 1.3, tex=1.0, tex_scale=0.75, scroll=(7.0, 0.0), seed=4)
            f.haze(PAL.sky_top, 0.55 * clouds, y0=-4000, y1=horizon - spread * 1.3, feather=spread * 1.2, tex=1.0,
                   tex_scale=0.55, scroll=(4.0, 0.0), seed=8)
    finally:
        f.set_camera(old)
    return hz, sp


def rain(f, t, rig, density=1.0, alpha=1.0, seed=11, angle=-10.0):
    """atmos.rain seen through a zoom-1 camera that follows the view (the drops stay the
    size of rain near the lens whatever the lens does; the field moves with the aim)."""
    tx, ty = rig.offsets()
    old = f.cam
    f.set_camera(Camera(540.0 - 0.8 * tx, 960.0 - 0.8 * ty - 0.25 * K_F * (rig.Y - LOCK_Y) * rig.zf, 1.0))
    try:
        atmos.rain(f, density=density, angle=angle, t=t, seed=seed, alpha=alpha, speed=2300.0)
    finally:
        f.set_camera(old)


# =========================================================================== people helpers
def seated(yaw, lean=6.0, hip=86.0, knee=84.0, spread=5.0, arms=None):
    """pose_fn for Actor.free(): sitting on a chair / bed edge (FK legs), facing `yaw`."""
    def fn(t, u):
        p = FIG.Pose(0.0, 0.0, yaw)
        p.pitch = lean
        for s, d in (("L", 1.0), ("R", -1.0)):
            p.legs[s] = dict(hip=hip + 2.0 * d, abd=spread, knee=knee + 3.0 * d, ankle=-4.0, toe=0.0)
        a = arms or dict(sh=28.0, abd=6.0, elbow=58.0, wrist=6.0, grip=0.45)
        p.arms["L"] = dict(a)
        p.arms["R"] = dict(a, sh=a["sh"] - 4.0, elbow=a["elbow"] + 6.0)
        return p
    return fn


def seat_actor(body, look, x, floor_y, yaw, scale, seed=0, lean=6.0, arms=None, t0=-5.0, t1=60.0, hip=86.0,
               knee=84.0):
    """An Actor sitting from t0 to t1 with its feet on floor_y (world)."""
    a = Actor(body, look, x=x, ground=floor_y, facing=yaw, scale=scale, seed=seed)
    Hh = body.height * scale
    y = floor_y - (body.shin + body.ankle_h + 0.012) * Hh
    a.free(t1 - t0, lambda t, x=x, y=y: (x, y), seated(yaw, lean, hip, knee, arms=arms), at=t0, end_x=x)
    return a


def chair(ctx, seat, k, facing=1, color=None):
    """A plain wooden kitchen chair in profile: seat (world point = front middle of the
    seat), k = world px per metre, facing = the way its sitter faces (+1 right)."""
    sx, sy = seat
    d = -facing                      # the backrest is behind the sitter
    sw, th = 0.42 * k, 0.03 * k
    col = color or INK
    back_x = sx + d * sw
    front_x = sx + d * 0.04 * k
    draw.rect(ctx, min(sx, back_x) - 0.01 * k, sy, max(sx, back_x) + 0.01 * k, sy + th)        # seat
    for lx in (front_x, back_x - d * 0.02 * k):
        draw.rect(ctx, lx - 0.016 * k, sy, lx + 0.016 * k, sy + 0.45 * k)                      # legs
    draw.rect(ctx, back_x - 0.018 * k, sy - 0.48 * k, back_x + 0.018 * k, sy)                  # back post
    draw.poly(ctx, [(back_x - 0.02 * k, sy - 0.50 * k), (back_x + d * 0.05 * k, sy - 0.49 * k),
                    (back_x + d * 0.05 * k, sy - 0.40 * k), (back_x - 0.02 * k, sy - 0.41 * k)])   # top rail
    draw.rect(ctx, min(front_x, back_x), sy + 0.30 * k, max(front_x, back_x), sy + 0.315 * k)  # stretcher
    draw.fill(ctx, col)


def armchair_side(ctx, x, floor_y, k, facing=-1, color=None):
    """A low upholstered armchair in profile. x = middle of the seat, facing = the way its
    sitter faces (-1 left). Seat top 0.44 m, back 1.0 m, arm 0.62 m."""
    d = -facing                       # +1: the back is to the right
    col = color or INK
    seat_y = floor_y - 0.44 * k
    xf, xb = x - d * 0.30 * k, x + d * 0.30 * k
    # cushion and the box under it
    draw.smooth(ctx, [(xf, seat_y + 0.02 * k), (xf - d * 0.02 * k, seat_y - 0.05 * k), (x, seat_y - 0.07 * k),
                      (xb, seat_y - 0.05 * k), (xb, seat_y + 0.16 * k), (xf, seat_y + 0.16 * k)], close=True,
                tension=0.25)
    draw.rect(ctx, min(xf, xb) + 0.02 * k, seat_y + 0.1 * k, max(xf, xb) - 0.02 * k, floor_y - 0.08 * k)
    # back, raked a little
    bx0, bx1 = xb - d * 0.05 * k, xb + d * 0.10 * k
    draw.smooth(ctx, [(bx0, seat_y), (bx0 + d * 0.06 * k, floor_y - 0.96 * k), (bx0 + d * 0.13 * k, floor_y - 1.03 * k),
                      (bx1 + d * 0.03 * k, floor_y - 1.0 * k), (bx1, floor_y - 0.85 * k), (bx1, floor_y - 0.08 * k),
                      (bx0, floor_y - 0.08 * k)], close=True, tension=0.22)
    # arm with a rolled front
    ay = floor_y - 0.62 * k
    draw.rect(ctx, min(xf, xb), ay, max(xf, xb), ay + 0.10 * k)
    draw.circle(ctx, (xf + d * 0.01 * k, ay + 0.04 * k), 0.065 * k)
    draw.rect(ctx, xf - 0.03 * k, ay + 0.06 * k, xf + 0.03 * k, seat_y + 0.12 * k)
    # turned feet
    for fx in (xf + d * 0.05 * k, xb - d * 0.04 * k):
        draw.poly(ctx, [(fx - 0.025 * k, floor_y - 0.08 * k), (fx + 0.025 * k, floor_y - 0.08 * k),
                        (fx + 0.012 * k, floor_y), (fx - 0.012 * k, floor_y)])
    draw.fill(ctx, col)


def rimlit(f, L, fn, rim=(COOL, 0.5), d=2.0, clip=None, dirs=6, up=0.6):
    """Draw fn's ink silhouette on L with a hairline of backlight round its outline (it
    stands in front of a bright window). d: rim width in screen px; clip: world rect where
    the backlight is (only there the rim shows); up: extra weight for the top edges."""
    col, a = rim
    if a <= 0.01:
        fn(L)
        return
    L.push_group()
    fn(L)
    pat = L.pop_group()
    zoom = abs(L.get_matrix().xx) / max(f.scale, 1e-6) or 1.0
    dw = d / zoom
    L.save()
    if clip is not None:
        L.rectangle(clip[0], clip[1], clip[2] - clip[0], clip[3] - clip[1])
        L.clip()
    for j in range(dirs):
        ang = 2 * math.pi * j / dirs
        w = a * (1.0 + up * max(0.0, -math.sin(ang))) / (1.0 + up) * 0.75
        L.save()
        L.translate(dw * math.cos(ang), dw * math.sin(ang))
        draw.rgba(L, col, w)
        L.mask(pat)
        L.restore()
    L.restore()
    L.set_source(pat)
    L.paint()


def glint(f, p, size, level, color=None, rot=12.0):
    """A four-point star glint (emissive) at world point p."""
    if level <= 0.01:
        return
    col = color or sets.mix(HOT, (1.0, 1.0, 1.0), 0.5)
    with f.emit() as G:
        for a in (rot, rot + 90.0):
            draw.ellipse(G, p, size, size * 0.09, angle=a)
            draw.fill(G, col, 0.9 * level)
        draw.circle(G, p, size * 0.22)
        draw.fill(G, col, level)
    with f.light(blur=1.5) as A:
        for a in (rot, rot + 90.0):
            draw.ellipse(A, p, size * 0.75, size * 0.05, angle=a)
            draw.fill(A, col, 0.8 * level)
        sets.glow(A, p, size * 0.6, col, 0.6 * level)


# =========================================================================== window 4: the dancer
W4 = FAC.window_rect(4)
W12 = FAC.window_rect(12)
W30 = FAC.window_rect(30)
W9 = FAC.window_rect(9)
P_H = FAC.person_h                      # 233: an adult in a window (facade units)
FK = K_F                                # facade px per metre (furniture inside windows)


def _spin_keys(T):
    """Dancer's turn angle (deg, added to her yaw) over time: two pirouettes after Four,
    then slow turns in her loop."""
    four, alone = T["four"], T["alone"]
    keys = [(-10.0, 0.0), (four + 0.10, 0.0), (four + 0.72, 360.0, "out3"), (alone + 0.12, 360.0),
            (alone + 0.78, 720.0, "inout")]
    ang = 720.0
    for (a, b) in _spins(T)[2:]:
        keys += [(a, ang), (b, ang + 180.0, "inout")]
        ang += 180.0
    keys.append((90.0, ang))
    return keys


def _spins(T):
    four, alone = T["four"], T["alone"]
    out = [(four + 0.10, four + 0.72), (alone + 0.12, alone + 0.78)]
    for k in range(8):
        a = alone + 2.4 + 3.9 * k
        out.append((a, a + 1.2))
    return out


def dancer_pose(T):
    """pose_fn for the dancer (yaw spins; one leg in passe on the turns; arms in a slow
    port de bras between them)."""
    spins = _spins(T)

    def fn(t, u):
        p = FIG.Pose(0.0, 0.0, 20.0)
        on = 0.0
        prep = 0.0
        for (a, b) in spins:
            on = max(on, smoothstep(a - 0.12, a + 0.02, t) * (1.0 - smoothstep(b - 0.05, b + 0.2, t)))
            prep = max(prep, math.sin(math.pi * clamp((t - (a - 0.32)) / 0.34)) * (t < a + 0.02))
        sway = math.sin(t * 1.25 + 0.6)
        # legs: standing leg straight on half-toe; working leg in passe on the turns
        p.legs["L"] = dict(hip=-2.0 + 3.0 * sway, abd=3.0, knee=4.0 + 22.0 * prep, ankle=-18.0 * on, toe=0.0)
        p.legs["R"] = dict(hip=lerp(4.0 - 3.0 * sway, 52.0, on), abd=lerp(4.0, 32.0, on),
                           knee=lerp(6.0 + 22.0 * prep, 118.0, on), ankle=lerp(0.0, -40.0, on), toe=0.0)
        p.pitch = -2.0 * on + 4.0 * prep
        p.spine = [0.0, -2.0 * on, -3.0 + 2.0 * sway * (1 - on)]
        p.head = -6.0 * on + 4.0 * sway * (1 - on)
        # arms: rounded in front on the turn, overhead after it, a slow wave between
        wave = 0.5 + 0.5 * math.sin(t * 0.9)
        for s in ("L", "R"):
            sh_idle = lerp(70.0, 150.0, wave if s == "L" else 1.0 - wave)
            p.arms[s] = dict(sh=lerp(sh_idle, 165.0, on) - 30.0 * prep, abd=lerp(40.0, 18.0, on) + 25.0 * prep,
                             elbow=lerp(28.0, 52.0, on), wrist=12.0, grip=0.2)
        p.extra["spin_on"] = on
        return p
    return fn


def _releve(t, T):
    """Half-toe rise for the turns after Four (0..1)."""
    return smoothstep(T["four"], T["four"] + 0.12, t) * (1.0 - smoothstep(T["alone"] + 0.8, T["alone"] + 1.1, t))


@lru_cache(maxsize=4)
def dancer(four=0.80, alone=1.58):
    T = dict(four=four, alone=alone)
    x0, y0, x1, y1 = W4
    floor = FAC.floor_y(4)
    sc = P_H / 600.0
    a = Actor(cast.DANCER, cast.dancer(), x=x0 + 0.52 * (x1 - x0), ground=floor, facing=20.0, scale=sc, seed=4)
    hip_y = floor - (cast.DANCER.hip - 0.006) * cast.DANCER.height * sc
    a.free(100.0, lambda t, x=a.state["x"], y=hip_y: (x, y - 0.012 * P_H * _releve(t, T)),
           dancer_pose(T), at=-10.0)
    a.key("yaw", _spin_keys(T), mode="add")
    return a


def dancer_look(a, t):
    """Her look with the skirt and ponytail flying out on the turns."""
    lk = cast.dancer()
    on = a.pose(t).extra.get("spin_on", 0.0)
    lk.opts = dict(lk.opts or {}, flow=0.9 * on)
    return lk


def window4_flare(t, four):
    """Extra light in window 4 when she turns the lamp up on 'Four' (0..1)."""
    if t < four - 0.02:
        return 0.0
    dt = t - four + 0.02
    v = min(1.0, dt / 0.06)
    return v * (0.75 + 0.25 * math.exp(-dt * 3.0))


def draw_dancer(ctx, win, T4):
    """Window 4's interior: on 'Four' the room behind her brightens (painted UNDER her, so
    she stays a crisp silhouette on bright glass), then the dancer."""
    a = dancer(*T4)
    t = win.t
    v = window4_flare(t, T4[0])
    if v > 0.01 and win.mode == "direct":
        x0, y0, x1, y1 = win.rect
        w, h = x1 - x0, y1 - y0
        draw.radial(ctx, (x0 + 0.60 * w, y0 + 0.38 * h), 0, h * 1.0,
                    [(0, sets.mix(HOT, (1, 1, 1), 0.15), 0.92 * v), (0.4, HOT, 0.75 * v), (1, AMBER, 0.55 * v)])
        ctx.rectangle(x0 - 2, y0 - 2, w + 4, h + 4)
        ctx.fill()
    a.draw(win.f, t, ctx, look=dancer_look(a, t), eyes=win.mode == "direct")


def draw_window4_flare(f, t, four, k=1.0):
    """The brighter light of window 4 spilling OUT of the opening (halo on the wall, the
    sill) - never over the glass, so the dancer stays dark."""
    v = window4_flare(t, four) * k
    if v <= 0.01:
        return
    x0, y0, x1, y1 = W4
    w, h = x1 - x0, y1 - y0
    with f.light(blur=8.0) as A:
        A.save()
        A.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        A.rectangle(x0 - 3 * w, y0 - 3 * h, 7 * w, 7 * h)
        A.rectangle(x0 + 2, y0 + 2, w - 4, h - 4)
        A.clip()
        A.set_fill_rule(cairo.FILL_RULE_WINDING)
        sets.glow(A, ((x0 + x1) / 2, (y0 + y1) / 2 + 0.1 * h), h * 1.35, AMBER, 0.20 * v)
        sets.glow_ellipse(A, ((x0 + x1) / 2, y1 + 6), w * 0.8, 18, HOT, 0.45 * v)
        A.restore()


# =========================================================================== window 12: cat lady + cat
@lru_cache(maxsize=4)
def cat_lady(twelve=2.79, talks=3.25, cat_t=4.05):
    x0, y0, x1, y1 = W12
    w = x1 - x0
    floor = FAC.floor_y(12)
    sc = P_H / 600.0
    a = seat_actor(cast.CAT_LADY, cast.cat_lady(), x0 + 0.70 * w, floor, 180.0, sc, seed=12, lean=14.0,
                   arms=dict(sh=24.0, abd=8.0, elbow=70.0, wrist=10.0, grip=0.5), t1=80.0)
    # Twelve: she perks up and leans to the cat; talks: the near hand lifts and chats
    a.key("pitch", [(twelve - 0.3, 14.0), (twelve + 0.25, 26.0, "outback"), (cat_t + 0.9, 24.0),
                    (cat_t + 1.8, 12.0), (80.0, 12.0)], fade=0.2)
    a.key("head", [(twelve - 0.3, 18.0), (twelve + 0.2, 4.0, "out3"), (cat_t + 1.8, 10.0), (80.0, 10.0)], fade=0.2)
    # chatty nods on the syllables of 'talks to her cat'
    nods = [(talks - 0.1, 0.0)]
    for k, tk in enumerate((talks, talks + 0.22, talks + 0.48, talks + 0.66, cat_t, cat_t + 0.3)):
        nods += [(tk + 0.05, 7.0 + 2.0 * (k % 2)), (tk + 0.16, 0.0)]
    nods += [(cat_t + 2.0, 0.0)]
    a.key("neck", nods, mode="add")
    hand = [(talks - 0.25, 28.0), (talks + 0.1, 62.0, "out3"), (talks + 0.4, 50.0), (talks + 0.7, 66.0),
            (cat_t + 0.1, 58.0), (cat_t + 0.5, 70.0), (cat_t + 1.2, 30.0, "inout"), (80.0, 28.0)]
    a.key("arm.L.sh", hand, fade=0.25)
    a.key("arm.L.elbow", [(talks - 0.25, 70.0), (talks + 0.1, 40.0), (cat_t + 0.5, 34.0), (cat_t + 1.2, 70.0),
                          (80.0, 70.0)], fade=0.25)
    a.key("arm.L.wrist", [(talks, 0.0), (talks + 0.2, -25.0), (talks + 0.45, 10.0), (talks + 0.7, -22.0),
                          (cat_t + 0.1, 8.0), (cat_t + 0.4, -18.0), (cat_t + 1.0, 0.0)], fade=0.25)
    return a


CAT_SIZE = 0.40 * FK                     # a big tom (shoulder height 0.4 m)
CAT_CUSHION = 0.17 * FK                  # he sits on a cushion on the sill, above the fire-escape rail


@lru_cache(maxsize=4)
def window_cat(twelve=2.79, talks=3.25, cat_t=4.05):
    x0, y0, x1, y1 = W12
    w = x1 - x0
    c = Cat(x0 + 0.28 * w, y1 - CAT_CUSHION, facing=1, size=CAT_SIZE, seed=4)
    c.sit(talks + 4.8, look=0.0, tail="wrap")
    c.look(1.0, turn=55.0).sit(4.0, tail="wrap").look(1.6, turn=25.0).sit(60.0, tail="wrap")
    c.overlay("look", twelve + 0.15, 1.0, turn=-20.0)
    c.overlay("meow", talks + 0.55, 0.6)
    c.overlay("flick", cat_t - 0.02, 0.6, n=2)
    c.overlay("flick", cat_t + 1.9, 0.5, n=1)
    for k in range(6):
        c.overlay("flick", cat_t + 4.5 + 3.3 * k + 0.8 * hash01(12, k), 0.5, n=1)
    return c


def draw_cat_lady(ctx, win, T12):
    a = cat_lady(*T12)
    c = window_cat(*T12)
    t = win.t
    x0, y0, x1, y1 = W12
    w = x1 - x0
    floor = FAC.floor_y(12)
    chair(ctx, (x0 + 0.70 * w - 0.04 * FK, floor - 0.47 * FK), FK, facing=-1)
    a.draw(win.f, t, ctx, eyes=win.mode == "direct")
    # the cushion on the sill, then the cat on it
    cx = x0 + 0.28 * w
    draw.smooth(ctx, [(cx - 0.30 * FK, y1), (cx - 0.31 * FK, y1 - CAT_CUSHION * 0.8), (cx - 0.2 * FK, y1 - CAT_CUSHION),
                      (cx + 0.2 * FK, y1 - CAT_CUSHION), (cx + 0.31 * FK, y1 - CAT_CUSHION * 0.8), (cx + 0.30 * FK, y1)],
                close=True, tension=0.3)
    draw.fill(ctx, INK)
    c.draw(win.f, t, ctx, eyes=False)


# =========================================================================== window 30: the crier
def _sobs(t, start):
    """Sob envelope: bursts of 3-4 shudders with pauses, deterministic."""
    if t < start - 3.0:
        return 0.0
    v = 0.0
    k0 = int(math.floor((t - start) / 1.7)) - 1
    for k in range(k0, k0 + 3):
        tb = start + k * 1.7 + 0.3 * hash01(30, k, 1)
        n = 3 + int(hash01(30, k, 2) * 2)
        for j in range(n):
            tj = tb + j * (0.17 + 0.05 * hash01(30, k, j, 3))
            dt = t - tj
            if 0.0 <= dt < 0.35:
                v = max(v, math.sin(math.pi * min(1.0, dt / 0.07)) * math.exp(-dt * 9.0) * (1.0 - 0.15 * j))
    return v


@lru_cache(maxsize=4)
def crier(thirty=4.99, cries=5.35):
    x0, y0, x1, y1 = W30
    w = x1 - x0
    floor = FAC.floor_y(30)
    sc = P_H / 600.0
    body = cast.CRIER
    a = seat_actor(body, cast.crier(), x0 + 0.40 * w, floor, 0.0, sc, seed=30, lean=36.0,
                   arms=dict(sh=62.0, abd=10.0, elbow=118.0, wrist=20.0, grip=0.6), hip=80.0, knee=78.0, t1=80.0)
    a.pose_keys(-5.0, 80.0, fade=0.0, head=38.0, neck=14.0, **{"spine.2": 14.0, "spine.1": 6.0})
    a.eyes(-5.0, 80.0, open=0.0)
    amp = lambda t: 0.45 + 0.55 * smoothstep(cries - 0.3, cries + 0.2, t)
    a.channel("spine.2", lambda t: -7.0 * _sobs(t, cries) * amp(t), -5.0, 80.0, mode="add")
    a.channel("y", lambda t: -0.016 * P_H * _sobs(t, cries) * amp(t), -5.0, 80.0, mode="add")
    a.channel("head", lambda t: 4.0 * _sobs(t - 0.04, cries) * amp(t), -5.0, 80.0, mode="add")
    a.channel("arm.L.sh", lambda t: 5.0 * _sobs(t, cries) * amp(t), -5.0, 80.0, mode="add")
    a.channel("arm.R.sh", lambda t: 5.0 * _sobs(t - 0.02, cries) * amp(t), -5.0, 80.0, mode="add")
    return a


def draw_crier(ctx, win, T30):
    a = crier(*T30)
    x0, y0, x1, y1 = W30
    w = x1 - x0
    floor = FAC.floor_y(30)
    # the end of a bed she sits on
    bx = x0 + 0.40 * w
    draw.rect(ctx, x0 - 10.0, floor - 0.46 * FK, bx + 0.10 * FK, floor)
    draw.rect(ctx, x0 - 10.0, floor - 0.95 * FK, x0 + 0.05 * FK, floor)
    draw.fill(ctx, INK)
    a.draw(win.f, win.t, ctx, eyes=False)


def interiors_for(T4, T12, T30):
    """The three window lives as facade interior callbacks."""
    return {4: lambda c, w: draw_dancer(c, w, T4), 12: lambda c, w: draw_cat_lady(c, w, T12),
            30: lambda c, w: draw_crier(c, w, T30)}


# =========================================================================== the street below
class Walker:
    """Somebody under an umbrella seen from her window (high above): x(t) along the street,
    depth u in the street band (< 0: the far sidewalk), size relative."""

    __slots__ = ("t0", "x0", "vx", "u", "size", "seed")

    def __init__(self, t0, x0, vx, u, size=1.0, seed=0):
        self.t0, self.x0, self.vx, self.u, self.size, self.seed = t0, x0, vx, u, size, seed

    def at(self, t, st):
        x = self.x0 + self.vx * (t - self.t0)
        if self.u < 0:
            y = st.g + (st.curb_y - st.g) * 0.55
            s = 1.0
        else:
            y = st.lane_y(self.u)
            s = st.depth_scale(self.u)
        return x, y, s * self.size


def _walker_shape(ctx, t, w, x, y, s):
    """Umbrella seen from above at an angle: a scalloped canopy hiding the walker, legs
    scissoring under its near edge, the ferrule on top."""
    k = K_F * s
    R = 0.52 * k
    q = 0.62                                     # canopy foreshortening (seen from ~40 deg)
    stride = 0.72 * k
    ph = (x - w.x0) / max(stride, 1e-6) * math.pi * (1 if w.vx >= 0 else -1)
    dirx = 1.0 if w.vx >= 0 else -1.0
    hip = (x, y - 0.80 * k * 0.55)
    for sgn in (1.0, -1.0):
        sw = math.sin(ph) * sgn
        foot = (x + dirx * 0.22 * k * sw, y - 0.06 * k * max(0.0, math.cos(ph) * sgn))
        draw.capsule(ctx, hip, foot, 0.055 * k, 0.045 * k)
    # coat skirt under the canopy
    draw.poly(ctx, [(x - 0.20 * k, y - 0.80 * k * 0.55 - 0.05 * k), (x + 0.20 * k, y - 0.80 * k * 0.55 - 0.05 * k),
                    (x + 0.14 * k, y - 1.7 * k * 0.55), (x - 0.14 * k, y - 1.7 * k * 0.55)])
    cy = y - 1.75 * k * 0.55
    bob = 0.02 * k * abs(math.sin(ph))
    cx = x + dirx * 0.06 * k
    pts = []
    n = 8
    for j in range(n * 4 + 1):
        a = 2 * math.pi * j / (n * 4) + 0.3 * w.seed
        scal = 1.0 - 0.07 * (0.5 - 0.5 * math.cos(a * n))         # sags between the ribs
        pts.append((cx + R * scal * math.cos(a), cy - bob + R * q * scal * math.sin(a)))
    draw.poly(ctx, pts)
    draw.circle(ctx, (cx, cy - bob - 0.03 * k), 0.035 * k)
    draw.fill(ctx, INK)


def draw_walkers(f, t, st, walkers, sheen=1.0):
    """Umbrellas in the street band (facade camera set): their broken reflections in the
    wet road first, then the walkers, then the rain sheen on the canopies."""
    vb = f.cam.view_rect(200)
    vis = []
    for w in walkers:
        x, y, s = w.at(t, st)
        k = K_F * s
        if x + k < vb[0] or x - k > vb[2] or y - 2 * k > vb[3] or y + k < vb[1]:
            continue
        vis.append((w, x, y, s))
    for (w, x, y, s) in vis:
        k = K_F * s
        bb = (x - 0.7 * k, y - 1.3 * k, x + 0.7 * k, y + 0.05 * k)
        st.reflect(f, t, lambda c, w=w, x=x, y=y, s=s: _walker_shape(c, t, w, x, y, s), y, bb, strength=0.45,
                   length=0.9, seed=w.seed)
    if not vis:
        return
    with f.layer() as L:
        for (w, x, y, s) in vis:
            _walker_shape(L, t, w, x, y, s)
    if sheen > 0:
        with f.light(blur=2.0) as A:
            for (w, x, y, s) in vis:
                k = K_F * s
                R, q = 0.52 * k, 0.62
                cy = y - 1.75 * k * 0.55
                cx = x + (0.06 if w.vx >= 0 else -0.06) * k
                A.save()
                A.translate(cx, cy)
                A.scale(1.0, q)
                A.new_path()
                A.arc(0, 0, R * 0.92, math.pi * 1.08, math.pi * 1.92)
                A.restore()
                A.set_line_width(0.05 * k)
                draw.rgba(A, sets.mix(COOL, AMBER, 0.3), 0.42 * sheen)
                A.stroke()


# =========================================================================== the title
TITLE_H = 250.0                       # cap height (facade units): a window row is 320


@lru_cache(maxsize=2)
def _title_words():
    return (bass.title_glyphs("SHADOW", height=TITLE_H, tracking=0.10, seed=21, rough=1.0, jitter=0.6),
            bass.title_glyphs("PLAY", height=TITLE_H, tracking=0.10, seed=22, rough=1.0, jitter=0.6))


def draw_title(f, t, t_in, t_out, cx=860.0, rows=(1210.0, 2010.0), color=PAPER):
    """SHADOW / PLAY in hand-cut PAPER letters sliding along the facade's grid lines (North
    by Northwest): SHADOW in along row 3 from the left, PLAY along row 5 from the right;
    they stop at t_in + ~0.6 and slide on off along the same lines from t_out."""
    words = _title_words()
    if t < t_in - 0.05 or t > t_out + 1.2:
        return
    with f.layer() as L:
        for wi, (Tg, cy) in enumerate(zip(words, rows)):
            frm = -1.0 if wi == 0 else 1.0
            n = len(Tg)
            for i, g in enumerate(Tg):
                order = (n - 1 - i) if frm < 0 else i          # the leading letter arrives first
                a0 = t_in + 0.05 * order + 0.08 * wi
                b0 = t_out + 0.045 * (n - 1 - order) + 0.06 * wi
                pin = kseg(t, a0, a0 + 0.55, "out5")
                pout = kseg(t, b0, b0 + 0.5, "in3")
                if pin <= 0.0 or pout >= 1.0:
                    continue
                dx = frm * 2600.0 * (1.0 - pin) - frm * 2600.0 * pout
                L.new_path()
                g.path(L, (cx + 12.0, cy + 14.0), dx=dx)
                draw.fill(L, INK, 0.55)
                L.new_path()
                g.path(L, (cx, cy), dx=dx)
                draw.fill(L, sets.mix(color, COOL, 0.12))


# =========================================================================== the facade world
def facade_lit(t, extra=None):
    lit = dict(sets.NIGHT)
    if extra:
        lit.update(extra)
    return lit


def halo_for(zf):
    """Facade halo / emit strength: full at the lock, lower when the windows are big (the
    bloom would wash the silhouettes out)."""
    k = smoothstep(0.42, 0.85, zf)
    return lerp(1.0, 0.45, k), lerp(1.0, 0.40, k)


def draw_world(f, t, rig, lit=None, interiors=None, curtains=None, street_depth=560.0, rain_k=1.0,
               sky=True, street=True, people=None, title=None, flare4=None, haze=1.0, rain_on=True,
               halo=None, emit=None):
    """The facade world through the rig, back to front: sky, neighbours, facade (+ window
    people), street, [walkers], lamp, haze, [title], rain. Returns the facade camera."""
    lit = lit if lit is not None else sets.NIGHT
    hk, ek = halo_for(rig.zf)
    halo = hk if halo is None else halo
    emit = ek if emit is None else emit
    if sky:
        night_sky(f, t, rig)
    cam = rig.facade()
    f.set_camera(cam)
    sets.draw_blocks(f, t, BLOCKS, layer=dict(par=1.0, fog=0.28))
    FAC.draw(f, t, lit=lit, interiors=interiors or {}, curtains=curtains or {}, shops=SHOPS, halo=halo, emit=emit)
    if flare4 is not None:
        draw_window4_flare(f, t, flare4)
    if street:
        st = sets.Street(FAC.ground_y, depth=street_depth, seed=3)
        lamp = sets.Streetlamp((FAC.x0 + 250.0, FAC.ground_y + 40.0), height=680.0, facing=1)
        srcs = FAC.light_sources(t, lit, shops=SHOPS) + [lamp.light_source()]
        for b in BLOCKS:
            srcs += b.light_sources(t)
        st.draw(f, t, sources=srcs, lamp_pools=[(lamp.lantern[0], 1.0)])
        if people is not None:
            people(f, t, st)
        lamp.draw(f, t)
        f.haze(PAL.fog_at(0.85), 0.20 * haze, y0=3450.0, y1=4700.0 + street_depth, feather=500.0)
    f.haze(PAL.fog_at(1.0), 0.05 * haze)
    if title is not None:
        title(f, t)
    if rain_on and rain_k > 0:
        rain(f, t, rig, density=rain_k)
    return cam


# =========================================================================== her (s02, inside)
HER_X = 0.40                 # her pelvis, m right of her window's centre
HER_Z = STREET_W + 0.75      # her plane: 0.75 m inside the glass
HER_SEAT = 0.44
HER_YAW = 190.0              # facing left (toward the window's middle), a touch away
XH, FLOOR_H = room_xy(HER_X, HER_FLOOR)
YH = FLOOR_H - HER_SEAT * ROOM_K - 0.10 * ROOM_K       # hip joint above the cushion
WIPE = (0.66, 0.66, 75.0)    # the patch of the steamed pane she wiped clear to watch


def _her_curl(t, u):
    """Curled in the armchair, knees up, leaning toward the glass."""
    p = FIG.Pose(0.0, 0.0, HER_YAW)
    p.pitch = 10.0
    p.spine = [5.0, 8.0, 6.0]
    p.neck = 4.0
    p.head = -6.0
    for s, d in (("L", 1.0), ("R", -1.0)):
        p.legs[s] = dict(hip=112.0 + 4.0 * d, abd=6.0, knee=138.0 + 6.0 * d, ankle=26.0, toe=12.0)
    for s in ("L", "R"):
        p.arms[s] = dict(sh=36.0, abd=10.0, elbow=70.0, wrist=0.0, grip=0.85)
    return p


def raise_k(t, watch):
    """Binoculars from her lap (0) to her eyes (1): a quick lift on 'watch'."""
    return kseg(t, watch - 0.06, watch + 0.34, "inout3")


def bino_angle(t, watch):
    k = raise_k(t, watch)
    a = lerp(196.0, 189.0, k)
    dt = t - watch - 0.34
    if dt > 0:                                   # a little settle once they reach her eyes
        a += 1.6 * math.exp(-dt * 7.0) * math.sin(dt * 22.0)
    return a


@lru_cache(maxsize=2)
def her_inside(watch=9.18):
    """(actor, head_actor): her curled at the window; the head actor (no arm IK) gives the
    eye position the binoculars go to."""
    def mk():
        a = Actor(cast.HER, cast.her(), x=XH, ground=FLOOR_H, facing=HER_YAW, scale=1.0, seed=21)
        a.free(100.0, lambda t: (XH, YH), _her_curl, at=-20.0, end_x=XH)
        a.channel("spine.1", lambda t: 1.4 * math.sin(t * 2.0 * math.pi / 4.1), -20.0, 80.0, mode="add")
        a.key("head", [(watch - 1.2, -6.0), (watch - 0.45, -12.0), (watch + 0.5, -9.0), (80.0, -9.0)], fade=0.4)
        a.key("pitch", [(watch - 0.35, 10.0), (watch + 0.3, 15.0, "out3"), (80.0, 15.0)], fade=0.3)
        return a
    head = mk()
    a = mk()

    def wrist(t, side):
        g, ang = bino_grip(t, watch)
        ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        along = -6.0 if side == "R" else 10.0
        below = 12.0
        # (along the glasses, below them): below = rotate (0, +1) as the hump is flipped
        return (g[0] + along * ca - below * sa * -1.0, g[1] + along * sa + below * ca * -1.0)

    a.reach("R", -20.0, 80.0, lambda t: wrist(t, "R"), fade=0.0, grip=0.95)
    a.reach("L", -20.0, 80.0, lambda t: wrist(t, "L"), fade=0.0, grip=0.95)
    a.channel("eyes.glow", lambda t: 1.0 - raise_k(t, watch), -20.0, 80.0)
    return a, head


def bino_grip(t, watch=9.18):
    """(grip point, angle): in her lap on her knees, then at her eyes."""
    _, head = her_inside(watch)
    sk = head.skeleton(t)
    k = raise_k(t, watch)
    ang = bino_angle(t, watch)
    e1, e2, r, w, front = FIG.eye_points(sk, cast.her())
    au = math.radians(189.0)
    up = (e1[0] + 33.0 * math.cos(au) - 3.0, e1[1] + 33.0 * math.sin(au) + 2.0)
    kx, ky = sk.j["knee_L"]
    rest = (kx + 26.0, ky - 22.0)
    g = lerp(rest, up, k)
    g = (g[0] + 22.0 * math.sin(math.pi * k), g[1])      # the lift arcs in toward her chest
    return g, ang


def draw_her_inside(f, t, rig, watch=9.18, rim=0.55):
    """Her plane: the armchair, her, the binoculars, rim-lit by the window behind her."""
    cam = rig.room(HER_Z)
    if cam is None:
        return
    a, head = her_inside(watch)
    room = rig.room(STREET_W)
    clip = None
    if room is not None:
        x0, y0, x1, y1 = ROOM.glass
        p0 = cam.to_world(room.to_screen((x0, y0)))
        p1 = cam.to_world(room.to_screen((x1, ROOM.sill_y)))
        clip = (p0[0], p0[1], p1[0], p1[1])
    f.set_camera(cam)
    g, ang = bino_grip(t, watch)
    look = cast.her()

    def shapes(L):
        armchair_side(L, XH + 0.05 * ROOM_K, FLOOR_H, ROOM_K, facing=-1)
        a.draw(f, t, L, look=look, eyes=False)
        sets.binoculars(L, g, angle=ang, scale=1.0, view="side", flip=-1)

    with f.layer() as L:
        rimlit(f, L, shapes, rim=(sets.mix(COOL, AMBER, 0.2), rim), d=2.2, clip=clip)
        FIG.draw_eyes(f, a.skeleton(t), look, L)
    # the glint: the objective catches the facade's light as the glasses come up
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    obj = (g[0] + 30.0 * ca, g[1] + 30.0 * sa - 6.0)
    lv = pulse(t, watch + 0.36, attack=0.05, decay=0.22)
    glint(f, obj, 34.0, 1.1 * lv)


def draw_room(f, t, rig, watch=9.18, rain_k=1.0, her=True):
    """Her window wall (glass, frost with the wiped patch, rain on the pane, sash, sill,
    radiator, plant, gathered curtain) and her in front of it. Nothing when the camera
    is outside."""
    cam = rig.room(STREET_W)
    if cam is None:
        return
    d = rig.c - STREET_W
    f.set_camera(cam)
    near = smoothstep(0.04, 0.5, d)                 # the drops on the glass melt away very close
    ROOM.draw(f, t, binoculars=False, chair=False, mug=True, rain=rain_k * near, condensation=0.85,
              outside_light=1.0, wipe=WIPE)
    if her and rig.c > HER_Z + 0.02:
        draw_her_inside(f, t, rig, watch)
