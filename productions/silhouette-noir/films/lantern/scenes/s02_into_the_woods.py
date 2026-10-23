"""s02 · INTO THE WOODS: Saul Bass cut paper, animated on ones (style test v2, fluid).

One continuous camera, no cuts until the final black. Flat paper field, black trunk bars at
three depths, an amber disc of lantern light laid over the wood, the girl a precise paper
figure (engine.paperdoll): planted footfalls, IK knees, spring hair and scarf, a physical
lantern. Red only for the scarf, the bow and the flame.

Beats (scene time, s):
   -0.5  the title's iris opens on the lantern flame; the camera pulls back to the wood
    0-7  she walks right
    7.0  she stops at her brother's wooden horse; crouches; the camera pushes in on it;
         her hand takes it; she rises and hugs it as the camera eases back
    9.3  lifts the lantern high and looks ahead
   10.3  walks on, slower; the field darkens to night, the disc shrinks
   14.0  white eyes with red pupils open in the dark, one pair at a time; she stops, leans
         back, pulls the lantern in, trembling
   15.9  thrusts the lantern: the disc swells and throws rings; the eyes snap shut
   16.7  she runs
   18.2  two jagged black legs (The Man with the Golden Arm) stab down into the light;
         she looks up. 19.45 the light closes to the flame; 19.78 black
"""
import math
from functools import lru_cache

import cairo

from engine import bass, paperdoll as pd
from engine.core import clamp, lerp, ease, hash01, noise1
from engine.palette import PAPER, RED
from engine.timing import Cue
from films.lantern.scenes import s01_title as S1

FIELD = S1.FIELD
NIGHT = (0.105, 0.095, 0.088)
GREY = (0.60, 0.57, 0.52)
FAR_INK = (0.13, 0.12, 0.11)
AMBER = (0.95, 0.66, 0.24)
IRIS = S1.FLAME
GROUND_SCREEN = 1590.0               # where the ground line sits at zoom 1
LEAD = 160.0                         # camera leads her by this (she sits at screen x 380)

T_STOP = 7.0
T_LIFT = 9.3
T_EYES = 14.0
T_THRUST = 15.9
T_RUN = 16.7
T_LEG = 18.2
T_CLOSE = 19.45
T_BLACK = 19.78

SPEED = [(-2.0, 230.0), (6.45, 230.0), (7.0, 0.0), (10.3, 0.0), (10.8, 165.0), (13.95, 165.0),
         (14.4, 0.0), (T_RUN, 0.0), (T_RUN + 0.25, 640.0), (17.85, 640.0), (18.25, 0.0), (40.0, 0.0)]


def k(t, t0, dur, e="inout"):
    return ease(e, clamp((t - t0) / dur))


def track(keys, t):
    """Eased keys [(t, v), ...]: smoothstep between neighbours."""
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            u = clamp((t - t0) / max(t1 - t0, 1e-6))
            return lerp(v0, v1, u * u * (3 - 2 * u))
    return keys[-1][1]


@lru_cache(maxsize=1)
def fig():
    return pd.girl(RED)


@lru_cache(maxsize=1)
def walker():
    return pd.Walker(fig(), x0=0.0, speed=SPEED, t0=-3.0, t1=24.0)


def X(t):
    return walker().x(t)


X_TOY = None


def x_toy():
    return X(T_STOP) + 150.0


def x_eyes():
    return X(14.4)


def x_end():
    return X(18.4)


# ----------------------------------------------------------------------------- her pose
def crouch_w(t):
    return k(t, T_STOP + 0.15, 0.55) * (1 - k(t, T_STOP + 1.55, 0.6))


