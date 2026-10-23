"""OPPOSITE: the world, the light schedule and the one continuous camera (film time).

Two facades face the viewer across a street, drawn flat like a Saul Bass diagram: hers
(A, left) and his (B, right), four floors on one window grid. Everything is cut once with
fixed seeds and only transformed, so no edge ever boils. Both scenes draw this world at
film time, so the title flows into s02 with no transition (s01's last frame = s02's first).

World px, y down, street level y = 0. Times below are FILM times (s02 starts at 6.0).
"""
import math
from functools import lru_cache

import cairo

from engine import bass, paperdoll as pd
from engine.core import clamp, lerp, ease
from engine.palette import PAPER, RED

FIELD = (0.80, 0.765, 0.70)
AMBER = (0.95, 0.66, 0.24)
UNLIT = (0.20, 0.185, 0.17)
ROOM = (0.085, 0.078, 0.07)
DOOR = (0.21, 0.195, 0.18)
JAMB = (0.31, 0.29, 0.27)

FLOOR_H, FLOORS = 380.0, 4
ROOF = -FLOOR_H * FLOORS
WIN_W, WIN_H = 220.0, 280.0
BUILDINGS = {"A": dict(x0=-1060.0, x1=0.0, cols=(-800.0, -480.0, -160.0), stair=-990.0),
             "B": dict(x0=620.0, x1=1680.0, cols=(780.0, 1100.0, 1420.0), stair=1610.0)}
HER = ("w", "A", 2, 2)
HIS = ("w", "B", 0, 2)
FS = 0.40                                   # figures in windows are drawn at this scale
STREET_X = 310.0
LAMP_X = 310.0

# ----------------------------------------------------------------------------- the beats (film time)
T_PUSH = 4.6           # the title's camera pushes into her window
T_GLIDE_OUT = 9.8      # across the street to his window
T_ARGUE = 12.0
T_RAISE = 12.9
T_SLASH = 13.52
T_HIS_OFF = 13.9
T_GLIDE_BACK = 15.0
T_CUP = 16.6           # the cup slips from her hand
T_SHATTER = 17.0
T_STEP = 17.15
T_HIS_ON = 18.3        # he is standing there, looking at her
T_POINT = 19.4
T_HER_OFF = 21.2
T_LEAVE = 21.3
T_STAIR_B = (21.7, 22.2, 22.7)      # floors 3, 2, 1: coming down
T_DOOR_B = 23.15
T_LINE = (23.35, 24.85)            # the red dotted path across the street
T_DOOR_A = 24.9
T_STAIR_A = (25.45, 26.05)         # floors 1, 2: coming up, faster
T_HALL = 26.25                     # the line of light under her door
T_DOOR_PUSH = 27.2
T_FEET = 29.15
T_KNOB = (29.65, 30.15)
T_KEY_PUSH = 30.0
T_EYE = 30.95
T_BLACK = 31.9

# windows lit in the title, in rhythm (key, t_on)
TITLE_ON = [(("w", "B", 1, 3), 2.70), (("w", "A", 0, 1), 2.85), (("w", "B", 2, 1), 3.00), (("w", "A", 1, 3), 3.15),
            (HIS, 3.30), (("w", "A", 0, 3), 3.45), (("w", "B", 1, 0), 3.60), (("w", "A", 1, 0), 3.75),
            (("w", "B", 2, 3), 3.90), (HER, 4.10)]
LIGHT = {k: [(t, 99.0)] for k, t in TITLE_ON}
LIGHT[HIS] = [(3.30, T_HIS_OFF), (T_HIS_ON, 99.0)]
LIGHT[HER] = [(4.10, T_HER_OFF)]
LIGHT[("w", "A", 1, 3)] = [(3.15, 24.3)]
LIGHT[("w", "B", 2, 1)] = [(3.00, 24.6)]
LIGHT[("s", "B", 3)] = [(T_STAIR_B[0], T_STAIR_B[1])]
LIGHT[("s", "B", 2)] = [(T_STAIR_B[1], T_STAIR_B[2])]
LIGHT[("s", "B", 1)] = [(T_STAIR_B[2], T_DOOR_B)]
LIGHT[("d", "B")] = [(T_DOOR_B, T_DOOR_B + 0.45)]
LIGHT[("d", "A")] = [(T_DOOR_A, T_STAIR_A[0])]
LIGHT[("s", "A", 1)] = [(T_STAIR_A[0], T_STAIR_A[1])]
LIGHT[("s", "A", 2)] = [(T_STAIR_A[1], 99.0)]


