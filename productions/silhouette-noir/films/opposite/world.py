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

from engine import bass, mocap as mc, paperdoll as pd
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
T_SIP = 5.6            # she sips from her mug
T_HEAR = 8.4           # she hears them across the street ...
T_WALK = 8.6           # ... and walks to the window to look
D = 1.2                # everything after her walk runs this much later than in the first cut


def S(t):
    """A time from the first cut, shifted past her walk to the window."""
    return t + D


T_GLIDE_OUT = S(9.8)   # across the street to his window
T_QUARREL = S(10.6)    # the quarrel, already going as the camera arrives
T_SLASH = S(13.52)
T_RAISE = T_SLASH - 0.6            # the knife goes up (crash zoom)
T_HIS_OFF = S(14.15)   # his light goes out after she has fallen
T_GLIDE_BACK = S(15.0)
T_CUP = S(16.6)        # she startles; the mug flies from her hand
T_SHATTER = T_CUP + 0.48
T_STEP = T_CUP + 1.1   # she backs away from the window
T_HIS_ON = S(18.3)     # he is standing there, looking at her
T_POINT = S(19.4)
T_LEAVE = S(19.95)     # his arm drops; he turns and runs out of the room
T_TURN = T_LEAVE + 0.15
T_RUN = T_LEAVE + 0.38
T_REACH = S(20.95)     # she reaches up for the cord of her lamp
T_HER_OFF = S(21.45)
T_STAIR_B = (S(21.7), S(22.2), S(22.7))      # floors 3, 2, 1: coming down
T_DOOR_B = S(23.15)
T_LINE = (S(23.35), S(24.85))                # the red dotted path across the street
T_DOOR_A = S(24.9)
T_STAIR_A = (S(25.45), S(26.05))             # floors 1, 2: coming up, faster
T_HALL = S(26.25)                            # the line of light under her door
T_DOOR_PUSH = S(27.2)
T_FEET = S(29.15)
T_KNOB = (S(29.65), S(30.15))
T_KEY_PUSH = S(30.0)
T_EYE = S(30.95)
T_BLACK = S(31.9)

# windows lit in the title, in rhythm (key, t_on)
TITLE_ON = [(("w", "B", 1, 3), 2.70), (("w", "A", 0, 1), 2.85), (("w", "B", 2, 1), 3.00), (("w", "A", 1, 3), 3.15),
            (HIS, 3.30), (("w", "A", 0, 3), 3.45), (("w", "B", 1, 0), 3.60), (("w", "A", 1, 0), 3.75),
            (("w", "B", 2, 3), 3.90), (HER, 4.10)]