def pose(t, with_hold=True):
    W = walker()
    st = W.state(t)
    v, ph, run = st["speed"], st["phase"], st["run"]
    sw = clamp(v / 230.0, 0.0, 1.0)
    p = pd.Pose()
    c = crouch_w(t)
    p.crouch = 118.0 * c
    p.lean = 2.5 * sw + 13.0 * run + 30.0 * c + track(
        [(-3, 0), (T_EYES + 0.2, 0), (T_EYES + 0.6, -8), (T_THRUST, -8), (T_THRUST + 0.18, 9), (T_THRUST + 0.7, 0),
         (T_LEG + 0.3, 0), (T_LEG + 0.8, -6), (40, -6)], t)
    p.head = track([(-3, 0), (T_STOP - 0.6, 0), (T_STOP - 0.1, -22), (T_STOP + 1.7, -22), (T_STOP + 2.2, 0),
                    (T_LIFT + 0.3, 9), (T_LIFT + 1.4, 9), (T_LIFT + 1.9, 0), (T_EYES, 0), (T_EYES + 0.4, 7),
                    (T_THRUST + 0.6, 7), (T_RUN, 0), (T_LEG + 0.5, 0), (T_LEG + 1.1, 24), (40, 24)], t)
    # the lantern arm (near)
    sh = track([(-3, 26), (T_STOP, 26), (T_STOP + 0.6, 44), (T_STOP + 1.7, 44), (T_STOP + 2.1, 26),
                (T_LIFT, 26), (T_LIFT + 0.85, 124), (T_LIFT + 1.4, 124), (T_LIFT + 2.0, 26),
                (T_EYES + 0.3, 26), (T_EYES + 0.75, 6), (T_THRUST, 6), (T_THRUST + 0.16, 98),
                (T_THRUST + 0.75, 98), (T_RUN + 0.45, 40), (T_LEG + 0.3, 40), (T_LEG + 0.9, 64), (40, 64)], t)
    el = track([(-3, 36), (T_LIFT, 36), (T_LIFT + 0.85, -8), (T_LIFT + 1.4, -8), (T_LIFT + 2.0, 36),
                (T_EYES + 0.3, 36), (T_EYES + 0.75, 78), (T_THRUST, 78), (T_THRUST + 0.16, 0),
                (T_THRUST + 0.75, 0), (T_RUN + 0.45, 42), (40, 26)], t)
    fear = k(t, T_EYES + 0.5, 0.4) * (1 - k(t, T_THRUST, 0.1))
    sh += 3.5 * fear * math.sin(t * 47.0) + 2.0 * fear * noise1(t * 6, seed=2)
    p.arms["near"] = ("ang", sh, el)
    # the far arm: swings with the stride, reaches for the toy, then hugs it
    swing = ("ang", -22.0 * sw * math.sin(2 * math.pi * ph) - 30.0 * run, 14.0 + 50.0 * run)
    sh_pt = _shoulder(st, p)
    rest = (sh_pt[0] + 8.0, sh_pt[1] + fig().upper + fig().fore - 14.0)
    grab = (x_toy() - 18.0, -64.0)
    chest = (sh_pt[0] + 46.0, sh_pt[1] + 70.0)
    if t < T_STOP:
        p.arms["far"] = swing
    else:
        r1 = k(t, T_STOP + 0.35, 0.55, "inout3")        # reach down
        r2 = k(t, T_STOP + 1.3, 0.7, "inout3")          # lift to the chest
        tgt = (lerp(lerp(rest[0], grab[0], r1), chest[0], r2), lerp(lerp(rest[1], grab[1], r1), chest[1], r2))
        p.arms["far"] = ("ik", tgt)
        if with_hold and t >= T_STOP + 1.18:
            p.hold["far"] = lambda ctx, hc, deg: draw_toy(ctx, (hc[0] + 6.0, hc[1] + 50.0), 0.82, -6.0 * r2)
    p.springs = {"pony": pony(t), "scarf": scarf(t)}
    p.eye = 1.0 - _blink(t)
    p.gaze = 0.6 * k(t, T_EYES, 0.3) * (1 - k(t, T_THRUST + 0.7, 0.4))
    return st, p


def _blink(t):
    b = 0.0
    for tb in (3.1, T_LIFT + 1.6, T_EYES + 1.2, T_RUN - 0.4):
        b = max(b, 1.0 - clamp(abs(t - tb) / 0.07))
    return b