def k(t, t0, dur, e="inout"):
    return ease(e, clamp((t - t0) / dur))


def light(key, t, snap=0.06):
    v = 0.0
    for t_on, t_off in LIGHT.get(key, ()):
        v = max(v, clamp((t - t_on) / snap) * (1.0 - clamp((t - t_off) / snap)))
    return v


# ----------------------------------------------------------------------------- geometry
def win_rect(b, col, fl):
    x = BUILDINGS[b]["cols"][col]
    fb = -fl * FLOOR_H
    return (x - WIN_W / 2, fb - 60.0 - WIN_H, x + WIN_W / 2, fb - 60.0)


def stair_rect(b, fl):
    x = BUILDINGS[b]["stair"]
    fb = -fl * FLOOR_H
    return (x - 40.0, fb - 300.0, x + 40.0, fb - 90.0)


def door_rect(b):
    x = BUILDINGS[b]["stair"]
    return (x - 48.0, -215.0, x + 48.0, 0.0)


def rect_of(key):
    if key[0] == "w":
        return win_rect(*key[1:])
    if key[0] == "s":
        return stair_rect(*key[1:])
    return door_rect(key[1])


def centre(r):
    return ((r[0] + r[2]) / 2.0, (r[1] + r[3]) / 2.0)


HER_R = win_rect("A", 2, 2)
HIS_R = win_rect("B", 0, 2)
DOOR_IN = (-205.0, -1070.0, -115.0, -870.0)          # her door, seen through her window
KNOB = (-128.0, -978.0)
KEYHOLE = (-128.0, -959.0)


def _cr(r, seed, amp=0.35):
    return bass.cut_rect(r[0], r[1], r[2], r[3], seed=seed, amp=amp, seg=(50.0, 140.0))


@lru_cache(maxsize=1)
def facade_polys():
    """Each building's ink mass with its cornice and roof furniture, cut once."""
    out = {}
    for i, (b, B) in enumerate(BUILDINGS.items()):
        x0, x1 = B["x0"], B["x1"]
        polys = [_cr((x0, ROOF, x1, 40.0), 10 + i),
                 _cr((x0 - 26.0, ROOF - 34.0, x1 + 26.0, ROOF + 6.0), 20 + i),
                 _cr((x0 - 12.0, -FLOOR_H - 14.0, x1 + 12.0, -FLOOR_H + 6.0), 30 + i)]   # string course
        if b == "A":
            polys.append(_cr((x0 + 120.0, ROOF - 210.0, x0 + 190.0, ROOF), 40))          # chimney
            polys.append(_cr((x0 + 108.0, ROOF - 226.0, x0 + 202.0, ROOF - 204.0), 41))
        else:
            # a water tower on legs
            polys.append(_cr((x1 - 330.0, ROOF - 330.0, x1 - 170.0, ROOF - 170.0), 42))
            polys.append(bass.cut([(x1 - 342.0, ROOF - 330.0), (x1 - 250.0, ROOF - 400.0), (x1 - 158.0, ROOF - 330.0)],
                                  seed=43, amp=0.3))
            for lx in (x1 - 320.0, x1 - 260.0, x1 - 200.0):
                polys.append(_cr((lx, ROOF - 172.0, lx + 12.0, ROOF), 44 + int(lx) % 7))
        out[b] = polys
    return out


@lru_cache(maxsize=256)
def window_poly(key):
    seed = 100 + sum((i + 1) * (ord(ch) if isinstance(ch, str) else 7 * ch) for i, ch in enumerate("".join(map(str, key))))
    return _cr(rect_of(key), seed % 997, amp=0.3)


def all_windows():
    keys = []
    for b in BUILDINGS:
        for fl in range(FLOORS):
            for col in range(3):
                keys.append(("w", b, col, fl))
            if fl >= 1:
                keys.append(("s", b, fl))
        keys.append(("d", b))
    return keys


