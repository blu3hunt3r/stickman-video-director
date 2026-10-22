"""s12 · MOSTLY · 12.0 s · her window -> through the crack -> the street -> the facade lock.
The film's last scene: one continuous shot, ends on black (held).

A pinhole camera moves through a few flat planes (each drawn with its own Camera, so the
parallax is exact): her room's window wall (2.5 m ahead at the start), HER (2.32 m), the
facade across the street (20.5 m), the far skyline, and 3D rain in between.

  IN       (dissolve from s11's red doll) she stands at the glass, back to us, binoculars at
           her eyes, elbows out: the doll's W, at the same place and size (head ~(540, 905)).
  0.45     she lowers them; 1.15-1.60 sets them down on the sill (they stay there).
  1.0-2.9  L27 "I don't watch the windows anymore." She reaches right for the curtain's
           edge (1.95), pulls it across (accelerating), lets go at 2.60 and it slides home
           on its rings by 2.90. Dark.
  2.9-4.2  she stands in front of the closed curtain; her head drops. The camera creeps in.
  4.2-4.9  L28 "Mostly." She turns into profile, her fingers part the curtain (4.25-4.55): a
           slit of cold light, one eye glints in it (4.55). [4.72] across the street a new
           window (14, her floor, one to the right) lights up warm, framed in the slit.
  7.2-9.8  L29 "Be honest... would you have crossed the street?" The camera slips past her
           face, through the crack and the wet glass (7.95), out into the rain over the
           street, and settles on the facade lock (9.45, s01's grid). [street] 9.26: in dark
           window 9 the glint of binoculars looks straight at us.
  10.0-    the lights go out one by one, closing in on window 9 (Bass stagger, crisp):
           street lamp, diner, lobby, the neighbours, then 37 30 26 23 19 12 14 2 7 4; the
           glint last (11.50). Black from 11.70, held to 12.0.
"""
import math

import cairo
import numpy as np

from engine import draw
from engine import figure as FG
from engine.core import H, W, clamp, ease, fbm1, hash01, lerp, noise1
from engine.figure import Body, Look, Pose
from engine.frame import Camera
from engine.timing import Cue
from films.shadowplay.sets_base import AMBER, HOT, INK, PAL, PX_M, RAIN, glow, glow_ellipse, mix, mul, switch
from films.shadowplay.sets_facade import Block, Facade, NIGHT, Skyline, draw_blocks, neighbours, night_sky
from films.shadowplay.sets_props import binoculars as draw_binoculars
from films.shadowplay.sets_rooms import HerRoom
from films.shadowplay.sets_street import Car, Street, Streetlamp
from films.shadowplay.scenes import _lib_s11_s12 as lib

# ----------------------------------------------------------------------------- 3D layout
F = 600.0                                   # focal length, screen px
ROOM = HerRoom((540.0, 1800.0), 1.0)
FAC = Facade((540.0, 3940.0), 1.0)
K_ROOM = PX_M                               # px per metre in the room / her plane
K_FAC = 400.0 / 3.0                         # facade: one storey (400 units) = 3 m
D_WALL, D_HER, D_FAC = 2.5, 2.32, 20.5
YF = (FAC.ground_y - FAC.floor_y(13)) / K_FAC        # her floor above the street (same design)
ROOM_V0 = 1800.0 + YF * K_ROOM
_LOCK = FAC.camera_lock()
Y_LOCK = (FAC.ground_y - _LOCK.y) / K_FAC
Z_LOCK = D_FAC - F / (_LOCK.zoom * K_FAC)
_SKY_REF = _LOCK.parallax(0.55)             # s01/s02's skyline layer at the lock
D_SKY = 60.0
K_SKY = F / ((D_SKY - Z_LOCK) * _SKY_REF.zoom)
SKY_V0 = _SKY_REF.y + Y_LOCK * K_SKY

HX = 556.0                                  # her pelvis x (her plane = room coords)
GAP_AT = 0.76                               # the crack: just in front of her face once she turns
CRACK_X = lerp(ROOM.glass[0], ROOM.glass[2], GAP_AT)
NEW_WIN = 14                                # the window that lights up, seen through the crack
X0 = (HX + 4.0 - 540.0) / K_ROOM            # camera starts behind her head
Y0 = YF + 1.38
X_PASS = (CRACK_X + 6.0 - 540.0) / K_ROOM   # where the camera slips through the crack
Y_PASS = YF + 1.71

T_TURN = 4.05
T_GAP = (4.25, 4.55)
T_NEW = 4.72                                # window NEW_WIN lights up across the street
T_GLINT = 9.26                              # [street]
T_DARK0 = 10.0
T_BLACK = 11.70

