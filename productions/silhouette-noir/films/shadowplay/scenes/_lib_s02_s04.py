"""Shared code for SHADOW PLAY s02 THE WATCHER, s03 WINDOW NINE and s04 NOTHING.

THE STREET SECTION RIG. s02 and s03 are one camera journey through one world: the facade
across the street, the street, her window 20 m away. `Rig` is a pinhole camera in that
section (metres): F = lens (px), c = distance from the facade plane, (X, Y) its position
(Y up from the sidewalk), (u, v) the facade-world point it looks at. Every plane of the
world (facade, her window wall, her chair, the sky at infinity) gets its own engine Camera
from the rig (`Rig.cam(z, k, u0, v0)`), so a dolly through her window is real perspective
and a tilt moves every plane together.

WINDOW PEOPLE (facade scale, inside the lit windows; `interiors` callbacks):
    4  the dancer twirls alone      12  the cat lady talks to her cat (creatures.Cat)
    30 the woman who cries on Sundays
"""
import math
from functools import lru_cache

import cairo

from engine import atmos, bass, draw
from engine import figure as FIG
from engine.core import W, H, clamp, lerp, ease, smoothstep, hash01, noise1, fbm1
from engine.creatures import Cat
from engine.frame import Camera
from engine.motion import Actor
from engine.palette import SHADOWPLAY as PAL, RED, PAPER
from films.shadowplay import cast, sets

INK = PAL.ink
AMBER = PAL.light
HOT = PAL.lamp_hot

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

# her room (s02 reveal, s03): the window wall at z = STREET_W, in HerRoom world units
ROOM_K = 343.0                    # HerRoom scale 1: 1 m = 343 px
ROOM_O = (540.0, 1800.0)          # HerRoom origin (floor under the window centre)
HER_FLOOR = 18.9                  # her floor above the street (m): sixth floor, her eye ~ row 3
ROOM = sets.HerRoom(ROOM_O, 1.0)


def fac_xy(X, Y):
    """Metres (X right of the facade centre, Y up from the sidewalk) -> facade world."""
    return 540.0 + K_F * X, 3940.0 - K_F * Y