# ----------------------------------------------------------------------------- camera
WIDE_Y = -1450.0                     # ground sits at screen y ~1480 in the wide
WIDE = (STREET_X, WIDE_Y, 0.36)
SEGMENTS = [  # (t0, t1, anchor, screen target, zoom, dip (log), ease)
    (0.0, 4.6, (STREET_X, WIDE_Y), (540.0, 960.0), 0.372, 0.0, "inout"),
    (T_PUSH, 6.6, centre(HER_R), (540.0, 980.0), 3.0, 0.0, "inout3"),
    (6.6, T_GLIDE_OUT, centre(HER_R), (540.0, 980.0), 3.2, 0.0, "inout"),
    (T_GLIDE_OUT, 12.0, centre(HIS_R), (540.0, 980.0), 3.3, math.log(3.2 / 1.25), "inout3"),
    (12.0, T_GLIDE_BACK, centre(HIS_R), (540.0, 980.0), 3.5, 0.0, "inout"),
    (T_GLIDE_BACK, 17.0, centre(HER_R), (540.0, 980.0), 3.2, math.log(3.4 / 1.25), "inout3"),
    (17.0, 18.0, centre(HER_R), (540.0, 980.0), 3.25, 0.0, "inout"),
    (18.0, 19.1, (STREET_X, -960.0), (540.0, 1000.0), 0.85, 0.0, "inout3"),
    (19.1, 21.0, (STREET_X, -960.0), (540.0, 1000.0), 0.88, 0.0, "inout"),
    # follow him: down his stairwell, across the street with the red path, up hers
    (21.0, 22.9, (1310.0, -800.0), (540.0, 960.0), 0.60, 0.0, "inout3"),
    (22.9, 25.1, (-690.0, -800.0), (540.0, 960.0), 0.60, 0.0, "inout"),
    (25.1, T_DOOR_PUSH, (-690.0, -800.0), (540.0, 960.0), 0.64, 0.0, "inout"),
    (T_DOOR_PUSH, 29.0, centre(DOOR_IN), (540.0, 960.0), 9.0, 0.0, "inout3"),
    (29.0, T_KEY_PUSH, centre(DOOR_IN), (540.0, 960.0), 9.6, 0.0, "inout"),
    (T_KEY_PUSH, 30.9, KEYHOLE, (540.0, 960.0), 190.0, 0.0, "in3"),
    (30.9, 32.5, KEYHOLE, (540.0, 960.0), 200.0, 0.0, "out3"),
]


def to_screen(cam, p):
    cx, cy, z = cam
    return ((p[0] - cx) * z + 540.0, (p[1] - cy) * z + 960.0)


@lru_cache(maxsize=64)
def _seg_start(i):
    if i == 0:
        return WIDE
    t0, t1, A, S, z, dip, e = SEGMENTS[i - 1]
    return _cam_in(i - 1, t1)


def _cam_in(i, t):
    t0, t1, A, S, z1, dip, e = SEGMENTS[i]
    c0 = _seg_start(i)
    s0 = to_screen(c0, A)
    u = ease(e, clamp((t - t0) / (t1 - t0)))
    z = math.exp(lerp(math.log(c0[2]), math.log(z1), u) - dip * math.sin(math.pi * u))
    sx, sy = lerp(s0[0], S[0], u), lerp(s0[1], S[1], u)
    return (A[0] - (sx - 540.0) / z, A[1] - (sy - 960.0) / z, z)


def camera(t):
    for i, seg in enumerate(SEGMENTS):
        if t < seg[1] or i == len(SEGMENTS) - 1:
            return _cam_in(i, t)
    return WIDE


def apply(c, cam):
    cx, cy, z = cam
    c.translate(540.0, 960.0)
    c.scale(z, z)
    c.translate(-cx, -cy)


# ----------------------------------------------------------------------------- figures
@lru_cache(maxsize=1)
def figs():
    return pd.woman(RED, 0), pd.man(RED, 0), pd.woman(RED, 1)


def _track(keys, t):
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            u = clamp((t - t0) / max(t1 - t0, 1e-6))
            return lerp(v0, v1, u * u * (3 - 2 * u))
    return keys[-1][1]


def her_x(t):
    return -172.0 - 46.0 * k(t, T_STEP, 0.6, "inout3") - 14.0 * k(t, T_POINT + 0.15, 0.4, "out3")