HER_BODY = Body.adult_f(590, upper_arm=0.002, forearm=0.002, hand=0.002, hand_scale=0.02)
HER_LOOK = Look(hair="bob", shoes="heel", eyes=False)
UA, FA = 0.186 * 590, 0.146 * 590
HAND = 0.108 * 0.9 * 590
R_UA, R_FA = (0.031 * 590, 0.023 * 590), (0.024 * 590, 0.016 * 590)


def _k(t, t0, dur, e="inout"):
    return ease(e, (t - t0) / dur) if dur > 0 else float(t >= t0)


def _track(keys, t):
    """keys [(t, v, ease_into)], scalar or tuple values, held outside."""
    if t <= keys[0][0]:
        return keys[0][1]
    for i in range(1, len(keys)):
        if t <= keys[i][0]:
            t0, a = keys[i - 1][0], keys[i - 1][1]
            t1, b = keys[i][0], keys[i][1]
            u = ease(keys[i][2] if len(keys[i]) > 2 else "inout", (t - t0) / (t1 - t0))
            if isinstance(a, tuple):
                return tuple(lerp(x, y, u) for x, y in zip(a, b))
            return lerp(a, b, u)
    return keys[-1][1]


def _pchip(keys, t):
    """Monotone cubic through (t, v) keys, flat at both ends."""
    ts = [k[0] for k in keys]
    ys = [k[1] for k in keys]
    if t <= ts[0]:
        return ys[0]
    if t >= ts[-1]:
        return ys[-1]
    n = len(ts)
    h = [ts[i + 1] - ts[i] for i in range(n - 1)]
    d = [(ys[i + 1] - ys[i]) / h[i] for i in range(n - 1)]
    m = [0.0] * n
    for i in range(1, n - 1):
        if d[i - 1] * d[i] > 0:
            w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
    i = 0
    while i < n - 2 and t > ts[i + 1]:
        i += 1
    s = (t - ts[i]) / h[i]
    return ((2 * s ** 3 - 3 * s * s + 1) * ys[i] + (s ** 3 - 2 * s * s + s) * h[i] * m[i]
            + (-2 * s ** 3 + 3 * s * s) * ys[i + 1] + (s ** 3 - s * s) * h[i] * m[i + 1])


# ----------------------------------------------------------------------------- camera
_ZK = [(-0.7, -0.215), (0.0, -0.19), (1.0, -0.13), (2.9, 0.22), (4.2, 0.52), (4.9, 0.70), (7.2, 1.30),
       (7.72, 2.05), (7.98, 2.62), (8.48, 5.30), (8.98, 7.62), (9.45, Z_LOCK)]


def cam3(t):
    z = _pchip(_ZK, t)
    if t > 9.45:
        z = Z_LOCK + 0.035 * _k(t, 9.45, 2.4, "out")
    x = _track([(1.0, X0), (4.2, X0, "inout"), (7.2, X_PASS - 0.012, "inout"), (7.98, X_PASS, "inout"),
                (9.45, 0.0, "inout")], t)
    y = _track([(1.0, Y0), (4.2, Y0 + 0.05, "inout"), (7.2, Y_PASS, "inout"), (7.98, Y_PASS, "inout"),
                (9.45, Y_LOCK, "inout")], t)
    # a breath of handheld while we are in the room, steadier outside
    a = 0.012 * (1.0 - _k(t, 7.4, 1.5))
    x += a * fbm1(t * 0.5, 3)
    y += a * fbm1(t * 0.45, 9)
    return (x, y, z)


def pcam(c3, d, k, u0, v0):
    x, y, z = c3
    return Camera(u0 + x * k, v0 - y * k, F / (max(d - z, 1e-3) * k))


def cams(t):
    c3 = cam3(t)
    return dict(c3=c3, room=pcam(c3, D_WALL, K_ROOM, 540.0, ROOM_V0), her=pcam(c3, D_HER, K_ROOM, 540.0, ROOM_V0),
                fac=pcam(c3, D_FAC, K_FAC, 540.0, FAC.ground_y), sky=pcam(c3, D_SKY, K_SKY, 540.0, SKY_V0))


def _room_to_her(C, p):
    return C["her"].to_world(C["room"].to_screen(p))


def _her_to_room(C, p):
    return C["room"].to_world(C["her"].to_screen(p))


# ----------------------------------------------------------------------------- the curtain
_EDGE_OPEN = ROOM.curtain_edge(0.0)
_EDGE_SHUT = ROOM.curtain_edge(1.0)
_PULL = (1.95, 2.60)
_X_RELEASE = 432.0
_V_RELEASE = 2.0 * (_EDGE_OPEN - _X_RELEASE) / (_PULL[1] - _PULL[0])
_SLIDE = 2.0 * (_X_RELEASE - _EDGE_SHUT) / _V_RELEASE