def fac_XY(u, v):
    return (u - 540.0) / K_F, (3940.0 - v) / K_F


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
        world coords map metres as u = u0 + k X, v = v0 - k Y."""
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
        return self.cam(z, ROOM_K, ROOM_O[0], ROOM_O[1] + ROOM_K * HER_FLOOR)

    def sky(self):
        """Camera for the sky at infinity: sky world = the lock's screen, shifted by the
        aim and magnified by the lens."""
        z = self.F / LOCK_F
        tx, ty = self.offsets()
        tx0 = LOCK.zoom * (540.0 - LOCK.x)
        ty0 = LOCK.zoom * (3940.0 - K_F * LOCK_Y - LOCK.y)
        return Camera(540.0 - (tx - tx0) / z, 960.0 - (ty - ty0) / z, z)

    def to_screen(self, cam, p):
        return cam.to_screen(p)


LOCK_RIG = Rig(LOCK_F, LOCK_C, 0.0, LOCK_Y, LOCK.x, LOCK.y)


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
            (alone + 0.78, 720.0, "inout"), (alone + 2.4, 720.0), (alone + 3.6, 900.0, "inout"), (alone + 6.2, 900.0),
            (alone + 7.4, 1080.0, "inout"), (alone + 10.0, 1080.0), (alone + 11.2, 1260.0, "inout"), (60.0, 1260.0)]
    return keys


def dancer_pose(T):
    """pose_fn for the dancer (yaw spins; one leg in passe on the turns; arms in a slow
    port de bras between them)."""
    four, alone = T["four"], T["alone"]
    spins = [(four + 0.10, four + 0.72), (alone + 0.12, alone + 0.78), (alone + 2.4, alone + 3.6),
             (alone + 6.2, alone + 7.4), (alone + 10.0, alone + 11.2)]

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
        for s, sg in (("L", 1.0), ("R", -1.0)):
            sh_idle = lerp(70.0, 150.0, wave if s == "L" else 1.0 - wave)
            p.arms[s] = dict(sh=lerp(sh_idle, 165.0, on) - 30.0 * prep, abd=lerp(40.0, 18.0, on) + 25.0 * prep,
                             elbow=lerp(28.0, 52.0, on), wrist=12.0, grip=0.2)
        p.extra["spin_on"] = on
        return p
    return fn


@lru_cache(maxsize=4)
def dancer(four=0.80, alone=1.58):
    T = dict(four=four, alone=alone)
    x0, y0, x1, y1 = W4
    floor = FAC.floor_y(4)
    sc = P_H / 600.0
    a = Actor(cast.DANCER, cast.dancer(), x=x0 + 0.52 * (x1 - x0), ground=floor, facing=20.0, scale=sc, seed=4)
    hip_y = floor - (cast.DANCER.hip - 0.006) * cast.DANCER.height * sc
    a.free(70.0, lambda t, x=a.state["x"], y=hip_y: (x, y - 0.012 * P_H * _relevé(t, T)),
           dancer_pose(T), at=-10.0)
    a.key("yaw", _spin_keys(T), mode="add")
    return a


def _relevé(t, T):
    return smoothstep(T["four"] + 0.0, T["four"] + 0.12, t) * (1.0 - smoothstep(T["alone"] + 0.8, T["alone"] + 1.1, t))


def dancer_look(a, t):
    """Her look with the skirt and ponytail flying out on the turns."""
    lk = cast.dancer()
    sp = 0.0
    for dt in (-0.04, 0.04):
        pass
    p = a.pose(t)
    on = p.extra.get("spin_on", 0.0)
    lk.opts = dict(lk.opts or {}, flow=0.9 * on)
    return lk


def draw_dancer(ctx, win, T4):
    a = dancer(*T4)
    t = win.t
    eyes = win.mode == "direct"
    a.draw(win.f, t, ctx, look=dancer_look(a, t), eyes=eyes)


def window4_flare(t, four):
    """Extra light in window 4 when she turns the lamp up on 'Four' (0..1)."""
    if t < four - 0.02:
        return 0.0
    dt = t - four + 0.02
    v = min(1.0, dt / 0.06)
    return v * (0.75 + 0.25 * math.exp(-dt * 3.0))


def draw_window4_flare(f, t, four, k=1.0):
    v = window4_flare(t, four) * k
    if v <= 0.01:
        return
    x0, y0, x1, y1 = W4
    w, h = x1 - x0, y1 - y0
    with f.light(blur=6.0) as A:
        A.save()
        A.rectangle(x0, y0, w, h)
        A.clip()
        sets.glow(A, (x0 + 0.62 * w, y0 + 0.42 * h), h * 0.8, sets.HOT, 0.30 * v)
        A.restore()
        sets.glow(A, ((x0 + x1) / 2, (y0 + y1) / 2), h * 1.25, AMBER, 0.10 * v)
    with f.emit() as G:
        G.rectangle(x0, y0, w, h)
        draw.fill(G, AMBER, 0.22 * v)


# =========================================================================== window 12: cat lady + cat
@lru_cache(maxsize=4)
def cat_lady(twelve=2.79, talks=3.25, cat_t=4.05):
    x0, y0, x1, y1 = W12
    w = x1 - x0
    floor = FAC.floor_y(12)
    sc = P_H / 600.0
    a = seat_actor(cast.CAT_LADY, cast.cat_lady(), x0 + 0.70 * w, floor, 180.0, sc, seed=12, lean=14.0,
                   arms=dict(sh=24.0, abd=8.0, elbow=70.0, wrist=10.0, grip=0.5))
    # Twelve: she perks up and leans to the cat; talks: the near hand lifts and chats
    a.key("pitch", [(twelve - 0.3, 14.0), (twelve + 0.25, 26.0, "outback"), (cat_t + 0.9, 24.0),
                    (cat_t + 1.8, 12.0), (60.0, 12.0)], fade=0.2)
    a.key("head", [(twelve - 0.3, 18.0), (twelve + 0.2, 4.0, "out3"), (cat_t + 1.8, 10.0), (60.0, 10.0)], fade=0.2)
    # chatty nods on the syllables of 'talks to her cat'
    nods = [(talks - 0.1, 0.0)]
    for k, tk in enumerate((talks, talks + 0.22, talks + 0.48, talks + 0.66, cat_t, cat_t + 0.3)):
        nods += [(tk + 0.05, 7.0 + 2.0 * (k % 2)), (tk + 0.16, 0.0)]
    nods += [(cat_t + 2.0, 0.0)]
    a.key("neck", nods, mode="add")
    hand = [(talks - 0.25, 28.0), (talks + 0.1, 62.0, "out3"), (talks + 0.4, 50.0), (talks + 0.7, 66.0),
            (cat_t + 0.1, 58.0), (cat_t + 0.5, 70.0), (cat_t + 1.2, 30.0, "inout"), (60.0, 28.0)]
    a.key("arm.L.sh", hand, fade=0.25)
    a.key("arm.L.elbow", [(talks - 0.25, 70.0), (talks + 0.1, 40.0), (cat_t + 0.5, 34.0), (cat_t + 1.2, 70.0),
                          (60.0, 70.0)], fade=0.25)
    a.key("arm.L.wrist", [(talks, 0.0), (talks + 0.2, -25.0), (talks + 0.45, 10.0), (talks + 0.7, -22.0),
                          (cat_t + 0.1, 8.0), (cat_t + 0.4, -18.0), (cat_t + 1.0, 0.0)], fade=0.25)
    return a


@lru_cache(maxsize=4)
def window_cat(twelve=2.79, talks=3.25, cat_t=4.05):
    x0, y0, x1, y1 = W12
    w = x1 - x0
    c = Cat(x0 + 0.33 * w, y1, facing=1, size=0.25 * FK, seed=4)
    c.sit(talks - 0.2 + 5.0, look=0.0, tail="hang")
    c.look(1.0, turn=55.0).sit(4.0, tail="hang").look(1.6, turn=25.0).sit(30.0, tail="hang")
    c.overlay("look", twelve + 0.15, 1.0, turn=-20.0)
    c.overlay("meow", talks + 0.55, 0.6)
    c.overlay("flick", cat_t - 0.02, 0.6, n=2)
    c.overlay("flick", cat_t + 1.9, 0.5, n=1)
    return c


def draw_cat_lady(ctx, win, T12):
    a = cat_lady(*T12)
    c = window_cat(*T12)
    t = win.t
    eyes = win.mode == "direct"
    x0, y0, x1, y1 = W12
    w = x1 - x0
    floor = FAC.floor_y(12)
    chair(ctx, (x0 + 0.70 * w - 0.04 * FK, floor - 0.47 * FK), FK, facing=-1)
    a.draw(win.f, t, ctx, eyes=eyes)
    c.draw(win.f, t - 5.0 + 5.0, ctx, eyes=False)


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
                   arms=dict(sh=62.0, abd=10.0, elbow=118.0, wrist=20.0, grip=0.6), hip=80.0, knee=78.0)
    a.pose_keys(-5.0, 60.0, fade=0.0, head=38.0, neck=14.0, **{"spine.2": 14.0, "spine.1": 6.0})
    a.eyes(-5.0, 60.0, open=0.0)
    amp = lambda t: 0.45 + 0.55 * smoothstep(cries - 0.3, cries + 0.2, t)
    a.channel("spine.2", lambda t: -7.0 * _sobs(t, cries) * amp(t), -5.0, 60.0, mode="add")
    a.channel("y", lambda t: -0.016 * P_H * _sobs(t, cries) * amp(t), -5.0, 60.0, mode="add")
    a.channel("head", lambda t: 4.0 * _sobs(t - 0.04, cries) * amp(t), -5.0, 60.0, mode="add")
    a.channel("arm.L.sh", lambda t: 5.0 * _sobs(t, cries) * amp(t), -5.0, 60.0, mode="add")
    a.channel("arm.R.sh", lambda t: 5.0 * _sobs(t - 0.02, cries) * amp(t), -5.0, 60.0, mode="add")
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


# =========================================================================== the facade world
def facade_lit(t, extra=None):
    lit = dict(sets.NIGHT)
    if extra:
        lit.update(extra)
    return lit


def draw_world(f, t, rig, lit=None, interiors=None, curtains=None, street_depth=560.0, rain_k=1.0,
               sky=True, street=True, people=None, title=None, flare4=None, haze=1.0, rain_on=True):
    """The facade world through the rig, back to front: sky, neighbours, facade (+ window
    people), street, lamp, car, haze, [people in the street], [title], rain."""
    lit = lit if lit is not None else sets.NIGHT
    if sky:
        night_sky(f, t, rig)
    cam = rig.facade()
    f.set_camera(cam)
    sets.draw_blocks(f, t, BLOCKS, layer=dict(par=1.0, fog=0.28))
    FAC.draw(f, t, lit=lit, interiors=interiors or {}, curtains=curtains or {}, shops=SHOPS)
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