def her_pose(t, hold=True):
    p = pd.Pose()
    breathe = 1.2 * math.sin(t * 1.9)
    p.lean = breathe * 0.5 + _track([(0, 0), (T_STEP, 0), (T_STEP + 0.3, -9), (T_STEP + 0.9, -4), (T_POINT, -4),
                                     (T_POINT + 0.25, -12), (T_POINT + 0.9, -7), (99, -7)], t)
    p.head = _track([(0, 0), (7.4, 0), (7.8, 6), (8.3, 0), (99, 0)], t)
    sh = _track([(0, 34), (7.3, 34), (7.75, 64), (8.35, 64), (8.8, 34), (T_CUP - 0.1, 34), (T_CUP + 0.25, 22),
                 (T_STEP + 0.6, 8), (99, 8)], t)
    el = _track([(0, 100), (7.3, 100), (7.75, 128), (8.35, 128), (8.8, 100), (T_CUP - 0.1, 100), (T_CUP + 0.3, 40),
                 (T_STEP + 0.6, 24), (99, 24)], t)
    p.arms["near"] = ("ang", sh, el)
    fsh = _track([(0, -6), (T_STEP, -6), (T_STEP + 0.35, 118), (99, 118)], t)
    fel = _track([(0, 10), (T_STEP, 10), (T_STEP + 0.35, 104), (99, 104)], t)
    p.arms["far"] = ("ang", fsh, fel)
    if hold and t < T_CUP:
        p.hold["near"] = draw_cup
    p.eye = 1.0 - max(0.0, 1.0 - abs(t - 8.9) / 0.07) - max(0.0, 1.0 - abs(t - 11.3) / 0.07)
    return p


def draw_cup(ctx, hc, deg):
    ctx.save()
    ctx.translate(hc[0] + 4.0, hc[1] - 6.0)
    bass.fill_polys(ctx, [_CUP], (0.02, 0.018, 0.016))
    ctx.restore()


_CUP = bass.cut([(-14, -26), (18, -26), (14, 8), (-10, 8)], seed=61, amp=0.3)


@lru_cache(maxsize=1)
def cup_release():
    """World position of her cup at the moment it slips (a dry draw)."""
    s = cairo.ImageSurface(cairo.FORMAT_A8, 1, 1)
    j = figs()[0].draw(cairo.Context(s), pd.standing(figs()[0]), her_pose(T_CUP, hold=False),
                       {"ink": (0, 0, 0), "red": (0, 0, 0), "far": (0, 0, 0)}, facing=1)
    hx, hy = j["hand_near"]
    return (her_x(T_CUP) + hx * FS + 1.6, -FLOOR_H * 2 + hy * FS - 2.4)


def man_pose(t):
    """In his window: the quarrel and the knife (T_ARGUE..), then alone, pointing (T_HIS_ON..)."""
    p = pd.Pose()
    if t < T_HIS_ON:
        p.lean = 3.0 * math.sin(t * 5.0) * k(t, T_ARGUE, 0.3) * (1 - k(t, T_RAISE, 0.2)) + _track(
            [(0, 0), (T_RAISE, 0), (T_RAISE + 0.35, -6), (T_SLASH, -6), (T_SLASH + 0.12, 14), (99, 14)], t)
        sh = _track([(0, 14), (T_ARGUE, 14), (T_ARGUE + 0.3, 70), (T_ARGUE + 0.6, 30), (T_RAISE, 30),
                     (T_RAISE + 0.4, 168), (T_SLASH - 0.04, 172), (T_SLASH + 0.12, 64), (99, 64)], t)
        el = _track([(0, 10), (T_ARGUE, 10), (T_ARGUE + 0.3, 40), (T_ARGUE + 0.6, 20), (T_RAISE, 20),
                     (T_RAISE + 0.4, 18), (T_SLASH - 0.04, 22), (T_SLASH + 0.12, 4), (99, 4)], t)
        p.arms["near"] = ("ang", sh, el)
        p.arms["far"] = ("ang", 8.0 + 30.0 * k(t, T_ARGUE + 0.1, 0.3) * (1 - k(t, T_RAISE, 0.3)), 30.0)
        if t >= T_RAISE - 0.1:
            p.hold["near"] = draw_knife
    else:
        p.head = 2.0
        sh = _track([(0, 6), (T_POINT, 6), (T_POINT + 0.35, 92), (T_LEAVE, 92), (T_LEAVE + 0.3, 10), (99, 10)], t)
        el = _track([(0, 8), (T_POINT, 8), (T_POINT + 0.35, -4), (T_LEAVE, -4), (T_LEAVE + 0.3, 8), (99, 8)], t)
        p.arms["near"] = ("ang", sh, el)
        p.arms["far"] = ("ang", -4.0, 12.0)
        if t >= T_POINT + 0.05 and t < T_LEAVE + 0.1:
            p.hold["near"] = draw_point
    return p