def curtain_x(t):
    """Room-plane x of the curtain's leading edge (she pulls it, then it slides home)."""
    if t <= _PULL[0]:
        return _EDGE_OPEN
    if t <= _PULL[1]:
        u = (t - _PULL[0]) / (_PULL[1] - _PULL[0])
        return lerp(_EDGE_OPEN, _X_RELEASE, u * u)
    u = clamp((t - _PULL[1]) / _SLIDE)
    x = lerp(_X_RELEASE, _EDGE_SHUT, 1.0 - (1.0 - u) ** 2)
    # the rings knock against the end of the rod
    if u >= 1.0:
        d = t - _PULL[1] - _SLIDE
        x += 5.0 * math.exp(-d / 0.08) * math.sin(d * 2 * math.pi * 6.0)
    return x


def curtain_close(t):
    return clamp((_EDGE_OPEN - curtain_x(t)) / (_EDGE_OPEN - _EDGE_SHUT), 0.0, 1.02)


def crack(t):
    return _k(t, T_GAP[0], T_GAP[1] - T_GAP[0], "out3")


# ----------------------------------------------------------------------------- her
def _her_pose(t):
    p = Pose(0.0, 0.0, 0.0)
    p.yaw = _track([(1.7, -90.0), (1.95, -82.0, "inout"), (2.6, -106.0, "in"), (3.05, -94.0, "out"), (3.5, -90.0),
                    (T_TURN, -90.0), (T_TURN + 0.38, 0.0, "inout")], t)
    p.pitch = _track([(1.1, 0.0), (1.42, 15.0, "inout"), (1.7, 2.0, "inout"), (4.3, 0.0), (4.62, 7.0, "inout")], t)
    p.spine = [0.0, 0.0, _track([(4.3, 0.0), (4.62, 6.0, "inout")], t)]
    p.head = _track([(0.3, 2.0), (0.9, 9.0, "inout"), (1.6, 12.0), (1.9, -3.0, "inout"), (2.9, 2.0, "inout"),
                     (3.6, 13.0, "inout"), (T_TURN, 13.0), (T_TURN + 0.42, -4.0, "inout"), (4.62, -2.0)], t)
    p.head_yaw = _track([(1.6, 0.0), (1.85, 24.0, "inout"), (2.35, -10.0, "inout"), (2.9, 0.0, "inout")], t)
    br = 1.2 * math.sin(t * 2 * math.pi * 0.23)
    p.spine[1] = 0.6 * br
    p.legs = {"L": dict(hip=0.0, abd=1.2, knee=2.0, ankle=0.0, toe=0.0),
              "R": dict(hip=0.0, abd=1.2, knee=2.0, ankle=0.0, toe=0.0)}
    if t > T_TURN:
        u = _k(t, T_TURN, 0.38)
        p.legs["L"].update(hip=lerp(0, 6, u), knee=lerp(2, 4, u))
        p.legs["R"].update(hip=lerp(0, -5, u), knee=lerp(2, 6, u))
    p.eyes = dict(open=0.0, glow=0.0, look=0.0)
    p.x = HX + _track([(T_TURN, 0.0), (T_TURN + 0.38, -10.0, "inout")], t)
    return p


def her_skeleton(t):
    p = _her_pose(t)
    p.y = 0.0
    sk = FG.solve(p, HER_BODY)
    J = sk.j
    g = max(J["heel_L"][1], J["heel_R"][1], J["ball_L"][1], J["ball_R"][1]) + 0.012 * sk.H
    p.y = ROOM.floor_y - g
    return FG.solve(p, HER_BODY)


def _ik(sh, tgt, prefer, ua=UA, fa=FA):
    dx, dy = tgt[0] - sh[0], tgt[1] - sh[1]
    d = math.hypot(dx, dy)
    d2 = clamp(d, abs(ua - fa) + 1e-3, (ua + fa) * 0.995)
    a = math.atan2(dy, dx)
    b = math.acos(clamp((ua * ua + d2 * d2 - fa * fa) / (2 * ua * d2), -1.0, 1.0))
    best = None
    for s in (1.0, -1.0):
        e = (sh[0] + ua * math.cos(a + s * b), sh[1] + ua * math.sin(a + s * b))
        score = (e[0] - sh[0]) * prefer[0] + (e[1] - sh[1]) * prefer[1]
        if best is None or score > best[0]:
            best = (score, e)
    w = (sh[0] + d2 * math.cos(a), sh[1] + d2 * math.sin(a))
    return best[1], w


def _bino_scale(t, C):
    """Binoculars in her hand are in her plane; on the sill they are in the wall plane. While
    she sets them down they slide from one to the other (same screen size at the hand-off)."""
    return 1.05 * lerp(1.0, C["room"].zoom / C["her"].zoom, _k(t, 1.28, 0.34))