def _shoulder(st, p):
    P = (st["pelvis"][0], st["pelvis"][1] + p.crouch)
    a = math.radians(p.lean)
    sx, sy = fig().shoulder
    return (P[0] + sx * math.cos(a) - sy * math.sin(a), P[1] + sx * math.sin(a) + sy * math.cos(a))


def _head_point(t):
    st = walker().state(t)
    c = crouch_w(t)
    return (st["pelvis"][0] + 30.0 * c, st["pelvis"][1] + 118.0 * c - 320.0)


@lru_cache(maxsize=1)
def _springs():
    return (pd.Spring(_head_point, rest=lambda t: 6.0, freq=1.7, damping=0.28, gain=0.03, vel_gain=0.035, lo=-20, hi=70),
            pd.Spring(_head_point, rest=lambda t: 4.0, freq=1.3, damping=0.22, gain=0.035, vel_gain=0.04, lo=-30, hi=60))


def pony(t):
    return _springs()[0](t)


def scarf(t):
    return _springs()[1](t) + 3.0 * math.sin(t * 2.3)


@lru_cache(maxsize=1)
def _hand_table():
    """Near-hand world position at 120 Hz (the lantern's pivot), found by a dry draw."""
    S = cairo.ImageSurface(cairo.FORMAT_A8, 1, 1)
    C = cairo.Context(S)
    out = []
    for i in range(int(26 * 120)):
        t = -3.0 + i / 120.0
        st, p = pose(t, with_hold=False)
        j = fig().draw(C, st, p, {"ink": (0, 0, 0), "red": (0, 0, 0), "far": (0, 0, 0)})
        out.append(j["hand_near"])
    return out


def hand(t):
    T = _hand_table()
    f = clamp((t + 3.0) * 120.0, 0, len(T) - 1.001)
    a = int(f)
    u = f - a
    return (lerp(T[a][0], T[a + 1][0], u), lerp(T[a][1], T[a + 1][1], u))


class _Swing:
    """The lantern on its bail: a pendulum driven by the hand's acceleration, with a little
    wrist stiffness and air drag so a fast lift sways it but never flings it over."""

    def __init__(self, L=96.0, g=1800.0, damp=3.4, stiff=12.0, drive=0.75, dt=1.0 / 240.0, t0=-2.5, t1=23.0):
        n = int((t1 - t0) / dt) + 2
        th = om = 0.0
        self.t0, self.dt, self.out = t0, dt, []
        h = 1.0 / 120.0
        for i in range(n):
            t = t0 + i * dt
            p0, p1, p2 = hand(t - h), hand(t), hand(t + h)
            ax = (p2[0] - 2 * p1[0] + p0[0]) / (h * h)
            ay = (p2[1] - 2 * p1[1] + p0[1]) / (h * h)
            al = -(g * math.sin(th) + drive * (ax * math.cos(th) - ay * math.sin(th))) / L - damp * om - stiff * th
            om += al * dt
            th = clamp(th + om * dt, -0.9, 0.9)
            self.out.append(th)

    def angle(self, t):
        f = clamp((t - self.t0) / self.dt, 0.0, len(self.out) - 1.001)
        a = int(f)
        return lerp(self.out[a], self.out[a + 1], f - a)


@lru_cache(maxsize=1)
def swing():
    return _Swing()


# ----------------------------------------------------------------------------- the lantern
LANTERN = {
    "cap": bass.cut([(-30, -2), (30, -2), (38, 16), (-38, 16)], seed=31, amp=0.4),
    "ring": bass.cut([(-9, -18), (9, -18), (9, -2), (-9, -2)], seed=32, amp=0.3),
    "posts": [bass.cut([(x0, 14), (x0 + 7, 14), (x0 + 7, 92), (x0, 92)], seed=33 + i, amp=0.3)
              for i, x0 in enumerate((-36, -3.5, 29))],
    "base": bass.cut([(-40, 90), (40, 90), (34, 108), (-34, 108)], seed=36, amp=0.4),
    "glass": bass.cut([(-30, 14), (30, 14), (30, 92), (-30, 92)], seed=37, amp=0.3),
}