def draw_knife(ctx, hc, deg):
    ctx.save()
    ctx.translate(*hc)
    ctx.rotate(math.radians(deg))
    bass.fill_polys(ctx, [_HILT], (0.02, 0.018, 0.016))
    bass.fill_polys(ctx, [_BLADE], PAPER)
    ctx.restore()


_HILT = bass.cut([(-6, -7), (16, -7), (16, 7), (-6, 7)], seed=62, amp=0.2)
_BLADE = bass.cut([(16, -9), (96, -3), (118, 4), (16, 9)], seed=63, amp=0.2)


def draw_point(ctx, hc, deg):
    """A Bass pointing hand over his fist: the index finger aimed at her window."""
    bass.pointing_hand(ctx, (hc[0] + 6.0 * math.cos(math.radians(deg)), hc[1] + 6.0 * math.sin(math.radians(deg))),
                       64.0, (0.02, 0.018, 0.016), angle=deg, seed=3)


def victim_pose(t):
    p = pd.Pose()
    p.lean = _track([(0, 0), (T_ARGUE + 0.4, 0), (T_ARGUE + 0.7, 5), (T_RAISE + 0.2, 5), (T_RAISE + 0.5, -14),
                     (T_SLASH + 0.1, -14), (T_SLASH + 0.3, -26), (99, -26)], t)
    sh = _track([(0, 10), (T_ARGUE + 0.3, 10), (T_ARGUE + 0.6, 80), (T_ARGUE + 0.85, 40), (T_RAISE + 0.2, 40),
                 (T_RAISE + 0.5, 128), (99, 128)], t)
    el = _track([(0, 20), (T_ARGUE + 0.3, 20), (T_ARGUE + 0.6, 30), (T_RAISE + 0.5, 70), (99, 70)], t)
    p.arms["near"] = ("ang", sh, el)
    p.arms["far"] = ("ang", sh * 0.8, el + 10)
    return p


def _draw_fig(c, fig, x, floor_y, pose, facing, colors):
    c.save()
    c.translate(x, floor_y)
    c.scale(FS, FS)
    out = fig.draw(c, pd.standing(fig), pose, colors, facing=facing)
    c.restore()
    return out


# ----------------------------------------------------------------------------- drawing
def _clip(c, r):
    c.save()
    c.new_path()
    c.rectangle(r[0], r[1], r[2] - r[0], r[3] - r[1])
    c.clip()