def _arm_targets(t, sk, C):
    """Wrist targets (her plane) and the elbows' preferred directions, per arm."""
    shL, shR = sk.j["shoulder_L"], sk.j["shoulder_R"]
    hc = sk.j["head"]
    back = t < T_TURN + 0.2
    eye_y = hc[1] + 6.0
    rp = _room_to_her(C, ROOM.binocular_rest)
    rest = (rp[0], rp[1] - 15.0)
    grab_y = 1292.0
    edge = _room_to_her(C, (curtain_x(t) + 6.0, grab_y))
    # her fingers on the edge of the cloth at shoulder height, her eye at the slit above them
    crack_pt = _room_to_her(C, (CRACK_X - 26.0 * crack(t) - 4.0, 1352.0))
    sideL = (shL[0] - 16.0, shL[1] + 190.0)          # arms hanging (almost straight)
    sideR = (shR[0] + 16.0, shR[1] + 190.0)
    if back:
        L = _track([(0.45, (hc[0] - 38.0, eye_y + 34.0)), (1.15, (hc[0] - 28.0, shL[1] + 92.0), "inout"),
                    (1.55, sideL, "inout")], t)
        R = _track([(0.45, (hc[0] + 38.0, eye_y + 34.0)), (1.15, (hc[0] + 28.0, shR[1] + 92.0), "inout")], t)
        if t > 1.15:
            R = _track([(1.15, R), (1.58, rest, "inout")], t)
        if t > 1.62:
            R = _track([(1.62, rest), (1.95, edge, "inout")], t)
        if t > 1.95:
            R = edge
        if t > _PULL[1]:
            # she lets go and the arm follows through past her left side, then drops
            rel = _room_to_her(C, (_X_RELEASE + 6.0, grab_y))
            follow = (rel[0] - 92.0, shR[1] + 52.0)
            R = _track([(_PULL[1], rel), (2.84, follow, "out"), (3.55, sideR, "inout")], t)
        if t > T_TURN:
            L = sideL
        prefL = (-1.0, 0.55) if t < 1.2 else (-0.25, 1.0)
        prefR = (1.0, 0.55) if t < 1.2 else (0.4, 0.9)
        if 1.6 < t < 3.3:
            prefR = (0.15, 1.0)
        if t > T_TURN:
            R = _track([(T_TURN, sideR), (T_GAP[0] + 0.05, crack_pt, "inout")], t)
            prefR = (0.2, 1.0)
        return dict(L=(L, prefL), R=(R, prefR))
    # profile, facing right: R is the near arm, its fingers at the crack; L (far) hangs
    return dict(L=(sideL, (-0.3, 1.0)), R=(crack_pt, (0.15, 1.0)))


def _hand(c, w, ang, grip=0.4):
    d = (math.cos(ang), math.sin(ang))
    tip = (w[0] + d[0] * HAND * 0.62, w[1] + d[1] * HAND * 0.62)
    draw.capsule(c, w, tip, 8.6, 7.0)
    n = (-d[1], d[0])
    th = (w[0] + d[0] * 14.0 + n[0] * 9.0, w[1] + d[1] * 14.0 + n[1] * 9.0)
    draw.capsule(c, (w[0] + d[0] * 6.0, w[1] + d[1] * 6.0), th, 5.0, 3.6)


def draw_her(f, t, C, color=INK, ctx=None):
    """Her silhouette (rig body + 2D arms) in her plane, on ctx (default the frame).
    Returns her skeleton."""
    sk = her_skeleton(t)
    c = ctx if ctx is not None else f.ctx
    FG.draw_figure(f, sk, HER_LOOK, c, color=color, eyes=False)
    arms = _arm_targets(t, sk, C)
    # binoculars at her eyes: the upper arms point forward, out and down (foreshortened)
    fs = _k(t, 0.45, 0.8)
    ua, fa = UA * lerp(0.80, 1.0, fs), FA * lerp(0.92, 1.0, fs)
    wr, hcen = {}, {}
    for s in ("L", "R"):
        tgt, pref = arms[s]
        sh = sk.j["shoulder_" + s]
        e, w = _ik(sh, tgt, pref, ua, fa)
        wr[s] = w
        draw.capsule(c, sh, e, R_UA[0], R_UA[1])
        draw.capsule(c, e, w, R_FA[0], R_FA[1])
        ang = math.atan2(w[1] - e[1], w[0] - e[0])
        _hand(c, w, ang)
        hcen[s] = (w[0] + math.cos(ang) * HAND * 0.45, w[1] + math.sin(ang) * HAND * 0.45)
        draw.fill(c, color)
    # the binoculars: at her eyes (barrels just showing past her head), lowered in both
    # hands, then carried in the right hand to the sill
    if t < 1.15:
        mid = ((hcen["L"][0] + hcen["R"][0]) / 2, (hcen["L"][1] + hcen["R"][1]) / 2 - 4.0)
        draw_binoculars(c, mid, view="front", scale=1.05, color=color)
    elif t < 1.62:
        sc = _bino_scale(t, C)
        draw_binoculars(c, (wr["R"][0], wr["R"][1] + 15.0 * sc / 1.05), angle=90.0, scale=sc, view="pair",
                        color=color)
    return sk