def lantern(t):
    """(hand, ring, angle, glass centre, flame) in world px."""
    h = hand(t)
    a = swing().angle(t)
    ring = (h[0] + math.sin(a) * 42.0, h[1] + 8.0 + math.cos(a) * 42.0)
    c = (ring[0] + math.sin(a) * 53.0, ring[1] + math.cos(a) * 53.0)
    fl = (ring[0] + math.sin(a) * 60.0, ring[1] + math.cos(a) * 60.0)
    return h, ring, a, c, fl


def draw_lantern(ctx, t, ink, flick):
    h, ring, a, c, _ = lantern(t)
    ctx.new_path()
    ctx.move_to(h[0], h[1] + 4)
    ctx.line_to(*ring)
    ctx.set_line_width(5.0)
    ctx.set_source_rgb(*ink)
    ctx.stroke()
    ctx.save()
    ctx.translate(*ring)
    ctx.rotate(-a)
    bass.fill_polys(ctx, [LANTERN["glass"]], AMBER)
    sway = 5.0 * noise1(t * 2.1, seed=3) - 30.0 * math.sin(a)
    bass.fill_polys(ctx, [S1.flame_pts((0.0, 68.0), 13.0 * flick, sway, 2)], RED)
    bass.fill_polys(ctx, [LANTERN["cap"], LANTERN["ring"], LANTERN["base"]] + LANTERN["posts"], ink)
    ctx.restore()


# ----------------------------------------------------------------------------- the toy
def _toy_polys(k=1.0, seed=25):
    S = lambda pts: [(x * k, y * k) for x, y in pts]
    c = lambda pts, s, a=0.4: bass.cut(S(pts), seed=seed + s, amp=a)
    return [
        bass.cut_ellipse((0.0, -56.0 * k), 38.0 * k, 17.0 * k, seed=seed, amp=0.3),
        c([(20, -66), (34, -104), (48, -114), (66, -104), (64, -94), (46, -92), (36, -60)], 1),
        c([(34, -108), (38, -126), (44, -110)], 2, 0.2),
        c([(-36, -64), (-58, -52), (-62, -32), (-48, -50), (-34, -50)], 3),
        c([(-28, -48), (-20, -48), (-20, -22), (-28, -22)], 4, 0.2),
        c([(-12, -48), (-4, -48), (-4, -22), (-12, -22)], 5, 0.2),
        c([(12, -48), (20, -48), (20, -22), (12, -22)], 6, 0.2),
        c([(26, -48), (34, -48), (34, -22), (26, -22)], 7, 0.2),
        c([(-46, -24), (46, -24), (46, -14), (-46, -14)], 8, 0.2),
        bass.cut_ellipse((-30.0 * k, -9.0 * k), 10.0 * k, 10.0 * k, seed=seed + 9, amp=0.2),
        bass.cut_ellipse((30.0 * k, -9.0 * k), 10.0 * k, 10.0 * k, seed=seed + 10, amp=0.2),
    ]


TOY = _toy_polys()


def draw_toy(ctx, foot, k=1.0, angle=0.0, ink=(0.02, 0.018, 0.016)):
    ctx.save()
    ctx.translate(*foot)
    ctx.rotate(math.radians(angle))
    ctx.scale(k, k)
    bass.fill_polys(ctx, TOY, ink)
    ctx.restore()


# ----------------------------------------------------------------------------- camera
@lru_cache(maxsize=8192)
def _smooth_x(tq):
    return sum(X(tq + i * 0.1) for i in range(-6, 7)) / 13.0