def draw_interior(c, t, ink):
    """Her room with the light off: the door, the line of light under it, the keyhole."""
    _clip(c, HER_R)
    c.rectangle(HER_R[0], HER_R[1], HER_R[2] - HER_R[0], HER_R[3] - HER_R[1])
    c.set_source_rgb(*ROOM)
    c.fill()
    d = DOOR_IN
    bass.fill_polys(c, [bass.cut_rect(d[0] - 7, d[1] - 7, d[2] + 7, d[3], seed=71, amp=0.15, seg=(20.0, 60.0))], JAMB)
    bass.fill_polys(c, [bass.cut_rect(d[0], d[1], d[2], d[3], seed=72, amp=0.12, seg=(20.0, 60.0))], DOOR)
    # panels, very quiet
    for (px0, py0, px1, py1) in ((d[0] + 12, d[1] + 14, d[2] - 12, d[1] + 86), (d[0] + 12, d[1] + 104, d[2] - 12, d[3] - 14)):
        bass.fill_polys(c, [[(px0, py0), (px1, py0), (px1, py1), (px0, py1)]], ROOM, alpha=0.35)
    hall = clamp((t - T_HALL) / 0.12)
    if hall > 0:
        y = d[3]
        x0, x1 = d[0] + 2.0, d[2] - 2.0
        c.rectangle(x0, y - 0.3, x1 - x0, 1.9)
        c.set_source_rgba(*AMBER, hall)
        c.fill()
        # two foot shadows step into the light
        for j, fx in enumerate((-176.0, -150.0)):
            w = 13.0 * k(t, T_FEET + 0.12 * j, 0.22, "out3")
            if w > 0.1:
                c.rectangle(fx - w / 2, y - 0.6, w, 2.6)
                c.set_source_rgb(*ROOM)
                c.fill()
    draw_keyhole(c, t, hall)
    # the lever handle: still, then it turns (twice)
    turn = 0.0
    for t0 in T_KNOB:
        turn = max(turn, math.sin(math.pi * clamp((t - t0) / 0.32)) ** 0.8)
    c.save()
    c.translate(*KNOB)
    bass.fill_polys(c, [bass.draw.circle_pts((0, 0), 5.2, n=24)], JAMB)
    c.rotate(math.radians(-38.0 * turn))
    bass.fill_polys(c, [[(-1.6, -1.8), (-17.0, -1.6), (-17.0, 1.8), (-1.6, 1.9)]], JAMB)
    c.restore()
    c.restore()


def keyhole_path(c):
    x, y = KEYHOLE
    c.new_path()
    c.arc(x, y, 2.6, math.radians(115), math.radians(65))
    c.line_to(x + 2.3, y + 8.0)
    c.line_to(x - 2.3, y + 8.0)
    c.close_path()


def draw_keyhole(c, t, hall):
    keyhole_path(c)
    c.set_source_rgb(*(AMBER if hall > 0 else ROOM))
    c.fill()
    if t < T_EYE - 0.25:
        return
    # his face blocks the hall light; the eye opens in the keyhole, looks, finds her
    c.save()
    keyhole_path(c)
    c.clip()
    dark = k(t, T_EYE - 0.25, 0.22)
    c.rectangle(KEYHOLE[0] - 5, KEYHOLE[1] - 5, 10, 16)
    c.set_source_rgba(*ROOM, dark)
    c.fill()
    o = k(t, T_EYE, 0.2, "out3")
    if o > 0.01:
        ex, ey = KEYHOLE[0], KEYHOLE[1] + 0.2
        w, h = 2.25, 1.15 * o
        top = [(ex + lerp(-w, w, i / 24.0), ey - h * math.sin(math.pi * i / 24.0) ** 0.8) for i in range(25)]
        bot = [(ex + lerp(w, -w, i / 24.0), ey + h * math.sin(math.pi * i / 24.0) ** 0.8) for i in range(25)]
        bass.fill_polys(c, [top + bot], PAPER)
        look = _track([(T_EYE, 0.0), (T_EYE + 0.2, 0.0), (T_EYE + 0.38, -1.0), (T_EYE + 0.55, -1.0),
                       (T_EYE + 0.75, 1.0), (T_EYE + 0.88, 1.0), (T_EYE + 1.02, 0.0), (99, 0.0)], t)
        grow = 1.0 + 0.18 * k(t, T_EYE + 0.98, 0.15, "out3")
        r = 0.62 * grow
        c.save()
        c.new_path()
        for i, p in enumerate(top + bot):
            (c.move_to if i == 0 else c.line_to)(*p)
        c.close_path()
        c.clip()
        bass.fill_polys(c, [bass.draw.circle_pts((ex + look * 1.1, ey), r, n=32)], RED)
        bass.fill_polys(c, [bass.draw.circle_pts((ex + look * 1.1, ey), r * 0.42, n=24)], (0.02, 0.018, 0.016))
        c.restore()
    c.restore()