LIGHT = {k: [(t, 99.0)] for k, t in TITLE_ON}
LIGHT[HIS] = [(3.30, T_HIS_OFF), (T_HIS_ON, 99.0)]
LIGHT[HER] = [(4.10, T_HER_OFF)]
LIGHT[("w", "A", 1, 3)] = [(3.15, S(24.3))]
LIGHT[("w", "B", 2, 1)] = [(3.00, S(24.6))]
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
HER_C, HIS_C = centre(HER_R), centre(HIS_R)
KNIFE_C = (HIS_C[0] + 10.0, HIS_C[1] - 40.0)
CORD_C = (-125.0, -1000.0)
SEGMENTS = [  # (t0, t1, anchor, screen target, zoom, dip (log), ease)
    (0.0, 4.6, (STREET_X, WIDE_Y), (540.0, 960.0), 0.372, 0.0, "inout"),
    (T_PUSH, 6.6, HER_C, (540.0, 980.0), 3.0, 0.0, "inout3"),
    (6.6, T_GLIDE_OUT, HER_C, (540.0, 980.0), 3.15, 0.0, "inout"),
    (T_GLIDE_OUT, S(12.0), HIS_C, (540.0, 980.0), 3.3, math.log(3.2 / 1.25), "inout3"),
    (S(12.0), T_RAISE, HIS_C, (540.0, 980.0), 3.55, 0.0, "inout"),
    # crash zoom on the knife, held through the fall and the dark
    (T_RAISE, T_RAISE + 0.28, KNIFE_C, (540.0, 960.0), 4.7, 0.0, "out3"),
    (T_RAISE + 0.28, T_HIS_OFF + 0.3, KNIFE_C, (540.0, 960.0), 4.85, 0.0, "inout"),
    (T_HIS_OFF + 0.3, T_GLIDE_BACK, HIS_C, (540.0, 980.0), 3.4, 0.0, "inout"),
    # whip back to her, then a slow push while the mug falls
    (T_GLIDE_BACK, S(15.85), HER_C, (540.0, 980.0), 3.3, math.log(3.4), "inout3"),
    (S(15.85), S(18.0), HER_C, (540.0, 980.0), 3.75, 0.0, "inout"),
    (S(18.0), S(18.85), (STREET_X, -960.0), (540.0, 1000.0), 0.85, 0.0, "inout3"),
    # a push lands on him as he points, then creeps on; whip to her and the cord
    (S(18.85), S(19.5), HIS_C, (540.0, 1000.0), 1.6, 0.0, "inout3"),
    (S(19.5), S(20.9), HIS_C, (540.0, 1000.0), 1.9, 0.0, "inout"),
    (S(20.9), S(21.3), CORD_C, (540.0, 960.0), 3.3, math.log(1.7), "inout3"),
    (S(21.3), S(21.65), CORD_C, (540.0, 960.0), 3.45, 0.0, "inout"),
    # follow him: down his stairwell, across the street with the red path, up hers
    (S(21.65), S(22.9), (1310.0, -800.0), (540.0, 960.0), 0.60, 0.0, "inout3"),
    (S(22.9), S(25.1), (-690.0, -800.0), (540.0, 960.0), 0.60, 0.0, "inout"),
    (S(25.1), T_DOOR_PUSH, (-690.0, -800.0), (540.0, 960.0), 0.64, 0.0, "inout"),
    (T_DOOR_PUSH, S(29.0), centre(DOOR_IN), (540.0, 960.0), 9.0, 0.0, "inout3"),
    (S(29.0), T_KEY_PUSH, centre(DOOR_IN), (540.0, 960.0), 9.6, 0.0, "inout"),
    (T_KEY_PUSH, S(30.9), KEYHOLE, (540.0, 960.0), 190.0, 0.0, "in3"),
    (S(30.9), S(32.5), KEYHOLE, (540.0, 960.0), 200.0, 0.0, "out3"),
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


def tilt(t):
    """Dutch angle (deg): the frame leans while he watches her, and again at her door."""
    return (-4.5 * k(t, T_HIS_ON - 0.3, 1.2) * (1.0 - k(t, S(21.65), 0.8))
            + 3.5 * k(t, T_FEET - 0.6, 1.0) * (1.0 - k(t, T_KEY_PUSH, 0.6)))


def shake(t):
    """Screen jolt (px) on the knife, the cup, his point and the eye."""
    a = 0.0
    for t0, amp in ((T_SLASH, 18.0), (T_SHATTER, 6.0), (T_POINT + 0.1, 8.0), (T_EYE + 0.98, 12.0)):
        if t >= t0:
            a += amp * math.exp(-(t - t0) / 0.12)
    return (a * math.sin(t * 91.0), 0.7 * a * math.cos(t * 73.0))


def apply(c, cam, t=None):
    cx, cy, z = cam
    c.translate(540.0, 960.0)
    if t is not None:
        c.translate(*shake(t))
        c.rotate(math.radians(tilt(t)))
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


def _reach(fig, st, pose, target, facing=1, bend=1.0):
    """("ang") shoulder and elbow angles that put the wrist on target (figure units)."""
    q = pd._rot(fig.shoulder, pose.lean)
    s = (st["pelvis"][0] + facing * q[0], st["pelvis"][1] + pose.crouch + q[1])
    e, w = pd.ik2(s, target, fig.upper, fig.fore, forward=bend * facing)
    a1 = math.degrees(math.atan2(facing * (e[0] - s[0]), e[1] - s[1]))
    a2 = math.degrees(math.atan2(facing * (w[0] - e[0]), w[1] - e[1]))
    return a1 - pose.lean, (a2 - a1 + 180.0) % 360.0 - 180.0


# ----------------------------------------------------------------------------- performances
# Real motion capture (engine.mocap: CMU Graphics Lab Motion Capture Database), seen from the
# side and retargeted onto the paper figures. Performances run in figure units around x = 0;
# the window drawing places them at HER_X / MAN_X / VIC_X.
HER_X = -245.0
MAN_X, MAN_X2, VIC_X = 736.0, 790.0, 842.0
Q0 = T_QUARREL - 1.2                 # the quarrel is already going when the camera arrives


@lru_cache(maxsize=1)
def her_perf():
    C = mc.Clip.load
    return mc.Performance(figs()[0], [
        mc.Seg(C("137_26"), 0.3, 2.3, at=1.6, speed=0.5),                          # mug at her chest
        mc.Seg(C("137_26"), 7.0, 9.9, at=T_SIP),                                   # a sip
        mc.Seg(C("137_26"), 2.3, 3.2, at=T_WALK),                                  # to the window, mug in hand
        mc.Seg(C("137_26"), 5.55, 6.4, at=T_WALK + 0.9, blend=0.35),               # she stops at the glass
        mc.Seg(C("137_26"), 6.3, 6.4, at=T_WALK + 1.75, speed=0.05, lean=9.0, blend=0.6),  # peering out
        mc.Seg(C("120_15"), 3.45, 4.4, at=T_CUP - 0.15, travel=0.0, blend=0.12),   # the startle
        mc.Seg(C("76_03"), 2.2, 3.6, at=T_STEP, lean=-16.0, travel=2.0, blend=0.3),   # backing away
        mc.Seg(C("79_73"), 3.6, 5.3, at=T_STEP + 1.4, blend=0.4),                  # frozen
    ], facing=1, near="Right")


@lru_cache(maxsize=1)
def man_perfs():
    """(the quarrel and the knife, alone at the glass pointing, the run out)."""
    C = mc.Clip.load
    fm = figs()[1]
    quarrel = mc.Performance(fm, [
        mc.Seg(C("80_48"), 2.2, 2.2 + (T_SLASH - 1.35 - Q0), at=Q0),
        mc.Seg(C("86_04"), 42.3, 43.05, at=T_SLASH - 1.35, speed=0.6, near="Right", blend=0.3),   # the knife goes up
        mc.Seg(C("86_04"), 43.05, 44.4, at=T_SLASH - 0.1, near="Right", blend=0.04),             # and comes down
    ], facing=1, near="Left")
    alone = mc.Performance(fm, [
        mc.Seg(C("80_48"), 8.6, 9.4, at=T_HIS_ON - 0.3, speed=0.5),
        mc.Seg(C("80_48"), 5.7, 6.05, at=T_POINT - 0.2),                               # the arm comes up
        mc.Seg(C("80_48"), 6.05, 6.15, at=T_POINT + 0.15, speed=0.2, blend=0.1),       # and holds on her
        mc.Seg(C("80_48"), 8.6, 8.8, at=T_LEAVE, blend=0.3),
    ], facing=-1, near="Left")
    x = alone.raw(T_TURN + 0.125)["pelvis"][0]
    run = mc.Performance(fm, [mc.Seg(C("80_48"), 8.8, 8.8, at=T_TURN),
                              mc.Seg(C("09_01"), 0.0, 1.6, at=T_RUN, blend=0.2)], facing=1, x=-x, near="Left")
    return quarrel, alone, run


@lru_cache(maxsize=1)
def vic_perf():
    C = mc.Clip.load
    return mc.Performance(figs()[2], [
        mc.Seg(C("80_48"), 4.0, 4.0 + (T_RAISE + 0.05 - Q0), at=Q0),                  # she argues back
        mc.Seg(C("79_73"), 0.45, 1.6, at=T_RAISE + 0.05, lean=-12.0),                  # hands up to her face
        mc.Seg(C("90_18"), 0.55, 1.6, at=T_SLASH + 0.05, blend=0.12),                  # goes over backward
    ], facing=-1, near="Left")


def victim_pose(t):
    """(state, pose): her captured quarrel and fall, with her arms thrown up over her face as
    the knife goes up."""
    st, p = vic_perf()(t)
    w = k(t, T_RAISE + 0.1, 0.25, "out3") * (1.0 - k(t, T_SLASH + 0.05, 0.12))
    if w > 0.0:
        p.arms["near"] = _toward(p.arms["near"], 150.0, 95.0, w)
        p.arms["far"] = _toward(p.arms["far"], 128.0, 105.0, w)
    return st, p


def foot_contacts(state_fn, t0, t1, hz=120.0):
    """Times a foot comes down onto the floor (for footsteps), from a state function."""
    out = []
    prev = None
    up = [False, False]
    lift = [-5.0, -5.0]
    for i in range(int((t1 - t0) * hz) + 1):
        t = t0 + i / hz
        st = state_fn(t)
        ys = [st["feet"][side][1] for side in ("near", "far")]
        if prev is not None:
            for i_, (a, b) in enumerate(zip(prev, ys)):
                if a < lift[i_]:
                    up[i_] = True
                if up[i_] and b >= -3.2:
                    up[i_] = False
                    if not out or t - out[-1] > 0.12:
                        out.append(t)
        prev = ys
    return out


def _toward(arm, sh, el, w):
    return ("ang", arm[1] + mc._wrap(sh - arm[1]) * w, arm[2] + mc._wrap(el - arm[2]) * w)


def her_scale(t):
    """She comes up to the glass (a little bigger), and shrinks back into the room."""
    return 1.0 + 0.15 * k(t, T_WALK + 0.3, 1.6) * (1.0 - k(t, T_STEP, 1.2))


def her_world_x(st, lx, t):
    """World x of figure-unit x lx, with her scale taken about her pelvis."""
    px = st["pelvis"][0]
    return HER_X + FS * (px + her_scale(t) * (lx - px))


@lru_cache(maxsize=1)
def cord_home():
    """The bead of her lamp's pull cord (world), just in front of where she ends up."""
    st, _ = her_perf()(T_REACH)
    return (her_world_x(st, st["pelvis"][0], T_REACH) + 40.0, -1046.0)


def cord_pull(t):
    """World px she has pulled the cord down."""
    return 22.0 * k(t, T_HER_OFF - 0.14, 0.14, "in")


def her_pose(t, hold=True):
    """(state, pose): the mocap performance plus her hand to her mouth and the reach for the cord."""
    fig = figs()[0]
    st, p = her_perf()(t)
    w = k(t, T_CUP + 0.3, 0.2)
    if w > 0.0:
        p.arms["far"] = _toward(p.arms["far"], 72.0, 142.0, w)
    w = k(t, T_REACH, 0.32, "inout3")
    if w > 0.0:
        cx, cy = cord_home()
        m = her_scale(t)
        tgt = (st["pelvis"][0] + (cx - her_world_x(st, st["pelvis"][0], t)) / (FS * m),
               (cy + 3.0 + cord_pull(t) + FLOOR_H * 2) / (FS * m))
        p.arms["near"] = _toward(p.arms["near"], *_reach(fig, st, p, tgt), w)
        p.head = lerp(p.head, 16.0, w)
    if hold and t < T_CUP:
        p.hold["near"] = lambda ctx, hc, deg: draw_mug(ctx, hc, deg, t)
    p.eye = 1.0 - max(0.0, 1.0 - abs(t - 7.9) / 0.07) - max(0.0, 1.0 - abs(t - 10.3) / 0.07)
    return st, p


def _mug_shape(ctx, ink, steam_t=None):
    """A coffee mug (handle at the back) with steam curling off it; origin at the hand."""
    bass.fill_polys(ctx, [_MUG], ink)
    ctx.save()
    ctx.new_path()
    ctx.arc(-17.0, -6.0, 10.0, math.radians(90), math.radians(270))
    ctx.set_line_width(5.5)
    ctx.set_source_rgb(*ink)
    ctx.stroke()
    if steam_t is not None:
        ctx.set_line_width(3.2)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        for j, x0 in enumerate((-4.0, 6.0)):
            ctx.new_path()
            for i in range(14):
                u = i / 13.0
                x = x0 + 5.0 * math.sin(2 * math.pi * (u * 1.2 - steam_t * 0.9) + j * 2.0) * u
                y = -30.0 - 46.0 * u
                (ctx.move_to if i == 0 else ctx.line_to)(x, y)
            ctx.set_source_rgba(*PAPER, 0.75)
            ctx.stroke()
    ctx.restore()


def draw_mug(ctx, hc, deg, t):
    tilt = clamp(-deg - 55.0, 0.0, 75.0)          # tipped toward her lips when she drinks
    ctx.save()
    ctx.translate(hc[0] + 10.0, hc[1] - 4.0)
    ctx.rotate(math.radians(-tilt))
    _mug_shape(ctx, (0.02, 0.018, 0.016), steam_t=t if tilt < 20.0 else None)
    ctx.restore()


_MUG = bass.cut([(-14, -28), (16, -28), (15, 12), (-13, 12)], seed=61, amp=0.2)


@lru_cache(maxsize=1)
def cup_release():
    """World position of her mug at the moment she startles (a dry draw)."""
    s = cairo.ImageSurface(cairo.FORMAT_A8, 1, 1)
    st, p = her_pose(T_CUP, hold=False)
    j = figs()[0].draw(cairo.Context(s), st, p, {"ink": (0, 0, 0), "red": (0, 0, 0), "far": (0, 0, 0)}, facing=1)
    hx, hy = j["hand_near"]
    m = her_scale(T_CUP)
    return (her_world_x(st, hx + 10.0, T_CUP), -FLOOR_H * 2 + (hy - 4.0) * FS * m)


def man_pose(t):
    """(state, pose, facing, sx) for him: quarrel and knife; alone pointing; the paper turn; the run."""
    quarrel, alone, run = man_perfs()
    if t < T_HIS_ON:
        st, p = quarrel(t)
        # the knife arm: high over his head (Psycho), then one stab down; the body stays captured
        S_ = k(t, T_SLASH - 0.07, 0.1, "out")
        w = k(t, T_RAISE, 0.32, "out3") * (1.0 - k(t, T_SLASH + 0.5, 0.5))
        if w > 0.0:
            p.arms["near"] = _toward(p.arms["near"], lerp(170.0, 30.0, S_) - p.lean * (1.0 - S_),
                                     lerp(30.0, 0.0, S_), w)
        if t >= T_RAISE - 0.2:                        # overhand grip: the blade hangs from the fist
            off = lerp(150.0, 70.0, S_)
            p.hold["near"] = lambda ctx, hc, deg: draw_knife(ctx, hc, deg + off)
        return st, p, 1, 1.0
    sx = math.cos(math.pi * k(t, T_TURN, 0.25))
    if sx > 0.0:
        st, p = alone(t)
        w = k(t, T_POINT - 0.1, 0.22, "out3") * (1.0 - k(t, T_LEAVE, 0.25))
        if w > 0.0:                                   # the point is aimed level, straight at her window
            p.arms["near"] = _toward(p.arms["near"], 96.0 - p.lean, -4.0, w)
        if T_POINT + 0.05 <= t < T_LEAVE + 0.1:
            p.hold["near"] = draw_point
        return st, p, -1, max(sx, 0.04)
    st, p = run(t)
    return st, p, 1, max(-sx, 0.04)


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


def _draw_fig(c, fig, x, floor_y, pose, facing, colors, st=None, sx=1.0, m=1.0):
    """Draw a figure at FS on a floor; sx squashes it about the pelvis (a paper-doll turn),
    m scales it about the pelvis and the floor (nearer the glass)."""
    st = st or pd.standing(fig)
    c.save()
    c.translate(x, floor_y)
    c.scale(FS, FS)
    if sx != 1.0 or m != 1.0:
        px = st["pelvis"][0]
        c.translate(px, 0.0)
        c.scale(sx * m, m)
        c.translate(-px, 0.0)
    out = fig.draw(c, st, pose, colors, facing=facing)
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
        draw_lamp(c, t, ink)
        st, p = her_pose(t)
        _draw_fig(c, figs()[0], HER_X, -FLOOR_H * 2, p, 1, {"ink": ink, "red": RED, "far": ink}, st=st, m=her_scale(t))
        c.restore()
    if key == HIS and L > 0.02:
        _clip(c, r)
        fw, fm, fv = figs()
        cols = {"ink": ink, "red": RED, "far": ink}
        if t < T_HIS_ON:
            st, p = victim_pose(t)
            _draw_fig(c, fv, VIC_X, -FLOOR_H * 2, p, -1, cols, st=st)
            st, p, facing, sx = man_pose(t)
            _draw_fig(c, fm, MAN_X, -FLOOR_H * 2, p, facing, cols, st=st)
        else:
            st, p, facing, sx = man_pose(t)
            _draw_fig(c, fm, MAN_X2, -FLOOR_H * 2, p, facing, cols, st=st, sx=sx)
        c.restore()


@lru_cache(maxsize=1)
def _her_lamp():
    x, y = cord_home()[0] - 14.0, LAMP_TOP
    flex = _cr((x - 1.3, y - 10.0, x + 1.3, y + 16.0), 87, amp=0.05)
    shade = bass.cut([(x - 12.0, y + 14.0), (x + 12.0, y + 14.0), (x + 27.0, y + 36.0), (x - 27.0, y + 36.0)], seed=86, amp=0.15)
    return x, [flex, shade]


LAMP_TOP = -1100.0


def draw_lamp(c, t, ink):
    """Her pendant lamp: shade, bulb, and the pull cord she will reach for."""
    x, polys = _her_lamp()
    y = LAMP_TOP
    bass.fill_polys(c, [bass.draw.ellipse_pts((x, y + 37.0), 8.0, 4.5, n=20)], PAPER)
    bass.fill_polys(c, polys, ink)
    cx, cy = cord_home()
    cy += cord_pull(t)
    c.rectangle(cx - 0.6, y + 34.0, 1.2, cy - (y + 34.0))
    c.set_source_rgb(*ink)
    c.fill()
    bass.fill_polys(c, [bass.draw.circle_pts((cx, cy), 2.2, n=16)], ink)


def draw_cup_fall(c, t, ink):
    if t < T_CUP or t > T_SHATTER + 0.2:
        return
    x0, y0 = cup_release()
    dt = t - T_CUP
    _clip(c, HER_R)
    c.save()
    c.translate(x0 + 30.0 * dt, y0 - 90.0 * dt + 0.5 * 1900.0 * dt * dt)     # flung up a little, then down
    c.rotate(math.radians(-260.0 * dt))
    c.scale(FS * her_scale(T_CUP), FS * her_scale(T_CUP))
    _mug_shape(c, ink)
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
        apply(c, cam, t)
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
    """Crisp cut paper (one sample) unless the camera whips; then enough sub-frames across
    the shutter that the smear reads as blur, not as ghosts."""
    h = 0.25 / 24.0
    a, b = camera(t - h), camera(t + h)
    move = max(math.hypot(a[0] - b[0], a[1] - b[1]) * max(a[2], b[2]), 960.0 * abs(math.log(b[2] / a[2])))
    if move < 20.0:
        return 1
    return int(min(14, 3 + move / 8.0))