def _her_rim(f, t, C, sk_fn):
    """The crack's light along her face and fingers: her silhouette shifted toward the slit,
    in light (fading away from the slit), drawn just before her ink."""
    g = crack(t)
    if g <= 0.01:
        return
    warm = switch(t, T_NEW, kind="bulb")
    col = mix(PAL.fog_at(1.0), mix(AMBER, HOT, 0.5), 0.35 * warm)
    col = mix(col, (1, 1, 1), 0.25)
    cx = _room_to_her(C, (CRACK_X, 1240.0))[0]
    c = f.ctx
    c.save()
    c.translate(3.2 / max(C["her"].zoom, 0.2), -0.6)
    c.push_group()
    sk_fn(f, t, C, color=(1, 1, 1))
    pat = c.pop_group()
    eye = FG.eye_points(her_skeleton(t), HER_LOOK)[0]
    lg = cairo.RadialGradient(cx - 10.0, eye[1] + 30.0, 0.0, cx - 10.0, eye[1] + 30.0, 520.0)
    for o, a in ((0.0, 1.0), (0.18, 0.85), (0.45, 0.35), (1.0, 0.06)):
        lg.add_color_stop_rgba(o, col[0], col[1], col[2], a * 0.9 * g)
    c.set_source(lg)
    c.mask(pat)
    c.restore()


def _eye_glint(f, t, C, sk):
    g = crack(t)
    if g <= 0.01 or t < T_GAP[0] + 0.1:
        return
    e1, e2, r, w, front = FG.eye_points(sk, HER_LOOK)
    lv = _k(t, T_GAP[1] - 0.08, 0.12, "out") * (1.0 + 0.6 * math.exp(-max(0.0, t - T_GAP[1] - 0.04) / 0.12))
    lv *= 1.0 + 0.25 * math.exp(-max(0.0, t - T_NEW - 0.05) / 0.2) * (t > T_NEW)
    lv *= 0.92 + 0.08 * math.sin(t * 5.1)
    warm = switch(t, T_NEW, kind="bulb")
    col = mix((0.92, 0.95, 1.0), (1.0, 0.92, 0.78), 0.4 * warm)
    p = (e1[0] + 1.0, e1[1])
    draw.circle(f.ctx, p, r * 0.95)
    draw.fill(f.ctx, col, clamp(0.95 * lv))
    with f.emit() as G:
        draw.glow_disc(G, p, r * 6.0, col, 0.55 * lv)
    with f.light(blur=1.5) as A:
        glow(A, p, r * 3.2, col, 0.35 * lv)


# ----------------------------------------------------------------------------- outside
def _lit_schedule():
    """Lights of the lock view and when they go out (the Bass stagger closes in on 9)."""
    order = [37, 30, 26, 23, 19, 12, NEW_WIN, 2, 7, 4]
    t0, dt = T_DARK0 + 0.30, 0.118
    offs = {}
    for k, i in enumerate(order):
        offs[i] = t0 + k * dt * (1.0 - 0.025 * k)
    return offs


_OFF = _lit_schedule()
_OFF_LAMP, _OFF_DINER, _OFF_LOBBY, _OFF_NEIGHBOURS = T_DARK0 + 0.0, T_DARK0 + 0.08, T_DARK0 + 0.16, T_DARK0 + 0.24
_OFF_GLINT = 11.50


def _lit(t):
    lit = {}
    for i, v in NIGHT.items():
        lit[i] = switch(t, None, _OFF.get(i), level=v)
    lit[NEW_WIN] = switch(t, T_NEW, _OFF[NEW_WIN], kind="bulb", level=0.9)
    return lit


class _Blk(Block):
    """A neighbour whose lit windows all go out at one moment."""
    t_off = None

    def lit_windows(self, t=0.0):
        k = 1.0 if self.t_off is None else switch(t, None, self.t_off)
        return [(w, l * k) for (w, l) in Block.lit_windows(self, t) if l * k > 0.01]


def _blocks():
    out = []
    for b in neighbours(FAC):
        nb = _Blk(b.x0, b.x1, b.top, b.ground, seed=b.seed, scale=b.s, lit_frac=b.lit_frac, tone=b.tone,
                  water_tank=b.water_tank)
        nb.t_off = _OFF_NEIGHBOURS
        out.append(nb)
    return out


BLOCKS = _blocks()
SKYLINE = Skyline(x0=-3000, x1=4000, base_y=3500, seed=2, scale=1.0, height=(1500, 3300), lit=0.05)
STREET = Street(FAC.ground_y, depth=560, seed=3)
LAMP = Streetlamp((FAC.x0 + 250, FAC.ground_y + 40), height=680, facing=1)
CAR = Car((FAC.x1 - 330, STREET.lane_y(0.25)), scale=1.0, facing=-1, seed=1)