def track_cam(t):
    x = _smooth_x(round(t * 48.0) / 48.0)
    lead = LEAD + 90.0 * k(t, T_EYES - 0.6, 1.3) * (1 - k(t, T_THRUST + 0.4, 1.0)) + 70.0 * k(t, T_LEG - 0.4, 1.4)
    z = 1.0 + 0.06 * k(t, T_EYES, 1.6) * (1 - k(t, T_THRUST, 0.3)) + 0.10 * k(t, T_LEG, 1.6)
    # the push-in on the toy and back out
    push = k(t, T_STOP - 0.1, 1.0, "inout3") * (1 - k(t, T_STOP + 1.5, 1.3, "inout3"))
    z = lerp(z, 2.05, push)
    cx = lerp(x + lead, x_toy() - 40.0, push)
    ground_y = lerp(GROUND_SCREEN, 1330.0, push)
    cy = -(ground_y - 960.0) / z - 120.0 * k(t, T_LEG + 0.2, 1.6)
    return cx, cy, z


def to_screen(cam, p):
    cx, cy, z = cam
    return ((p[0] - cx) * z + 540.0, (p[1] - cy) * z + 960.0)


def camera(t):
    cam = track_cam(t)
    b = k(t, -0.5, 3.0, "inout3")
    if b >= 1.0:
        return cam
    fl = lantern(t)[4]
    z = math.exp(lerp(math.log(7.5), math.log(cam[2]), b))
    s_end = to_screen(cam, fl)
    sx, sy = lerp(IRIS[0], s_end[0], b), lerp(IRIS[1], s_end[1], b)
    return (fl[0] - (sx - 540.0) / z, fl[1] - (sy - 960.0) / z, z)


def apply(c, cam, par=1.0):
    cx, cy, z = cam
    zp = z ** par
    c.translate(540.0, 960.0)
    c.scale(zp, zp)
    c.translate(-cx * par, -cy)


# ----------------------------------------------------------------------------- the wood
def darkness(t):
    return k(t, 9.6, 4.8, "inout")


@lru_cache(maxsize=4096)
def _trunk(i, w, seed):
    polys = [bass.cut_rect(-w / 2, -3200.0, w / 2, 400.0, seed=seed * 1000 + i, amp=0.5, seg=(60.0, 160.0))]
    if hash01(seed, i, 5) < 0.55:
        y = -260.0 - 900.0 * hash01(seed, i, 6)
        sgn = 1 if hash01(seed, i, 7) < 0.5 else -1
        L = w * 1.4 + 80 * hash01(seed, i, 8)
        polys.append(bass.cut([(0, y), (sgn * L, y - 0.8 * L), (sgn * (L + 9), y - 0.8 * L + 13), (0, y + w * 0.45)],
                              seed=seed * 1000 + i + 7, amp=0.3))
    return polys