def draw_window(c, key, t, ink):
    r = rect_of(key)
    L = light(key, t)
    if key == HER and L < 1.0 and t > 10.0:
        draw_interior(c, t, ink)
        if L <= 0.0:
            return
    poly = window_poly(key)
    if L < 1.0 and not (key == HER and t > 10.0):
        bass.fill_polys(c, [poly], UNLIT)
    if L > 0.0:
        bass.fill_polys(c, [poly], AMBER, alpha=L)
    if key == HER and L > 0.0:
        _clip(c, r)
        fw, _, _ = figs()
        _draw_fig(c, fw, her_x(t), -FLOOR_H * 2, her_pose(t), 1, {"ink": ink, "red": RED, "far": ink})
        c.restore()
    if key == HIS and L > 0.02:
        _clip(c, r)
        fw, fm, fv = figs()
        if t < T_HIS_ON:
            _draw_fig(c, fv, 842.0, -FLOOR_H * 2, victim_pose(t), -1, {"ink": ink, "red": RED, "far": ink})
            _draw_fig(c, fm, 736.0, -FLOOR_H * 2, man_pose(t), 1, {"ink": ink, "red": RED, "far": ink})
        else:
            x = 790.0 + 190.0 * k(t, T_LEAVE, 0.55, "in3")
            _draw_fig(c, fm, x, -FLOOR_H * 2, man_pose(t), -1, {"ink": ink, "red": RED, "far": ink})
        c.restore()


def draw_cup_fall(c, t, ink):
    if t < T_CUP or t > T_SHATTER + 0.2:
        return
    x0, y0 = cup_release()
    dt = t - T_CUP
    _clip(c, HER_R)
    c.save()
    c.translate(x0 - 18.0 * dt, y0 + 0.5 * 1900.0 * dt * dt)
    c.rotate(math.radians(-160.0 * dt))
    c.scale(FS, FS)
    bass.fill_polys(c, [_CUP], ink)
    c.restore()
    c.restore()


def draw_slash(c, t):
    if t < T_SLASH or t > T_HIS_OFF + 0.4:
        return
    r = HIS_R
    p0 = (r[0] - 40.0, r[1] + 30.0)
    p1 = (r[2] + 40.0, r[3] - 20.0)
    u = k(t, T_SLASH, 0.14, "out3")
    tail = k(t, T_HIS_OFF + 0.02, 0.3, "in3")
    bass.slash(c, p0, p1, RED, width=30.0, u=u, tail=tail, seed=7)


def red_path():
    xb, xa = BUILDINGS["B"]["stair"], BUILDINGS["A"]["stair"]
    return [(xb, 20.0), (xb, 120.0), (xa, 120.0), (xa, 20.0)]


def draw_red_line(c, t):
    if t < T_LINE[0]:
        return
    u = k(t, T_LINE[0], T_LINE[1] - T_LINE[0], "inout")
    fade = 1.0 - k(t, T_DOOR_PUSH + 0.6, 0.6)
    P = red_path()
    seg = [math.dist(a, b) for a, b in zip(P, P[1:])]
    total = sum(seg)
    step = 96.0
    n = int(total * u / step)
    for i in range(n + 1):
        s = i * step
        j = 0
        while j < len(seg) - 1 and s > seg[j]:
            s -= seg[j]
            j += 1
        a, b = P[j], P[j + 1]
        f = s / seg[j]
        x, y = lerp(a[0], b[0], f), lerp(a[1], b[1], f)
        horiz = abs(b[1] - a[1]) < 1e-6
        w, h = (58.0, 24.0) if horiz else (24.0, 58.0)
        bass.fill_polys(c, [[(x - w / 2, y - h / 2), (x + w / 2, y - h / 2), (x + w / 2, y + h / 2), (x - w / 2, y + h / 2)]],
                        RED, alpha=fade)


@lru_cache(maxsize=1)
def _lamp():
    x = LAMP_X
    return ([_cr((x - 7.0, -760.0, x + 7.0, 0.0), 81), _cr((x - 70.0, -768.0, x + 7.0, -756.0), 82),
             bass.cut([(x - 92.0, -760.0), (x - 48.0, -760.0), (x - 40.0, -744.0), (x - 100.0, -744.0)], seed=83, amp=0.2)],
            [bass.cut([(x - 94.0, -744.0), (x - 46.0, -744.0), (x - 54.0, -722.0), (x - 86.0, -722.0)], seed=84, amp=0.2)])