def _resident(i, sway=0.0, dx=0.0):
    def fn(c, w):
        d = lib.dolls()[i]
        k = w.person_h / 600.0
        pin = (w.cx + dx * w.w, w.floor_y - d.bbox[3] * k)
        d.draw(c, pin, k, sway * math.sin(w.t * 1.3), solid=INK)
    return fn


INTERIORS = {4: _resident(4, sway=4.0, dx=0.05), 12: _resident(12, dx=0.08), 30: _resident(30, dx=-0.05)}


def _outside(f, t, C, dark):
    """Everything beyond her glass, through each plane's own camera. dark: 0..1 the end."""
    out_k = _k(t, 7.85, 0.5)                         # we are outside: the facade comes into focus
    # sky and the far city
    f.set_camera(C["fac"])
    hz = C["fac"].to_screen((540.0, FAC.top_y))[1] + 70.0
    night_sky(f, t, horizon=hz, spread=lerp(300.0, 420.0, out_k), glow=1.0 - 0.85 * dark, clouds=0.7)
    f.set_camera(C["sky"])
    SKYLINE.draw(f, t, layer=dict(par=1.0, blur=3, fog=0.72))
    f.haze(PAL.fog_at(0.9), 0.32 * (1.0 - 0.6 * dark), y0=600, y1=5200, feather=1600)
    # the street's buildings
    f.set_camera(C["fac"])
    blur = lerp(2.2, 0.0, out_k)
    draw_blocks(f, t, BLOCKS, layer=dict(par=1.0, fog=0.28, blur=blur))
    lit = _lit(t)
    lamp_on = switch(t, None, _OFF_LAMP)
    diner = switch(t, None, _OFF_DINER, level=0.6)
    lobby = switch(t, None, _OFF_LOBBY)
    FAC.draw(f, t, layer=dict(par=1.0, fog=0.10 * (1.0 - out_k), blur=blur), lit=lit, interiors=INTERIORS,
             curtains={9: "open", 12: "sheers_open"}, shops=(0.0, diner), entrance=lobby, wall_tone=1.0 - 0.35 * dark)
    srcs = FAC.light_sources(t, lit, entrance=lobby, shops=(0.0, diner)) + [LAMP.light_source(on=lamp_on)]
    for b in BLOCKS:
        srcs += b.light_sources(t)
    STREET.draw(f, t, sources=srcs, lamp_pools=[(LAMP.lantern[0], lamp_on)])
    with f.layer() as L:
        CAR.draw_on(L)
    LAMP.draw(f, t, on=lamp_on)
    f.haze(PAL.fog_at(0.85), 0.20 * (1.0 - dark), y0=3450, y1=4700, feather=500)
    f.haze(PAL.fog_at(1.0), 0.05 * (1.0 - dark))
    _glint(f, t, C)


def _glint(f, t, C):
    """Window 9, dark: someone stands back from the glass with binoculars on us."""
    if t < T_GLINT - 0.3:
        return
    lv = _k(t, T_GLINT - 0.04, 0.10, "out") * (1.0 + 1.3 * math.exp(-max(0.0, t - T_GLINT - 0.06) / 0.18))
    lv *= 0.86 + 0.14 * math.sin(t * 3.7) * math.sin(t * 1.9 + 1.0)
    if t > _OFF_GLINT - 0.25:
        lv *= 1.0 + 1.4 * math.exp(-abs(t - (_OFF_GLINT - 0.12)) / 0.06)
    if t > _OFF_GLINT:
        lv *= math.exp(-(t - _OFF_GLINT) / 0.035)
    if lv <= 0.01:
        return
    x0, y0, x1, y1 = FAC.window_rect(9)
    cx = (x0 + x1) / 2 + 0.06 * (x1 - x0)
    ey = FAC.floor_y(9) - 0.90 * FAC.person_h
    lenses = [(cx - 15.0, ey), (cx + 15.0, ey)]
    col = mix(PAL.lightning, (1, 1, 1), 0.2)
    f.set_camera(C["fac"])
    z = C["fac"].zoom
    with f.emit() as G:
        for p in lenses:
            draw.circle(G, p, 4.5 / z)
            draw.fill(G, col, 0.9 * min(lv, 1.6))
    with f.light(blur=1.0) as A:
        for p in lenses:
            glow(A, p, 16.0 / z, col, 0.55 * min(lv, 2.0))
            draw.circle(A, p, 1.6 / z)
            draw.fill(A, (1, 1, 1), min(1.0, 0.9 * lv))
        # a small star on the brighter lens
        p = lenses[1]
        for ang, ln in ((0.0, 34.0), (90.0, 26.0)):
            a = math.radians(ang + 4.0 * math.sin(t * 0.7))
            d = (math.cos(a) * ln / z * min(lv, 1.8), math.sin(a) * ln / z * min(lv, 1.8))
            draw.capsule(A, (p[0] - d[0], p[1] - d[1]), (p[0] + d[0], p[1] + d[1]), 0.5 / z, 0.5 / z)
            draw.fill(A, col, 0.35 * min(lv, 1.5))