def draw_trunks(c, cam, par, spacing, wr, seed, color, avoid=None):
    cx, cy, z = cam
    zp = z ** par
    half = 600.0 / zp + 300.0
    x0, x1 = cx * par - half, cx * par + half
    c.save()
    apply(c, cam, par)
    for i in range(int(x0 // spacing) - 1, int(x1 // spacing) + 2):
        if hash01(seed, i) < 0.18:
            continue
        x = i * spacing + spacing * 0.7 * hash01(seed, i, 1)
        w = lerp(wr[0], wr[1], hash01(seed, i, 2))
        if avoid is not None and abs(x - avoid[0] * par) < avoid[1] + w / 2:
            continue
        c.save()
        c.translate(x, 0.0)
        bass.fill_polys(c, _trunk(i, round(w, 1), seed), color)
        c.restore()
    c.restore()


@lru_cache(maxsize=4096)
def _tuft(i):
    n = 3 + int(hash01(71, i) * 3)
    polys = []
    for j in range(n):
        x = (j - n / 2) * 11 + 6 * hash01(71, i, j)
        h = 22 + 40 * hash01(72, i, j)
        lean = (hash01(73, i, j) - 0.5) * 30
        polys.append(bass.cut([(x - 5, 4), (x + lean, -h), (x + 5, 4)], seed=i * 13 + j, amp=0.2))
    return polys


def draw_ground(c, cam, ink, t):
    cx, cy, z = cam
    x0, x1 = cx - 600.0 / z - 200, cx + 600.0 / z + 200
    bass.fill_polys(c, [[(x0, 0.0), (x1, 0.0), (x1, 3000.0), (x0, 3000.0)]], ink)
    for i in range(int(x0 // 85), int(x1 // 85) + 1):
        if hash01(70, i) < 0.4:
            continue
        x = i * 85 + 40 * hash01(74, i)
        c.save()
        c.translate(x, 2.0)
        c.rotate(math.radians(2.0 * math.sin(t * 1.3 + i)))       # a breath of wind
        bass.fill_polys(c, _tuft(i), ink)
        c.restore()


@lru_cache(maxsize=1)
def _disc():
    """The light: one cut disc of unit radius (scaled each frame: its edge never boils)."""
    return [(x / 400.0, y / 400.0) for x, y in bass.cut_ellipse((0.0, 0.0), 400.0, 400.0, seed=4, amp=0.6, max_len=70.0)]


def light_disc(c, center, r, color, alpha=1.0):
    c.save()
    c.translate(*center)
    c.scale(r, r)
    bass.fill_polys(c, [_disc()], color, alpha)
    c.restore()


# ----------------------------------------------------------------------------- the eyes
def eyes():
    xe = x_eyes()
    return [(xe + 430.0, -650.0, 1.00, T_EYES + 0.00),
            (xe + 610.0, -930.0, 0.80, T_EYES + 0.42),
            (xe + 400.0, -290.0, 0.72, T_EYES + 0.74),
            (xe + 640.0, -470.0, 1.15, T_EYES + 1.02),
            (xe + 520.0, -1180.0, 0.62, T_EYES + 1.30)]


def almond(cx, cy, w, h, n=20):
    top = [(cx + lerp(-w, w, i / n), cy - h * math.sin(math.pi * i / n) ** 0.8) for i in range(n + 1)]
    bot = [(cx + lerp(w, -w, i / n), cy + h * math.sin(math.pi * i / n) ** 0.8) for i in range(n + 1)]
    return top + bot


def draw_eyes(c, t, her):
    if t < T_EYES - 0.05 or t > T_THRUST + 0.6:
        return
    for j, (x, y, s, t_in) in enumerate(eyes()):
        o = clamp(bass.pop(t, t_in, 0.32))
        o *= 1.0 - k(t, T_THRUST + 0.06 + 0.035 * j, 0.12, "in3")
        ph = (t * 0.55 + j * 0.31) % 1.0
        o *= 1.0 - 0.95 * math.exp(-((ph - 0.5) / 0.035) ** 2)       # a slow blink, now and then
        if o <= 0.02:
            continue
        dx = her[0] - x
        look = clamp(dx / 900.0, -1.0, 1.0) * 16.0 * s
        for ex in (-52.0 * s, 52.0 * s):
            bass.fill_polys(c, [almond(x + ex, y, 40.0 * s, 20.0 * s * o)], PAPER)
            ph_ = 17.0 * s * o
            px = x + ex + look
            bass.fill_polys(c, [[(px - 6 * s, y - ph_), (px + 6 * s, y - ph_), (px + 6 * s, y + ph_), (px - 6 * s, y + ph_)]], RED)


# ----------------------------------------------------------------------------- render
LEGS = [(T_LEG, 1.0, 330.0, (920.0, -1650.0)), (T_LEG + 0.45, 0.8, 600.0, (1000.0, -1250.0))]


def render(f, t, T):
    bass.bass_scene(f, field=FIELD, paper=0.8, vignette=0.16, mottle=0.04)
    if t >= T_BLACK:
        with f.screen() as c:
            c.rectangle(0, 0, 1080, 1920)
            c.set_source_rgb(0.0, 0.0, 0.0)
            c.fill()
        return
    ink = f.pal.ink
    d = darkness(t)
    cam = camera(t)
    st, p = pose(t)
    h, ring, a, lc, flame = lantern(t)
    fl = math.exp(-max(0.0, t - T_THRUST - 0.12) * 2.6) * k(t, T_THRUST, 0.12, "out3")
    flick = 1.0 + 0.035 * noise1(t * 3.0, seed=7) + 0.015 * noise1(t * 11.0, seed=8)
    close = k(t, T_CLOSE, T_BLACK - T_CLOSE, "in3")
    lift = k(t, T_LIFT + 0.2, 0.5) * (1 - k(t, T_LIFT + 1.3, 0.5))
    R = 470.0 * (1.0 - 0.27 * d) * (1.0 + 0.5 * fl) * flick * (1.0 + 0.10 * lift) * (1.0 - 0.97 * close)
    with f.screen() as c:
        field = tuple(lerp(a_, b_, d) for a_, b_ in zip(FIELD, NIGHT))
        c.rectangle(0, 0, 1080, 1920)
        c.set_source_rgb(*field)
        c.fill()
        far = tuple(lerp(a_, b_, clamp(d * 1.15)) for a_, b_ in zip(GREY, NIGHT))
        draw_trunks(c, cam, 0.45, 150.0, (16.0, 44.0), 11, far)
        draw_trunks(c, cam, 1.0, 330.0, (46.0, 110.0), 23, ink)
        c.save()
        apply(c, cam)
        light_disc(c, lc, R, AMBER)
        if fl > 0.01:
            u = k(t, T_THRUST + 0.05, 0.9, "out3")
            for j, (r0, r1, w0) in enumerate(((1.05, 2.4, 70.0), (1.3, 3.4, 52.0), (1.6, 4.6, 36.0))):
                rr = R * lerp(r0, r1, u)
                bass.ring(c, lc, rr, w0 * (1 - u) + 1.5, AMBER, seed=5 + j, alpha=1.0 - 0.6 * u)
        draw_ground(c, cam, ink, t)
        if t < T_STOP + 1.18:
            draw_toy(c, (x_toy(), 2.0), 0.82, 0.0, ink)
        fig().draw(c, st, p, {"ink": ink, "red": RED, "far": (0.10, 0.09, 0.085)})
        draw_lantern(c, t, ink, flick * (1 + 0.6 * fl) * (1 - 0.6 * close))
        for (t0, g, dx, base) in LEGS:
            if t >= t0:
                xe = x_end()
                bass.jagged_arm(c, (xe + base[0], base[1]), (xe + dx, 6.0), ink, width=84.0,
                                grow=ease("out3", clamp((t - t0) / g)), jags=4, jag=0.9, claw=0.75, seed=int(dx))
        draw_eyes(c, t, st["pelvis"])
        c.restore()
        draw_trunks(c, cam, 1.8, 1500.0, (150.0, 230.0), 37, ink, avoid=(X(t) + 120.0, 560.0))


def motion_blur(t, T):
    if T_RUN + 0.1 < t < T_LEG + 0.3 or T_THRUST - 0.05 < t < T_THRUST + 0.5:
        return 4
    return 1


def steps():
    """Footfalls (scene time, running?) from the walker's plants."""
    W = walker()
    out = []
    for side in ("near", "far"):
        for i, _x in W.plants[side][1:]:
            t = W.t0 + i / pd.HZ
            if -0.5 <= t < T_BLACK and W.V[i] > 20.0:
                out.append((t, W.R[i] > 0.5))
    return sorted(out)


def lantern_angle(t):
    return swing().angle(t)


def cues(T):
    return [Cue(-0.5, "night wind through trees", gain_db=-14, dur=20.0),
            Cue(T_STOP + 1.2, "small wooden toy picked up, wheels rattle", gain_db=-14),
            Cue(T_EYES, "eyes opening: soft wet clicks, a low breath", gain_db=-12, dur=1.6),
            Cue(T_THRUST + 0.05, "lantern flare whoosh", gain_db=-8),
            Cue(T_LEG + 1.0, "chitinous stab into the ground", gain_db=-6)]