# ----------------------------------------------------------------------------- title parts
def grid_lines():
    xs, ys = set(), set()
    for b, B in BUILDINGS.items():
        xs.update((B["x0"], B["x1"]))
        for col in B["cols"]:
            xs.update((col - WIN_W / 2, col + WIN_W / 2))
    for fl in range(FLOORS):
        r = win_rect("A", 0, fl)
        ys.update((r[1], r[3]))
    ys.update((ROOF, 0.0))
    return sorted(xs), sorted(ys)


@lru_cache(maxsize=1)
def title():
    return bass.title_glyphs("OPPOSITE", width=2240.0, tracking=0.09, seed=2, rough=0.5, jitter=0.25)


TITLE_C = (STREET_X, -2560.0)


def draw_title(c, t, ink):
    if t > 9.0:
        return
    xs, ys = grid_lines()
    lw = 7.0
    for i, x in enumerate(xs):
        e_in = k(t, 0.10 + 0.045 * i, 0.55, "out3")
        e_out = k(t, 1.75 + 0.03 * i, 0.55, "in3")
        if e_in <= 0 or e_out >= 1:
            continue
        sgn = 1 if i % 2 == 0 else -1
        off = sgn * (1 - e_in) * 4200.0 - sgn * e_out * 4200.0
        c.rectangle(x - lw / 2, -3400.0 + off, lw, 3800.0)
    for j, y in enumerate(ys):
        e_in = k(t, 0.30 + 0.06 * j, 0.55, "out3")
        e_out = k(t, 1.85 + 0.04 * j, 0.55, "in3")
        if e_in <= 0 or e_out >= 1:
            continue
        sgn = 1 if j % 2 == 0 else -1
        off = sgn * (1 - e_in) * 5200.0 - sgn * e_out * 5200.0
        c.rectangle(-2400.0 + off, y - lw / 2, 5400.0, lw)
    c.set_source_rgb(*ink)
    c.fill()
    # the title rides in along its own grid line, which stays as a rule under it
    T = title()
    u = clamp((t - 2.0) / 1.1)
    if u > 0:
        bass.draw_title(c, T, TITLE_C, ink, u=u, anim="slide", frm="left", order="ltr", overlap=0.78, dist=2600.0)
    e = k(t, 1.9, 0.7, "out5")
    if e > 0:
        y = TITLE_C[1] + 245.0
        x0, x1 = BUILDINGS["A"]["x0"], BUILDINGS["B"]["x1"]
        c.rectangle(lerp(x1 + 3000.0, x0, e), y, x1 - x0, 10.0)
        c.set_source_rgb(*ink)
        c.fill()


# ----------------------------------------------------------------------------- the frame
def draw(f, t):
    """Draw OPPOSITE at film time t."""
    ink = f.pal.ink
    if t >= T_BLACK:
        with f.screen() as c:
            c.rectangle(0, 0, 1080, 1920)
            c.set_source_rgb(0.0, 0.0, 0.0)
            c.fill()
        return
    cam = camera(t)
    with f.screen() as c:
        c.rectangle(0, 0, 1080, 1920)
        c.set_source_rgb(*FIELD)
        c.fill()
        c.save()
        apply(c, cam)
        draw_title(c, t, ink)
        # the facades rise out of the street like a pop-up
        for i, b in enumerate(("A", "B")):
            rise = k(t, 1.30 + 0.15 * i, 0.95, "out3")
            if rise <= 0:
                continue
            c.save()
            c.translate(0.0, (1.0 - rise) * 1700.0)
            bass.fill_polys(c, facade_polys()[b], ink)
            for key in all_windows():
                if key[1] == b:
                    draw_window(c, key, t, ink)
            c.restore()
        lamp_u = k(t, 2.1, 0.5, "out3")
        if lamp_u > 0:
            c.save()
            c.translate(0.0, (1 - lamp_u) * 900.0)
            poles, heads = _lamp()
            bass.fill_polys(c, poles, ink)
            bass.fill_polys(c, heads, AMBER)
            c.restore()
        draw_cup_fall(c, t, ink)
        # the street
        c.rectangle(-4000.0, 0.0, 9000.0, 4000.0)
        c.set_source_rgb(*ink)
        c.fill()
        draw_red_line(c, t)
        draw_slash(c, t)
        c.restore()


def motion_blur_at(t):
    return 1                # crisp cut paper: averaged sub-frames read as ghosts here