RAIN_N = 2400
_RAIN_R = np.random.default_rng(1207).random((RAIN_N, 4))
RAIN_BOX = (24.0, 30.0, 14.0)               # metres around the camera (x, y, z ahead)
RAIN_V, RAIN_WIND, RAIN_DT = 8.5, 0.9, 0.030


def _rain3d(f, t, c3, level):
    """Rain as 3D streaks in a box that travels with the camera, projected each frame through
    the same pinhole as the planes: the streaks stretch with the fall and with the camera's
    own move (the dolly through the glass streams them past). Only beyond her glass and in
    front of the facade."""
    if level <= 0.01:
        return
    xc, yc, zc = c3
    xp, yp, zp = cam3(t - RAIN_DT)
    bw, bh, bd = RAIN_BOX
    R = _RAIN_R
    v = RAIN_V * (0.9 + 0.2 * R[:, 3])
    x = xc + np.mod(R[:, 0] * bw + RAIN_WIND * t - xc, bw) - bw / 2
    y = yc + np.mod(R[:, 1] * bh - v * t - yc, bh) - bh / 2
    z = zc + 0.3 + np.mod(R[:, 2] * bd - zc, bd)
    zmin = (D_WALL + 0.03) if zc < D_WALL else zc + 0.3
    keep = (z > zmin) & (z < D_FAC - 0.3)
    x, y, z, v = x[keep], y[keep], z[keep], v[keep]
    dz = z - zc
    dzp = np.maximum(z - zp, 0.05)
    sx = W / 2 + F * (x - xc) / dz
    sy = H / 2 - F * (y - yc) / dz
    px = W / 2 + F * (x - RAIN_WIND * RAIN_DT - xp) / dzp
    py = H / 2 - F * (y + v * RAIN_DT - yp) / dzp
    vis = (sx > -80) & (sx < W + 80) & (sy > -80) & (np.minimum(sy, py) < H + 80)
    if not vis.any():
        return
    sx, sy, px, py, dz = sx[vis], sy[vis], px[vis], py[vis], dz[vis]
    # clamp absurd streaks (a drop right at the lens during the dolly)
    ln = np.hypot(sx - px, sy - py)
    k = np.minimum(1.0, 420.0 / np.maximum(ln, 1e-3))
    px = sx + (px - sx) * k
    py = sy + (py - sy) * k
    q = np.clip(4.5 / dz, 0.42, 1.0)
    width = np.clip(2.6 / dz, 1.0, 3.2)
    ab = np.clip((q * 6.0 - 1e-3).astype(int), 0, 5)
    wb = np.clip(np.round((width - 1.0) / 0.55).astype(int), 0, 4)
    col = mix(RAIN, PAL.fog_at(1.0), 0.25)
    f.set_camera(Camera())
    with f.light(blur=0.0) as A:
        A.set_line_cap(cairo.LINE_CAP_ROUND)
        for ai in range(6):
            for wi in range(5):
                sel = np.nonzero((ab == ai) & (wb == wi))[0]
                if not len(sel):
                    continue
                for j in sel:
                    A.move_to(float(px[j]), float(py[j]))
                    A.line_to(float(sx[j]), float(sy[j]))
                A.set_line_width(1.0 + 0.55 * wi)
                draw.rgba(A, col, level * 0.27 * (ai + 0.5) / 6.0)
                A.stroke()


def _curtain_glow(f, t, g):
    """The drawn curtain is not quite opaque: the window glows through the cloth, its four
    panes and the cross of the sash a shade darker (only over the covered glass)."""
    x0, y0, x1, y1 = ROOM.glass
    a = max(curtain_x(t), x0 - 8.0)
    if a >= x1 - 4.0:
        return
    gw = 26.0 * g
    segs = [(a, x1)] if g <= 0.01 else [(a, CRACK_X - gw - 3.0), (CRACK_X + gw + 3.0, x1)]
    cx, ym = (x0 + x1) / 2, (y0 + y1) / 2
    panes = [(x0 + 16, y0 + 16, cx - 6, ym - 13), (cx + 6, y0 + 16, x1 - 16, ym - 13),
             (x0 + 16, ym + 13, cx - 6, y1 - 18), (cx + 6, ym + 13, x1 - 16, y1 - 18)]
    col = mix(PAL.fog_at(1.0), RAIN, 0.25)
    with f.light(blur=10.0) as A:
        for (sa, sb) in segs:
            if sb - sa < 2.0:
                continue
            A.save()
            A.rectangle(sa, y0 - 40.0, sb - sa, y1 - y0 + 80.0)
            A.clip()
            for (px0, py0, px1, py1) in panes:
                A.rectangle(px0, py0, px1 - px0, py1 - py0)
            draw.linear(A, (0, y0), (0, y1), [(0, col, 0.30), (0.6, col, 0.36), (1, col, 0.46)])
            A.fill()
            # the folds: the cloth is thinner on the crests
            n = int((sb - sa) / 34.0) + 1
            for j in range(n):
                fx = sa + (j + 0.5) * (sb - sa) / n
                draw.linear(A, (fx - 17.0, 0), (fx + 17.0, 0), [(0, col, 0.0), (0.5, col, 0.10), (1, col, 0.0)])
                A.rectangle(fx - 17.0, y0, 34.0, y1 - y0)
                A.fill()
            A.restore()


# ----------------------------------------------------------------------------- render
def render(f, t, T):
    C = cams(t)
    c3 = C["c3"]
    dark = _k(t, T_DARK0, 1.6, "in")
    f.fill(INK)
    _outside(f, t, C, dark)
    _rain3d(f, t, c3, (1.0 - _k(t, T_DARK0 + 0.2, 1.3)) * lerp(0.8, 1.0, _k(t, 7.6, 0.6)))
    # her room: the window wall with the curtain, the crack
    if c3[2] < D_WALL - 0.004:
        f.set_camera(C["room"])
        g = crack(t)
        ROOM.draw(f, t, curtain=curtain_close(t), gap=g, gap_at=GAP_AT, rain=1.0, binoculars=t >= 1.62, lamp=0.0,
                  chair=True, outside_light=1.1, condensation=1.0, room_light=0.0)
        _curtain_glow(f, t, g)
        if g > 0.01:
            warm = switch(t, T_NEW, kind="bulb")
            if warm > 0.01:
                with f.light(blur=6.0) as A:
                    gw = 26.0 * g
                    draw.linear(A, (CRACK_X - gw, 0), (CRACK_X + gw, 0), [(0, AMBER, 0.0), (0.5, AMBER, 0.12 * warm),
                                                                          (1, AMBER, 0.0)])
                    A.rectangle(CRACK_X - gw, ROOM.rod_y + 10, 2 * gw, ROOM.floor_y - ROOM.rod_y - 10)
                    A.fill()
    # her
    if c3[2] < D_HER - 0.012:
        f.set_camera(C["her"])
        _her_rim(f, t, C, draw_her)
        sk = draw_her(f, t, C)
        # she hides the bloom of whatever lit window is behind her
        with f.emit() as G:
            G.save()
            G.set_operator(cairo.OPERATOR_CLEAR)
            draw_her(f, t, C, color=(0, 0, 0), ctx=G)
            G.restore()
        _eye_glint(f, t, C, sk)
    f.set_camera(Camera())
    f.post["vignette"] = 0.6
    if t >= T_BLACK - 0.25:
        f.post["fade"] = _k(t, T_BLACK - 0.25, 0.25, "in")


def motion_blur(t, T):
    return 3 if 7.55 <= t <= 8.75 else 1


def cues(T):
    out = [
        Cue(-0.6, "rain on her window, close; the radiator ticks", -6.0, 0.0, dur=12.6),
        Cue(1.36, "binoculars set down on the wooden sill (soft knock)", -8.0, 0.2),
        Cue(1.95, "she takes the curtain: rings shiver on the rod", -8.0, 0.4),
        Cue(2.05, "curtain rings run along the rod, the drape swishes shut", -2.0, -0.2, dur=0.85),
        Cue(2.92, "the rings knock home at the end of the rod", -6.0, -0.5),
        Cue(4.25, "the drape parted by her fingers (soft fabric)", -12.0, 0.1),
        Cue(4.72, "across the street a light switch clicks on, far and small", -16.0, 0.0),
        Cue(7.2, "score: strings lift, rain swells", -6.0, 0.0, dur=2.6),
        Cue(7.95, "through the glass: a wet hush, then the open rain and the street below", -4.0, 0.0, dur=1.2),
        Cue(T.at("street"), "a tiny bright glint (binoculars)", -10.0, 0.25),
        Cue(_OFF_LAMP, "the street lamp dies (Bass stagger begins)", -10.0, -0.5),
    ]
    for i, tt in sorted(_OFF.items(), key=lambda kv: kv[1]):
        out.append(Cue(tt, "window %d goes dark: a muted pizzicato click" % i, -12.0, (i - 1) % 5 / 2.0 - 1.0))
    out.append(Cue(_OFF_GLINT, "the glint winks out; silence, the rain thins to nothing", -10.0, 0.25, dur=0.5))
    return out
